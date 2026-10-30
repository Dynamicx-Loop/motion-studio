# Local Motion Studio baseline — design interview

## Settled decisions

Confirmed by the user on 2026-10-30:

- First reproduce the official UMR Studio workflow locally in Motion Studio; use the validated local application as the foundation for later retargeting backends such as hhtools.
- Execute native pinned UMR through a Motion Studio adapter, retaining its independent runtime.
- Reproduce workflow and inspection capabilities using Motion Studio's own layout and local assets. Exact visual duplication and the complete hosted catalog are not baseline requirements.
- The earlier saved-results-only proposal is superseded. Its proposed fixtures-only reuse milestone and export-only delivery form were never accepted.

Confirmed in round 2:

- Accept local MJCF assets and compatible SMPL-X motions; G1 with the existing HiPHI clip is the required end-to-end acceptance case. Include robot loading and T-pose editing, with explicit validation/rejection for unsupported inputs.
- Single-user local application; the local process owns jobs and persistent artifacts. Browser closure/refresh does not own job lifetime; reopening restores run history. Interrupted-stage recovery remains to be decided.
- Preserve stage-by-stage sampling/canonical binding inspection and synchronized animated binding inspection, including filters, paired-slot selection and ownership.
- Complete workflow operates offline after setup, with local frontend dependencies and explicit local assets.

Confirmed in round 3:

- Offer Run all and run through a selected stage; show prerequisite computation before starting and retain completed stage inspection.
- Stop preserves completed artifacts/logs. Retry restarts the interrupted stage with verified completed prerequisites. Browser closure does not stop jobs; service interruption is detected on reopening and retry remains explicit. No mid-stage resume guarantee.
- Input/pose/settings changes create fresh run revisions; preserve previous results and visibly invalidate affected stages. Reuse requires matching recorded inputs/settings; cross-clip correspondence reuse is deferred pending a validated compatibility contract.
- One compute job at a time. Saved-run inspection remains available; additional runs remain drafts until explicitly started. Automatic queue and parallel GPU execution are deferred.

Confirmed in round 4:

- Numeric T-pose editing: searchable joint sliders/numeric values, root translation/orientation, reset and saved named poses; explicit units/limits. Direct limb dragging and IK pose editing deferred.
- Pinned official-default G1 preset plus curated validated Advanced settings. Full resolved configuration inspectable; exact editable settings remain open.
- Exact saved-frame/source correspondence and FPS, scale and ground convention; no interpolation/resampling. Placement/centering are display-only. Missing source matches are errors, not nearest-frame substitution.
- UI access to native motion, configuration, logs, provenance and standalone inspection bundles. Bundles run over local HTTP without UMR; file-double-click support is not required.

Confirmed in round 5:

- Initial robot imports: one humanoid, named finite-limit hinges and one floating root; explicit recorded fixed-to-free-root derivation allowed on copies. Resolve compiler defaults/angle units, validate complete local asset dependencies and torso/centering selection. Ball/slide joints, multi-robot scenes and ambiguous roots are unsupported initially.
- Initial motion imports: single-person SMPL-X NPZ, constant FPS, explicit translation/axis metadata, constant ten-coefficient shape. Preserve source bytes/channels but reconstruct native body/root motion with disclosed neutral hands and omitted facial channels. Missing metadata requires explicit supply or rejection. Irregular timing, expressive hands/faces and interaction-object tracks deferred.
- Copy imported robot/motion assets to a managed hash-identified library; runs reference immutable versions. Keep licensed model weights at configured local location and record hashes. Missing/changed weights block reconstruction, not viewing completed bundles.
- Acceptance includes fresh full G1/HiPHI execution through the app, stage inspection, cancellation/retry, revision invalidation, reopening, offline operation and standalone playback. Validate playback against the new run's native outputs, compare config/outcome with preserved baseline, and do not require byte-identical new training results.

Confirmed in round 6:

- Main layout: run/asset sidebar, central 3D viewport with stage tabs, settings/details panel, persistent access to status/logs. Show current run/revision and stage availability; tab navigation never launches work. Saved results stay browsable during computation.
- Computation requires validated CUDA UMR environment and readiness checks for source pin, interpreter, GPU, models, inputs and output location. Saved viewing remains available without CUDA. CPU-only training/retargeting deferred.
- Isolate UMR-specific imports, translation and execution behind concrete adapter; application owns run management and visualization and consumes explicit results/artifacts. Defer general plugin system until hhtools provides demonstrated variation; do not require other backends to mimic UMR stages.
- Existing completed G1 result accessible as read-only labeled historical reference. Fresh inspection derivatives use new destinations and do not imply a fresh native run.

Confirmed in round 7:

- Advanced controls: sampling seed 0, training epochs 500, trajectory smoothing LQR with off offered after validation. Keep training/solver seeds, 4096 slots, segmentation, binding parameters and full-clip selection fixed/inspectable. Modified runs are labeled, not represented as validated quality presets.
- Progress: active stage, elapsed time, observed epochs/loss or completed frames, live logs; no fabricated percentages/ETA. Failures retain stage/context/logs.
- Numerical acceptance: finite output, exact frame correspondence, dimensions/FPS, root quaternion norms and joint-limit compliance; robot binding replay per-axis tolerance 5e-7 m and human decoded vertex/binding tolerance 5.1e-5 m with native references/chunk-boundary samples. These are representation checks, not contact/dynamics certification.
- Playback: responsive controls, bounded human cache, synchronized frames; rendering may skip displayed frames to follow time. Scrubbing/stepping reach exact requested frames. Measure machine-specific loading/seeking/playback, with no requirement to render every ~90 FPS input frame.

