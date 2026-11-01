const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

class Element {
  constructor(tag = 'div') {
    this.tagName = tag.toUpperCase(); this.children = []; this.dataset = {};
    this.style = {}; this.hidden = false; this.value = ''; this.checked = false;
    this.classList = {add() {}, remove() {}};
  }
  set textContent(value) {this.text = String(value); this.children = [];}
  get textContent() {return (this.text || '') + this.children.map(child => child.textContent).join('');}
  append(...children) {this.children.push(...children);}
  replaceChildren(...children) {this.text = ''; this.children = children;}
  setAttribute() {}
  addEventListener() {}
  scrollIntoView() {}
  contains() {return false;}
  click() {if (!this.disabled) return this.onclick?.();}
}
const all = element => [element, ...element.children.flatMap(all)];
const ids = ['builtin-robots', 'sample-motions', 'asset-status', 'inspection', 'viewport',
  'robot-upload-files', 'robot-upload-folder', 'upload-robot', 'upload-entry',
  'upload-summary', 'robot-zip-entry', 'upload-derive'];
const roots = Object.fromEntries(ids.map(id => [id, new Element()]));
const details = new Element(), robotsTab = new Element('button');
global.document = {
  getElementById:id => roots[id], createElement:tag => new Element(tag),
  querySelector:selector => selector === '.upload-details' ? details : robotsTab,
  querySelectorAll:selector => selector === '.motion-card[data-managed-id]'
    ? all(roots['sample-motions']).filter(node => node.dataset.managedId) : []
};
global.FileReader = class {
  readAsDataURL() {this.result = 'data:application/xml;base64,PHhtbC8+'; this.onload();}
};
const moduleURL = source => 'data:text/javascript;base64,' + Buffer.from(source).toString('base64');
const deferred = () => {
  let resolve;
  const promise = new Promise(done => {resolve = done;});
  return {promise, resolve};
};
const flush = async () => {for (let i = 0; i < 15; i++) await Promise.resolve();};
const findButton = (root, label) => all(root).find(node => node.tagName === 'BUTTON' && node.textContent === label);
const robot = {asset:{asset_id:'robot'}, pose:{name:'Reference', qpos:[0], torso_body:'base'}};

(async () => {
  const web = path.join(__dirname, '../motion_studio/studio/web');
  global.previews = [];
  const preview = moduleURL('export const hideSourcePreview=()=>{}; export async function showSourcePreview(value){globalThis.previews.push(await value.asset);}');
  const thumbnails = moduleURL('export const resetMotionThumbnails=()=>{}; export const motionThumbnail=()=>document.createElement("img");');
  const library = moduleURL(fs.readFileSync(path.join(web, 'motion-library.js'), 'utf8'));
  const source = fs.readFileSync(path.join(web, 'assets.js'), 'utf8')
    .replace('./source-preview.js', preview).replace('./motion-thumbnails.js', thumbnails).replace('./motion-library.js', library);
  const {renderAssets} = await import(moduleURL(source));
  const calls = [], errors = [], refreshes = [];
  let handler;
  const api = async (url, data) => {calls.push({url, data}); return handler(url, data);};
  const draft = (id, revision = 'r1') => ({run_id:id, revision_id:revision, is_latest:true, read_only:false, motion_asset_id:null, stages:[]});
  function render(run, catalog = {robots:[{id:'g1', name:'G1', available:true}], motions:[]}, motions = []) {
    renderAssets({run, state:{catalog, motions}, api, failure:error => errors.push(error.message),
      refresh:async stage => refreshes.push(stage)});
  }

  // An asset can finish importing after navigation, but must never edit the new draft.
  const imported = deferred(); handler = () => imported.promise;
  render(draft('A'));
  const adding = findButton(roots['builtin-robots'], 'Add robot').click(); await flush();
  render(draft('B')); imported.resolve(robot); await adding;
  assert.deepEqual(calls.map(call => call.url), ['/api/catalog/robots']);
  assert.match(errors.at(-1), /Selection changed/);
  assert.equal(refreshes.length, 0);

  // Staying on the same revision (including rerenders) keeps the intended action usable.
  calls.length = 0;
  const stable = deferred(); handler = url => url === '/api/catalog/robots' ? stable.promise : {};
  render(draft('A'));
  const successful = findButton(roots['builtin-robots'], 'Add robot').click();
  render(draft('A')); stable.resolve(robot); await successful;
  assert.deepEqual(calls.map(call => call.url), ['/api/catalog/robots', '/api/runs/A/robot-pose']);
  assert.deepEqual(refreshes, ['preparation']);

  // A newer revision of the same run also invalidates an outstanding mutation.
  calls.length = 0;
  const revised = deferred(); handler = () => revised.promise;
  render(draft('A'));
  const revisionRace = findButton(roots['builtin-robots'], 'Add robot').click();
  render(draft('A', 'r2')); revised.resolve(robot); await revisionRace;
  assert.deepEqual(calls.map(call => call.url), ['/api/catalog/robots']);

  // Creating a draft from a read-only run cannot steal a later selection.
  calls.length = 0;
  const created = deferred(); handler = url => url === '/api/catalog/robots' ? robot : created.promise;
  render({...draft('history'), read_only:true});
  const creating = findButton(roots['builtin-robots'], 'Add robot').click(); await flush();
  render(draft('B')); created.resolve(draft('new')); await creating;
  assert.deepEqual(calls.map(call => call.url), ['/api/catalog/robots', '/api/runs']);

  // Sample resolution and uploaded robot import obey the same navigation guard.
  calls.length = 0;
  const motion = deferred(); handler = () => motion.promise;
  const catalog = {robots:[], motions:[{id:'sample-race', name:'Sample', available:true}]};
  render(draft('A'), catalog);
  const choosing = findButton(roots['sample-motions'], 'Use for retargeting').click();
  render(draft('B'), catalog); motion.resolve({asset_id:'motion'}); await choosing;
  assert.deepEqual(calls.map(call => call.url), ['/api/catalog/motions']);

  calls.length = 0;
  const uploaded = deferred(); handler = () => uploaded.promise;
  render(draft('A'));
  await roots['robot-upload-files'].onchange({target:{files:[{name:'robot.xml', size:6}]}});
  roots['robot-zip-entry'].hidden = true; roots['upload-entry'].value = 'robot.xml';
  roots['upload-robot'].onsubmit({preventDefault() {}}); await flush();
  render(draft('B')); uploaded.resolve({asset_id:'uploaded', default_qpos:[0], root_body:'base'}); await flush();
  assert.deepEqual(calls.map(call => call.url), ['/api/robot-upload']);
  assert.match(errors.at(-1), /Selection changed/);

  // Managed cached previews stay reachable when the external sample is absent.
  calls.length = 0; handler = () => {throw Error('No upstream import should be needed');};
  const saved = {asset_id:'saved', name:'saved.npz', frame_count:90, fps:30};
  render(draft('A'), {robots:[], motions:[{id:'saved-sample', asset_id:'saved', available:false}]}, [saved]);
  const previewButton = findButton(roots['sample-motions'], 'Preview');
  assert.equal(previewButton.disabled, false);
  assert.equal(findButton(roots['sample-motions'], 'Use for retargeting').disabled, false);
  await previewButton.click();
  assert.equal(global.previews.at(-1).asset_id, 'saved');
  assert.deepEqual(calls, []);
  console.log('Asset navigation/revision races, stable selection, upload and offline saved previews passed');
})().catch(error => {console.error(error); process.exitCode = 1;});
