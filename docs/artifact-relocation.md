# Local artifact preservation and relocation

Generated experiment bytes live in fresh ignored `outputs/artifact-archives/`
cohorts. Source, configurations, provenance, patches and small reviewed results
remain eligible for version control in their experiment directory. Select members
by reviewed role; a JSON extension does not distinguish a reviewed result from a
large generated viewer payload. Existing licenses and notices still apply. This
local operation establishes no permission to redistribute assets.

The public operations in `motion_studio.artifacts` are `plan_relocation`,
`relocate`, `verify_relocation` and `restore`. They take an explicit data workspace,
separate from the checkout running the code. They require the independent original
inventory SHA-256, explicit selected paths and a fresh archive below `outputs/`.
Plans include each original and destination path, original size/hash/mode, role,
inbound references, exact relative alias and compatibility action. Review the
referenced model/mesh closure separately; retain external source assets in place.

For a fresh cohort, create a reviewed JSON selection containing a `files` list of
objects with `path` and `role`. Run the dry plan first:

```sh
python3 scripts/relocate_artifacts.py plan \
  --workspace /data/workspace/motion_studio \
  --inventory /data/workspace/motion_studio/outputs/preservation/layout-and-robot-assets-20261029-01/inventory.json \
  --inventory-sha256 32c9f10f145814668c2b19caf0555e3aa2c7f6ad416252c542be68f357eb30d7 \
  --selection /path/to/reviewed-selection.json \
  --destination outputs/artifact-archives/FRESH-COHORT > /path/to/reviewed-plan.json
```

`apply /path/to/reviewed-plan.json --step-limit N` copies at most N members before
returning. With N equal to the selection count, every copy exists and originals
remain ordinary files. Independently hash both locations against the original
inventory and check the whole resource graph at both roots before aliasing.
`apply ... --resume` verifies existing copies and resumes individual atomic alias
replacements. A failure retains readable originals or independently verified
copies. A resumed plan must match its receipt; collisions, drift, unknown aliases,
unsafe paths and stale/incomplete receipts are refused. Never remove an original
or partial archive to bypass a refusal. Inspect a staging-file conflict explicitly.
The operation assumes no concurrent writer to the selected files during migration.

`verify /absolute/archive/relocation.json` checks both names and archive write bits.
`restore /absolute/archive/relocation.json` copies verified archive bytes back to
ordinary original files, restores recorded file modes and retains every archive
copy. Restoration never deletes the only verified evidence copy. Tiny-fixture tests
exercise restoration, source/archive drift, conflicts, partial-copy and partial-
alias resume, relative links, nested paths and write refusal under the normal user.

## HiPHI robot-control pilot

The tracked [plan](../experiments/layout-and-robot-assets-evidence/artifact-pilot-plan.json)
and additive [context](../experiments/layout-and-robot-assets-evidence/artifact-pilot-context.json)
are the explicit migration map and retained input/model closure. On 2026-10-29,
173 selected generated files (258,336,820 logical bytes) were copied, independently
verified against the original seal, then replaced by recorded relative aliases.
The archive is:

```text
/data/workspace/motion_studio/outputs/artifact-archives/hiphi-robot-control-20261029-01/
```

`relocation.json` records the immutable plan and operation state.
`independent-before-alias.json`, `independent-after-alias.json`,
`viewer-graph-final.json`, `browser-smoke.json` and `preservation-summary.json`
record checks. No raw assets, media or checkpoints are committed. Thirteen original
source/config/provenance/result files remain byte-identical, including README and
small `report.json`. Four trajectory-embedded external XML paths and their mesh
closures were checked against the sealed viewer's model hashes and inventory;
those paths and NPZ strings remain unchanged.

The two checkpoints, correspondence/trajectory/slot arrays, conversion, six logs
and generated viewer closure were selected explicitly. Before copying, these
members had 173 distinct ordinary-file inodes totaling 258,336,820 bytes. After
aliasing, archive copies hold those bytes and old names resolve to them; aliases
preserve logical readability and do not reduce total workspace bytes. Temporary
copy duplication peaked at another 258,336,820 bytes. Fresh preparation below adds
its own deliberately run-local asset copies; it is not a reusable asset cache.

The static graph resolves 148 binary resources and four HTML/JS/vendor files,
including 35 Astro and 37 G1 parts and four transform arrays with exact frame/part
sizes. The old HTTP viewer loaded all 148 binaries, rendered a canvas and advanced
Astro playback. Pause, G1 selection/seeking, return to Astro and overlay responded
with empty app error text. A missing favicon produced one 404. Direct-file WebGL
playback was not established; no numerical or dynamic claim follows from this
reader check.

