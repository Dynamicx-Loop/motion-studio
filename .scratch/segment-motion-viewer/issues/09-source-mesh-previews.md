# 09 — Animated source meshes and sample motion thumbnails

Status: resolved
Category: enhancement
Spec: ../spec.md
Blocked by: none

## Context

Ticket 08 reconstructs SMPL-X vertices on CPU but discards them into a joint-only
preview. The user requested animated full human surfaces and sample thumbnails
before retargeting, with browsable cards that do not select a run automatically.

## Scope and acceptance criteria

- Render actual native human surfaces, exact saved frames/FPS and original source
  translation in Z-up metres; disclose neutral hands and omitted facial channels.
- Retain all triangle topology and source frames in a separate versioned cache;
  use bounded 64-frame root-relative int16 vertex chunks (0.1 mm precision),
  without a giant all-frame vertex JSON or a GPU/robot solve.
- Sample cards render actual mesh thumbnail frames and support browsing/preview
  without run selection; intentional Use remains explicit.
- Verify manifest, topology and chunk registration independently by SHA-256 and
  export-root confinement. Concurrent builds coalesce; generated viewing works
  offline without native scientific packages or licensed model weights.
- Keep the existing skeleton cache, completed runs, pinned externals, old viewers
  and prior ticket 08 work intact. Record numeric and browser checks separately.

## Validation

Pure service/HTTP cache and representation cases; native CPU numerical reference
including both sides of a 64-frame boundary, source/FPS/axis preservation; browser
sample-card thumbnails, source playback and explicit-use behavior.

## Comments

2026-10-30: Claimed for the user-requested follow-up. Backend and frontend are
owned Motion Studio additions; no external changes or model redistribution.

## Backend implementation and validation

- Added version-one manifest, one exact native Uint32 triangle topology and
  64-frame little-endian int16 vertex chunks, reusing the owned native viewer's
  root-relative 0.1-mm encoder. Recorded original roots, frames, FPS, bounds,
  input axis, source/model hashes and pinned native revision. Vertex data never
  accumulates across the whole clip in Python or JSON.
- Kept legacy skeleton endpoints/registry separate. Registered each new public
  file independently; refused unknown resources, traversal, cache symlinks,
  changed bytes, malformed topology/timelines and unexpected output sizes.
  Same-state concurrent Studio callers share one CPU build. Existing generated
  meshes reopen without original source files, weights or reconstruction.
- Added surface POST/manifest/chunk HTTP routes. Sample imports persist a
  catalog-to-managed-asset identity map with frame/FPS metadata, without selecting
  a run or creating a revision.
- `python3 -B -m unittest discover -s tests -p test_studio_source_mesh_preview.py -v`:
  **8 tests passed**. Analytic frames 0/63/64/65 preserve translation within
  `5.1e-5 m`; tests cover offline reload, six simultaneous requests, legacy cache
  isolation, actual HTTP binaries, tampering/confinement and failed native output.
- `externals/UMR/.venv/bin/python -B -m unittest discover -s tests -p test_studio_source_mesh_runtime.py -v`:
  **1 actual native CPU test passed**. Full 165-channel, 66-frame, Y-up source at
  47.5 FPS matched direct `SMPLX.forward` reconstruction at frames 0/63/64/65,
  using nonzero body poses, shape, translations and ignored hand input. Native
  topology matched exactly: 10475 vertices / 20908 triangles; maximum decoded
  axis error `5.003452301e-5 m`. Source bytes stayed unchanged and no run existed.
- Existing `test_studio_source_preview.py`: **6 legacy tests passed**.
- `python3 -B scripts/check.py --tier pure`: **30/30 selected suites passed**;
  `git diff --check` and focused Python compilation passed.

## Answer

Implemented animated native human surfaces in sample thumbnails and the central
source preview. The motion library now has one readable card per sample, short
names, duration and rounded FPS, with provenance collapsed by default. Preview
and Use for retargeting are separate actions; browsing does not edit a run.

- Prepared all three local samples: 180-frame excerpt, 5468-frame HiPHI and
  7745-frame tennis. Mesh caches remain local and support offline viewing.
- Browser acceptance verified animated thumbnails, play/pause, exact frames
  63/64, tennis raised-arm frame 796 and both full clips' final frames. Camera
  framing passed narrow and wide viewport checks. Final REA capture completed
  without page errors; see [screenshot](../../../outputs/studio-mesh-preview-20261030/mesh-library.png).
- Four frontend suites and eight module syntax checks passed. Independent
  correctness review found no remaining actionable findings.
- Before/after run, job and selected-run records matched exactly. The original
  preservation verifier passed all 288 protected files and external states.
  Existing viewers, completed runs and pinned externals remain unchanged.
- Source reconstruction uses neutral hands and omits facial animation, disclosed
  in the preview. Source channels remain preserved. No retarget job was started
  for this visualization-only follow-up.

Evidence: `outputs/studio-mesh-preview-20261030/` contains server/prewarm records,
state snapshots and the acceptance screenshot. REA capture evidence ID:
`ev_98ec83bcef6a67451ffc76c2155371e2f39f13a522425a66c587b0cbdcd339e0`.
