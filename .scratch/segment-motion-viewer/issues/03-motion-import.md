# 03 — Import and inspect explicit SMPL-X motion metadata

Status: resolved
Category: enhancement
Spec: ../spec.md
Blocked by: 01

## Context and outcome

Deliver import and inspect explicit smpl-x motion metadata as a complete usable slice of the confirmed local Studio baseline. Read the full spec and interview for contracts and exclusions.

## Acceptance criteria

- [x] Import existing HiPHI and compatible safe single-person NPZ via app into immutable managed storage.
- [x] Validate pose/translation/shape/FPS/gender/up-axis and aliases, matching local model hashes; missing metadata explicit, unsupported layouts/timing rejected.
- [x] UI displays frame count/FPS/shape/model provenance and neutral-hand/omitted-face disclosure, selecting an imported motion for a draft.
- [x] Preserve all source bytes/channels; moving originals does not break imported version. Tests cover baseline headers, malformed arrays/aliases and missing model.

## Implementation and validation

Use the implement-spec orchestration and TDD skill. Test public behavior. Work only in the assigned isolated branch/worktree based on integration; preserve canonical viewer, all existing runs and pinned externals. Record precise tests, evidence and limitations under Answer, then resolve only when criteria are met. No commits of unrelated local experiments or generated large assets.

## Comments

User explicitly approved spec/ticket synthesis and immediate implementation; this breakdown operationalizes that accepted scope.


## Answer

Implemented the owned safe motion import/inspection slice in `_motion.py`, the
Studio operations, loopback endpoints and motion asset UI. Original bytes and all
channels are retained separately from a hash-checked generated native NPZ; the
upstream permissive loader never receives the unvalidated original. Every NPY
header/payload is bounded and validated with pickle disabled. Full/body and split
axis-angle layouts, numeric translation, ten constant betas, scalar metadata and
baseline aliases/timing are checked. Missing metadata is entered explicitly;
missing matching weights fail clearly. Model provenance records the external
path and SHA-256 without copying or loading licensed weights. Saved metadata
remains readable after weight removal; native input access/selection is blocked.

Motion selection creates a fresh revision, an immutable `motion.json` record and
append-only selection history, preserving robot selections across revisions.
Original relocation, duplicate imports, new-content versions, asset tampering,
missing metadata/weights, malformed arrays, conflicting aliases, custom timing,
and an executable pickle payload are exercised through public outcomes.

Validation:

- TDD red/green traces: first import/selection failed before the constructor and
  operations existed; HTTP import failed 404 before routes existed; baseline
  alias/frame_time and boolean-FPS/declared-unit cases failed before guards.
- `python3 -B -m unittest discover -s tests -p test_studio_motion.py -v`: 9 pass.
- `python3 -B -m unittest discover -s tests -p 'test_studio*.py' -v`: 18 pass.
- `python3 -B scripts/check.py --tier pure`: 21/21 suites passed (NumPy available).
  Motion tests explicitly skip when NumPy is absent; import then reports the
  missing runtime, while startup and saved viewing remain independent of NumPy.
- `node --check motion_studio/studio/web/{app,motion}.js` and `git diff --check` pass.
- Real Chromium form smoke at loopback port 8776: created a draft, imported the
  pinned canonical HiPHI NPZ, displayed 5468 frames at 90.00090026855469 FPS,
  Y-up, all ten shape values, source/model hashes and reconstruction disclosure;
  selection persisted as revision r0002 after refresh. Resource audit found no
  requests outside the loopback origin. Source bytes compared identical and the
  generated safe NPZ retained `(5468,165)` poses and `(5468,3)` translations.
- Actual HiPHI source SHA-256:
  `3a3d20c4ebd1727536136888efdde62f7ea685eb6ea0c88f1160116009416808`;
  actual installed neutral model SHA-256:
  `381c808965deb4f5e845f8c3eddb0cd69930cc72e5774ce4f34c4ce3cf058361`.
  Ignored local smoke state/screenshot/snapshot:
  `/data/workspace/motion_studio/outputs/studio-worktrees/03/outputs/ticket03-browser-state`,
  `ticket03-browser.png` and `ticket03-browser.txt` beside it.

No native reconstruction, GPU computation or quality claim belongs to this
slice. External source, original viewer and existing runs were read-only.
