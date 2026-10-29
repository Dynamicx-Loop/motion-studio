# Implementation orchestration

Status: active

The user authorized `ask-matt` → `implement-spec` orchestration on 2026-10-29.
Implementer subagents work on individual branches/worktrees; a merger integrates
resolved tickets on `codex/layout-and-robot-assets`. The main session coordinates.
No remote issues or pull requests are created by this local-tracker workflow.

## Source checkpoint

The integration branch starts from a source-only checkpoint of the dirty canonical
workspace at `/data/workspace/motion_studio`, original branch `experiments/umr-astro`,
HEAD `1bfa7fc4931fec7ebc5f19444515a3125ff5207b`. Original working files and staging
were not changed. The checkpoint is preservation context, not implementation.

644 owned source/small-evidence files (10,692,896 bytes) were copied byte-exactly.
497 generated/media/binary/third-party/local-only entries (1,656,700,060 bytes) were
excluded and retained at their original locations. The ignored selection manifest
is `outputs/implementation/layout-and-robot-assets/seed-manifest.json`, SHA-256
`7c26dc24003aa6a496d290b587755d8da985614f3bf8f2c5f71fe30b965739db`.
It records all selected/excluded paths and hashes plus canonical Git status.

## Local resources and safeguards

Existing external/output children are ignored links to the canonical workspace.
Treat them as READ-ONLY INPUTS: do not build, regenerate, decorate or write through
these links. New output/run names belong to the individual worktree's own output
directory. Never replace the entire output directory with a canonical symlink.
An implementer should pass explicit canonical evidence roots when supported.
Excluded experiment artifacts are available only in the canonical workspace; they
were not copied or silently relocated into the source checkpoint.

`workspace.py` rejects per-checkout links that resolve outside its externals root.
This is an existing safety rule; ticket 03 may provide explicit source-workspace
inspection without changing bootstrap preservation semantics. Setup does not
weaken that rule. Environments, large assets and generated reader entries remain
local prerequisites, not committed distribution assets.

The managed integration checkout is outside the current sandbox writable roots.
Terminal writes/commits there require `require_escalated`; isolated implementer
worktrees may instead use writable `/tmp` paths with their Git metadata operations
escalated. Never reset or switch the canonical checkout.

## Preservation checkpoint validation

The source snapshot retained historical CSV line endings and patch whitespace
byte-exactly. The initial staged whitespace check reports pre-existing findings
in 23 files; full output is in the ignored seed-whitespace receipt.
Do not reformat historical evidence to clear those baseline findings. New
implementation diffs are checked relative to this source checkpoint.

## Integration ledger

As of ticket 05 integration, tickets 01, 02, 03 and 05 are resolved and merged.
Ticket 06 (documentation editions) and ticket 09 (robot resolver) are active.
Tickets 04, 07, 08, 10, 11, 12 and 13 remain pending dependency-frontier dispatch.
The initial source checkpoint above remains unchanged and is the review base.

- 02: `370c106` — explicit test discovery/runtime tiers; pure checks passed.
- 01: `de0d6f5` — sealed canonical inventory and recovery; pure checks passed.
- 03: `bbd6dac` — pinned conversion dependency and preserved historical roles; pure checks passed.
- 05: `7cd852e` — owned legacy evidence operations and motion-path compatibility; pure checks passed.

Root checks run with `PYTHONDONTWRITEBYTECODE=1`; shared evidence links are inputs
only. Stable preservation and dependency-role receipts have per-child ignored
read-only links under this worktree's own outputs directory. No ticket worktree
or ignored receipt has been deleted. Stable ticket 05 evidence is committed under
`experiments/layout-and-robot-assets-evidence/`.

### Resolver integration

Ticket 09 integrated at `55d43a7`: immutable pinned Astro selection, schema and
pose/closure validation. Root pure checks passed (8/8); runtime representation
validation remains explicitly unverified until ticket 11. Tickets 01/02/03/05/09
are integrated. Ticket 06 is finalizing its persisted edition, 07 is active, and
10/11 are unblocked by resolver integration. No canonical source change occurred.

### Documentation edition integration

Ticket 06 integrated at `074e32c` and its frozen durable edition was published
using the SHA-256-verified guarded handoff publisher. Integration root/basic/home
entries are complete static pages and `outputs/docs-site/` remains a real local
directory with one read-only per-edition alias to canonical
`outputs/docs-site/ticket06-20261029-validated`. No research input or frozen
edition was written, and no second 2.5 GB edition copy was made.

Publication verified 3,766 source hashes, 3,604 output hashes, 1,134 local links,
eight preserved legacy originals, 46 documents and zero new experiments.
Direct-file browser rendering remains unverified. The publication receipt is
`outputs/docs-site/ticket06-publication/`; original entries are preserved there
if present. Root pure plus selected JavaScript checks passed (10/10 suites).
Tickets 01/02/03/05/06/09 are integrated. Ticket 07 pilot and 10 G1 guard are active.

