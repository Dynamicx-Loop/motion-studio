# Layout navigation and bounded acceptance — 2026-10-29

This additive closeout records implemented layout/operation boundaries; historical
experiment files and numerical claims retain their original provenance. The parent
implementation remains subject to the coordinating session's final standards/spec
review. The local tracker and execution ledger remain authoritative for that state.

## Current operations and independent inputs

The [workspace layout](../../../README.md#layout) now names owned operations,
concrete adapters, thin CLI/frozen compatibility scripts, tests, experiment schemas,
robot definitions, local tracker, source records and ignored outputs/cache.
[Workflow](../../../docs/workflow.md#implemented-workflow-entry-points),
[dependency roles](../../../docs/dependency-roles.md), [checks](../../../docs/checks.md)
and the [experiment template](../../TEMPLATE.md) describe the concrete contracts.
The original [hhtools migration](../../../docs/migration.md) remains unchanged;
its old metadata, absolute environment paths and compatibility links are retained.

[Official G1 reproduction](../../umr-g1-baseline-20261029/README.md) keeps UMR's
pinned bundled assets and full train/retarget route independently of the robot
catalog. [Canonical preparation](../../../docs/umr-canonical-preparation.md)
requires deliberate definition/representation/pose/source selection. It produces
closed run-local copies, a derived pose XML and stage fingerprints; all receipts
remain prepared-only with execution readiness false. Metadata compatibility does
not establish tensor/runtime/learned semantic compatibility. Geometry, pose, order
or settings changes create a new cohort and can require new sampling, training and
binding. No historical checkpoint fallback is allowed.

[Robot selections](../../../robots/README.md) validate pinned bytes, source closure,
conventions and named scalar/root poses without simulation. Exact report claims
remain separate: Astro named frames/scalar metadata pass but aggregate inertia is
incompatible at unchanged conservative tolerances; G1's pair is incompatible.
Collision-policy acceptance never establishes collision equality or full model
or dynamics equivalence. See [measured reports](../ticket11/README.md) and
[three prior preparation/CPU compile observations](../ticket12/README.md).

## Preservation and storage accounting

The original inventory is unchanged:
`outputs/preservation/layout-and-robot-assets-20261029-01/inventory.json`, SHA-256
`32c9f10f145814668c2b19caf0555e3aa2c7f6ad416252c542be68f357eb30d7`.
[Receipt boundaries](../../../docs/preservation.md) and
[relocation/restoration](../../../docs/artifact-relocation.md) distinguish source
preservation, aliases, ordinary stored bytes and recovery exclusions.

The complete additive ledger at
`experiments/layout-and-robot-assets-evidence/artifact-batches-ledger.json` covers
all 1,019 sealed experiment members in 24 experiment directories and all 21
original output cohorts. Including the pilot, **493 files / 1,656,674,064 bytes**
were copied, independently verified and exposed through old relative aliases to
read-only archives. The **526 retained files / 10,101,981 bytes** have explicit
source/configuration/patch/provenance/small-result reasons and remain eligible for
version control. Already-placed output bulk remains listed separately. Existing
output bulk was 13,503,142,270 logical bytes / 13,496,851,770 unique ordinary-file
bytes at the original seal. No workspace-size reduction or deduplication is claimed;
sequential batch copy duplication peaked at another 1,379,156,370 bytes.

The three archive receipts are retained under `outputs/artifact-archives/`:

| Cohort | Files | Logical bytes | relocation.json SHA-256 |
| --- | ---: | ---: | --- |
| `hiphi-robot-control-20261029-01` | 173 | 258,336,820 | `38c49690bf08f90957688472bac3afcc95cdc81f5720bfb6ce9d4e078c549513` |
| `hiphi-conversion-control-20261029-01` | 133 | 1,379,156,370 | `479e9b57049d9327e5f0ee3d6e282d5bc0a6ec6623eb55b347704e649c1be167` |
| `hiphi-head-objective-20261029-01` | 187 | 19,180,874 | `8e082dbc4aa7cee4ad5d176aa75fc2d267261cb6e9619ab7f614d716f504bfc5` |

Frozen old writers/exporters/analyzers are preserved source, not invoked against
archives or retained reports. Restoration copies verified bytes back to ordinary
original paths and preserves the archive; never delete the only verified copy.
The old inventory verifier intentionally reports 493 declared kind transitions
plus newly created output evidence. This is not an unchanged whole-inventory pass.
The final additive receipt accounts for those exact paths and checks sealed bytes,
canonical Git HEAD/status/patch, external state and compatibility links.
Authorized integration/ticket worktrees and source commits are accounted separately.

## Bounded acceptance and exact prerequisites

Use `PYTHONDONTWRITEBYTECODE=1` for all Python commands. The tooling interpreter was
`/usr/bin/python3` (Python 3.12); no shared environment or dependency install was
created. All five available tiers are selected explicitly below:

```sh
python3 scripts/check.py --json
python3 scripts/check.py --tier saved-evidence --json
python3 scripts/check.py --tier javascript \
  --docs-edition outputs/docs-site/ticket13-20261029-final --json
python3 scripts/check.py --tier umr-static \
  --umr-python /data/workspace/motion_studio/externals/UMR/.venv/bin/python \
  --umr-run /data/workspace/motion_studio/outputs/umr-astro-baseline-v1/static-20261024-01 --json
python3 scripts/check.py --tier robot-static \
  --robot-python /data/workspace/notAnyrobot/menagerie_x/.venv/bin/python --json
```

Pure tests discover 17 suites, including alias/physical-target verification and a
relocated-source CLI handoff regression; manifest/source/output/root-entry hashes
remain enforced. Saved-evidence reconstructs 76 legacy arms / 1,924 rows without a
numerical rerun. UMR static checks use the existing pinned historical checkout/run;
robot runtime fixtures require NumPy/MuJoCo and step no simulation. JavaScript
checks use Node and six DOM-stub search cases; they do not prove browser rendering.
Missing selected prerequisites are failures/unavailable, never silently passed.

Bounded cross-workflow acceptance inspects external pins read-only, exercises help
for conversion, official G1, canonical preparation, relocation, representation
reports and docs build/verify; rechecks the small saved Wendy excerpt (12 array
fields / 16 report fields); reconstructs/verifies a fresh evidence bundle; resolves
all three real pinned MJCF robot selections; and prepares a fresh Astro 29 cohort
using the existing official UMR runtime and explicit clip/shape/model evidence.
The separate prepared-only cohort is retained at
`outputs/implementation/layout-and-robot-assets/ticket13-20261029-validated/canonical-astro29/`.
Exact argv, interpreter, input hashes and observations are in its preparation
receipt and adjacent closeout receipts. This does not execute conversion fitting,
training, retargeting or advance a baseline.

Ticket 08 independently checked 681 resolvable README/config edges, 935 recorded
inbound reader edges, fourteen optional-inspector static resource graphs and a
small restore probe. Its HTTP viewers loaded all 123 conversion and 148 head
binary resources, rendered and advanced playback, with seeking, robot switching
and overlay checks. These are reading observations, not numerical/dynamic parity.
Direct-file WebGL and optional-inspector browser interactions remain unverified.

## Fresh reader edition and durable handoff

Authored templates/catalog and all registered records are finalized before the
fresh edition is built, using the current implementation worktree as source and
`/data/workspace/motion_studio` as read-only evidence:

```sh
python3 scripts/build_docs.py --source-root . \
  --evidence-root /data/workspace/motion_studio --edition ticket13-20261029-final
python3 scripts/verify_docs.py --source-root . \
  --evidence-root /data/workspace/motion_studio --edition ticket13-20261029-final
```

An existing edition (including the default `current`) is refused. The full new
edition is independently sealed/copied once to the same relative path under
canonical `outputs/docs-site/`, then the worktree's verified local edition is
replaced by a read-only per-edition alias. Root/basic/home entries retain ordinary
portable relative links. A guarded handoff verifies the frozen closure, current
source hashes and regenerated entry hashes, preserves prior entry bytes, and rolls
back on publication failure. It never replaces the entire `outputs/docs-site/`
directory. The exact tested publisher, seal and final counts/hashes are recorded
outside the sealed source closure, in the ticket Answer and durable receipts at
`outputs/implementation/layout-and-robot-assets/ticket13-20261029-validated/` and
`outputs/docs-site/ticket13-20261029-handoff/`.

The CLI verifies the executing checkout by default after temporary worktree removal;
the Python API preserves recorded-root semantics unless overridden. Frozen ticket
06 bytes and historical publication evidence remain intact; today's root entries
intentionally select the new edition. Static links/hashes and HTTP reading checks
are distinct from `file://` browser rendering, which remains unverified under the
available browser protocol policy. Optional inspectors retain their local HTTP
requirement. No GPU, physical robot, new solver/framework, upstream edit, automatic
asset download, full retargeting, numerical rerun or licensed-asset redistribution
is part of this closeout.
