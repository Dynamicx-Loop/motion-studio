"""Fresh legacy preparation never launches historical writers."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from motion_studio.integrations.umr_hiphi_control import prepare_legacy_run


class PreparationTests(unittest.TestCase):
    def test_fresh_configs_isolate_writes_and_freeze_models(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            cohort = root / 'experiments/hiphi-robot-control'
            (cohort / 'configs').mkdir(parents=True)
            model = root / 'model'
            (model / 'meshes').mkdir(parents=True)
            (model / 'meshes/body.stl').write_bytes(b'mesh')
            (model / 'robot.xml').write_text('<mujoco><asset><mesh file="meshes/body.stl"/></asset></mujoco>')
            motion = root / 'motion.npz'
            motion.write_bytes(b'motion')
            for robot in ('astro', 'g1'):
                for version in ('reference', 'reconverted'):
                    config = {'robot': {'xml': str(model / 'robot.xml')},
                              'motion': {'data': str(motion)},
                              'correspondence': {'dataset': {'out': '/old'}, 'train': {'out_dir': '/old'}},
                              'retarget': {'out': '/old'}}
                    (cohort / 'configs' / f'{robot}-{version}-resolved.json').write_text(json.dumps(config))
            pipeline = root / 'externals/UMR/scripts/humanoid_retarget_pipeline.py'
            pipeline.parent.mkdir(parents=True)
            pipeline.write_text('# preserved pipeline source\n')
            viewer = root / 'scripts/hiphi-robot-viewer'
            viewer.mkdir(parents=True)
            (viewer / 'index.html').write_text('<html>viewer source</html>')
            (viewer / 'app.js').write_text('// viewer source')
            inventory = root / 'inventory.json'
            files = [{'absolute_path': str(p), 'path': str(p.relative_to(root)),
                      'bytes': p.stat().st_size, 'kind': 'file',
                      'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
                     for p in root.rglob('*') if p.is_file()]
            inventory.write_text(json.dumps({'files': files}))
            anchor = hashlib.sha256(inventory.read_bytes()).hexdigest()
            run = root / 'outputs/fresh'
            receipt = prepare_legacy_run(root, inventory, anchor, 'outputs/fresh', Path('/usr/bin/python3'))
            self.assertEqual(len(receipt['commands']), 4)
            self.assertIn(str(pipeline), receipt['inputs'])
            self.assertEqual(receipt['viewer']['destination'], str(run / 'viewer'))
            self.assertTrue((run / 'viewer/app.js').is_file())
            for entry in receipt['commands']:
                config = json.loads(Path(entry['argv'][-2]).read_text())
                self.assertTrue(Path(config['robot']['xml']).is_relative_to(run))
                self.assertTrue(Path(config['retarget']['out']).is_relative_to(run))
                self.assertEqual(config['motion']['data'], str(motion))
            self.assertEqual((model / 'meshes/body.stl').read_bytes(), b'mesh')
            with self.assertRaises(ValueError):
                prepare_legacy_run(root, inventory, anchor, 'outputs/fresh', Path('/usr/bin/python3'))
