"""Read-only pair comparison, with scientific imports isolated in a worker."""
from dataclasses import dataclass
import hashlib
import json
import re
import os
from pathlib import Path
import subprocess
from typing import Mapping, Iterable

from . import RobotSelectionError, resolve_robot
from ._schema import read_json


CONSISTENCY_REPORT_VERSION = 2


@dataclass(frozen=True)
class ConsistencyFinding:
    check: str
    status: str
    detail: str


@dataclass(frozen=True)
class ConsistencyReport:
    definition_id: str
    poses: tuple[str, ...]
    findings: tuple[ConsistencyFinding, ...]
    identities: tuple[str, ...]
    source_hashes: tuple[tuple[str, str], ...]
    runtime: str
    position_tolerance_m: float = 1e-6
    angle_tolerance_rad: float = 1e-6
    mass_tolerance_kg: float = 1e-6
    inertia_tolerance_kg_m2: float = 1e-6
    schema_version: int = CONSISTENCY_REPORT_VERSION
    policy_sha256: str = ""
    declared_checks: tuple[str, ...] = ("joint_metadata", "joint_order", "named_frames",
        "inertial_totals", "visual_geometry_equality", "collision_policy")

    @property
    def status(self) -> str:
        if self.schema_version != CONSISTENCY_REPORT_VERSION:
            return 'unverified'
        states = {f.status for f in self.findings if f.check in self.declared_checks or f.check in ('poses','representations','runtime')}
        return 'incompatible' if 'incompatible' in states else (
            'unverified' if 'unverified' in states else 'supported')

    def supports(self, check: str) -> bool:
        if self.schema_version != CONSISTENCY_REPORT_VERSION:
            return False
        matches = [f for f in self.findings if f.check == check]
        return bool(matches) and all(f.status == 'supported' for f in matches)

    def require_supported(self, checks: Iterable[str]) -> None:
        missing = [check for check in checks if not self.supports(check)]
        if missing:
            raise RobotSelectionError('Unsupported representation claims: ' + ', '.join(missing))


