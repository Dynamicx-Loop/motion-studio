# Local calibration for the uniform BONES-SEED samples

The parent README is an unchanged upstream guide. This local installation adds:

```text
bones-seed/
  shapes/
    soma_uniform_fit_mhr_params/soma_base_fit_mhr_params.npz
    soma_base_rig/soma_base_skel_minimal.usd
    notices/KIMODO-LICENSE.txt
    notices/SOMA-RETARGETER-LICENSE.txt
  soma_assets -> /data/motions/human_models/soma-x/f81a01796f65/overlays/umr
```

The shared uniform fit was copied from the existing Kimodo checkout at
`/data/workspace/notAnyrobot/kimodo`, revision
`3b98f78344cb6c1580d7e5cb95aa2ea4320bafe9`. SHA-256 is
`61f0b96c8386a19d44823faf4399816642b7e20691ed5b398c7402921090096e`.
The [earlier investigation](../../../../experiments/umr-baseline-g1-somax-20261102/records/uniform-fit-investigation.json)
records byte equality with NVIDIA Kimodo's official shared BONES-SEED fit at
upstream revision `e1c219c99b4b94ba48be1fb6a1cbc64ecee4c954`. It was not compared
with a newly downloaded BONES-SEED archive.

The optional rig USD was copied from the existing soma-retargeter checkout at
`/data/workspace/github/soma-x/soma-retargeter`, revision
`b3ef2708d84bfd1314ddb52d0db6c9c211df1f57`. This is a local reference rig, not a
newly acquired BONES-SEED rig distribution. The README's additional
`soma_base_skel_minimal.bvh` remains absent: the pinned fitted uniform path does
not read it or the standalone USD. No proportional actor fits are needed for
these uniform clips, even when their names contain A001.

Canonical calibration copies and license notices are under
`/data/motions/datasets/bones-seed/calibration/`. The sample manifest records
their hashes. Original dataset metadata describes the earlier migration state;
it is not rewritten as a new acquisition record.

The model link uses the existing UMR compatibility overlay derived from official
NVIDIA SOMA-X revision `f81a01796f652260ff930d5318d6c6b845a505ed`. Its
`LOCAL_MODIFICATIONS.md` explains the derived neutral NPZ; other assets link to
unchanged original downloads. Ten model, transfer and notice files are checked
by hash without copying roughly 0.7 GiB of weights. See `soma_assets/LICENSE`
and `shapes/notices/` for source notices; dataset terms remain separate.

## Use with UMR

Select SOMA source defaults and override both `soma_usd_path` and
`smpl_template.soma_usd_path` with the absolute path to the local rig USD above.
Set `motion.data` to the absolute path of `motions_uniform/bvh` and `motion.seq_key`
to one of the three filename stems. Keep `smpl_template.type` set to `soma`.
Retain a literal `motions_uniform` ancestor: discovery needs the sibling
`shapes/` and `soma_assets/` directories. Copying a BVH elsewhere can silently
select the generic neutral route.

For explicit model selection, set `UMR_SOMA_ASSETS_PATH` to the absolute
`data/sample_data/bones-seed/soma_assets` path. Assert the loaded source format
is `soma_bvh_boneseed_uniform` and template name is `soma_uniform`. Train fresh
correspondence for this fitted body and target robot; generic-neutral slots
cannot be assumed compatible.

`python3 scripts/sample_data.py populate` restores calibration copies and the
local model link; `check` verifies copied files and linked model hashes.
Nothing was downloaded, installed or accepted on the user's behalf.
