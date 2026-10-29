# Wendy SMPL-X conversion preview

Completed 2026-10-22. Astro configuration was not changed and no robot
retargeting ran. This is an inspection checkpoint, not a full-dataset conversion.

## Inspect

Open http://127.0.0.1:8766/ while the local server is running. The viewer has
real-time playback, 0.5× and 0.25× speed, pause, frame scrubbing, orbit, front/side
views, mesh/skeleton visibility, and an overlay comparison. Blue is the converted
SMPL-X mesh; orange is the original 57-joint Wendy BVH. Side-by-side mode adds
±1 m display offsets on X only; overlay removes them. Neither modifies the NPZ.
The grid is Y=0. All browser assets are local; nothing is published.

Restart the server from `/data/workspace/motion_studio`:

```bash
python3 -m http.server 8766 --bind 127.0.0.1 --directory outputs/smplx/wendy-viewer
```

## Outputs and findings

- `outputs/smplx/wendy_happy_dance_preview.npz`: source frames 0–119, the
  requested initial 120-frame test. This first second is nearly static.
- `outputs/smplx/wendy_happy_dance_6s_9s.npz`: source frames 720–1079 (zero-based),
  360 frames / 2.9999988 seconds, used by the browser preview.
- Both preserve frame time 0.00833333 s (120.000048 Hz), use meters and
  `output_up='y'`, and contain poses `[T,165]`, trans `[T,3]`, zero betas `[10]`,
  and neutral gender. The source is unchanged. No resampling or ground correction.
- Numeric arrays are finite. Dance mean joint-fit residual is 0.0348665 m;
  maximum per-frame mean is 0.0365325 m. These are distances to the upstream
  fitting targets, including its adjusted foot targets, not surface errors.
- Mesh minimum Y over the dance is -0.0017966 m. First-frame mesh vertical
  extent is 1.69476 m. Mesh joints agree with IK joints within 3.7e-7 m.
- Visually checked side-by-side pose at 7.5 s and front overlay at 8.75 s:
  upright body, plausible scale and arm/leg correspondence. Mean-shape limb
  and torso proportions do not exactly match the source. This is not a
  claim of production-quality fitting or contact/foot-slip validation.
- Neutral mean shape (10 zero betas) was used, with no shape fitting/prior.
  Fingers, face and eyes are not fitted. Preview uses `flat_hand_mean=True`
  and `use_pca=False` so zero hand rotations display a flat rest hand.
- `.diagnostics.npz` files retain source joints, names/parents, fitted joints,
  losses and residuals. `.report.json` files contain numeric checks.
- `outputs/smplx/wendy-viewer/preview.png` and `overlay.png` are inspected captures.
- Licensed model weights remain at their original local path. The viewer
  contains derived meshes, never the model weights; keep these assets local.

## Reproduce

The converter is checked out at
`65e51315ebbc82b2f0ff8e35a94565beb1b345e1` in `externals/hiphi2smplx`.
Current Context7 documentation confirmed the custom named-map/fixed-betas
workflow; pinned local source was inspected for actual behavior.
The wrapper registers HIPHI_MAP with spine=Spine1, spine2=Spine2, chest=Chest,
left_toe=LeftToe, right_toe=RightToe. Its native parser scale is 0.01;
centimeter input units are inferred, not declared by the BVH.

From `/data/workspace/motion_studio`:

```bash
# Only needed to reconstruct the environment. Installs must run sequentially.
UV_CACHE_DIR=/tmp/umr-uv-cache uv pip install \
  --python externals/UMR/.venv/bin/python \
  -c configs/umr/hiphi-constraints.txt -e externals/hiphi2smplx

# Refuses to overwrite existing outputs; use new output paths in configs to rerun.
externals/UMR/.venv/bin/python scripts/convert_wendy.py
externals/UMR/.venv/bin/python scripts/convert_wendy.py \
  --config configs/umr/wendy-dance-preview.json

# Download viewer library if reconstructing a clean output directory.
mkdir -p outputs/smplx/wendy-viewer/vendor
curl -fL https://cdn.jsdelivr.net/npm/three@0.165.0/build/three.module.js \
  -o outputs/smplx/wendy-viewer/vendor/three.module.js
curl -fL https://cdn.jsdelivr.net/npm/three@0.165.0/examples/jsm/controls/OrbitControls.js \
  -o outputs/smplx/wendy-viewer/vendor/OrbitControls.js

# GPU access requires execution outside the Codex sandbox on this machine.
externals/UMR/.venv/bin/python scripts/export_wendy_preview.py
python3 -m http.server 8766 --bind 127.0.0.1 --directory outputs/smplx/wendy-viewer
```

Converter runs on CPU; mesh baking uses CUDA batches of 30. Full environment
snapshot: `outputs/smplx/wendy-environment.txt`. Verified torch 2.7.1+cu128,
MuJoCo 3.3.7, Mink 1.1.0; `uv pip check` passes. The initial unpinned Mink 1.3.0
install upgraded MuJoCo, which was immediately restored to 3.3.7 with compatible
Mink 1.1.0. The new constraints prevent recurrence.

The user subsequently approved the preview and requested Astro retargeting.
See `docs/wendy-astro-preview.md` for the completed run and updated combined viewer.
