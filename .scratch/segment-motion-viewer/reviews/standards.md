## Standards — final recheck

Reviewed `b5b2364..a23f137` and follow-up recovery delta `cc4f6d1..e4e0eb2` against AGENTS.md and the documented development policy.

All prior findings are resolved:

- **Adapter ownership:** `NativeStages.launch`, `decode_progress` and `required_artifacts` own UMR environment setup, native output conventions and progress parsing. `studio/_native_jobs.py` retains generic process control, logging and verified publication. An observable subprocess regression exercises a distinct environment variable, progress convention and output filename through that seam.
- **Acyclic execution dependency:** both execution modules import UTC formatting from leaf module `studio/_timestamps.py`; the native job runner no longer imports `_execution`.
- **Duplicate cache:** both viewers consume the single owned `web/human-motion.js`, including timeline/integer-frame validation. HTTP serving and standalone export packaging resolve that source; packaging assertions verify exported relative imports.

The official G1 preset keeps pin-relative source/preset checks and managed closure byte verification in the adapter before returning typed, unit-documented `RobotPosePreset`. Loading creates no revision or named pose. The service validates compiled qpos bounds; HTTP coverage checks official values, unchanged persisted state and generic-robot rejection.

The precision correction explicitly records schema, dtype, coordinates and tolerance. Both viewers share encoding selection and retain historical float32 decoding.

The namespace recovery follow-up keeps Linux boot/PID namespace discovery in `_process_guard.py` and persisted lifecycle decisions in `_recovery.py`. Unknown ownership, prior boot and verified same-scope ownership are distinguished locally before signalling or terminal publication; no UMR runtime knowledge leaked into the service. The new regression suite checks observable busy/interrupted behavior and preservation of a real unrelated sentinel process. Documentation records the actual namespace incident and conservative recovery behavior.

No new actionable documented-standard breach or baseline smell was found in either delta. Handwritten files remain within the size guideline. Vendor sources and notices are unchanged.

Source/evidence inspection only; no tests or native jobs were run. Recorded validation was inspected, not rerun. Ticket 07's final acceptance-documentation delta remains for the integrating reviewer to verify.

**Final count:** 0 remaining documented-standard findings; 0 remaining actionable baseline smells.


## Integration closeout

Root verified the final ticket 07 delta through merge `b8d363c`: documentation, reproducible validation drivers and a focused HTTP regression refinement only; no product changes beyond reviewed `e4e0eb2`. Final stable-code full native cohort, independent numerical gates, browser/standalone checks, native cancellation/retry and preservation all passed. Ticket 07 is resolved.
