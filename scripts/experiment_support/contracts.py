"""Versioned structural validation plus the few cross-field experiment invariants."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

from .files import read_json

SCHEMAS = Path(__file__).resolve().parents[2] / 'schemas' / 'experiments'


@lru_cache
def validator(kind: str):
    try:
        from jsonschema import Draft202012Validator
    except ImportError as error:
        raise RuntimeError('Schema validation needs jsonschema in the chosen tooling '
                           'Python. No packages are installed automatically.') from error
    schema = read_json(SCHEMAS / f'{kind}.schema.json')
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def validate(document: dict[str, Any], kind: str) -> None:
    """Raise ValueError with a field path; do not mutate data or inspect runtimes."""
    errors = sorted(validator(kind).iter_errors(document), key=lambda e: str(e.path))
    if errors:
        first = errors[0]
        raise ValueError(f"{kind} {'/'.join(map(str, first.path))}: {first.message}")
    if kind == 'plan':
        _plan_invariants(document)
    elif kind == 'result':
        if document['evidence_origin'] == 'retrospective' and document['reproducibility'] != 'not_rerun':
            raise ValueError('Retrospective reconstruction cannot claim a tested rerun')
        for metric in document['metrics']:
            if (metric['status'] == 'not_measured') != (metric['value'] is None):
                raise ValueError('Unknown metric must be null and marked not_measured')
            if metric['value'] is None and not metric['reason']:
                raise ValueError('Unknown metric requires a reason')
        keys = [(r['label_schema'], r['segment']) for r in document['segments']]
        if len(keys) != len(set(keys)):
            raise ValueError('Duplicate segment identity')
        for row in document['segments']:
            if row['compatible'] > row['slots']:
                raise ValueError('Compatible count exceeds source-slot denominator')
            if row['slots'] and abs(row['precision'] - row['compatible'] / row['slots']) > 1e-12:
                raise ValueError('Segment precision does not match its denominator')


def _plan_invariants(plan: dict) -> None:
    for field in ('inputs', 'arms', 'stages'):
        ids = [v['id'] for v in plan[field]]
        if len(ids) != len(set(ids)):
            raise ValueError(f'Duplicate {field} IDs')
    inputs = {v['id']: v for v in plan['inputs']}
    arms = {v['id']: v for v in plan['arms']}
    interval = plan['source']['interval']
    if interval['end_exclusive'] <= interval['start']:
        raise ValueError('Source interval must be nonempty and end-exclusive')
    for arm in arms.values():
        if arm['config_input'] not in inputs:
            raise ValueError(f"Unknown config input for {arm['id']}")
        control = arms.get(arm['matched_control'])
        if arm['robot'] == 'astro':
            if not control or control['robot'] != 'g1':
                raise ValueError(f"Astro arm {arm['id']} requires a G1 control")
            if any(arm[k] != control[k] for k in ('center', 'variant')):
                raise ValueError('G1 control must match center and calibration variant')
        elif arm['matched_control'] is not None:
            raise ValueError('G1 control has no further matched_control')
    for stage in plan['stages']:
        if not set(stage['input_ids']).issubset(inputs):
            raise ValueError(f"Unknown inputs in stage {stage['id']}")
        for output in stage['outputs']:
            p = Path(output)
            if p.is_absolute() or '..' in p.parts or not p.parts or output == '.':
                raise ValueError('Stage outputs must stay relative to the future run folder')
    outputs = [p for stage in plan['stages'] for p in stage['outputs']]
    if len(outputs) != len(set(outputs)):
        raise ValueError('Stage outputs must not overwrite another stage')
