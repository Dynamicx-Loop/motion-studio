"""Static orthographic evidence with complete actual selected target geometry."""
from pathlib import Path
import json,numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'outputs/segment-binding-audit';VIEW=OUT/'viewer'
data=json.loads((VIEW/'audit.json').read_text());arms=data['arms']
fig,axes=plt.subplots(4,4,figsize=(15,14),facecolor='white')
filters=[['head'],['torso'],['leftUpLeg','rightUpLeg'],['leftForeArm','rightForeArm']]
colors=['#dc2f5b','#de9c00','#3869b1','#03a080']
for col,name in enumerate(['human','visual','primitive','g1']):
 meta=data['human_mesh'] if name=='human' else arms[name]['mesh']
 v=np.fromfile(VIEW/meta['vertices']['file'],dtype='<f4').reshape(-1,3)
 f=np.fromfile(VIEW/meta['faces']['file'],dtype='<u4').reshape(-1,3)
 triangles=v[f];order=np.argsort(triangles[:,:,2].mean(1));triangles=triangles[order]
 h=arms['visual'] if name=='human' else arms[name]
 points=np.array(h['human'] if name=='human' else h['projected']);labels=np.array(h['source_labels'])
 for row,segments in enumerate(filters):
  ax=axes[row,col];ax.add_collection(PolyCollection(triangles[:,:,:2],facecolor='#c8cdd2',edgecolor='none',rasterized=True))
  mask=np.isin(labels,segments);ax.scatter(points[mask,0],points[mask,1],s=5,c=colors[row],zorder=3,linewidths=0)
  if row==0:
   neck=mask&(np.array(h['source55'])==12);ax.scatter(points[neck,0],points[neck,1],s=8,c='#00a9c7',zorder=4,linewidths=0)
  if name!='human':
   a=h['anchors']
   for side in ['left','right']:
    key=side+('_knee_joint' if row==2 else '_elbow_joint')
    if row in [2,3]:
     q=a[key];ax.plot([q[1]-.05,q[1]+.05],[q[2],q[2]],c='black',lw=1,zorder=5)
  ax.set_aspect('equal');ax.set_xlim(v[:,0].min()-.035,v[:,0].max()+.035);ax.set_ylim(v[:,1].min()-.035,v[:,1].max()+.035);ax.axis('off')
  if row==0:ax.set_title({'human':'Human source','visual':'Astro visual','primitive':'Astro primitive\nREJECTED binding','g1':'G1 matched control'}[name],fontsize=13)
  if col==0:ax.text(-.06,.5,' / '.join(segments),transform=ax.transAxes,rotation=90,va='center',ha='right',fontsize=11)
fig.suptitle('Static segment transfers on actual selected geometry\nHead/face red; neck cyan. All highlighted points shown through the surface; front orthographic view.',fontsize=14)
fig.subplots_adjust(top=.91,bottom=.035,left=.045,right=.99,hspace=.08,wspace=.08)
fig.savefig(OUT/'segment-evidence.png',dpi=160)
