"""Compatibility alias for the owned recorded-motion-path resolver."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from motion_studio import motion_data_paths as _owned

sys.modules[__name__] = _owned
