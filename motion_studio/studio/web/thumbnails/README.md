# Robot card previews

These small PNGs are actual projections of locally compiled pinned UMR robot
geometry in the native named T-pose, produced on 2026-10-30 for the asset library.
No AI/generic placeholder robot is used. Source checkout:
`externals/UMR`, commit `d1cdaedaf67a827198da71c5fa831f48b2e51f91`.
Preset configs are `robot_configs/humanoid_retarget_*_example.json` for
`unitree_g1`, `booster_k1`, `hightorque_pipluspro`, `engineai_t800`.

They show an orthographic front projection (native +X toward camera), original
compiled RGBA with triangle-normal shading, and preserve actual joint geometry.
Texture images are not reproduced. These are display thumbnails, not simulation,
contact or dynamics evidence. Original assets and their separate terms remain
with UMR; the catalog adapter verifies original pinned bytes before use.

Regenerate from the workspace root with
`python3 -B scripts/build_studio_thumbnails.py` (independent MuJoCo interpreter,
local pinned source, Pillow and NumPy required; no network).
