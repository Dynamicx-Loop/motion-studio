# UMR Studio: evidence for reusable viewer design

Investigated 2026-10-30. Scope: official public Studio and directly linked browser
sources, with the local pinned UMR checkout and existing viewer handoff as comparison.
This is research, not an implementation specification or integration decision.

## Evidence and limits

The official HTML and JavaScript were fetched and inspected. The local UMR checkout
reports revision `d1cdaedaf67a827198da71c5fa831f48b2e51f91`. The public website was
inspected as deployed; its source was **not** established to match that revision.
No browser training, retargeting job, performance benchmark, or interactive visual
check was run. Behaviors below are source observations or documented claims, not
newly tested runtime guarantees. No external or viewer files were modified.

## Product workflow

The [official Studio page](https://hanyang9.github.io/UMR/umr_studio.html)
describes a browser-local sequence: load an MJCF robot, edit its T-pose, choose a
reference, sample surfaces, train correspondence, bind meshes, and retarget. Its
preset cards include PiPlus, Booster K1, Unitree G1, and EngineAI T800. It explicitly
calls this a visualization experience, requires at least 3 GiB free memory, and
says results cannot be downloaded because of data licensing. CPU browser
performance is explicitly not representative of native UMR.

The [Studio template](https://hanyang9.github.io/UMR/umr_project.html) provides:

- UMR and HiPHI reference-library tabs with motion cards.
- Folder/drop/paste robot loading, MJCF selection, a root/torso selector, searchable
  joint controls, direct joint dragging, Reset, and Copy T-pose config.
- T-pose, Samples, Mesh binding, and Motion stage tabs; completed stages remain
  reviewable. Stage-specific instructions and progress expose the computation.
- Worker-count selection, Retarget/Stop, then play/pause, frame scrubber, frame/time
  display, and speeds 0.5×, 1×, 1.5×, 2×.

The template documents hinge values in degrees and slide values in metres. These
are UI units, not proof of a general motion interchange contract.

Native UMR documents the practical bridge: copy `tpose_qpos` from Studio into a
robot config and run the native pipeline. See the [pinned README](../../externals/UMR/README.md)
and its [revision-specific upstream counterpart](https://github.com/hanyang9/UMR/blob/d1cdaedaf67a827198da71c5fa831f48b2e51f91/README.md).

## Runtime and asset architecture

The [standalone-page loader](https://hanyang9.github.io/UMR/static/js/umr-studio-page.js)
fetches `umr_project.html`, extracts its Studio template, mounts it, and imports
`mujoco-viewer.js`. Thus the standalone entry page shares the project-page
application rather than embedding a separate remote compute service.

The [main viewer](https://hanyang9.github.io/UMR/static/js/mujoco-viewer.js) imports
vendored Three.js, OrbitControls, MuJoCo WASM, a reference-motion library, the browser
runtime, and floating-root preparation. Browser computation is the default; a
`compute=server` query option selects a separate server path. Public deployment
availability of that alternative was not tested. HTTP hosting is required by its
WASM loading path.

The [browser runtime](https://hanyang9.github.io/UMR/static/js/browser-umr-runtime-exact-v1.js)
orchestrates source-pack loading, visual mesh collection, WASM exterior sampling,
WASM correspondence training, slot binding, current-run compute-pack construction,
and a MuJoCo-Jacobian/Clarabel retargeter. Its result includes `umr-qpos-v1`, qpos,
`nq`, FPS, source-frame IDs, ground height, interaction objects, and compute backend.
Names containing “exact” identify this implementation; numerical parity with the
native pinned checkout was not verified here.

The [training wrapper](https://hanyang9.github.io/UMR/static/js/umr-exact-correspondence-wasm-v1.js)
runs one-worker training in process and multiple workers through a module Worker.
Multicore mode checks cross-origin isolation, SharedArrayBuffer, and Worker
availability; it reports an error recommending one worker when isolation is
missing. Synchronous single-worker epochs yield between epochs. The template says
60 epochs, while the implementation obtains the actual epoch count from its
runtime contract. The page also loads `coi-serviceworker.min.js`; merely copying
its visible HTML would not package the full runtime.

The [source-pack loader](https://hanyang9.github.io/UMR/static/js/umr-exact-source-pack-v1.js)
loads per-motion `source-manifest.json` plus binary assets under
`static/assets/browser_runtime/source/`, and validates a versioned format marker.
The [reference library](https://hanyang9.github.io/UMR/static/js/reference-motion-scene.js)
loads static catalogs and per-motion JSON with API fallbacks. It supports skinned
vertex tracks, skeleton tracks, and MuJoCo qpos tracks, plus interaction-object
geometry/transforms. Skinned tracks load full typed-array assets, including int16
vertices, uint16 indices and float32 roots; supported compression includes gzip
spatial/temporal int16 deltas. This source does not establish the bounded 64-frame
chunk cache used by the local Motion Studio viewer.

## What “mesh binding” and playback actually mean

The [runtime stage-artifact builder](https://hanyang9.github.io/UMR/static/js/browser-umr-runtime-exact-v1.js)
constructs source/target point arrays, segment IDs, correspondence IDs and segment
names. The final classification artifact uses learned slots projected onto both
meshes. It is a distinct visualization artifact, not the entire solver binding.

The [robot binding module](https://hanyang9.github.io/UMR/static/js/umr-exact-robot-binding-v1.js)
projects slots to mesh faces, resolves geom/body ownership, and stores geom-local
positions/normals, face IDs and barycentric coordinates. Projection is configurable;
when disabled, local positions derive from learned slot positions. Explicit axis
conversion separates training coordinates from robot-root coordinates. These
contracts are much richer than a pair of colored XYZ arrays.

In the [viewer stage/render/playback methods](https://hanyang9.github.io/UMR/static/js/mujoco-viewer.js),
Samples and Mesh binding show side-by-side normalized clouds with training-center
markers. Binding colors carry segment and correspondence information. Switching
to Motion clears stage visualization: this is **not an animated binding-point
inspector**. Motion applies discrete qpos and calls `mj_forward`; playback is
kinematic. Wall-clock time and selected speed choose integer frames, modulo clip
length, so looping is automatic and slow rendering can skip displayed frames.
Reference synchronization uses `source_frame_ids`, with a time/FPS fallback.

The reference library's `setSourceFrame` binary-searches available source frame IDs
and chooses the nearest one, preferring the earlier entry on an equal-distance tie.
Consequently synchronization can mean nearest available reference sample, not
necessarily identical sampling on both tracks. See
[reference-motion-scene.js](https://hanyang9.github.io/UMR/static/js/reference-motion-scene.js).

## Comparison with Motion Studio's existing viewer

Local evidence: [handoff](handoff.md) and [viewer guide](../../docs/umr-g1-binding-viewer.md).
The local viewer's reported checks were read, not rerun in this investigation.

| Concern | Official Studio, inspected source | Existing local viewer, documented contract |
| --- | --- | --- |
| Primary job | New-robot pose preparation and browser retargeting | Inspect a completed saved G1/UMR run |
| Bindings | Separate normalized canonical-stage clouds | Points transported on both moving surfaces, selected slots and paired lines |
| Source identity | Motion catalogs and source frame mapping | Recorded source/model hashes, frame IDs and export provenance |
| Playback | qpos forward kinematics, looping, nearest reference frame | Original saved frames/FPS, shared buffering, explicit loop control |
| Human storage | Full decoded binary tracks | Root-relative int16 chunks, 64 frames per chunk, three cached |
| Inspection controls | Stage review, pose editing, segment legend | Segment filters, target ownership, point picking, camera presets and centering |
| Runtime boundary | Browser renderer plus sampling/training/solver stack | CPU exporter plus static browser replay; no training/solve |
| Reuse boundary | Curated references, MJCF assets and browser compute packs | Currently fixed revision, G1 and SMPL-X assumptions |

## Design implications to discuss, not settled requirements

1. Keep “review a completed result” distinct from “run retargeting.” Studio's staged
   workflow is a useful UX reference without requiring a solver in the reusable
   viewer. The local moving-binding inspection is a concrete capability beyond
   Studio's separate canonical-stage visualization.
2. Treat paired slot identity, semantic segment labels, and target geom/body
   ownership as separate concepts. Bindings require transport rules and coordinate
   metadata, not just static points.
3. Specify source-frame mapping explicitly. Strict one-to-one replay, nearest-frame
   lookup and time-based synchronization are different contracts.
4. Decide whether canonical normalized comparison and physical-scale motion are
   separate views. Studio's point-cloud normalization should not silently become
   the coordinate convention of a reusable inspection artifact.
5. Copy useful interaction ideas only after deciding asset/runtime ownership.
   Dropping the complete Studio stack into this project would pull in computation,
   curated data, WASM, worker and isolation concerns not needed for saved replay.

## Licensing and unresolved provenance

The [pinned UMR LICENSE](../../externals/UMR/LICENSE) grants MIT software rights
subject to preserving its copyright and permission notice. That is not evidence
that website motion assets, SMPL-X weights, robot meshes, or all website source
files inherit the same license. The Studio explicitly restricts result downloads
for data-license reasons. The project page credits NeRFies/Jekyll website templates
and an adapted Robot Viewer; those origins need review before copying browser code.
No asset redistribution permission or website-to-native revision correspondence
was established. This is a concrete provenance gap, not a claim that reuse is
forbidden.

## Retrieval fingerprints

Fetched directly from the URLs above on 2026-10-30. These hashes identify the
inspected deployment content when the website later changes:

| File | SHA-256 |
| --- | --- |
| `umr-studio-page.js` | `20dec83ec8499a438aad329115714be8b823b22f1f0c71ccb939c4938e22b1a8` |
| `mujoco-viewer.js` | `bb71d0ffbf2751455d167f1e1cccfa9a8c47aaf335139091e3d2b9ead4c5802a` |
| `browser-umr-runtime-exact-v1.js` | `37699e28038a69ba6e504a33904d6ab1c6e25efff9ad16554eedde5f5f87a08b` |
| `reference-motion-scene.js` | `f0377c83b3ae0c64421fb37300adcd28d650a7e9310330d83e8ac64d0e95c71c` |
| `umr-exact-robot-binding-v1.js` | `7a473016335387d68e31ad7dbf2a8127ed257198c7af1fdc28238f0e7d5ca894` |
| `umr-exact-correspondence-wasm-v1.js` | `d3c77b638ff8979c46c8a761ddadcd724a152a7f9c5310516368d42860130bbc` |
