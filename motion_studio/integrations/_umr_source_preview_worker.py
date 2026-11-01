"""CPU source reconstruction only; never samples, trains, binds or retargets."""
import json
from pathlib import Path
import sys


def main(checkout, request_path, output):
    sys.path.insert(0, str(checkout / 'scripts'))
    import numpy as np
    import torch
    import smpl_surface_retarget_common as common
    torch.set_num_threads(2)
    request = json.loads(request_path.read_text())
    collection, _ = common.load_motion_collection(Path(request['motion']))
    _, sequence = common.select_sequence(collection, None, 0)
    count = common.sequence_frame_count(sequence)
    if count != request['frame_count'] or not 1 <= count <= 20000:
        raise ValueError('Source preview requires 1–20000 exact frames')
    if abs(float(sequence['fps']) - request['fps']) > 1e-6:
        raise ValueError('Preview FPS differs from managed metadata')
    frames = []
    floor = float('inf')
    for start in range(0, count, 64):
        ids = np.arange(start, min(start + 64, count))
        vertices, joints, _ = common.source_motion_vertices_joints(
            sequence, ids, Path(request['model']), batch_size=32,
            smplx_device='cpu', smplx_batch_size=32, zero_source_finger_pose=True)
        vertices = common.source_points_to_retarget_frame(vertices, 'smplx', sequence.get('output_up', 'z'))
        joints = common.source_points_to_retarget_frame(joints, 'smplx', sequence.get('output_up', 'z'))[:, :22]
        if joints.shape != (len(ids), 22, 3) or not np.isfinite(joints).all() or not np.isfinite(vertices).all():
            raise ValueError('Native source reconstruction returned invalid coordinates')
        floor = min(floor, float(vertices[:, :, 2].min()))
        frames.extend(joints.tolist())
    parents = [-1,0,0,0,1,2,3,4,5,6,7,8,9,9,9,12,13,14,16,17,18,19]
    payload = {'frame_count': count, 'fps': request['fps'], 'frames': frames,
               'parents': parents, 'ground_z': floor,
               'coordinates': 'Z-up metres; original source translation; no resampling',
               'scope': 'Source SMPL-X body joints; neutral hands; facial channels omitted. No robot solve.'}
    output.write_text(json.dumps(payload, allow_nan=False, separators=(',', ':')))


if __name__ == '__main__':
    main(*map(Path, sys.argv[1:4]))
