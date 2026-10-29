# Final integration review and corrections

Reviewed frozen range `8d7dff5374d2d19caa7e5482147549c3f742f0cd...2eb4a78e2fb576b6a906fc65600b433b0502a592`.
Fix branch `codex/layout-assets-review-fixes` descends from that exact tip, isolated
at `/tmp/motion-studio-layout-review-fixes`. Parent spec remains claimed until
coordinating acceptance; all 13 ticket statuses/history are retained.

## Standards axis

Original review: zero documented-standard violations and zero actionable heuristic
smells. Separate correctness P3: historical banner and action link rendered
literal `self.legacy`. Both now render LEGACY. Public build output regression
first failed then passed, covering both banner and sticky action region.

## Spec axis

Original review: two P2 findings, no other missing requirements/scope creep.

1. Same-name/AABB cube and octahedron meshes falsely supported collision policy
   and equality. Runtime now declares all mesh geometry checks unverified; exact
   hash-bound known collision exceptions can support policy only. Primitive
   checks retain measured behavior. Real temporary MuJoCo fixture, required-claim
   guard and canonical preparation regression failed before and pass after.
   Report version 2 centralizes corrected semantics: old reports expose no
   supported claims and cannot satisfy canonical guards. Separate old-report
   public tests reproduced unsafe acceptance before the fix.
2. Wendy output under an unrelated linked external target could write failure
   artifacts. Preflight protects lexical externals plus resolved child checkouts
   and discoverable common-workspace external roots before any writes. Public
   temporary alias and absent-worktree-link fixtures verify rejection with an
   empty external target. No live external write reproduction was attempted.

[Superseding real reports](../../experiments/layout-and-robot-assets-evidence/review-fixes/README.md)
retain original source/pose/policy hashes and conservative tolerances. Mesh visual
checks are unverified; Astro explicit collision policy passes without equality;
G1 mesh collision checks are unverified. Prior ticket11 reports remain historical.
No asset/source edits, solver changes, installs, GPU, training or retargeting.

## Validation and publication

Exact durable receipts and hashes follow after execution. Pure, saved-evidence,
robot-static, UMR-static and selected-edition JavaScript tiers are exercised.
UMR initially lacked the local ignored historical-checkout link; adding the
read-only canonical link in this disposable worktree made preflight available.
Runtime checks use menagerie Python and canonical UMR Python, with the unchanged
`static-20261024-01` saved run. No numerical baseline rerun is claimed.

All five tiers passed: 17 pure suites and one each saved-evidence, robot-static,
UMR-static and JavaScript. Focused Wendy/docs tests pass 18 tests; consistency
runtime fixtures pass five tests, including real different-mesh refusal. Public
pure consistency/canonical tests pass 17 tests after comparison version change.
Fresh Astro preparation/CPU compile verifies 112 hashes, nq/nv 36/35, pose at
1e-12, zero integration steps and execution_readiness=false. Node uses the fresh
edition. Static documentation validation checks 62 documents and all local links
without missing fragments. Markdown path audit and source/seed whitespace checks
pass; no package-to-script implementation imports were introduced. Changed modules
remain cohesive and below the project's source-size guidance.

Durable receipts: `/data/workspace/motion_studio/outputs/implementation/layout-and-robot-assets/review-fixes-20261029`.
[Tracked validation](../../experiments/layout-and-robot-assets-evidence/review-fixes/validation.json)
records exact check receipt hashes, frozen edition anchors and source accounting.
Original inventory verification remains intentionally false for the 493 declared
alias kind changes and additive output paths, with zero other source/Git/status
or compatibility diagnostics. The latest receipt enumerates additions including
new review edition, handoff and prepared/validation artifacts. It does not claim
workspace-size reduction or edit/reseal the original inventory. Frozen 06/13
closures independently verify 3,612/3,648 regular files. Review worktree/branch
registration is authorized added Git infrastructure; original canonical source,
external revisions/status, archived evidence and compatibility paths are retained.

The fresh edition is 3,652 regular files / 2,600,601,927 file bytes, independently
sealed and copied once; only its per-edition alias is installed locally. The
same publisher passed success, conflicting alias, frozen drift and forced
post-publication rollback fixtures. Keep current main entries until this branch
is merged, then run the exact handoff below from the integration checkout:

```sh
python3 -B /data/workspace/motion_studio/outputs/docs-site/review-20261029-handoff/guarded-handoff.py \
  --root /home/android/.codex/worktrees/layout-robot-assets/motion_studio \
  --frozen /data/workspace/motion_studio/outputs/docs-site/review-20261029-final \
  --seal /data/workspace/motion_studio/outputs/docs-site/review-20261029-handoff/frozen-closure.json \
  --receipt /home/android/.codex/worktrees/layout-robot-assets/motion_studio/outputs/docs-site/review-publication
python3 -B scripts/verify_docs.py --edition review-20261029-final
```

Publisher SHA-256: `847c3fb2c9e6883da957d1036c85efae5c4a91303267617e617b7adaeccc0ae3`.
Seal SHA-256: `5aafee659085fef809df9bc1d79110f9ba4d2b00939bae70fe817beef4f51427`.
Manifest SHA-256: `8003aa15b3d51206d5cc5c0c94f478f31af78a454315eff040a732897a5767d2`.
The fresh receipt preserves previous entry bytes/hashes under originals/. Failed
publication restores entries and removes only a newly added alias. Deliberate
rollback restores these originals to their recorded paths while retaining both
frozen editions and all receipts. No integration publication was performed here.

Remaining limits: no new browser/optional-inspector/file/WebGL interaction;
previous protocol restriction remains. No GPU, installation, full conversion,
training, retargeting or dynamic-feasibility checks. Mesh geometry is unsupported.
Prior prepared receipts use earlier adapter code and require regeneration; this
is explicit cache invalidation, not a numerical-regression claim.
