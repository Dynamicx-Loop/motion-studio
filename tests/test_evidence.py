"""Small fixtures at the owned evidence/reconstruction and preparation seams."""
CHECK_MODULES = ('jsonschema',)

import copy
import json
from pathlib import Path
import tempfile
import unittest

from motion_studio.evidence import (normalize_segment, validate_static_result,
                                    reconstruct, verify_bundle, inspect_plan, reserve, validate)
from evidence_fixtures import saved_evidence, static_row, plan_fixture, write


class EvidenceFixtureTests(unittest.TestCase):
    def test_native_segment_retains_source_denominator_and_missing_coverage(self):
        row = {'source': 'head', 'slots': 8, 'compatible_zone_slots': 3,
               'zone_precision': 0.375}
        self.assertEqual(normalize_segment(row, common=False), {
            'segment': 'head', 'slots': 8, 'compatible': 3, 'precision': 0.375,
            'coverage': None, 'high_slots': None, 'high_compatible': None})

    def test_reconstruction_uses_saved_inputs_without_a_report_builder(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            saved_evidence(root)
            destination = root / 'new-index'
            summary = reconstruct(root, destination)
            self.assertEqual((summary['static_arms'], summary['motion_arms'],
                              summary['segment_rows'], summary['new_baseline_arms']),
                             (7, 4, 259, 0))
            records = [json.loads(line) for line in
                       (destination / 'results.jsonl').read_text().splitlines()]
            self.assertEqual(records[0]['run_id'],
                             'legacy:soma-correspondence-audit:smplx_g1_spine1')
            self.assertEqual(records[0]['segments'][0]['precision'], 0.5)
            self.assertTrue(all(r['cohort_status'] == 'legacy' and
                                r['reproducibility'] == 'not_rerun' for r in records))
            self.assertTrue(verify_bundle(destination, root)['passed'])

    def test_file_ready_plan_can_only_reserve_a_non_executing_receipt(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            plan = plan_fixture(root)
            original = copy.deepcopy(plan)
            report = inspect_plan(plan, root)
            self.assertTrue(report['file_ready'])
            self.assertFalse(report['execution_ready'])
            self.assertEqual(plan, original)
            write(root / 'plan.json', plan)
            destination = reserve(root / 'plan.json', root, root / 'runs')
            receipt = json.loads((destination / 'receipt.json').read_text())
            self.assertEqual(receipt['state'], 'prepared_only')
            self.assertEqual(receipt['stages_executed'], [])
            self.assertFalse(receipt['execution_ready'])
            self.assertTrue(verify_bundle(destination, root)['passed'])
            self.assertFalse((destination / 'result.json').exists())

    def test_reconstruction_refuses_overwrite_and_preserves_destination(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            destination = root / 'occupied'
            destination.mkdir()
            (destination / 'saved.txt').write_text('keep')
            with self.assertRaises(FileExistsError):
                reconstruct(root, destination)
            self.assertEqual((destination / 'saved.txt').read_text(), 'keep')
            self.assertEqual(list(destination.iterdir()), [destination / 'saved.txt'])

    def test_invalid_saved_json_fails_before_publishing(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            saved_evidence(root)
            source = root / 'experiments/soma-correspondence-audit/results.json'
            source.write_text('{"duplicate": 1, "duplicate": 2}')
            with self.assertRaisesRegex(ValueError, 'Duplicate JSON key'):
                reconstruct(root, root / 'new-index')
            self.assertFalse((root / 'new-index').exists())

    def test_retrospective_reconstruction_cannot_claim_a_tested_rerun(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            saved_evidence(root)
            reconstruct(root, root / 'new-index')
            record = json.loads((root / 'new-index/results.jsonl').read_text().splitlines()[0])
            record['reproducibility'] = 'tested_rerun'
            with self.assertRaisesRegex(ValueError, 'Retrospective'):
                validate(record, 'result')

    def test_sealed_bundle_reports_source_drift_and_output_tampering(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            saved_evidence(root)
            destination = root / 'new-index'
            reconstruct(root, destination)
            implementation = json.loads((destination / 'implementation.json').read_text())
            paths = [row['path'] for row in implementation['sources']]
            self.assertTrue(any(p.endswith('motion_studio/evidence/_legacy.py') for p in paths))
            source = root / 'experiments/soma-correspondence-audit/results.json'
            source.write_text('{}')
            (destination / 'summary.json').write_text('{}')
            (destination / 'extra.txt').write_text('unsealed')
            verification = verify_bundle(destination, root)
            self.assertFalse(verification['passed'])
            self.assertIn('Changed sources: experiments/soma-correspondence-audit/results.json',
                          verification['errors'])
            self.assertIn('Changed outputs: summary.json', verification['errors'])
            self.assertIn('Unsealed output: extra.txt', verification['errors'])

    def test_preflight_blocks_drift_and_reservation_does_not_create_outputs(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            plan = plan_fixture(root)
            write(root / 'plan.json', plan)
            (root / 'input.txt').write_text('changed input')
            report = inspect_plan(plan, root)
            self.assertFalse(report['file_ready'])
            self.assertFalse(report['execution_ready'])
            self.assertTrue(any('Hash mismatch' in row['detail'] for row in report['checks']))
            with self.assertRaisesRegex(ValueError, 'Preflight blocked'):
                reserve(root / 'plan.json', root, root / 'runs')
            self.assertFalse((root / 'runs').exists())

    def test_invalid_plan_cannot_escape_the_future_run(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            plan = plan_fixture(root)
            plan['stages'][0]['outputs'] = ['../outside.json']
            write(root / 'plan.json', plan)
            with self.assertRaisesRegex(ValueError, 'relative to the future run'):
                reserve(root / 'plan.json', root, root / 'runs')
            self.assertFalse((root / 'runs').exists())

    def test_static_report_rejects_precision_using_a_different_denominator(self):
        document = static_row()
        document['per_segment'][0]['zone_precision'] = 0.25
        with self.assertRaisesRegex(ValueError, 'denominator'):
            validate_static_result(document)


if __name__ == '__main__':
    unittest.main()
