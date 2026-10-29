"""Reconstruct saved evidence and inspect/reserve plans without numerical execution.

Inputs are explicit workspace Paths and JSON-compatible v1 dictionaries. Returned
summaries/reports are independent dictionaries; inputs are not mutated. New bundle
writes are exclusive. The package imports no upstream runtime or report builder.
Schema validation requires jsonschema in the selected tooling Python, loaded only
when validating a plan/result. No dependency is installed automatically.
"""
from ._contracts import validate
from ._files import verify_bundle
from ._legacy import reconstruct
from ._preflight import inspect_plan, reserve
from .report_rules import normalize_segment, validate_static_result

__all__ = ['reconstruct', 'validate', 'verify_bundle',
           'normalize_segment', 'validate_static_result', 'inspect_plan', 'reserve']
