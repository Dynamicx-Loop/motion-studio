const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

// A small DOM fixture exercises the exported UI with real async request ordering.
class Node {
  constructor(tag) { this.tagName = tag; this.children = []; this.dataset = {}; this.attributes = {}; this._text = ''; this.disabled = false; this.hidden = false; }
  set textContent(text) { this._text = String(text); this.children = []; }
  get textContent() { return this._text + this.children.map(child => child.textContent).join(''); }
  append(...nodes) { this.children.push(...nodes); }
  replaceChildren(...nodes) { this._text = ''; this.children = nodes; }
  setAttribute(key, value) { this.attributes[key] = value; }
  checkValidity() { return this.valid !== false; }
  reportValidity() { return this.checkValidity(); }
}
const roots = Object.fromEntries(['execution', 'viewport-execution', 'active-job', 'logs', 'status'].map(id => [id, new Node('div')]));
global.document = {getElementById:id => roots[id], createElement:tag => new Node(tag), createTextNode:text => Object.assign(new Node('#text'), {_text:text})};
const all = node => [node, ...node.children.flatMap(all)];
const find = predicate => Object.values(roots).flatMap(all).find(predicate);
const button = text => find(node => node.tagName === 'button' && node.textContent === text);
const action = stage => find(node => node.dataset.through === stage);
const flush = async () => { for (let i = 0; i < 5; i++) await Promise.resolve(); };
const deferred = () => { let resolve, reject; const promise = new Promise((yes, no) => { resolve = yes; reject = no; }); return {promise, resolve, reject}; };
const settings = {epochs:500, sampling_seed:0, trajectory_filter:'LQR'};
const run = (revision_id = 'rev1') => ({run_id:'run1', revision_id, name:'Draft', is_latest:true, read_only:false, stages:[]});
const plan = (through, overrides = {}) => ({run_id:'run1', revision_id:'rev1', through, ready:true, stages:['sampling','training','binding','retargeting'].slice(0, ['sampling','training','binding','retargeting'].indexOf(through) + 1), completed:[], readiness:{message:'Native runtime ready'}, ...overrides});

