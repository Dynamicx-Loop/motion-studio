"""Resolve paths recorded before the 2026-10-27 motion-data relocation.

New configs use canonical paths directly. Archived provenance keeps its original
bytes and hashes; readers translate recorded filenames through the saved move
map rather than requiring filesystem compatibility symlinks. This changes path
resolution only, never the contents or expected hash of a recorded input.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_ROOT = Path('/data/motions')
_LEGACY = {'smpl', 'soma', 'soma_uniform', 'fzmotion', 'hiphi', 'bvh'}
_MAP = _ROOT / '.migration/2026-10-27/path-replacements.json'


def _relocations() -> tuple[tuple[Path, Path], ...]:
    records = json.loads(_MAP.read_text())
    return tuple((Path(old), Path(new)) for old, new in
                 sorted(records.items(), key=lambda item: -len(item[0])))


def canonical_motion_path(path: str | Path) -> Path:
    """Return a recorded motion path's current location without legacy entries.

    The move map is read only for a legacy path. Unknown legacy paths raise
    ValueError rather than silently selecting an unrelated dataset. Paths outside
    this migration, including relative paths, pass through unchanged.
    """
    value = Path(path)
    if not value.is_relative_to(_ROOT):
        return value
    relative = value.relative_to(_ROOT)
    if not relative.parts or relative.parts[0] not in _LEGACY:
        return value
    for old, new in _relocations():
        if value.is_relative_to(old):
            return new / value.relative_to(old)
    raise ValueError(f'No unambiguous motion-data relocation for {value}; see {_MAP}')


def canonical_motion_config(value: Any) -> Any:
    """Copy JSON-like config data with recorded motion paths relocated.

    Preserves scalar types and leaves the input unchanged. Only absolute motion
    paths are translated, including dictionary keys used by provenance maps.
    """
    if isinstance(value, str) and value.startswith(str(_ROOT) + '/'):
        return str(canonical_motion_path(value))
    if isinstance(value, dict):
        return {canonical_motion_config(k): canonical_motion_config(v)
                for k, v in value.items()}
    if isinstance(value, list):
        return [canonical_motion_config(item) for item in value]
    return value
