"""Saved static-report rules shared by reconstruction and historical callers.

Rows describe native19 or common18 anatomical labels and retain their original
source-slot denominators. These checks neither load geometry nor compute metrics.
"""
from __future__ import annotations

import math


def normalize_segment(row: dict, common: bool) -> dict:
    """Copy one saved row into the result contract; absent measurements stay null."""
    return {
        'segment': row['source'], 'slots': row['slots'],
        'compatible': row['compatible'] if common else row['compatible_zone_slots'],
        'precision': row['zone_precision'],
        'coverage': row.get('coverage_within_20mm') if common else row.get('expected_sample_coverage_within_20mm'),
        'high_slots': row.get('high_confidence_slots'),
        'high_compatible': row.get('high_confidence_compatible'),
    }


def validate_static_result(document: dict, common: bool = False) -> None:
    """Validate the saved 4,096-slot native19/common18 counts and precision.

    Raise ValueError on inconsistent rows. No mutation, resampling, pooling or
    rounding is performed. The 1e-12 precision tolerance is the historical rule.
    """
    rows = document['common_per_segment'] if common else document['per_segment']
    if len(rows) != (18 if common else 19):
        raise ValueError('Static report requires 18 common or 19 native segments')
    if sum(row['slots'] for row in rows) != 4096:
        raise ValueError('Static report source-slot denominator must total 4096')
    for row in rows:
        precision = row['zone_precision']
        count = row.get('compatible', row.get('compatible_zone_slots'))
        if not math.isfinite(precision) or not 0 <= precision <= 1:
            raise ValueError('Segment precision must be finite and within [0, 1]')
        if not 0 <= count <= row['slots'] or row['slots'] <= 0:
            raise ValueError('Compatible count must be within a positive source-slot denominator')
        if abs(count / row['slots'] - precision) >= 1e-12:
            raise ValueError('Segment precision does not match its source-slot denominator')
