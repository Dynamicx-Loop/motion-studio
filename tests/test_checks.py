"""Root check outcomes against tiny independent projects, never recursive discovery."""
from pathlib import Path
import json
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from motion_studio.checks import check, discover


class RootCheckTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.root = Path(self.folder.name)

    def write_suite(self, path, source):
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(source)
        return target

    def test_new_owned_suite_is_discovered_and_run_without_registration(self):
        self.write_suite('tests/test_new_behavior.py', '''import unittest
class Behavior(unittest.TestCase):
    def test_literal_expectation(self):
        self.assertEqual('motion'.upper(), 'MOTION')
''')
        report = check(self.root)
        self.assertEqual(report.exit_code, 0)
        self.assertEqual([(r.path, r.status) for r in report.outcomes],
                         [('tests/test_new_behavior.py', 'passed')])

    def test_empty_discovery_is_not_reported_as_passing(self):
        report = check(self.root)
        self.assertNotEqual(report.exit_code, 0)
        self.assertIn('No owned checks discovered', report.outcomes[0].detail)

    def test_reader_package_relative_imports_work(self):
        self.write_suite('scripts/reader/known.py', "EXPECTED = 37\n")
        self.write_suite('scripts/reader/test_known.py', '''import unittest
from .known import EXPECTED
class Reading(unittest.TestCase):
    def test_known_value(self):
        self.assertEqual(EXPECTED, 37)
''')
        report = check(self.root)
        self.assertEqual(report.exit_code, 0, report.outcomes)

    def test_empty_suite_is_not_reported_as_passing(self):
        self.write_suite('tests/test_empty.py', '"""Not an actual test."""\n')
        report = check(self.root)
        self.assertNotEqual(report.exit_code, 0)
        self.assertIn('No tests loaded', report.outcomes[0].detail)

    def test_saved_evidence_is_inventoried_without_import_and_unavailable_if_missing(self):
        self.write_suite('tests/test_small.py', '''import unittest
class Small(unittest.TestCase):
    def test_good(self): self.assertTrue(True)
''')
        self.write_suite('scripts/test_evidence.py', '''CHECK_TIER = 'saved-evidence'
CHECK_INPUTS = ('records/frozen.json',)
raise RuntimeError('Inventory must not import this module')
''')
        default = check(self.root)
        self.assertEqual(default.exit_code, 0)
        self.assertEqual({r.path: r.status for r in default.outcomes}, {
            'tests/test_small.py': 'passed',
            'scripts/test_evidence.py': 'not-selected'})
        evidence = check(self.root, tiers=('saved-evidence',))
        self.assertNotEqual(evidence.exit_code, 0)
        result = next(r for r in evidence.outcomes if r.tier == 'saved-evidence')
        self.assertEqual(result.status, 'unavailable')
        self.assertIn('records/frozen.json', result.detail)

    def test_unknown_tier_cannot_hide_an_owned_suite(self):
        self.write_suite('tests/test_hidden.py', "CHECK_TIER = 'purre'\n")
        with self.assertRaisesRegex(ValueError, 'Unknown check tier'):
            discover(self.root)

    def test_static_tier_requires_explicit_existing_runtime_and_run(self):
        self.write_suite('scripts/test_static.py', '''CHECK_TIER = 'umr-static'
CHECK_RUN_INPUTS = ('frozen.json',)
import sys, unittest
run = sys.argv.pop(1)
class Frozen(unittest.TestCase):
    def test_selected_run(self): self.assertTrue(run.endswith('saved-run'))
if __name__ == '__main__': unittest.main()
''')
        absent = check(self.root, tiers=('umr-static',))
        self.assertEqual(absent.outcomes[0].status, 'unavailable')
        run = self.root / 'saved-run'
        run.mkdir()
        incomplete = check(self.root, tiers=('umr-static',),
                           umr_python=Path(sys.executable), umr_run=run)
        self.assertEqual(incomplete.outcomes[0].status, 'unavailable')
        (run / 'frozen.json').write_text('{}')
        actual = check(self.root, tiers=('umr-static',),
                       umr_python=Path(sys.executable), umr_run=run)
        self.assertEqual(actual.exit_code, 0, actual.outcomes)

    def test_robot_static_tier_requires_an_explicit_existing_interpreter(self):
        self.write_suite('tests/test_robot.py', """CHECK_TIER = 'robot-static'
import unittest
class Robot(unittest.TestCase):
    def test_selected_runtime(self): self.assertTrue(True)
""")
        missing = check(self.root, tiers=('robot-static',))
        self.assertEqual(missing.outcomes[0].status, 'unavailable')
        selected = check(self.root, tiers=('robot-static',),
                         robot_python=Path(sys.executable))
        self.assertEqual(selected.exit_code, 0, selected.outcomes)

    def test_javascript_check_is_visible_and_requires_declared_saved_bundle(self):
        self.write_suite('scripts/test_search.cjs',
                         '// CHECK_INPUTS: ["records/search.html"]\nprocess.exit(0);\n')
        suites = discover(self.root)
        self.assertEqual([(s.path, s.tier) for s in suites],
                         [('scripts/test_search.cjs', 'javascript')])
        result = check(self.root, tiers=('javascript',))
        self.assertEqual(result.outcomes[0].status, 'unavailable')
        self.assertIn('records/search.html', result.outcomes[0].detail)

    def test_missing_runtime_package_is_unavailable_before_test_import(self):
        self.write_suite('tests/test_package.py', '''CHECK_TIER = 'saved-evidence'
CHECK_MODULES = ('motion_studio_missing_fixture_package',)
raise RuntimeError('Do not import with missing prerequisites')
''')
        report = check(self.root, tiers=('saved-evidence',))
        self.assertEqual(report.outcomes[0].status, 'unavailable')
        self.assertIn('motion_studio_missing_fixture_package', report.outcomes[0].detail)

    def test_cli_propagates_selected_suite_failure(self):
        self.write_suite('tests/test_failure.py', '''import unittest
class Failure(unittest.TestCase):
    def test_literal_disagreement(self): self.assertEqual(37, 41)
''')
        cli = Path(__file__).resolve().parents[1] / 'scripts/check.py'
        result = subprocess.run([sys.executable, str(cli), '--root', str(self.root),
                                 '--json'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 1, result.stderr)
        output = json.loads(result.stdout)
        self.assertEqual(output['outcomes'][0]['status'], 'failed')
        self.assertIn('37 != 41', output['outcomes'][0]['detail'])

    def test_selected_docs_edition_needs_no_historical_bundle(self):
        # Stand-in executable at the process boundary keeps this test pure.
        # The harmless string carries the same inventory metadata as real search.
        self.write_suite('scripts/docs_site/test_search.cjs', '''"""
// CHECK_INPUTS: ["outputs/umr-binding-report/supporting-records.html"]
"""
import pathlib, sys
assert sys.argv[1] == '--output'
assert pathlib.Path(sys.argv[2], 'supporting-records.html').read_text() == 'Selected edition'
''')
        selected = self.root / 'outputs/docs-site/selected'
        selected.mkdir(parents=True)
        (selected / 'supporting-records.html').write_text('Selected edition')
        with patch('motion_studio.checks.shutil.which', return_value=sys.executable):
            result = check(self.root, tiers=('javascript',), docs_edition=selected)
        self.assertEqual(result.exit_code, 0, result.outcomes)
        absent = check(self.root, tiers=('javascript',), docs_edition=self.root / 'missing')
        self.assertEqual(absent.outcomes[0].status, 'unavailable')
        self.assertNotEqual(absent.exit_code, 0)
        self.assertIn('missing/supporting-records.html', absent.outcomes[0].detail)


if __name__ == '__main__':
    unittest.main()