def compare_representations(
    definition_id: str, source_roots: Mapping[str, Path | str], *,
    poses: tuple[str, ...] = ('zero', 'tpose'),
    runtime_python: Path | str | None = None,
    definitions_root: Path | str | None = None,
) -> ConsistencyReport:
    """Compare verified URDF/MJCF selections at explicit poses without source writes.

    Default tolerances are 1e-6 m/rad/kg/kg m². No dependency discovery or install.
    Supply an existing MuJoCo interpreter for measured frame/inertia/geometry
    checks. Missing runtime/representation is unverified; source drift raises the
    resolver's error, never an accepted known difference. No simulation stepping.
    """
    if not isinstance(definition_id,str) or not re.fullmatch(r'[a-z0-9][a-z0-9_-]*',definition_id):
        raise RobotSelectionError('Invalid definition ID')
    if not poses or len(set(poses)) != len(poses):
        raise RobotSelectionError('Supply distinct named comparison poses')
    catalog = Path(definitions_root) if definitions_root else Path(__file__).resolve().parents[2] / 'robots'
    definition = read_json(catalog / definition_id / 'robot.json')
    if not {'urdf', 'mjcf'} <= set(definition['representations']):
        return ConsistencyReport(definition_id, tuple(poses),
            (ConsistencyFinding('representations', 'unverified', 'Both URDF and MJCF are required.'),), (), (), 'unavailable')
    pairs = [tuple(resolve_robot(definition_id, rep, pose, source_roots, definitions_root=catalog)
              for rep in ('urdf', 'mjcf')) for pose in poses]
    urdf, mjcf = pairs[0]
    findings = []
    def finding(check, status, detail):
        findings.append(ConsistencyFinding(check, status, detail))
    mismatches = []
    a, b = {j.name: j for j in urdf.joints}, {j.name: j for j in mjcf.joints}
    if set(a) != set(b):
        mismatches.append('joint sets differ')
    for name in sorted(set(a) & set(b)):
        x, y = a[name], b[name]
        if x.kind != y.kind or any(abs(v-w) > 1e-6 for v,w in zip(x.axis,y.axis)):
            mismatches.append(name + ': type/axis differs')
        if max(abs(x.lower-y.lower), abs(x.upper-y.upper)) > 1e-6:
            mismatches.append(name + ': physical limits differ')
    finding('joint_metadata', 'incompatible' if mismatches else 'supported',
            '; '.join(mismatches) or 'Named scalar sets, axes/types/limits agree within 1e-6; native order maps by name.')
    finding('joint_order', 'supported', json.dumps({rep: [s.native_joint_names.index(n) for n in s.joint_names]
             for rep,s in [('urdf',urdf),('mjcf',mjcf)]}))
    for u,m in pairs:
        if u.joint_names != m.joint_names or u.pose_values != m.pose_values or u.root_pose != m.root_pose:
            finding('poses', 'incompatible', u.pose_name + ': expanded named poses/root differ')
    hashes = tuple(sorted({(f.relative_path,f.sha256) for pair in pairs for s in pair for f in s.files}))
    identities = tuple(s.identity for pair in pairs for s in pair)
    runtime = 'unavailable'
    policy_path = catalog / definition_id / 'consistency.json'
    policy_hash = hashlib.sha256(policy_path.read_bytes()).hexdigest() if policy_path.exists() else ''
    if runtime_python is None:
        for check in ('named_frames','inertial_totals','visual_geometry_equality','collision_policy','collision_geometry_equality'):
            finding(check,'unverified','Supply runtime_python with existing MuJoCo; no simulator imported.')
    else:
        requests = []
        for pair in pairs:
            requests.append([dict(representation=s.representation, model=str(s.model_path),
                root=s.conventions.root_frame, names=s.joint_names, values=s.pose_values,
                translation=s.root_pose.translation, quaternion=s.root_pose.quaternion) for s in pair])
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
        try:
            result = subprocess.run([str(runtime_python), str(Path(__file__).with_name('_consistency_worker.py'))],
                input=json.dumps(requests), text=True, capture_output=True, env=env, timeout=120)
        except (OSError,subprocess.TimeoutExpired) as error:
            result = subprocess.CompletedProcess([],1,stderr=str(error))
        for pair in pairs:
            for selection in pair:
                for source in selection.files:
                    if hashlib.sha256(source.path.read_bytes()).hexdigest() != source.sha256:
                        raise RobotSelectionError('Source changed during comparison: '+str(source.path))
        if result.returncode:
            finding('runtime','unverified',result.stderr[-4000:])
            for check in ('named_frames','inertial_totals','visual_geometry_equality','collision_policy','collision_geometry_equality'):
                finding(check,'unverified','Runtime compilation/comparison unavailable.')
        else:
            output = json.loads(result.stdout)
            runtime = output['runtime']
            policy_path = catalog / definition_id / 'consistency.json'
            policy = read_json(policy_path) if policy_path.exists() else {}
            actual = {rep: next(f.sha256 for f in s.files if f.path == s.model_path)
                      for rep,s in [('urdf',urdf),('mjcf',mjcf)]}
            closure = {rep: hashlib.sha256(json.dumps(sorted((f['path'], f['sha256'])
                for f in definition['representations'][rep]['files']),separators=(',',':')).encode()).hexdigest()
                for rep in ('urdf','mjcf')}
            known = (policy.get('schema_version') == 1 and policy.get('model_sha256') == actual
                     and policy.get('closure_sha256') == closure
                     and policy.get('source_revision') == urdf.source_revision)
            for pose, observation in zip(poses, output['poses'], strict=True):
                for check in ('named_frames','inertial_totals','visual_geometry_equality','collision_policy','collision_geometry_equality'):
                    record = observation[{'visual_geometry_equality':'visuals','collision_policy':'collisions','collision_geometry_equality':'collisions'}.get(check,check)]
                    status = ('unverified' if not record.get('verified', True) else
                              'supported' if record['matches'] else 'incompatible')
                    detail = pose + ': ' + json.dumps(record, sort_keys=True)
                    if not record['matches'] and check == 'collision_policy' and known and policy.get('collision_differences'):
                        status = 'supported'
                        detail += '; Exact pinned pair has enumerated intentional differences: ' + '; '.join(policy['collision_differences'])
                    finding(check,status,detail)
            finding('import_conventions','supported',output['import_conventions'])
    return ConsistencyReport(definition_id,tuple(poses),tuple(findings),identities,hashes,runtime,policy_sha256=policy_hash)
