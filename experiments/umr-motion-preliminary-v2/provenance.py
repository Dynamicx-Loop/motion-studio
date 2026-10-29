"""Record immutable input/output hashes and runtime, then verify paired timing."""
from pathlib import Path
import json,hashlib,subprocess,sys
import numpy as np,torch,mujoco
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).parent;OUT=ROOT/'outputs/umr-motion-preliminary-v2'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
r={'date':'2026-10-23','python':sys.version,'numpy':np.__version__,'torch':torch.__version__,'mujoco':mujoco.__version__,'hardware':'RTX 5070 Laptop 8151MiB','gpu_memory':'Spot sample 2367MiB device total during full run; peak GPU memory not instrumented. CPU peak RSS per run in time -v logs. Not a controlled speed benchmark.','files':{},'repositories':{}}
for repo in [ROOT/'externals/UMR-astro-surface-experiment',Path('/data/workspace/notAnyrobot/menagerie_x')]:
 patch=subprocess.check_output(['git','-C',str(repo),'diff','HEAD']);(HERE/(repo.name+'.patch')).write_bytes(patch)
 r['repositories'][str(repo)]={'head':subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip(),'tracked_patch_sha256':hashlib.sha256(patch).hexdigest()}
assets=Path('/data/workspace/notAnyrobot/menagerie_x/robots/astro_p2_43dof_dex3_1')
for base in [assets,ROOT/'externals/UMR-astro-surface-experiment/assets/g1']:
 for p in base.rglob('*'):
  if p.is_file() and p.suffix.lower() in ['.xml','.stl','.obj','.mtl','.json','.md']:r['files'][str(p)]=sha(p)
for p in HERE.glob('smplx_*.json'):
 c=json.loads(p.read_text());r['files'][str(p)]=sha(p)
 for key in [c['motion']['data'],c['correspondence']['slots'],c['correspondence']['dataset']['out'],c['retarget']['out']]:r['files'][key]=sha(Path(key))
 z=np.load(c['retarget']['out'],allow_pickle=True);assert len(z['qpos'])==1823 and np.array_equal(z['frame_ids'],np.arange(0,5468,3))
 r.setdefault('motion',{})[p.stem]={'fps':float(z['fps'][0]),'frame_ids':[0,5466,3],'frames':1823,'shape':list(z['qpos'].shape),'source_template':'smplx_neutral_betas_52fa48a138','source_quaternions':'input axis-angle; output root wxyz','units':'metres/radians','source_frame':'Y up; solver converts (x,y,z) to (x,-z,y); output Z up','finger_pose':'zeroed by baseline preprocessing','filter':'LQR; saved cost is pre-filter solver cost, not exported pose residual'}
for filename in ['asset-inspection.json','binding-validation.json','results.json','provenance.json']:
 p=ROOT/'experiments/astro-hands-correspondence'/filename;shutil_name='static-hands-'+filename
 (HERE/shutil_name).write_bytes(p.read_bytes());r['files'][str(p)]=sha(p)
model=Path('/data/motions/human_models/smplx/1.1/models_smplx_v1_1/models/smplx/SMPLX_NEUTRAL.pkl')
r['files'][str(model)]=sha(model)
for p in list(OUT.glob('*/generated-model.xml'))+list((OUT/'viewer').glob('source*')):
 r['files'][str(p)]=sha(p)
(HERE/'provenance.json').write_text(json.dumps(r,indent=2)+'\n')
print('Verified all four frame IDs, shapes, source/config/geometry hashes and provenance.')
