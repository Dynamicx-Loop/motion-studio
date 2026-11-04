# Implementation graph

Integration branch: `codex/local-umr-studio`

01 → (02, 03) → 04 → (05, 06) → 07.

Each implementer uses a fresh GPT-6.1 Sol / high context and isolated worktree; a merger integrates each completed ticket. Root retains orchestration and final standards/spec review.

See [spec](spec.md) and one ticket per file under issues/.

## Completion

All seven tickets resolved on `codex/local-umr-studio`, integrated through `b8d363c` before this documentation closeout. Implementers and mergers used GPT-6.1 Sol / high in fresh contexts. Correctness review fixes were applied by a separate fresh implementer and re-reviewed.

- 01 historical app: merge `8c4341a`.
- 02 robot/pose: merge `3e081b5`; import integrity fixes `92ba5b0`.
- 03 motion import: merge `7d5b60f`.
- 04 native stages: merge `d198afe`.
- 05 inspections: merge `524def5`, whitespace follow-up `b5b2364`.
- 06 lifecycle: merge `6ead0d6`.
- 07 acceptance: official-pose merge `8ad6730`, final evidence merge `b8d363c`.
- Final review fixes: `cc4f6d1`; namespace recovery `e4e0eb2`.

[Standards](reviews/standards.md) and [Spec](reviews/spec.md): no remaining findings.
[Acceptance record](../../experiments/studio-baseline-acceptance-20261030/README.md): fresh 500-epoch/5468-frame run on stable final product code, all numerical gates, native cancellation/retry, offline-resource audit, standalone playback, preservation and applicable checks passed. Networking remained enabled during browser resource audits; this is not an air-gap test.

Completed code worktrees are removed after integration; generated evidence remains at original paths. Original viewer, completed historical runs and pinned external states remain unchanged.


## Asset-library follow-up

[Ticket 08](issues/08-asset-library.md) resolved after actual four-model runtime
checks, 29/29 pure suites, independent review, native browser drag/upload/source
playback and a fresh 5-epoch/180-frame all-stage G1 smoke. The
[experiment record](../../outputs/artifact-archives/experiment-reset-20261104/experiments/archive/studio-asset-library-20261030/README.md)
keeps this usability smoke separate from the original full-quality acceptance.
Original preservation passed all 288 files; no external pin/source changes.

## Source mesh preview follow-up

[Ticket 09](issues/09-source-mesh-previews.md) resolved with animated mesh
thumbnails, full source previews and a simplified motion library. All 30 pure
suites, native reconstruction reference, frontend checks, independent review
and browser acceptance passed. Browsing preserved every run/job and the selected
revision; all 288 original protected files and pinned external states passed
preservation checks. Hands remain neutral and facial animation is omitted.

## Inspection layout follow-up

[Ticket 13](issues/13-inspection-properties.md) resolves the user-requested
consolidation into main Properties. A live owned shell reads existing registered
bundles without mutating exports, while session-checked commands and renderer
state keep playback/selection synchronized. Focused bridge/HTTP/export/numerical
checks and actual saved Binding/Motion browser QA passed; 288 protected files
remained unchanged. Standalone controls and historical viewer remain preserved.

## Bundled Astro follow-up

[Ticket 15](issues/15-bundled-astro.md) adds the current default Astro P2 under
root `assets/`, preserving source bytes/notices and an owned collision-attachment
import derivative. Public import/HTTP/pose, browser preview and representation
parity in MuJoCo 3.3.7 and 3.11.0 passed; 41 pure/JavaScript and seven native static
suites passed. [Acceptance](../../outputs/artifact-archives/experiment-reset-20261104/experiments/archive/studio-astro-builtin-20261101/README.md)
records the exact snapshot and limits. No learned stages or historical pins changed.
