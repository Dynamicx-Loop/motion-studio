"""Owned explicit-stage UMR execution contract; heavy imports stay in its worker."""
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
import subprocess


STAGES = ('sampling', 'training', 'binding', 'retargeting')
PIN = 'd1cdaedaf67a827198da71c5fa831f48b2e51f91'
CHECKOUT = Path('/data/workspace/motion_studio/externals/UMR')


def canonical_hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


@dataclass(frozen=True)
class ExecutionSettings:
    sampling_seed: int = 0
    epochs: int = 500
    trajectory_filter: str = 'LQR'

    @classmethod
    def from_dict(cls, value=None):
        from motion_studio.studio._contracts import StudioError
        value = {} if value is None else value
        if not isinstance(value, dict) or set(value) - {'sampling_seed', 'epochs', 'trajectory_filter'}:
            raise StudioError('invalid_settings', 'Only sampling_seed, epochs and trajectory_filter are supported')
        result = cls(**value)
        for name, lo, hi in (('sampling_seed', 0, 2**31-10000), ('epochs', 1, 10000)):
            number = getattr(result, name)
            if type(number) is not int or not lo <= number <= hi:
                raise StudioError('invalid_settings', f'{name} must be an integer in [{lo}, {hi}]')
        if result.trajectory_filter not in ('LQR', 'none'):
            raise StudioError('invalid_settings', 'trajectory_filter must be LQR or none')
        return result

    @property
    def native_filter(self):
        return 'lqr' if self.trajectory_filter == 'LQR' else 'off'


class NativeStages:
    """Concrete independent-runtime adapter. Requests/results contain JSON values only."""
    def __init__(self, checkout=CHECKOUT, python=None):
        self.checkout = Path(checkout).resolve()
        self.python = Path(python) if python else self.checkout / '.venv/bin/python'

    def readiness(self):
        from motion_studio.studio._history import digest
        try:
            revision = subprocess.check_output(['git', '-C', str(self.checkout), 'rev-parse', 'HEAD'], text=True).strip()
            changed = subprocess.check_output(['git', '-C', str(self.checkout), 'diff', '--name-only', 'HEAD'], text=True).strip()
            if revision != PIN or changed:
                raise ValueError('Pinned UMR source revision or tracked bytes changed')
            result = subprocess.run([str(self.python), '-B', '-u', str(Path(__file__).with_name('_umr_stage_worker.py')), 'probe', str(self.checkout)],
                                    capture_output=True, text=True, timeout=45)
            if result.returncode:
                raise ValueError(result.stderr[-2000:] or 'Runtime probe failed')
            runtime = json.loads(result.stdout)
            if not runtime['cuda']:
                raise ValueError('CUDA unavailable; native sampling/training/retargeting requires host GPU access')
            paths = ['humanoid_retarget_defaults.json', 'robot_configs/humanoid_retarget_unitree_g1_example.json',
                     'assets/smplx_parts_segm.pkl']
            paths += [str(p.relative_to(self.checkout)) for p in sorted((self.checkout / 'scripts').glob('*.py'))]
            identity = {'pin': revision, 'native_files': {p: digest(self.checkout / p) for p in paths},
                        'adapter_files': {p.name: digest(p) for p in sorted(Path(__file__).parent.glob('*umr_stage*.py'))},
                        'runtime': runtime}
            return {'ready': True, 'identity': identity, 'message': runtime['gpu']}
        except (OSError, ValueError, KeyError, subprocess.SubprocessError) as error:
            return {'ready': False, 'message': str(error)}

    def capture(self, studio, run):
        """Verify immutable managed input closures; originals never reach native loaders."""
        from motion_studio.studio._history import digest
        robot = studio.get_robot(run.robot_asset_id)
        pose = studio.get_robot_pose(run.robot_asset_id, run.robot_pose_id)
        motion = studio.get_motion(run.motion_asset_id)
        files = {name: str(studio.robot_file(robot.asset_id, name)) for name in robot.files}
        motion_path = studio.motion_file(motion.asset_id)
        # G1-specific limits apply only to byte-verified official G1 source closure.
        official = self.checkout / 'assets/g1'
        g1 = robot.source_entry == 'g1_29dof.xml'
        for name, path in files.items():
            if not name.startswith('source/') or name == 'source/__studio_model.xml':
                continue
            original = official / name.removeprefix('source/')
            g1 = g1 and original.is_file() and digest(original) == digest(Path(path))
        return {'robot': asdict(robot), 'pose': asdict(pose), 'motion': asdict(motion),
                'motion_file': str(motion_path), 'motion_sha256': digest(motion_path),
                'robot_files': files, 'official_g1': bool(g1)}

    def command(self, request_file):
        return [str(self.python), '-B', '-u', str(Path(__file__).with_name('_umr_stage_worker.py')),
                'run', str(self.checkout), str(request_file)]
