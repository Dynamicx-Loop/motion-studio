"""Official public preparation with fixture filesystem/Git/runtime boundaries."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from motion_studio.integrations.umr import reproduce_g1_baseline

PIN = 'd1cdaedaf67a827198da71c5fa831f48b2e51f91'
MODEL = Path('/data/motions/human_models/smplx/1.1/models_smplx_v1_1/models/smplx/SMPLX_NEUTRAL.pkl')
MOTION = 'sample_data/hiphi/data/Getting_up/get_up/Getting_up-get_up_0004/motion_actor_smplx.npz'
ROOT = Path(__file__).resolve().parents[1]

# The scientific process boundary exercises real owned preparation, with tiny
# upstream modules replacing CUDA and pipeline configuration loading. No training.
RUNTIME = '''import json, pathlib, runpy, sys, types
args = sys.argv[1:]
if args[-1] == 'prepare':
    torch = types.ModuleType('torch')
    torch.cuda = types.SimpleNamespace(is_available=lambda: True, get_device_name=lambda n: 'fixture GPU')
    sys.modules['torch'] = torch
    pipeline = types.ModuleType('humanoid_retarget_pipeline')
    def load(config, defaults):
        value = json.loads(pathlib.Path(config).read_text())
        value['solver'] = json.loads(pathlib.Path(defaults).read_text())['solver']
        return value
    pipeline.load_pipeline_config = load
    sys.modules['humanoid_retarget_pipeline'] = pipeline
    sys.argv = args
    runpy.run_path(args[0], run_name='__main__')
elif '--stage' in args:
    config = json.loads(pathlib.Path(args[args.index('--config')+1]).read_text())
    xml = pathlib.Path(config['robot']['xml'])
    xml.with_suffix('.floating_mjcf.xml').write_text('generated beside run-local input')
else:
    pathlib.Path(args[2], 'validation.json').write_text('{"fixture_only": true}')
'''


class G1PreparationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.workspace = Path(self.temp.name)
        shutil.copytree(ROOT / 'motion_studio', self.workspace / 'motion_studio')
        self.checkout = self.workspace / 'externals/UMR'
        self.checkout.mkdir(parents=True)
        self.asset = self.checkout / 'assets/g1'
        self.asset.mkdir(parents=True)
        (self.asset / 'g1_29dof.xml').write_text('<mujoco model="official fixture"/>')
        (self.asset / 'mesh.obj').write_bytes(b'original mesh\n')
        (self.asset / 'other-edition.xml').write_text('full bundle, not selected closure')
        config = {'robot': {'xml': '../assets/g1/g1_29dof.xml',
                            'tpose_qpos': {'left_elbow_joint': 1.57079632679},
                            'point_cloud_center': 'body:waist_yaw_link'},
                  'calibration': {'fixture_original': 7}}
        (self.checkout / 'robot_configs').mkdir()
        (self.checkout / 'robot_configs/humanoid_retarget_unitree_g1_example.json').write_text(json.dumps(config))
        (self.checkout / 'humanoid_retarget_defaults.json').write_text(json.dumps({
            'solver': {'fixture_default': 13}, 'correspondence': {'train': {}, 'dataset': {}}}))
        motion = self.checkout / MOTION
        motion.parent.mkdir(parents=True)
        motion.write_bytes(b'complete fixture clip')
        self.model = self.workspace / 'human-model.pkl'
        self.model.write_bytes(b'fixture human model')
        runtime = self.workspace / 'runtime.py'
        runtime.write_text(RUNTIME)
        python = self.checkout / '.venv/bin/python'
        python.parent.mkdir(parents=True)
        python.write_text(f'#!/bin/sh\nexec {sys.executable} {runtime} "$@"\n')
        python.chmod(0o755)
        for args in (['init', '-q'], ['add', '.'],
                     ['-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'fixture']):
            subprocess.run(['git', '-C', str(self.checkout), *args], check=True)
        (self.workspace / 'externals/manifest.json').write_text(json.dumps({
            'projects': [{'name': 'UMR', 'revision': PIN}]}))

    def boundaries(self):
        from contextlib import ExitStack
        stack = ExitStack()
        original_git = subprocess.check_output
        original_open, original_is_file = Path.open, Path.is_file
        def git(command, *args, **kwargs):
            command = list(command)
            if command[-2:] == ['rev-parse', 'HEAD']:
                return PIN + '\n'
            command = ['HEAD' if v == PIN else v for v in command]
            return original_git(command, *args, **kwargs)
        stack.enter_context(patch('subprocess.check_output', side_effect=git))
        stack.enter_context(patch.object(Path, 'open', lambda p, *a, **k:
                                        original_open(self.model if p == MODEL else p, *a, **k)))
        stack.enter_context(patch.object(Path, 'is_file', lambda p:
                                        original_is_file(self.model if p == MODEL else p)))
        return stack

    def test_catalog_removal_or_redirection_cannot_change_official_preparation(self):
        source = {p.relative_to(self.asset): p.read_bytes() for p in self.asset.rglob('*') if p.is_file()}
        frozen = self.workspace / 'experiments/frozen/record.json'
        frozen.parent.mkdir(parents=True)
        frozen.write_bytes(b'{"frozen": "original baseline"}\n')
        old_run = self.workspace / 'outputs/old-run/motion.npz'
        old_run.parent.mkdir(parents=True)
        old_run.write_bytes(b'preserved numerical evidence')
        for catalog in ('removed', 'redirected'):
            with self.subTest(catalog=catalog):
                if catalog == 'redirected':
                    target = self.workspace / 'robots/g1_29dof'
                    target.mkdir(parents=True)
                    (target / 'robot.json').write_text('{"model": "malicious.xml"}')
                    (target / 'poses.json').write_text('invalid catalog')
                output = self.workspace / catalog
                # Import the owned package from the isolated workspace: its actual
                # default catalog is absent/redirected, not merely an unused root.
                runner = """import sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
