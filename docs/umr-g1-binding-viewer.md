# G1 motion and segment binding viewer

Export a fresh browser viewer from a completed official G1 run. From the
Motion Studio workspace:

```sh
python3 -B scripts/view_umr_bindings.py \
  --run outputs/umr-g1-baseline/manual-01 \
  --output outputs/umr-g1-inspection/my-playback
python3 -B -m http.server 8772 --bind 127.0.0.1 \
  --directory outputs/umr-g1-inspection
```

Open `http://127.0.0.1:8772/my-playback/`. Choose a fresh output name for each
export; existing directories are rejected. Export uses the pinned official UMR
interpreter, saved learned correspondence arrays, and run-local G1 assets.
It reconstructs the source SMPL-X motion on CPU and performs G1 forward
kinematics without training, retargeting, or simulation stepping. Input hashes and external source state are checked before and after.
The exporter currently requires the local Three.js vendor files retained in
`outputs/umr-binding-report/documentation/vendor`.

Use **Play**, the timeline, or **Frame** to inspect the saved clip. Step with
**−1 frame / +1 frame**, change **Speed**, and enable or disable **Loop playback**.
Segment filtering, slot selection, mesh visibility, and paired lines work during
playback. **Reference pose** pauses the clip and restores the original inspection
pose. **Front / Rear / Side** refit the camera to the current pose.

The human on the left plays the original source motion, using the saved body
shape, finger-pose policy, source frame IDs, ground shift and retargeting scale.
The G1 mesh on the right plays the saved robot motion on the same timeline.
Human binding points follow their bound triangles using barycentric coordinates;
G1 binding points share each moving geometry's rigid transform. Colors
represent the source segment assigned to each learned slot; target body and mesh
ownership are listed separately. Projection distances refer to the reference
binding step. These reconstructed bindings are not saved per-frame solver
telemetry or evidence of anatomical accuracy or dynamic feasibility.

The export preserves all saved frames at their recorded FPS, with no interpolation
or resampling. Human vertices stream in 64-frame chunks, with at most three
chunks cached in the browser. Both models wait together if the next human chunk
is unavailable. Human vertices use root-relative int16 coordinates in 0.1 mm
steps (about 0.05 mm maximum error per axis); root positions retain float32
precision. The source clip and SMPL-X model hashes are recorded and checked for
changes during export. The existing local SMPL-X weights are required. Rendering can skip displayed frames when the browser is slower
than the recorded rate. Source frame IDs, joint order, root quaternion convention
(`wxyz`), units (metres), and coordinate conversion are recorded in `bindings.json`.
The viewer uses Y-up coordinates: native robot `[x,y,z]` becomes `[y,z,x]`.
During motion playback both use the saved ground convention and fixed initial
horizontal origins; **Keep both centered horizontally** additionally removes
each model's changing horizontal translation for display only. Turn it off to
inspect both saved trajectories. Vertical root motion and all rotations are
retained. Reference-pose comparison restores the original static meshes and
their separate floor offsets.

The verified local example is
`outputs/umr-g1-inspection/manual-01-synchronized/`; `human-verification.json`
records sampled vertex and binding-point comparisons with direct SMPL-X forward
calls. The previous robot-only export is retained at
`outputs/umr-g1-inspection/manual-01-playback/`, including its robot transform
verification record.