### G1 definition and baseline guard integration

Ticket 10 integrated at `5c5d166`: explicit pinned G1 comparison definition plus
regression coverage preserving catalog-independent official baseline preparation.
The URDF/MJCF pair is reported incompatible at unchanged tolerances; shared
runtime consistency validation remains ticket 11. Fresh run-local MJCF compile
evidence is preserved under the durable canonical
`outputs/implementation/layout-and-robot-assets/ticket10/` with a per-directory
read-only alias here; seed receipt storage remains a real directory.
Root pure checks passed 11/11. Tickets 01/02/03/05/06/09/10 are integrated;
07/11 are active and 04 is next available implementation work.

### Artifact pilot integration

Ticket 07 integrated at `ba49d3b`: explicit copy-first preservation operations,
viewer validation and isolated UMR HiPHI preparation. The authorized canonical
pilot installed 173 verified legacy aliases for 258,336,820 bytes, retaining
independent original hashes and read-only archives. Durable archive/prepared-run
receipts have per-directory read-only links here beneath real output parents.
The initial inventory correctly records 173 declared kind changes plus additive
03/06/07 receipts; this is not described as an unchanged whole-inventory pass.
No protected sealed bytes or dependency HEAD/status values drifted.
Root pure checks passed 14/14. Tickets 01/02/03/05/06/07/09/10 are integrated;
08 is unblocked, and 04/11 are active.

### Dex3 and representation consistency integration

Ticket 11 integrated at `48aa3b6`: pinned 43-joint Dex3 poses/closure and immutable
exact-claim representation reports with a separate optional CPU runtime tier.
Durable measured reports/preservation receipt are committed under
`experiments/layout-and-robot-assets-evidence/ticket11/`. Astro named-frame and
scalar metadata claims pass, while aggregate inertia remains incompatible at
the original conservative tolerance. G1 discrepancies and separate collision
policy/equality claims remain explicit. No geometry-equivalence or dynamics claim
was introduced. Root pure checks passed 15/15; the implementer independently
passed the optional four-case runtime fixture suite and read-only real pairs.
Tickets 01/02/03/05/06/07/09/10/11 are integrated. Ticket 12 is unblocked;
04 conversion and 08 storage batches are active, with 13 pending closeout.

### Wendy conversion adapter integration

Ticket 04 integrated at `5f6e3ba`: typed owned conversion operation with pinned
private runtime, exclusive preflight/publication, true source timing and thin CLI.
Implementer CPU excerpt parity matched all 12 historical array fields and
16 report fields; synthetic timing/metre expectations were independently checked.
Durable receipts are preserved under canonical
`outputs/implementation/layout-and-robot-assets/ticket04/` with a per-directory
read-only alias here. Root pure checks passed 16/16; no full conversion/GPU or
source/upstream mutation was performed. Tickets 01/02/03/04/05/06/07/09/10/11
are integrated. Ticket 08 storage ledger and 12 canonical preparation are active;
13 closeout remains gated on those outcomes.

### Remaining artifact batches integration

Ticket 08 integrated at `e0283aa`: the bounded ledger accounts for all 1,019
sealed experiment files across 24 directories plus 21 original output cohorts.
Including the pilot, 493 files / 1,656,674,064 bytes now live in verified ignored
archives behind compatibility aliases; 526 small/source files are retained with
explicit reasons. Original inventory differences remain 493 declared kind changes
plus additive receipts, with no changed sealed bytes or canonical repository
drift. No whole-inventory pass or disk-size reduction is claimed.
Durable ticket08 receipts have a per-directory read-only alias here. Root pure
checks passed 16/16; optional viewers/direct-file limits remain as recorded.
Tickets 01 through 11 are integrated. Ticket 12 canonical preparation remains
active and is the final prerequisite for ticket 13 closeout.

### Canonical comparison preparation integration

Ticket 12 integrated at `b1d37da`: typed explicit canonical preparation with exact
representation-claim guards, stage fingerprints and cache artifact hash checks.
All successful receipts remain prepared-only/execution-readiness false. Final
fresh G1/Astro29/Dex3 CPU preparation/compile evidence is preserved under canonical
`outputs/implementation/layout-and-robot-assets/ticket12-20261029-validated/`
with a per-directory read-only alias here; earlier sets remain separate.
Official G1 baseline behavior and frozen inputs remain unchanged. Root pure
checks passed 17/17. Tickets 01–12 are integrated; ticket 13 closeout is ready
for navigation, full bounded acceptance and fresh documentation publication.
Final standards/spec review against seed `8d7dff5` still gates completion.
