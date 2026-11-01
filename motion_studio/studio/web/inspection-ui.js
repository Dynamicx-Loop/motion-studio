import {showInspectionProperties} from './inspection-properties.js';
// Inspection derivatives only read completed outputs; native execution stays explicit.
const builds = new Map();
const inspectable = new Set(['sampling', 'training', 'binding', 'retargeting', 'motion']);
let active;

function node(tag, text) {
  const element = document.createElement(tag);
  if (text !== undefined) element.textContent = text;
  return element;
}

function build(view, exportBundle = false) {
  const previous = builds.get(view.key);
  if (previous?.pending) return;
  const stage = view.options.run.stages.find(value => value.stage === view.options.selectedStage);
  const entry = {pending:true, url:previous?.url || stage?.inspection_url};
  builds.set(view.key, entry);
  // Record the request before starting it so repeated renders and aliases share it.
  Promise.resolve().then(() => view.options.api(
    `/api/runs/${view.options.run.run_id}/inspections/${view.nativeStage}`,
    {revision_id:view.options.run.revision_id}
  )).then(result => {
    entry.url = result.url;
    if (exportBundle) entry.path = result.path;
  }).catch(error => {
    entry.error = error.message;
  }).finally(() => {
    entry.pending = false;
    // A completion may repaint an alias, but cannot replace another run/revision/stage.
    if (active?.key === view.key) renderInspection(active.options);
  });
}

function viewport(url, message, embedded) {
  const frame = document.getElementById('inspection');
  const empty = document.getElementById('empty');
  frame.hidden = !url;
  empty.hidden = Boolean(url);
  const source = showInspectionProperties(embedded ? url : undefined) || url;
  if (source && frame.getAttribute('src') !== source) frame.src = source;
  if (!url) frame.removeAttribute('src');
  empty.replaceChildren();
  if (message) empty.textContent = message;
  else empty.append(document.createTextNode('Drop a robot or motion here'), node('br'),
    node('small', 'Start with a built-in asset on the left, or drop your robot files.'));
}

export function renderInspection(options) {
  const {run, selectedStage} = options;
  const nativeStage = selectedStage === 'motion' ? 'retargeting' : selectedStage;
  const key = `${run?.run_id}/${run?.revision_id}/${nativeStage}`;
  const view = {key, nativeStage, options};
  active = view;
  const host = document.getElementById('inspection-tools');
  host.replaceChildren();
  host.dataset.identity = key;
  const stage = run?.stages.find(value => value.stage === selectedStage && value.status === 'available');
  const available = stage && inspectable.has(selectedStage);
  let entry = builds.get(key);
  const url = available ? entry?.url || stage.inspection_url : undefined;
  if (available && !run.read_only && !url && !entry) {
    build(view);
    entry = builds.get(key);
  }
  const title = selectedStage[0].toUpperCase() + selectedStage.slice(1);
  const error = entry?.error;
  const message = available && !url ? error ? `${title} visualization unavailable: ${error}`
    : `Loading ${selectedStage} visualization…` : undefined;
  viewport(url, message, !run?.read_only);
  if (!available || run.read_only) return;

  if (entry?.pending) {
    const loading = node('span', url ? 'Exporting standalone bundle…' : `Loading ${selectedStage} visualization…`);
    loading.setAttribute('role', 'status');
    host.append(loading);
  } else {
    if (error) {
      const failure = node('span', error);
      failure.setAttribute('role', 'alert');
      host.append(failure, document.createTextNode(' '));
    }
    const button = node('button', error ? url ? 'Retry standalone export' : 'Retry stage visualization'
      : 'Export fresh standalone bundle');
    button.onclick = () => {
      if (active?.key !== key) return;
      build(active, Boolean(url));
      renderInspection(active.options);
    };
    host.append(button);
  }
  if (url) {
    for (const [label, file] of [['Open standalone viewer', 'index.html'], ['Native outputs, config, logs', 'files.html'], ['Export provenance', 'provenance.json']]) {
      const link = node('a', label);
      link.href = url.replace('index.html', file);
      link.target = '_blank'; link.rel = 'noopener';
      host.append(document.createTextNode(' · '), link);
    }
  }
  if (entry?.path) host.append(node('p', `Standalone HTTP bundle: ${entry.path}`));
}
