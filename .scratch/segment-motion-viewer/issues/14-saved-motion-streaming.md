# 14 — Remove redundant pipeline validation from motion streaming

Status: resolved
Category: bug
Spec: ../spec.md
Blocked by: none

## Context

Retargeted playback repeatedly paused with “Loading source frame …”. The selected
G1/HiPHI full clip stores 64-frame chunks at 90.001 FPS (0.711 seconds per chunk).

## Scope

Serve registered inspection chunks independently of native-stage hydration, while
preserving run existence, bundle registration, path confinement and per-file hashes.
No changes to saved outputs, numerical playback, chunk cache or external projects.

## Acceptance criteria

- Local chunk delivery fits within the playback window.
- Streaming does not recursively verify native receipts.
- Changed exported bytes still fail verification; unknown runs return 404.

## Answer

Reproduced by `python3 outputs/studio-playback-20261030/probe.py`: three 4,022,400-byte
chunks took 1.178, 1.220 and 1.137 seconds, failing the 0.711-second delivery budget.
Browser playback displayed “Loading source frame 960…” while held at frame 959.

Ranked causes: native run validation, chunk I/O/hash cost, insufficient prefetch.
Profiling exported_inspection_file showed 638/641 ms in get_run hydration, including
651 digest calls. HTTP routing independently hydrated the run too. Replaced both
with a lightweight existence/kind lookup; retained requested-resource SHA-256.
After removing both checks, the same probe passed with 0.006 seconds per chunk.

Regression failed before the fix on native receipt hydration and passed afterward.
The test covers both file access and real HTTP routing, corrupted bytes and missing
runs. Five inspection and five HTTP tests passed; whitespace passed. All 288
protected files passed preservation verification.

Fresh browser replay reached frame 1097 (12.19 seconds) after a 12-second observation
at 1x, crossing 17 chunk boundaries; no page errors. Screenshot:
`outputs/studio-playback-20261030/playing.png`. Evidence:
`ev_665d5e88f3313084d27aa2ce0182849e38cb9fa71fdc6635cfd22dbd05d4d8dc`.
This validates local streaming for the saved full G1/HiPHI clip, not all hardware or
slow storage conditions. No native job or bundle rebuild was needed. Existing
standalone bundle bytes remain intact.
