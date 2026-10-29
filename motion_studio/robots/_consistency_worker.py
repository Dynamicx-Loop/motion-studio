"""Concrete CPU MuJoCo reader. Invoked by _consistency, never imported by callers."""
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

import mujoco
import numpy as np

CONVENTIONS = ('URDF imported in memory with absolute mesh paths, discardvisual=false, '
               'fusestatic=false, strippath=false, inertiafromgeom=false, and an added '
               'massless world link/floating joint to the declared root; original MJCF '
               'compiled directly. Explicit named scalar qpos and XYZ/wxyz root at each '
               'pose; mj_forward only, no keyframe reset or integration. World-frame '
               'aggregate mass/COM/inertia includes parallel-axis contributions.')


def load(request):
    path = Path(request['model'])
    if request['representation'] == 'mjcf':
        return mujoco.MjModel.from_xml_path(str(path))
    xml = ET.fromstring(path.read_text())
    for mesh in xml.findall('.//mesh'):
        mesh.set('filename', str((path.parent / mesh.attrib['filename']).resolve()))
    compiler = xml.find('mujoco/compiler')
    if compiler is None:
        extension = xml.find('mujoco')
        if extension is None:
            extension = ET.SubElement(xml, 'mujoco')
        compiler = ET.SubElement(extension, 'compiler')
    compiler.attrib.clear()
    compiler.attrib.update(discardvisual='false', fusestatic='false',
                          strippath='false', inertiafromgeom='false')
    ET.SubElement(xml, 'link', name='world')
    floating = ET.SubElement(xml, 'joint', name='__motion_studio_free__', type='floating')
    ET.SubElement(floating, 'parent', link='world')
    ET.SubElement(floating, 'child', link=request['root'])
    return mujoco.MjModel.from_xml_string(ET.tostring(xml, encoding='unicode'))


def snapshot(request):
    model = load(request)
    data = mujoco.MjData(model)
    for name,value in zip(request['names'],request['values'],strict=True):
        data.joint(name).qpos[0] = value
    for i in range(model.njnt):
        if model.jnt_type[i] == mujoco.mjtJoint.mjJNT_FREE:
            address = model.jnt_qposadr[i]
            data.qpos[address:address+7] = request['translation'] + request['quaternion']
    mujoco.mj_forward(model,data)
    frames = {model.body(i).name: (data.xpos[i],data.xmat[i].reshape(3,3))
              for i in range(1,model.nbody) if model.body(i).name != '__motion_studio_world__'}
    masses = model.body_mass
    total = float(masses.sum())
    com = np.sum(masses[:,None]*data.xipos,axis=0)/total
    inertia = np.zeros((3,3))
    for i in range(1,model.nbody):
        rotation = data.ximat[i].reshape(3,3)
        offset = data.xipos[i] - com
        inertia += rotation @ np.diag(model.body_inertia[i]) @ rotation.T
        inertia += masses[i]*(np.dot(offset,offset)*np.eye(3)-np.outer(offset,offset))
    geometry = {'visuals': [], 'collisions': []}
    for i in range(model.ngeom):
        # Ground/world geoms are environment, not part of the robot pair.
        body = model.geom_bodyid[i]
        if body == 0:
            continue
        collision = bool(model.geom_contype[i] or model.geom_conaffinity[i])
        record = [model.body(body).name,int(model.geom_type[i]),
                  model.geom_size[i].tolist(),model.geom_pos[i].tolist(),model.geom_quat[i].tolist()]
        meshid = model.geom_dataid[i]
        if model.geom_type[i] == mujoco.mjtGeom.mjGEOM_MESH:
            record.append(model.mesh(meshid).name)
        geometry['collisions' if collision else 'visuals'].append(record)
    return frames,total,com,inertia,geometry


def geometry_equal(first, second):
    def key(x):
        return (x[0],x[1],str(x[5:]),tuple(round(v,6) for row in x[2:5] for v in row))
    a,b = sorted(first,key=key),sorted(second,key=key)
    if len(a) != len(b):
        return False
    return all(x[:2] == y[:2] and x[5:] == y[5:] and
               all(np.allclose(u,v,atol=1e-6,rtol=0) for u,v in zip(x[2:5],y[2:5]))
               for x,y in zip(a,b))


def compare(pair):
    first,second = [snapshot(request) for request in pair]
    fa,fb = first[0],second[0]
    missing = sorted(set(fa)^set(fb))
    positions,angles = [],[]
    for name in sorted(set(fa)&set(fb)):
        pa,ra = fa[name];pb,rb = fb[name]
        positions.append(float(np.linalg.norm(pa-pb)))
        r = ra.T @ rb
        sine = np.linalg.norm([r[2,1]-r[1,2],r[0,2]-r[2,0],r[1,0]-r[0,1]])/2
        angles.append(float(np.arctan2(sine,(np.trace(r)-1)/2)))
    pos,angle = max(positions,default=0),max(angles,default=0)
    mass = abs(first[1]-second[1]);com = float(np.linalg.norm(first[2]-second[2]))
    inertia = float(np.max(np.abs(first[3]-second[3])))
    result = dict(named_frames=dict(matches=not missing and pos<=1e-6 and angle<=1e-6,
        missing_frames=missing,compared_frames=len(positions),max_position_m=pos,max_angle_rad=angle),
        inertial_totals=dict(matches=mass<=1e-6 and com<=1e-6 and inertia<=1e-6,
        inertia_world_com_kg_m2=[first[3].tolist(),second[3].tolist()],
        masses_kg=[first[1],second[1]],com_world_m=[first[2].tolist(),second[2].tolist()],
        mass_difference_kg=mass,com_difference_m=com,
        max_inertia_difference_kg_m2=inertia))
    for kind in ('visuals','collisions'):
        a,b = first[4][kind],second[4][kind]
        verified = not any(x[1] == int(mujoco.mjtGeom.mjGEOM_MESH) for x in a+b)
        result[kind]=dict(matches=verified and geometry_equal(a,b),verified=verified,
            counts=[len(a),len(b)],
            scope='Compiled body-local primitive type/size/position/quaternion; mesh geometry comparison unsupported, regardless of mesh names/bounds or sealed source bytes. No rendered/contact equality inferred.')
    return result


if __name__ == '__main__':
    requests=json.load(sys.stdin)
    print(json.dumps(dict(runtime='MuJoCo '+mujoco.__version__+'; NumPy '+np.__version__,
                         import_conventions=CONVENTIONS,poses=[compare(pair) for pair in requests]),allow_nan=False))
