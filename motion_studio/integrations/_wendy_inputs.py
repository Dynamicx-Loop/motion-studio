"""System-Python validation for the concrete Wendy conversion adapter."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import math
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def configuration(value: object) -> dict:
    if not isinstance(value, dict):
        raise ValueError('Configuration must be a JSON object')
    value = dict(value)
    unknown = set(value) - {'source', 'model', 'output', 'frames', 'start_frame',
                            'unit_scale', 'betas', 'output_up', 'mapping_overrides'}
    if unknown:
        raise ValueError(f'Unknown configuration keys: {sorted(unknown)}')
    for key, minimum in (('frames', 1), ('start_frame', 0)):
        number = value.get(key, 0)
        if type(number) is not int or number < minimum:
            raise ValueError(f'{key} must be an integer >= {minimum}')
        value[key] = number
    scale = value.get('unit_scale', 0.01)
    if type(scale) not in (int, float) or scale != 0.01 or not math.isfinite(scale):
        raise ValueError('unit_scale must be 0.01: pinned fitting uses centimetres to metres')
    value['unit_scale'] = scale
    betas = value.get('betas', [0] * 10)
    if (not isinstance(betas, list) or len(betas) != 10 or
            any(type(b) not in (int, float) or abs(b) > 3.4e38 or not math.isfinite(b)
                for b in betas)):
        raise ValueError('betas must contain 10 finite float32 fixed shape coefficients')
    value['betas'] = betas
    if value.get('output_up', 'y') != 'y':
        raise ValueError('output_up must be y; this operation performs no axis rotation')
    value['output_up'] = 'y'
    mapping = value.get('mapping_overrides', {})
    if (not isinstance(mapping, dict) or
            any(not isinstance(k, str) or not isinstance(v, str) or not v.strip()
                for k, v in mapping.items())):
        raise ValueError('mapping_overrides must map semantic strings to joint names')
    value['mapping_overrides'] = mapping
    for key in ('source', 'model', 'output'):
        if not isinstance(value.get(key), str) or not value[key].strip():
            raise ValueError(f'{key} must be a nonempty path')
    return value


@dataclass(frozen=True)
class Source:
    lines: tuple[str, ...]
    motion_line: int
    frames: int
    frame_time: float
    names: tuple[str, ...]
    sha256: str

    def excerpt(self, start: int, frames: int) -> str:
        first = self.motion_line + 3 + start
        return '\n'.join((*self.lines[:self.motion_line + 1], f'Frames: {frames}',
                          self.lines[self.motion_line + 2],
                          *self.lines[first:first + frames])) + '\n'


def source_bvh(path: Path, start: int, frames: int) -> Source:
    """Validate declared timing, channels and every row before any output writes.

    This validates the concrete input envelope, leaving rotations/kinematics to
    the pinned upstream parser. No float32 arrays or rotations are reconstructed.
    """
    raw = path.read_bytes()
    lines = tuple(raw.decode('utf-8').splitlines())
    try:
        motion = next(i for i, line in enumerate(lines) if line.strip() == 'MOTION')
        header = lines[motion + 1].split(':')
        timing = lines[motion + 2].split(':')
        if header[0].strip() != 'Frames' or timing[0].strip() != 'Frame Time':
            raise ValueError('expected Frames and Frame Time')
        count, dt = int(header[1]), float(timing[1])
        if (count < 1 or not math.isfinite(dt) or dt <= 0 or
                not math.isfinite(1 / dt) or not math.isfinite(count * dt)):
            raise ValueError('invalid source timing')
    except (IndexError, StopIteration, OverflowError, ValueError) as error:
        raise ValueError(f'{path}: invalid BVH motion header: {error}') from error
    if start + frames > count:
        raise ValueError(f'Excerpt [{start}, {start + frames}) exceeds source motion [0, {count})')
    names, channels, stack, pending = [], 0, [], None
    offsets, channel_joints = set(), set()
    for line in lines[:motion]:
        parts = line.strip().split()
        if not parts:
            continue
        if parts[0] in ('ROOT', 'JOINT'):
            if (len(parts) < 2 or pending is not None or
                    (parts[0] == 'ROOT') != (not names) or
                    (names and (not stack or stack[-1] == 'END'))):
                raise ValueError(f'{path}: invalid source hierarchy')
            names.append(line.strip().split(maxsplit=1)[1])
            pending = len(names) - 1
        elif parts == ['End', 'Site']:
            if pending is not None or not stack or stack[-1] == 'END':
                raise ValueError(f'{path}: invalid End Site hierarchy')
            pending = 'END'
        elif parts == ['{']:
            if pending is None:
                raise ValueError(f'{path}: unexpected opening hierarchy brace')
            stack.append(pending)
            pending = None
        elif parts == ['}']:
            if not stack or pending is not None:
                raise ValueError(f'{path}: unexpected closing hierarchy brace')
            stack.pop()
        if parts[0] == 'CHANNELS':
            if not stack or stack[-1] == 'END' or stack[-1] in channel_joints:
                raise ValueError(f'{path}: invalid hierarchy CHANNELS')
            channel_joints.add(stack[-1])
            if (len(parts) < 2 or not parts[1].isdigit() or
                    int(parts[1]) != len(parts) - 2):
                raise ValueError(f'{path}: invalid CHANNELS declaration')
            if len(set(parts[2:])) != len(parts[2:]) or any(
                    p not in ('Xposition', 'Yposition', 'Zposition',
                              'Xrotation', 'Yrotation', 'Zrotation') for p in parts[2:]):
                raise ValueError(f'{path}: invalid channels')
            channels += int(parts[1])
        if parts[0] == 'OFFSET':
            if not stack or (stack[-1] != 'END' and stack[-1] in offsets):
                raise ValueError(f'{path}: invalid hierarchy OFFSET')
            offsets.add(stack[-1])
            try:
                if len(parts) != 4 or not all(abs(float(v)) <= 3.4e38 and math.isfinite(float(v)) for v in parts[1:]):
                    raise ValueError('nonfinite or malformed OFFSET')
            except (ValueError, OverflowError) as error:
                raise ValueError(f'{path}: invalid OFFSET') from error
    if stack or pending is not None or set(range(len(names))) - offsets or set(range(len(names))) != channel_joints:
        raise ValueError(f'{path}: incomplete source hierarchy')
    if not names or len(set(names)) != len(names) or channels < 1:
        raise ValueError(f'{path}: invalid source joint names/channels')
    rows = lines[motion + 3:]
    if len(rows) < count or any(line.strip() for line in rows[count:]):
        raise ValueError(f'{path}: source frame count does not match motion rows')
    for index, line in enumerate(rows[:count]):
        try:
            values = [float(v) for v in line.split()]
            if len(values) != channels or any(not math.isfinite(v) or abs(v) > 3.4e38
                                              for v in values):
                raise ValueError('wrong channel count or nonfinite float32 value')
        except (ValueError, OverflowError) as error:
            raise ValueError(f'{path}: invalid source frame {index}: {error}') from error
    return Source(lines, motion, count, dt, tuple(names), hashlib.sha256(raw).hexdigest())


def dependency(root: Path, checkout: Path, expected: str, overrides: dict,
               names: tuple[str, ...]) -> tuple[dict, dict[str, str]]:
    """Verify pinned code and read literal mapping data without importing it."""
    import ast
    import json
    import os
    import subprocess

    manifest = root / 'externals/manifest.json'
    records = json.loads(manifest.read_text())['projects']
    pin = next((p.get('revision') for p in records if p.get('name') == 'hiphi2smplx'), None)
    if pin != expected:
        raise ValueError('Review Wendy adapter compatibility before changing hiphi2smplx revision')

    def git(*args):
        try:
            return subprocess.check_output(['git', '-C', str(checkout), *args],
                                           text=True, stderr=subprocess.PIPE,
                                           env={**os.environ, 'GIT_OPTIONAL_LOCKS': '0'}).strip()
        except subprocess.CalledProcessError as error:
            raise ValueError(f'Cannot inspect hiphi2smplx checkout: {checkout}') from error

    if git('rev-parse', 'HEAD') != pin or git('diff', pin, '--name-only'):
        raise ValueError('hiphi2smplx revision/tracked source differs from the supported pin')
    code = {name: sha256(checkout / name) for name in git('ls-files').splitlines()
            if (checkout / name).is_file() and (name.endswith('.py') or
                                               name in ('pyproject.toml', 'LICENSE'))}
    skeleton = checkout / 'src/hiphi2smplx/skeleton.py'
    mapping = None
    for node in ast.parse(skeleton.read_text()).body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'HIPHI_MAP'
                                               for t in node.targets):
            mapping = ast.literal_eval(node.value)
    if not isinstance(mapping, dict) or set(overrides) - set(mapping):
        raise ValueError('mapping_overrides contains unknown body semantics')
    mapping.update(overrides)
    if len(set(mapping.values())) != len(mapping) or set(mapping.values()) - set(names):
        raise ValueError('Wendy mapping contains duplicate or missing source joints')
    return ({'revision': pin, 'checkout': str(checkout), 'tracked_code_sha256': code,
             'status': git('status', '--porcelain'),
             'manifest_sha256': sha256(manifest)}, mapping)
