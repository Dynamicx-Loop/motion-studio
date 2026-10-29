# BONES-SEED blocker (2026-10-23)

No BONES-SEED motion BVH was found in `/data/motions`, the UMR sample tree, or a broader `/data` filename scan (the latter could not read `/data/lost+found`). UMR's sample folder contains adapter documentation, not motion data. Public SOMA model assets and a static neutral template are not BONES-SEED motion. No substitution was made.

The [official dataset page](https://huggingface.co/datasets/bones-studio/seed), checked this session, requires login and acceptance of its access conditions before downloading gated files. No terms were accepted or access gate bypassed.

To unblock one **uniform** motion pair, supply authorized local paths for:

- A real `soma_uniform/bvh/{date}/{motion_name}.bvh` from `soma_uniform.tar.gz` (UMR's example defaults name `flip_090_002__A304_M.bvh`, but another actual sequence is acceptable).
- `soma_shapes/soma_base_fit_mhr_params.npz`.
- `soma_shapes/soma_base_rig/soma_base_skel_minimal.bvh` and `.usd`.

UMR expects the shape NPZ under `shapes/soma_uniform_fit_mhr_params/` and the rig under `shapes/soma_base_rig/`. Existing `/data/motions/human_models/soma-x/f81a01796f65/assets` and `umr_assets` are runtime assets, not evidence of a downloaded dataset motion. Once the actor shape is available, its template must be compared with the frozen SOMA correspondence template; static public-neutral bindings are not automatically compatible. A proportional motion instead needs the filename's exact Axxx shape NPZ. Dataset files must remain local and must not be redistributed.

## Current canonical rerun

Rechecked on 2026-10-23. The user identified `/data/motions/human_models/soma-x/f81a01796f65/overlays/umr`;
this contains the valid SOMA-X compatibility model, MHR weights, public rig and
correspondence meshes. Both UMR checkouts now link to it at the existing
`sample_data/bones-seed/soma_assets` auto-detection location. Direct adapter
loading without environment variables passed (18056 vertices, 78 joints).
These files do not include a dataset motion BVH, actor-fit NPZ or dataset base
rig BVH/USD. Static SOMA arms are complete; SOMA/BONES-SEED motion remains pending
those exact authorized inputs. No alternative animation was substituted.
