"""Static front projections of complete selected triangles and paired slots."""
from pathlib import Path
import json,numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'outputs/all-robot-segment-audit';VIEW=OUT/'viewer'
LABELS={'human':'Human source','visual':'Astro visual','primitive':'Astro primitive\nREJECTED','g1':'G1','piplus':'PiPlusPro','k1':'Booster K1','t800':'T800','h2':'H2','mimickit':'MimicKit','g1_racket':'G1 racket\nhuman-only control','g1_spherehand':'G1 sphere hands'}

def plot(data,names,filename):
    arms=data['arms'];fig,axes=plt.subplots(4,len(names),figsize=(3.15*len(names),13.5),facecolor='white')
    filters=[['head'],['torso'],['leftUpLeg','rightUpLeg'],['leftForeArm','rightForeArm']];colors=['#dc2f5b','#de9c00','#3869b1','#03a080']
    for col,name in enumerate(names):
        meta=data['human_mesh'] if name=='human' else arms[name]['mesh']
        v=np.fromfile(VIEW/meta['vertices']['file'],dtype='<f4').reshape(-1,3);f=np.fromfile(VIEW/meta['faces']['file'],dtype='<u4').reshape(-1,3)
        tri=v[f];tri=tri[np.argsort(tri[:,:,2].mean(1))]
        h=arms['g1'] if name=='human' else arms[name];points=np.array(h['human'] if name=='human' else h['projected']);labels=np.array(h['source_labels'])
        for row,segments in enumerate(filters):
            ax=axes[row,col];ax.add_collection(PolyCollection(tri[:,:,:2],facecolor='#c8cdd2',edgecolor='none',rasterized=True))
            mask=np.isin(labels,segments);ax.scatter(points[mask,0],points[mask,1],s=5,c=colors[row],zorder=3,linewidths=0)
            if row==0:
                neck=mask&(np.array(h['source55'])==12);ax.scatter(points[neck,0],points[neck,1],s=7,c='#00a9c7',zorder=4,linewidths=0)
            if name!='human' and row in [2,3]:
                for side in ['left','right']:
                    q=h['anchors'][side+('_knee_joint' if row==2 else '_elbow_joint')];ax.plot([q[1]-.04,q[1]+.04],[q[2],q[2]],c='black',lw=1,zorder=5)
            ax.set_aspect('equal');ax.set_xlim(v[:,0].min()-.03,v[:,0].max()+.03);ax.set_ylim(v[:,1].min()-.03,v[:,1].max()+.03);ax.axis('off')
            if row==0:ax.set_title(LABELS[name],fontsize=12)
            if col==0:ax.text(-.05,.5,' / '.join(segments),transform=ax.transAxes,rotation=90,va='center',ha='right',fontsize=10)
    fig.suptitle('Matched correspondence audit · actual selected geometry · no motion retargeting\nHead/face red; neck cyan. Points visible through geometry. Black marks: knee/elbow pivots. Each target fitted separately.',fontsize=13)
    fig.subplots_adjust(top=.91,bottom=.025,left=.04,right=.99,hspace=.06,wspace=.07);fig.savefig(OUT/filename,dpi=140);plt.close(fig)

def main():
    data=json.loads((VIEW/'audit.json').read_text())
    plot(data,['human','piplus','k1','g1','t800'],'demo-evidence.png')
    plot(data,['visual','h2','mimickit','g1_racket','g1_spherehand'],'additional-evidence.png')
    m=json.loads((ROOT/'experiments/all-robot-segment-audit/results.json').read_text());names=[n for n in data['arms'] if not n.endswith('_native_center')];sources=[r['source'] for r in m[names[0]]['per_segment']]
    a=np.array([[next(r['zone_precision'] if r.get('target_zone_available',True) else np.nan for r in m[n]['per_segment'] if r['source']==s) for n in names] for s in sources])
    fig,ax=plt.subplots(figsize=(12,10));im=ax.imshow(a,vmin=0,vmax=1,cmap='YlGnBu',aspect='auto');ax.set_xticks(range(len(names)),[LABELS[n] for n in names],rotation=35,ha='right');ax.set_yticks(range(19),sources)
    for i in range(19):
        for j in range(len(names)):ax.text(j,i,'N/A' if np.isnan(a[i,j]) else f'{a[i,j]*100:.0f}',ha='center',va='center',fontsize=8,color='white' if a[i,j]>.6 else 'black')
    ax.set_title('Strict zone compatibility (%) · heuristic diagnostic; no overall quality ranking\nN/A: selected target zone absent. Primitive column includes rejected projections.');fig.colorbar(im,ax=ax);fig.tight_layout();fig.savefig(OUT/'all-segments.png',dpi=150)
if __name__=='__main__':main()