sys.path.insert(1, sys.argv[2])
from test_g1_preparation import G1PreparationTests, reproduce_g1_baseline
fixture = G1PreparationTests()
fixture.model = Path(sys.argv[1]) / 'human-model.pkl'
with fixture.boundaries():
    reproduce_g1_baseline(Path(sys.argv[3]), workspace=Path(sys.argv[1]))
"""
                subprocess.run([sys.executable, '-c', runner, str(self.workspace),
                                str(ROOT / 'tests'), str(output)], check=True,
                               cwd=self.workspace, capture_output=True, text=True)
                config = json.loads((output / 'config.json').read_text())
                self.assertEqual(Path(config['robot']['xml']), output / 'assets/g1/g1_29dof.xml')
                self.assertEqual(config['robot']['tpose_qpos'], {'left_elbow_joint': 1.57079632679})
                self.assertEqual(config['calibration'], {'fixture_original': 7})
                self.assertEqual(config['motion']['data'], str(self.checkout / MOTION))
                for name, data in source.items():
                    self.assertEqual((output / 'assets/g1' / name).read_bytes(), data)
                    self.assertEqual((self.asset / name).read_bytes(), data)
                self.assertFalse((self.asset / 'g1_29dof.floating_mjcf.xml').exists())
                self.assertTrue((output / 'assets/g1/g1_29dof.floating_mjcf.xml').is_file())
                self.assertTrue(json.loads((output / 'preservation.json').read_text())['external_and_inputs_unchanged'])
                self.assertTrue((output / 'validation.json').is_file())
                self.assertEqual(frozen.read_bytes(), b'{"frozen": "original baseline"}\n')
                self.assertEqual(old_run.read_bytes(), b'preserved numerical evidence')

    def test_changed_required_asset_is_rejected_before_output_mutation(self):
        (self.asset / 'mesh.obj').write_bytes(b'changed mesh')
        output = self.workspace / 'run'
        with self.boundaries(), self.assertRaisesRegex(ValueError, 'unchanged'):
            reproduce_g1_baseline(output, workspace=self.workspace)
        self.assertFalse(output.exists())


if __name__ == '__main__':
    unittest.main()
