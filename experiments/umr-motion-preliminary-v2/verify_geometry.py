"""Check concurrent model edits did not alter audited visual/kinematic binding."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts'))
from motion_data_paths import canonical_motion_path
import json,hashlib,subprocess,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).parent
repo=Path('/data/workspace/notAnyrobot/menagerie_x');rel='robots/astro_p2_43dof_dex3_1/astro_p2_43dof_dex3_1.xml'
old=subprocess.check_output(['git','-C',str(repo),'show','1316cac090144c9891453a53b8336e8374c96196:'+rel]);now=(repo/rel).read_bytes()
def strip(b):
 r=ET.fromstring(b)
 for parent in r.iter():
  for child in list(parent):
   if child.tag=='geom' and child.get('group')=='3':parent.remove(child)
 return ET.tostring(r)
assert strip(old)==strip(now),'Non-collision XML change invalidates binding!'
records=json.loads((ROOT/'experiments/astro-hands-correspondence/asset-inspection.json').read_text());checked=0
for p,h in records['asset_hashes'].items():
 if '/meshes/' in p:
  assert hashlib.sha256(canonical_motion_path(p).read_bytes()).hexdigest()==h,p;checked+=1
record={'visual_kinematic_xml_equal_after_removing_group3_geoms':True,'audited_mesh_hashes_match':checked,'current_xml_sha256':hashlib.sha256(now).hexdigest(),'audited_xml_sha256':hashlib.sha256(old).hexdigest(),'note':'Concurrent collision-only refinements preserved, not used for binding or self-collision. Numeric geom IDs can shift; binding is rebuilt against current model, not reused by numeric ID.'}
(HERE/'geometry-compatibility.json').write_text(json.dumps(record,indent=2)+'\n');print(record)
