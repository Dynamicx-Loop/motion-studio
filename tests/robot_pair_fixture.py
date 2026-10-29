"""Analytic two-link source pair for public consistency tests."""
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile


class PairFixture:
    def __init__(self, testcase, *, shift=0, limit=2, collision_radius=.1):
        folder=tempfile.TemporaryDirectory();testcase.addCleanup(folder.cleanup)
        self.root=Path(folder.name);self.source=self.root/'source';self.source.mkdir()
        self.catalog=self.root/'definitions';self.definition=self.catalog/'fixture';self.definition.mkdir(parents=True)
        (self.source/'model.urdf').write_text('''<robot name="fixture">
<link name="pelvis"><inertial><mass value="1"/><inertia ixx=".1" iyy=".1" izz=".1" ixy="0" ixz="0" iyz="0"/></inertial></link>
<link name="arm"><inertial><mass value="1"/><inertia ixx=".1" iyy=".1" izz=".1" ixy="0" ixz="0" iyz="0"/></inertial><collision><geometry><sphere radius=".1"/></geometry></collision></link>
<joint name="hinge" type="revolute"><parent link="pelvis"/><child link="arm"/><origin xyz="1 0 0"/><axis xyz="0 0 1"/><limit lower="-2" upper="2" effort="1" velocity="1"/></joint>
<link name="tip"><inertial><mass value=".1"/><inertia ixx=".01" iyy=".01" izz=".01" ixy="0" ixz="0" iyz="0"/></inertial></link>
<joint name="tip_fixed" type="fixed"><parent link="arm"/><child link="tip"/><origin xyz="1 0 0"/></joint></robot>''')
        (self.source/'model.xml').write_text(f'''<mujoco><compiler angle="radian" fusestatic="false" inertiafromgeom="false"/>
<worldbody><body name="pelvis" pos="{shift} 0 0"><freejoint/><inertial pos="0 0 0" mass="1" diaginertia=".1 .1 .1"/>
<body name="arm" pos="1 0 0"><joint name="hinge" axis="0 0 1" range="-2 {limit}"/><inertial pos="0 0 0" mass="1" diaginertia=".1 .1 .1"/><geom type="sphere" size="{collision_radius}"/>
<body name="tip" pos="1 0 0"><inertial pos="0 0 0" mass=".1" diaginertia=".01 .01 .01"/></body></body></body></worldbody></mujoco>''')
        self.git('init','-q');self.git('add','.');self.git('-c','user.name=Fixture','-c','user.email=fixture@example.invalid','commit','-qm','analytic pair')
        conventions=dict(length_unit='metre',angle_unit='radian',up_axis='+Z',forward_axis='+X',left_axis='+Y',root_frame='pelvis',root_translation_unit='metre',root_quaternion_order='wxyz')
        reps={}
        for rep,filename in [('urdf','model.urdf'),('mjcf','model.xml')]:
            reps[rep]=dict(model=filename,root='unencoded' if rep=='urdf' else 'free',files=[dict(path=filename,role='model',sha256=hashlib.sha256((self.source/filename).read_bytes()).hexdigest())],joints=[dict(name='hinge',kind='revolute',axis=[0,0,1],lower=-2,upper=2 if rep=='urdf' else limit)])
        d=dict(schema_version=1,id='fixture',version=1,source=dict(key='fixture',repository='fixture://local',revision=self.git('rev-parse','HEAD').strip()),provenance=dict(license_coverage='unknown',modifications=[],files=[]),conventions=conventions,joint_order=['hinge'],representations=reps)
        (self.definition/'robot.json').write_text(json.dumps(d))
        poses=dict(schema_version=1,angle_unit='radian',poses={'zero':dict(joints=dict(hinge=0),root_translation=[0,0,0],root_quaternion=[1,0,0,0],root_handling='explicit world origin'), 'bent':dict(base='zero',joints=dict(hinge=1.5707963267948966))})
        (self.definition/'poses.json').write_text(json.dumps(poses))
        self.roots={'fixture':self.source}

    def git(self,*args):
        return subprocess.check_output(['git','-C',str(self.source),*args],text=True,stderr=subprocess.PIPE)
