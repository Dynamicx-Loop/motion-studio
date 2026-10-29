"""Static actual-triangle inspection panels; no subsampling of robot geometry."""
from pathlib import Path
import json,numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'outputs/soma-correspondence-audit';VIEW=OUT/'viewer'
payload=json.loads((VIEW/'audit.json').read_text());arms=payload['arms']
filters=[['head/face','neck'],['torso'],['leftUpLeg','rightUpLeg'],['leftForeArm','rightForeArm']]
colors=['#dc2f5b','#bc8300','#3869b1','#00856c']
for center in ['spine1','bbox50']:
    fig,axes=plt.subplots(4,6,figsize=(19,13),facecolor='white')
    columns=[('smplx','human'),('smplx','astro'),('smplx','g1'),('soma','human'),('soma','astro'),('soma','g1')]
    for col,(source,robot) in enumerate(columns):
        a=arms[f'{source}_{"astro" if robot=="human" else robot}_{center}']
        meta=a['human_mesh'] if robot=='human' else a['mesh']
        v=np.fromfile(VIEW/meta['vertices']['file'],dtype='<f4').reshape(-1,3)
        f=np.fromfile(VIEW/meta['faces']['file'],dtype='<u4').reshape(-1,3)
        tri=v[f];tri=tri[np.argsort(tri[:,:,2].mean(1))]
        points=np.array(a['human'] if robot=='human' else a['projected']);labels=np.array(a['source_common'])
        for row,segments in enumerate(filters):
            ax=axes[row,col];ax.add_collection(PolyCollection(tri[:,:,:2],facecolor='#c8cdd2',edgecolor='none',rasterized=True))
            mask=np.isin(labels,segments);ax.scatter(points[mask,0],points[mask,1],s=5,c=colors[row],zorder=3,linewidths=0)
            if row==0:
                neck=labels=='neck';ax.scatter(points[neck,0],points[neck,1],s=5,c='#00a9c7',zorder=4,linewidths=0)
            if robot!='human' and row in [2,3]:
                for side in ['left','right']:
                    q=a['anchors'][side+('_knee_joint' if row==2 else '_elbow_joint')]
                    ax.plot([q[1]-.05,q[1]+.05],[q[2],q[2]],c='black',lw=1,zorder=5)
            ax.set_aspect('equal');ax.set_xlim(v[:,0].min()-.035,v[:,0].max()+.035);ax.set_ylim(v[:,1].min()-.035,v[:,1].max()+.035);ax.axis('off')
            if row==0:ax.set_title(source.upper()+' · '+robot,fontsize=12)
            if col==0:ax.text(-.07,.5,['Head / neck','Torso','Thigh','Forearm'][row],transform=ax.transAxes,rotation=90,va='center',fontsize=12)
    fig.suptitle(f'Static correspondence · {center} · actual triangles, independent equal-height panels\nHead/face red; neck cyan. Highlighted slots visible through geometry. Different source shapes and samples; no cross-source slot identity.',fontsize=13)
    fig.subplots_adjust(top=.91,bottom=.025,left=.035,right=.995,hspace=.06,wspace=.08)
    fig.savefig(OUT/f'segment-evidence-{center}.png',dpi=150);plt.close(fig)
