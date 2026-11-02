# First official-default SMPL-X Astro/G1 static baseline

> **Status: legacy** — marked 2026-11-02. Retained as historical evidence.
> New experiments will establish the standard experiment contract; this record
> does not define that contract. “Current” and similar wording below refer to
> the original cohort or documentation snapshot. See the [experiment index](../README.md).

**Completed 2026-10-24; baseline candidate for review. No motion or ablation was run.**

Guideline and branch were approved before this bounded run. Both arms used fresh official UMR dataset preparation and 500-epoch, batch-two correspondence training. G1 completed in 39.04 seconds and Astro in 37.65 seconds; both exited zero within the 600-second bound.

Under the existing native19 anatomical-zone diagnostic, G1 has **3,562/4,096 compatible slots (86.96%)** and Astro **2,327/4,096 (56.81%)**. This single actor/seed shows a binding gap worth investigating. It does not establish statistical significance, acceptable performance, motion quality or a cause. Native19 segment denominators differ because official all-samples training learns the human slots independently in each arm.

| Source segment | G1 compatible / source slots | Astro compatible / source slots |
| --- | ---: | ---: |
| head | 408/415 (98.3%) | 91/413 (22.0%) |
| hips | 341/477 (71.5%) | 149/476 (31.3%) |
| leftArm | 93/93 (100.0%) | 60/83 (72.3%) |
| leftFoot | 100/142 (70.4%) | 132/136 (97.1%) |
| leftForeArm | 78/136 (57.4%) | 52/141 (36.9%) |
| leftHand | 100/100 (100.0%) | 95/95 (100.0%) |
| leftLeg | 252/265 (95.1%) | 231/269 (85.9%) |
| leftShoulder | 30/66 (45.5%) | 0/69 (0.0%) |
| leftUpLeg | 345/358 (96.4%) | 223/362 (61.6%) |
| leftUpperArm | 52/57 (91.2%) | 0/65 (0.0%) |
| rightArm | 100/100 (100.0%) | 59/89 (66.3%) |
| rightFoot | 101/143 (70.6%) | 135/139 (97.1%) |
| rightForeArm | 71/131 (54.2%) | 51/129 (39.5%) |
| rightHand | 98/98 (100.0%) | 97/97 (100.0%) |
| rightLeg | 260/290 (89.7%) | 255/292 (87.3%) |
| rightShoulder | 34/80 (42.5%) | 2/87 (2.3%) |
| rightUpLeg | 329/336 (97.9%) | 217/340 (63.8%) |
| rightUpperArm | 42/48 (87.5%) | 0/56 (0.0%) |
| torso | 728/761 (95.7%) | 478/758 (63.1%) |

The target-zone rules are inherited diagnostic conventions based on mesh identity and joint planes, not unique anatomical ground truth. Coverage uses an absolute 20 mm radius and is scale-sensitive. Do not read the aggregate as an official UMR benchmark score. Full per-segment precision, sample coverage, denominators and production bindings are in the run results.

Mean learned-slot projection distance to the visual mesh is 7.03 mm for G1 and 5.74 mm for Astro. A smaller projection distance does not imply better anatomical correspondence. This is not penetration depth. Mean difference between learned human slots across the two trainings is 14.29 mm, despite identical source mesh, actor shape and input samples.

## What was held fixed and what was integrated

- Official UMR source: `d1cdaedaf67a827198da71c5fa831f48b2e51f91`, unchanged tracked implementation. Shipped G1 configuration and official algorithm/hyperparameters retained. Explicit device/path selection and seed zero; no fixed-template override, wrist calibration, tuning, filter or objective change.
- Astro: inspected local menagerie_x `d2070956558ffbf9226dcf74017d40740724d8d8`. XML SHA-256 `c688a4177a1ff5ba07764f9e310bb62c33d24a47b193259922a55b6c5fe88c66`; fist JSON SHA-256 `65aa714e64a642058237351515951e3840982d0692cc04c079356e1eb0e0ed7b`. All 75 tracked bundle files copied into the new output only and individually hashed. Remote freshness remains unverified.
- Minimal Astro integration is pelvis centering, named shoulder/elbow T-pose and the fourteen asset fist angles. No MJCF/source changes. Fingers are static pose inputs here; future motion constraints have not been configured or tested.
- Same bundled HiPHI `Getting_up-get_up_0004` neutral SMPL-X actor shape for both arms; source arrays equality verified. Static processing does not select or retarget motion frames. The loader used `SMPLX_NEUTRAL.pkl`; both pkl and npz files were hashed. The preparation helper comment incorrectly says npz first; the inspected loader and actual logs establish pkl first. This comment has no execution effect.
- Dedicated worktree/config/output/cache/temp paths. Existing UMR venv shared read-only, with versions recorded. RTX 5070 Laptop GPU, driver 580.178.04. No dependency installation, paid resource, upload or push.

## Records and validation

- Worktree: `/data/workspace/motion_studio/externals/UMR-baseline-v1`; branch `motion-studio/astro-baseline-v1`. Initial integration commit `e045058`; later commits may add evaluation/records only.
- Run: `/data/workspace/motion_studio/outputs/umr-astro-baseline-v1/static-20261024-01`.
- `provenance.json`: input and asset hashes, package versions, model shape, exact config conditions and literature reference. `configs/`: overrides plus full resolved configs. `logs/`: commands, cwd, timestamps, timeout, environment, GPU and full training logs. `evaluation/results.json`: native19 diagnostics and checks. `evaluation/*-binding.npz`: production bindings. `artifact-manifest.json`: final artifact hashes.
- Three preflight/safety tests passed. Both official dataset/slot compatibility checks passed; target geometry equals each saved dataset within 200 nm, and source mesh/faces/shape/samples are exactly equal across arms. Existing report validator passed for both 19-row, 4096-slot results. Evaluation exited zero under a 180-second CPU bound.
- Four legacy-evidence regression tests passed. `outputs/umr-legacy-index-20261024` reconstructs 52 static arms, 24 motion arms and 1,924 segment rows, all **legacy / retrospective / not rerun**, with zero new-baseline arms. Its 447 source hashes and four output hashes verified. Ancillary inventory includes provenance/proposal records; no new run result is normalized as legacy.
- `preservation-before.json` and `preservation-after.json` verify 509 pre-existing report/config/source records and every previously dirty external file unchanged. Original repository HEADs unchanged; root still unborn. This is not a full rehash of every historical binary: no command targeted existing raw outputs.

## Review boundary and remaining work

Review these bindings before the kinematic motion stage and before any controlled ablation. Both intended comparison axes remain: Astro versus G1 within each source, and SMPL-X versus SOMA-X within each robot. Matched SOMA-X motion, actor shape and dataset rig are missing; model assets alone are insufficient. This run does not fill that branch.

No repeated-seed study, exact global-triangle audit, common18/LBS confidence analysis, visual review, motion metrics, floor/collision check or dynamics/controller test was performed. Zero motion joint-limit, collision or force claims are made. Default source learning, robot morphology/centers and diagnostic region boundaries must remain visible when interpreting differences.

Methodology reference: `references/umr-paper-study-v1.md`, v1 (2026-10-24), SHA-256 `f3d540a28ae372b0a4819641899e2ad4f03ed1e4f227ff7b3980cadc7fa459ba`. Its prior fixed-fist findings remain legacy. All previous raw reports, configs, datasets, checkpoints and trajectories stay in place.
