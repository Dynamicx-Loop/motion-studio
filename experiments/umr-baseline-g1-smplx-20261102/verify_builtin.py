"""Compare the built-in G1 selection with the fresh official baseline, CPU only."""
from dataclasses import asdict
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from motion_studio.studio import Studio


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    run = args.run.resolve()
    config = json.loads((run / 'resolved.json').read_text())
    studio = Studio(output / 'state')
    imported = studio.add_builtin_robot('g1')
    asset = studio.get_robot(imported['asset']['asset_id'])
    official = studio.official_robot_pose(asset.asset_id)
    assert tuple(official.qpos) == tuple(imported['pose']['qpos'])
    assert official.torso_body == config['robot']['point_cloud_center'].removeprefix('body:')
    source_files = {name.removeprefix('source/'): digest for name, digest in asset.files.items()
                    if name.startswith('source/') and name != 'source/__studio_model.xml'}
    closure = {}
    for name, digest in source_files.items():
        path = run / 'assets/g1' / name
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        assert actual == digest, name
        closure[name] = digest
    for joint in asset.joints:
        assert official.qpos[joint.qpos_index] == config['robot']['tpose_qpos'].get(joint.name, 0.)
    assert official.qpos[:7] == (0., 0., 0., 1., 0., 0., 0.)
    preview = studio.preview_robot(asset.asset_id, official.qpos)
    # Native runtime comparison remains inside its own interpreter; the public
    # import/preset operations above provide the independently selected model.
    result = {'selection': 'Studio.add_builtin_robot("g1")',
              'asset': asdict(asset), 'builtin_pose': imported['pose'],
              'official_pose': asdict(official), 'closure_sha256': closure,
              'source_closure_equal': True, 'named_scalar_pose_equal': True,
              'root_xyz_wxyz_equal': True, 'centering_equal': True,
              'runtime_preview': preview,
              'managed_model': str(studio.robot_file(asset.asset_id, 'source/__studio_model.xml')),
              'baseline_model': config['robot']['xml'],
              'limitations': ['Closure and pose equality do not establish hardware calibration or dynamics.']}
    (output / 'selection.json').write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print(output / 'selection.json')


if __name__ == '__main__':
    main()
