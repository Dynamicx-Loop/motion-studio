"""Compare winding of each convex selected primitive without changing the model."""
from pathlib import Path
import importlib.util,json
import numpy as np,mujoco
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent

def main():
    model=mujoco.MjModel.from_xml_path(str(ROOT/'externals/UMR/assets/mimickit/humanoid.xml'));result={}
    for label,directory in [('baseline','UMR'),('experimental','UMR-astro-surface-experiment')]:
        spec=importlib.util.spec_from_file_location(label,ROOT/'externals'/directory/'scripts/mujoco_geom_surface.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);rows=[]
        for g in module.surface_geom_ids(model,'auto'):
            v,f=module.geom_local_mesh(model,int(g));t=v[f];normal=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]);area=np.linalg.norm(normal,axis=1)
            dot=np.einsum('ij,ij->i',normal,t.mean(1)-v.mean(0))
            rows.append(dict(geom=int(g),name=model.geom(int(g)).name,triangles=len(f),degenerate=int((area<=1e-12).sum()),inward=int((dot < -1e-12).sum()),outward=int((dot>1e-12).sum())))
        result[label]=rows
    (HERE/'mimickit-geometry-gate.json').write_text(json.dumps(result,indent=2)+'\n')
    summary={k:{s:sum(r[s] for r in rows) for s in ['triangles','degenerate','inward','outward']} for k,rows in result.items()}
    assert summary['experimental']['inward']==summary['experimental']['degenerate']==0
    print(summary)
if __name__=='__main__':main()
