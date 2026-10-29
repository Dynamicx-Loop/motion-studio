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

    def test_same_bounds_different_meshes_cannot_support_required_claims(self):
        import hashlib
        from motion_studio.robots import RobotSelectionError
        from motion_studio.integrations.umr_canonical import CanonicalInputs, prepare_canonical_comparison
        f=PairFixture(self)
        for part in ['u','m']:(f.source/part).mkdir()
        cube='''v -1 -1 -1
       v 1 -1 -1
       v 1 1 -1
       v -1 1 -1
       v -1 -1 1
       v 1 -1 1
       v 1 1 1
       v -1 1 1
       f 1 3 2
       f 1 4 3
       f 5 6 7
       f 5 7 8
       f 1 2 6
       f 1 6 5
       f 2 3 7
       f 2 7 6
       f 3 4 8
       f 3 8 7
       f 4 1 5
       f 4 5 8
       '''
        octa='''v -1 0 0
       v 1 0 0
       v 0 -1 0
       v 0 1 0
       v 0 0 -1
       v 0 0 1
       f 1 3 5
       f 3 2 5
       f 2 4 5
       f 4 1 5
       f 1 6 3
       f 3 6 2
       f 2 6 4
       f 4 6 1
       '''
        (f.source/'u/surface.obj').write_text(cube);(f.source/'m/surface.obj').write_text(octa)
        urdf=f.source/'model.urdf';urdf.write_text(urdf.read_text().replace('<sphere radius=".1"/>','<mesh filename="u/surface.obj"/>'))
        xml=f.source/'model.xml';xml.write_text(xml.read_text().replace('<worldbody>','<asset><mesh name="surface" file="m/surface.obj"/></asset><worldbody>').replace('<geom type="sphere" size="0.1"/>','<geom type="mesh" mesh="surface"/>'))
        f.git('add','.');f.git('-c','user.name=Fixture','-c','user.email=fixture@example.invalid','commit','-qm','different surfaces same bounds')
        d=json.loads((f.definition/'robot.json').read_text());d['source']['revision']=f.git('rev-parse','HEAD').strip()
        for rep,mesh in [('urdf','u/surface.obj'),('mjcf','m/surface.obj')]:
         d['representations'][rep]['files'].append(dict(path=mesh,role='mesh',sha256=''))
         for entry in d['representations'][rep]['files']:entry['sha256']=hashlib.sha256((f.source/entry['path']).read_bytes()).hexdigest()
        (f.definition/'robot.json').write_text(json.dumps(d))
        report=self.report(f)
        for claim in ('collision_policy','collision_geometry_equality'):
            self.assertFalse(report.supports(claim))
            with self.assertRaises(RobotSelectionError):
                report.require_supported((claim,))
        inputs=f.root/'inputs'; inputs.mkdir()
        for name in ('clip.npz','shape.json','neutral.pkl'):
            (inputs/name).write_bytes(b'fixture')
        with self.assertRaises(ValueError):
            prepare_canonical_comparison('fixture','mjcf','zero',
                CanonicalInputs(inputs/'clip.npz',inputs/'shape.json',(inputs/'neutral.pkl',),30),
                f.root/'new-run',f.roots,definitions_root=f.catalog,
                representation_report=report,required_claims=('collision_policy',))
        self.assertFalse((f.root/'new-run').exists())

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
