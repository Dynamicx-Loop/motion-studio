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
