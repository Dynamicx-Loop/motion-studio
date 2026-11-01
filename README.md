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

Motion Studio owns feature development and the interfaces used to call external
tools. External repositories stay pinned and minimally modified; concrete adapters
in this project handle their functions, formats, and runtimes. See the
[development policy](docs/workflow.md#development-policy).

| Project | Local checkout | Role |
| --- | --- | --- |
| UMR | [externals/UMR](externals/UMR/README.md) | Learned surface correspondence and motion retargeting |
| hiphi2smplx | [externals/hiphi2smplx](externals/hiphi2smplx/README.md) | Active HiPHI/Wendy BVH to SMPL-X conversion |
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

See [dependency roles and historical recovery](docs/dependency-roles.md) for local
state, separate runtime prerequisites and read-only inspection from a worktree.

The migrated hhtools checkout includes local Astro robot changes, its existing
environment, local assets, and Git history. Those local changes are not reproduced
by cloning its recorded commit. See [migration notes](docs/migration.md).

See the [ProtoMotions/PyRoki setup and solver comparison](docs/protomotions-pyroki.md)
and [official UMR implementation investigation](docs/umr-solver-investigation.md).
ProtoMotions is included as source; large Git LFS assets are fetched on demand.

## UMR G1 reproduction

Run fresh official-default training and the complete bundled HiPHI motion through
Motion Studio's own interface:

```sh
python3 scripts/reproduce_umr_g1.py --output outputs/umr-g1-baseline/<fresh-run-id>
```

Requires the existing UMR environment, local SMPL-X model, and host GPU access.
See the [integration review](docs/umr-integration-review.md) and
[experiment record](experiments/umr-g1-baseline-20261029/README.md).

## Local Studio application

Launch persistent robot/pose and motion preparation, native UMR stages and
synchronized inspection with `python3 -B scripts/studio.py`. See
[Local Studio](docs/local-studio.md) for setup, offline dependencies, recovery
and owned service contracts. The [full G1 acceptance record](experiments/studio-baseline-acceptance-20261030/README.md)
keeps fresh application results separate from historical references.

## Local documentation

Double-click [docs.html](docs.html) in this project root to read the offline
HTML documentation. Navigation, search and saved figures are prebundled; no
server or localhost URL is required for reading. See the
[documentation guide](docs/offline-documentation.md) for rebuilding, portability,
the direct-file verification limit and separately optional 3D tools.
Legacy evidence and the prospective static baseline remain labeled separately.
Generated HTML and evidence bundles stay local. After editing sources, select an
unused edition ID for each build (an existing destination is refused):

```sh
python3 scripts/build_docs.py --edition local-20261029-03
python3 scripts/verify_docs.py --edition local-20261029-03
```
A fresh clone also needs the preserved local report/evidence artifacts described
in the guide.

## Layout

```text
motion_studio/   Owned operations, typed interfaces and concrete integrations/ adapters
scripts/         Thin CLI wiring and explicit frozen compatibility entry points
tests/           Owned behavior tests; root check command discovers pure suites
schemas/         Experiment plan/result JSON schemas
robots/          Pinned robot definitions, named poses and source notices
assets/          Portable built-in robot snapshots, meshes and source notices
externals/       Independent upstream checkouts and their manifest
references/      Zotero-derived bibliography and reading index
docs/            Authored guidance, reader templates and catalog
configs/         Owned configuration and dependency-role records
experiments/     Reproduction source, provenance and small reviewed results
.scratch/        Authoritative local specs, tickets and execution records
data/            Local input data (contents ignored)
outputs/         Fresh runs, reading editions and verified archives (ignored)
```

The package owns `evidence/`, `documentation/`, `preservation/`, `artifacts/`,
`robots/`, `checks.py` and `motion_data_paths.py`; robot schema validation lives in
`motion_studio/robots/_schema.py`. An ignored `.cache/` may hold verified immutable
source closures; generated models, geometry and learned artifacts belong to fresh
runs. No shared environment or automatic asset download is introduced.

The [bundled assets](assets/README.md) include the current default Astro P2 from
`menagerie_x`, available as a built-in robot in Local Studio. Its snapshot is
independent of the historical Astro definitions under `robots/`.

Use the [check command and runtime tiers](docs/checks.md),
[Wendy conversion adapter](docs/wendy-conversion-adapter.md),
[saved evidence operations](docs/evidence.md), [robot selection](robots/README.md),
and [canonical UMR preparation](docs/umr-canonical-preparation.md). Canonical
preparation is explicitly selected and remains prepared-only; official G1
reproduction above keeps its own pinned bundled assets and does not consult the
robot catalog. Named-frame checks, inertia and geometry claims remain separate.

For storage and recovery, see [preservation receipts](docs/preservation.md),
[verified relocation and restoration](docs/artifact-relocation.md), and the
[additive layout closeout](experiments/layout-and-robot-assets-evidence/ticket13/README.md).
Legacy aliases retain original bytes; frozen historical writers must use fresh
preparation/output routes. Existing bulky outputs and retained exceptions are
accounted for in the relocation ledger, without a workspace-size reduction claim.

Shared local datasets and human-model assets are organized under `/data/motions`;
see [local data conventions](data/README.md).

Start with the [workflow and roadmap](docs/workflow.md), the
[reference library](references/README.md), or the
[experiment template](experiments/TEMPLATE.md).

## Contributing and attribution

For branch naming, integration and cleanup, follow the
[branch convention](docs/workflow.md#branches-and-worktrees).

Record source revisions, commands, data provenance, coordinate conventions, and
results for experiments. Develop features and integrations here; preserve any
unavoidable minimal upstream patch in its external repository with a reproducible
record, following the development policy.

External repositories retain their own licenses and notices. Dataset, model-weight,
and robot-asset terms apply separately. No umbrella license is chosen for new
Motion Studio code yet. Cite the methods and datasets used in each result.
