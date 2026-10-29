# Official UMR G1 reproduction through Motion Studio

Date / author: 2026-10-29 / Codex, requested by the project owner.

## Objective

Reproduce fresh official-default G1 correspondence training and the complete
bundled HiPHI getting-up clip through a Motion Studio-owned interface. Success
requires completed training/retargeting, compatible finite artifacts, all source
frames and FPS preserved, quaternion/joint-limit checks, and unchanged external
source and inputs. This is pipeline reproduction, not an official quality score
or a dynamics validation.

## Provenance

- Official UMR: `d1cdaedaf67a827198da71c5fa831f48b2e51f91`, official checkout;
  no source patch, experimental clone, or baseline worktree used.
- Input: bundled `Getting_up-get_up_0004/motion_actor_smplx.npz`; source/model/code
  SHA-256 values are in each run's `provenance.json`.
- Human: neutral SMPL-X, actor shape read by UMR from the bundled input; local
  licensed model under `/data/motions/human_models/smplx/1.1/`.
- Robot: official G1 29-DoF XML and shipped calibration/limit overrides, copied
  into the run with its asset bundle so generated XML stays outside the external.
- Environment: existing UMR Python runtime; package inventory and GPU recorded in
  `environment.json`. No dependencies installed or environment changed.
- Conventions: source Y-up; robot native Z-up; metres/radians; free-root qpos
  quaternion wxyz. Joint names and motion FPS are saved with the result.
- Training: official 500 epochs, batch two, all_samples, 4096 points; seed zero.
- Solver, contacts, calibration and trajectory filter remain the official defaults.
  Operational overrides: explicit paths/device, no viewer, and SMPL-X processing
  batch size 128 instead of 7567 for the local 8 GB GPU. No trimming/resampling.
- Input, model, robot assets and generated geometry retain their respective terms;
  raw files stay local under ignored outputs.

## Reproduction

From the Motion Studio root, on the host with GPU access:

```sh
python3 scripts/reproduce_umr_g1.py --output outputs/umr-g1-baseline/<fresh-run-id>
python3 -m unittest discover -s tests -v
```

The CLI calls `motion_studio.integrations.umr.reproduce_g1_baseline`. It refuses
existing outputs and unreviewed dependency revisions. Each stage has a bounded
runtime, command receipt and log. Training is limited to 600 s; motion to 7200 s.
Failures retain partial outputs and require an explicit fresh run.

Run `20261029-01` was intentionally interrupted after training while correcting a
validation field name (`poses` versus the loader's `pose_aa`). Its original logs
and successful preservation check remain in place. It is not the completed cohort.
Run `20261029-02` is the fresh corrected reproduction.

## Evaluation

Run `20261029-02` completed successfully. Raw output:
`outputs/umr-g1-baseline/20261029-02/motion.npz`.

| Check | Measured result |
| --- | --- |
| Build + 500-epoch training | 41.56 s, exit zero |
| Complete motion retarget stage | 96.88 s, exit zero; includes preprocessing/filtering |
| Source frame preservation | All 5,468 frames; IDs 0–5,467; 90.0009002686 Hz; no trimming/resampling |
| Motion shape / finiteness | `(5468, 36)`; all finite |
| Root quaternion norm error | Maximum `5.96e-8` |
| Model + configured joint-limit excess | `0.0` rad, tolerance `1e-6` rad |
| Absolute scalar-joint step | P95 `0.024253`, max `0.153127` rad/frame |
| Static target geometry consistency | Faces equal; vertices match within 200 nm |
| Official dataset/slot compatibility | Both pass; all_samples, `(2,4096,3)` finite slots |
| External and frozen input preservation | All recorded hashes, HEAD, and Git status unchanged |
| Historical static reproduction | Selected dataset arrays and reconstructed slots exactly equal to October 24 G1 |

Runtime is from this single local run, not a controlled benchmark. Duration by
frame count/FPS is 60.75495 s; elapsed first-to-last sample time is one frame less.

Small [validation](records/validation.json), [provenance](records/provenance.json),
[resolved configuration](records/resolved.json), environment, stage receipts and
artifact hashes are copied under `records/`; raw data/checkpoints/robot geometry
remain under ignored outputs. Original logs and records remain in the run.

The static comparison checks source/target mesh geometry, point samples and face
assignments, actor shape, and reconstructed slots. Run it in the UMR environment:

```sh
externals/UMR/.venv/bin/python experiments/umr-g1-baseline-20261029/compare_static.py \
  --fresh outputs/umr-g1-baseline/20261029-02 \
  --historical outputs/umr-astro-baseline-v1/static-20261024-01/g1 \
  --output /tmp/g1-static-comparison.json
```

See [static-comparison.json](static-comparison.json). Its equality checks establish
static numerical reproduction on this machine. The October 24 cohort contains no
motion result, so the new full trajectory has no matched historical reference.
No visual, ground/contact, foot-sliding, collision, or dynamics claim is implied
by successful solver execution or joint-limit checks.

Four public-interface safety tests passed. The adapter and worker remain below
200 lines each; no new abstract protocol or external source patch was needed.

## Observations and next step

See [the integration review](../../docs/umr-integration-review.md) for policy gaps
and their disposition. Existing static pair scripts and historical worktrees are
preserved; migrate other callers incrementally when their workflows are changed.
