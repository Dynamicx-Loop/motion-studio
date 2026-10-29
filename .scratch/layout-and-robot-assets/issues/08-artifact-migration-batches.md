# 08 — Apply storage policy to the remaining inventoried artifacts

Status: resolved
Category: enhancement
Spec: [Layout and robot assets](../spec.md)
Blocked by: 07
Dependencies: [07 relocation pilot](07-artifact-migration-pilot.md)

## Context

The inspected experiment tree is about 1.55 GiB, spread across many historical
cohorts. A successful single pilot does not finish the layout cleanup. Viewer
geometry, checkpoints and generated models need the same preservation guarantees
as the pilot, including cohorts referred to by the offline research bundle.

## Outcome and scope

Apply the verified relocation operation to the remaining artifacts classified by
ticket 01. Execute one complete cohort/resource closure per batch, maintaining a
batch ledger. Process only the sealed inventory; newly discovered or changed
local work is reported for review rather than absorbed into a stale move plan.

## Acceptance criteria

- Ledger lists every inventoried experiment directory and each generated cohort
  as migrated, retained-with-reason or already correctly placed. No silent gaps.
  Source/config/patch/provenance/small-result files remain version-control eligible.
- Copy/verify/compatibility checks pass per batch before considering the next;
  historical hashes and records are unchanged, with additive relocation maps.
  Large JSON geometry is classified by purpose, not treated as small text evidence.
- Frozen baseline assets, raw outputs, experiment scripts and legacy absolute/
  relative references remain readable. Do not regenerate geometry or reinterpret
  past results with the latest robot definition.
- All moved bytes live in ignored run/archive storage; old links resolve to the
  same bytes. Keep originals where compatibility cannot be proved and document
  a concrete remaining constraint. Existing aliases/worktree metadata survive.
- Compare unique stored bytes separately from logical file sizes so symlinks or
  temporary duplicate copies do not produce misleading cleanup claims. Report
  remaining bulk and reasons. No broad ignore/deletion hides unresolved work.

## Validation

Run full relocation verification against the original inventory and sample hash
checks independent of the migrator. Traverse local paths in experiment README,
config, viewer and documentation resource graphs, including optional inspectors.
Exercise restore for one small archived member without modifying the only copy.
Recheck frozen run manifests and all repository status/worktree/link inventories.
No GPU or numerical rerun is required; report viewer checks not exercised.

## Comments

Planning only. This ticket completes the bounded inventory, not an open-ended
cleanup of all future outputs or unrelated user files.

Claimed by ticket08 implementer on `codex/layout-assets-08` from `1935afa`.

## Answer

Applied the existing verified relocation operation in two sequential complete
resource batches: **133 files / 1,379,156,370 bytes** for HiPHI conversion-control,
then **187 files / 19,180,874 bytes** for head-objective. Both canonical archives
are under `outputs/artifact-archives/<cohort>-20261029-01/`. Each batch stopped
with ordinary originals intact after copying; independent checks compared all
old/new hashes to ticket 01's original seal before aliases were installed. Both
names still return the sealed bytes, and archive payload files/parent directories
have no write bits. Original modes, directory-mode records, operation receipts and
restore procedure are retained. No source, report, baseline or upstream rewrite.

The [complete ledger](../../../experiments/layout-and-robot-assets-evidence/artifact-batches-ledger.json)
accounts for all **1,019 sealed experiment members**, all **24 experiment
directories**, the authored experiment template, and all **21 original output
cohorts**. Including ticket 07, **493 files / 1,656,674,064 bytes** are migrated.
The remaining **526 files / 10,101,981 bytes** retain precise source/configuration,
patch/provenance/small-result reasons and remain version-control eligible.
Already-placed output bulk is listed separately with original logical and unique
storage totals. JSON viewer payloads and copied viewer source/vendor resources
are classified by runtime purpose; original coarse inventory roles remain visible.
There are no unclassified sealed experiment members or new broad ignore rules.

Tracked additive maps and evidence:

- [Conversion plan](../../../experiments/layout-and-robot-assets-evidence/artifact-batch-hiphi-conversion-control-plan.json)
  and [head plan](../../../experiments/layout-and-robot-assets-evidence/artifact-batch-hiphi-head-objective-plan.json):
  old/new paths, hashes, roles, modes, inbound references and exact relative aliases.
- [Validation anchors](../../../experiments/layout-and-robot-assets-evidence/artifact-batches-validation.json):
  durable canonical receipts and their SHA-256 values, storage accounting,
  graph/browser results and explicit limits.
- [Operator guide](../../../docs/artifact-relocation.md): writer hazards,
  restoration, retained bulk and ledger interpretation.

Durable local scripts and independent before/after/mode/restore/preservation
receipts live under
`/data/workspace/motion_studio/outputs/implementation/layout-and-robot-assets/ticket08/`.
No receipt depends on a disposable cleanup location. Canonical legacy readers
continue using their existing paths; the small restore probe materialized an exact
archived 3,538-byte export log in isolated output storage, restored it to an
ordinary file through the public operation, and retained the verified archive.

Validation passed: all three relocation receipts (including pilot), independent
checks of every selected byte/path, five separate `sha256sum` samples, 681
resolvable README/config path edges, 935 recorded inbound reader edges, and 14
optional-inspector resource graphs spanning the frozen research bundle and new
reading edition. The reading edition passed 3,766 source hashes, 3,604 output
hashes and 1,134 local links through its recorded lexical locator. A direct
canonical-target invocation reaches an existing location-sensitive prefix
assertion; the preserved alias invocation succeeds without rewriting the edition.
Fourteen head NPZs retain fourteen absolute XML names. Some lexical names were
outside the original inventory, but every model/mesh matches independently sealed
content; this is recorded without pretending those paths were originally sealed.

HTTP browser checks loaded all 123 conversion bins and all 148 head-viewer bins,
rendered canvases, advanced playback, sought conversion 10 s/20 s/final frame and
G1 final frame, switched robots and toggled overlay with empty app error text.
Direct-file WebGL and optional-inspector browser interactions were not exercised.
No numerical/dynamic claim follows. No training, conversion/export, old writer,
GPU run, installation or upstream write occurred. Five normal-user permission-only
write-open checks were refused; standalone old validators/analyzers can still
rewrite retained small reports and remain explicitly frozen/unexecuted.

Full original preservation verification reports **493 declared file-kind changes**
and additive output receipts only: zero changed sealed bytes and zero canonical
repository HEAD/status/patch drift. Existing worktree paths/branches/compatibility
links survived; concurrent owned integration/ticket11 HEAD advances are recorded
separately. The original inventory and seal are unchanged; no whole-inventory
pass is claimed. Unique ordinary payload bytes stay equal to selected logical
bytes; old aliases expose those bytes logically. Sequential copy duplication
peaked at another 1,379,156,370 bytes. No workspace-size reduction is claimed.

Root `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check.py` passed all 14 pure suites
before integration refresh; `git diff --check` passed. No production behavior was
added, so existing relocation success/failure/resume/restore suites were reused.
