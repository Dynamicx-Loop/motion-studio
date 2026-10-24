# Motion Studio

A workspace for studying, using, and developing motion retargeting and editing tools.

Motion Studio starts as a curated collection of open-source projects, including UMR
human-humanoid-tools (hhtools), and ProtoMotions with PyRoki. Daily use, reproducible
comparisons, and custom
experiments will guide its evolution into an integrated motion processing workflow.
The scope includes human, character, and robot motion, motion editing, contact and
interaction preservation, visualization, and export.

## Current stage

The upstream tools run independently. There is no shared runtime or unified editor yet.
Keep each project's dependencies and setup separate; add shared abstractions only
when real workflows demonstrate a need.

| Project | Local checkout | Role |
| --- | --- | --- |
| UMR | [externals/UMR](externals/UMR/README.md) | Learned surface correspondence and motion retargeting |
| hhtools | [externals/human-humanoid-tools](externals/human-humanoid-tools/README.md) | Import, calibration, retargeting, visualization, and export |
| ProtoMotions | [externals/ProtoMotions](externals/ProtoMotions/README.md) | PyRoki retargeting workflows and motion processing |
| PyRoki | [externals/pyroki](externals/pyroki/README.md) | Kinematic optimization library used by ProtoMotions |

## Getting started

From the Motion Studio root:

```sh
python3 scripts/workspace.py list
python3 scripts/workspace.py check
```

On a fresh checkout, run `python3 scripts/workspace.py bootstrap` to clone missing
external repositories at the revisions in `externals/manifest.json`. Existing
checkouts are never reset or updated. Then follow each project's linked README
from its own directory to install dependencies and run it.

The migrated hhtools checkout includes local Astro robot changes, its existing
environment, local assets, and Git history. Those local changes are not reproduced
by cloning its recorded commit. See [migration notes](docs/migration.md).

See the [ProtoMotions/PyRoki setup and solver comparison](docs/protomotions-pyroki.md)
and [official UMR implementation investigation](docs/umr-solver-investigation.md).
ProtoMotions is included as source; large Git LFS assets are fetched on demand.

## Local documentation

Double-click [docs.html](docs.html) in this project root to read the offline
HTML documentation. Navigation, search and saved figures are prebundled; no
server or localhost URL is required for reading. See the
[documentation guide](docs/offline-documentation.md) for rebuilding, portability,
the direct-file verification limit and separately optional 3D tools.
Legacy evidence and the prospective static baseline remain labeled separately.
Generated HTML and evidence bundles stay local; after editing documentation sources,
run `python3 scripts/build_docs.py` and `python3 scripts/verify_docs.py`.
A fresh clone also needs the preserved local report/evidence artifacts described
in the guide.

## Layout

```text
externals/       Independent upstream Git checkouts and their manifest
references/      Zotero-derived bibliography and reading index
docs/            Scope, workflow, roadmap, and migration notes
configs/         Shared configuration examples as integrations emerge
experiments/     Reproducible experiment notes and comparison records
scripts/         Workspace management utilities
data/            Local input data (contents ignored)
outputs/         Generated results (contents ignored)
```

Start with the [workflow and roadmap](docs/workflow.md), the
[reference library](references/README.md), or the
[experiment template](experiments/TEMPLATE.md).

## Contributing and attribution

Record source revisions, commands, data provenance, coordinate conventions, and
results for experiments. Keep upstream-specific changes in the corresponding
external repository; put cross-project orchestration and documentation here.

External repositories retain their own licenses and notices. Dataset, model-weight,
and robot-asset terms apply separately. No umbrella license is chosen for new
Motion Studio code yet. Cite the methods and datasets used in each result.
