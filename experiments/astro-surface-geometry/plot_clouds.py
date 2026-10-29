#!/usr/bin/env python3
"""Render already-validated static clouds; performs no simulation or fitting."""
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/astro-surface-geometry"
clouds = np.load(OUT / "clouds.npz")
fig, axes = plt.subplots(2, 2, figsize=(10, 9), sharey=True, layout="constrained")
for col, (key, color, title) in enumerate((("visual", "#2864ad", "Visual meshes"),
                                          ("primitive", "#db7130", "Cleaned collision primitives"))):
    points = clouds[key]
    for row, (axis, label) in enumerate(((0, "Left (m)"), (2, "Forward (m)"))):
        ax = axes[row, col]
        ax.scatter(points[:, axis], points[:, 1], s=2, c=color, alpha=.65, linewidths=0)
        ax.set_aspect("equal")
        ax.set_xlabel(label)
        ax.set_ylabel("Up from pelvis (m)")
        ax.grid(alpha=.18)
        ax.spines[["top", "right"]].set_visible(False)
        ax.set_title(f"{title} · {'front' if row == 0 else 'side'}")
        ax.set_xlim((-1.05, 1.05) if row == 0 else (-.35, .35))
fig.suptitle("Astro T-pose surface comparison · 4,096 points per surface · seed 9000", fontsize=13)
fig.savefig(OUT / "surface-comparison.png", dpi=170)
