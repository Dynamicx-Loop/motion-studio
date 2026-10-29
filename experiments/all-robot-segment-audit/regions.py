"""Robot-specific static zones in metres (forward,left,up).

These diagnostic conventions use inspected shells and canonical joint planes.
They are independent of learned pairings and do not assert semantic truth.
"""
import numpy as np

PROFILES={
 'piplus':{'waist':'waist_yaw_joint','head':('head_pitch_link',),'neck':('head_yaw_link',),
  'joints':('{s}_shoulder_roll_joint','{s}_elbow_joint','{s}_wrist_joint','{s}_hip_pitch_joint','{s}_calf_joint','{s}_ankle_roll_joint')},
 'k1':{'waist':None,'head':('Head_2',),'neck':('Head_1',),
  'joints':('{s}_Shoulder_Roll','{s}_Elbow_Pitch','{s}_Elbow_Yaw','{s}_Hip_Pitch','{s}_Knee_Pitch','{s}_Ankle_Roll')},
 't800':{'waist':'J12_TORSO_YAW','head':('LINK_HEAD_YAW',),'neck':('LINK_HEAD_PITCH',),
  'joints':('J{sh}_SHOULDER_ROLL_{s}','J{el}_ELBOW_PITCH_{s}',None,'J{hip}_HIP_PITCH_{s}','J{kn}_KNEE_PITCH_{s}','J{an}_ANKLE_ROLL_{s}')},
 'h2':{'waist':'waist_yaw_joint','head':('head_yaw_link',),'neck':('head_pitch_link',),
  'joints':('{s}_shoulder_roll_joint','{s}_elbow_joint','{s}_wrist_roll_joint','{s}_hip_pitch_joint','{s}_knee_joint','{s}_ankle_roll_joint')},
 'mimickit':{'waist':'abdomen_z','head':('head',),'neck':(),
  'joints':('{s}_shoulder_x','{s}_elbow',None,'{s}_hip_x','{s}_knee','{s}_ankle_x')},
 'g1_racket':{'waist':'waist_yaw_joint','head':('head_link',),'neck':(),
  'joints':('{s}_shoulder_roll_joint','{s}_elbow_joint','{s}_wrist_roll_joint','{s}_hip_pitch_joint','{s}_knee_joint','{s}_ankle_roll_joint')},
}

def rigid_owner(model,body):
    while body and model.body_jntnum[body]==0:body=int(model.body_parentid[body])
    return model.body(body).name


def joint_anchors(model,data,center,rotation):
    names={model.joint(j).name:j for j in range(model.njnt) if model.joint(j).name}
    profile=('piplus' if 'l_calf_joint' in names else 'k1' if 'AAHead_yaw' in names else
       't800' if 'J12_TORSO_YAW' in names else 'mimickit' if 'abdomen_z' in names else
       'h2' if 'head_pitch_joint' in names else 'g1_racket')
    spec=PROFILES[profile]
    anchors={n:((data.xanchor[j]-center)@rotation).tolist() for n,j in names.items()}
    for side in ('left','right'):
        short=side[0];s=short if profile=='piplus' else side.title() if profile=='k1' else short.upper() if profile=='t800' else side
        values=dict(s=s,sh='14' if side=='left' else '19',el='16' if side=='left' else '21',hip='00' if side=='left' else '06',kn='03' if side=='left' else '09',an='05' if side=='left' else '11')
        for key,pattern in zip(('shoulder_roll','elbow','wrist_roll','hip_pitch','knee','ankle_roll'),spec['joints']):
            if pattern:anchors[side+'_'+key+'_joint']=anchors[pattern.format(**values)]
        if profile=='mimickit':
            anchors[side+'_wrist_roll_joint']=((data.xpos[model.body(side+'_hand').id]-center)@rotation).tolist()
    if spec['waist']:anchors['waist_yaw_joint']=anchors[spec['waist']]
    anchors['_profile']=profile
    return anchors


def family(body,profile):
    low=body.lower();side=None
    for s in ('left','right'):
        if low.startswith(s+'_') or (profile=='piplus' and low.startswith(s[0]+'_')) or (profile=='t800' and low.endswith('_'+s[0])):side=s
    if side:
        if any(t in low for t in ('shoulder','elbow','wrist','hand','arm','gripper')):return side,'arm'
        if any(t in low for t in ('hip','thigh','calf','knee','shank','shin','ankle','foot')):return side,'leg'
    return None,'central'


def ownership_region(body):
    # Actual owner remains in the separate table. This coarse label is descriptive.
    return body


def geometry_regions(points,bodies,meshes,anchors):
    profile=anchors['_profile'];spec=PROFILES[profile];out=[]
    waist=anchors.get('waist_yaw_joint');shoulder=np.mean([anchors[s+'_shoulder_roll_joint'][2] for s in ('left','right')])
    for q,body,mesh in zip(points,bodies,meshes):
        if mesh in spec['head']:zone='head shell'
        elif mesh in spec['neck']:zone='neck hardware'
        elif 'camera' in mesh.lower():zone='sensor'
        elif 'racket' in mesh.lower():zone='tool racket'
        else:
            side,kind=family(body,profile)
            if kind=='arm':
                sign=1 if side=='left' else -1;x=sign*q[1]
                sh=sign*anchors[side+'_shoulder_roll_joint'][1];el=sign*anchors[side+'_elbow_joint'][1]
                wrist=anchors.get(side+'_wrist_roll_joint');wr=sign*wrist[1] if wrist is not None else np.inf
                zone=side+(' shoulder' if x<sh else ' upper arm' if x<el else ' forearm' if x<wr else ' hand')
            elif kind=='leg':
                hip=anchors[side+'_hip_pitch_joint'][2];knee=anchors[side+'_knee_joint'][2];ankle=anchors[side+'_ankle_roll_joint'][2]
                zone=side+(' hip cap' if q[2]>hip else ' thigh' if q[2]>knee else ' shin' if q[2]>ankle else ' foot')
            elif waist is None:
                # K1 has one rigid trunk and no waist joint/pelvis shell.
                zone='lower torso' if q[2]<shoulder/2 else 'upper torso'
            else:zone='pelvis' if q[2]<waist[2] else 'lower torso' if q[2]<(waist[2]+shoulder)/2 else 'upper torso'
        out.append(zone)
    return np.array(out,dtype=str)


def expected_regions(source):
    if source=='head':return {'head shell'}
    if source=='torso':return {'lower torso','upper torso'}
    if source=='hips':return {'pelvis','left hip cap','right hip cap'}
    side='left' if source.startswith('left') else 'right'
    return {side+' '+{'Shoulder':'shoulder','UpperArm':'upper arm','Arm':'upper arm','ForeArm':'forearm','Hand':'hand','UpLeg':'thigh','Leg':'shin','Foot':'foot'}[source[len(side):]]}
