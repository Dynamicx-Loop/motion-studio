# UMR on this machine

Local setup: 2026-10-22. UMR revision: `d1cdaed`.

## Environment

The isolated Python 3.12 environment lives at `externals/UMR/.venv`.
Activate it from the workspace root:

```bash
source /data/workspace/motion_studio/externals/UMR/.venv/bin/activate
cd /data/workspace/motion_studio/externals/UMR
```

This machine has an NVIDIA RTX 5070 Laptop GPU with 8 GB VRAM and driver
580.178.04. GPU devices are hidden inside the Codex sandbox; `nvidia-smi`
works outside it. Run GPU jobs from a normal host terminal or with approved
host access. No driver change is needed.

Use PyTorch 2.7.1 with CUDA 12.8 for this Blackwell GPU, instead of the
upstream README's older torch 2.4.1/cu121 combination. See
[PyTorch's Blackwell support announcement](https://pytorch.org/blog/pytorch-2-7/).
UMR's other requirements come from `externals/UMR/requirements-umr.txt`.

To recreate the environment using the installed `uv` tool:

```bash
cd /data/workspace/motion_studio/externals/UMR
UV_CACHE_DIR=/tmp/umr-uv-cache uv venv --python /usr/bin/python3 .venv
UV_CACHE_DIR=/tmp/umr-uv-cache uv pip install --python .venv/bin/python \
  --index-url https://download.pytorch.org/whl/cu128 torch==2.7.1
UV_CACHE_DIR=/tmp/umr-uv-cache uv pip install --python .venv/bin/python \
  -r requirements-umr.txt -c ../../configs/umr/constraints.txt
```

Run these installation steps sequentially. `constraints.txt` preserves the
GPU-compatible PyTorch build.

## Models and robot

The neutral, male, and female SMPL-X NPZ files are symlinked into UMR's
`smpl/` directory from:

```text
/data/motions/human_models/smplx/1.1/models_smplx_v1_1/models/smplx
```

No weights were copied or modified. SMPL files are not needed for the bundled
SMPL-X HiPHI example.

`configs/umr/astro_p2_29dof.json` points to the canonical Astro MJCF in
`/data/workspace/notAnyrobot/menagerie_x/robots/astro_p2_29dof/` and uses
`body:pelvis` as its point-cloud center. CUDA is selected, with SMPL-X batch
size capped at 128. The HiPHI G1 shared-correspondence settings are disabled
and cleared so Astro builds its own sequence-specific correspondence.

## Astro T-pose

The user supplied the Studio T-pose on 2026-10-22. All 29 joint values are
saved in `robot.tpose_qpos`, with the requested exact-angle normalization:
left shoulder roll +π/2, right shoulder roll −π/2, and both elbows +π/2.
All other joint values remain zero. The values passed MJCF joint-limit
validation and forward kinematics.

For current Astro runs, use the built-in Studio robot through the
[standard UMR experiment](../experiments/umr-standard/README.md).

## Setup verification

Passed on 2026-10-22:

- Dependency compatibility check: 80 packages; exact installed versions are
  recorded in `configs/umr/requirements-installed.txt`.
- PyTorch CUDA forward/backward computation on GPU capability 12.0.
- Astro MJCF load: `nq=36`, `nv=35`, 40 bodies, 92 geoms.
- Neutral, male, and female SMPL-X GPU forward passes: 10,475 vertices each,
  all finite.
- UMR pipeline imports and Embree mesh ray intersection.
- HiPHI preparation stage using the Astro config. Generated preparation
  artifacts are in `outputs/umr/setup-check/`; this stage does not train or
  retarget. The subsequently supplied T-pose was validated separately.

The bundled HiPHI example contains 5,468 frames at approximately 90 Hz.
The screenshot shows a 450-frame, 30 Hz web-demo clip, so local full-clip
length and processing time will differ.
