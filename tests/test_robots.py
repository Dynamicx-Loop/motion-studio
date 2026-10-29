"""Small source repositories exercise the public static selection boundary."""
from dataclasses import FrozenInstanceError
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from motion_studio.robots import RobotSelectionError, resolve_robot


class RobotSelectionTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / 'source'
        self.source.mkdir()
        self.git('init', '-q')
        self.git('config', 'user.email', 'fixture@example.invalid')
        self.git('config', 'user.name', 'Fixture')
        (self.source / 'model.xml').write_text('''<mujoco><compiler angle="radian"/>
<asset><mesh name="mesh" file="mesh.stl"/></asset><worldbody><body name="pelvis">
<freejoint/><joint name="hinge" axis="0 1 0" range="-2 2"/>
</body></worldbody></mujoco>''')
        (self.source / 'mesh.stl').write_bytes(b'fixture geometry')
        (self.source / 'SOURCE.txt').write_text('fixture provenance; rights unknown')
        self.git('add', '.')
        self.git('commit', '-qm', 'fixture')
        self.definitions = self.root / 'definitions'
        self.definition_dir = self.definitions / 'fixture'
        self.definition_dir.mkdir(parents=True)
        self.definition = {
            'schema_version': 1, 'id': 'fixture', 'version': 1,
            'source': {'key': 'fixture-source', 'repository': 'fixture://local',
                       'revision': self.git('rev-parse', 'HEAD').strip()},
            'provenance': {'license_coverage': 'unknown', 'modifications': [],
                           'files': [self.file('SOURCE.txt', 'source-record')]},
            'conventions': {'length_unit': 'metre', 'angle_unit': 'radian',
                            'up_axis': '+Z', 'forward_axis': '+X', 'left_axis': '+Y',
                            'root_frame': 'pelvis', 'root_translation_unit': 'metre',
                            'root_quaternion_order': 'wxyz'},
            'joint_order': ['hinge'],
            'representations': {'mjcf': {'model': 'model.xml',
                'root': 'free', 'files': [self.file('model.xml', 'model'),
                                         self.file('mesh.stl', 'mesh')],
                'joints': [{'name': 'hinge', 'kind': 'revolute',
                            'axis': [0, 1, 0], 'lower': -2, 'upper': 2}]}}}
        self.poses = {'schema_version': 1, 'angle_unit': 'radian',
                      'poses': {'zero': {'joints': {'hinge': 0},
                         'root_translation': [0, 0, 0],
                         'root_quaternion': [1, 0, 0, 0],
                         'root_handling': 'model-origin; no standing height'}}}
        self.save()

    def git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.source), *args],
                                       text=True, stderr=subprocess.PIPE)

    def file(self, path, role):
        return {'path': path, 'sha256': hashlib.sha256(
            (self.source / path).read_bytes()).hexdigest(), 'role': role}

    def save(self):
        (self.definition_dir / 'robot.json').write_text(json.dumps(self.definition))
        (self.definition_dir / 'poses.json').write_text(json.dumps(self.poses))

    def select(self, representation='mjcf', pose='zero'):
        return resolve_robot('fixture', representation, pose,
            {'fixture-source': self.source}, definitions_root=self.definitions)

    def test_pose_rejects_incomplete_unknown_nonfinite_and_out_of_limit_values(self):
        for values in ({}, {'other': 0}, {'hinge': float('nan')},
                       {'hinge': float('inf')}, {'hinge': 2.1}, {'hinge': True}):
            with self.subTest(values=values):
                self.poses['poses']['zero']['joints'] = values
                self.save()
                with self.assertRaisesRegex(RobotSelectionError, 'pose|Pose'):
                    self.select()

    def test_duplicate_json_fields_and_invalid_root_data_are_rejected(self):
        path = self.definition_dir / 'poses.json'
        path.write_text('{"schema_version": 1, "schema_version": 1}')
        with self.assertRaisesRegex(RobotSelectionError, 'Duplicate.*schema_version'):
            self.select()
        self.save()
        self.poses['poses']['zero']['root_quaternion'] = [0, 0, 0, 0]
        self.save()
        with self.assertRaisesRegex(RobotSelectionError, 'unit.*quaternion'):
            self.select()

    def test_explicit_base_pose_overlay_maps_to_complete_ordered_values(self):
        self.poses['poses']['bent'] = {'base': 'zero', 'joints': {'hinge': 1.5}}
        self.save()
        selection = self.select(pose='bent')
        self.assertEqual(selection.pose_values, (1.5,))
        self.assertNotEqual(selection.identity, self.select().identity)
        self.poses['poses']['zero']['base'] = 'bent'
        self.save()
        with self.assertRaisesRegex(RobotSelectionError, 'Cyclic pose'):
            self.select()

    def test_missing_include_and_uncommitted_wrapper_cannot_be_selected(self):
        path = self.source / 'model.xml'
        path.write_text(path.read_text().replace('<asset>', '<include file="missing.xml"/><asset>'))
        self.git('add', '.')
        self.git('commit', '-qm', 'missing include reference')
        self.definition['source']['revision'] = self.git('rev-parse', 'HEAD').strip()
        self.definition['representations']['mjcf']['files'][0] = self.file('model.xml', 'model')
        self.save()
        with self.assertRaisesRegex(RobotSelectionError, 'closure.*missing.xml'):
            self.select()
        self.definition['representations']['mjcf']['files'].append(
            {'path': 'missing.xml', 'sha256': '0' * 64, 'role': 'include'})
        self.save()
        with self.assertRaisesRegex(RobotSelectionError, 'missing.xml'):
            self.select()
        (self.source / 'missing.xml').write_text('<mujocoinclude/>')
        self.definition['representations']['mjcf']['files'][-1] = self.file('missing.xml', 'include')
        self.save()
        with self.assertRaisesRegex(RobotSelectionError, 'not committed.*missing.xml'):
            self.select()

    def test_duplicate_closure_entries_are_not_silently_deduplicated(self):
        files = self.definition['representations']['mjcf']['files']
        files.append(files[1])
        self.save()
        with self.assertRaisesRegex(RobotSelectionError, 'Duplicate.*source path'):
            self.select()

    def test_native_order_and_application_order_are_related_by_names(self):
        path = self.source / 'model.xml'
        path.write_text(path.read_text().replace('</body>',
            '<body name="child"><joint name="other" axis="1 0 0" range="-1 1"/></body></body>'))
        self.git('add', '.')
        self.git('commit', '-qm', 'second native joint')
        self.definition['source']['revision'] = self.git('rev-parse', 'HEAD').strip()
        model = self.definition['representations']['mjcf']
        model['files'][0] = self.file('model.xml', 'model')
        model['joints'].append({'name': 'other', 'kind': 'revolute',
                                'axis': [1, 0, 0], 'lower': -1, 'upper': 1})
        self.definition['joint_order'] = ['other', 'hinge']
        self.poses['poses']['zero']['joints'] = {'hinge': 1.5, 'other': -0.5}
        self.save()
        selection = self.select()
        self.assertEqual(selection.native_joint_names, ('hinge', 'other'))
        self.assertEqual(selection.joint_names, ('other', 'hinge'))
        self.assertEqual(selection.pose_values, (-0.5, 1.5))

    def test_escaping_symlink_and_unknown_pose_fields_fail(self):
        external = self.root / 'outside.stl'
        external.write_bytes(b'fixture geometry')
        (self.source / 'mesh.stl').unlink()
        (self.source / 'mesh.stl').symlink_to(external)
        with self.assertRaisesRegex(RobotSelectionError, 'escapes root'):
            self.select()
        (self.source / 'mesh.stl').unlink()
        (self.source / 'mesh.stl').write_bytes(b'fixture geometry')
        self.poses['poses']['zero']['joint'] = {'hinge': 0}
        self.save()
        with self.assertRaisesRegex(RobotSelectionError, 'Unknown pose fields.*joint'):
            self.select()
        del self.poses['poses']['zero']['joint']
        self.poses['poses']['zero']['representations'] = ['urdf']
        self.save()
        with self.assertRaisesRegex(RobotSelectionError, 'does not support mjcf'):
            self.select()

    def test_source_references_and_joint_metadata_are_checked_independently(self):
        self.definition['representations']['mjcf']['files'].pop()
        self.save()
        with self.assertRaisesRegex(RobotSelectionError, 'closure.*mesh.stl'):
            self.select()
        self.definition['representations']['mjcf']['files'].append(self.file('mesh.stl', 'mesh'))
        self.definition['representations']['mjcf']['joints'][0]['axis'] = [1, 0, 0]
        self.save()
        with self.assertRaisesRegex(RobotSelectionError, 'hinge.*axis'):
            self.select()

    def test_application_order_must_cover_each_native_joint_once(self):
        for order in ([], ['hinge', 'hinge'], ['unknown']):
            with self.subTest(order=order):
                self.definition['joint_order'] = order
                self.save()
                with self.assertRaisesRegex(RobotSelectionError, 'joint_order'):
                    self.select()

    def test_missing_and_drifted_required_assets_fail_before_writing(self):
        (self.source / 'mesh.stl').unlink()
        with self.assertRaisesRegex(RobotSelectionError, 'mesh.stl'):
            self.select()
        (self.source / 'mesh.stl').write_bytes(b'changed')
        with self.assertRaisesRegex(RobotSelectionError, 'hash drift.*mesh.stl'):
            self.select()
        self.git('add', '.')
        self.git('commit', '-qm', 'different revision')
        with self.assertRaisesRegex(RobotSelectionError, 'commit drift'):
            self.select()

    def test_unsupported_selection_and_paths_are_actionable(self):
        with self.assertRaisesRegex(RobotSelectionError, 'Unsupported representation.*usd'):
            self.select('usd')
        self.definition['representations']['mjcf']['files'][1]['path'] = '../escape.stl'
        self.save()
        with self.assertRaisesRegex(RobotSelectionError, 'relative.*path|escape'):
            self.select()
        with self.assertRaisesRegex(RobotSelectionError, 'definition ID'):
            resolve_robot('../fixture', 'mjcf', 'zero', {},
                          definitions_root=self.definitions)

    def test_selection_is_immutable_and_relocation_does_not_change_identity(self):
        selection = self.select()
        self.assertEqual(selection.joint_names, ('hinge',))
        self.assertEqual(selection.pose_values, (0.0,))
        self.assertEqual(selection.native_joint_names, ('hinge',))
        self.assertEqual(selection.root_pose.translation, (0.0, 0.0, 0.0))
        self.assertEqual(selection.model_path, self.source / 'model.xml')
        self.assertEqual(selection.static_validation, 'validated')
        self.assertEqual(selection.runtime_validation, 'unverified')
        with self.assertRaises(FrozenInstanceError):
            selection.identity = 'changed'
        moved = self.root / 'moved'
        shutil.copytree(self.source, moved)
        (moved / 'generated-floating.xml').write_text('unrelated')
        (moved / 'untracked.txt').write_text('not selected')
        relocated = resolve_robot('fixture', 'mjcf', 'zero',
            {'fixture-source': moved}, definitions_root=self.definitions)
        self.assertEqual(relocated.identity, selection.identity)
        self.assertEqual({p.name for p in self.source.iterdir()},
                         {'.git', 'model.xml', 'mesh.stl', 'SOURCE.txt'})


if __name__ == '__main__':
    unittest.main()
