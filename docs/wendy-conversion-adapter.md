# Owned Wendy conversion

`motion_studio.integrations.wendy.convert_wendy(WendyConversionRequest(...))`
owns the active configuration-based Wendy conversion. The thin existing CLI
supports the same `--config` default and prints the same report fields:

```sh
python3 scripts/convert_wendy.py --help
python3 scripts/convert_wendy.py --config configs/umr/wendy-preview.json
```

Use a config with a **fresh** output path. Historical defaults already have
results on this machine and are deliberately refused. Import/help needs only
system Python; actual fitting uses the existing `externals/UMR/.venv/bin/python`.
The default checkout is `externals/hiphi2smplx`; `--checkout` and `--python` accept
explicit existing locations for read-only canonical inputs from another worktree.
Nothing is installed or fetched. hiphi2smplx remains independently pinned at
`65e51315ebbc82b2f0ff8e35a94565beb1b345e1`, as declared in the owned manifest.
Manifest drift or changed tracked upstream source fails before writes.

## Contract

Required JSON keys are `source`, `model`, `output` and positive integer `frames`.
Paths resolve against the Motion Studio workspace, preserving the existing CLI
rule. Recorded legacy motion/model paths use the shared owned migration helper.
Defaults are `start_frame=0`, `unit_scale=0.01`, `output_up="y"`, ten zero `betas`,
and empty `mapping_overrides`. Existing Wendy configs supply their exact named
mapping overrides. Unknown keys fail instead of being silently ignored.

The selected interval is `[start_frame, start_frame + frames)`. Declared BVH
frame count, complete channel rows, hierarchy and finite values are checked
before output creation, including rows outside the selected interval. Mapping
keys and source joint names are checked against the pinned mapping. The model
and existing interpreter must exist. Invalid inputs raise `ValueError` or
`FileNotFoundError`; occupied paths raise `FileExistsError`.

The pinned fitter uses centimetres to metres at **0.01**. Other scales are
rejected because the fitter hardcodes that conversion. Wendy Y-up is declared;
no axis rotation or resampling occurs. Source frame time and original indices
are retained, including timestamps `original_index * frame_time`. Pose arrays
retain SMPL-X order, `(frames, 165)` axis-angle radians, translations are metres,
and ten configured neutral-body betas stay fixed (float32 conversion). Shape is
not estimated; fingers, face and eyes are not fitted. Kinematic fitting does not
establish dynamic feasibility.

The result returns motion/diagnostic/report/provenance paths, original source
and model, half-open interval, frame time and FPS. Existing motion NPZ,
diagnostic NPZ and all original report fields remain available. Both NPZs also
contain `source_frame_indices` and `source_timestamps`; the motion includes
`frame_time`. Added report fields describe timing, mapping and information loss.
The nonzero-offset `.source.bvh` is a derived excerpt; the original BVH and its
arrays are preserved.

## Ownership and failures

For output `motion.npz`, the operation reserves these sibling names before it
launches the independent worker:

- `motion.npz`, `motion.diagnostics.npz`, `motion.report.json`
- `motion.provenance.json`, `motion.conversion.log`, `motion.conversion.lock`
- `motion.conversion/` containing worker request/environment and private cache/tmp
- `motion.source.bvh` for a nonzero start frame

Any occupied name, directory or dangling symlink fails before writes. Outputs
inside external checkouts are rejected, including paths through aliases.
A process-local reservation and exclusive publication prevent overwriting
concurrent results. The worker owns named-map registration in its own process,
so repeated calls cannot leak upstream global mapping mutations.

Provenance records full source/model/config and owned/external code hashes,
manifest pin, effective config, mapping, interval, conversions/information loss,
interpreter hash, Python/platform/package versions, environment overrides,
output ownership and derived output hashes. It excludes its own recursive hash.
Runtime failure retains its log, worker files and failed provenance, then raises
`RuntimeError`; use a fresh output path to retry. Large numerical runs remain an
explicit action, outside the root pure checks.

## Validation

`PYTHONDONTWRITEBYTECODE=1 python3 scripts/check.py` discovers the public boundary
and CLI-help tests in `tests/test_wendy_conversion.py`. A five-frame synthetic
BVH at 0.01 seconds checks the exclusive excerpt boundary and rejection cases.
A fresh three-frame CPU Wendy excerpt was compared with the unmodified prior
script; see the [experiment record](../outputs/artifact-archives/experiment-reset-20261104/experiments/wendy-conversion-adapter/README.md).
No full historical conversion, GPU workflow or solver tuning was performed.