The original preservation verifier still reports additions and the 173 declared
file-to-symlink changes. Its saved check found **no changed sealed bytes or
repository-state diagnostics**. Additional dependency-role/documentation outputs
created by the concurrent integration are listed separately in the full local
receipt. The original inventory and seal were not rewritten to hide these changes.

## Frozen writers and a fresh preparation route

The old `experiments/hiphi-robot-control/run.py` truncates `astro-reference.log`
before launching its first pipeline. The old `scripts/export_hiphi_robot_control.py`
writes its first mesh binary before rewriting the small report. Those archived
log/mesh targets have no write bits, so an ordinary user's accidental first write
fails. This protection was tested on a disposable fixture; neither historical tool
was executed. File modes do not prevent an owner from deliberately changing them.
`summarize.py` can rewrite README independently; preserve it as historical source
and do not execute it against this frozen cohort.

`motion_studio.integrations.umr_hiphi_control.prepare_legacy_run` is the concrete
adapter for fresh preparation. The CLI prepares four configs and 74 verified
model/mesh files from the sealed original source inputs, records every source hash,
configuration hash, new identity, exact argv/cwd and fresh log paths, and executes
nothing:

```sh
python3 scripts/relocate_artifacts.py prepare-legacy \
  --workspace /data/workspace/motion_studio \
  --inventory /data/workspace/motion_studio/outputs/preservation/layout-and-robot-assets-20261029-01/inventory.json \
  --inventory-sha256 32c9f10f145814668c2b19caf0555e3aa2c7f6ad416252c542be68f357eb30d7 \
  --destination outputs/artifact-runs/FRESH-RUN \
  --python /data/workspace/motion_studio/externals/UMR/.venv/bin/python
```

The concrete prepared-only example is
`outputs/artifact-runs/hiphi-robot-control-prepared-20261029-01/preparation.json`;
its additive `preparation-source-context.json` anchors the original pipeline and
historical tool/template source hashes. `fresh-viewer-context.json` records the
copied viewer source templates and reserved fresh geometry destination; no
geometry or viewer manifest was generated. Each robot's reference/reconverted pair
shares new run-local correspondence/training paths; robots have separate paths.
Retargets, logs and model XMLs are fresh and run-local. Source motions remain read
inputs. Generated XML therefore cannot be written beside the external source XML.
Old correspondence/checkpoints are not reused. Missing or changed source/model
closure fails before fresh run creation. The copied model identity is the sealed
input closure; this preparation does not claim a historical numerical rerun.

For execution, use the four receipt argv/cwd entries individually, redirecting each
stdout/stderr to its recorded fresh log; runtime and human-model prerequisites need
separate validation. Do not invoke the old hard-coded runner, exporter or
summarizer. A future viewer export must accept the fresh destination explicitly;
the preserved viewer source templates are copied into the fresh run. No training, conversion,
export, GPU job, installation or upstream source write occurred in this pilot.

## Remaining sealed batches and complete ledger

Ticket 08 reused the pilot operation on two further complete resource closures,
copying and independently checking each before installing that batch's aliases:

| Archive below `outputs/artifact-archives/` | Files | Logical bytes |
| --- | ---: | ---: |
| `hiphi-conversion-control-20261029-01` | 133 | 1,379,156,370 |
| `hiphi-head-objective-20261029-01` | 187 | 19,180,874 |

The additive [directory/member ledger](../experiments/layout-and-robot-assets-evidence/artifact-batches-ledger.json)
covers **all 1,019 experiment members in the independent original inventory**,
all 24 experiment directories, the experiment template, and all 21 existing
output cohorts. The earlier planning filesystem measurement included entries
outside this seal; migration scope uses the sealed paths exclusively. Together
with the pilot, 493 generated members / 1,656,674,064 bytes are archived with
legacy aliases. The remaining 526 sealed experiment members / 10,101,981 bytes
are source, configuration, exact patches, provenance and small reviewed results;
all remain version-control eligible. Existing output cohorts already hold their
bulk in ignored storage and remain in place. No ignore rules were broadened.

