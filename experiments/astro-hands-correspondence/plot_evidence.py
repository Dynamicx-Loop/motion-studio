"""Render actual saved triangles and paired slots; one English image per figure."""
import hashlib
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
OUT=ROOT/'outputs/astro-hands-correspondence'
INPUTS={}
ROWS=[(['head/face','neck'],'Head / neck','#dc2f5b'),(['leftShoulder','rightShoulder'],'Shoulder / clavicle','#8a48bd'),(['torso'],'Torso','#bc8300'),(['hips'],'Hips / pelvis','#dd632b'),(['leftUpLeg','rightUpLeg'],'Thigh','#3869b1'),(['leftForeArm','rightForeArm'],'Forearm','#00856c'),(['leftHand','rightHand'],'Hands','#bb397c')]

def read(p):
    b=p.read_bytes();INPUTS[str(p.relative_to(ROOT))]=hashlib.sha256(b).hexdigest();return b

def main():
    views={k:ROOT/'outputs'/v/'viewer' for k,v in [('old','soma-correspondence-audit'),('new','astro-hands-correspondence')]}
    payload={k:json.loads(read(v/'audit.json'))['arms'] for k,v in views.items()}
    checks=[]
    for center in ['spine1','bbox50']:
        columns=[(s,n) for n in ['human','old','new','g1'] for s in ['smplx','soma']]
        fig,axes=plt.subplots(7,8,figsize=(24,20),facecolor='white')
        for col,(source,name) in enumerate(columns):
            cohort='new' if name=='new' else 'old';vdir=views[cohort]
            arm=f'{source}_{"g1" if name=="g1" else "astro"}_{center}';a=payload[cohort][arm]
            meta=a['human_mesh'] if name=='human' else a['mesh']
            v=np.frombuffer(read(vdir/meta['vertices']['file']),dtype='<f4').reshape(-1,3)
            f=np.frombuffer(read(vdir/meta['faces']['file']),dtype='<u4').reshape(-1,3)
            height=np.ptp(v[:,1]); offset=np.array([(v[:,0].min()+v[:,0].max())/2,v[:,1].min(),0])
            v=(v-offset)/height
            tri=v[f];tri=tri[np.argsort(tri[:,:,2].mean(1))]
            p=(np.asarray(a['human'] if name=='human' else a['projected'])-offset)/height;labels=np.asarray(a['source_common'])
            for row,(segments,title,color) in enumerate(ROWS):
                ax=axes[row,col];mask=np.isin(labels,segments)
                expected=sum(r['slots'] for r in a['metrics']['common_per_segment'] if r['source'] in segments)
                assert int(mask.sum())==expected
                checks.append(dict(arm=arm,cohort=cohort,row=title,slots=expected))
                ax.add_collection(PolyCollection(tri[:,:,:2],facecolor='#c8cdd2',edgecolor='none',rasterized=True))
                ax.scatter(p[mask,0],p[mask,1],s=5,c=color,zorder=3,linewidths=0)
                if row==0:
                    neck=labels=='neck';ax.scatter(p[neck,0],p[neck,1],s=5,c='#00a9c7',zorder=4,linewidths=0)
                if name!='human' and row in [4,5,6]:
                    joint={4:'knee',5:'elbow',6:'wrist_roll'}[row]
                    for side in ['left','right']:
                        q=a['anchors'][side+'_'+joint+'_joint'];x=(q[1]-offset[0])/height;y=(q[2]-offset[1])/height;ax.plot([x-.03,x+.03],[y,y],c='black',lw=1,zorder=5)
                ax.set_aspect('equal');ax.set_xlim(-.8,.8);ax.set_ylim(-.025,1.025);ax.axis('off')
                if row==0:ax.set_title(source.upper().replace('SMPLX','SMPL-X')+'\n'+{'human':'Human source','old':'Astro OLD: no mesh hands','new':'Astro NEW: Dex3-1','g1':'G1 control (reused)'}[name],fontsize=11)
                if col==0:ax.text(-.06,.5,title,transform=ax.transAxes,rotation=90,va='center',ha='right',fontsize=11)
        fig.suptitle(f'Astro with hands: static correspondence / {center} / seed 0, 500 epochs\nSame human samples; new robot surface resampled once. Actual triangles; points visible through surfaces; independently fitted equal-height panels.\nHead/face red, neck cyan. Black marks: knee, elbow, wrist. Historical results and G1 controls are reused unchanged.',fontsize=13)
        fig.subplots_adjust(top=.92,bottom=.02,left=.035,right=.995,hspace=.08,wspace=.08)
        fig.savefig(OUT/f'comparison-{center}.png',dpi=140);plt.close(fig)
    # Close views make the newly selected finger/palm geometry inspectable.
    fig,axes=plt.subplots(4,2,figsize=(12,13),facecolor='white')
    for row,(source,center) in enumerate([(s,c) for s in ['smplx','soma'] for c in ['spine1','bbox50']]):
        a=payload['new'][f'{source}_astro_{center}'];meta=a['mesh'];vdir=views['new']
        v=np.frombuffer(read(vdir/meta['vertices']['file']),dtype='<f4').reshape(-1,3);f=np.frombuffer(read(vdir/meta['faces']['file']),dtype='<u4').reshape(-1,3);tri=v[f]
        p=np.asarray(a['projected']);labels=np.asarray(a['source_common'])
        for col,side in enumerate(['left','right']):
            ax=axes[row,col];q=a['anchors'][side+'_wrist_roll_joint'];sign=1 if side=='left' else -1
            keep=sign*tri[:,:,0].max(1)>sign*q[1]-.12 if side=='left' else tri[:,:,0].min(1)<q[1]+.12
            t=tri[keep];t=t[np.argsort(t[:,:,2].mean(1))]
            ax.add_collection(PolyCollection(t[:,:,:2],facecolor='#c8cdd2',edgecolor='none',rasterized=True))
            for label,color in [(side+'Hand','#bb397c'),(side+'ForeArm','#00856c')]:
                m=labels==label;ax.scatter(p[m,0],p[m,1],s=13,c=color,label=label,zorder=3,linewidths=0)
            ax.axvline(q[1],color='black',lw=1);ax.set_xlim((q[1]-.12,v[:,0].max()+.025) if side=='left' else (v[:,0].min()-.025,q[1]+.12));ax.set_ylim(q[2]-.14,q[2]+.14);ax.set_aspect('equal');ax.set_title(f'{source.upper()} / {center} / {side}');ax.legend(fontsize=8)
    fig.suptitle('New Astro hands: source hand slots (magenta) and forearm slots (green)\nBlack line = wrist plane. Anatomical hand-zone precision differs from actual Dex3 mesh ownership.',fontsize=13)
    fig.tight_layout(rect=(0,0,1,.94));fig.savefig(OUT/'hand-closeups.png',dpi=160);plt.close(fig)
    read(Path(__file__))
    (HERE/'figure-provenance.json').write_text(json.dumps({'figure_language':'en','inputs':INPUTS,'source_mask_checks':checks,'outputs':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in OUT.glob('*.png')}},indent=2)+'\n')

if __name__=='__main__':main()
