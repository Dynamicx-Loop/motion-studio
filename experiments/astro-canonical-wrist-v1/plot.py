"""Actual-triangle left-hand closeups; same limits within each raw/corrected pair."""
import hashlib,json,sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent;OUT=ROOT/'outputs/astro-canonical-wrist-v1'
controls=json.loads((HERE/'preparation.json').read_text())['controls'];inputs={}
def read(p):
    p=Path(p);inputs[str(p.relative_to(ROOT))]=hashlib.sha256(p.read_bytes()).hexdigest();return np.load(p,allow_pickle=True)
fig,axes=plt.subplots(4,4,figsize=(16,12),layout='constrained')
for row,(source,center) in enumerate([(s,c) for s in ['smplx','soma'] for c in ['spine1','bbox50']]):
    for col,robot in [(0,'astro'),(2,'g1')]:
        arm=f'{source}_{robot}_{center}';ds=read(controls[arm]['dataset']);v=ds['mesh_vertices_1'];f=ds['mesh_faces_1'];tri=v[f][:,:,:2]
        # Source-frame +X is left/outward, +Y is up. Real physical metre axes.
        crop=(tri[:,:,0].max(axis=1)>.40)&(tri[:,:,0].min(axis=1)<1.02)
        for delta,exp in [(0,controls[arm]['experiment']),(1,'astro-canonical-wrist-v1')]:
            a=read(ROOT/'outputs'/exp/f'{arm}-audit.npz');p=a['robot_projected'][:,[1,2]];ax=axes[row,col+delta]
            ax.add_collection(PolyCollection(tri[crop],facecolors='#d4dbe2',edgecolors='none',rasterized=True))
            for label,color in [('leftForeArm','#0b986a'),('leftHand','#ba2a98')]:
                mask=a['source_common']==label;ax.scatter(p[mask,0],p[mask,1],s=10,c=color,zorder=3)
            params=json.loads((HERE/'calibration-parameters.json').read_text())[arm]['32']['calibrations'][0]
            start,tip=params['palm_start_outward'],params['tip_outward'];ax.axvline(start,color='#253449',lw=1,ls='--')
            ax.set_xlim(start-.23,tip+.025)
            handverts=v[(v[:,0]>start-.23)&(v[:,0]<tip+.025)];y0,y1=handverts[:,1].min(),handverts[:,1].max();ax.set_ylim(y0-.025,y1+.025)
            ax.set_aspect('equal');ax.grid(alpha=.18);ax.set_title(f'{source.upper().replace("SMPLX","SMPL-X")} {center} | {"Astro Dex3" if robot=="astro" else "G1"} | {"raw" if delta==0 else "calibrated"}',fontsize=10)
            ax.set_xlabel('Outward distance (m)',fontsize=8);ax.set_ylabel('Height (m)',fontsize=8);ax.tick_params(labelsize=7)
fig.suptitle('Canonical Astro d207095 | static wrist/palm calibration | matched raw controls\nMagenta: human hand slots; green: human forearm slots; dashed: actual hand mesh start',fontsize=16)
path=OUT/'wrist-calibration-closeups.png';fig.savefig(path,dpi=160);plt.close(fig)
(HERE/'figure-provenance.json').write_text(json.dumps({'figure_language':'en','inputs':inputs,'outputs':{str(path.relative_to(ROOT)):hashlib.sha256(path.read_bytes()).hexdigest()},'view':'left hands; both hands measured in tables; fixed physical metre scales within matched pairs'},indent=2)+'\n')
