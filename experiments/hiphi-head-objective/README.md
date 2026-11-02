# HiPHI head-objective controls: historical analysis correction

The saved `report.json` and `metrics.npz` are historical evidence and remain
unchanged. Their neutral-control pitch values use the animated source clip's
per-frame heading, rather than the neutral input's heading. Consequently the
neutral frame-92 and window pitch statistics should not be interpreted as pitch
relative to the neutral control. The torso-axis errors and world-up tilt use a
different reference and are unaffected by this error. The animated-source pitch
uses its corresponding heading.

The analyzer now derives heading from each input and requires `--output` naming a
new directory, which it refuses to replace. It reads the historical input and
trajectory aliases and writes the report, metrics and source crosscheck only in
that fresh directory. It requires the original local model, BVH, robot XML/mesh
closures, and UMR runtime; the full analyzer and motion pipeline were not rerun.
The 2026-11-02 focused check used saved torso axes and the neutral input's constant
heading: Astro neutral-baseline pitch range changes from 0.137189° with the wrong
heading to about 5.36e-8° with the corrected heading. This checks the reference
correction, not a fresh forward-kinematics reconstruction. Saved metrics remain
unchanged.
The historical `run.py`, `export_viewer.py`, and `plot.py` still target frozen
paths and must not be run against the original cohort. See
[artifact relocation](../../docs/artifact-relocation.md#remaining-sealed-batches-and-complete-ledger)
for preservation limits and the [robot-control preparation route](../../docs/artifact-relocation.md#frozen-writers-and-a-fresh-preparation-route)
for a separate prepared-only comparison; it does not prepare these head ablations.
