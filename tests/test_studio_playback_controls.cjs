const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const web = path.join(__dirname, '../motion_studio/studio/web');
const moduleURL = source => 'data:text/javascript;base64,' + Buffer.from(source).toString('base64');
const flush = async () => {for (let i = 0; i < 30; i++) await Promise.resolve();};

// Render primitives are inert; the shipped app, controls, cache and frame requests
// run unchanged so the assertions exercise actual user playback interactions.
class Vector {
  constructor(x = 0, y = 0, z = 0) {this.set(x, y, z);}
  set(x, y, z) {Object.assign(this, {x, y, z}); return this;}
  copy(value) {return this.set(value.x, value.y, value.z);}
  add() {return this;}
}
class Object3D {
  constructor(geometry, material) {
    this.geometry = geometry; this.material = material; this.position = new Vector();
    this.matrix = {set() {}}; this.userData = {};
  }
  add() {} remove() {} updateMatrixWorld() {} updateProjectionMatrix() {}
}
class Geometry {
  constructor() {this.attributes = {};}
  setAttribute(name, value) {this.attributes[name] = value;}
  getAttribute(name) {return this.attributes[name];}
  setIndex() {} computeVertexNormals() {} computeBoundingSphere() {} computeBoundingBox() {} dispose() {}
}
class Attribute {
  constructor(array) {this.array = array;}
  setUsage() {return this;}
  setXYZ(index, x, y, z) {this.array.set([x, y, z], index * 3);}
}
class Material {dispose() {}}
class Color {
  setHSL() {return this;} getHexString() {return 'ffffff';} toArray() {return [1, 1, 1];}
}
class Element {
  constructor() {this.value = '0'; this.checked = false; this.style = {}; this.children = []; this.textContent = '';}
  add(option) {this.children.push(option);}
  replaceChildren(...children) {this.children = children;}
  addEventListener() {} append() {}
  click() {this.onclick?.();}
}
const elements = new Map();
const $ = id => {if (!elements.has(id)) elements.set(id, new Element()); return elements.get(id);};
global.document = {getElementById:$, createElement:() => new Element(), body:new Element(), addEventListener() {}, hidden:false};
global.Option = class {constructor(text, value) {Object.assign(this, {textContent:text, value});}};
global.addEventListener = () => {};
global.devicePixelRatio = 1; global.innerWidth = 1280; global.innerHeight = 720;
$('segment').value = 'all'; $('speed').value = '1'; $('surfaces').checked = true;
let animate;
global.testThree = {
  Scene:Object3D, Group:Object3D, Mesh:Object3D, Points:Object3D, LineSegments:Object3D,
  HemisphereLight:Object3D, DirectionalLight:Object3D, GridHelper:Object3D,
  BufferGeometry:Geometry, SphereGeometry:Geometry, BufferAttribute:Attribute, Float32BufferAttribute:Attribute,
  MeshStandardMaterial:Material, MeshBasicMaterial:Material, PointsMaterial:Material, LineBasicMaterial:Material,
  Color, Vector3:Vector, Vector2:Vector,
  PerspectiveCamera:class extends Object3D {constructor(fov) {super(); this.fov = fov;}},
  Box3:class {
    expandByObject() {return this;}
    getCenter() {return new Vector();} getSize() {return new Vector(2, 2, 2);}
  },
  Raycaster:class {constructor() {this.params = {Points:{}};}},
  MathUtils:{degToRad:value => value * Math.PI / 180},
  WebGLRenderer:class {
    constructor() {this.domElement = new Element();}
    setPixelRatio() {} setSize() {} render() {}
    setAnimationLoop(callback) {animate = callback;}
  }
};
const count = 8, chunks = Array.from({length:4}, (_, index) => ({file:`chunk-${index}`, start:index * 2, count:2}));
const mesh = {vertices:'vertices', faces:'faces', vertex_count:3, face_count:1};
const data = {
  counts:{body:1}, labels:['body'], source:[[0, 0, 0]], target:[[0, 0, 0]],
  bodies:['base'], meshes:[null], geom_ids:[0], projection_m:[0], geometry:{human:mesh, robot:mesh},
  motion:{frame_count:count, fps:10, pieces:[], vertex_count:0, face_count:0,
    vertices:'robot-vertices', faces:'robot-faces', transforms:'transforms',
    slot_local:[[0, 0, 0]], slot_piece:[0], frame_ids:Array.from({length:count}, (_, i) => i),
    root_positions:Array.from({length:count}, () => [0, 0, 0]), display_origin:[0, 0, 0]},
  human_motion:{frame_count:count, fps:10, chunk_size:2, vertex_count:3, chunks,
    source_scale:1, quantization_m:.0001, slot_vertices:[[0, 1, 2]], slot_bary:[[1, 0, 0]],
    root_positions:Array.from({length:count}, () => [0, 0, 0])}
};
let delayFirst = false, releaseFirst;
const requests = [];
global.fetch = async url => {
  requests.push(url);
  if (url === 'bindings.json') return {ok:true, json:async () => data};
  if (url === 'chunk-0' && delayFirst) await new Promise(resolve => {releaseFirst = resolve;});
  const array = url.startsWith('chunk-') ? new Int16Array(18)
    : url === 'vertices' ? new Float32Array(9) : url === 'faces' ? new Uint32Array([0, 1, 2]) : new Float32Array();
  return {ok:true, arrayBuffer:async () => array.buffer};
};

