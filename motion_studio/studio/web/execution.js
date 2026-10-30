// Explicit server-owned execution. Selecting a tab never calls these operations.
const $ = id => document.getElementById(id);
let selected, apiCall, refreshState, showFailure, polling = false;
const terminal = job => !['queued', 'running', 'cancelling'].includes(job.status);
function logLinks(job) {
  const host = $('logs'); host.replaceChildren();
  for (const stage of Object.keys(job.attempts)) {
    const a = document.createElement('a'); a.textContent = `${stage} native log`;
    a.href = `/api/jobs/${job.job_id}/log/${stage}`; a.target = '_blank'; a.rel = 'noopener';
    host.append(a, document.createTextNode(' · '));
  }
}
function displayActive(job) {
  const host = $('active-job'); host.replaceChildren();
  if (terminal(job)) return;
  const note = document.createElement('p');
  note.textContent = `${job.status} · ${job.stage || 'starting'} · ${job.message}. Browser closure leaves this job running. No automatic queue.`;
  const stop = document.createElement('button'); stop.textContent = 'Stop active job';
  stop.disabled = job.status === 'cancelling';
  stop.onclick = async () => {
    try { displayActive(await apiCall(`/api/jobs/${job.job_id}/cancel`, {})); }
    catch (error) { showFailure(error); }
  };
  host.append(note, stop);
}
function displayJob(job) {
  displayActive(job);
  const p = job.progress;
  const observed = [p.epoch ? `observed epoch ${p.epoch}/${p.epochs}` : '',
    p.frames_total ? `solved frames ${p.frames_done}/${p.frames_total}${job.status === 'completed' ? '; output validated' : '; output validation pending'}` : '',
    p.elapsed_seconds ? `${p.elapsed_seconds}s observed elapsed` : ''].filter(Boolean);
  $('status').textContent = `${job.status} · ${job.stage || 'starting'} · ${job.message}${observed.length ? ' · ' + observed.join(' · ') : ''}`;
  $('execution-progress').textContent = p.last_line || '';
  $('cancel-execution').hidden = terminal(job);
  $('cancel-execution').onclick = async () => {
    try { displayJob(await apiCall(`/api/jobs/${job.job_id}/cancel`, {})); } catch (error) { showFailure(error); }
  };
  logLinks(job);
}
async function poll(job) {
  if (polling) return;
  polling = true;
  try {
    while (!terminal(job)) {
      await new Promise(resolve => setTimeout(resolve, 1000));
      job = await apiCall(`/api/jobs/${job.job_id}`);
      displayActive(job);
      if (selected?.run_id === job.run_id && selected?.revision_id === job.revision_id) displayJob(job);
    }
    await refreshState();
  } catch (error) { showFailure(error); }
  finally { polling = false; }
}
export function renderExecution({state, run, api, refresh, failure}) {
  selected = run; apiCall = api; refreshState = refresh; showFailure = failure;
  const host = $('execution'); host.replaceChildren();
  const active = state.jobs.find(job => !terminal(job));
  $('active-job').replaceChildren();
  if (active) { displayActive(active); poll(active); }
  if (!run || run.read_only) return;
  const form = document.createElement('form');
  const title = document.createElement('h3'); title.textContent = 'Native UMR execution'; form.append(title);
  const help = document.createElement('small');
  help.textContent = 'Defaults: 4096 slots, seed 0, 500 epochs, LQR. Modified controls create a new revision; small-epoch runs are smoke experiments.';
  form.append(help);
  const recovery = document.createElement('p'); recovery.textContent = 'Retry restarts the interrupted stage in a fresh attempt, using only verified compatible prerequisites. No epoch/frame resume. Saving a draft never queues work.'; form.append(recovery);
  const fields = {};
  for (const [name, label, value] of [['sampling_seed','Sampling seed',0],['epochs','Training epochs',500]]) {
    const row = document.createElement('label'); row.textContent = label;
    const input = document.createElement('input'); input.type = 'number'; input.name = name; input.value = value;
    input.min = name === 'epochs' ? 1 : 0; input.max = name === 'epochs' ? 10000 : 2147473647;
    input.step = 1; input.required = true; row.append(input); form.append(row); fields[name] = input;
  }
  const row = document.createElement('label'); row.textContent = 'Trajectory filter';
  const filter = document.createElement('select');
  for (const text of ['LQR','none']) { const option = document.createElement('option'); option.value = text; option.textContent = text; filter.append(option); }
  row.append(filter); form.append(row);
  const through = document.createElement('select'); through.setAttribute('aria-label','Run through stage');
  for (const stage of ['sampling','training','binding','retargeting']) {
    const option = document.createElement('option'); option.value = stage;
    option.textContent = stage === 'retargeting' ? 'Run all (through retargeting)' : `Run through ${stage}`;
    through.append(option);
  }
  through.value = 'retargeting'; form.append(through);
  const save = document.createElement('button'); save.type = 'button'; save.textContent = 'Save settings revision'; form.append(save);
  const review = document.createElement('button'); review.textContent = 'Review prerequisite plan'; form.append(review);
  const planText = document.createElement('p'); planText.setAttribute('role','status'); form.append(planText);
  const launch = document.createElement('button'); launch.type = 'button'; launch.textContent = 'Launch reviewed plan'; launch.hidden = true; form.append(launch);
  const controls = () => ({sampling_seed:Number(fields.sampling_seed.value),epochs:Number(fields.epochs.value),trajectory_filter:filter.value});
  save.onclick = async () => {
    save.disabled = true;
    try { await api(`/api/runs/${run.run_id}/settings`, {settings:controls()}); await refresh(); }
    catch (error) { failure(error); save.disabled = false; }
  };
  form.oninput = () => { launch.hidden = true; planText.textContent = 'Review the changed settings before launch.'; };
  form.onsubmit = async event => {
    event.preventDefault(); review.disabled = true; launch.hidden = true;
    try {
      const settings = controls();
      const plan = await api(`/api/runs/${run.run_id}/plan`, {through:through.value,settings});
      planText.textContent = plan.ready ? `Prerequisites to compute: ${plan.stages.join(' → ') || 'none; verified outputs already available'}. ${plan.readiness.message}` :
        `Not ready: ${plan.missing_inputs.join(', ') || plan.readiness?.message}`;
      launch.hidden = !plan.ready || !plan.stages.length;
      launch.disabled = Boolean(active);
      if (active) planText.textContent += ' Another job is active; this plan is not queued.';
      planText.textContent += ` ${plan.reuse_message || ''}`;
      launch.onclick = async () => {
        launch.disabled = true;
        try {
          const job = await api(`/api/runs/${run.run_id}/execute`, {through:plan.through,settings});
          displayJob(job); poll(job); await refresh();
        } catch (error) { failure(error); launch.disabled = false; }
      };
    } catch (error) { failure(error); } finally { review.disabled = false; }
  };
  const outputs = {sampling:'dataset.npz', training:'train/correspondence_slots_final.npz', binding:'binding.npz', retargeting:'motion.npz'};
  for (const stage of run.stages.filter(s => outputs[s.stage] && s.status === 'available')) {
    const details = document.createElement('details');
    const summary = document.createElement('summary'); summary.textContent = `${stage.stage} saved artifacts`; details.append(summary);
    const base = `/artifacts/${run.run_id}/${run.revision_id}/${stage.stage}/`;
    for (const [label, url] of [['Native output',base+outputs[stage.stage]], ['Resolved configuration',base+'humanoid_retarget_runtime_config.json'],
      ['Numerical validation',base+'validation.json'], ['Completion receipt',`/api/runs/${run.run_id}/revisions/${run.revision_id}/stages/${stage.stage}/receipt`]]) {
      const a = document.createElement('a'); a.textContent = label; a.href = url; a.target = '_blank'; a.rel = 'noopener';
      details.append(a, document.createElement('br'));
    }
    host.append(details);
  }
  if (run.is_latest) host.append(form);
  const cancel = document.createElement('button'); cancel.id = 'cancel-execution'; cancel.textContent = 'Cancel active stage'; cancel.hidden = true; host.append(cancel);
  const progress = document.createElement('pre'); progress.id = 'execution-progress'; host.append(progress);
  api(`/api/runs/${run.run_id}/revisions/${run.revision_id}/settings`).then(settings => {
    if (selected?.run_id !== run.run_id || selected?.revision_id !== run.revision_id) return;
    fields.epochs.value = settings.epochs; fields.sampling_seed.value = settings.sampling_seed; filter.value = settings.trajectory_filter;
  }).catch(failure);
  const jobs = state.jobs.filter(job => job.run_id === run.run_id && job.revision_id === run.revision_id);
  const last = jobs.at(-1);
  if (last) {
    displayJob(last); if (active && active.job_id !== last.job_id) displayActive(active);
    if (!terminal(last)) poll(last);
    if (['failed','cancelled','interrupted'].includes(last.status) && run.is_latest) {
      const retry = document.createElement('button'); retry.type = 'button'; retry.textContent = 'Review explicit retry';
      retry.disabled = Boolean(active);
      retry.onclick = () => { through.value = last.plan.through; form.requestSubmit(); };
      host.append(retry);
    }
  }
}
