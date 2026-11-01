import {renderAssets} from './assets.js';
import {hideSourcePreview} from './source-preview.js';
import {renderRobot} from '/robot.js';
import {renderExecution} from './execution.js';
import {renderMotion} from './motion.js';
import {renderInspection} from './inspection-ui.js';
const $ = id => document.getElementById(id);
let state, selectedStage = 'motion', renderedIdentity;
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
  const run = state.selected_run || state.runs.find(item => item.run_id === state.selected_run_id);
  const identity=`${run?.run_id}/${run?.revision_id}`;
  if(renderedIdentity!==identity)hideSourcePreview();
  renderedIdentity=identity;
  const revisions = $('revisions');
  revisions.replaceChildren(...(state.revisions || []).map(item => {
    const option = document.createElement('option'); option.value = item.revision_id;
    option.textContent = `${item.revision_id}${item.is_latest ? ' · latest editable' : ' · saved snapshot'}`;
    return option;
  }));
  revisions.value = run?.revision_id || ''; revisions.disabled = !run;
  revisions.onchange = async () => {
    try { hideSourcePreview(); await api('/api/selection', {run_id:run.run_id, revision_id:revisions.value}); await refresh(); }
    catch (error) { failure(error); }
  };
  $('revision-note').textContent = run && !run.is_latest ? 'Viewing an immutable saved revision. Select latest to change inputs or launch work.' : 'Saved edits create a revision; unaffected verified prerequisites may be reused. Robot, pose or motion edits invalidate all stages.';
  $('runs').replaceChildren(...state.runs.map(item => {
    const button = document.createElement('button'); button.textContent = item.name;
    button.setAttribute('aria-current', String(item.run_id === run?.run_id));
    const badge = document.createElement('small'); badge.textContent = item.read_only ? 'Historical · read-only' : 'Draft';
    button.append(badge);
    button.onclick = async () => {
      try { hideSourcePreview(); await api('/api/selection', {run_id: item.run_id}); await refresh(); } catch (error) { failure(error); }
    };
    return button;
  }));
  $('history-roots').textContent = state.history_roots.length ? `Allowed roots: ${state.history_roots.join(', ')}` : 'No historical roots configured. Restart with --history-root to permit registration.';
  $('run-name').textContent = run?.name || 'Choose or create a run';
  $('identity').textContent = run ? `Run ${run.run_id} · revision ${run.revision_id}` : '';
  $('kind').textContent = run ? run.read_only ? 'Historical reference · read-only' : 'Draft · ready for input preparation' : 'Select a saved run.';
  const active = state.jobs.find(job => ['queued', 'running', 'cancelling'].includes(job.status));
  $('status').textContent = active ? `${active.status} · ${active.stage || 'starting'} · ${state.runs.find(r => r.run_id === active.run_id)?.name || active.run_id} · browser closure leaves this job running` : run?.read_only ? 'Viewing preserved saved output · no computation active' : 'Idle · no computation active';
  if (!run?.stages.some(stage => stage.stage === selectedStage && stage.status === 'available'))
    selectedStage = run?.stages.find(stage => stage.status === 'available')?.stage || 'preparation';
  $('stages').replaceChildren(...(run?.stages || []).map(stage => {
    const button = document.createElement('button');
    button.textContent = `${stage.stage[0].toUpperCase()}${stage.stage.slice(1)} · ${stage.status}`;
    button.disabled = stage.status !== 'available';
    button.title = stage.reason || '';
    button.dataset.status = stage.status;
    if (stage.status === 'stale') button.textContent += ' · recompute explicitly';
    button.setAttribute('aria-current', String(stage.stage === selectedStage));
    button.onclick = () => { hideSourcePreview(); selectedStage = stage.stage; render(); };
    return button;
  }));
  $('viewport').dataset.stage = selectedStage;
  renderInspection({run,selectedStage,api});
  renderAssets({state,run,api,refresh,failure});
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
async function refresh(stage) {
  if(stage)selectedStage=stage;
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
window.addEventListener('pageshow', event => {
  if (event.persisted) refresh().catch(failure);
});
