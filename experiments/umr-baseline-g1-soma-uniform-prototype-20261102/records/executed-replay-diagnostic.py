"""Controlled float32 fitted-forward repeatability and quantization diagnostic."""
import argparse
import json
import os
from pathlib import Path
import sys
# Reject mismatched BLAS/CUDA configuration before importing numerical runtimes.
EXPECTED_NUMERICAL_ENVIRONMENT = {'OMP_NUM_THREADS':'4', 'OPENBLAS_NUM_THREADS':'4',
    'CUDA_VISIBLE_DEVICES':'0', 'UMR_SOMA_ASSETS_PATH':'/data/motions/human_models/soma-x/f81a01796f65/overlays/umr',
    'UMR_SOMA_SMPLX_ASSETS_PATH':'/data/motions/human_models/soma-x/f81a01796f65/overlays/umr/SMPLX'}
NUMERICAL_ENVIRONMENT_AT_IMPORT = {k:os.environ.get(k) for k in EXPECTED_NUMERICAL_ENVIRONMENT}
if __name__ == '__main__' and NUMERICAL_ENVIRONMENT_AT_IMPORT != EXPECTED_NUMERICAL_ENVIRONMENT:
    raise RuntimeError('Tight fitted replay audit requires the recorded exporter environment before numerical imports: '+repr(NUMERICAL_ENVIRONMENT_AT_IMPORT))

import numpy as np
import torch
torch.set_num_threads(2)
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'externals/UMR/scripts'))
import soma_source
import smpl_surface_retarget_common as common
import humanoid_retarget_pipeline as pipeline
import retarget_smpl_to_humanoid_surface_vector as robot

p=argparse.ArgumentParser(__doc__)
for name in ('run','inspection','output'):
    p.add_argument('--'+name,type=Path,required=True)
a=p.parse_args()
if a.output.exists(): raise FileExistsError(a.output)
assert torch.cuda.is_available() and torch.get_num_threads() == 2
hardware=json.loads((a.run/'runtime-hardware.json').read_text())
assert torch.__version__ == hardware['torch_version']
runtime={'environment':NUMERICAL_ENVIRONMENT_AT_IMPORT, 'torch_version':torch.__version__, 'torch_threads':torch.get_num_threads(), 'torch_cuda_runtime':torch.version.cuda, 'cuda_device':torch.cuda.get_device_name(0), 'soma_device':'cuda:0', 'numpy_version':np.__version__}
h=json.loads((a.inspection/'bindings.json').read_text())['human_motion']
with np.load(a.run/'motion.npz',allow_pickle=True) as saved:
    source=Path(str(saved['source_data'].item()));key=str(saved['source_sequence_key'].item())
collection,_=common.load_motion_collection(source)
_,seq=common.select_sequence(collection,key,0)
config=pipeline.load_pipeline_config(a.run/'config.json',ROOT/'externals/UMR/humanoid_retarget_defaults_bones_seed.json')
tpl=robot.smpl_template_config(config,seq,key,'neutral')
model_dir=Path(config['smplx_model_dir'])
v,j,faces,names,_=common.source_template_vertices_joints_faces(seq,tpl,model_dir)
with np.load(a.run/'dataset.npz',allow_pickle=True) as saved:
    centered,_,_=common.center_source_template(v,j,str(saved['center_modes'][0]),joint_names=names,source_type='soma')
    template_error=float(np.abs(centered-saved['mesh_vertices_0']).max())
ids=np.arange(512,576)
def forward():
    return soma_source.soma_motion_vertices_joints(seq,ids,batch_size=32,zero_fingers=True)[:2]
v1,j1=forward();v2,j2=forward()
v3,j3,_=common.source_motion_vertices_joints(seq,ids,model_dir,batch_size=32,smplx_device='cpu',smplx_batch_size=32,zero_source_finger_pose=True)
def display(v):
    out=common.source_points_to_retarget_frame(v,'soma',seq.get('output_up','z'))
    out[:,:,2]-=h['source_ground_shift_native_z_m']
    return (out*h['source_scale'])[:,:,[1,2,0]]
v1d=display(v1); roots=display(j1)[:,names.index('Hips')]
codes=np.rint((v1d-roots[:,None])/.0001).astype('<i2')
decoded=codes.astype(np.float32)*.0001+roots[:,None]
c=h['chunks'][8]
old=np.fromfile(a.inspection/c['file'],dtype='<i2').reshape(c['count'],h['vertex_count'],3).astype(float)*.0001+np.array(h['root_positions'])[512:576,None]
# Explicitly evict just this module's cached model; retain the same process/runtime.
cache_names=[name for name in vars(soma_source) if 'CACHE' in name]
result={'runtime':runtime, 'source_frames':ids.tolist(),'template_vs_saved_dataset_max_axis_m':template_error,
    'same_model_native_repeat_vertices_max_axis_m':float(np.abs(v1-v2).max()),
    'same_model_native_repeat_joints_max_axis_m':float(np.abs(j1-j2).max()),
    'direct_vs_common_wrapper_vertices_max_axis_m':float(np.abs(v1-v3).max()),
    'direct_vs_common_wrapper_joints_max_axis_m':float(np.abs(j1-j3).max()),
    'fresh_quantization_own_reference_max_axis_m':float(np.abs(decoded-v1d).max()),
    'exported_decoded_vs_current_native_max_axis_m':float(np.abs(old-v1d).max()),
    'exported_root_vs_current_native_max_axis_m':float(np.abs(np.array(h['root_positions'])[512:576]-roots).max()),
    'cached_model_keys':cache_names,'torch_threads':torch.get_num_threads()}
# lru_cache model factory supplies a clean independent instance with the same inputs.
if hasattr(soma_source._soma_x_layer,'cache_clear'):
    soma_source._soma_x_layer.cache_clear()
    v4,j4=forward()
    result.update({'fresh_model_native_vertices_max_axis_m':float(np.abs(v1-v4).max()),
        'fresh_model_native_joints_max_axis_m':float(np.abs(j1-j4).max())})
with a.output.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps(result,indent=2))
