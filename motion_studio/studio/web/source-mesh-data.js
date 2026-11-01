import {humanMotion} from './human-motion.js';

// A fast scrub may request hundreds of chunks. Keep one transfer in flight and
// one latest queued request; discarded seeks never allocate a vertex buffer.
export function boundedChunkReader(binary) {
  let running = false, queued;
  async function read(request) {
    running = true;
    try {request.resolve(await binary(...request.args));}
    catch(error) {request.reject(error);}
    finally {
      running = false;
      if (queued) {const next = queued; queued = undefined; read(next);}
    }
  }
  return (...args) => new Promise((resolve, reject) => {
    const request = {args, resolve, reject};
    if (!running) read(request);
    else {queued?.reject(Error('Source mesh seek superseded')); queued = request;}
  });
}

// Exact source frames; only three quantized chunks are retained per open clip.
export function validateSourceMesh(meta) {
  if (meta.schema !== 'motion-studio-source-mesh-v1'
      || !Number.isFinite(meta.fps) || meta.fps <= 0
      || !Number.isFinite(meta.quantization_m) || meta.quantization_m <= 0
      || !Number.isInteger(meta.face_count) || meta.face_count < 1
      || !Array.isArray(meta.root_positions) || meta.root_positions.length !== meta.frame_count
      || meta.root_positions.some(root => !Array.isArray(root) || root.length !== 3 || !root.every(Number.isFinite)))
    throw Error('Unsupported source mesh preview metadata');
  for (const file of [meta.faces, ...(meta.chunks || []).map(chunk => chunk.file)])
    if (typeof file !== 'string' || !/^[a-zA-Z0-9_.-]+$/.test(file)) throw Error('Invalid mesh preview file');
  return meta;
}

export async function loadSourceMesh(asset, api) {
  const record = await api(`/api/motions/${asset.asset_id}/mesh-preview`, {});
  const meta = validateSourceMesh(await api(record.url));
  const base = record.url.slice(0, record.url.lastIndexOf('/') + 1);
  async function binary(file, Type, length) {
    const response = await fetch(base + file);
    if (!response.ok) throw Error(`Source mesh data unavailable (${response.status})`);
    const buffer = await response.arrayBuffer();
    if (buffer.byteLength !== length * Type.BYTES_PER_ELEMENT) throw Error('Source mesh data has an unexpected length');
    return new Type(buffer);
  }
  const replay = humanMotion(meta, boundedChunkReader(binary));
  const [faces] = await Promise.all([binary(meta.faces, Uint32Array, meta.face_count * 3), replay.load(0)]);
  if (faces.some(index => index >= meta.vertex_count)) throw Error('Source mesh contains an invalid triangle');
  return {asset, meta, faces, replay};
}

export function sourcePositions(source, frame, centered = true) {
  const {meta, replay} = source, encoded = replay.vertices(frame);
  if (!encoded) throw Error('Source mesh frame is not loaded');
  const root = meta.root_positions[frame], first = meta.root_positions[0];
  const positions = new Float32Array(encoded.length);
  for (let i = 0; i < encoded.length; i++) {
    const axis = i % 3;
    positions[i] = encoded[i] * meta.quantization_m + root[axis] - (centered && axis < 2 ? root[axis] - first[axis] : 0);
  }
  return positions;
}
