# SOMA-X for UMR

For the official Studio's BONES-SEED example, native source integration, and
the verified local uniform fit, see the
[SOMA/BONES-SEED integration trace](umr-soma-boneseed-integration.md).

Prepared on 2026-10-22; local auto-detection links verified on 2026-10-23.
SOMA static correspondence is available; BONES-SEED motion remains a separate input.

Use the existing UMR environment:

```bash
cd /data/workspace/motion_studio/externals/UMR
source /data/motions/human_models/soma-x/f81a01796f65/env.sh
PYTHONPATH=scripts .venv/bin/python -c 'from soma_source import default_soma_assets_path; print(default_soma_assets_path())'
```

The source command exports:

```bash
export UMR_SOMA_ASSETS_PATH=/data/motions/human_models/soma-x/f81a01796f65/overlays/umr
export UMR_SOMA_SMPLX_ASSETS_PATH=/data/motions/human_models/soma-x/f81a01796f65/assets/SMPLX
```

## Local asset links

Both `externals/UMR` and `externals/UMR-astro-surface-experiment` now contain:

```text
sample_data/bones-seed/soma_assets -> /data/motions/human_models/soma-x/f81a01796f65/overlays/umr
```

This uses UMR's existing auto-detected model-asset location, analogous
to the existing SMPL asset links. No source-loader change or asset copy is needed.
The link points to the compatibility overlay, which retains access to the original
MHR weights, rig, SMPL-X correspondence meshes and license. It does not provide
BONES-SEED motion, fitted shape parameters or the dataset-specific base rig.
The explicit environment variables above continue to take precedence. The links
are local untracked entries: upstream's directory-only ignore rule does not
match a symlink. No upstream tracked files were changed.

To recreate a missing link from the Motion Studio root (do not overwrite an
existing location):

```bash
ln -s /data/motions/human_models/soma-x/f81a01796f65/overlays/umr externals/UMR/sample_data/bones-seed/soma_assets
ln -s /data/motions/human_models/soma-x/f81a01796f65/overlays/umr externals/UMR-astro-surface-experiment/sample_data/bones-seed/soma_assets
```

To verify auto-detection without the environment variables:

```bash
cd /data/workspace/motion_studio/externals/UMR
env -u UMR_SOMA_ASSETS_PATH -u UMR_SOMA_SMPLX_ASSETS_PATH PYTHONPATH=scripts \
  .venv/bin/python -c 'from soma_source import default_soma_assets_path, load_soma_bind_tpose_template; print(default_soma_assets_path()); t=load_soma_bind_tpose_template(); print(t["points"].shape, t["skinning_weights"].shape)'
```

Verified output: `(18056, 3)` points and `(18056, 78)` weights, with 78 finite
bind/T-pose transforms. The same check passes in the isolated experiment checkout.

## Installed assets

- Original official assets: `/data/motions/human_models/soma-x/f81a01796f65/assets`.
- Local compatibility overlay for UMR: `/data/motions/human_models/soma-x/f81a01796f65/overlays/umr`.
- Provenance, file sizes, and checksums: `/data/motions/human_models/soma-x/f81a01796f65/asset-manifest.json`.
- CPU/GPU model validation: `/data/motions/human_models/soma-x/f81a01796f65/validation.json`.
- Environment: `/data/workspace/motion_studio/externals/UMR/.venv`, Python 3.12, `py-soma-x==0.3.4`, `torch==2.7.1+cu128`.

Assets are pinned to NVIDIA Hugging Face revision
[`f81a01796f652260ff930d5318d6c6b845a505ed`](https://huggingface.co/nvidia/SOMA-X/tree/f81a01796f652260ff930d5318d6c6b845a505ed).
All original files were checked against the upstream Git blob hash or LFS SHA-256.
The existing MHR model and mesh correspondences were reused only after their
hashes matched this revision. Updated core files were downloaded from NVIDIA.
The model repository is public and carries an Apache-2.0 license; its `LICENSE`
and model card are included with the original assets.

The installed files cover UMR's configured **mid** LOD with the MHR identity
backend: the neutral NPZ, template rig, procedural transforms, MHR LOD1 model
and meshes. The SMPL-X correspondence meshes are also installed for body-segment
transfer; these are correspondence assets and do not include a separately
licensed SMPL-X identity model. Pose correctives and lower MHR LODs are not
needed by the configured UMR path and were not installed.

## Compatibility overlay

Current SOMA-X releases store the public rig in `SOMA_template_rig.usda` and
ship a slim `SOMA_neutral.npz`. UMR's `load_soma_bind_tpose_template` also reads
rig arrays directly from that NPZ. The overlay adds the public 78-joint rig
arrays reconstructed by the official `SOMALayer` loader to a derived NPZ.
Its other entries point to the original verified files, which remain unchanged.
The overlay has a `LOCAL_MODIFICATIONS.md` describing this derivation.

Validation loads UMR's adapter, checks its bind/T-pose template, runs a finite
neutral MHR forward pass on CPU and the RTX 5070 Laptop GPU, and loads the
compatibility overlay through UMR's `SOMALayer` constructor and forward pass. The mid mesh has
18,056 vertices and the public skeleton has 78 transforms.

The setup and overlay/validation scripts are retained under
`/data/motions/human_models/soma-x/f81a01796f65/tools`. To rebuild the overlay and repeat model validation:

```bash
/data/workspace/motion_studio/externals/UMR/.venv/bin/python \
  /data/motions/human_models/soma-x/f81a01796f65/tools/prepare_umr_overlay_and_verify.py
```

GPU validation must run in a host context with NVIDIA device access. The setup
script reuses an existing verified local model when available and otherwise
downloads the pinned public files. Run the overlay/validation script after
running the asset setup script, because it also writes the UMR environment file.

## BONES-SEED motion data

The SOMA-X model setup is separate from BONES-SEED BVHs and fitted actor shapes.
Those gated files are not downloaded by this setup. Follow the
[UMR BONES-SEED guide](../externals/UMR/sample_data/bones-seed/README.md) after
obtaining access from the [upstream dataset](https://huggingface.co/datasets/bones-studio/seed).
Uniform motion needs `soma_base_fit_mhr_params.npz`; proportional motion needs
an actor-matched `Axxx.npz`. The base rig USD is also part of that dataset layout.
No dataset license acceptance was performed.
