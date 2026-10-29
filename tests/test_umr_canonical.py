"""Pure tests of explicit canonical preparation and learned-artifact guards."""
import hashlib
import json
from pathlib import Path
from dataclasses import replace
from unittest.mock import patch

from motion_studio.robots import RobotSelectionError, compare_representations
import shutil
import subprocess
import sys
import unittest

from robot_pair_fixture import PairFixture
from motion_studio.integrations.umr_canonical import (
    CanonicalInputs, SamplingSettings, prepare_canonical_comparison,
    require_cache_compatible, CanonicalPreparationError, UMRRuntime,
)


class CanonicalPreparationTests(unittest.TestCase):
    def setUp(self):
        self.f = PairFixture(self)
        self.input_dir = self.f.root / 'input'; self.input_dir.mkdir()
        for name, data in [('clip.npz', b'clip'), ('shape.json', b'[0,0]'), ('neutral.pkl', b'model')]:
            (self.input_dir / name).write_bytes(data)
        self.inputs = CanonicalInputs(self.input_dir/'clip.npz', self.input_dir/'shape.json',
                                      (self.input_dir/'neutral.pkl',), fps=30)

    def prepare(self, name='run', **kwargs):
        return prepare_canonical_comparison('fixture', 'mjcf', kwargs.pop('pose', 'zero'),
            self.inputs, self.f.root/name, self.f.roots,
            definitions_root=self.f.catalog, **kwargs)

    def test_prepares_only_run_local_closure_and_complete_pose(self):
        before = (self.f.source/'model.xml').read_bytes()
        result = self.prepare()
        receipt = json.loads(result.receipt.read_text())
        config = json.loads(result.config.read_text())
        self.assertEqual(receipt['state'], 'prepared-only')
        self.assertFalse(receipt['execution_readiness'])
        self.assertEqual(receipt['runtime']['status'], 'unverified')
        self.assertEqual(config['robot']['tpose_qpos'], {'hinge': 0})
        self.assertEqual(Path(config['robot']['xml']), result.model)
        self.assertEqual(receipt['joint_order']['native'], ['hinge'])
        self.assertEqual(receipt['pose']['root_translation_m'], [0, 0, 0])
        self.assertTrue(result.model.name.endswith('-pose.xml'))
        self.assertEqual((self.f.source/'model.xml').read_bytes(), before)
        self.assertTrue(result.inputs.is_file())
        self.assertIsNone(config['correspondence']['slots'])
        self.assertEqual(Path(config['motion']['data']).suffix, '.npz')
        import xml.etree.ElementTree as ET
        root_body = ET.parse(result.model).getroot().find('worldbody/body')
        self.assertEqual(root_body.get('pos'), '0 0 0')
        self.assertEqual(root_body.get('quat'), '1 0 0 0')

    def cache(self, result, stage='checkpoint'):
        artifact = self.f.root / 'old-checkpoint.pt'; artifact.write_bytes(b'learned bytes')
        receipt = json.loads(result.receipt.read_text())
        metadata = self.f.root/'old-checkpoint.json'
        metadata.write_text(json.dumps({'schema_version': 1, 'stage': stage,
            'fingerprint': receipt['fingerprints'][stage], 'complete': True,
            'artifact_sha256': hashlib.sha256(b'learned bytes').hexdigest()}))
        return artifact, metadata

    def test_cache_guard_rejects_tampered_preparation_identity(self):
        result = self.prepare()
        artifact, metadata = self.cache(result)
        receipt = json.loads(result.receipt.read_text())
        receipt['semantic_inputs']['adapter_version'] = 'old-adapter'
        result.receipt.write_text(json.dumps(receipt))
        with self.assertRaises(CanonicalPreparationError):
            require_cache_compatible(result.receipt, artifact, metadata, stage='checkpoint')

    def test_cache_stages_have_distinct_identities(self):
        result = self.prepare()
        fingerprints = json.loads(result.receipt.read_text())['fingerprints']
        self.assertEqual(len(set(fingerprints.values())), 3)

    def test_relocated_source_and_output_keep_semantic_cache_identity(self):
        first = self.prepare('first')
        artifact, metadata = self.cache(first)
        relocated = self.f.root/'relocated-source'; shutil.copytree(self.f.source, relocated)
        copied_input = self.f.root/'relocated-input'; shutil.copytree(self.input_dir, copied_input)
        inputs = replace(self.inputs, clip=copied_input/'clip.npz', shape=copied_input/'shape.json',
                         model_files=(copied_input/'neutral.pkl',))
        second = prepare_canonical_comparison('fixture', 'mjcf', 'zero', inputs,
            self.f.root/'second', {'fixture': relocated}, definitions_root=self.f.catalog)
        self.assertEqual(json.loads(first.receipt.read_text())['semantic_identity'],
                         json.loads(second.receipt.read_text())['semantic_identity'])
        self.assertEqual(require_cache_compatible(second.receipt, artifact, metadata,
                                                  stage='checkpoint'), artifact)

    def test_pose_shape_and_sampling_change_reject_old_artifacts(self):
        first = self.prepare('first'); artifact, metadata = self.cache(first)
        for name, kwargs in [('pose', {'pose': 'bent'}),
                             ('sampling', {'settings': SamplingSettings(num_points=16)}),
                             ('seed', {'settings': SamplingSettings(seed=7)})]:
            with self.subTest(name=name):
                result = self.prepare(name, **kwargs)
                with self.assertRaises(CanonicalPreparationError):
                    require_cache_compatible(result.receipt, artifact, metadata, stage='checkpoint')
        self.inputs.shape.write_bytes(b'[1,0]')
        changed = self.prepare('changed-shape')
        with self.assertRaises(CanonicalPreparationError):
            require_cache_compatible(changed.receipt, artifact, metadata, stage='checkpoint')

    def commit_model(self, definition):
        self.f.git('add', '.')
        self.f.git('-c', 'user.name=Fixture', '-c', 'user.email=f@example.invalid', 'commit', '-qm', 'new edition')
        definition['source']['revision'] = self.f.git('rev-parse', 'HEAD').strip()
        model = definition['representations']['mjcf']
        for entry in model['files']:
            entry['sha256'] = hashlib.sha256((self.f.source/entry['path']).read_bytes()).hexdigest()
        (self.f.definition/'robot.json').write_text(json.dumps(definition))

    def test_mesh_bytes_and_application_order_invalidate_cache(self):
        definition = json.loads((self.f.definition/'robot.json').read_text())
        model = self.f.source/'model.xml'
        model.write_text(model.read_text().replace('<worldbody>',
            '<asset><mesh name="surface" file="surface.obj"/></asset><worldbody>'))
        (self.f.source/'surface.obj').write_text('v 0 0 0\nv 1 0 0\nv 0 1 0\nf 1 2 3\n')
        definition['representations']['mjcf']['files'].append(dict(path='surface.obj',role='mesh',sha256=''))
        model.write_text(model.read_text().replace('<body name="tip"',
            '<body name="tip"').replace('<body name="tip" pos="1 0 0">',
            '<body name="tip" pos="1 0 0"><joint name="finger" axis="1 0 0" range="-1 1"/>'))
        definition['joint_order'].append('finger')
        definition['representations']['mjcf']['joints'].append(dict(name='finger',kind='revolute',axis=[1,0,0],lower=-1,upper=1))
        poses = json.loads((self.f.definition/'poses.json').read_text())
        poses['poses']['zero']['joints']['finger'] = .5
        (self.f.definition/'poses.json').write_text(json.dumps(poses))
        self.commit_model(definition)
        first = self.prepare('first'); artifact, metadata = self.cache(first)
        definition['joint_order'].reverse()
        (self.f.definition/'robot.json').write_text(json.dumps(definition))
        changed_order = self.prepare('order')
        config = json.loads(changed_order.config.read_text())
        self.assertEqual(list(config['robot']['tpose_qpos']), ['hinge', 'finger'])
        self.assertEqual(list(config['robot']['tpose_qpos'].values()), [0, .5])
        with self.assertRaises(CanonicalPreparationError):
            require_cache_compatible(changed_order.receipt, artifact, metadata, stage='checkpoint')
        (self.f.source/'surface.obj').write_text('v 0 0 0\nv 2 0 0\nv 0 1 0\nf 1 2 3\n')
        with self.assertRaises(RobotSelectionError):
            self.prepare('drift')
        self.assertFalse((self.f.root/'drift').exists())
        self.commit_model(definition)
        mesh = self.prepare('mesh')
        with self.assertRaises(CanonicalPreparationError):
            require_cache_compatible(mesh.receipt, artifact, metadata, stage='checkpoint')

    def test_exact_claim_guards_reject_stale_wrong_or_unverified_reports_before_creation(self):
        report = compare_representations('fixture', self.f.roots, poses=('zero',), definitions_root=self.f.catalog)
        self.prepare('supported', representation_report=report, required_claims=('joint_order',))
        cases = [(None, ('joint_order',)), (report, ('named_frames',)),
                 (report, ('collision_geometry_equality',)),
                 (replace(report, definition_id='wrong'), ('joint_order',)),
                 (replace(report, poses=('bent',)), ('joint_order',)),
                 (replace(report, source_hashes=()), ('joint_order',)),
                 (replace(report, identities=('old',)), ('joint_order',))]
        for index, (candidate, claims) in enumerate(cases):
            name = f'rejected-{index}'
            with self.subTest(index=index), self.assertRaises((CanonicalPreparationError, RobotSelectionError)):
                self.prepare(name, representation_report=candidate, required_claims=claims)
            self.assertFalse((self.f.root/name).exists())

    def test_destinations_and_runtime_fail_before_creation(self):
        self.prepare('exists')
        with self.assertRaises(FileExistsError):
            self.prepare('exists')
        link = self.f.root/'linked'; link.symlink_to(self.f.source, target_is_directory=True)
        with self.assertRaises(CanonicalPreparationError):
            self.prepare('linked/fresh')
        self.assertFalse((self.f.source/'fresh').exists())
        with self.assertRaises(CanonicalPreparationError):
            self.prepare('wrong-runtime', runtime=UMRRuntime(self.f.source, Path('/missing/python')))
        self.assertFalse((self.f.root/'wrong-runtime').exists())
        with self.assertRaises(CanonicalPreparationError):
            prepare_canonical_comparison('fixture', 'urdf', 'zero', self.inputs,
                self.f.root/'urdf', self.f.roots, definitions_root=self.f.catalog)
        self.assertFalse((self.f.root/'urdf').exists())

    def test_failed_copy_retains_failed_receipt_and_requires_new_destination(self):
        with patch('shutil.copyfileobj', side_effect=OSError('worked disk failure')):
            with self.assertRaises(OSError):
                self.prepare('failed')
        result = json.loads((self.f.root/'failed/preparation.json').read_text())
        self.assertEqual(result['state'], 'failed')
        self.assertFalse(result['execution_readiness'])
        artifact=self.f.root/'artifact';artifact.write_bytes(b'old')
        metadata=self.f.root/'metadata.json';metadata.write_text('{"schema_version":1}')
        with self.assertRaises(CanonicalPreparationError):
            require_cache_compatible(self.f.root/'failed/preparation.json',artifact,metadata,stage='checkpoint')
        with self.assertRaises(FileExistsError):
            self.prepare('failed')

    def test_cache_requires_metadata_bytes_stage_and_unchanged_prepared_files(self):
        result = self.prepare(); artifact, metadata = self.cache(result)
        self.assertEqual(require_cache_compatible(result.receipt, artifact, metadata,
                                                  stage='checkpoint'), artifact)
        with self.assertRaises(CanonicalPreparationError):
            require_cache_compatible(result.receipt, artifact, metadata, stage='slots')
        metadata.unlink()
        with self.assertRaises(CanonicalPreparationError):
            require_cache_compatible(result.receipt, artifact, metadata, stage='checkpoint')
        artifact, metadata = self.cache(result)
        artifact.write_bytes(b'same filename, different bytes')
        with self.assertRaises(CanonicalPreparationError):
            require_cache_compatible(result.receipt, artifact, metadata, stage='checkpoint')
        artifact, metadata = self.cache(result)
        result.model.write_bytes(b'edited model')
        with self.assertRaises(CanonicalPreparationError):
            require_cache_compatible(result.receipt, artifact, metadata, stage='checkpoint')

    def test_malformed_cache_records_fail_with_public_error(self):
        result = self.prepare(); artifact, metadata = self.cache(result)
        for value in ('[]', '{"schema_version":1,"schema_version":1}', '{"schema_version":true}'):
            metadata.write_text(value)
            with self.subTest(value=value), self.assertRaises(CanonicalPreparationError):
                require_cache_compatible(result.receipt, artifact, metadata, stage='checkpoint')

    def test_includes_and_mesh_references_are_closed_inside_fresh_run(self):
        import xml.etree.ElementTree as ET
        definition = json.loads((self.f.definition/'robot.json').read_text())
        model = self.f.source/'model.xml'
        model.write_text(model.read_text().replace('<worldbody>', '<include file="bundle.xml"/><worldbody>'))
        (self.f.source/'bundle.xml').write_text('<mujocoinclude><asset><mesh name="triangle" file="surface.obj"/></asset></mujocoinclude>')
        (self.f.source/'surface.obj').write_text('v 0 0 0\nv 1 0 0\nv 0 1 0\nf 1 2 3\n')
        for path, role in [('bundle.xml','include'), ('surface.obj','mesh')]:
            definition['representations']['mjcf']['files'].append(dict(path=path,role=role,sha256=''))
        self.commit_model(definition)
        result = self.prepare()
        tree = ET.parse(result.model).getroot()
        self.assertEqual(list(tree.iter('include')), [])
        mesh = Path(tree.find('asset/mesh').attrib['file'])
        self.assertTrue(mesh.is_relative_to(result.receipt.parent))
        self.assertEqual(mesh.read_bytes(), (self.f.source/'surface.obj').read_bytes())
        self.assertTrue((result.receipt.parent/'assets/bundle.xml').is_file())

    def test_isolated_worktree_protects_other_actual_external_symlink_targets(self):
        project = self.f.root/'project'; project.mkdir()
        shutil.copytree(Path(__file__).resolve().parents[1]/'motion_studio', project/'motion_studio')
        def git(*args):
            subprocess.run(['git','-C',str(project),*args],check=True,capture_output=True)
        git('init','-q');git('add','motion_studio')
        git('-c','user.name=Fixture','-c','user.email=f@example.invalid','commit','-qm','owned source')
        fork = self.f.root/'fork'
        git('worktree','add','--detach',str(fork),'HEAD')
        other = self.f.root/'other-external';other.mkdir()
        (project/'externals').mkdir()
        (project/'externals/unrelated').symlink_to(other,target_is_directory=True)
        command = """from pathlib import Path
from motion_studio.integrations.umr_canonical import CanonicalInputs,CanonicalPreparationError,prepare_canonical_comparison
import sys
r=Path(sys.argv[1])
try:
 prepare_canonical_comparison('fixture','mjcf','zero',CanonicalInputs(r/'input/clip.npz',r/'input/shape.json',(r/'input/neutral.pkl',),30),r/'other-external/fresh',{'fixture':r/'source'},definitions_root=r/'definitions')
except CanonicalPreparationError:
 sys.exit(0)
sys.exit(3)
"""
        result = subprocess.run([sys.executable,'-c',command,str(self.f.root)],cwd=fork,
                                capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertFalse((other/'fresh').exists())


if __name__ == '__main__':
    unittest.main()
