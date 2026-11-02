"""Worked reference-heading cases for the HiPHI head-control analysis."""
CHECK_TIER = "saved-evidence"
CHECK_MODULES = ("numpy",)

import importlib.util
from pathlib import Path
import unittest

import numpy as np

path = Path(__file__).resolve().parents[1] / 'experiments/hiphi-head-objective/pitch.py'
spec = importlib.util.spec_from_file_location('head_pitch', path)
pitch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pitch)


class HeadPitchTest(unittest.TestCase):
    def test_constant_control_uses_its_own_heading(self):
        # A torso leaning 10 degrees along +X and an unmoving +X heading.
        angle = np.deg2rad(10)
        axes = np.tile([np.sin(angle), 0, np.cos(angle)], (2, 1))
        neutral_roots = np.tile([[0, 0, 1], [1, 0, 0], [0, 1, 0]], (2, 1, 1))
        neutral_heading = pitch.projected_heading(neutral_roots, np.eye(3))
        # The unrelated animated source turns 90 degrees; using it is wrong.
        animated_heading = np.array([[1, 0, 0], [0, 1, 0]])
        np.testing.assert_allclose(
            pitch.variant_pitch_degrees(axes, 'neutral-baseline', animated_heading, neutral_heading),
            [10, 10], atol=1e-12,
        )
        np.testing.assert_allclose(
            pitch.variant_pitch_degrees(axes, 'baseline', animated_heading, neutral_heading),
            [10, 0], atol=1e-12,
        )

    def test_vertical_forward_has_no_heading(self):
        with self.assertRaises(ValueError):
            pitch.projected_heading(np.eye(3)[None, :, :], np.eye(3))


if __name__ == '__main__':
    unittest.main()
