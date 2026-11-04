# SOMA-X for UMR

For the official Studio's BONES-SEED example, native source integration, and
the verified local uniform fit, see the
[SOMA/BONES-SEED integration trace](umr-soma-boneseed-integration.md).

## Workspace setup

Use Motion Studio's [SOMA-X model assets](../assets/human_models/soma-x/README.md)
and [BONES-SEED calibration](../assets/calibrations/bones-seed/README.md).
From the Motion Studio root, restore and verify the existing local links:

```bash
python3 scripts/sample_data.py populate
python3 scripts/sample_data.py check
```

The [sample-data UMR runner](../outputs/artifact-archives/experiment-reset-20261104/experiments/sample-data-umr-g1-20261102/README.md)
uses the official UMR environment and builds the expected BONES-SEED layout in
the fresh run directory. It links shared fit and overlay assets from
`assets/calibrations/bones-seed/` and `assets/human_models/soma-x/overlays/umr/`.
The historical auto-detection links inside UMR checkouts are retired.

## Installed asset provenance

The October 2026 setup and validation used Python 3.12, `py-soma-x==0.3.4`,
and `torch==2.7.1+cu128` in the official UMR environment. The backing store
retains the original asset manifest and validation report.

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
Use the [local samples](../data/sample_data/bones-seed/README.md) for the verified
uniform workflow. For further dataset inputs, follow the
[UMR BONES-SEED guide](../externals/UMR/sample_data/bones-seed/README.md) after
obtaining access from the [upstream dataset](https://huggingface.co/datasets/bones-studio/seed).
Uniform motion needs `soma_base_fit_mhr_params.npz`; proportional motion needs
an actor-matched `Axxx.npz`. The base rig USD is also part of that dataset layout.
No dataset license acceptance was performed.
