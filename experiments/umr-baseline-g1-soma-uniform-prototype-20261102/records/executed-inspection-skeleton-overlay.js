// Two independently reconstructed, name-matched skeletons in the source mesh view.
export async function skeletonOverlay(scene, THREE, human, binary) {
  const meta = human.skeleton;
  const map = await (await fetch(meta.joint_map)).json();
  const frames = human.frame_count, joints = meta.joint_count;
  const arrays = await Promise.all([meta.fitted, meta.bvh].map(file => binary(file, Float32Array, frames * joints * 3)));
  const edges = map.parents.flatMap((p, j) => p >= 0 ? [[p, j]] : []);
  const lines = arrays.map((_, i) => {
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.BufferAttribute(new Float32Array(edges.length * 6), 3));
    const line = new THREE.LineSegments(g, new THREE.LineBasicMaterial({color: i ? 0x00e5ff : 0xffbf47, depthTest: false}));
    line.renderOrder = 8; scene.add(line); return line;
  });
  return (frame, shift, visible) => lines.forEach((line, side) => {
    line.visible = visible;
    if (!visible) return;
    const attr = line.geometry.getAttribute('position');
    edges.forEach((edge, e) => edge.forEach((j, k) => {
      const base = (frame * joints + j) * 3;
      attr.setXYZ(e * 2 + k, ...[0, 1, 2].map(a => arrays[side][base + a] + shift[a]));
    }));
    attr.needsUpdate = true; line.geometry.computeBoundingSphere();
  });
}
