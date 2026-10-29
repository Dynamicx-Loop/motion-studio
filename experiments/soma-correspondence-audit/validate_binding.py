"""Independent global-triangle projection check of the actual visual bindings."""
import json,sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
OUT=ROOT/'outputs/soma-correspondence-audit'
sys.path.insert(0,str(ROOT/'externals/UMR-astro-surface-experiment/scripts'))
sys.path.insert(0,str(ROOT/'experiments/segment-binding-audit'))
import mujoco
import build_correspondence_ae_dataset as build
import retarget_smpl_to_humanoid_surface_vector as rb
from primitive_surface import bind_points_to_mesh_exact
from regions import geometry_regions,joint_anchors

def main():
    results={}
    for arm,path in json.loads((HERE/'arms.json').read_text()).items():
        print('CHECK',arm,flush=True)
        c=json.loads(Path(path).read_text());ds=np.load(c['correspondence']['dataset']['out'],allow_pickle=True)
        a=np.load(OUT/f'{arm}-audit.npz');source=arm.split('_')[0]
        model=mujoco.MjModel.from_xml_path(c['robot']['xml']);data=mujoco.MjData(model)
        build.apply_joint_qpos(model,data,c['robot']['tpose_qpos'],required=True);mujoco.mj_forward(model,data)
        v,f,owners,center,rot,_=rb.collect_root_mesh(model,data,rb.visual_geom_ids(model,'auto'),c['robot']['point_cloud_center'])
        np.testing.assert_array_equal(f,ds['mesh_faces_1'])
        np.testing.assert_allclose(v@rb.SMPL_TO_ROBOT_ROOT_MATRIX,ds['mesh_vertices_1'],atol=2e-7,rtol=0)
        p=rb.smpl_frame_to_robot_root(a['robot_learned'])
        exact=bind_points_to_mesh_exact(p,v,f);g=owners[exact['face_ids']]
        body=np.array([model.body(int(model.geom_bodyid[x])).name for x in g])
        mesh=np.array([model.mesh(int(model.geom_dataid[x])).name for x in g])
        zones=geometry_regions(exact['closest_points'],body,mesh,joint_anchors(model,data,center,rot))
        delta=np.linalg.norm(exact['closest_points']-a['robot_projected'],axis=1)
        head=a['source_common']=='head/face'
        w=np.load(OUT/'human-weight-diagnostics.npz')
        np.testing.assert_array_equal(ds['mesh_faces_0'],w[source+'_faces'])
        np.testing.assert_allclose(ds['mesh_vertices_0'],w[source+'_vertices']-ds['root_offsets'][0],atol=1e-7,rtol=0)
        anchors=joint_anchors(model,data,center,rot)
        old_error=np.linalg.norm(p-a['robot_projected'],axis=1)
        new_error=np.linalg.norm(p-exact['closest_points'],axis=1)
        improvement=old_error-new_error
        assert improvement.min()>-2e-7
        cross={}
        for side in ['left','right']:
            for label,axis,cut,direction in [(side+'UpLeg',2,anchors[side+'_knee_joint'][2],-1),(side+'ForeArm',1,anchors[side+'_elbow_joint'][1],-1 if side=='left' else 1)]:
                mask=a['source_common']==label
                cross[label]={'exact':int((mask&(direction*(exact['closest_points'][:,axis]-cut)>.02)).sum()),'production':int((mask&(direction*(a['robot_projected'][:,axis]-cut)>.02)).sum())}
        np.savez_compressed(OUT/f'{arm}-exact-projection.npz',points=exact['closest_points'],geom_ids=g,body_names=body,mesh_names=mesh,regions=zones,error_improvement_m=improvement)
        results[arm]={'cross_joint_checks':cross,'distance_improvement_over_1micron':int((improvement>1e-6).sum()),'max_distance_improvement_m':float(improvement.max()),'changed_body_equal_distance_within_1micron':int(((body!=a['body_names'])&(abs(improvement)<=1e-6)).sum()),'max_projection_position_difference_m':float(delta.max()),'over_1mm':int((delta>.001).sum()),'changed_body_count':int((body!=a['body_names']).sum()),'changed_mesh_count':int((mesh!=a['mesh_names']).sum()),'changed_geometry_zone_count':int((zones!=a['geometry_regions']).sum()),'exact_head_face_to_torso':int((head&np.isin(zones,['upper torso','lower torso'])).sum()),'production_head_face_to_torso':int((head&np.isin(a['geometry_regions'],['upper torso','lower torso'])).sum()),'source_mesh_matches_audited_asset':True,'target_mesh_matches_dataset':True}
    (HERE/'binding-validation.json').write_text(json.dumps(results,indent=2)+'\n')
    print(json.dumps(results,indent=2))
if __name__=='__main__':main()
