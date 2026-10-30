import * as THREE from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {humanMotion} from './human-motion.js';
import {transformArrayType} from './robot-motion.js';
const $ = id => document.getElementById(id);
async function binary(path, Type, count) {
  const response = await fetch(path);
  if (!response.ok) throw Error(`Cannot load ${path}`);
  const array = new Type(await response.arrayBuffer());
  if (array.length !== count) throw Error(`Byte count mismatch: ${path}`);
  return array;
}
function geometry(vertices, faces) {
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.BufferAttribute(vertices, 3));
  g.setIndex(new THREE.BufferAttribute(faces, 1)); g.computeVertexNormals();
  return g;
}
try {
  const response = await fetch('bindings.json');
  if (!response.ok) throw Error('Cannot load bindings.json');
  const data = await response.json(), motion = data.motion, human = data.human_motion;
  const names = Object.keys(data.counts).sort();
  const color = name => new THREE.Color().setHSL((names.indexOf(name) * .61803398875) % 1, .75, .56);
  for (const name of names) $('segment').add(new Option(`${name} (${data.counts[name]})`, name));
  $('summary').textContent = `${data.run} · ${data.labels.length} paired slots · ${names.length} source segments`;
  $('slot').max = data.labels.length - 1;
  $('legend').replaceChildren(...names.map(name => {
    const row = document.createElement('div'); row.textContent = name;
    row.style.borderLeft = `8px solid #${color(name).getHexString()}`; row.style.paddingLeft = '7px'; return row;
  }));
  const scene = new THREE.Scene(); scene.background = new THREE.Color('#14202c');
  const renderer = new THREE.WebGLRenderer({antialias: true});
  renderer.setPixelRatio(Math.min(devicePixelRatio, 2)); document.body.append(renderer.domElement);
  const camera = new THREE.PerspectiveCamera(38, 1, .01, 50);
  const controls = new OrbitControls(camera, renderer.domElement); controls.enableDamping = true;
  scene.add(new THREE.HemisphereLight(0xffffff, 0x526375, 2));
  const light = new THREE.DirectionalLight(0xffffff, 2); light.position.set(2, 4, 4); scene.add(light);
  scene.add(new THREE.GridHelper(8, 32, 0x637485, 0x30404f));
  const material = new THREE.MeshStandardMaterial({color: 0x8c9bab, side: THREE.DoubleSide, roughness: .85});
  const surfaces = [], points = [], floors = [], offsets = [-1.05, 1.05];
  for (const [i, key] of ['human', 'robot'].entries()) {
    const meta = data.geometry[key];
    const [v, f] = await Promise.all([binary(meta.vertices, Float32Array, meta.vertex_count * 3), binary(meta.faces, Uint32Array, meta.face_count * 3)]);
    let floor = Infinity; for (let j = 1; j < v.length; j += 3) floor = Math.min(floor, v[j]); floors.push(floor);
    const mesh = new THREE.Mesh(geometry(v, f), material);
    mesh.position.set(offsets[i], -floor, 0); scene.add(mesh); surfaces.push(mesh);
    points.push((i === 0 ? data.source : data.target).map(p => [p[0] + offsets[i], p[1] - floor, p[2]]));
  }
  if (!motion) throw Error('This export has no motion. Re-export with the current view_umr_bindings.py.');
  if (!human || human.frame_count !== motion.frame_count || human.fps !== motion.fps) throw Error('Human and G1 timelines do not agree');
  const replay = humanMotion(human, binary);
  await replay.load(0); replay.prefetch(0);
  const humanReference = surfaces[0].geometry.getAttribute('position').array.slice();
  surfaces[0].geometry.getAttribute('position').setUsage(THREE.DynamicDrawUsage);
  $('comparison').textContent = `Human reference left · G1 right · source scale ${(human.source_scale * 100).toFixed(2)}%`;
  const pieces = motion.pieces;
  const [localVertices, localFaces, transforms] = await Promise.all([
    binary(motion.vertices, Float32Array, motion.vertex_count * 3),
    binary(motion.faces, Uint32Array, motion.face_count * 3),
    binary(motion.transforms, transformArrayType(motion), motion.frame_count * pieces.length * 12)
  ]);
  const robotGroup = new THREE.Group(); scene.add(robotGroup);
  const movingMeshes = pieces.map(piece => {
    const v = localVertices.slice(piece.vertex_start * 3, (piece.vertex_start + piece.vertex_count) * 3);
    const f = localFaces.slice(piece.face_start * 3, (piece.face_start + piece.face_count) * 3).map(i => i - piece.vertex_start);
    const mesh = new THREE.Mesh(geometry(v, f), material); mesh.matrixAutoUpdate = false;
    robotGroup.add(mesh); return mesh;
  });
  let dynamic = [], clouds = [], markers = [], lines = [], selected = [], selectedSlot = 0;
  let frame = 0, playing = false, cursor = 0, previousTime, loading = false, requestVersion = 0;
  $('frame').max = $('timeline').max = motion.frame_count - 1;
  function add(object) { scene.add(object); dynamic.push(object); return object; }
  function addLine(ids) {
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.BufferAttribute(new Float32Array(ids.length * 6), 3).setUsage(THREE.DynamicDrawUsage));
    const line = add(new THREE.LineSegments(g, new THREE.LineBasicMaterial({color: ids.length === 1 ? 0xffffff : 0x718799, depthTest: false})));
    lines.push({line, ids});
  }
  function refreshOverlay() {
    clouds.forEach((cloud, side) => {
      const attr = cloud.geometry.getAttribute('position');
      selected.forEach((id, j) => attr.setXYZ(j, ...points[side][id]));
      attr.needsUpdate = true; cloud.geometry.computeBoundingSphere();
      markers[side].position.set(...points[side][selectedSlot]);
    });
    for (const {line, ids} of lines) {
      const attr = line.geometry.getAttribute('position');
      ids.forEach((id, j) => {attr.setXYZ(j * 2, ...points[0][id]); attr.setXYZ(j * 2 + 1, ...points[1][id]);});
      attr.needsUpdate = true; line.geometry.computeBoundingSphere();
    }
    $('info').textContent = `Slot ${selectedSlot}\nSource: ${data.labels[selectedSlot]}\nTarget body: ${data.bodies[selectedSlot]}\nTarget mesh: ${data.meshes[selectedSlot]}\nGeom ID: ${data.geom_ids[selectedSlot]}\nReference projection: ${(data.projection_m[selectedSlot] * 1000).toFixed(3)} mm\nHuman displayed XYZ (m): ${points[0][selectedSlot].map(x => x.toFixed(3)).join(', ')}\nTarget displayed XYZ (m): ${points[1][selectedSlot].map(x => x.toFixed(3)).join(', ')}\nShown: ${selected.length} slots`;
  }
  function pose() {
    const reference = $('reference').checked;
    surfaces[0].visible = $('surfaces').checked;
    surfaces[1].visible = $('surfaces').checked && reference;
    robotGroup.visible = $('surfaces').checked && !reference;
    const humanGeometry = surfaces[0].geometry, attr = humanGeometry.getAttribute('position');
    if (reference) {
      attr.array.set(humanReference);
      surfaces[0].position.set(offsets[0], -floors[0], 0);
      data.source.forEach((p, i) => {points[0][i] = [p[0] + offsets[0], p[1] - floors[0], p[2]];});
      data.target.forEach((p, i) => {points[1][i] = [p[0] + offsets[1], p[1] - floors[1], p[2]];});
    } else {
      const encoded = replay.vertices(frame);
      if (!encoded) throw Error('Human frame was not loaded before committing playback');
      for (let i = 0; i < encoded.length; i++) attr.array[i] = encoded[i] * human.quantization_m;
      const root = human.root_positions[frame], firstRoot = human.root_positions[0];
      const shiftHuman = [offsets[0] + ($('center').checked ? 0 : root[0] - firstRoot[0]), root[1], $('center').checked ? 0 : root[2] - firstRoot[2]];
      surfaces[0].position.set(...shiftHuman);
      human.slot_vertices.forEach((vertices, i) => {
        for (let axis = 0; axis < 3; axis++) {
          points[0][i][axis] = shiftHuman[axis] + vertices.reduce((sum, vertex, corner) => sum + attr.array[vertex * 3 + axis] * human.slot_bary[i][corner], 0);
        }
      });
      const origin = $('center').checked ? motion.root_positions[frame] : motion.display_origin;
      const shift = [offsets[1] - origin[0], -motion.display_origin[1], -origin[2]];
      robotGroup.position.set(...shift);
      movingMeshes.forEach((mesh, i) => {
        const t = transforms.subarray((frame * pieces.length + i) * 12, (frame * pieces.length + i + 1) * 12);
        mesh.matrix.set(...t, 0, 0, 0, 1); mesh.matrixWorldNeedsUpdate = true;
      });
      motion.slot_local.forEach(([x, y, z], i) => {
        const start = (frame * pieces.length + motion.slot_piece[i]) * 12;
        for (let row = 0; row < 3; row++) {
          const j = start + row * 4;
          points[1][i][row] = transforms[j] * x + transforms[j + 1] * y + transforms[j + 2] * z + transforms[j + 3] + shift[row];
        }
      });
    }
    attr.needsUpdate = true; humanGeometry.computeVertexNormals();
    humanGeometry.computeBoundingBox(); humanGeometry.computeBoundingSphere();
    $('frame').value = $('timeline').value = frame;
    $('time').textContent = reference ? 'Reference pose · playback paused' : `Frame ${frame} / ${motion.frame_count - 1} · ${(frame / motion.fps).toFixed(2)} s · ${motion.fps.toFixed(3)} fps · source frame ${motion.frame_ids[frame]}`;
    refreshOverlay();
  }
  function update() {
    for (const o of dynamic) {scene.remove(o); o.geometry.dispose(); o.material.dispose();}
    dynamic = []; clouds = []; markers = []; lines = [];
    selected = data.labels.map((_, i) => i).filter(i => $('segment').value === 'all' || data.labels[i] === $('segment').value);
    selectedSlot = Math.max(0, Math.min(data.labels.length - 1, Math.trunc(+$('slot').value) || 0));
    if (!selected.includes(selectedSlot)) selectedSlot = selected[0]; $('slot').value = selectedSlot;
    for (let side = 0; side < 2; side++) {
      const g = new THREE.BufferGeometry();
      g.setAttribute('position', new THREE.BufferAttribute(new Float32Array(selected.length * 3), 3).setUsage(THREE.DynamicDrawUsage));
      g.setAttribute('color', new THREE.Float32BufferAttribute(selected.flatMap(i => color(data.labels[i]).toArray()), 3));
      const cloud = add(new THREE.Points(g, new THREE.PointsMaterial({size: .012, vertexColors: true, depthTest: !$('xray').checked})));
      cloud.renderOrder = 3; cloud.userData.ids = selected; clouds.push(cloud);
      const marker = add(new THREE.Mesh(new THREE.SphereGeometry(.018, 12, 8), new THREE.MeshBasicMaterial({color: 0xffffff, depthTest: false})));
      marker.renderOrder = 5; markers.push(marker);
    }
    if ($('lines').checked) addLine(selected.filter((_, i) => i % 32 === 0));
    addLine([selectedSlot]); pose();
  }
  function setPlaying(value) {
    playing = value; previousTime = undefined; cursor = frame;
    $('play').textContent = playing ? 'Pause' : 'Play';
  }
  function requestFrame(next) {
    const version = ++requestVersion;
    if (replay.vertices(next)) {
      loading = false; frame = next; replay.pin(frame); pose(); replay.prefetch(frame); $('loading').textContent = ''; return;
    }
    loading = true; $('loading').textContent = `Loading reference frame ${next}…`;
    replay.load(next).then(() => {
      if (version !== requestVersion) return;
      frame = next; replay.pin(frame); cursor = next; loading = false; previousTime = undefined;
      $('loading').textContent = ''; pose(); replay.prefetch(frame);
    }).catch(error => {
      if (version !== requestVersion) return;
      loading = false; setPlaying(false); $('loading').textContent = ''; $('error').textContent = error.message;
    });
  }
  function seek(value) {
    setPlaying(false); $('reference').checked = false;
    const next = Math.max(0, Math.min(motion.frame_count - 1, Math.trunc(+value) || 0)); cursor = next; requestFrame(next);
  }
  $('play').onclick = () => {
    $('reference').checked = false;
    if (frame === motion.frame_count - 1 && !playing) requestFrame(0);
    else pose();
    setPlaying(!playing);
  };
  for (const id of ['frame', 'timeline']) $(id).oninput = () => seek($(id).value);
  $('back-frame').onclick = () => seek(frame - 1); $('next-frame').onclick = () => seek(frame + 1);
  $('speed').onchange = () => {cursor = frame; previousTime = undefined;};
  $('reference').oninput = () => {requestVersion++; loading = false; $('loading').textContent = ''; setPlaying(false); pose();};
  for (const id of ['center', 'surfaces']) $(id).oninput = pose;
  for (const id of ['segment', 'slot', 'xray', 'lines']) $(id).addEventListener('input', update);
  for (const [id, step] of [['previous', -1], ['next', 1]]) $(id).onclick = () => {
    $('slot').value = selected[(selected.indexOf(selectedSlot) + step + selected.length) % selected.length]; update();
  };
  let viewMode = 'front';
  function view(which) {
    viewMode = which; scene.updateMatrixWorld(true);
    const bounds = new THREE.Box3().expandByObject(surfaces[0]);
    bounds.expandByObject($('reference').checked ? surfaces[1] : robotGroup);
    const center = bounds.getCenter(new THREE.Vector3()), size = bounds.getSize(new THREE.Vector3());
    const tangent = Math.tan(THREE.MathUtils.degToRad(camera.fov / 2));
    const width = which === 'side' ? size.z : size.x, depth = which === 'side' ? size.x : size.z;
    const distance = 1.15 * Math.max(width / (2 * tangent * camera.aspect), size.y / (2 * tangent)) + depth / 2;
    camera.position.copy(center).add(new THREE.Vector3(which === 'side' ? distance : 0, 0, which === 'rear' ? -distance : which === 'side' ? 0 : distance));
    controls.target.copy(center); camera.far = Math.max(50, distance * 3); camera.updateProjectionMatrix(); controls.update();
  }
  for (const id of ['front', 'rear', 'side']) $(id).onclick = () => view(id);
  const ray = new THREE.Raycaster(); ray.params.Points.threshold = .018; let down;
  renderer.domElement.addEventListener('pointerdown', e => down = [e.clientX, e.clientY]);
  renderer.domElement.addEventListener('pointerup', e => {
    if (!down || Math.hypot(e.clientX - down[0], e.clientY - down[1]) > 4) return;
    const rect = renderer.domElement.getBoundingClientRect();
    ray.setFromCamera(new THREE.Vector2((e.clientX - rect.left) / rect.width * 2 - 1, 1 - (e.clientY - rect.top) / rect.height * 2), camera);
    const hit = ray.intersectObjects(clouds)[0];
    if (hit) {$('slot').value = hit.object.userData.ids[hit.index]; update();}
  });
  addEventListener('keydown', e => {
    if (e.code === 'Space' && !['INPUT', 'SELECT', 'BUTTON'].includes(e.target.tagName)) {e.preventDefault(); $('play').click();}
  });
  document.addEventListener('visibilitychange', () => {previousTime = undefined;});
  function resize() {
    const w = Math.max(300, innerWidth - 280); renderer.setSize(w, innerHeight);
    renderer.domElement.style.marginLeft = '280px'; camera.aspect = w / innerHeight; view(viewMode);
  }
  addEventListener('resize', resize); update(); resize();
  $('loading').textContent = '';
  renderer.setAnimationLoop(now => {
    if (playing && previousTime !== undefined && !document.hidden && !loading) {
      cursor += (now - previousTime) / 1000 * motion.fps * +$('speed').value;
      if (cursor >= motion.frame_count) {
        if ($('loop').checked) cursor %= motion.frame_count;
        else {setPlaying(false); cursor = motion.frame_count - 1;}
      }
      const next = Math.floor(cursor);
      if (next !== frame) requestFrame(next);
    }
    previousTime = now; controls.update(); renderer.render(scene, camera);
  });
} catch (error) {$('error').textContent = error.stack || String(error);}
