"""Native UMR labels and independent grouped-LBS diagnostics on human slots."""
import numpy as np
import retarget_body_segment_surface as seg


def diagnose(source,ds,binding,human,weights):
    faces=ds['mesh_faces_0'];fi=binding['face_ids'];bary=binding['bary'];vertices=faces[fi]
    if source=='smplx':
        ids=seg.smplx_slot_part_ids_from_binding(faces,fi,template_vertices=ds['mesh_vertices_0'],bary=bary,slot_points=human)
        raw=weights['smplx_raw55_face_labels'][fi]
        common=weights['smplx_joint_common_regions'][raw]
        mixed=np.zeros(len(fi),bool)
        vertex_ids=seg.vertex_part_ids_from_face_part_ids(faces,seg.load_smplx17_face_parts()[0],len(ds['mesh_vertices_0']))
    else:
        ids=seg.soma_slot_part_ids_from_smplx_correspondence(faces,fi,len(ds['mesh_vertices_0']),slot_points=human)
        rawverts=weights['soma_raw55_vertex_labels'][vertices]
        raw=np.array([np.bincount(row,minlength=55).argmax() for row in rawverts])
        commonverts=weights['smplx_joint_common_regions'][rawverts]
        common=np.array([sorted(set(row),key=lambda x:(-list(row).count(x),x))[0] for row in commonverts])
        mixed=(commonverts!=commonverts[:,:1]).any(1)
        vertex_ids=weights['soma_native17_vertex_labels']
    native=np.array([seg.BODY_SEGMENT_PART_NAMES[int(x)] for x in ids])
    group=(weights[source+'_grouped_weights'][vertices]*bary[:,:,None]).sum(1)
    full=(weights[source+'_weights'][vertices]*bary[:,:,None]).sum(1)
    common_names=weights['common_names'];winner=common_names[group.argmax(1)]
    confidence=group.max(1)
    source_column=np.array([list(common_names).index(x) for x in common])
    declared_weight=group[np.arange(len(fi)),source_column]
    high=(declared_weight>=.8)&~mixed
    top=np.sort(full,axis=1)[:,-2:]
    vertex_ids=seg.relabel_upper_arm_slots(vertex_ids,ds['mesh_vertices_0'])
    # Independent source-joint planes: label spill and target spill are separate.
    joints=weights[source+'_joints']-ds['root_offsets'][0]
    names=list(weights[source+'_joint_names'])
    source_planes={}
    for side in ['left','right']:
        knee=names.index(side[0].upper()+'_Knee' if source=='smplx' else side.title()+'Shin')
        elbow=names.index(side[0].upper()+'_Elbow' if source=='smplx' else side.title()+'ForeArm')
        for label,axis,cut,direction in [(side+'UpLeg',1,joints[knee,1],-1),(side+'ForeArm',0,joints[elbow,0],-1 if side=='left' else 1)]:
            mask=common==label;distance=direction*(human[:,axis]-cut)
            source_planes[label]={'slots':int(mask.sum()),'source_beyond_plane_over_20mm':int((mask&(distance>.02)).sum()),'high_confidence_slots':int((mask&high).sum()),'high_confidence_beyond_plane_over_20mm':int((mask&high&(distance>.02)).sum())}
    report={'native_label_counts':{n:int((native==n).sum()) for n in sorted(set(native))},
      'common_label_counts':{n:int((common==n).sum()) for n in sorted(set(common))},
      'common_vs_lbs_disagreements':int((common!=winner).sum()),'mixed_common_vertex_faces':int(mixed.sum()),
      'high_confidence_slots':int(high.sum()),'lbs_top1_top2_gap_under_005':int(((top[:,1]-top[:,0])<.05).sum()),
      'lbs_max_row_sum_error':float(abs(full.sum(1)-1).max()),'source_joint_plane_checks':source_planes,
      'per_common_region':{n:{'slots':int((common==n).sum()),'high_confidence_slots':int(((common==n)&high).sum()),'lbs_agree':int(((common==n)&(winner==n)).sum()),'mean_declared_group_weight':float(declared_weight[common==n].mean())} for n in sorted(set(common))}}
    return dict(native=native,common=common,raw=raw,mixed=mixed,high=high,group_weight=declared_weight,lbs_winner=winner,report=report,vertex_ids=vertex_ids)
