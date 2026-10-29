# Workspace preservation receipts

Use the owned preservation operation before moving evidence or changing dependency
layout. It records existing bytes and dirty source without resetting a repository,
rebuilding an environment or running an experiment. The command needs system
Python and Git only.

From the project root, with a fresh ignored receipt destination:

```sh
python3 scripts/preserve_workspace.py capture \
  --workspace /data/workspace/motion_studio \
  --output /data/workspace/motion_studio/outputs/preservation/<fresh-id> \
  --repository menagerie=/data/workspace/notAnyrobot/menagerie_x \
  --compatibility-root /data/workspace/rplab/human-humanoid-tools \
  --source-root /data/motions
python3 scripts/preserve_workspace.py verify \
  /data/workspace/motion_studio/outputs/preservation/<fresh-id>
```

`capture_inventory` and `verify_inventory` are the public Python operations in
`motion_studio.preservation`. Capture returns receipt and inventory hash; verify
returns a result with `passed`, `errors`, file count and repository count. Keep the
returned SHA-256 outside the receipt when an independent integrity anchor matters.
A self-contained local seal detects accidental changes, not deliberate replacement
of both content and seal.

## What is captured

- `inventory.json` contains absolute and workspace-relative file paths, sizes,
  SHA-256, file/symlink kind, symlink target, cohort, role and inbound text references.
  Logical bytes include file symlinks; unique stored bytes count ordinary file
  inodes once. Directory symlinks are recorded without recursive traversal.
- The owned workspace and experiment/output evidence are scanned, excluding the
  receipt itself, Git object directories, credentials, virtual environments,
  caches and temporary directories. Source-root options permit hashing only
  explicitly provenance-named inputs there; they do not recursively scan datasets.
- Each discovered external checkout plus explicitly named repository records its
  HEAD, exact NUL-delimited porcelain status, Git/worktree locations, ignored
  locations and metadata. Pins and historical source versions remain in the
  captured workspace manifest and experiment records.
- `recovery/<repository>/tracked.patch` contains credential-safe dirty tracked
  changes relative to HEAD. `untracked-source.tar` contains eligible untracked text
  source/small evidence, up to 4 MiB per file. Capture reconstructs changed HEAD
  blobs in disposable scratch space, applies the patch and checks recovered source
  hashes; untracked archive members are also restored/checked without touching live
  repositories. Excluded and non-archived paths are enumerated.
- `frozen_reference_checks` preserves expected hashes from historical JSON records
  and identifies whether the currently available file matches. An old absolute
  path or old source revision can be unavailable/different. This finding does not
  rewrite the record or claim a historical numerical rerun.
- Compatibility roots record top-level paths and alias targets without traversing
  their environments or duplicating the old hhtools metadata.
- `seal.json` hashes receipt payloads. Verification also detects added payloads,
  changed source bytes/aliases, added ignored artifacts and Git source drift.

## Boundaries

Role and inbound-reference fields assist review; they are not an automatic move
plan. File extensions and local path conventions cannot prove every artifact's
origin. Relocation must select complete, reviewed resource closures and preserve
legacy readers using a separate verified mapping. Large JSON may be generated
geometry; small configuration/results must stay reproducible.

Credential directories and files such as `.aws`, `.codex`, `.agents`, `.ssh` and
`.env*` are never archived or scanned for contents. Their Git status/path metadata
may still appear, with excluded tracked paths explicitly identified. The receipt
is local: source patches, paths and small evidence retain their original terms.
Do not treat it as permission to redistribute assets or private records.

Ignored binary assets and environments remain at their original locations, with
manifests and selected frozen-input hashes. Git object databases are not backed
up. The recovery bundle does not recreate the entire machine, licensed models,
all ignored assets or unavailable historical revisions. Preserve those separately
before recreating a workspace elsewhere.

An existing receipt is refused. Verification never rewrites its baseline; expected
later owned changes must be explained using separate migration/change receipts.
A passing preservation check establishes unchanged recorded inputs, not numerical
reproduction, contact quality, dynamic feasibility or hardware safety.
