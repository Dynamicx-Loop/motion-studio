# ProtoMotions / PyRoki integration and solver comparison

Investigated 2026-10-22. Source integration only: no dependency installation,
GPU benchmark, or end-to-end retargeting job has been performed.

## Included repositories

| Repository | Local path | Revision | Code license |
| --- | --- | --- | --- |
| ProtoMotions | `externals/ProtoMotions` | `f69fdcaabff31846b4d2247207417b57dc788828` | Apache-2.0 |
| PyRoki | `externals/pyroki` | `388e43e1fc0d0ee382968d3dd72970fd62a0450c` | MIT |

ProtoMotions' `pyroki/` directory contains its robot-specific retargeting scripts.
It is not the installable PyRoki library; that library is the separate sibling
checkout. ProtoMotions explicitly says that v3 uses PyRoki and earlier versions
used Mink. This change applies to ProtoMotions, not to official UMR.
[ProtoMotions README](https://github.com/NVlabs/ProtoMotions/blob/f69fdcaabff31846b4d2247207417b57dc788828/README.md), [PyRoki package metadata](https://github.com/chungmin99/pyroki/blob/388e43e1fc0d0ee382968d3dd72970fd62a0450c/pyproject.toml).

## What the ProtoMotions retargeter solves

The inspected G1 implementation constructs joint and root-pose variables across
all timesteps, plus scale variables, and solves a `jaxls.LeastSquaresProblem`
through PyRoki/JAX. Its costs include relative keypoint alignment, world-space
alignment (including auxiliary points), scale regularization, joint/root temporal
smoothness, rest posture, joint-limit and velocity penalties, foot contact, and
foot tilt. The solve requests up to 800 iterations. PyRoki describes its jaxls
backend as Levenberg–Marquardt optimization on manifolds; the application does
not override the default solver algorithm here.
[G1 cost assembly and solve](https://github.com/NVlabs/ProtoMotions/blob/f69fdcaabff31846b4d2247207417b57dc788828/pyroki/batch_retarget_to_g1_from_keypoints.py#L1199-L1306),
[PyRoki solver description](https://github.com/chungmin99/pyroki/blob/388e43e1fc0d0ee382968d3dd72970fd62a0450c/README.md).

These are kinematic trajectory costs. This step does not simulate a controller
or certify dynamic feasibility. In this particular G1 script, joint bounds are
soft `limit_cost` penalties, and the self-collision cost is commented out. Do not
assume every capability of the general PyRoki library is enabled by this workflow.
[G1 costs](https://github.com/NVlabs/ProtoMotions/blob/f69fdcaabff31846b4d2247207417b57dc788828/pyroki/batch_retarget_to_g1_from_keypoints.py#L1199-L1253).

The G1 batch script defaults to `--target-raw-frames 450`. It truncates longer
inputs and pads shorter ones before optimization; 450 frames correspond to
15 seconds at 30 FPS. This is a default buffer policy, not an intrinsic PyRoki
limit. Account for it when comparing full clips, and use the direct batch script
to change the buffer size if needed.
[Padding/trimming](https://github.com/NVlabs/ProtoMotions/blob/f69fdcaabff31846b4d2247207417b57dc788828/pyroki/batch_retarget_to_g1_from_keypoints.py#L156-L202),
[CLI default](https://github.com/NVlabs/ProtoMotions/blob/f69fdcaabff31846b4d2247207417b57dc788828/pyroki/batch_retarget_to_g1_from_keypoints.py#L449-L454).

## Comparison with UMR

| Aspect | Official UMR | Unofficial UMR reproduction | ProtoMotions PyRoki workflow |
| --- | --- | --- | --- |
| Correspondence | Learned ordered surface points | Reproduction of surface-correspondence approach | Explicit robot-specific keypoint/link mappings |
| Optimization interface | Custom residual/Jacobian and constraint assembly | Mink tasks/limits, custom conic branch | PyRoki + JAX + jaxls least squares |
| Numerical backend | Direct Clarabel quadratic/conic solves | Mink IK; L2 branch calls Clarabel directly | jaxls Levenberg–Marquardt backend |
| Temporal treatment | Sequential frames; optional bidirectional candidates and DP | Framewise IK loop | Coupled trajectory variables and temporal costs |
| Dynamics guarantee | Not established by retargeting | Not established by retargeting | Not established by retargeting |

See the [official UMR investigation](umr-solver-investigation.md) for the exact
source evidence and qualifications for both UMR implementations. ProtoMotions'
robot-specific keypoint mapping is in its
[G1 script](https://github.com/NVlabs/ProtoMotions/blob/f69fdcaabff31846b4d2247207417b57dc788828/pyroki/batch_retarget_to_g1_from_keypoints.py).
This table compares formulations, not measured quality or speed. Porting UMR to
PyRoki would require implementing its surface objectives and constraints; it is
not simply a solver dependency swap.

## Setup in Motion Studio

1. Run `python3 scripts/workspace.py bootstrap` from the Motion Studio root on a
   fresh workspace. Existing checkouts are preserved.
2. Follow [ProtoMotions installation](https://nvlabs.github.io/ProtoMotions/getting_started/installation.html)
   for a dedicated ProtoMotions environment and your selected simulator.
3. Follow [the retargeting tutorial](https://nvlabs.github.io/ProtoMotions/tutorials/workflows/retargeting_pyroki.html)
   for a separate PyRoki environment. Install the local library checkout instead
   of cloning a second copy:

   ```sh
   conda create -n pyroki python=3.10
   conda activate pyroki
   python -m pip install -e /data/workspace/motion_studio/externals/pyroki
   ```

   Choose JAX/CUDA dependencies appropriate to the machine. The upstream library
   declares jaxls via a Git URL without a commit pin; the workspace manifest pins
   repository source, not a fully locked transitive environment. Capture installed
   versions when establishing a runnable baseline.
   [Dependency declaration](https://github.com/chungmin99/pyroki/blob/388e43e1fc0d0ee382968d3dd72970fd62a0450c/pyproject.toml).

4. Fetch required large assets. ProtoMotions is configured in the manifest with
   `skip_lfs: true` to avoid automatically downloading all pretrained models and
   motion data. Some assets may already be cached locally; others remain LFS
   pointer files. From its checkout, fetch the robot meshes needed for G1/H1_2:

   ```sh
   cd /data/workspace/motion_studio/externals/ProtoMotions
   git lfs pull --include="protomotions/data/assets/mesh/G1/**,protomotions/data/assets/mesh/H1_2/**"
   ```

   Fetch other assets explicitly as required by the selected workflow. Preserve
   their upstream license notices. Source cloning alone is not runtime readiness.
   [LFS rules](https://github.com/NVlabs/ProtoMotions/blob/f69fdcaabff31846b4d2247207417b57dc788828/.gitattributes), [asset defaults](https://github.com/NVlabs/ProtoMotions/blob/f69fdcaabff31846b4d2247207417b57dc788828/pyroki/batch_retarget_to_g1_from_keypoints.py#L408-L440).

## Run the upstream workflow

Run from `externals/ProtoMotions` after setup. Replace interpreter and input
placeholders with absolute paths:

```sh
bash scripts/retarget_amass_to_robot.sh \
  /absolute/path/to/protomotions-env/bin/python \
  /absolute/path/to/pyroki-env/bin/python \
  /absolute/path/to/amass_train.pt \
  g1 50
```

The input is a packaged SMPL MotionLib, not raw AMASS files. The final number
selects every Nth motion; it does not limit frames. The script extracts keypoints,
retargets them, extracts source contact labels, converts results, and packages
`proto-g1.pt`. Outputs are written alongside the input MotionLib. Use a dedicated
experiment directory. `h1_2` is the other supported target in this wrapper.
[Exact wrapper behavior](https://github.com/NVlabs/ProtoMotions/blob/f69fdcaabff31846b4d2247207417b57dc788828/scripts/retarget_amass_to_robot.sh).

For one SMPL `.motion` file and an explicit output directory:

```sh
bash scripts/retarget_single_motion_to_robot.sh \
  /absolute/path/to/protomotions-env/bin/python \
  /absolute/path/to/pyroki-env/bin/python \
  /absolute/path/to/walk.motion \
  /data/workspace/motion_studio/outputs/pyroki-g1-walk \
  g1
```

[Single-motion wrapper](https://github.com/NVlabs/ProtoMotions/blob/f69fdcaabff31846b4d2247207417b57dc788828/scripts/retarget_single_motion_to_robot.sh).
The Astro robot requires its own mapping, scaling, assets, and conversion support;
it is not enabled merely by including these repositories.
