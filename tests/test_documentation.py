"""Documentation publication behavior through the owned build operation."""
import tempfile
import json
import re
import shutil
import os
import subprocess
import sys
from pathlib import Path
import unittest

from motion_studio.documentation import build_edition, verify_edition


REPOSITORY = Path(__file__).resolve().parents[1]


def fixture(root):
    """Small worked saved-evidence cohort; no generated media dependencies."""
    shutil.copytree(REPOSITORY / 'docs/site', root / 'docs/site')
    references = set()
    for template in (root / 'docs/site').rglob('*.html'):
        references.update(re.findall(r'\{\{DOC:([^}]+)\}\}', template.read_text()))
    catalog = {'snapshot_date': '2026-10-29', 'timeline': [], 'documents': []}
    for number, path in enumerate(sorted(references)):
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text('# Saved record\n\n' + 'Recorded evidence. ' * 100)
        catalog['documents'].append({'id': f'record-{number}', 'path': path,
            'title': 'Saved record', 'description': 'Saved evidence', 'state': 'reference'})
    (root / 'docs/site/catalog.json').write_text(json.dumps(catalog))
    for path in ('scripts/build_docs.py', 'scripts/verify_docs.py', 'scripts/docs_site/test_search.cjs'):
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text('fixture source')
    return root


class DocumentationPublicationTests(unittest.TestCase):
    def test_alias_and_physical_edition_verify_identical_destinations(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root = fixture(base / 'workspace')
            result = build_edition(root, root, edition='first')
            physical = base / 'preserved-edition'
            result.output.rename(physical)
            result.output.symlink_to(physical, target_is_directory=True)
            expected = verify_edition(result.output)
            self.assertEqual(verify_edition(physical), expected)
            # Publication hashes still guard the actual root entry bytes.
            (root / 'docs.html').write_text((root / 'docs.html').read_text() + 'changed')
            with self.assertRaises(AssertionError):
                verify_edition(physical)

    def test_cli_uses_current_source_workspace_after_handoff(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root = fixture(base / 'build-workspace')
            script = root / 'scripts/verify_docs.py'
            shutil.copyfile(REPOSITORY / 'scripts/verify_docs.py', script)
            evidence = base / 'stable-evidence'
            evidence.mkdir()
            build_edition(root, evidence, edition='first')
            current = base / 'current-workspace'
            root.rename(current)
            environment = {**os.environ, 'PYTHONPATH': str(REPOSITORY),
                           'PYTHONDONTWRITEBYTECODE': '1'}
            result = subprocess.run([sys.executable, str(current / 'scripts/verify_docs.py'),
                                     '--edition', 'first'], env=environment,
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(json.loads(result.stdout)['new_experiments_run'], 0)

    def test_missing_inputs_leave_working_entries_and_edition_intact(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'docs/site').mkdir(parents=True)
            for name in ('docs.html', 'docs-basic.html', 'docs/site/home.html'):
                (root / name).write_text('Preserved complete reading entry: ' + name)
            old = root / 'outputs/docs-site/previous'
            old.mkdir(parents=True)
            (old / 'docs.html').write_text('Previous edition')
            with self.assertRaises(FileNotFoundError):
                build_edition(root, root, edition='new')
            self.assertEqual((root / 'docs.html').read_text(),
                             'Preserved complete reading entry: docs.html')
            self.assertEqual((old / 'docs.html').read_text(), 'Previous edition')
            self.assertFalse((root / 'outputs/docs-site/new').exists())

    def test_build_excludes_legacy_bundle_and_preserves_complete_old_entries(self):
        with tempfile.TemporaryDirectory() as directory:
            root = fixture(Path(directory))
            old_report = root / 'outputs/umr-binding-report/index.html'
            old_report.parent.mkdir(parents=True)
            old_report.write_text('Historical report')
            (root / 'docs.html').write_text('<html><body>Prior complete overview</body></html>')
            result = build_edition(root, root, edition='first')
            manifest = json.loads(result.manifest.read_text())
            self.assertFalse((result.output / 'index.html').exists())
            self.assertFalse((result.output / 'inspectors').exists())
            self.assertEqual(old_report.read_text(), 'Historical report')
            self.assertEqual((result.output / manifest['preserved_entries']['docs.html']['archive']).read_text(),
                             '<html><body>Prior complete overview</body></html>')
            self.assertIn('outputs/docs-site/first/installation.html', (root / 'docs.html').read_text())
            self.assertNotIn('<script', (root / 'docs/site/home.html').read_text())
            self.assertEqual(verify_edition(result.output)['missing_fragments'], [])

    def test_saved_sources_are_explicit_checked_and_visibly_labeled(self):
        with tempfile.TemporaryDirectory() as directory:
            root = fixture(Path(directory))
            first = build_edition(root, root, edition='first')
            catalog = json.loads((root / 'docs/site/catalog.json').read_text())
            missing = catalog['documents'][0]['path']
            (root / missing).unlink()
            current = (root / 'docs.html').read_bytes()
            with self.assertRaises(FileNotFoundError):
                build_edition(root, root, edition='missing')
            self.assertEqual((root / 'docs.html').read_bytes(), current)
            saved = build_edition(root, root, edition='saved', saved_edition=first.output)
            manifest = json.loads(saved.manifest.read_text())
            self.assertIn(missing, manifest['reused_source_snapshots'])
            self.assertIn('Saved evidence edition', (root / 'docs.html').read_text())
            self.assertEqual(verify_edition(saved.output)['reused_source_snapshots_verified'], 1)
            (first.output / 'documentation/sources' / missing).write_text('corrupt snapshot')
            current = (root / 'docs.html').read_bytes()
            with self.assertRaisesRegex(ValueError, 'unverified saved source'):
                build_edition(root, root, edition='corrupt', saved_edition=first.output)
            self.assertEqual((root / 'docs.html').read_bytes(), current)
            self.assertFalse((root / 'outputs/docs-site/corrupt').exists())

    def test_broken_authored_navigation_fails_before_publication(self):
        with tempfile.TemporaryDirectory() as directory:
            root = fixture(Path(directory))
            (root / 'docs.html').write_text('Prior complete entry')
            template = root / 'docs/site/templates/overview.html'
            template.write_text(template.read_text() + '<a href="absent.html">Missing page</a>')
            with self.assertRaisesRegex(ValueError, 'Missing reading link'):
                build_edition(root, root, edition='broken')
            self.assertEqual((root / 'docs.html').read_text(), 'Prior complete entry')
            self.assertFalse((root / 'outputs/docs-site/broken').exists())


if __name__ == '__main__':
    unittest.main()
