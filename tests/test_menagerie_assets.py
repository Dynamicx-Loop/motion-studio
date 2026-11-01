"""Portable snapshots preserve committed source and refuse unsupported changes."""
import hashlib
from pathlib import Path
import subprocess
import tempfile
import unittest

from motion_studio.integrations.menagerie_assets import (
    COLLISIONS, ENTRY, LICENSES, SOURCE_ENTRY, astro_catalog, portable_astro, snapshot_astro,
)
from motion_studio.studio import StudioError


class AstroSnapshotTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.checkout = self.root / 'upstream'
        source = self.checkout / 'astro_p2'
        (source / 'assets').mkdir(parents=True)
        (source / 'assets' / 'body.stl').write_bytes(b'fixture mesh')
        for name in LICENSES:
            (source / name).write_text(f'Fixture notice {name}\n')
        compiler = '<compiler angle="radian" inertiafromgeom="false" fusestatic="false"/>'
        (source / COLLISIONS[0]).write_text('<mujoco>' + compiler +
            '<worldbody><body name="foot_link"><geom name="sole" type="box" size=".1 .1 .01"/>'
            '</body></worldbody></mujoco>')
        (source / COLLISIONS[1]).write_text('<mujoco>' + compiler +
            '<worldbody><geom name="handle" type="capsule" size=".01" fromto="0 0 0 0 .1 0"/>'
            '</worldbody></mujoco>')
        joints = ''.join(f'<joint name="{name}" range="-2 2"/>' for name in (
            'left_shoulder_roll_joint', 'right_shoulder_roll_joint', 'left_elbow_joint', 'right_elbow_joint'))
        (source / SOURCE_ENTRY).write_text('<mujoco model="astro_p2">' + compiler.replace('/>', ' meshdir="assets"/>') +
            '<asset><model name="feet" file="foot_collisions.xml"/>'
            '<model name="neck" file="neck_handle_collisions.xml"/>'
            '<mesh name="body" file="body.stl"/></asset><worldbody><body name="pelvis">'
            '<joint name="root" type="free"/><body name="waist_roll_link">' + joints +
            '<attach model="feet" body="foot_link" prefix="left_"/>'
            '<attach model="feet" body="foot_link" prefix="right_"/>'
            '<attach model="neck" prefix=""/></body></body></worldbody></mujoco>')
        self.git('init', '-q', '-b', 'main')
        self.commit()
        self.destination = self.root / 'assets' / 'astro'

    def git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.checkout), *args], stderr=subprocess.PIPE)

    def commit(self):
        self.git('add', '.')
        self.git('-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid',
                 'commit', '-qm', 'Record fixture source')

    def test_snapshot_is_self_contained_and_preserves_source_and_collision_ownership(self):
        manifest = snapshot_astro(self.checkout, self.destination)
        self.assertEqual(manifest['source']['revision'], self.git('rev-parse', 'HEAD').decode().strip())
        for name, expected in manifest['source']['files_sha256'].items():
            self.assertEqual((self.destination / name).read_bytes(), (self.checkout / 'astro_p2' / name).read_bytes())
            self.assertEqual(hashlib.sha256((self.destination / name).read_bytes()).hexdigest(), expected)
        import xml.etree.ElementTree as ET
        root = ET.parse(self.destination / ENTRY).getroot()
        self.assertEqual(list(root.iter('attach')), [])
        self.assertEqual(list(root.iter('model')), [])
        self.assertIsNotNone(root.find('.//body[@name="left_foot_link"]/geom[@name="left_sole"]'))
        self.assertIsNotNone(root.find('.//body[@name="right_foot_link"]/geom[@name="right_sole"]'))
        self.assertIsNotNone(root.find('.//body[@name="waist_roll_link"]/geom[@name="handle"]'))
        self.assertEqual(self.git('status', '--porcelain'), b'')
        # Reading the built-in does not need the original checkout or Git metadata.
        import shutil
        shutil.rmtree(self.checkout)
        with portable_astro(self.destination) as (path, pose, originals):
            self.assertEqual(path, self.destination / ENTRY)
            self.assertEqual(pose['torso_body'], 'waist_roll_link')
            self.assertTrue(all(path.is_file() for path in originals.values()))

    def test_existing_destination_dirty_source_and_source_overlap_are_refused(self):
        snapshot_astro(self.checkout, self.destination)
        with self.assertRaisesRegex(ValueError, 'already exists'):
            snapshot_astro(self.checkout, self.destination)
        source = self.checkout / 'astro_p2' / SOURCE_ENTRY
        source.write_text(source.read_text() + '\n<!--local edit-->')
        with self.assertRaisesRegex(ValueError, 'differs from committed'):
            snapshot_astro(self.checkout, self.root / 'dirty')
        with self.assertRaisesRegex(ValueError, 'outside the source'):
            snapshot_astro(self.checkout, self.checkout / 'new-assets')
        self.assertFalse((self.root / 'dirty').exists())

    def test_new_collision_joint_semantics_require_an_explicit_conversion(self):
        path = self.checkout / 'astro_p2' / COLLISIONS[0]
        path.write_text(path.read_text().replace('<geom', '<joint name="unexpected"/><geom'))
        self.commit()
        with self.assertRaisesRegex(ValueError, 'geom-only'):
            snapshot_astro(self.checkout, self.destination)
        self.assertFalse(self.destination.exists())

    def test_changed_missing_or_escaping_snapshot_files_are_refused(self):
        snapshot_astro(self.checkout, self.destination)
        path = self.destination / 'assets/body.stl'
        original = path.read_bytes()
        path.write_bytes(b'changed')
        with self.assertRaisesRegex(StudioError, 'bytes changed'):
            with portable_astro(self.destination):
                self.fail('Changed snapshot was accepted')
        path.unlink()
        outside = self.root / 'outside.stl'
        outside.write_bytes(original)
        path.symlink_to(outside)
        with self.assertRaisesRegex(StudioError, 'escapes'):
            with portable_astro(self.destination):
                self.fail('Escaping snapshot was accepted')
        path.unlink()
        with self.assertRaisesRegex(StudioError, 'missing'):
            with portable_astro(self.destination):
                self.fail('Missing snapshot was accepted')

    def test_catalog_explicitly_reports_an_unavailable_snapshot(self):
        self.assertFalse(astro_catalog(self.destination)['available'])
        snapshot_astro(self.checkout, self.destination)
        entry = astro_catalog(self.destination)
        self.assertEqual((entry['id'], entry['name']), ('astro', 'Astro P2'))
        self.assertTrue(entry['available'])


if __name__ == '__main__':
    unittest.main()
