"""Private MuJoCo worker; invoked only in the explicitly selected independent runtime."""
import json
import math
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

import mujoco
import numpy as np


def primitive(kind, size):
    if kind == mujoco.mjtGeom.mjGEOM_BOX:
        vertices = np.array([[x,y,z] for x in (-1,1) for y in (-1,1) for z in (-1,1)]) * size
        faces = [[0,1,3],[0,3,2],[4,6,7],[4,7,5],[0,4,5],[0,5,1],
                 [2,3,7],[2,7,6],[0,2,6],[0,6,4],[1,5,7],[1,7,3]]
        return vertices, faces
    if kind in (mujoco.mjtGeom.mjGEOM_SPHERE, mujoco.mjtGeom.mjGEOM_ELLIPSOID,
                mujoco.mjtGeom.mjGEOM_CAPSULE, mujoco.mjtGeom.mjGEOM_CYLINDER):
        vertices, faces = [], []
        for row in range(13):
            a = math.pi * row / 12
            radius, z = math.sin(a), math.cos(a)
            for col in range(24):
                b = 2 * math.pi * col / 24
                point = np.array([radius*math.cos(b),radius*math.sin(b),z])
                if kind == mujoco.mjtGeom.mjGEOM_ELLIPSOID:
                    point *= size
                elif kind == mujoco.mjtGeom.mjGEOM_CYLINDER:
                    point = np.array([math.cos(b)*size[0], math.sin(b)*size[0],
                                      size[1] if row < 6 else -size[1]])
                else:
                    point *= size[0]
                    if kind == mujoco.mjtGeom.mjGEOM_CAPSULE:
                        point[2] += size[1] if row <= 6 else -size[1]
                vertices.append(point)
                if row < 12:
                    k = row*24+col; n = row*24+(col+1)%24
                    faces.extend([[k,n,k+24],[n,n+24,k+24]])
        return np.asarray(vertices), faces
    raise ValueError(f'Unsupported robot visual geometry type: {kind}')


def main(request):
    path = Path(request['model'])
    model = mujoco.MjModel.from_xml_path(str(path))
    derived = []
    roots = [i for i in range(1, model.nbody) if model.body_parentid[i] == 0]
    if len(roots) != 1:
        raise ValueError('Expected one unambiguous humanoid root body; multi-robot scenes unsupported')
    root = roots[0]
    frees = [i for i in range(model.njnt) if model.jnt_type[i] == mujoco.mjtJoint.mjJNT_FREE]
    if not frees and request.get('derive_free_root'):
        tree = ET.parse(path)
        bodies = tree.getroot().findall('./worldbody/body')
        if len(bodies) != 1 or bodies[0].find('joint') is not None:
            raise ValueError('Cannot derive floating root from a jointed or ambiguous root')
        ET.SubElement(bodies[0], 'freejoint', name='__studio_free_root__')
        derived.append('Added floating root on managed derived XML; source closure preserved')
        if model.body_mass[root] <= 0:
            ET.SubElement(bodies[0], 'inertial', pos='0 0 0', mass='0.001', diaginertia='0.000001 0.000001 0.000001')
            derived.append('Synthetic root inertia: mass 0.001 kg, diagonal 1e-6 kg m²')
        # Fixed-root keyframes have incompatible nq after adding the floating root.
        if tree.getroot().find('keyframe') is not None:
            raise ValueError('Fixed-root keyframes require explicit conversion; unsupported')
        tree.write(path)
        model = mujoco.MjModel.from_xml_path(str(path))
        frees = [i for i in range(model.njnt) if model.jnt_type[i] == mujoco.mjtJoint.mjJNT_FREE]
    if len(frees) != 1 or model.jnt_bodyid[frees[0]] != root or model.jnt_qposadr[frees[0]] != 0:
        raise ValueError('Expected one floating root at qpos[0:7]; explicitly allow fixed-to-free derivation')
    joints = []
    for i in range(model.njnt):
        if i in frees:
            continue
        name = model.joint(i).name
        low, high = model.jnt_range[i]
        if model.jnt_type[i] != mujoco.mjtJoint.mjJNT_HINGE:
            raise ValueError('Only named bounded hinges and one floating root are supported')
        if not name or not model.jnt_limited[i] or not np.isfinite([low,high]).all() or low >= high:
            raise ValueError('Every hinge requires a name and finite increasing compiled limits')
        joints.append(dict(name=name, minimum_rad=float(low), maximum_rad=float(high),
                           qpos_index=int(model.jnt_qposadr[i])))
    if any(not j['minimum_rad'] <= model.qpos0[j['qpos_index']] <= j['maximum_rad'] for j in joints):
        raise ValueError('Compiled default pose exceeds joint limits; supply an MJCF with a valid reference pose')
    if not joints:
        raise ValueError('Expected an articulated humanoid with named hinges')
    bodies = [model.body(i).name for i in range(1,model.nbody)]
    if not all(bodies) or len(set(bodies)) != len(bodies):
        raise ValueError('Robot bodies must have unique names for torso selection')
    data = mujoco.MjData(model)
    if 'qpos' in request:
        data.qpos[:] = request['qpos']
    mujoco.mj_forward(model, data)
    ids = [i for i in range(model.ngeom) if model.geom_bodyid[i] != 0]
    if not ids:
        raise ValueError('Robot has no previewable geometry')
    transforms = [dict(position=data.geom_xpos[i].tolist(),
                       rotation=data.geom_xmat[i].tolist()) for i in ids]
    if request['operation'] == 'preview':
        return dict(transforms=transforms)
    geometry = []
    for i in ids:
        if model.geom_type[i] == mujoco.mjtGeom.mjGEOM_MESH:
            mesh = int(model.geom_dataid[i]); va = model.mesh_vertadr[mesh]; fa = model.mesh_faceadr[mesh]
            vertices = model.mesh_vert[va:va+model.mesh_vertnum[mesh]]
            faces = model.mesh_face[fa:fa+model.mesh_facenum[mesh]]
        else:
            vertices, faces = primitive(model.geom_type[i], model.geom_size[i])
        geometry.append(dict(vertices=np.asarray(vertices).tolist(), faces=np.asarray(faces).tolist(),
                             rgba=model.geom_rgba[i].tolist(), body=model.body(int(model.geom_bodyid[i])).name))
    Path(request['geometry']).write_text(json.dumps(dict(geometries=geometry, transforms=transforms)))
    return dict(root_body=model.body(root).name,bodies=bodies,joints=joints,
                default_qpos=model.qpos0.tolist(),derived=derived,runtime='MuJoCo '+mujoco.__version__)


if __name__ == '__main__':
    try:
        print(json.dumps(main(json.load(sys.stdin)), allow_nan=False))
    except Exception as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
