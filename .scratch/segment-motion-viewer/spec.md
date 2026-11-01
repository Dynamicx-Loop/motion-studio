# Local Motion Studio with native UMR

Status: resolved

## Problem Statement

The current synchronized human/G1 binding viewer is a working saved-export vertical slice. The user needs a persistent fully local Studio workflow for preparation, native UMR execution, intermediate inspection and motion playback, serving as a validated foundation for later hhtools integration.

## Solution

Build a single-user local application with a run/asset sidebar, central 3D stage viewport, settings/details panel and persistent status/log access. Native pinned UMR runs in its existing independent CUDA environment. Everything operates offline after setup. Preserve the existing viewer, completed runs, historical experiments, frozen assets and pinned external source unchanged.

## User Stories

1. As a Motion Studio user, I want to launch a single-user offline local application, so that hosted services are unnecessary.
2. As a Motion Studio user, I want to open historical G1 results read-only, so that prior evidence remains intact.
3. As a Motion Studio user, I want to import a complete local humanoid MJCF asset, so that I can prepare a robot without editing upstream code.
4. As a Motion Studio user, I want to validate compiled joints, roots, limits and asset dependencies, so that unsupported inputs fail clearly.
5. As a Motion Studio user, I want to edit and save named T-poses with numeric joint/root controls, so that preparation is reproducible.
6. As a Motion Studio user, I want to import a single-person SMPL-X NPZ with explicit metadata, so that motion interpretation is unambiguous.
7. As a Motion Studio user, I want to see neutral-hand and omitted-face disclosures, so that native reconstruction limitations are clear.
8. As a Motion Studio user, I want to keep immutable managed versions of imported assets, so that moving originals cannot break runs.
9. As a Motion Studio user, I want to select official G1 defaults or curated advanced settings, so that experiments retain an identifiable reference.
10. As a Motion Studio user, I want to run the entire pipeline or through a selected stage, so that intermediate results can be inspected.
11. As a Motion Studio user, I want to inspect sampled surfaces and canonical bindings before solving, so that correspondence can be evaluated.
12. As a Motion Studio user, I want to see real stage, epoch/frame and elapsed-time progress with logs, so that execution is understandable.
13. As a Motion Studio user, I want to close the browser without terminating computation, so that jobs are independent of UI lifetime.
14. As a Motion Studio user, I want to stop and retry a stage while retaining completed work, so that recovery does not destroy evidence.
15. As a Motion Studio user, I want to create fresh revisions when inputs/settings change, so that completed results remain immutable.
16. As a Motion Studio user, I want to reuse only verified compatible stages, so that stale data cannot silently affect results.
17. As a Motion Studio user, I want to inspect saved runs while one job computes, so that GPU work does not block analysis.
18. As a Motion Studio user, I want to play synchronized human/robot motion with animated bindings, so that correspondence can be inspected over time.
19. As a Motion Studio user, I want to filter segments, select paired slots and inspect ownership, so that binding errors can be localized.
20. As a Motion Studio user, I want to scrub exact saved frames and control speed/loop/centering, so that motion inspection preserves source timing.
21. As a Motion Studio user, I want to access native outputs, logs and provenance, so that results remain usable outside the application.
22. As a Motion Studio user, I want to export a standalone offline HTTP inspection bundle, so that viewing does not require UMR.
23. As a Motion Studio user, I want to check environment readiness before computation, so that missing prerequisites produce actionable errors.
24. As a Motion Studio user, I want to validate a fresh full G1/HiPHI run and lifecycle behavior, so that the application is a demonstrated baseline.
25. As a Motion Studio user, I want to add hhtools later through a concrete adapter, so that backend differences do not leak into generic run management.

## Implementation Decisions

