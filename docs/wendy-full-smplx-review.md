# Full Wendy SMPL-X review

Converted 2026-10-22 from
`/data/motions/datasets/fzmotion/raw/bvh/wendy/2026-10-19/wendy_happy_dance_Skeleton1.bvh`.
All 6,924 frames are retained at original frame time 0.00833333 s
(120.000048 Hz): 57.69997692 seconds. No full-motion robot retargeting ran.

Preview: http://127.0.0.1:8767/

Human-only viewer includes play/pause, speed, full timeline, individual frame
stepping, orbit/front/side cameras, and optional original BVH skeleton overlay.
Every source frame has a baked mesh. One-second chunks are fetched on demand;
a bounded six-chunk cache avoids loading the entire ~870 MB animation at once.
Playback pauses progression if a required chunk is loading. It wraps at the
end; this loop boundary is not guaranteed continuous.

Output: `outputs/smplx/wendy_happy_dance_full.npz` (about 1.7 MB).
Poses `[6924,165]`, translations `[6924,3]` in meters, Y-up metadata,
neutral gender, 10 zero shape coefficients. Uses the previously validated
Wendy map and pinned hiphi2smplx revision. Finger/face/eye poses are unfitted.

Checks: finite arrays; all 58 mesh chunks have correct sizes including the
last 84-frame chunk; mean body-joint fitting residual 3.303 cm and maximum
per-frame mean 3.662 cm. Rendered joints match IK joints within 4.06e-7 m.
Minimum mesh Y is -1.935 cm: no ground correction was applied. Residuals are
against the converter's targets, including its adjusted foot targets.
Browser scrubbing was checked at 30 s and the final frame. This is an
inspection checkpoint, not a claim of contact or full-motion fit perfection.

Reproduce from `/data/workspace/motion_studio`:

```bash
# Refuses to overwrite an existing conversion.
externals/UMR/.venv/bin/python scripts/convert_wendy.py --config configs/umr/wendy-full.json
# GPU access outside the sandbox required on this host.
externals/UMR/.venv/bin/python scripts/export_wendy_full_preview.py
python3 -m http.server 8767 --bind 127.0.0.1 --directory outputs/smplx/wendy-full-viewer
```

The exporter reuses the local Three.js vendor assets from the excerpt viewer.
See `docs/wendy-smplx-preview.md` to reconstruct those dependencies.
Diagnostics, report and logs are saved next to the full NPZ. Browser sources
are in `scripts/wendy-full-viewer/`. Licensed weights remain local and are
not included in the served directory. The earlier Astro comparison remains
available separately on port 8766.
