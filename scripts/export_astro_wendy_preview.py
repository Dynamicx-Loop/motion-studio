"""Add Astro's visual meshes and FK animation to the local Wendy viewer."""
import argparse
import json
import shutil
from pathlib import Path
import mujoco
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--result',type=Path,default=ROOT/'outputs/umr/astro_p2_29dof/wendy_6s_9s/retarget.npz')
args=parser.parse_args()
result_path=args.result.resolve()
out = ROOT / 'outputs/smplx/wendy-viewer'
with np.load(result_path, allow_pickle=True) as data:
    qpos = data['qpos'].copy()
    fps = float(np.asarray(data['fps']).reshape(-1)[0])
    frame_ids = data['frame_ids'].copy()
    xml = str(data['robot_xml'].item())
manifest = json.loads((out/'manifest.json').read_text())
assert len(qpos) == manifest['frames'] == 360
assert np.array_equal(frame_ids, np.arange(360))
assert np.isclose(fps, manifest['fps'])
assert np.isfinite(qpos).all()
model = mujoco.MjModel.from_xml_path(xml)
data = mujoco.MjData(model)
assert qpos.shape[1] == model.nq
# Invert UMR's Y-up-to-Z-up basis, bringing robot world poses into the human viewer.
basis = np.array([[1,0,0],[0,0,1],[0,-1,0]], dtype=np.float64)
geom_ids = [i for i in range(model.ngeom)
            if model.geom_group[i] == 1 and model.geom_type[i] == mujoco.mjtGeom.mjGEOM_MESH]
meshes=[]
for i in geom_ids:
    mesh_id=int(model.geom_dataid[i])
    va=int(model.mesh_vertadr[mesh_id]); vn=int(model.mesh_vertnum[mesh_id])
    fa=int(model.mesh_faceadr[mesh_id]); fn=int(model.mesh_facenum[mesh_id])
    verts=model.mesh_vert[va:va+vn].copy()
    faces=model.mesh_face[fa:fa+fn].copy()
    verts.astype('<f4').tofile(out/f'robot-{i}-vertices.bin')
    faces.astype('<u4').tofile(out/f'robot-{i}-faces.bin')
    meshes.append(dict(geom_id=i,vertices=f'robot-{i}-vertices.bin',faces=f'robot-{i}-faces.bin',
        color=model.geom_rgba[i,:3].tolist()))
transforms=np.zeros((len(qpos),len(geom_ids),12),dtype='<f4')
mins=[];maxs=[]
for frame,q in enumerate(qpos):
    data.qpos[:]=q
    mujoco.mj_forward(model,data)
    low=np.full(3,np.inf);high=-low
    for k,i in enumerate(geom_ids):
        rot=basis @ data.geom_xmat[i].reshape(3,3)
        pos=basis @ data.geom_xpos[i]
        transforms[frame,k,:9]=rot.reshape(-1)
        transforms[frame,k,9:]=pos
        mesh_id=int(model.geom_dataid[i]); va=int(model.mesh_vertadr[mesh_id]);vn=int(model.mesh_vertnum[mesh_id])
        world=model.mesh_vert[va:va+vn] @ rot.T+pos
        low=np.minimum(low,world.min(0));high=np.maximum(high,world.max(0))
    mins.append(low);maxs.append(high)
transforms.tofile(out/'robot-transforms.bin')
limited=np.flatnonzero(model.jnt_limited & (model.jnt_type == mujoco.mjtJoint.mjJNT_HINGE))
angles=qpos[:,model.jnt_qposadr[limited]]
violation=np.maximum(model.jnt_range[limited,0]-angles,angles-model.jnt_range[limited,1])
report=dict(frames=len(qpos),fps=fps,qpos_shape=list(qpos.shape),all_finite=True,
    max_joint_limit_violation_rad=float(max(0,violation.max())),
    root_quaternion_norm_max_error=float(np.abs(np.linalg.norm(qpos[:,3:7],axis=1)-1).max()),
    max_joint_frame_step_rad=float(np.abs(np.diff(angles,axis=0)).max()),
    min_visual_mesh_height_m=float(np.min(mins,axis=0)[1]),
    visual_mesh_bounds=[np.min(mins,axis=0).tolist(),np.max(maxs,axis=0).tolist()],
    root_displacement_m=float(np.linalg.norm(qpos[-1,:3]-qpos[0,:3])))
result_path.with_suffix('.preview-report.json').write_text(json.dumps(report,indent=2)+'\n')
# Static centering only: root motion and height remain intact.
robot_center=(basis @ qpos[0,:3]).tolist()
torso_report_path=result_path.with_suffix('.torso-report.json')
if torso_report_path.exists(): report['torso']=json.loads(torso_report_path.read_text())
manifest['robot']=dict(meshes=meshes,transforms='robot-transforms.bin',center=robot_center,report=report)
(out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
for name in ('index.html','app.js'):
    shutil.copy(ROOT/'scripts/wendy-viewer'/name,out/name)
print(json.dumps(report,indent=2))
