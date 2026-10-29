"""Discover and run owned checks without importing scientific runtimes."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import ast
import json
import os
import re
import shutil
import subprocess
import sys

TIERS = ('pure', 'saved-evidence', 'javascript', 'umr-static')


@dataclass(frozen=True)
class Suite:
    path: str
    tier: str
    inputs: tuple[str, ...] = ()
    modules: tuple[str, ...] = ()
    run_inputs: tuple[str, ...] = ()


def discover(root: Path) -> tuple[Suite, ...]:
    """Inventory owned tests using literal metadata, never importing their code.

    New Python test files default to pure. Set CHECK_TIER and optional CHECK_INPUTS
    and CHECK_MODULES literals for checks needing evidence or another runtime.
    """
    suites = []
    for folder in ('tests', 'scripts', 'motion_studio'):
        for path in sorted((root / folder).rglob('test*.py')):
            metadata = {}
            for node in ast.parse(path.read_text(), filename=str(path)).body:
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name) and target.id.startswith('CHECK_'):
                            metadata[target.id] = ast.literal_eval(node.value)
            tier = metadata.get('CHECK_TIER', 'pure')
            if tier not in TIERS:
                raise ValueError(f'Unknown check tier {tier!r}: {path}')
            for field in ('CHECK_INPUTS', 'CHECK_MODULES', 'CHECK_RUN_INPUTS'):
                values = metadata.get(field, ())
                if not isinstance(values, (tuple, list)) or not all(
                        isinstance(value, str) for value in values):
                    raise ValueError(f'{field} must be a list of strings: {path}')
            suites.append(Suite(str(path.relative_to(root)), tier,
                                tuple(metadata.get('CHECK_INPUTS', ())),
                                tuple(metadata.get('CHECK_MODULES', ())),
                                tuple(metadata.get('CHECK_RUN_INPUTS', ()))))
        for path in sorted((root / folder).rglob('test*.cjs')):
            found = re.search(r'^// CHECK_INPUTS: (.+)$', path.read_text(), re.M)
            inputs = json.loads(found[1]) if found else []
            if not isinstance(inputs, list) or not all(isinstance(v, str) for v in inputs):
                raise ValueError(f'CHECK_INPUTS must be a list of strings: {path}')
            suites.append(Suite(str(path.relative_to(root)), 'javascript', tuple(inputs)))
    return tuple(suites)


@dataclass(frozen=True)
class Outcome:
    path: str
    tier: str
    status: str
    detail: str


@dataclass(frozen=True)
class Report:
    outcomes: tuple[Outcome, ...]

    @property
    def exit_code(self) -> int:
        return int(any(o.status in ('failed', 'unavailable') for o in self.outcomes))


def check(root: Path, *, tiers: tuple[str, ...] = ('pure',),
          umr_python: Path | None = None, umr_run: Path | None = None,
          docs_edition: Path | None = None) -> Report:
    """Run selected tiers; unavailable prerequisites fail without importing tests.

    Each suite executes in a separate subprocess. Static reproduction checks use
    the caller-supplied interpreter and saved run, never the default pure runtime.
    No packages are installed and no experiment stages are started.
    """
    if not tiers or set(tiers) - set(TIERS):
        raise ValueError('Select at least one known check tier: ' + ', '.join(TIERS))
    root = root.resolve()
    outcomes = []
    for suite in discover(root):
        path = root / suite.path
        if suite.tier not in tiers:
            outcomes.append(Outcome(suite.path, suite.tier, 'not-selected',
                                    'Select this tier explicitly'))
            continue
        selected_docs = (docs_edition is not None and
                         suite.path == 'scripts/docs_site/test_search.cjs')
        edition_path = (root / docs_edition).resolve() if selected_docs else None
        inputs = ((str(edition_path / 'supporting-records.html'),)
                  if selected_docs else suite.inputs)
        missing = [name for name in inputs if not (root / name).exists()]
        python = sys.executable
        node = shutil.which('node')
        if suite.tier == 'javascript' and not node:
            missing.append('Node.js executable on PATH')
        if suite.tier == 'umr-static':
            if umr_python is None or not umr_python.is_file():
                missing.append('--umr-python must name an existing interpreter')
            if umr_run is None or not umr_run.is_dir():
                missing.append('--umr-run must name an existing preserved run directory')
            else:
                missing.extend(str(umr_run / name) for name in suite.run_inputs
                               if not (umr_run / name).is_file())
            python = str(umr_python)
        if missing:
            outcomes.append(Outcome(suite.path, suite.tier, 'unavailable',
                                    'Missing required inputs: ' + ', '.join(missing)))
            continue
        env = os.environ.copy()
        env['PYTHONDONTWRITEBYTECODE'] = '1'
        env['PYTHONPATH'] = os.pathsep.join((str(root), str(root / 'scripts')))
        command = [python, str(Path(__file__).with_name('_check_worker.py')),
                   str(path), str(root)]
        if suite.tier == 'umr-static':
            command = [python, str(path), str(umr_run.resolve()), '-v']
        if suite.tier == 'javascript':
            command = [node, str(path)]
            if selected_docs:
                command.extend(('--output', str(edition_path)))
        try:
            if suite.modules:
                probe = subprocess.run(
                    [python, '-c',
                     'import importlib.util,sys; '
                     'sys.exit(0 if all(importlib.util.find_spec(n) '
                     'is not None for n in sys.argv[1:]) else 1)', *suite.modules],
                    cwd=root, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    check=False, timeout=30)
                if probe.returncode:
                    outcomes.append(Outcome(suite.path, suite.tier, 'unavailable',
                                            'Required runtime modules: ' + ', '.join(suite.modules)))
                    continue
            result = subprocess.run(command, cwd=root, env=env, text=True,
                                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                    check=False, timeout=300)
            outcomes.append(Outcome(suite.path, suite.tier,
                                    'passed' if result.returncode == 0 else 'failed',
                                    result.stdout))
        except (OSError, subprocess.TimeoutExpired) as error:
            outcomes.append(Outcome(suite.path, suite.tier, 'failed', str(error)))
    if not outcomes:
        outcomes.append(Outcome('', 'pure', 'failed', 'No owned checks discovered'))
    elif not any(o.status != 'not-selected' for o in outcomes):
        outcomes.append(Outcome('', ','.join(tiers), 'failed',
                                'No checks selected for requested tiers'))
    return Report(tuple(outcomes))
