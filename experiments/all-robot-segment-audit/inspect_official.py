"""Read official demo metadata and verify declared asset URLs; never run its pipeline."""
import concurrent.futures,hashlib,json,re,urllib.parse,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'outputs/all-robot-segment-audit/official'
BASE='https://hanyang9.github.io/UMR/'
FILES={'umr_studio.html':'umr_studio.html','umr-studio-page.js':'static/js/umr-studio-page.js?v=20260927-hiphi-sit-lqr-v1',
 'mujoco-viewer.js':'static/js/mujoco-viewer.js?v=20260927-hiphi-sit-lqr-v1',
 'manifest.json':'static/assets/studio_robot_presets/manifest.json?v=20260905-studio-robot-presets-v1',
 'browser-runtime.js':'static/js/browser-umr-runtime-exact-v1.js?v=20260927-hiphi-sit-lqr-v1'}

def fetch(name,relative):
    url=urllib.parse.urljoin(BASE,relative);b=urllib.request.urlopen(url,timeout=40).read();(OUT/name).write_bytes(b)
    return dict(url=url,file=name,bytes=len(b),sha256=hashlib.sha256(b).hexdigest())

def head(item):
    robot,file,url=item
    try:
        with urllib.request.urlopen(urllib.request.Request(url,method='HEAD'),timeout=40) as r:
            return dict(robot=robot,file=file,url=url,status=r.status,content_length=r.headers.get('Content-Length'))
    except Exception as e:return dict(robot=robot,file=file,url=url,error=str(e))

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    sources=[fetch(n,r) for n,r in FILES.items()];m=json.loads((OUT/'manifest.json').read_text());assets=[];robots=[]
    for r in m['robots']:
        root=urllib.parse.urljoin(BASE+FILES['manifest.json'],r['asset_root']);xml=fetch(r['id']+'.xml',urllib.parse.urljoin(root,r['model_path']))
        robots.append({**r,'xml_source':xml,'checkpoint_files':[f for f in r['files'] if f.endswith(('.npz','.pt','.pth','.ckpt','.safetensors'))]})
        assets.extend((r['id'],f,urllib.parse.urljoin(root,f)) for f in r['files'])
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:checks=list(pool.map(head,assets))
    result=dict(retrieved_date='2026-10-23',sources=sources,robots=robots,asset_availability=checks)
    (ROOT/'experiments/all-robot-segment-audit/official-inventory.json').write_text(json.dumps(result,indent=2)+'\n')
    print('checked',len(checks),'assets; unavailable:',[x for x in checks if x.get('status')!=200])
if __name__=='__main__':main()
