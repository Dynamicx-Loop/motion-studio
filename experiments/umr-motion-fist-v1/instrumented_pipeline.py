"""Run upstream pipeline unchanged, adding read-only fixed-coordinate instrumentation."""
import importlib.util
from pathlib import Path
import subprocess
import sys
ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / 'externals/UMR-astro-surface-experiment/scripts'
sys.path.insert(0, str(SCRIPTS))
import humanoid_retarget_pipeline as pipeline
original = pipeline.run_command

def run_command(cmd, dry_run=False):
    if Path(cmd[1]).name == 'retarget_smpl_to_humanoid_surface_vector.py':
        cmd = [cmd[0], str(Path(__file__).with_name('instrumented_retarget.py')), *cmd[1:]]
    return original(cmd, dry_run=dry_run)

pipeline.run_command = run_command
pipeline.main()
