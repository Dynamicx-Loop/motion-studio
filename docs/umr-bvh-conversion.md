# BVH to SMPL-X for UMR

Investigated on 2026-10-22. No conversion, fitting, correspondence training, or
robot retargeting was run. The source parsers, joint-name validation, and local
neutral model loading were checked.

## Recommendation for the local Wendy motions

Use [hiphi2smplx](https://github.com/noitom-robotics/hiphi2smplx) with a **new
Wendy skeleton map**, then feed its NPZ to UMR's ordinary SMPL-X adapter.
This is a small adaptation of the official HiPHI converter, rather than a
claim that Wendy is already supported upstream. Start with a short clip and
fixed zero betas; fit body shape only after inspecting the motion.

The inspected files are:

- `/data/motions/datasets/fzmotion/raw/bvh/wendy/2026-10-19/Wendy-t-pose_Skeleton1.bvh`: 331 frames.
- `/data/motions/datasets/fzmotion/raw/bvh/wendy/2026-10-19/wendy_happy_dance_Skeleton1.bvh`: 6,924 frames,
  approximately 57.7 seconds.

Both have 57 named joints, root translation plus Z/Y/X Euler rotations, and
`Frame Time: 0.00833333` (approximately 120 Hz). Their rest offsets place the
head above the pelvis on Y, arms along X, and toes toward Z. Thigh/shin
lengths near 44/41 are consistent with centimeters; applying the converter's
0.01 scale gives a plausible approximately 1.60 m skeleton. The units are an
inference from the data, since BVH does not declare them.

Stock `hiphi` mapping rejects both files because it requires `Spine`,
`Spine4`, `LeftToeBase`, and `RightToeBase`. The following map passed the
upstream parser and required-joint validation on **both local files**:

```python
from hiphi2smplx.skeleton import HIPHI_MAP, SOURCE_SKELETON_MAPS

SOURCE_SKELETON_MAPS["wendy"] = {
    **HIPHI_MAP,
    "spine": "Spine1",
    "spine2": "Spine2",
    "chest": "Chest",
    "left_toe": "LeftToe",
    "right_toe": "RightToe",
}
```

This verifies names and parsing, not the quality of fitted rotations or the
body surface. Inspect the T-pose and a moving excerpt for shoulder/foot
orientation, scale, root trajectory, and ground height before processing the
whole collection. The upstream converter fits 22 body joints; facial and
finger poses are zero unless an external MANO fitter is supplied. Wendy's
finger channels therefore are not preserved by this workflow.

Sources: upstream [skeleton map and validation](https://github.com/noitom-robotics/hiphi2smplx/blob/65e51315ebbc82b2f0ff8e35a94565beb1b345e1/src/hiphi2smplx/skeleton.py),
[BVH parser](https://github.com/noitom-robotics/hiphi2smplx/blob/65e51315ebbc82b2f0ff8e35a94565beb1b345e1/src/hiphi2smplx/bvh.py),
and [body fitting pipeline](https://github.com/noitom-robotics/hiphi2smplx/blob/65e51315ebbc82b2f0ff8e35a94565beb1b345e1/src/hiphi2smplx/pipeline.py).

## Proposed local conversion commands

These commands are instructions for a subsequent conversion run; they have
not been executed. Preserve the existing CUDA PyTorch build by using the
workspace constraint when adding the converter to UMR's environment:

```bash
cd /data/workspace/motion_studio
git clone https://github.com/noitom-robotics/hiphi2smplx.git externals/hiphi2smplx
git -C externals/hiphi2smplx checkout 65e51315ebbc82b2f0ff8e35a94565beb1b345e1
UV_CACHE_DIR=/tmp/umr-uv-cache uv pip install \
  --python externals/UMR/.venv/bin/python \
  -c configs/umr/constraints.txt -e externals/hiphi2smplx
```

The package requires Python >=3.10 plus NumPy, SciPy, Mink, MuJoCo,
qpsolvers, DAQP, PyTorch, h5py, smplx, and tqdm. At inspection time UMR already
had most of these; Mink, qpsolvers, DAQP, and h5py were missing. DAQP is the
default IK QP backend. See [the dependency declaration](https://github.com/noitom-robotics/hiphi2smplx/blob/65e51315ebbc82b2f0ff8e35a94565beb1b345e1/pyproject.toml).

For Wendy, save the following as a small local wrapper, for example
`/tmp/convert_wendy.py`. It registers the map before building the CLI parser
and adds the axis metadata needed by UMR's generic NPZ loader:

```python
import sys
from pathlib import Path

import numpy as np
from hiphi2smplx.cli import main
from hiphi2smplx.skeleton import HIPHI_MAP, SOURCE_SKELETON_MAPS

SOURCE_SKELETON_MAPS["wendy"] = {
    **HIPHI_MAP,
    "spine": "Spine1", "spine2": "Spine2", "chest": "Chest",
    "left_toe": "LeftToe", "right_toe": "RightToe",
}

if __name__ == "__main__":
    main()
    # The --output path in the command below is a separate argument.
    output = Path(sys.argv[sys.argv.index("--output") + 1])
    with np.load(output, allow_pickle=False) as packed:
        fields = {name: packed[name] for name in packed.files}
    fields["output_up"] = np.asarray("y")
    np.savez_compressed(output, **fields)
```

Create an initial mean-body shape, then convert just one second of dance:

```bash
cd /data/workspace/motion_studio
externals/UMR/.venv/bin/python - <<'PY'
import numpy as np
np.save('/tmp/wendy_zero_betas.npy', np.zeros(10, dtype=np.float32))
PY
externals/UMR/.venv/bin/python /tmp/convert_wendy.py \
  --input-bvh /data/motions/datasets/fzmotion/raw/bvh/wendy/2026-10-19/wendy_happy_dance_Skeleton1.bvh \
  --output /data/workspace/motion_studio/outputs/smplx/wendy_happy_dance_preview.npz \
  --model-path /data/motions/human_models/smplx/1.1/models_smplx_v1_1/models/smplx/SMPLX_NEUTRAL.npz \
  --skeleton-map wendy --betas /tmp/wendy_zero_betas.npy \
  --max-frames 120 --progress
```

The neutral NPZ model already exists locally and its 22 body joints loaded
successfully in the static check. The converter requires **exactly one** of
`--betas` or `--fit-betas`. Fixed zero betas avoid downloading pose-prior
assets but are only an initial approximation of Wendy's proportions.

For improved proportions, run the same wrapper on the T-pose with
`--fit-betas --beta-fit-data /path/to/beta_fit --beta-device cuda:0` in place
of `--betas`. The asset directory must contain licensed
`neutral_smpl_mean_params.h5` and `gmm_08.pkl`; these are separate from the
SMPL-X model. The fitter estimates betas from the first frame. Reuse the
resulting NPZ's `betas` for every Wendy clip by passing it to `--betas`;
remove `--max-frames` for a complete conversion. The optional beta fitter
contains HiPHI-specific foot assumptions, so Wendy shape results still need
inspection. See [CLI options](https://github.com/noitom-robotics/hiphi2smplx/blob/65e51315ebbc82b2f0ff8e35a94565beb1b345e1/src/hiphi2smplx/cli.py),
[beta fitting implementation](https://github.com/noitom-robotics/hiphi2smplx/blob/65e51315ebbc82b2f0ff8e35a94565beb1b345e1/src/hiphi2smplx/beta_fitting.py),
and [official asset instructions](https://github.com/noitom-robotics/hiphi2smplx#download-model-files).

## UMR handoff and axes

The converter saves `poses` `[T,165]` (SMPL-X axis-angle radians), `trans`
`[T,3]` in meters, `betas` `[10]`, `gender="neutral"`, and the original
`mocap_framerate`. Wendy should therefore remain approximately 120 Hz.

For Wendy, use `humanoid_retarget_pipeline.py` and set `motion.data` to the
converted NPZ or its directory and `motion.seq_key` to the filename stem in
a separate configuration derived from the Astro configuration. Do not use
the HiPHI launcher for an unwrapped Wendy NPZ.

The distinction matters:

| Input route | Required layout | Default when axis metadata is missing |
|---|---|---|
| Ordinary SMPL-X NPZ | One NPZ per clip; no dataset metadata | Z-up |
| HiPHI directory wrapper | `motion_actor_smplx.npz`, `metadata.json` with `dataset="hiphi"`, and optional object tracks/meshes | Y-up |

The HiPHI converter preserves native Y-up coordinates and omits `output_up`.
Its NPZ works in the genuine HiPHI directory wrapper because that loader
supplies Y-up. For the ordinary NPZ route, explicitly adding
`output_up="y"` makes UMR apply its Y-to-Z basis conversion. Merely naming a
folder `hiphi` or inventing HiPHI metadata is unnecessary for Wendy.

Local sources: `externals/UMR/sample_data/lafan1_smplx/README.md`,
`scripts/smpl_surface_retarget_common.py` (`load_smplx_npz_motion`,
`source_points_to_retarget_frame`), and
`scripts/humanoid_retarget_pipeline_hsi_hoi.py` (`load_source_motion`).
The upstream [HiPHI directory guide](https://github.com/hanyang9/UMR/blob/main/sample_data/hiphi/README.md)
describes object metadata. No handoff command was run during this research.

## The LAFAN1 alternative

[lafan_to_smplx](https://github.com/jaraujo98/lafan_to_smplx) is suitable for
**actual LAFAN1** BVHs. It depends on GMR and uses predetermined LAFAN
joint-axis corrections and fitted shape coefficients. Its real source-code
option is `--output_file`; the README's `--output` happens to work as an
argparse prefix abbreviation in the inspected revision. Prefer the full name:

```bash
python lafan_to_smplx.py \
  --bvh_file /path/to/LAFAN1/dance1_subject2.bvh \
  --smplx_model_path /data/motions/human_models/smplx/1.1/models_smplx_v1_1/models \
  --model_type smplx --output_file /path/to/dance1_subject2.npz
```

The model-path argument is the parent of `smplx/`, unlike hiphi2smplx's
direct model filename. The script emits `[T,55,3]` poses, translations, betas,
neutral gender, and a **hardcoded 30 Hz** frame rate. Its GMR loader supplies
LAFAN joint positions/orientations. Wendy lacks its required `Spine` joint;
simple renaming would also leave axis corrections, body proportions, and
timing incorrect. Do not run this unchanged on Wendy. Source inspected:
[lafan_to_smplx.py at d465aa7](https://github.com/jaraujo98/lafan_to_smplx/blob/d465aa7202ddc94f2cd557b682854437573e0dca/lafan_to_smplx.py).

## Direct BVH alternatives in UMR

- **NR FBX/BVH** avoids SMPL-X fitting when a compatible skinned FBX exists.
  Put it at a character root and the BVHs under the exact directory
  `motion_actor_retarget_205_with_ids/`. The FBX and BVH must share compatible
  skin bone names/hierarchy; the adapter assumes centimeters and Y-up and
  needs Node.js >=18. A rest-pose BVH alone provides no skin surface. No FBX
  was found directly in Wendy's folder. See [NR adapter guide](https://github.com/hanyang9/UMR/blob/main/sample_data/nr/README.md).
- **SOMA/BONES-SEED** accepts BVH attached to the expected SOMA skeleton and
  body assets, with actor shape data for BONES-SEED. It is not a generic
  importer for arbitrary BVH skeletons: the skin template requires its
  matching joint names. See [BONES-SEED guide](https://github.com/hanyang9/UMR/blob/main/sample_data/bones-seed/README.md)
  and local `scripts/soma_source.py` (`_bvh_to_usd_joint_indices`).

Context7 was consulted first. It had no matching hiphi2smplx or
lafan_to_smplx documentation, so their official GitHub source was used.
Context7's `/vchoutas/smplx` documentation confirmed the model-file versus
model-directory conventions. All upstream code links above are pinned to
the inspected revisions where practical.