- User confirmed the complete agreement on 2026-10-30; the accepted interview is authoritative supporting detail. This spec supersedes earlier export-only proposals.
- Application owns persistent run/asset management and visualization. Concrete UMR adapter owns upstream imports, translation, environment invocation and result validation. Prefer existing owned operations and preservation/artifact facilities; do not change prepared-only canonical preparation into execution. No general plugin registry yet.
- Test through outcome-oriented owned operations and the same HTTP/UI surface used by callers. Keep numerical and runtime details private. New application operations must expose typed results, expected failures, units, timing and mutation contracts.
- Use a loopback local service, no accounts or hosted services. Jobs outlive browser sessions; service interruption is detected and reported. Only one active compute job, with other runs saved as drafts; no automatic queue.
- Stages: import/pose preparation, sampling, correspondence training, binding inspection, retargeting, motion inspection. Run all or through a selected stage. Tab navigation never starts computation. Show prerequisite work before launch; native implicit build/train must not bypass owned orchestration.
- Cancel terminates owned process group, retains logs and completed artifacts. Retry restarts the interrupted stage; no epoch/frame checkpoint continuation promise. Publish completion receipts only for verified stage outputs. Reuse checks exact recorded dependencies/settings/hashes. New input/settings edits make a new revision and mark stale stages. Cross-clip correspondence reuse is deferred.
- Robot support: one humanoid, named finite-limit hinge joints, one floating root or explicit recorded fixed-to-free derivation. Resolve compiler defaults and angle units using compiled model metadata, validate selected root/torso, include/mesh/material dependencies and path confinement. Reject slides/balls, extra free joints, ambiguous roots, multi-robot scenes, missing/cyclic/escaping dependencies. Preserve original assets and record derived changes including synthetic inertia. Do not apply G1-specific solve limits to arbitrary imports.
- T-pose controls: searchable sliders/numeric values, root position/orientation, reset and named save/load, explicit units and enforced limits. No direct limb dragging/IK.
- Motion support: single-person safe NPZ numeric/string arrays, recognized axis-angle body/full SMPL-X layout, finite translation in metres, constant ten-value shape, recognized gender/installed matching model, explicit positive constant FPS and Y/Z-up. Missing metadata is supplied explicitly or rejected; conflicting aliases fail. All frames retained. Irregular timing/custom frame numbering, interaction objects, expressive hand/face reconstruction deferred. Preserve full original bytes; native root/body reconstruction uses neutral hands and omits facial channels, clearly disclosed in UI/records.
- Imported robot/motion versions are copied into immutable hash-identified managed storage. Licensed weights remain at configured external local location with checked hashes. Missing/changed weights block reconstruction, not existing bundle viewing.
- Official G1 preset retained. Advanced controls: sampling seed 0, training epochs 500, trajectory filter LQR or none after validation. Training/solver seeds, 4096 slots, native19 taxonomy, binding k=24/projected robot slots and full-clip selection remain fixed/inspectable. Full resolved configuration available. Resource override SMPL-X batch cap 128 is not a quality preset.
- Show real progress (stage, elapsed, observed epoch/loss or frame count), logs and contextual failures; no invented percentages/ETA.
- Stage inspections plus moving bindings use explicit distinction between source semantic labels, paired slot identity and target geom/body ownership. Existing selection/filter/paired lines/mesh visibility/orbit/zoom/camera presets/reference pose/centering preserved.
- Exact saved frame IDs/FPS/scale/ground convention; no interpolation/resampling/nearest-frame fallback. Both tracks commit together; stepping/scrubbing exact, display frame skipping allowed. Horizontal centering and comparison placement are display-only. Bounded human-frame cache.
- Native results/config/logs/provenance available through UI. Standalone bundles include local dependencies/notices and work over HTTP without UMR; no file-double-click guarantee. Do not rely on old generated outputs as permanent vendor source; preserve/license/hash required vendor assets independently.
- Historical G1 outputs are registered/read read-only and clearly labeled; new inspection derivatives always use fresh destinations. No existing run mutation, external patches/pin changes or cleanup of unrelated local work.

## Testing Decisions

