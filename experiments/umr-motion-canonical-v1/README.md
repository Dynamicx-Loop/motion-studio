# Experiment: canonical Astro raw/candidate offline HiPHI motion

> **Status: legacy** — marked 2026-11-02. Retained as historical evidence.
> New experiments will establish the standard experiment contract; this record
> does not define that contract. “Current” and similar wording below refer to
> the original cohort or documentation snapshot. See the [experiment index](../README.md).

Date / author: 2026-10-23 / Codex.

## Objective

Run preliminary motion with one immutable latest Astro model and matched G1
controls, comparing raw learned correspondence with the k32 wrist candidate.
All eight solves are fresh. Offline retargeting is authorized; no physical robot
execution, dynamic rollout or new collision-primitive experiment is performed.

## Provenance and input contract

Canonical Astro: `d2070956558ffbf9226dcf74017d40740724d8d8`, exact XML SHA-256
`c688a4177a1ff5ba07764f9e310bb62c33d24a47b193259922a55b6c5fe88c66`.
Every Astro config references the same XML from
[the static asset manifest](../astro-canonical-static-v1/canonical-asset.json).
G1 is separately frozen as a control. Both already contain a free root, so
`xml_policy.add_freejoint_root=false` preserves exact model bytes without writing
generated wrappers into live upstream assets. Projection/binding is rebuilt by
every solve; no historical geom/body numeric IDs are reused.

UMR baseline and experimental checkout revision
`d1cdaedaf67a827198da71c5fa831f48b2e51f91` and the preserved experimental patch
are recorded in the canonical static experiment. Source/config/runtime code hashes
and full commands are in [provenance.json](provenance.json),
[runs.json](runs.json) and each arm's retained config. No dependency installation.
Runtime:Python3.12,Torch2.7.1+cu128,MuJoCo3.3.7,RTX5070Laptop8GB.
GPU jobs run serially with no competing compute job; wall times include startup,
source evaluation and solve and are not a controlled speed benchmark.

Motion is the unchanged HiPHI
`externals/UMR/sample_data/hiphi/data/Getting_up/get_up/Getting_up-get_up_0004/motion_actor_smplx.npz`.
Use its neutral SMPL-X identity/shape and source frames0:5468:3, yielding1823
frames at about30Hz (full excerpt about60.75s). Input poses are axis-angle,
translations metres,Y-up. Solver conversion is(x,y,z)→(x,-z,y),Z-up. Output free
root quaternion is wxyz,hinges radians,ordered by recorded native joint names
and qpos addresses. No implicit application/body+hand array-order assumption.
Source finger poses are zeroed as declared by the baseline; no source ground
alignment is applied. No motion is substituted, shape swapped or frame relabeled.

Each arm copies the exact raw/candidate static dataset and slot file. Reference
pose is open hands; the asset's fist keyframe is not selected. The candidate is
a label-independent monotone lateral remap, not retraining or a finger identity
map. All source/centering choices and solver settings match the earlier v2
protocol: one iteration/frame,15 pose-init iterations,seed0,batch32,max_dq0.15,
global step0.4,unchanged contact-map/normal/segment weights and LQR filtering.
Full resolved settings live in the configs; segment point/normal objectives,
including head versus torso, remain separate. Configured robot self-penetration
cost is0 and its hard constraint isfalse. Latest collision geoms are retained but
not used to claim whole-body collision safety.

The valid SOMA-X model/weights at `/data/motions/human_models/soma-x/f81a01796f65/overlays/umr` are linked into
both UMR checkouts at the adapter's auto-detected model path. This enables static
SOMA/model loading without environment variables. It does not supply a
BONES-SEED motion,actor fit or dataset rig; [BONES-SEED.md](BONES-SEED.md) records
required files. Static public-neutral SOMA bindings are not automatically
compatible with a future dataset actor shape. SOMA motion remains unrun.

## Reproduction

The commands below document this historical cohort and may write to its fixed
paths. Do not run them against retained evidence; adapt every destination to a
fresh cohort before reuse.

From `/data/workspace/motion_studio`, after canonical raw/candidate preparation:

```sh
externals/UMR/.venv/bin/python experiments/umr-motion-canonical-v1/prepare.py
externals/UMR/.venv/bin/python experiments/umr-motion-canonical-v1/run.py
externals/UMR/.venv/bin/python experiments/umr-motion-canonical-v1/export.py
externals/UMR/.venv/bin/python experiments/umr-motion-canonical-v1/source.py
externals/UMR/.venv/bin/python experiments/umr-motion-canonical-v1/tracking.py
cp experiments/umr-motion-canonical-v1/viewer.js outputs/umr-motion-canonical-v1/viewer/app.js
cp experiments/umr-motion-canonical-v1/viewer.html outputs/umr-motion-canonical-v1/viewer/index.html
externals/UMR/.venv/bin/python experiments/umr-motion-canonical-v1/provenance.py
```

