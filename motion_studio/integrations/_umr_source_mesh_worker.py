"""Bounded CPU SMPL-X source mesh export; no robot or retargeting operations."""
import json
from pathlib import Path
import sys

try:
    from ._umr_studio_human import encode_root_relative
except ImportError:  # Direct worker invocation in the independent native runtime.
    from _umr_studio_human import encode_root_relative


def export_mesh(request, output, common, np):
    collection, _ = common.load_motion_collection(Path(request['motion']))
    _, sequence = common.select_sequence(collection, None, 0)
    count = common.sequence_frame_count(sequence)
    if (count != request['frame_count'] or not 1 <= count <= 20000
            or abs(float(sequence['fps']) - request['fps']) > 1e-6):
        raise ValueError('Source mesh requires exact managed frames and FPS')
    chunks, roots = [], []
    topology = None
    lower, upper = np.full(3, np.inf), np.full(3, -np.inf)
    max_error = 0.
    for start in range(0, count, 64):
        ids = np.arange(start, min(start + 64, count))
        vertices, joints, faces = common.source_motion_vertices_joints(
            sequence, ids, Path(request['model']), batch_size=32,
            smplx_device='cpu', smplx_batch_size=32, zero_source_finger_pose=True)
        vertices = common.source_points_to_retarget_frame(vertices, 'smplx', sequence.get('output_up', 'z'))
        joints = common.source_points_to_retarget_frame(joints, 'smplx', sequence.get('output_up', 'z'))
        if (vertices.ndim != 3 or vertices.shape[0] != len(ids) or vertices.shape[2] != 3
                or not 1 <= vertices.shape[1] <= 20000
                or joints.ndim != 3 or joints.shape[0] != len(ids) or joints.shape[1] < 22 or joints.shape[2] != 3
                or not np.isfinite(vertices).all() or not np.isfinite(joints).all()
                or faces.ndim != 2 or faces.shape[1] != 3 or not 1 <= len(faces) <= 40000
                or faces.dtype.kind not in 'iu' or faces.min() < 0 or faces.max() >= vertices.shape[1]):
            raise ValueError('Native source mesh returned invalid coordinates or topology')
        if topology is None:
            topology = faces.copy()
            vertex_count = vertices.shape[1]
            faces.astype('<u4').tofile(output / 'faces.bin')
        elif vertices.shape[1] != vertex_count or not np.array_equal(topology, faces):
            raise ValueError('Native source topology changed between frames')
        root = joints[:, 0]
        encoded = encode_root_relative(vertices, root, np)
        error = float(np.abs(encoded.astype(np.float64) * .0001 + root[:, None] - vertices).max())
        max_error = max(max_error, error)
        if error > 5.1e-5:
            raise ValueError('Source mesh quantization exceeds axis tolerance')
        name = f'vertices-{len(chunks):03d}.bin'
        encoded.tofile(output / name)
        chunks.append({'file': name, 'start': start, 'count': len(ids)})
        roots.extend(root.tolist())
        lower = np.minimum(lower, vertices.min(axis=(0, 1)))
        upper = np.maximum(upper, vertices.max(axis=(0, 1)))
        print(f'[SourceMesh] {start + len(ids)}/{count} frames', flush=True)
    payload = {'schema': 'motion-studio-source-mesh-v1', 'frame_count': count, 'fps': request['fps'],
               'vertex_count': vertex_count, 'face_count': len(topology), 'faces': 'faces.bin',
               'chunk_size': 64, 'chunks': chunks, 'root_positions': roots, 'quantization_m': .0001,
               'max_vertex_axis_error_m': max_error, 'ground_z': float(lower[2]),
               'bounds': {'min': lower.tolist(), 'max': upper.tolist()}, 'thumbnail_frame': 0,
               'encoding': 'int16 little endian; frame, vertex, xyz; root-relative Z-up metres',
               'coordinates': 'Z-up metres; original source translation; no resampling',
               'input_up_axis': sequence.get('output_up', 'z'), 'zero_source_finger_pose': True,
               'source_frame_start': 0, 'source_frame_stop_exclusive': count,
               'inputs_sha256': request['inputs_sha256'], 'source_revision': request['source_revision'],
               'scope': 'Source SMPL-X surface mesh; neutral hands; facial channels omitted. No robot solve.'}
    (output / 'manifest.json').write_text(json.dumps(payload, allow_nan=False, separators=(',', ':')))


def main(checkout, request_path, output):
    sys.path.insert(0, str(checkout / 'scripts'))
    import numpy as np
    import torch
    import smpl_surface_retarget_common as common
    torch.set_num_threads(2)
    export_mesh(json.loads(request_path.read_text()), output, common, np)


if __name__ == '__main__':
    main(*map(Path, sys.argv[1:4]))
