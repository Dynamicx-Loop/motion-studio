"""Fixed-mean-shape Wendy conversion; keeps diagnostics and true source timing."""
import argparse
import json
from pathlib import Path
import numpy as np
from hiphi2smplx.pipeline import ConversionConfig, fit_bvh, save_result
from hiphi2smplx.skeleton import HIPHI_MAP, SOURCE_SKELETON_MAPS
from hiphi2smplx.bvh import load_bvh

ROOT = Path(__file__).resolve().parents[1]
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--config', type=Path, default=ROOT / 'configs/umr/wendy-preview.json')
a = p.parse_args()
c = json.loads(a.config.read_text())
SOURCE_SKELETON_MAPS['wendy'] = {**HIPHI_MAP, **c['mapping_overrides']}
out = ROOT / c['output']
if out.exists():
    raise FileExistsError(out)
start = c.get('start_frame', 0)
source_path = Path(c['source'])
if start:
    lines = source_path.read_text().splitlines()
    motion = lines.index('MOTION')
    data = lines[motion + 3:]
    selected = data[start:start + c['frames']]
    if len(selected) != c['frames']:
        raise ValueError('Excerpt exceeds source motion')
    source_path = out.with_suffix('.source.bvh')
    source_path.parent.mkdir(parents=True, exist_ok=True)
    source_path.write_text('\n'.join(lines[:motion + 1] + [f'Frames: {len(selected)}', lines[motion + 2]] + selected) + '\n')
r = fit_bvh(source_path, c['model'], np.asarray(c['betas'], dtype=np.float32),
            skeleton_map='wendy', max_frames=c['frames'], config=ConversionConfig(progress=True))
for value in (r.poses, r.trans, r.betas, r.fitted_joints, r.residuals, r.final_losses):
    assert np.isfinite(value).all()
save_result(out, r)
with np.load(out) as z:
    fields = dict(z)
fields['output_up'] = np.asarray(c['output_up'])
np.savez_compressed(out, **fields)
source = load_bvh(source_path, unit_scale=c['unit_scale']).sliced(len(r.poses))
positions, _ = source.world_transforms()
np.savez_compressed(out.with_suffix('.diagnostics.npz'), fitted_joints=r.fitted_joints,
    residuals=r.residuals, final_losses=r.final_losses, source_joints=positions,
    source_parents=source.skeleton.parents, source_names=source.skeleton.joint_names)
report = dict(start_frame=start, frames=len(r.poses), frame_time=r.frame_time, fps=1/r.frame_time,
    duration_seconds=len(r.poses)*r.frame_time, output_up=c['output_up'], units='meters',
    residual_mean_m=float(r.residuals.mean()), residual_max_frame_mean_m=float(r.residuals.max()),
    trans_min=r.trans.min(0).tolist(), trans_max=r.trans.max(0).tolist(),
    source_bounds=[positions.min((0,1)).tolist(), positions.max((0,1)).tolist()],
    all_finite=True, shape='neutral zero betas', fingers='not fitted', face='not fitted')
out.with_suffix('.report.json').write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps(report, indent=2))