(async () => {
  const source = fs.readFileSync(path.join(__dirname, '../motion_studio/studio/web/execution.js'));
  const {renderExecution} = await import('data:text/javascript;base64,' + source.toString('base64'));
  const requests = [], failures = [];
  let handler;
  const api = async (url, data) => { requests.push({url, data}); return handler(url, data); };
  const render = (selected = run(), jobs = [], refresh = async () => {}) => renderExecution({state:{runs:[selected], jobs}, run:selected, api, refresh, failure:error => failures.push(error.message)});
  const pendingSettings = deferred();
  handler = () => pendingSettings.promise;
  render();
  assert.ok(action('sampling').disabled, 'actions wait for saved settings');
  assert.ok(find(node => node.name === 'epochs').disabled, 'settings cannot be overwritten during their initial load');
  pendingSettings.resolve(settings); await flush();
  assert.equal(action('binding').disabled, false);
  assert.match(roots['viewport-execution'].textContent, /Binding includes training/);
  const initialForm = find(node => node.tagName === 'form');
  initialForm.valid = false;
  await action('binding').onclick();
  assert.equal(find(node => node.tagName === 'details').open, true, 'invalid settings are revealed before reporting validity');
  assert.match(roots['viewport-execution'].textContent, /Check the highlighted advanced execution settings/);
  assert.equal(requests.filter(r => r.url.endsWith('/plan')).length, 0, 'invalid settings never request a plan');
  initialForm.valid = true;
  handler = (url, data) => plan(data.through);
  await action('binding').onclick();
  assert.match(roots['viewport-execution'].textContent, /Sampling → Training → Binding/);
  assert.equal(requests.filter(r => r.url.endsWith('/execute')).length, 0, 'review never starts compute');
  assert.equal(button('Launch Binding plan').hidden, false);
  handler = () => { throw Error('GPU launch rejected'); };
  await button('Launch Binding plan').onclick();
  assert.match(roots['viewport-execution'].textContent, /GPU launch rejected/);
  assert.match(roots['viewport-execution'].textContent, /Review the action again/);
  assert.equal(button('Launch Binding plan').hidden, true, 'launch error consumes the reviewed plan');

  handler = () => settings;
  render(); await flush();
  handler = (url, data) => plan(data.through, {ready:false, stages:[], missing_inputs:['robot_pose','motion']});
  await action('retargeting').onclick();
  assert.match(roots['viewport-execution'].textContent, /Not ready: robot_pose, motion/);
  assert.equal(find(node => node.className === 'execution-launch').hidden, true);

  handler = () => settings;
  render(); await flush();
  const stalePlan = deferred(); handler = () => stalePlan.promise;
  const review = action('binding').onclick();
  const form = find(node => node.tagName === 'form');
  form.oninput();
  stalePlan.resolve(plan('binding')); await review;
  assert.equal(find(node => node.className === 'execution-launch').hidden, true, 'changed settings invalidate an in-flight review');
  assert.match(roots['viewport-execution'].textContent, /Settings changed/);

  handler = () => settings;
  render(); await flush();
  handler = () => { throw Error('Runtime probe unavailable'); };
  await action('sampling').onclick();
  assert.match(roots['viewport-execution'].textContent, /Runtime probe unavailable/);
  assert.equal(find(node => node.className === 'execution-launch').hidden, true);
  handler = (url, data) => plan(data.through, {stages:[], completed:['sampling']});
  await action('sampling').onclick();
  assert.match(roots['viewport-execution'].textContent, /none; verified outputs already available/);
  assert.match(roots['viewport-execution'].textContent, /Reuse verified: Sampling/);
  assert.equal(find(node => node.className === 'execution-launch').hidden, true, 'complete stages never launch again automatically');
  handler = () => { throw Error('Settings unavailable'); };
  render(); await flush();
  assert.match(roots['viewport-execution'].textContent, /Settings unavailable/);
  assert.ok(action('sampling').disabled, 'settings failure leaves actions safely disabled');

  const oldSettings = deferred(), newSettings = deferred();
  handler = () => oldSettings.promise; render();
  handler = () => newSettings.promise; render();
  newSettings.resolve({...settings, epochs:91}); await flush();
  oldSettings.resolve({...settings, epochs:3}); await flush();
  assert.equal(find(node => node.name === 'epochs').value, 91, 'old same-revision renders cannot overwrite newer settings');
  const obsoletePlan = deferred(); handler = () => obsoletePlan.promise;
  const obsoleteReview = action('retargeting').onclick();
  handler = () => settings; render({...run('rev2'), is_latest:false}); await flush();
  obsoletePlan.resolve(plan('retargeting')); await obsoleteReview;
  assert.equal(find(node => node.className === 'execution-launch').hidden, true, 'a previous revision cannot reveal a launch button');
  assert.ok(action('sampling').disabled, 'saved snapshots cannot compute');
  render({...run(), read_only:true});
  assert.match(roots['viewport-execution'].textContent, /Historical result · read-only/);
  assert.ok(action('binding').disabled);
  assert.equal(find(node => node.tagName === 'form'), undefined, 'historical results have no execution settings form');

  handler = () => settings;
  render(run(), [{job_id:'done',run_id:'run1',revision_id:'rev1',status:'failed',stage:'training',message:'Training process failed',progress:{epoch:8,epochs:500,last_line:'native failure detail'},attempts:{training:1}}]);
  await flush();
  assert.match(roots['viewport-execution'].textContent, /failed · training · Training process failed/);
  assert.match(roots['viewport-execution'].textContent, /observed epoch 8\/500/);
  assert.match(roots['viewport-execution'].textContent, /native failure detail/);
  assert.equal(roots.logs.children[0].href, '/api/jobs/done/log/training');
  const bar = stage => find(node => node.attributes.role === 'progressbar' && node.attributes['aria-label'] === stage);
  assert.equal(bar('Training').attributes['aria-valuenow'], '1');
  assert.match(bar('Training').attributes['aria-valuetext'], /Failed · 1%/);

  // Mock polling timers and observations; no test starts a native process.
  const realTimeout = global.setTimeout, timers = [];
  global.setTimeout = callback => { timers.push(callback); return timers.length; };
  const job = (overrides = {}) => ({job_id:'progress', run_id:'run1', revision_id:'rev1', status:'running',
    stage:'training', plan:plan('retargeting'), attempts:{sampling:1, training:1},
    attempt_statuses:{sampling:'completed', training:'running'}, progress:{epoch:125, epochs:500}, ...overrides});
  render(run(), [job()]); await flush();
  assert.equal(bar('Sampling').attributes['aria-valuenow'], '100', 'accepted prerequisite is complete');
  assert.equal(bar('Training').attributes['aria-valuenow'], '25');
  assert.match(bar('Training').attributes['aria-valuetext'], /observed epoch 125\/500/);
  assert.equal(bar('Binding').attributes['aria-valuenow'], undefined, 'queued stages have no invented percentage');
  assert.equal(bar('Binding').dataset.indeterminate, 'true');
  render(run(), [job({progress:{epoch:500,epochs:500}})]); await flush();
  assert.equal(bar('Training').attributes['aria-valuenow'], '99', 'native counts cannot claim validated completion');
  for (const status of ['failed', 'cancelled', 'interrupted']) {
    render(run(), [job({status, progress:{epoch:500,epochs:500}})]); await flush();
    assert.equal(bar('Training').attributes['aria-valuenow'], '99', `${status} must never claim completion`);
    assert.match(bar('Training').attributes['aria-valuetext'], new RegExp(status, 'i'));
    assert.equal(bar('Training').dataset.indeterminate, undefined, 'stopped stages do not animate');
  }
  for (const stage of ['sampling', 'binding']) {
    render(run(), [job({stage, progress:{}, attempt_statuses:{[stage]:'running'}})]); await flush();
    assert.equal(bar(stage[0].toUpperCase() + stage.slice(1)).dataset.indeterminate, 'true');
  }
  render(run(), [job({stage:'retargeting', progress:{frames_done:12,frames_total:48}})]); await flush();
  assert.equal(bar('Retargeting').attributes['aria-valuenow'], '25');
  assert.match(bar('Retargeting').attributes['aria-valuetext'], /observed frames 12\/48/);
  render(run(), [job({stage:'retargeting', progress:{frames_done:0,frames_total:48}})]); await flush();
  assert.equal(bar('Retargeting').attributes['aria-valuenow'], '0', 'observed zero is measured progress');
  render(run(), [job({stage:'retargeting', progress:{frames_done:12,frames_total:0}})]); await flush();
  assert.equal(bar('Retargeting').attributes['aria-valuenow'], undefined, 'invalid totals remain indeterminate');
  render(run(), [job({stage:null, status:'queued', progress:{}, attempts:{}, attempt_statuses:{}})]); await flush();
  assert.equal(bar('Training').dataset.indeterminate, 'true');
  render(run(), [job({stage:'retargeting', status:'completed', progress:{frames_done:48,frames_total:48}})]); await flush();
  assert.equal(bar('Retargeting').attributes['aria-valuenow'], '100');
  assert.match(bar('Retargeting').attributes['aria-valuetext'], /Validated · 100%/);

  render(run(), [{job_id:'other',run_id:'run2',revision_id:'other-rev',status:'running',stage:'sampling',message:'Sampling points',progress:{},attempts:{}}]);
  await flush();
  assert.match(roots['active-job'].textContent, /Another run is active/);
  assert.match(roots['active-job'].textContent, /Sampling points/);
  assert.ok(action('retargeting').disabled, 'another active job disables all primary actions');
  assert.equal(button('Stop active job').disabled, false);
  assert.equal(requests.filter(r => r.url.endsWith('/execute')).length, 1, 'only the explicit launch click invoked execution');
  assert.equal(bar('Sampling').dataset.indeterminate, 'true', 'sampling without counters is indeterminate');

  let observed = job({job_id:'poll-stages'}), refreshes = 0;
  const refresh = async (...args) => {
    assert.deepEqual(args, [], 'poll refresh never selects the stage being computed');
    refreshes++; render(run(), [observed], refresh);
  };
  handler = url => url.includes('/api/jobs/') ? observed : settings;
  render(run(), [observed], refresh); await flush();
  const pendingTimers = timers.length;
  render(run(), [observed], refresh); await flush();
  assert.equal(timers.length, pendingTimers, 'rerender keeps one polling loop');
  const step = async next => { observed = next; const tick = timers.pop(); timers.length = 0; tick(); await flush(); };
  await step(job({job_id:'poll-stages',progress:{epoch:250,epochs:500}}));
  assert.equal(refreshes, 0, 'counter updates do not reload the selected scene');
  await step(job({job_id:'poll-stages',stage:'binding',progress:{},attempt_statuses:{sampling:'completed',training:'completed',binding:'running'}}));
  assert.equal(refreshes, 1, 'accepted stages become inspectable while the plan is still running');
  assert.equal(bar('Training').attributes['aria-valuenow'], '100');
  assert.equal(timers.length, 1, 'transition refresh does not create a second poll');
  await step(job({job_id:'poll-stages',stage:'binding',status:'failed',progress:{},attempt_statuses:{sampling:'completed',training:'completed',binding:'failed'}}));
  assert.equal(refreshes, 2, 'terminal state refreshes artifacts and availability');
  assert.equal(bar('Binding').attributes['aria-valuenow'], undefined, 'uncounted failure has no fake percentage');
  assert.match(bar('Binding').attributes['aria-valuetext'], /Failed/);
  assert.equal(timers.length, 0, 'terminal jobs stop polling');
  global.setTimeout = realTimeout;
  console.log('Viewport execution controls, observed stage progress, validation states and single-loop transition polling passed');
})().catch(error => { console.error(error); process.exitCode = 1; });