(async () => {
  const three = moduleURL(Object.keys(global.testThree).map(name => `export const ${name}=globalThis.testThree.${name};`).join('\n'));
  const orbit = moduleURL('export class OrbitControls {constructor(){this.target={copy(){}};} update(){}}');
  const bridge = moduleURL('export const inspectionBridge=()=>({embedded:false,resource:value=>value,publish(){},ready(){}});');
  let source = fs.readFileSync(path.join(web, 'stage-inspection/app.js'), 'utf8')
    .replace("from 'three'", `from '${three}'`)
    .replace('three/addons/controls/OrbitControls.js', orbit).replace('./bridge.js', bridge);
  for (const [name, file] of [['human-motion.js', 'human-motion.js'], ['robot-motion.js', 'robot-motion.js'], ['playback.js', 'stage-inspection/playback.js']])
    source = source.replace(`./${name}`, moduleURL(fs.readFileSync(path.join(web, file), 'utf8')));
  await import(moduleURL(source));
  assert.equal($('error').textContent, '', 'viewer initializes without errors');
  assert.equal(typeof animate, 'function');
  const seek = async frame => {$('frame').value = String(frame); $('frame').oninput(); await flush();};
  await seek(2); await seek(4); delayFirst = true; await seek(7);
  assert.equal(Number($('frame').value), 7);
  $('loop').checked = false;
  $('play').click(); await flush();
  assert.equal(typeof releaseFirst, 'function', 'restart must reload the evicted first chunk');
  assert.match($('loading').textContent, /Loading source frame 0/);
  animate(1000); animate(1100);
  assert.equal(Number($('frame').value), 7, 'both tracks wait together for the restart chunk');
  releaseFirst(); await flush();
  assert.equal(Number($('frame').value), 0);
  animate(1200); animate(1300); await flush();
  assert.equal(Number($('frame').value), 1, 'nonlooping replay advances from the beginning');
  assert.equal($('play').textContent, 'Pause');
  animate(2100); await flush();
  assert.equal(Number($('frame').value), 7, 'nonlooping replay still stops exactly at the end');
  assert.equal($('play').textContent, 'Play');
  assert.equal($('error').textContent, '');
  assert.ok(requests.filter(url => url === 'chunk-0').length >= 2);
  console.log('Shipped viewer restarts after first-chunk eviction, waits atomically and stops at exact end');
})().catch(error => {console.error(error); process.exitCode = 1;});
