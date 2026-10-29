"""The comparison G1 is an explicit selection with an explicit source requirement."""
import unittest

from motion_studio.robots import RobotSelectionError, resolve_robot


class G1DefinitionTests(unittest.TestCase):
    def test_g1_selection_requires_official_umr_source(self):
        for representation in ('mjcf', 'urdf'):
            with self.subTest(representation=representation):
                with self.assertRaisesRegex(RobotSelectionError, "Supply source_roots\\['UMR'\\]"):
                    resolve_robot('g1_29dof', representation, 'tpose', {})


if __name__ == '__main__':
    unittest.main()
