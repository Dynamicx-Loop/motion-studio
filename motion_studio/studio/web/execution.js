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
function displayJob(job) {
  const p = job.progress;
  const observed = [p.epoch ? `observed epoch ${p.epoch}/${p.epochs}` : '',
    p.frames_total ? `solved frames ${p.frames_done}/${p.frames_total}; output validation pending` : '',
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
      if (selected?.run_id === job.run_id) displayJob(job);
    }
    await refreshState();
  } catch (error) { showFailure(error); }
  finally { polling = false; }
}
export function renderExecution({state, run, api, refresh, failure}) {
  selected = run; apiCall = api; refreshState = refresh; showFailure = failure;
  const host = $('execution'); host.replaceChildren();
  if (!run || run.read_only) return;
  const form = document.createElement('form');
  const title = document.createElement('h3'); title.textContent = 'Native UMR execution'; form.append(title);
  const help = document.createElement('small');
  help.textContent = 'Defaults: 4096 slots, seed 0, 500 epochs, LQR. Modified controls create a new revision; small-epoch runs are smoke experiments.';
  form.append(help);
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
  const review = document.createElement('button'); review.textContent = 'Review prerequisite plan'; form.append(review);
  const planText = document.createElement('p'); planText.setAttribute('role','status'); form.append(planText);
  const launch = document.createElement('button'); launch.type = 'button'; launch.textContent = 'Launch reviewed plan'; launch.hidden = true; form.append(launch);
  const controls = () => ({sampling_seed:Number(fields.sampling_seed.value),epochs:Number(fields.epochs.value),trajectory_filter:filter.value});
  form.oninput = () => { launch.hidden = true; planText.textContent = 'Review the changed settings before launch.'; };
  form.onsubmit = async event => {
    event.preventDefault(); review.disabled = true; launch.hidden = true;
    try {
      const settings = controls();
      const plan = await api(`/api/runs/${run.run_id}/plan`, {through:through.value,settings});
      planText.textContent = plan.ready ? `Prerequisites to compute: ${plan.stages.join(' → ') || 'none; verified outputs already available'}. ${plan.readiness.message}` :
        `Not ready: ${plan.missing_inputs.join(', ') || plan.readiness?.message}`;
      launch.hidden = !plan.ready || !plan.stages.length;
      launch.onclick = async () => {
        launch.disabled = true;
        try {
          const job = await api(`/api/runs/${run.run_id}/execute`, {through:plan.through,settings});
          displayJob(job); poll(job); await refresh();
        } catch (error) { failure(error); launch.disabled = false; }
      };
    } catch (error) { failure(error); } finally { review.disabled = false; }
  };
  host.append(form);
  const cancel = document.createElement('button'); cancel.id = 'cancel-execution'; cancel.textContent = 'Cancel active stage'; cancel.hidden = true; host.append(cancel);
  const progress = document.createElement('pre'); progress.id = 'execution-progress'; host.append(progress);
  api(`/api/runs/${run.run_id}/settings`).then(settings => {
    if (selected?.run_id !== run.run_id) return;
    fields.epochs.value = settings.epochs; fields.sampling_seed.value = settings.sampling_seed; filter.value = settings.trajectory_filter;
  }).catch(failure);
  const jobs = state.jobs.filter(job => job.run_id === run.run_id);
  const last = jobs.at(-1);
  if (last) { displayJob(last); if (!terminal(last)) poll(last); }
}