The [conversion plan](../experiments/layout-and-robot-assets-evidence/artifact-batch-hiphi-conversion-control-plan.json)
and [head-objective plan](../experiments/layout-and-robot-assets-evidence/artifact-batch-hiphi-head-objective-plan.json)
record every selected old/new path, original hash, role, inbound references,
mode and relative alias. Selection includes generated runtime manifests, copied
viewer/vendor resources and review figures; the original inventory's coarse
extension-based roles are preserved separately in the ledger. A runtime JSON
manifest is not a small reviewed result. Original reports and configurations
were neither moved nor regenerated.

Durable local independent checks, exact audit scripts, mode records, restore probe,
and preservation receipts live at:

```text
/data/workspace/motion_studio/outputs/implementation/layout-and-robot-assets/ticket08/
```

[Validation anchors](../experiments/layout-and-robot-assets-evidence/artifact-batches-validation.json)
record their hashes and limits. `relocation.json` remains in each archive.
Archive files and the archive's `files/` directory tree have no write bits; the
original file modes and prior archive-directory modes remain in receipts. The
receipt directory is separate from the immutable payload tree. To restore a
cohort, use the documented public `restore` operation against its unchanged
receipt; it restores original file modes and retains the archive. Ticket 08 also
restored an exact archived 3,538-byte `export.log` in an isolated probe workspace,
confirming both ordinary restored bytes and the retained verified archive copy.
Canonical aliases were not replaced for that probe.

Each new cohort's unique ordinary-file payload equals its logical selected
bytes, both before and after relocation. Reading the old lexical names still
counts those same bytes logically. Copy duplication peaked at 1,379,156,370
additional bytes because the batches were sequential. There is no claim of
workspace-size reduction or deduplication; the existing multi-gigabyte outputs,
external assets, environments and new reading edition remain intentionally stored.
The 21 already-placed sealed output cohorts retain 13,503,142,270 logical bytes
and 13,496,851,770 unique ordinary-file bytes at the original seal.
The ledger reports the original output-cohort logical and unique storage totals
separately, without counting aliases as independent copies.

Validation checked all selected hashes through both names, all three relocation
receipts including the pilot, 681 resolvable README/configuration path edges,
935 recorded inbound-reader edges, and 14 optional-inspector resource graphs in
the frozen research bundle and separate reading edition. The reading edition
also passed its 3,766 source hashes, 3,604 output hashes and 1,134 local links
through its recorded original lexical locator. The verifier is location-sensitive:
passing the canonical target directory directly changes its computed prefix and
fails an existing root-navigation assertion; no edition or original entry was
rewritten to work around that limitation.

The conversion viewer's dynamic filename rule resolves 61 chunks per actor,
including each final 68-frame chunk, with exact float32 byte counts. All 123
binary resources loaded in HTTP browser checks; both actors rendered, playback
advanced, 10 s / 20 s / final-frame seeks and overlay worked. The head viewer
loaded all 148 binaries, rendered, switched to G1 and its final frame, returned
to Astro, played and toggled overlay. App error text stayed empty; one conversion favicon request returned 404. Direct-file
WebGL and optional-inspector browser interaction were not exercised. Static
resource readability and HTTP playback make no numerical or dynamic claim.

Fourteen unchanged head-ablation trajectory NPZs retain fourteen absolute generated
XML paths. Some lexical XML names were outside the original path inventory; every
current XML and mesh nevertheless matches bytes independently sealed at an existing
path. The separate embedded-model receipt identifies these content anchors without
silently adding paths to the old inventory. All external models and meshes remain
at their existing locations. No asset regeneration, baseline update or upstream
write occurred.

Keep the historical writers frozen. The conversion exporter first writes
`viewer/0-000.bin`; the head runner first truncates `astro-baseline.log`, the head
exporter first copies `viewer/astro-0-v.bin`, and plotting writes
`head-ablation.png`. Normal-user write-open checks on those archived targets were
refused without writing bytes. The conversion validator can independently replace
retained `report.json`, and the head analyzer can replace retained report/crosscheck
JSON. Read-only generated targets do not protect those separate small-evidence
writers. Do not run the old validator, runner, exporter, analyzer or summarizer
against frozen cohorts. Future work needs a fresh explicit output route; this
migration runs none of those tools.

The original preservation verifier still deliberately reports 493 declared
file-to-alias kind changes and additive output receipts. It found zero changed
sealed bytes and zero canonical repository HEAD/status/patch drift. Worktree paths,
branches and compatibility links survived; concurrent owned integration/ticket11
HEAD advances are recorded independently. This is not an unchanged whole-inventory
pass, and the original inventory/seal were not edited.
