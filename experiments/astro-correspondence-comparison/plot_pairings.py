#!/usr/bin/env python3
"""Static paired-slot inspection; no inference of motion quality."""
from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'outputs/astro-correspondence-comparison'
data=json.loads((OUT/'viewer/pairings.json').read_text())
h=np.asarray(data['visual']['human'])
lo=h.min(0);hi=h.max(0)
colors=np.clip((h-lo)/(hi-lo),0,1)
fig,axes=plt.subplots(2,2,figsize=(16,10),facecolor='#f3f6fa')
for row,arm in enumerate(['visual','primitive']):
 item=data[arm];human=np.asarray(item['human']);robot=np.asarray(item['projected'])
 human[:,0]-=1.15;robot[:,0]+=1.15
 human[:,1]-=human[:,1].min();robot[:,1]-=robot[:,1].min()
 bad=np.asarray(item['invalid'],dtype=int)
 for col,(title,direction) in enumerate([('Front',1),('Back',-1)]):
  ax=axes[row,col];ax.set_facecolor('#f3f6fa')
  for p in [human,robot]:ax.scatter(direction*p[:,0],p[:,1],c=colors,s=2.2,linewidths=0)
  for i in range(0,4096,64):ax.plot(direction*np.array([human[i,0],robot[i,0]]),[human[i,1],robot[i,1]],c='#526175',alpha=.1,lw=.4)
  if len(bad):ax.scatter(direction*robot[bad,0],robot[bad,1],c='#ec253b',s=4,linewidths=0)
  ax.set_aspect('equal');ax.set_xlim(-2.65,2.65);ax.set_ylim(-.1,1.85);ax.axis('off')
  names=['Human','Astro'] if direction==1 else ['Astro','Human']
  ax.text(-1.15,1.76,names[0],ha='center',fontsize=10,color='#475569');ax.text(1.15,1.76,names[1],ha='center',fontsize=10,color='#475569')
  verdict='production binding accepted' if not len(bad) else f'production binding REJECTED: {len(bad)}/4096 buried projections'
  ax.set_title(f'{arm.title()} surfaces · {title}\n{verdict}',fontsize=13,color='#17253a')
fig.suptitle('Same human slots → separately trained Astro correspondences',fontsize=19,color='#17253a',y=.98)
fig.text(.5,.03,'Projected diagnostic view · matching colours = shared human position · red = rejected buried projection\nEvery 64th slot linked · metres, separate floor offsets · no motion retargeting',ha='center',fontsize=11,color='#475569')
fig.subplots_adjust(left=.02,right=.98,top=.9,bottom=.1,hspace=.25,wspace=.08)
fig.savefig(OUT/'pairings-comparison.png',dpi=170)
