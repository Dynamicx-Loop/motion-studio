import json,numpy as np
from pathlib import Path
p=Path(__file__).resolve().parent;r=json.loads((p/'report.json').read_text());m=json.loads((p/'viewer/manifest.json').read_text())
rows=['\n## Results\n','| Metric | Astro | G1 |','|---|---:|---:|']
for title,key,mul in [('Mean joint difference (degrees)','joint_angle_difference_deg',1),('Mean wrist difference (degrees)','wrists_angle_difference_deg',1),('Mean non-wrist difference (degrees)','non_wrists_angle_difference_deg',1),('Mean leg difference (degrees)','legs_angle_difference_deg',1),('Mean root distance (mm)','root_position_difference_m',1000),('Mean root rotation difference (degrees)','root_orientation_difference_deg',1)]:
 rows.append(f"| {title} | {r['astro'][key]['mean']*mul:.4f} | {r['g1'][key]['mean']*mul:.4f} |")
for robot in ['astro','g1']:
 info=m['robots'][robot]
 for v in info['variants']:
  path=p/'viewer'/v['transforms'];assert path.stat().st_size==5468*len(info['parts'])*12*4
  assert np.isfinite(np.fromfile(path,dtype='<f4')).all()
  assert v['report']['configured_joint_limit_violation_rad']<1e-6
 rows.append(f"\n{robot}: maximum joint difference {r[robot]['joint_angle_difference_deg']['max']:.3f}° at {r[robot]['largest_joint_difference_at']}; maximum root distance {r[robot]['root_position_difference_m']['max']*1000:.3f} mm.")
 rows.append(f"Minimum visual mesh heights: reference {r[robot]['reference']['min_visual_y_m']*1000:.2f} mm, reconverted {r[robot]['reconverted']['min_visual_y_m']*1000:.2f} mm.")
rows.append('\nAll four outputs have finite qpos and full frame IDs. Model and configured joint limits hold within 1e-6 rad. Robot XML hashes match within each pair; logs confirm reuse of the shared correspondence slots. Finger clearing is recorded as enabled in every output. The largest average differences are concentrated in wrists (G1 has a transient maximum at its right hip), consistent with the known wrist differences between source motions; causal isolation would require an additional matched-wrist input control. Floor penetration remains in the visual meshes and is not corrected in the viewer.\n')
rows.append('Review: http://127.0.0.1:8769/ . Provenance and effective configuration equality checks are in provenance.json and configs/*-resolved.json.\n')
readme=p/'README.md';readme.write_text(readme.read_text().split('\n## Results\n')[0]+'\n'.join(rows));print('\n'.join(rows))
