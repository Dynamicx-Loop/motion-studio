# FZMotion Wendy sample

Original local captures from the Wendy session dated 2026-10-19:

```text
fzmotion/
  source-dataset.json
  wendy/2026-10-19/
    victory-146-short_Skeleton1.bvh
    Wendy-t-pose_Skeleton1.bvh
```

The source is `/data/motions/datasets/fzmotion/raw/bvh/wendy/2026-10-19/`.
`source-dataset.json` preserves the canonical dataset metadata. Only one motion
and its calibration reference are selected from the 80 source BVHs; the source
archive and remaining clips are kept in their original location.

| File | Frames | Source frame time | Channels |
| --- | ---: | ---: | ---: |
| `victory-146-short_Skeleton1.bvh` | 1383 | 0.0142857 s (about 70 FPS) | 174 |
| `Wendy-t-pose_Skeleton1.bvh` | 331 | 0.00833333 s (about 120 FPS) | 174 |

The samples retain every frame, hierarchy, joint name, channel order and Euler
rotation channel exactly as supplied. The T-pose is a separate multi-frame
capture with a different frame rate; it is not a synchronized motion track.
Units, axes and detailed acquisition settings remain unverified in the source
metadata. The [owned Wendy conversion interface](../../../docs/wendy-conversion-adapter.md)
assumes centimeters and Y-up and requires explicit mapping and licensed SMPL-X
assets. Raw BVHs remain separate from the derived SMPL-X sequence below.

Proprietary owner-supplied mocap: keep local. No redistribution permission is
recorded. Motion payloads and the source metadata copy are ignored by Git;
the parent manifest preserves their source paths and checksums.

## Converted SMPL-X motion for UMR

`smplx/victory-146-short_Skeleton1.npz` contains the full 1383-frame victory
motion: `poses` is float32 `[1383, 165]` in SMPL-X joint order and axis-angle
radians, `trans` is float32 `[1383, 3]` in meters, and `betas` is ten fixed zeros
for the neutral body. `output_up` is `y`. Original frame indices, timestamps and
frame time are included; `mocap_framerate` is about 70 FPS. No frames were trimmed
or resampled. The converter assumes centimeters and Y-up and scales by 0.01.

The owned converter fitted the body using pinned hiphi2smplx revision
`65e51315ebbc82b2f0ff8e35a94565beb1b345e1`. Mean joint residual is 0.03517 m;
the largest per-frame mean is 0.03891 m. Shape is not estimated, fingers/face/eyes
are not fitted, and this is an approximate kinematic fit. The T-pose is retained
as raw calibration data and was not used for actor-shape estimation.

UMR's actual `load_motion_collection` and `select_sequence` accepted this NPZ
with all 1383 frames, neutral gender, Y-up metadata and source frame rate. In a
fresh owned UMR experiment configuration, set:

```json
{
  "motion": {
    "data": "/data/workspace/motion_studio/data/sample_data/fzmotion/smplx/victory-146-short_Skeleton1.npz",
    "seq_key": "victory-146-short_Skeleton1"
  }
}
```

Merge these fields into the selected robot configuration, retaining the normal
licensed SMPL-X model setup and choosing fresh output paths. The file also works
as a motion directory input via `fzmotion/smplx/`; diagnostics are kept below
`smplx/provenance/` so directory scans do not mistake them for motion sequences.
No correspondence training or robot retargeting was run for this sample.

`smplx/provenance/` holds diagnostics, fit report, source/model/code hashes,
runtime environment, conversion config and log. Canonical derived copies live at
`/data/motions/datasets/fzmotion/derived/smplx/wendy-victory-20261102-v1/` and are
used by the sample population script. See the
[experiment record](../../../experiments/wendy-victory-sample-20261102/README.md).