Use new experiment/output directories for a fresh repeat: preparation refuses
overwrite, and UMR otherwise reuses saved trajectories. Source baking uses the
GPU only after motion solves finish. Numerical exports and source vertices are
local; original model,asset,motion licensing and dataset terms remain separate.
No redistribution rights are inferred from this local report.

## Measured results

| Arm | Worst visual penetration mm | Limit violations | Speed p95 rad/s | Acceleration p95 rad/s² | Mean pre-filter cost | Wall s |
|---|---:|---:|---:|---:|---:|---:|
| smplx_astro_bbox50_candidate | 56.71 | 0 | 1.841 | 21.00 | 0.090696 | 44.0 |
| smplx_astro_bbox50_raw | 37.05 | 0 | 1.889 | 21.17 | 0.091196 | 40.1 |
| smplx_astro_spine1_candidate | 30.76 | 0 | 1.871 | 20.95 | 0.132271 | 41.0 |
| smplx_astro_spine1_raw | 28.14 | 0 | 1.803 | 20.96 | 0.129721 | 40.1 |
| smplx_g1_bbox50_candidate | 17.96 | 0 | 2.220 | 23.80 | 0.102600 | 40.4 |
| smplx_g1_bbox50_raw | 18.02 | 0 | 2.241 | 24.24 | 0.102672 | 42.1 |
| smplx_g1_spine1_candidate | 13.01 | 0 | 2.066 | 22.67 | 0.059607 | 41.9 |
| smplx_g1_spine1_raw | 14.02 | 0 | 2.074 | 23.38 | 0.057813 | 42.1 |

All8 outputs are finite and have zero configured joint-limit violations at1e-6rad
tolerance. Some joints reach a bound. Fresh raw metrics reproduce prior v2
measurements, as expected from unchanged visual/solver inputs. The candidate's
static hand-mesh gains do not imply improved full-motion clearance: Astro bbox50
penetration worsens37.05→56.71mm and spine1 worsens28.14→30.76mm. G1 changes are
smaller(18.02→17.96mm bbox50;14.02→13.01mm spine1). No universal better/worse
ranking follows from pre-filter cost or these heterogeneous metrics. Raw remains
the default; candidate playback is explicitly selectable.

## Evaluation and limitations

Joint-limit margins,native hinge velocity/acceleration,quaternion norm,root paths,
visual-mesh minimum height and inferred-stance summaries use exported filtered
qpos. Visual height is computed using mesh convex-hull extrema, equivalent to the
minimum over mesh vertices for each transformed rigid geom. No vertical alignment
is applied in playback. Slot floor constraints do not ensure complete mesh
clearance after filtering. Inferred stance is ankle-body height within30mm of
that foot's clip minimum; its horizontal speed includes actual repositioning and
must not be reported as measured contact slip. Root-relative wrist/ankle landmark
errors compare robot body origins with scaled human joints; morphology and
frame-center differences contribute, so these are proxies, not surface residuals.
Full results retain means,p95,max and the exact definitions.

Solver cost is aggregate pre-LQR cost, not an exported-pose objective residual.
Per-segment post-filter residuals and reliable self-collision are not instrumented.
One iteration/frame does not establish convergence. No balance,support force,
torque,actuator velocity,contact,grasp,dynamic feasibility or hardware safety claim
follows. Only one get-up clip and one training seed are tested.

## Playback and verification

The report bundles synchronized source/G1/Astro playback under
`http://127.0.0.1:8770/inspectors/canonical-motion/index.html`.
Controls retain both matched centers and selected Astro bbox50/G1 spine1. Binding
selector defaults to raw; the k32 candidate is a separate explicit option. Human
and robots retain native sizes,initial-root horizontal centering and fixed display
offsets. Source fingers are zeroed consistently with solving. No per-frame fitted
alignment or vertical offset hides penetration.

The provenance verifier checks all8 fresh return codes,source hashes,frame IDs,
qpos dimensions,finite values,configured limits,native joint order,snapshot XML
identity,static dataset geometry within200nm,and all viewer binary sizes. Browser
playback and bilingual report checks are recorded in the report validation.
