"""Re-evaluate production projection for the minimal observed hand/wrist failure."""
import argparse
import json
import sys
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import mujoco
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'externals/UMR-astro-surface-experiment/scripts'))
import retarget_smpl_to_humanoid_surface_vector as rb
from humanoid_retarget_config import load_config

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--slots',type=Path)
    args=parser.parse_args()
    c=load_config(ROOT/'experiments/astro-hands-correspondence/smplx_astro_bbox50.json')
    frozen=ROOT/'outputs/astro-hand-wrist-correction/asset-snapshot/astro.xml'
    if frozen.exists():c['robot']['xml']=str(frozen)
    a=np.load(ROOT/'outputs/astro-hands-correspondence/smplx_astro_bbox50-audit.npz')
    learned=a['robot_learned'] if args.slots is None else np.load(args.slots)['reconstructed_slots'][1]
    model=mujoco.MjModel.from_xml_path(c['robot']['xml'])
    binding=rb.bind_robot_slots(model,SimpleNamespace(config_data=c),learned)
    # Stored sample mask is immutable; it selects exactly the same source slots.
    mask=a['source_common']=='leftHand'
    geoms=binding['geom_ids']
    meshes=np.array([model.mesh(int(model.geom_dataid[g])).name for g in geoms])
    if args.slots is None:np.testing.assert_array_equal(meshes,a['mesh_names'])
    actual=mask&np.char.startswith(meshes,'left_hand_')
    wrist=mask&np.char.startswith(meshes,'left_wrist_')
    print(json.dumps({'source_hand_slots':int(mask.sum()),'actual_Dex3':int(actual.sum()),'wrist_housing':int(wrist.sum())}))
    assert wrist.sum() < mask.sum()/2, 'Observed failure: a majority of left-hand slots bind to wrist housing'

if __name__=='__main__':main()
