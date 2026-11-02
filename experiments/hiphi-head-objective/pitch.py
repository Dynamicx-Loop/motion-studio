"""Pitch in degrees against each input's projected pelvis heading.

Rotations are (frames, 3, 3) source-local-to-world matrices; basis maps source
world coordinates to robot world coordinates. Axes and headings are (frames, 3).
"""
import numpy as np


def projected_heading(root_rotations, basis):
    forward = root_rotations[:, :, 2] @ basis.T
    forward[:, 2] = 0
    norms = np.linalg.norm(forward, axis=1)
    if np.any(norms < 1e-12):
        raise ValueError('Pelvis forward axis has no horizontal projection')
    return forward / norms[:, None]


def pitch_degrees(axes, headings):
    return np.rad2deg(np.arctan2(np.sum(axes * headings, axis=1), axes[:, 2]))


def variant_pitch_degrees(axes, variant, animated_heading, neutral_heading):
    """Use the heading of the source motion selected for this variant."""
    heading = neutral_heading if variant.startswith('neutral') else animated_heading
    return pitch_degrees(axes, heading)