- Drive implementation with TDD through public outcomes; meaningful success/failure/edge tests, not private call choreography. Existing owned preservation, inspection, numerical and JS cache tests provide prior art and remain intact.
- Test import closure/compiled metadata/pose limits and invalid NPZ contracts; immutable revisions and source preservation; single-job exclusivity, cancel/restart, stale completions, service interruption and verified cache reuse.
- Test offline HTTP app flows and standalone bundles in a browser, including stage availability, pose controls, history restoration, logs, exact frame stepping, boundary scrubbing, both moving meshes/bindings, filtering/selection, centering, loop/end-stop.
- Fresh full G1/HiPHI run via app is mandatory acceptance, using CUDA readiness checks and fresh output destination. Preserve historical outputs byte-for-byte. Compare config/outcome to baseline without requiring new training to be byte-identical.
- Numeric gates: finite qpos with model nq, exact source frames, FPS agreement <=1e-6, root quaternion norm error <=1e-6, joint limit excess <=1e-6 rad. Robot replay binding axis error <=5e-7 m; human decoded vertex/binding axis error <=5.1e-5 m against native reference including chunk boundaries. Static reconstructed target faces exact and vertices atol 2e-7 m where applicable.
- Record loading/seeking/playback and job durations on this machine; no requirement to display every ~90 FPS input frame. Motion quality observations are separate from representation gates; no contact/dynamics claim.
- Run owning check tiers proportionately, complete integration code review along standards and spec axes, fix actionable findings, report any hardware/asset limitations honestly. Do not mark acceptance complete with required runtime checks unperformed.

## Out of Scope

hhtools implementation, universal plugin framework, cloud/multiuser deployment, automatic queues/parallel GPU jobs, CPU-only training/retarget acceptance, mid-stage checkpoint resume, cross-clip correspondence reuse, full hosted catalog/pixel-identical Studio UI, expressive hands/faces, interaction objects, irregular timestamps, motion editing/resampling, IK pose editing, unsupported robot joints, physical/dynamic certification.

## Further Notes

This is an application baseline, not a replacement of historical numerical cohorts. All implementation lands on one integration branch via isolated ticket worktrees. Use the canonical workspace's pinned externals/assets read-only for runtime checks. The original viewer is preserved and may serve as a compatibility/reference implementation; build owned new modules additively where necessary.

Evidence: [confirmed interview](design-interview.md), [handoff](handoff.md), [official Studio research](umr-studio-research.md), [REA setup](rea-setup.md).

## Asset experience follow-up (2026-10-30)

User requested the official Studio asset-library interaction and layout, built-in
robot drag/drop and custom robot file drops, quick sample motion testing and
visualization, default named T-poses and display grounding. Implemented within
the same owned local service and native adapter constraints; see
[Ticket 08](issues/08-asset-library.md). This extends the previous exclusion of a
full hosted catalog with four locally available verified official robot examples.
Ground placement is display-only and never silently changes saved qpos.

## Source mesh preview follow-up (2026-10-30)

The user requested full animated source human meshes and sample motion thumbnails
before retargeting. [Ticket 09](issues/09-source-mesh-previews.md) adds a separately
versioned, hash-registered topology and bounded quantized vertex cache, exact
original frames/FPS/translation, and browse-only card previews with explicit use.
The earlier skeleton cache and historical native inspection contracts remain
preserved. Surface reconstruction uses neutral hands and omits facial channels.

## Inspection Properties follow-up (2026-10-30)

The user requested that embedded completed-stage inspection controls move into
the main Properties panel, freeing the scene from the nested sidebar.
[Ticket 13](issues/13-inspection-properties.md) retains exact playback, slot and
segment selection, binding details, display/camera settings and synchronized
point picking through an owned renderer command/state interface. Existing bundle
bytes/hashes, standalone controls and historical viewer are preserved; this
layout change starts no native computation.

## Bundled Astro follow-up (2026-11-01)

User requested a root `assets/` directory and the latest local Astro robot as a
built-in. [Ticket 15](issues/15-bundled-astro.md) snapshots the default 29-joint
Astro P2 from the clean `menagerie_x` source revision, including exact meshes,
XML and licenses, with an owned import derivative for shared collision models.
The existing asset library and immutable robot/pose flow expose it without a live
source checkout. Earlier experiment definitions, sources and UMR pins retain their
separate recorded identities.
