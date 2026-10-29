# Canonical preparation and CPU compile smoke

Measured on 2026-10-29 from ticket branch `codex/layout-assets-12`, initially based
on integration `a9ef925`. This is a fresh preparation observation, separate from
historical G1/static-pair cohorts. No train, dataset, learned slots, checkpoint,
retarget, simulation stepping, controller or quality evaluation was executed.

| Explicit selection | MuJoCo / scalar joints | nq / nv | Result |
| --- | --- | --- | --- |
| `g1_29dof / mjcf / tpose` | 3.3.7 / 29 | 36 / 35 | Prepared and CPU compiled |
| `astro_p2_29dof / mjcf / tpose` | 3.3.7 / 29 | 36 / 35 | Prepared and CPU compiled |
| `astro_p2_43dof_dex3_1 / mjcf / tpose_fist` | 3.3.7 / 43 | 50 / 49 | Prepared and CPU compiled |

The independent compile loaded each derived run-local XML, assigned scalar joints
by native model name and forwarded kinematics without stepping. Free-root XYZ and
wxyz values matched the declared pose within `1e-12`; scalar values matched within
`1e-12`; compiled scalar name order matched the receipt. This does not certify
representation parity, numerical pipeline compatibility or dynamic feasibility.
Every receipt remains `state='prepared-only'`, `execution_readiness=false`.

Sources: menagerie_x `d2070956558ffbf9226dcf74017d40740724d8d8`, official UMR
`d1cdaedaf67a827198da71c5fa831f48b2e51f91`. The clip was the bundled
`sample_data/hiphi/data/Getting_up/get_up/Getting_up-get_up_0004/motion_actor_smplx.npz`
with 5,468 frames and declared native FPS `90.00090026855469`, without trimming or
resampling. Actor-shape evidence was extracted from its `betas` and `gender` fields
with the existing UMR NumPy runtime. The explicit model was
`/data/motions/human_models/smplx/1.1/models_smplx_v1_1/models/smplx/SMPLX_NEUTRAL.pkl`.
Model/input bytes and shape evidence remain local; this record redistributes none.

Fresh run directories and detailed source/config/environment hashes are retained
under the durable canonical directory:
`/data/workspace/motion_studio/outputs/implementation/layout-and-robot-assets/ticket12-20261029/`.
Each robot child has original source/provenance closure copies, a separately
derived pose XML, source clip/shape/model copies, pinned backend source/config
copies, `config.json`, `inputs.json` and `preparation.json`. No outputs are aliased
through a temporary directory. The directory also retains `source/shape.json`,
`smoke-command.py`, `smoke.json` and `preservation.json`.

The exact executed smoke script is retained there with SHA-256
`ff17369b5d98ecaa2f6092c09584a86b7b288c385730c4a9f678e4308dee91ed`.
It ran as:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/tmp/motion-studio-layout-ticket12 \
  python3 /tmp/ticket12-real-smoke.py
```

The archived command has fixed historical paths and existing destinations; a
repeat must choose a separate fresh destination. It records the actual operation
and independent compile used, rather than claiming an execution pipeline.

[smoke.json](smoke.json) retains each preparation receipt hash and compiled
observations. [preservation.json](preservation.json) records the follow-up
independent streaming SHA-256 verification: all original selected robot source
files, copied selected files, original clip/shape/model files, original pinned
backend code/config and all prepared files matched their receipts after compile.
The selected source/provenance counts were 40, 40 and 67; complete prepared file
counts were 112, 112 and 139. Both source Git statuses were unchanged. Preservation
covers these selected dependencies, not an unchanged whole-workspace inventory.

Pure validation used `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check.py`; the new
public preparation/cache suite covers relocation, byte/settings mutation, exact
claims, malformed evidence, source-link/destination protection and failed receipts.
Matching cache fingerprints prove metadata compatibility only. Existing official
G1 baseline/help/definition-isolation tests also pass; no historical baseline was
advanced or canonical source asset edited.
