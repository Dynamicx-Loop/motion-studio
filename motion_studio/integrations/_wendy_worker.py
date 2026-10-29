"""Private independent-runtime worker; numerical choices match the old CLI."""
from __future__ import annotations

import importlib.metadata
import json
from pathlib import Path
import platform
import sys


def main():
    job = json.loads(Path(sys.argv[1]).read_text())
    checkout, work = Path(job['checkout']), Path(job['work'])
    sys.path.insert(0, str(checkout / 'src'))
    import numpy as np
    import hiphi2smplx
    from hiphi2smplx.bvh import load_bvh
    from hiphi2smplx.pipeline import ConversionConfig, fit_bvh, save_result
    from hiphi2smplx.skeleton import HIPHI_MAP, SOURCE_SKELETON_MAPS

    if not Path(hiphi2smplx.__file__).resolve().is_relative_to(checkout / 'src'):
        raise RuntimeError('hiphi2smplx was imported outside the pinned checkout')
    environment = {
        'python': sys.version, 'executable': sys.executable, 'prefix': sys.prefix,
        'platform': platform.platform(), 'hiphi_module': hiphi2smplx.__file__,
        'packages': sorted((d.metadata['Name'], d.version)
                           for d in importlib.metadata.distributions() if d.metadata['Name'])}
    (work / 'environment.json').write_text(json.dumps(environment, indent=2) + '\n')
    c = job['config']
    # This process owns the registration; no mapping state crosses calls.
    SOURCE_SKELETON_MAPS['wendy'] = {**HIPHI_MAP, **c['mapping_overrides']}
    r = fit_bvh(job['source_for_fit'], c['model'], np.asarray(c['betas'], dtype=np.float32),
                skeleton_map='wendy', max_frames=c['frames'], config=ConversionConfig(progress=True))
    expected = c['frames']
    dimensions = ((r.poses, (expected, 55, 3)), (r.trans, (expected, 3)),
                  (r.betas, (10,)), (r.fitted_joints, (expected, 22, 3)),
                  (r.residuals, (expected,)), (r.final_losses, (expected,)))
    if any(a.shape != shape or not np.isfinite(a).all() for a, shape in dimensions):
        raise ValueError('Conversion returned invalid/nonfinite array shapes')
    if r.frame_time != job['frame_time'] or not np.array_equal(
            r.betas, np.asarray(c['betas'], dtype=np.float32)):
        raise ValueError('Conversion changed source timing or fixed shape')
    indices = np.arange(c['start_frame'], c['start_frame'] + expected, dtype=np.int64)
    timestamps = indices * r.frame_time
    out = work / 'motion.npz'
    save_result(out, r)
    with np.load(out, allow_pickle=False) as z:
        fields = dict(z)
    fields.update(output_up=np.asarray(c['output_up']), frame_time=np.asarray(r.frame_time),
                  source_frame_indices=indices, source_timestamps=timestamps)
    np.savez_compressed(out, **fields)
    source = load_bvh(job['source_for_fit'], unit_scale=c['unit_scale']).sliced(len(r.poses))
    positions, _ = source.world_transforms()
    if not np.isfinite(positions).all():
        raise ValueError('Source diagnostics contain nonfinite positions')
    np.savez_compressed(work / 'diagnostics.npz', fitted_joints=r.fitted_joints,
        residuals=r.residuals, final_losses=r.final_losses, source_joints=positions,
        source_parents=source.skeleton.parents, source_names=source.skeleton.joint_names,
        source_frame_indices=indices, source_timestamps=timestamps)
    report = dict(start_frame=c['start_frame'], frames=len(r.poses), frame_time=r.frame_time,
        fps=1/r.frame_time, duration_seconds=len(r.poses)*r.frame_time,
        output_up=c['output_up'], units='meters', residual_mean_m=float(r.residuals.mean()),
        residual_max_frame_mean_m=float(r.residuals.max()), trans_min=r.trans.min(0).tolist(),
        trans_max=r.trans.max(0).tolist(),
        source_bounds=[positions.min((0, 1)).tolist(), positions.max((0, 1)).tolist()],
        all_finite=True, shape='neutral zero betas' if not any(c['betas']) else 'neutral fixed betas',
        fingers='not fitted', face='not fitted', eyes='not fitted',
        end_frame_exclusive=c['start_frame'] + expected,
        source_start_seconds=float(timestamps[0]), source_last_seconds=float(timestamps[-1]),
        source_frames=job['source_frames'], pose_convention='SMPL-X 55 joints, axis-angle radians',
        mapping=job['mapping'], fixed_betas=c['betas'],
        conversions=['centimetres to metres (0.01)', 'BVH channel Euler degrees to axis-angle radians',
                     'fixed-shape body fitting; original source timing; no axis rotation/resampling',
                     'betas and fitted motion use upstream float32 arrays'],
        information_loss=['fixed neutral shape, not actor shape estimation',
                          'fingers, face and eyes not fitted', 'body fit is approximate'] +
                         (['source trimmed to half-open frame interval']
                          if c['start_frame'] or expected != job['source_frames'] else []))
    (work / 'report.json').write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')


if __name__ == '__main__':
    main()
