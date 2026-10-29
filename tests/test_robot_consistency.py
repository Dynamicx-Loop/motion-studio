"""Pure public pair comparison: no scientific runtime imported."""
import unittest
from robot_pair_fixture import PairFixture
from motion_studio.robots import compare_representations, RobotSelectionError


class ConsistencyTest(unittest.TestCase):
    def report(self,fixture,**kwargs):
        return compare_representations('fixture',fixture.roots,poses=('zero','bent'),definitions_root=fixture.catalog,**kwargs)

    def test_previous_report_semantics_cannot_certify_claims(self):
        from dataclasses import replace
        from motion_studio.robots import ConsistencyFinding
        report=replace(self.report(PairFixture(self)),schema_version=1,
            findings=(ConsistencyFinding('collision_policy','supported','old mesh bounds'),))
        self.assertFalse(report.supports('collision_policy'))
        self.assertEqual(report.status,'unverified')
        with self.assertRaises(RobotSelectionError):
            report.require_supported(('collision_policy',))

    def test_static_success_does_not_certify_runtime_claims(self):
        f=PairFixture(self);report=self.report(f)
        self.assertEqual(report.status,'unverified')
        self.assertTrue(report.supports('joint_metadata'))
        self.assertFalse(report.supports('named_frames'))
        with self.assertRaisesRegex(RobotSelectionError,'named_frames'):
            report.require_supported(('named_frames',))
        self.assertEqual(len(report.identities),4)
        self.assertEqual(len(set(report.identities)),4)

    def test_deliberate_physical_limit_difference_blocks_joint_claim(self):
        f=PairFixture(self,limit=1.9);report=self.report(f)
        self.assertEqual(report.status,'incompatible')
        with self.assertRaisesRegex(RobotSelectionError,'joint_metadata'):
            report.require_supported(('joint_metadata',))

    def test_unavailable_runtime_does_not_certify_frames(self):
        f=PairFixture(self)
        report=self.report(f,runtime_python='/bin/false')
        self.assertEqual(report.status,'unverified')
        self.assertFalse(report.supports('named_frames'))


if __name__ == '__main__':
    unittest.main()
