"""Inventory tracked configs/assets and canonical pose geometry, without dynamics."""
import hashlib,json,subprocess,sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts'))
from motion_data_paths import canonical_motion_path
import mujoco,numpy as np
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
UP=ROOT/'externals/UMR';EXT=ROOT/'externals/UMR-astro-surface-experiment'
sys.path.insert(0,str(EXT/'scripts'))
import build_correspondence_ae_dataset as build
import retarget_smpl_to_humanoid_surface_vector as rb
from humanoid_retarget_config import load_config,resolve_path

def sha(p):return hashlib.sha256(canonical_motion_path(p).read_bytes()).hexdigest()
def main():
    tracked=subprocess.check_output(['git','-C',str(UP),'ls-files'],text=True).splitlines()
    inventory={'revision':subprocess.check_output(['git','-C',str(UP),'rev-parse','HEAD'],text=True).strip(),
       'tracked_pretrained_correspondence_candidates':[p for p in tracked if p.endswith(('.pt','.pth','.ckpt','.safetensors'))],
       'all_npz_files':[p for p in tracked if p.endswith('.npz')], 'configs':[], 'asset_models':[], 'canonical_geometries':{},'builder_presets':[]}
    for name,spec in build.SUPPORTED_ROBOT_SAMPLE_SPECS.items():
        inventory['builder_presets'].append({'name':name,'xml':str(spec.xml_path),'exists':spec.xml_path.exists(),'tpose_qpos':spec.tpose_qpos,'center':spec.root_body_name})
    for name,path in [('original_g1_default',build.DEFAULT_G1_XML),('g1_brainco_hand',build.DEFAULT_G1_BRAINCO_HAND_XML)]:
        inventory['builder_presets'].append({'name':name,'xml':str(path),'exists':path.exists()})
    for p in sorted(list(UP.glob('robot_configs/*.json'))+list(UP.glob('humanoid_retarget_defaults*.json'))):
        c=load_config(p)
        if not c.get('robot',{}).get('xml'):
            inventory['configs'].append({'path':str(p.relative_to(UP)),'sha256':sha(p),'kind':'source/task defaults; no robot XML','extends':json.loads(p.read_text()).get('extends')})
            continue
        x=resolve_path(c['robot']['xml'],c)
        inventory['configs'].append({'path':str(p.relative_to(UP)),'sha256':sha(p),'robot':c['robot']['name'],'xml':str(x.relative_to(UP)),
          'xml_exists':x.exists(),'native_human_center':c['correspondence']['dataset'].get('smpl_center'),
          'native_bbox_center_ratio':c['correspondence']['dataset'].get('bbox_center_ratio'),
          'source_template':c.get('smpl_template'), 'extends':json.loads(p.read_text()).get('extends')})
    for rel in tracked:
        if not rel.startswith('assets/') or not rel.endswith(('.xml','.urdf')):continue
        p=UP/rel;row={'path':rel,'sha256':sha(p),'bytes':p.stat().st_size}
        if p.suffix=='.xml':
            try:
                m=mujoco.MjModel.from_xml_path(str(p));row.update(nq=m.nq,nv=m.nv,bodies=m.nbody,geoms=m.ngeom,meshes=m.nmesh)
            except Exception as e:row['unavailable']=str(e)
        inventory['asset_models'].append(row)
    for p in sorted(HERE.glob('*.json')):
        if p.stem in {'inventory','results','provenance'} or p.stem.endswith('-resolved'):continue
        c=load_config(p)
        if not c.get('robot',{}).get('xml'):continue
        m=mujoco.MjModel.from_xml_path(c['robot']['xml']);d=mujoco.MjData(m)
        build.apply_joint_qpos(m,d,c['robot'].get('tpose_qpos',{}),required=True);mujoco.mj_forward(m,d)
        ids=rb.visual_geom_ids(m,'auto');v,f,o,center,rot,_=rb.collect_root_mesh(m,d,ids,c['robot']['point_cloud_center'])
        row={'xml':c['robot']['xml'],'xml_sha256':sha(c['robot']['xml']), 'bounds_root_m':[v.min(0).tolist(),v.max(0).tolist()],
          'joints':{m.joint(j).name:{'anchor':((d.xanchor[j]-center)@rot).tolist(),'axis':(d.xaxis[j]@rot).tolist(),'body':m.body(int(m.jnt_bodyid[j])).name} for j in range(m.njnt) if m.joint(j).name},'selected_geoms':[]}
        for g in ids:
            verts=v[np.unique(f[o==g])];b=int(m.geom_bodyid[g]);r=b
            while r and m.body_jntnum[r]==0:r=int(m.body_parentid[r])
            row['selected_geoms'].append({'id':int(g),'body':m.body(b).name,'parent':m.body(int(m.body_parentid[b])).name,
                'rigid_owner':m.body(r).name,'mesh':m.mesh(int(m.geom_dataid[g])).name if m.geom_type[g]==7 else m.geom(g).name or m.body(b).name,
                'type':int(m.geom_type[g]),'bounds_root_m':[verts.min(0).tolist(),verts.max(0).tolist()]})
        inventory['canonical_geometries'][p.stem]=row
    (HERE/'inventory.json').write_text(json.dumps(inventory,indent=2)+'\n')
    print(json.dumps({'configs':len(inventory['configs']),'asset_models':inventory['asset_models']},indent=2))
if __name__=='__main__':main()
