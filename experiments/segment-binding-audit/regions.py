"""Independent, explicit audit labels for canonical robot surface coordinates.

Points are metres in robot root (forward,left,up). Labels are diagnostic zones,
not training labels or asserted unique human/robot anatomical ground truth.
"""
import numpy as np


def joint_anchors(model, data, center, rotation):
    return {model.joint(j).name: ((data.xanchor[j]-center) @ rotation).tolist()
            for j in range(model.njnt) if model.joint(j).name}


def rigid_owner(model, body):
    """First joint-bearing ancestor, collapsing only welded body attachments."""
    while body and model.body_jntnum[body] == 0:
        body = int(model.body_parentid[body])
    return model.body(body).name


def ownership_region(body):
    for side in ('left', 'right'):
        if body.startswith(side+'_'):
            if 'hip' in body: return side+' thigh'
            if 'knee' in body: return side+' shin'
            if 'ankle' in body: return side+' foot'
            if 'shoulder' in body: return side+' upper arm'
            if 'elbow' in body: return side+' forearm'
            if 'wrist' in body or 'hand' in body: return side+' hand'
    return 'pelvis' if body == 'pelvis' else 'torso'


def geometry_regions(points, bodies, meshes, anchors):
    """Shell identity centrally, joint planes on limb families.

Head shell is identified by selected geom's mesh identity (primitive body's
identity). No invented robot neck. Central trunk splits at waist-yaw joint
height; torso upper/lower split midway to mean shoulder-roll height. Limb
families use inspected body hierarchy, then cut in space at actual joint
planes independent of which moving body owns each vertex/slot.
    """
    p=np.asarray(points); out=np.empty(len(p),dtype=object)
    waist=anchors['waist_yaw_joint'][2]
    shoulder=np.mean([anchors[s+'_shoulder_roll_joint'][2] for s in ('left','right')])
    for i,(q,body,mesh) in enumerate(zip(p,bodies,meshes)):
        if 'head' in mesh or 'head' in body:
            out[i]='head shell';continue
        if 'lidar' in body or 'imu' in body:
            out[i]='sensor';continue
        side=next((s for s in ('left','right') if body.startswith(s+'_')),None)
        if side and any(x in body for x in ('shoulder','elbow','wrist','hand')):
            sign=1 if side=='left' else -1
            x=sign*q[1]
            sh=sign*anchors[side+'_shoulder_roll_joint'][1]
            el=sign*anchors[side+'_elbow_joint'][1]
            wr=sign*anchors[side+'_wrist_roll_joint'][1]
            out[i]=side+(' shoulder' if x<sh else ' upper arm' if x<el else ' forearm' if x<wr else ' hand')
        elif side and any(x in body for x in ('hip','knee','ankle','foot')):
            hip=anchors[side+'_hip_pitch_joint'][2]
            knee=anchors[side+'_knee_joint'][2]
            ankle=anchors[side+'_ankle_roll_joint'][2]
            out[i]=side+(' hip cap' if q[2]>hip else ' thigh' if q[2]>knee else ' shin' if q[2]>ankle else ' foot')
        else:
            out[i]='pelvis' if q[2]<waist else ('lower torso' if q[2]<(waist+shoulder)/2 else 'upper torso')
    return out.astype(str)


def expected_regions(source):
    if source=='head':return {'head shell'}
    if source=='torso':return {'lower torso','upper torso'}
    if source=='hips':return {'pelvis','left hip cap','right hip cap'}
    side='left' if source.startswith('left') else 'right'
    suffix=source[len(side):]
    return {side+' '+{'Shoulder':'shoulder','UpperArm':'upper arm','Arm':'upper arm',
         'ForeArm':'forearm','Hand':'hand','UpLeg':'thigh','Leg':'shin','Foot':'foot'}[suffix]}
