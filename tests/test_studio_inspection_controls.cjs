const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

class Node {
  constructor(tag) {
    this.tagName = tag; this.children = []; this.dataset = {}; this.attributes = {};
    this._text = ''; this.hidden = false;
  }
  set textContent(value) { this._text = String(value); this.children = []; }
  get textContent() { return this._text + this.children.map(child => child.textContent).join(''); }
  set src(value) { this.attributes.src = value; }
  get src() { return this.attributes.src; }
  append(...nodes) { this.children.push(...nodes); }
  replaceChildren(...nodes) { this._text = ''; this.children = nodes; }
  setAttribute(key, value) { this.attributes[key] = value; }
  getAttribute(key) { return this.attributes[key]; }
  removeAttribute(key) { delete this.attributes[key]; }
}
const roots = Object.fromEntries(['inspection-tools', 'inspection', 'empty', 'inspection-properties'].map(id => [id, new Node('div')]));
global.window = {addEventListener() {}};
global.location = {origin:'http://127.0.0.1:8773'};
global.document = {
  getElementById:id => roots[id], createElement:tag => new Node(tag),
  createTextNode:text => Object.assign(new Node('#text'), {_text:text})
};
const all = node => [node, ...node.children.flatMap(all)];
const button = text => all(roots['inspection-tools']).find(node => node.tagName === 'button' && node.textContent === text);
const flush = async () => { for (let i = 0; i < 12; i++) await Promise.resolve(); };
const deferred = () => {
  let resolve, reject;
  const promise = new Promise((yes, no) => { resolve = yes; reject = no; });
  return {promise, resolve, reject};
};
const run = (overrides = {}) => ({
  run_id:'run1', revision_id:'r1', read_only:false,
  stages:['preparation', 'sampling', 'training', 'binding', 'retargeting', 'motion'].map(stage => ({stage, status:'available'})),
  ...overrides
});
const displayedBundle = () => roots.inspection.src?.startsWith('/stage-inspection/') ? new URL(roots.inspection.src, location.origin).searchParams.get('bundle') : roots.inspection.src;
const url = stage => `/inspection/run1/r1/${stage}/index.html`;

