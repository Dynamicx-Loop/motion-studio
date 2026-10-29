"""Freeze audited correspondence and paired motion configs without editing inputs."""
from pathlib import Path
import hashlib,json,shutil,subprocess
ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
OUT=ROOT/'outputs/umr-motion-preliminary-v1'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 records={}
 for robot in ['g1','astro']:
  for center in ['spine1','bbox50']:
   arm=f'smplx_{robot}_{center}'
   folder='astro-hands-correspondence' if robot=='astro' else 'soma-correspondence-audit'
   source=ROOT/'experiments'/folder/f'{arm}.json'
   c=json.loads(source.read_text()); dest=OUT/arm;dest.mkdir(exist_ok=False)
   inputs={}
   for key,p in [('dataset',Path(c['correspondence']['dataset']['out'])),('slots',Path(c['correspondence']['train']['out_dir'])/'correspondence_slots_final.npz')]:
    target=dest/f'{key}.npz';shutil.copy2(p,target);inputs[key]={'source':str(p),'copy':str(target),'sha256':sha(target)}
   c['correspondence']['dataset']['out']=str(dest/'dataset.npz')
   c['correspondence']['slots']=str(dest/'slots.npz')
   c['correspondence']['train']['out_dir']=str(dest/'unused-training')
   c['motion'].update(start=0,end=1080,stride=3,max_frames=0)
   c['retarget']['out']=str(dest/'trajectory.npz')
   c['retarget'].update(smplx_batch_size=128,smplx_batch_size_max=128)
   c['view']['enabled']=False
   c['experiment']={'stage':'offline_motion','retarget_authorized':True,'protocol':'first 12 seconds, every third frame, all four matched centering arms; no objective ablation'}
   (HERE/f'{arm}.json').write_text(json.dumps(c,indent=2)+'\n')
   inputs['config']={'sha256':sha(HERE/f'{arm}.json')}
   inputs['motion']={'path':c['motion']['data'],'sha256':sha(Path(c['motion']['data']))}
   records[arm]=inputs
 for repo in ['UMR','UMR-astro-surface-experiment']:
  p=ROOT/'externals'/repo
  patch=subprocess.check_output(['git','-C',str(p),'diff','HEAD'])
  (HERE/f'{repo}.patch').write_bytes(patch)
  records[repo]={'head':subprocess.check_output(['git','-C',str(p),'rev-parse','HEAD'],text=True).strip(),'patch_sha256':hashlib.sha256(patch).hexdigest()}
 (HERE/'inputs.json').write_text(json.dumps(records,indent=2)+'\n')
if __name__=='__main__':main()
