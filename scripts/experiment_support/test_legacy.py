"""Regression checks for retrospective evidence boundaries; no numerical reruns."""
CHECK_TIER = 'saved-evidence'
CHECK_MODULES = ('jsonschema',)
CHECK_INPUTS = (
    'experiments/soma-correspondence-audit/results.json',
    'experiments/astro-hands-correspondence/results.json',
    'experiments/astro-hand-wrist-correction/results.json',
    'experiments/astro-canonical-static-v1/results.json',
    'experiments/astro-canonical-wrist-v1/results.json',
    'experiments/astro-fist-static-v1/results.json',
    'experiments/astro-fist-wrist-v1/results.json',
    'experiments/umr-motion-preliminary-v1/results.json',
    'experiments/umr-motion-preliminary-v2/results.json',
    'experiments/umr-motion-canonical-v1/results.json',
    'experiments/umr-motion-fist-v1/results.json',
    'schemas/experiments/result.schema.json',
    'docs/umr-head-objective-investigation.md',
    'docs/umr-solver-investigation.md',
    'docs/umr-soma-setup.md',
    'docs/umr-astro-baseline-proposal.md',
)
import copy
import json
from pathlib import Path
import tempfile
import unittest

from experiment_support.contracts import validate
from experiment_support.files import verify_bundle
from experiment_support.legacy import reconstruct

ROOT = Path(__file__).resolve().parents[2]


class LegacyEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory()
        cls.destination = Path(cls.temporary.name) / 'derived'
        cls.summary = reconstruct(ROOT, cls.destination)
        cls.records = [json.loads(line) for line in
                       (cls.destination / 'results.jsonl').read_text().splitlines()]

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def test_every_historical_arm_stays_legacy(self):
        self.assertEqual(len(self.records), 76)
        self.assertEqual(self.summary['static_arms'], 52)
        self.assertEqual(self.summary['motion_arms'], 24)
        self.assertEqual(self.summary['segment_rows'], 1924)
        self.assertEqual(self.summary['new_baseline_arms'], 0)
        for record in self.records:
            self.assertEqual(record['cohort_status'], 'legacy')
            self.assertEqual(record['reproducibility'], 'not_rerun')
            self.assertEqual(record['evidence_origin'], 'retrospective')

    def test_sources_and_outputs_match_manifest(self):
        result = verify_bundle(self.destination, ROOT)
        self.assertTrue(result['passed'], result['errors'])

    def test_refuses_overwrite(self):
        with self.assertRaises(FileExistsError):
            reconstruct(ROOT, self.destination)

    def test_cannot_claim_retrospective_rerun(self):
        record = copy.deepcopy(self.records[0])
        record['reproducibility'] = 'tested_rerun'
        with self.assertRaisesRegex(ValueError, 'Retrospective'):
            validate(record, 'result')


if __name__ == '__main__':
    unittest.main()