(async () => {
  const web = path.join(__dirname, '../motion_studio/studio/web');
  const moduleURL = source => 'data:text/javascript;base64,' + Buffer.from(source).toString('base64');
  const bridge = moduleURL(fs.readFileSync(path.join(web,'stage-inspection/bridge.js'),'utf8'));
  const properties = moduleURL(fs.readFileSync(path.join(web,'inspection-properties.js'),'utf8').replace('./stage-inspection/bridge.js',bridge));
  const source = fs.readFileSync(path.join(web,'inspection-ui.js'),'utf8').replace('./inspection-properties.js',properties);
  const {renderInspection} = await import(moduleURL(source));
  const requests = [];
  let handler;
  const api = async (path, data) => { requests.push({path, data}); return handler(path, data); };
  const render = (selectedStage, selectedRun = run()) => renderInspection({run:selectedRun, selectedStage, api});

  render('preparation'); await flush();
  assert.equal(requests.length, 0, 'preparation never starts an inspection build');
  assert.match(roots.empty.textContent, /Drop a robot or motion/);
  const cached = run({stages:[{stage:'training', status:'available', inspection_url:url('training')}]});
  render('training', cached); await flush();
  assert.equal(displayedBundle(), url('training'));
  assert.equal(roots.inspection.hidden, false);
  assert.equal(requests.length, 0, 'cached views display directly');

  const sampling = deferred(); handler = () => sampling.promise;
  render('sampling'); render('sampling'); await flush();
  assert.equal(requests.length, 1, 'repeated renders share a pending selected-stage build');
  assert.deepEqual(requests[0], {path:'/api/runs/run1/inspections/sampling', data:{revision_id:'r1'}});
  assert.match(roots.empty.textContent, /Loading sampling visualization/);
  assert.equal(roots.inspection.hidden, true);
  assert.equal(button('Export fresh standalone bundle'), undefined, 'loading needs no manual build click');
  render('training', cached);
  sampling.resolve({url:url('sampling'), path:'/export/sampling'}); await flush();
  assert.equal(displayedBundle(), url('training'), 'late stage completion cannot replace the selected view');
  render('sampling');
  assert.equal(displayedBundle(), url('sampling'), 'completed derivative is reused on returning to the stage');
  assert.match(roots['inspection-tools'].textContent, /Open standalone viewer/);
  assert.doesNotMatch(roots['inspection-tools'].textContent, /Standalone HTTP bundle|\/export\/sampling/, 'automatic viewing keeps bundle paths out of the viewport controls');

  const motion = deferred(); handler = () => motion.promise;
  render('motion'); await flush(); render('retargeting'); await flush();
  assert.equal(requests.length, 2, 'motion and retargeting share the native-stage build');
  assert.equal(requests[1].path, '/api/runs/run1/inspections/retargeting');
  motion.resolve({url:url('retargeting'), path:'/export/motion'}); await flush();
  assert.equal(displayedBundle(), url('retargeting'), 'alias selection receives the same completed view');

  handler = () => { throw Error('CPU reconstruction unavailable'); };
  render('binding'); await flush();
  assert.match(roots.empty.textContent, /Binding visualization unavailable: CPU reconstruction unavailable/);
  assert.ok(button('Retry stage visualization'));
  render('binding'); render('preparation'); render('binding'); await flush();
  assert.equal(requests.length, 3, 'failed automatic loading waits for an explicit retry');
  const retry = deferred(); handler = () => retry.promise;
  button('Retry stage visualization').onclick(); render('binding'); await flush();
  assert.equal(requests.length, 4, 'retry and rerender still produce one build');
  retry.resolve({url:url('binding'), path:'/export/binding'}); await flush();
  assert.equal(displayedBundle(), url('binding'));
  assert.equal(roots.empty.hidden, true);
  assert.ok(button('Export fresh standalone bundle'), 'standalone export remains separate after automatic loading');
  handler = () => { throw Error('Standalone export failed'); };
  button('Export fresh standalone bundle').onclick(); await flush();
  assert.equal(displayedBundle(), url('binding'), 'a failed standalone export preserves the current viewport');
  assert.ok(button('Retry standalone export'));

  const oldRevision = deferred(); handler = () => oldRevision.promise;
  render('training'); await flush();
  render('preparation', run({revision_id:'r2'}));
  oldRevision.resolve({url:url('training'), path:'/export/old'}); await flush();
  assert.equal(displayedBundle(), undefined, 'an old revision cannot repaint the new revision');
  assert.match(roots.empty.textContent, /Drop a robot or motion/);

  const before = requests.length;
  render('motion', run({run_id:'history', read_only:true, stages:[{stage:'motion', status:'available', inspection_url:'/inspection/history/index.html'}]}));
  assert.equal(displayedBundle(), '/inspection/history/index.html');
  assert.equal(roots['inspection-tools'].textContent, '');
  render('sampling', run({run_id:'waiting', stages:[{stage:'sampling', status:'running'}]})); await flush();
  assert.equal(requests.length, before, 'historical and unfinished stages launch no work');
  handler = () => ({url:'/inspection/waiting/r1/sampling/index.html'});
  render('sampling', run({run_id:'waiting'})); await flush();
  assert.equal(requests.length, before + 1, 'a selected stage loads when refreshed as available');
  assert.equal(displayedBundle(), '/inspection/waiting/r1/sampling/index.html');

  const exporting = deferred(); handler = () => exporting.promise;
  const cachedExport = run({run_id:'cached-export', stages:[{stage:'training', status:'available', inspection_url:'/inspection/cached-export/r1/training/index.html'}]});
  render('training', cachedExport);
  button('Export fresh standalone bundle').onclick(); await flush();
  // A refreshed stage can omit its URL while the request is in flight; preserve the loaded view.
  render('training', {...cachedExport, stages:[{stage:'training', status:'available'}]});
  assert.equal(roots.inspection.hidden, false, 'exporting a server-cached view keeps the iframe visible');
  assert.equal(displayedBundle(), '/inspection/cached-export/r1/training/index.html');
  assert.match(roots['inspection-tools'].textContent, /Exporting standalone bundle/);
  exporting.resolve({url:'/inspection/cached-export/r1/training/index.html', path:'/explicit/export'}); await flush();
  assert.match(roots['inspection-tools'].textContent, /Standalone HTTP bundle: \/explicit\/export/, 'explicit export reveals the resulting bundle path');
  assert.ok(requests.every(request => /\/inspections\//.test(request.path)), 'viewing never calls native execution or revision APIs');
  console.log('Automatic stage views, cached reuse, alias coalescing, local retry, export and stale-view guards passed');
})().catch(error => { console.error(error); process.exitCode = 1; });
