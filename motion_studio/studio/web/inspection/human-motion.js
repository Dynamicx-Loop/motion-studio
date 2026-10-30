// Bounded, read-only cache of human vertex chunks. The caller commits both
// human and robot to a new frame only after its source chunk is available.
export function humanMotion(meta, binary) {
  const cache = new Map();
  const index = frame => Math.floor(frame / meta.chunk_size);
  let pinned = 0;
  function entry(frame) {return cache.get(index(frame));}
  async function load(frame) {
    const i = index(frame), chunk = meta.chunks[i];
    if (!chunk || frame < 0 || frame >= meta.frame_count) throw Error('Human frame out of range');
    if (cache.has(i)) {const value = cache.get(i); cache.delete(i); cache.set(i, value); return value.promise;}
    const value = {};
    value.promise = binary(chunk.file, Int16Array, chunk.count * meta.vertex_count * 3)
      .then(data => {value.data = data; return data;})
      .catch(error => {if (cache.get(i) === value) cache.delete(i); throw error;});
    cache.set(i, value);
    while (cache.size > 3) cache.delete([...cache.keys()].find(key => key !== pinned));
    return value.promise;
  }
  function vertices(frame) {
    const chunk = meta.chunks[index(frame)], data = entry(frame)?.data;
    if (!data) return null;
    const start = (frame - chunk.start) * meta.vertex_count * 3;
    return data.subarray(start, start + meta.vertex_count * 3);
  }
  function prefetch(frame) {
    const next = (index(frame) + 1) % meta.chunks.length;
    load(meta.chunks[next].start).catch(() => {}); // A demanded load reports errors.
  }
  return {load, vertices, prefetch, pin(frame) {pinned = index(frame);}};
}
