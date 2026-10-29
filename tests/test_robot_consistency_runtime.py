"""Analytic fixture pairs in an explicitly selected existing MuJoCo runtime."""
CHECK_TIER = 'robot-static'
CHECK_MODULES = ('mujoco', 'numpy')

import json
import sys
import unittest
from robot_pair_fixture import PairFixture
from motion_studio.robots import compare_representations


class RuntimeConsistencyTest(unittest.TestCase):
    def report(self,fixture):
        return compare_representations('fixture',fixture.roots,poses=('zero','bent'),
            definitions_root=fixture.catalog,runtime_python=sys.executable)

    def test_analytic_mass_com_and_ninety_degree_bent_pose(self):
        r=self.report(PairFixture(self))
        self.assertTrue(r.supports('named_frames'),r.findings)
        self.assertTrue(r.supports('inertial_totals'),r.findings)
        self.assertTrue(r.supports('collision_geometry_equality'),r.findings)
        records=[json.loads(f.detail.split(': ',1)[1]) for f in r.findings if f.check=='inertial_totals']
        self.assertAlmostEqual(records[0]['masses_kg'][0],2.1)
        # root mass at (0,0), arm at (1,0), tip at (2,0) / (1,1).
        for observed,expected in zip(records[0]['com_world_m'][0],(1.2/2.1,0,0)):
            self.assertAlmostEqual(observed,expected)
        for observed,expected in zip(records[1]['com_world_m'][0],(1.1/2.1,.1/2.1,0)):
            self.assertAlmostEqual(observed,expected)

        self.assertAlmostEqual(records[0]['inertia_world_com_kg_m2'][0][1][1],.21+5/7)
        self.assertAlmostEqual(records[1]['inertia_world_com_kg_m2'][0][0][1],-1/21)

    def test_deliberate_named_frame_shift_is_incompatible(self):
        # Shift the arm origin, keeping root qpos explicitly selected.
        f=PairFixture(self);path=f.source/'model.xml'
        path.write_text(path.read_text().replace('name="arm" pos="1 0 0"','name="arm" pos="1.25 0 0"'))
        f.git('add','.');f.git('-c','user.name=Fixture','-c','user.email=fixture@example.invalid','commit','-qm','shift')
        import hashlib
        p=f.definition/'robot.json';d=json.loads(p.read_text());d['source']['revision']=f.git('rev-parse','HEAD').strip()
        d['representations']['mjcf']['files'][0]['sha256']=hashlib.sha256(path.read_bytes()).hexdigest();p.write_text(json.dumps(d))
        r=self.report(f);self.assertFalse(r.supports('named_frames'))
        record=json.loads(next(x.detail for x in r.findings if x.check=='named_frames').split(': ',1)[1])
        self.assertAlmostEqual(record['max_position_m'],.25)

    def test_unexplained_collision_change_is_not_allowlisted(self):
        r=self.report(PairFixture(self,collision_radius=.2))
        self.assertTrue(r.supports('named_frames'))
        self.assertFalse(r.supports('collision_policy'))
        self.assertFalse(r.supports('collision_geometry_equality'))

    def test_hash_bound_collision_policy_never_certifies_geometry_equality(self):
        import hashlib
        f=PairFixture(self,collision_radius=.2)
        d=json.loads((f.definition/'robot.json').read_text())
        policy=dict(schema_version=1,source_revision=d['source']['revision'],
            model_sha256={rep:v['files'][0]['sha256'] for rep,v in d['representations'].items()},
            closure_sha256={rep:hashlib.sha256(json.dumps(sorted((x['path'],x['sha256']) for x in v['files']),separators=(',',':')).encode()).hexdigest() for rep,v in d['representations'].items()},
            collision_differences=['Analytic fixture arm sphere radius .1 versus .2 m.'])
        (f.definition/'consistency.json').write_text(json.dumps(policy))
        report=self.report(f)
        self.assertTrue(report.supports('collision_policy'))
        self.assertFalse(report.supports('collision_geometry_equality'))
        policy['closure_sha256']['mjcf']='0'*64
        (f.definition/'consistency.json').write_text(json.dumps(policy))
        self.assertFalse(self.report(f).supports('collision_policy'))


if __name__ == '__main__':
    unittest.main()
