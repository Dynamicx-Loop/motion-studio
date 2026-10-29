#!/usr/bin/env python3
"""Run the bundled HiPHI example after the Astro Studio T-pose is supplied."""
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
UMR = ROOT / "externals/UMR"
CONFIG = ROOT / "configs/umr/astro_p2_29dof.json"

config = json.loads(CONFIG.read_text())
pose = config["robot"].get("tpose_qpos")
if not isinstance(pose, dict) or not pose:
    sys.exit(f"T-pose pending: paste Studio's tpose_qpos joint-value object into {CONFIG}")

python = UMR / ".venv/bin/python"
os.chdir(UMR)
os.execv(str(python), [str(python), "scripts/humanoid_retarget_pipeline_hiphi.py",
    "--config", str(CONFIG),
    "--data", "sample_data/hiphi/data/Getting_up/get_up/Getting_up-get_up_0004",
    "--out", str(ROOT / "outputs/umr/astro_p2_29dof/getting_up.npz"),
    "--skip-view", *sys.argv[1:]])
