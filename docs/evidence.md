# Saved evidence and plan preparation

The owned operations live in `motion_studio.evidence`. They use the tooling Python
and import no upstream runtime, simulator or report builder. Validation needs
`jsonschema` in that Python; nothing is installed automatically.

```python
from pathlib import Path
from motion_studio.evidence import reconstruct, verify_bundle

saved_inputs = Path('/data/workspace/motion_studio')
fresh_bundle = Path('outputs/legacy-evidence/<fresh-id>')
summary = reconstruct(saved_inputs, fresh_bundle)
verification = verify_bundle(fresh_bundle, saved_inputs)
assert verification['passed'], verification['errors']
```

`reconstruct(root, destination)` reads the fixed historical cohort records under
an explicit saved-input workspace. The root is independent of the executing code
checkout. A missing, invalid or changed input fails; an existing destination is
refused. The returned v1 summary and per-arm records retain legacy IDs, conditions,
metric units and definitions, matched controls, missing measurements and caveats.
The operation does not rerun any numerical stage or advance a baseline.

Bundles contain `results.jsonl`, `inventory.json`, `summary.json`, `README.md`,
`implementation.json` and `manifest.json`. The new implementation receipt names
the ownership migration and hashes the executing package, motion-path resolver
and schemas. The manifest seals these outputs plus original saved sources and the
executing implementation. When code and inputs are in different checkouts, code
source paths are absolute so verification checks the code that actually ran.
Keep that checkout available, or preserve its exact source closure with the bundle;
a bundle is not a portable copy of every source or a write-once archive.
Historical manifests and saved records remain untouched.

`verify_bundle(directory, root)` returns `passed`, `errors`, `source_files` and
`output_files`. It reports missing/changed sources and outputs, escaping output
paths and added unsealed files. It does not rerun recorded metrics or verify raw
binary/model hashes merely mentioned inside historical records. The existing
[workspace preservation receipt](preservation.md) provides the wider frozen-file
inventory; these operations do not replace it.

`inspect_plan(plan, root)` accepts a v1 plan dictionary and reports file readiness,
observed source hashes and deferred runtime checks. It does not mutate the plan.
`reserve(plan_path, root, output_root)` reads and validates a strict JSON plan,
rechecks its pinned sources and exclusively creates a unique preparation bundle.
Its receipt always says `state: prepared_only`, `stages_executed: []` and
`execution_ready: false`: no launcher is implemented. File readiness is not runtime
readiness. Missing files, hash drift, invalid contracts and unsafe stage output
paths prevent reservation before output creation.

The public `validate(document, kind)` operation checks v1 `plan`/`result` contracts,
including retrospective-claim and matched-control invariants. The pure
`normalize_segment(row, common)` and `validate_static_result(document, common)`
rules retain native19/common18 source denominators, the 4,096-slot total and the
historical 1e-12 precision tolerance. Missing coverage stays null. Invalid static
counts/precision now raise explicit `ValueError` even with Python optimization.

Historical imports from `experiment_support.*` and `motion_data_paths` under
`scripts/` remain compatibility wrappers. The unchanged recorded-path behavior
is owned by `motion_studio.motion_data_paths`; callers may adopt that path without
changing data conventions. The historical report builder and static evaluation
caller import the pure owned rules; they retain their reproduction roles and
original numerical behavior. New runs record the owned rule source hash.

Run `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check.py` for small fixture checks,
and add `--tier saved-evidence` for the full saved legacy records. The saved suite
retains its tier metadata and historical standalone command:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=scripts python3 -m unittest experiment_support.test_legacy -v
```

See the [ticket 05 validation record](../experiments/layout-and-robot-assets-evidence/validation.json)
for the canonical before/after comparison. Report building, static evaluation in
the UMR runtime, numerical execution and GPU work were not exercised by this
ownership extraction.
