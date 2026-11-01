"""Rebuild actual pinned native-pose robot card thumbnails (Pillow/NumPy needed)."""
from pathlib import Path
import sys
import tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from motion_studio.studio import Studio
from PIL import Image,ImageDraw
import numpy as np,json
temporary=tempfile.TemporaryDirectory(prefix='studio-thumbnail-state-')
s=Studio(Path(temporary.name))
for key in ['g1','k1','piplus','t800']:
 r=s.add_builtin_robot(key);a=r['asset'];q=r['pose']['qpos'];geometry=json.loads(s.robot_file(a['asset_id'],'geometry.json').read_text());pose=s.preview_robot(a['asset_id'],q)
 polys=[];bounds=[]
 # Front-facing perspective: native robot +X points toward the camera.
 for g,t in zip(geometry['geometries'],pose['transforms']):
  v=np.asarray(g['vertices'])@np.asarray(t['rotation']).reshape(3,3).T+np.asarray(t['position']);f=np.asarray(g['faces']);bounds.extend(v[:,[1,2]])
  color=np.asarray(g['rgba'][:3]);
  for face in f:
   points=v[face];normal=np.cross(points[1]-points[0],points[2]-points[0]);norm=np.linalg.norm(normal)
   shade=.55+.4*abs(np.dot(normal/(norm or 1),[.7,-.3,.65]));rgb=tuple((np.clip(color*shade,0,1)*255).astype(int))
   polys.append((float(points[:,0].mean()),points[:,[1,2]],rgb))
 bounds=np.asarray(bounds);low=bounds.min(0);high=bounds.max(0);scale=min(280/(high[0]-low[0]),240/(high[1]-low[1]));center=(low+high)/2
 im=Image.new('RGB',(320,280),'#f5f7fa');draw=ImageDraw.Draw(im)
 for _,p,c in sorted(polys,key=lambda x:x[0]):
  xy=(p-center)*[scale,-scale]+[160,140];draw.polygon([tuple(x) for x in xy],fill=c)
 im.save(Path('motion_studio/studio/web/thumbnails')/(key+'.png'),optimize=True)
 print(key,len(polys),flush=True)

temporary.cleanup()
