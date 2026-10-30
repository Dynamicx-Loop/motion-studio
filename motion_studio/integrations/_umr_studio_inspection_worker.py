"""CPU-only derived stage inspection; explicit files, never native pipeline entry points."""
import json
from pathlib import Path
import sys


def main(checkout, request_path, output):
    sys.path.insert(0, str(checkout/'scripts'))
    import numpy as np
    import mujoco
    import humanoid_retarget_pipeline as pipeline
    import retarget_body_segment_surface as segments
    import retarget_smpl_to_humanoid_surface_vector as robot
    import smpl_surface_retarget_common as common
    from _umr_studio_human import export_human_motion
    from _umr_studio_motion import export_motion
    request = json.loads(request_path.read_text())
    stage = request['stage']
    def file(stage, suffix):
        matches = [Path(p) for name,p in request['artifacts'][stage].items()
                   if name == suffix or name.endswith('/'+suffix)]
        if len(matches) != 1:
            raise ValueError('Missing or ambiguous registered artifact: '+suffix)
        return matches[0]
    config = json.loads(file(stage, 'humanoid_retarget_runtime_config.json').read_text())
    segments.configure_body_segment_surface(config)
    dataset = file('sampling', 'dataset.npz')
    with np.load(dataset, allow_pickle=True) as saved:
        names = saved['names'].astype(str).tolist()
        hi = names.index(pipeline.expected_smpl_slot_name(config))
        ri = names.index(config['robot'].get('slot_name',config['robot']['name']))
        human_v, human_f = saved[f'mesh_vertices_{hi}'], saved[f'mesh_faces_{hi}']
        robot_v, robot_f = saved[f'mesh_vertices_{ri}'], saved[f'mesh_faces_{ri}']
        sampled_human, sampled_target = saved['points'][[hi,ri]]
    if stage in ('sampling','training'):
        if stage == 'sampling':
            human, target = sampled_human, sampled_target
        else:
            slots = file('training','train/correspondence_slots_final.npz')
            human, *_ = common.load_slot_data(slots, names[hi], 'reconstructed_slots')
            target, *_ = common.load_slot_data(slots, names[ri], 'reconstructed_slots')
        if human.shape != (4096,3) or target.shape != human.shape or not np.isfinite([human,target]).all():
            raise ValueError('Expected finite native 4096-point arrays')
        binding = common.bind_points_to_mesh(human, human_v, human_f,
                        nearest_vertex_k=int(config['solver']['bind_nearest_vertex_k']))
        parts = segments.smplx_slot_part_ids_from_binding(human_f,binding['face_ids'],
                    template_vertices=human_v,bary=binding['bary'],slot_points=binding['closest_points'])
        labels = [segments.BODY_SEGMENT_PART_NAMES[int(p)] for p in parts]
        geometry = {}
        for name,v,f in [('human',human_v,human_f),('robot',robot_v,robot_f)]:
            np.asarray(v,dtype='<f4').tofile(output/f'{name}-vertices.bin')
            np.asarray(f,dtype='<u4').tofile(output/f'{name}-faces.bin')
            geometry[name]={'vertices':f'{name}-vertices.bin','faces':f'{name}-faces.bin',
                            'vertex_count':len(v),'face_count':len(f)}
        payload = {'run':request['run_id'],'stage':stage,'schema':segments.BODY_SEGMENT_SCHEMA,
            'units':'metres', 'coordinates':'SMPL Y-up; centered static reference meshes',
            'scope':('Independent sampled surfaces; sample indices are not learned correspondences' if stage=='sampling'
                     else 'Learned paired slot indices before rigid binding; ownership is not assigned'),
            'slot_identity': 'sample index' if stage=='sampling' else 'paired learned slot',
            'paired':stage!='sampling', 'geometry':geometry, 'slot_index':list(range(4096)),
            'source':human.tolist(),'target':target.tolist(),'labels':labels,
            'bodies':[None]*4096,'meshes':[None]*4096,'geom_ids':[None]*4096,'projection_m':[None]*4096,
            'counts':{name:labels.count(name) for name in sorted(set(labels))}}
    else:
        payload = json.loads(file('binding','bindings.json').read_text())
        for model in ('human','robot'):
            for field in ('vertices','faces'):
                name=payload['geometry'][model][field]
                (output/name).write_bytes(file('binding',name).read_bytes())
        with np.load(file('binding','binding.npz'),allow_pickle=False) as binding:
            source={'face_ids':binding['source_face_ids'].copy(),'bary':binding['source_bary'].copy()}
            target={'geom_ids':binding['target_geom_ids'].copy(),'local_pos':binding['target_local_pos'].copy()}
        xml = file('sampling','model/__studio_model.xml')
        model=mujoco.MjModel.from_xml_path(str(xml))
        motion=file('retargeting','motion.npz')
        payload['stage']='motion'
        payload['motion']=export_motion(motion.parent,output,model,target,robot,mujoco,np,
                                       expected_xml=config['robot']['xml'])
        expected=request['receipts']['retargeting']['inputs']
        payload['human_motion']=export_human_motion(motion.parent,output,config,source,common,robot,np,
                                                  dataset_path=dataset,expected_motion=expected)
        payload['scope']='Saved exact-frame motion; source native face+bary replay and rigid target attachment; no per-frame rebind'
    (output/'bindings.json').write_text(json.dumps(payload,allow_nan=False)+'\n')
    print('STUDIO_INSPECTION_VALIDATED '+stage,flush=True)


if __name__=='__main__':
    main(*map(Path,sys.argv[1:4]))
