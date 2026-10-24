"""Focused safety checks for the prepared static pair; no training or simulation."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

import static_pair


class StaticPairTests(unittest.TestCase):
    def test_write_refuses_existing_record(self):
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder) / 'record.json'
            static_pair.write(p, {'original': True})
            with self.assertRaises(FileExistsError):
                static_pair.write(p, {'original': False})
            self.assertEqual(json.loads(p.read_text()), {'original': True})

    def test_frozen_config_retains_official_algorithm(self):
        run = Path(sys.argv_run)
        official = json.loads((static_pair.UMR / 'humanoid_retarget_defaults.json').read_text())
        for arm in ['astro', 'g1']:
            config = json.loads((run / 'configs' / (arm + '-resolved.json')).read_text())
            self.assertEqual(config['solver'], official['solver'])
            for key, value in official['correspondence']['train'].items():
                if key != 'device':
                    self.assertEqual(config['correspondence']['train'][key], value)
            for key, value in official['correspondence']['dataset'].items():
                if key != 'smpl_models':
                    self.assertEqual(config['correspondence']['dataset'][key], value)
            self.assertEqual(static_pair.pipeline.expected_correspondence_training_mode(config), 'all_samples')
        astro = json.loads((run / 'configs/astro-resolved.json').read_text())
        fist = json.loads((run / 'assets/astro/fist-pose.json').read_text())['joint_positions']
        for joint, value in fist.items():
            self.assertEqual(astro['robot']['tpose_qpos'][joint], value)
        self.assertNotIn('joint_limits', astro['robot'])

    def test_inputs_still_match_preparation(self):
        record = json.loads((Path(sys.argv_run) / 'provenance.json').read_text())
        self.assertEqual(record['observations']['astro']['template'], record['observations']['g1']['template'])
        for path, expected in record['inputs_sha256'].items():
            self.assertEqual(static_pair.sha(path), expected, path)
        static_pair.check_official_source()


if __name__ == '__main__':
    sys.argv_run = sys.argv.pop(1)
    unittest.main()