## Evidence

- [Working viewer handoff](handoff.md)
- [Official Studio investigation](umr-studio-research.md)
- [REA installation and checks](rea-setup.md)
- [Native integration review](../../docs/umr-integration-review.md)

## Design tree

1. Local Studio workflow with native UMR (settled)
   - Baseline input/robot coverage (settled at product level; detailed supported subset open)
     - Import validation, pose preparation and asset ownership
   - Local application lifecycle and persistence (single-user/persistent settled)
     - Job queue, cancellation, recovery and progress
   - Inspection scope (stage inspection plus animated bindings settled)
     - Stage artifacts, animated binding inspection and timeline semantics
   - Localization requirements (offline after setup settled)
     - Asset packaging and network independence
2. Native stage interfaces and compatibility (fact exploration underway)
   - Stage execution and reuse/invalidation decisions
3. Validation and baseline acceptance
   - Numerical comparisons, UI checks and representative complete run
4. Future hhtools seam based on demonstrated variation
5. Explicit shared-understanding confirmation before implementation

No implementation specification is approved yet. Recommendations in interview rounds are proposals until answered.

## Native-stage exploration findings

Read-only source inspection at pinned UMR revision, without compute jobs:

- Native CLI stages are build/train/retarget/view/all. Training can build implicitly; retarget can build/train implicitly. There is no standalone bind CLI stage. Owned orchestration must enforce explicit prerequisites and construct a pre-solve binding inspection artifact using native functions.
- Owned G1 reproduction is fresh-output-only. Canonical preparation already provides stronger stage fingerprints/cache guards but remains prepared-only and must keep that contract.
- Native trainer writes checkpoints but has no inspected checkpoint-loading/resume flow. Recovery should not promise continuation within an interrupted stage.
- Retarget offers machine-readable frame progress; training offers periodic epoch/loss logs. Existing owned process-group handling can support cancellation, but no public job lifecycle currently exists.
- Sources: `motion_studio/integrations/umr.py`, `motion_studio/integrations/umr_canonical.py`, `externals/UMR/scripts/humanoid_retarget_pipeline.py`. Facts inform proposals; execution/reuse policies remain undecided.

## Import exploration findings

The pinned SMPL-X forward path uses root/body pose channels through index 66, always zeroes hands and ignores face/jaw/eye channels. Thus exact saved-frame timing does not imply full-channel source reconstruction. The baseline HiPHI has poses (5468,165), trans (5468,3), betas (10,). Native import has permissive defaults for FPS/translation/shape that the owned importer should not silently inherit.

Native robot preparation can derive a free root but writes beside its input; invoke only on controlled copies. Named bounded hinges are the grounded initial robot subset. Imported MJCF compiler defaults/degrees need compiled metadata; the existing catalog parser alone does not cover them. Root/torso selection and complete include/mesh/material dependencies need explicit validation.

Sources: `externals/UMR/scripts/smpl_surface_retarget_common.py` (load_smplx_npz_motion, smplx_motion_vertices_joints), `externals/UMR/scripts/retarget_smpl_to_humanoid_surface_vector.py` (prepare_robot_xml), `motion_studio/robots/_model.py`. These are inspected facts, not executed generic-import validation.

## Final settings/validation exploration

Inspected native defaults, G1 preset, owned `_umr_worker.py` validator and manual-01 evidence. Candidate Advanced settings: dataset seed (0), train epochs (500), trajectory filter (lqr; none requires validation). Separate training/solver seeds remain unchanged unless explicitly designed otherwise. Existing contract fixes 4096 slots, native19 taxonomy, binding k=24/projected robot slots, neutral hands and full-clip frame selection. G1-specific solve-time limits must not leak into imported robots.

Existing numeric thresholds: FPS error <=1e-6; root quaternion norm error <=1e-6; joint-limit excess <=1e-6 radians; robot binding replay axis error <=5e-7 metres; human decoded vertex/binding axis error <=5.1e-5 metres. These validate representation/playback, not dynamics. Joint-step measurements are descriptive; no established foot-slip/contact/dynamics quality gates exist.

Manual-01 measured 41.73 seconds build/training and 99.99 seconds retarget, 5468 frames at ~90.0009 FPS on RTX 5070 Laptop GPU. These are historical single-run observations, not promised speed targets.

## Confirmation status

All numbered interview choices Q1–Q26 in the revised local-Studio interview have been accepted. Consolidated agreement presented for explicit confirmation before implementation. No implementation has started. Earlier superseded export-only proposals remain unaccepted. Implementation details may be selected within these contracts; a material scope or fidelity change requires revisiting the affected decision.

User confirmed the consolidated agreement and authorized spec/tickets and implementation. Requested implement-spec orchestration with GPT-6.1 Sol high implementer subagents.
