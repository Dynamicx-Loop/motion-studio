import {renderRobot} from '/robot.js';
import {renderExecution} from './execution.js';
import {renderMotion} from './motion.js';
const $ = id => document.getElementById(id);
let state, selectedStage = 'motion';
async function api(path, data) {
  const response = await fetch(path, data === undefined ? {} : {
    method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(data)
  });
  const result = await response.json();
  if (!response.ok) throw new Error(result.error?.message || `Request failed (${response.status})`);
  return result;
}
function failure(error) {
  $('error').textContent = error.message;
  $('connection').textContent = 'Action failed · retry or inspect logs';
}
function link(name, url) {
  const anchor = document.createElement('a'); anchor.textContent = name; anchor.href = url;
  anchor.target = '_blank'; anchor.rel = 'noopener'; return anchor;
}
function render() {
  const run = state.runs.find(item => item.run_id === state.selected_run_id);
  $('runs').replaceChildren(...state.runs.map(item => {
    const button = document.createElement('button'); button.textContent = item.name;
    button.setAttribute('aria-current', String(item.run_id === run?.run_id));
    const badge = document.createElement('small'); badge.textContent = item.read_only ? 'Historical · read-only' : 'Draft';
    button.append(badge);
    button.onclick = async () => {
      try { await api('/api/selection', {run_id: item.run_id}); await refresh(); } catch (error) { failure(error); }
    };
    return button;
  }));
  $('history-roots').textContent = state.history_roots.length ? `Allowed roots: ${state.history_roots.join(', ')}` : 'No historical roots configured. Restart with --history-root to permit registration.';
  $('run-name').textContent = run?.name || 'Choose or create a run';
  $('identity').textContent = run ? `Run ${run.run_id} · revision ${run.revision_id}` : '';
  $('kind').textContent = run ? run.read_only ? 'Historical reference · read-only' : 'Draft · ready for input preparation' : 'Select a saved run.';
  $('status').textContent = run?.read_only ? 'Viewing preserved saved output · no computation active' : 'Idle · no computation active';
  if (!run?.stages.some(stage => stage.stage === selectedStage && stage.status === 'available'))
    selectedStage = run?.stages.find(stage => stage.status === 'available')?.stage || 'preparation';
  $('stages').replaceChildren(...(run?.stages || []).map(stage => {
    const button = document.createElement('button');
    button.textContent = `${stage.stage[0].toUpperCase()}${stage.stage.slice(1)} · ${stage.status}`;
    button.disabled = stage.status !== 'available';
    button.setAttribute('aria-current', String(stage.stage === selectedStage));
    button.onclick = () => { selectedStage = stage.stage; render(); };
    return button;
  }));
  const stage = run?.stages.find(item => item.stage === selectedStage && item.status === 'available');
  const inspection = $('inspection'), url = stage?.inspection_url;
  inspection.hidden = !url; $('empty').hidden = Boolean(url);
  if (url && inspection.getAttribute('src') !== url) inspection.src = url;
  if (!url) inspection.removeAttribute('src');
  renderRobot({state,run,api,refresh,failure});
  renderMotion({state, run, api, refresh, failure});
  $('run-details').replaceChildren(); $('logs').replaceChildren();
  renderExecution({state, run, api, refresh, failure});
  if (run?.read_only) {
    const note = document.createElement('p'); note.textContent = 'Preserved G1 inspection: synchronized source human and saved robot motion, reconstructed bindings. No new native run.';
    $('run-details').append(note);
    const base = `/inspection/${run.run_id}/`;
    $('run-details').append(link('Provenance', base + 'provenance.json'), document.createElement('br'), link('Preservation receipt', base + 'preservation.json'));
    $('logs').append(link('Saved export log', base + 'export.log'));
  }
}
async function refresh() {
  state = await api('/api/state'); render();
  $('connection').textContent = 'Local service connected';
}
for (const [id, path] of [['new-draft', '/api/runs'], ['history', '/api/history']]) {
  $(id).onsubmit = async event => {
    event.preventDefault(); $('error').textContent = '';
    try {
      const record = await api(path, Object.fromEntries(new FormData(event.currentTarget)));
      await api('/api/selection', {run_id: record.run_id}); await refresh();
    } catch (error) { failure(error); }
  };
}
refresh().catch(failure);
window.addEventListener('pageshow', () => refresh().catch(failure));
