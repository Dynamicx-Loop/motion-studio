const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const web = path.join(__dirname, '../motion_studio/studio/web');
const moduleURL = source => 'data:text/javascript;base64,' + Buffer.from(source).toString('base64');
const bridgeURL = moduleURL(fs.readFileSync(path.join(web, 'stage-inspection/bridge.js'), 'utf8'));
const flush = async () => {for (let i = 0; i < 5; i++) await Promise.resolve();};
class Element {
  constructor(tag = 'input') {
    this.tagName = tag.toUpperCase(); this.children = []; this.dataset = {}; this.style = {};
    this.attributes = {}; this._text = ''; this.value = ''; this.checked = false; this.disabled = false;
    this.min = ''; this.max = ''; this.step = ''; this.childNodes = [];
  }
  set textContent(value) {this._text = String(value); this.children = [];}
  get textContent() {return this._text + this.children.map(child => child.textContent).join('');}
  append(...children) {this.children.push(...children);}
  replaceChildren(...children) {this._text = ''; this.children = children;}
  setAttribute(key, value) {this.attributes[key] = value;}
  getAttribute(key) {return this.attributes[key];}
  closest() {return null;}
  get options() {return this.children;}
  dispatchEvent(event) {this[`on${event.type}`]?.(event);}
  click() {if (!this.disabled) this.onclick?.();}
}
const all = element => [element, ...element.children.flatMap(all)];
(async () => {
  const {inspectionBridge, inspectionGroups, inspectionChannel:channel} = await import(bridgeURL);
  const controls = Object.fromEntries(inspectionGroups.flatMap(([, ids]) => ids).map(id => [id, new Element()]));
  for (const id of ['play','back-frame','next-frame','previous','next','front','rear','side']) {
    controls[id].tagName = 'BUTTON'; controls[id].textContent = id;
  }
  for (const id of ['loop','center','reference','xray','surfaces','lines']) controls[id].type = 'checkbox';
  for (const id of ['slot','frame','timeline']) {controls[id].type = 'number'; controls[id].value = '0'; controls[id].max = '99';}
  for (const id of ['speed','segment']) {
    controls[id].tagName = 'SELECT';
    controls[id].children = ['all', 'arm'].map(value => Object.assign(new Element('option'), {value, textContent:value}));
    controls[id].value = 'all';
  }
  for (const id of ['title','summary','comparison','scope','loading','time','info','error','legend']) controls[id] = new Element('p');
  controls.title.textContent = 'Motion inspection'; controls.info.textContent = 'Slot 0';
  let frame = 0, clicks = 0;
  controls.play.onclick = () => {clicks++; controls.play.textContent = clicks % 2 ? 'Pause' : 'Play';};
  controls.frame.oninput = () => {frame = Math.min(99, Math.max(0, +controls.frame.value)); controls.frame.value = String(frame);};
  controls.slot.oninput = () => {controls.info.textContent = `Slot ${controls.slot.value}`;};
  const messages = [], listeners = {};
  const origin = 'http://127.0.0.1:8773';
  const parent = {postMessage:(message, target) => messages.push({message, target})};
  const view = {location:{href:origin + '/stage-inspection/index.html?bundle=%2Finspection%2Frun%2Frev%2Fmotion%2Findex.html&session=one',
    origin, search:'?bundle=%2Finspection%2Frun%2Frev%2Fmotion%2Findex.html&session=one'}, parent,
    addEventListener:(name, callback) => listeners[name] = callback};
  let embedded = false;
  const doc = {getElementById:id => controls[id], documentElement:{classList:{add:() => embedded = true}}};
  const bridge = inspectionBridge(view, doc); await flush();
  assert.equal(embedded, true);
  assert.equal(messages.at(-1).message.ready, false, 'initial state cannot issue commands while loading');
  assert.equal(bridge.resource('human/chunk.bin'), origin + '/inspection/run/rev/motion/human/chunk.bin');
  assert.throws(() => bridge.resource('../secret.bin'), /escapes/);
  assert.throws(() => bridge.resource('https://remote.example/chunk.bin'), /escapes/);
  const command = (id, extra = {}, envelope = {}) => listeners.message({source:parent, origin,
    data:{channel, type:'command', session:'one', id, ...extra}, ...envelope});
  command('play'); assert.equal(clicks, 0);
  bridge.ready(); await flush();
  command('play', {}, {origin:'https://remote.example'});
  command('play', {}, {source:{}});
  command('play', {}, {data:{channel, type:'command', session:'old', id:'play'}});
  command('unknown'); assert.equal(clicks, 0, 'foreign source/origin/session/unknown controls are ignored');
  command('play'); await flush(); assert.equal(clicks, 1);
  assert.equal(messages.at(-1).message.controls.play.textContent, undefined);
  assert.equal(messages.at(-1).message.controls.play.text, 'Pause', 'renderer owns updated playback state');
  command('frame', {value:'71'}); await flush(); assert.equal(frame, 71);
  command('frame', {value:'nonsense'}); assert.equal(frame, 71);
  command('slot', {value:'17'}); await flush(); assert.equal(messages.at(-1).message.text.info, 'Slot 17');
  command('segment', {value:'missing'}); assert.equal(controls.segment.value, 'all');
  command('segment', {value:'arm'}); assert.equal(controls.segment.value, 'arm');
  controls.lines.disabled = true; command('lines', {checked:true}); assert.equal(controls.lines.checked, false, 'sampling restrictions stay renderer-owned');
  command('surfaces', {checked:true}); assert.equal(controls.surfaces.checked, true);
  assert.ok(messages.every(item => item.target === origin));
  const standalone = inspectionBridge({...view, location:{...view.location, search:''}}, doc);
  assert.equal(standalone.embedded, false);
  assert.throws(() => inspectionBridge({...view, location:{...view.location, search:'?bundle=https://remote.example/index.html&session=x'}}, doc), /Invalid/);

  const roots = {'inspection-properties':new Element('section'), inspection:new Element('iframe')};
  const posted = [], parentListeners = {};
  roots.inspection.contentWindow = {postMessage:(message,target) => posted.push({message,target})};
  global.window = {addEventListener:(name, callback) => parentListeners[name] = callback};
  global.location = {origin};
  global.document = {getElementById:id => roots[id] || Object.values(roots).flatMap(all).find(element => element.id === id),
    createElement:tag => new Element(tag), createTextNode:text => Object.assign(new Element('#text'), {textContent:text})};
  const propertiesURL = moduleURL(fs.readFileSync(path.join(web,'inspection-properties.js'),'utf8').replace('./stage-inspection/bridge.js', bridgeURL));
  const {showInspectionProperties} = await import(propertiesURL);
  const source = showInspectionProperties('/inspection/run/rev/motion/index.html');
  const session = new URL(source, origin).searchParams.get('session');
  const state = {...messages.at(-1).message, session};
  const receive = (data = state, envelope = {}) => parentListeners.message({source:roots.inspection.contentWindow, origin, data, ...envelope});
  receive(state, {origin:'https://remote.example'});
  assert.equal(document.getElementById('inspection-control-frame'), undefined);
  receive();
  const input = document.getElementById('inspection-control-frame');
  assert.equal(input.value, '71');
  input.value = '72'; input.oninput();
  assert.equal(posted.at(-1).message.id, 'frame'); assert.equal(posted.at(-1).message.value, '72');
  receive({...state, controls:{...state.controls, frame:{...state.controls.frame, value:'73'}}});
  assert.equal(document.getElementById('inspection-control-frame'), input, 'playback state updates preserve the control DOM and focus');
  assert.equal(input.value, '73');
  receive({...state, controls:{...state.controls, play:{...state.controls.play, disabled:true}, frame:{...state.controls.frame, disabled:true}}});
  assert.equal(document.getElementById('inspection-control-play').disabled, true);
  assert.match(document.getElementById('inspection-property-status').textContent, /Static reference pose/);
  const playback = roots['inspection-properties'].children.find(element => element.children[0]?.textContent === 'Playback');
  assert.equal(playback.hidden, true, 'static stages prioritize useful segment/binding controls');
  receive(state); assert.equal(playback.hidden, false, 'moving stages retain playback controls');
  const reload = showInspectionProperties('/inspection/run/rev/motion/index.html', {reload:true});
  const reloadSession = new URL(reload, origin).searchParams.get('session');
  assert.notEqual(reloadSession, session, 'reload creates a distinct renderer navigation');
  receive(state); assert.equal(document.getElementById('inspection-control-frame'), undefined);
  receive({...state, session:reloadSession, ready:false, text:{...state.text, loading:'', error:'Cannot load source chunk'}});
  assert.equal(document.getElementById('inspection-control-play').disabled, true);
  assert.match(document.getElementById('inspection-property-error').textContent, /Cannot load source chunk/);
  showInspectionProperties('/inspection/other/rev/binding/index.html');
  receive(state); assert.equal(document.getElementById('inspection-control-frame'), undefined, 'late old-stage state cannot recreate controls');
  showInspectionProperties(undefined); receive(state); assert.equal(roots['inspection-properties'].hidden, true);
  assert.equal(posted.length, 1, 'state sync and switching never launch operations');
  console.log('Renderer command/state synchronization, input persistence, stale sessions, disabled restrictions and resource confinement passed');
})().catch(error => {console.error(error); process.exitCode = 1;});
