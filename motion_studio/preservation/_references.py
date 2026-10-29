"""Record local reference edges and explicit hash-named input closures."""
from __future__ import annotations

import json
import os
from pathlib import Path
import re
from urllib.parse import unquote

from ._files import TEXT_SUFFIXES, secret

TOKEN = re.compile(r'''[^\s"'<>()[\]{},;=]+''')
DIGEST = re.compile('[0-9a-f]{64}')


def candidates(value: str, source: Path, workspace: Path):
    value = unquote(value.split('#', 1)[0].split('?', 1)[0])
    if not value or '://' in value or '\x00' in value:
        return []
    path = Path(value)
    if path.is_absolute():
        return [path]
    return [source.parent / path, workspace / path]


def link_references(files: list[dict], workspace: Path) -> None:
    lookup = {str(Path(item['absolute_path']).absolute()): item for item in files}
    for item in files:
        source = Path(item['absolute_path'])
        if source.suffix.lower() not in TEXT_SUFFIXES or item.get('bytes', 0) > 8 * 1024 * 1024:
            continue
        try:
            text = source.read_text()
        except (UnicodeError, OSError):
            continue
        for token in TOKEN.findall(text):
            if '/' not in token and '.' not in token:
                continue
            for path in candidates(token, source, workspace):
                target = lookup.get(os.path.abspath(path))
                if target is not None and item['path'] not in target['inbound_references']:
                    target['inbound_references'].append(item['path'])


def input_closure(files: list[dict], workspace: Path):
    """Yield explicit path/hash pairs; missing historical paths stay findings."""
    seen = set()
    for item in files:
        source = Path(item['absolute_path'])
        if source.suffix != '.json' or item.get('bytes', 0) > 8 * 1024 * 1024:
            continue
        try:
            data = json.loads(source.read_text())
        except (ValueError, OSError, UnicodeError):
            continue
        pairs = []

        def collect(value):
            if isinstance(value, dict):
                for key, child in value.items():
                    if isinstance(child, str) and DIGEST.fullmatch(child) and ('/' in key or '.' in key):
                        pairs.append((key, child))
                    elif key == 'path' and isinstance(child, str) and isinstance(value.get('sha256'), str):
                        pairs.append((child, value['sha256']))
                    elif isinstance(child, (dict, list)):
                        collect(child)
            elif isinstance(value, list):
                for child in value:
                    collect(child)

        collect(data)
        for value, expected in pairs:
            options = [Path(os.path.abspath(p)) for p in candidates(value, source, workspace)
                       if not secret(p) and not secret(p.resolve())]
            if not options:
                continue
            path = next((p for p in options if p.is_file()), options[0])
            key = str(path), expected
            if key not in seen:
                seen.add(key)
                yield path, expected, item['path']
