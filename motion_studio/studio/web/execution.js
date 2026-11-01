// Explicit server-owned execution. Inspection tabs never start computation.
const $ = id => document.getElementById(id);
const terminal = job => !['queued', 'running', 'cancelling'].includes(job.status);
const labels = {sampling:'Sampling', training:'Training', binding:'Binding', retargeting:'Retargeting'};
let current, activeJob, polling;
const matches = (job, run) => job?.run_id === run?.run_id && job?.revision_id === run?.revision_id;
const live = context => current === context;
function element(tag, text, className) {
  const node = document.createElement(tag);
  if (text) node.textContent = text;
  if (className) node.className = className;
  return node;
}
function report(error, context = current) {
  if (!live(context)) return;
  context.error.textContent = error.message;
  context.failure(error);
}
function invalidate(context, message = '') {
  context.version++;
  context.reviewed = null;
  context.launch.hidden = true;
  context.plan.textContent = message;
}
function syncControls(context = current) {
  if (!live(context)) return;
  const blocked = !context.editable || !context.loaded || context.busy || Boolean(activeJob);
  for (const button of context.actions) button.disabled = blocked;
  if (context.save) context.save.disabled = blocked;
  for (const field of Object.values(context.fields)) field.disabled = !context.editable || !context.loaded || context.busy || Boolean(activeJob);
  context.launch.disabled = blocked || !context.reviewed;
}
function logLinks(job) {
  const host = $('logs'); host.replaceChildren();
  for (const stage of Object.keys(job.attempts || {})) {
    const a = element('a', `${stage} native log`);
    a.href = `/api/jobs/${job.job_id}/log/${stage}`; a.target = '_blank'; a.rel = 'noopener';
    host.append(a, document.createTextNode(' · '));
  }
}
function jobSummary(job) {
  const p = job.progress || {};
  return [job.status, job.stage || 'starting', job.recovery_notice || job.message,
    p.epoch != null ? `observed epoch ${p.epoch}/${p.epochs}` : '',
    p.frames_total ? `solved frames ${p.frames_done}/${p.frames_total}${job.status === 'completed' ? '; output validated' : '; output validation pending'}` : '',
    p.elapsed_seconds ? `${p.elapsed_seconds}s observed elapsed` : ''].filter(Boolean).join(' · ');
}
function stageProgress(job) {
  const stages = [...new Set([...(job.plan?.completed || []), ...(job.plan?.stages || []),
    ...Object.keys(job.attempts || {}), ...(job.stage ? [job.stage] : [])])];
  const host = element('div', '', 'execution-stages');
  for (const stage of stages.length ? stages : ['queued']) {
    const complete = job.plan?.completed?.includes(stage) || job.attempt_statuses?.[stage] === 'completed'
      || (job.status === 'completed' && (job.plan?.stages?.includes(stage) || stage === job.stage));
    const active = stage === job.stage;
    const p = active ? job.progress || {} : {};
    const [done, total, unit] = stage === 'training' ? [p.epoch, p.epochs, 'epoch']
      : stage === 'retargeting' ? [p.frames_done, p.frames_total, 'frames'] : [];
    const measured = typeof done === 'number' && Number.isFinite(done) && done >= 0
      && typeof total === 'number' && Number.isFinite(total) && total > 0;
    const percent = complete ? 100 : measured ? Math.min(99, Math.floor(done / total * 100)) : null;
    const state = complete ? 'completed' : active ? job.status : terminal(job) ? 'not-run' : 'queued';
    const stateLabel = {completed:'Validated', failed:'Failed', cancelled:'Cancelled', interrupted:'Interrupted',
      cancelling:'Stopping', running:'Running', queued:'Queued', 'not-run':'Not run'}[state] || state;
    const label = `${labels[stage] || 'Execution'} · ${stateLabel}${percent === null ? '' : ` · ${percent}%`}`;
    const row = element('div', '', 'execution-stage-progress'); row.dataset.state = state;
    row.append(element('span', label));
    const bar = element('div', '', 'execution-progress-bar');
    bar.setAttribute('role', 'progressbar'); bar.setAttribute('aria-label', labels[stage] || 'Execution');
    bar.setAttribute('aria-valuemin', '0'); bar.setAttribute('aria-valuemax', '100');
    const detail = measured && !complete ? `observed ${unit} ${done}/${total}; output validation pending` : '';
    bar.setAttribute('aria-valuetext', [label, detail].filter(Boolean).join(' · '));
    if (percent !== null) bar.setAttribute('aria-valuenow', String(percent));
    else if (['queued', 'running', 'cancelling'].includes(state)) bar.dataset.indeterminate = 'true';
    const fill = element('div');
    if (percent !== null) fill.setAttribute('style', `width:${percent}%`);
    bar.append(fill); row.append(bar);
    if (detail) row.append(element('small', detail));
    host.append(row);
  }
  return host;
}
function jobCard(job, other = false) {
  const card = element('div', '', 'execution-job');
  card.dataset.status = job.status;
  if (other) card.append(element('strong', `${job.run_id === current.run?.run_id ? 'Another revision' : 'Another run'} is active · ${current.runNames[job.run_id] || job.run_id}`));
  card.append(element('p', jobSummary(job)));
  card.append(stageProgress(job));
  if (job.progress?.last_line) card.append(element('pre', job.progress.last_line, 'execution-progress'));
  if (!terminal(job)) {
    card.append(element('small', 'Browser closure leaves this job running. No automatic queue.'));
    const stop = element('button', job.status === 'cancelling' ? 'Stopping…' : 'Stop active job');
    stop.type = 'button'; stop.disabled = job.status === 'cancelling';
    stop.onclick = async () => {
      const context = current; stop.disabled = true;
      try { updateJob(await context.api(`/api/jobs/${job.job_id}/cancel`, {})); }
      catch (error) { report(error, context); if (live(context)) stop.disabled = false; }
    };
    card.append(stop);
  }
  return card;
}
function displayJobs(context = current) {
  if (!live(context)) return;
  const host = $('active-job'); host.replaceChildren();
  const other = activeJob && !matches(activeJob, context.run);
  if (other) host.append(jobCard(activeJob, true));
  context.summary.replaceChildren();
  const job = activeJob && !other ? activeJob : context.lastJob;
  if (job) {
    context.summary.append(jobCard(job)); logLinks(job);
    $('status').textContent = jobSummary(job);
  } else if (!other) context.summary.append(element('small', 'No computation active. Review an action to see its prerequisite plan.'));
  syncControls(context);
}
function updateJob(job) {
  if (!terminal(job)) activeJob = job;
  else if (activeJob?.job_id === job.job_id) activeJob = null;
  if (matches(job, current.run)) current.lastJob = job;
  displayJobs();
}
async function poll(job, api, refresh) {
  if (polling?.job_id === job.job_id) return;
  const session = {job_id:job.job_id}; polling = session;
  const checkpoint = value => JSON.stringify([value.stage, value.status, value.attempt_statuses]);
  try {
    while (!terminal(job) && polling === session) {
      await new Promise(resolve => setTimeout(resolve, 1000));
      if (polling !== session) return;
      const previous = checkpoint(job);
      job = await api(`/api/jobs/${job.job_id}`);
      if (polling !== session) return;
      updateJob(job);
      // Publish each accepted stage to the tabs during a multi-stage plan.
      // A refresh preserves the user's selected inspection stage.
      if (previous !== checkpoint(job)) await refresh();
    }
  } catch (error) { if (polling === session) report(new Error(`Job status unavailable: ${error.message}`)); }
  finally { if (polling === session) polling = null; }
}
function validSettings(context) {
  if (context.form.checkValidity()) return true;
  context.settingsDetails.open = true;
  context.form.reportValidity();
  context.error.textContent = 'Check the highlighted advanced execution settings.';
  return false;
}
async function review(context, through) {
  if (!live(context) || !context.loaded || !context.editable || context.busy || activeJob) return;
  if (!validSettings(context)) return;
  invalidate(context, `Reviewing ${labels[through]} prerequisites…`);
  const version = context.version;
  const settings = context.controls();
  context.error.textContent = ''; context.busy = true; syncControls(context);
  try {
    const plan = await context.api(`/api/runs/${context.run.run_id}/plan`, {through, settings});
    if (!live(context) || version !== context.version) return;
    if (plan.revision_id !== context.run.revision_id) throw new Error('Inputs changed. Select the latest revision and review again.');
    context.plan.replaceChildren(element('strong', `${labels[through]} plan`));
    if (!plan.ready) {
      context.plan.append(element('p', `Not ready: ${plan.missing_inputs?.join(', ') || plan.readiness?.message || 'Prerequisites unavailable'}`));
      return;
    }
    context.plan.append(element('p', `Compute: ${plan.stages.map(stage => labels[stage]).join(' → ') || 'none; verified outputs already available'}.`));
    if (plan.completed?.length) context.plan.append(element('p', `Reuse verified: ${plan.completed.map(stage => labels[stage]).join(', ')}.`));
    if (plan.readiness?.message) context.plan.append(element('small', plan.readiness.message));
    if (plan.reuse_message) context.plan.append(element('small', plan.reuse_message));
    if (plan.stages.length) {
      context.reviewed = {through:plan.through, settings, version};
      context.launch.textContent = `Launch ${labels[through]} plan`;
      context.launch.hidden = false;
    }
  } catch (error) { if (live(context) && version === context.version) { context.plan.textContent = 'Plan review failed. Retry explicitly.'; report(error, context); } }
  finally { if (live(context)) { context.busy = false; syncControls(context); } }
}
function settingsForm(context, host) {
  const details = element('details'); context.settingsDetails = details;
  details.append(element('summary', 'Advanced execution settings'));
  const form = element('form'); context.form = form;
  form.append(element('small', 'Defaults: 4096 slots, seed 0, 500 training epochs, LQR. Modified settings create a new revision. Small-epoch runs are smoke experiments.'));
  for (const [name, label, value] of [['sampling_seed','Sampling seed',0], ['epochs','Training epochs',500]]) {
    const row = element('label', label), input = element('input');
    input.type = 'number'; input.name = name; input.value = value;
    input.min = name === 'epochs' ? 1 : 0; input.max = name === 'epochs' ? 10000 : 2147473647;
    input.step = 1; input.required = true; row.append(input); form.append(row); context.fields[name] = input;
  }
  const row = element('label', 'Trajectory filter'), filter = element('select');
  for (const text of ['LQR', 'none']) { const option = element('option', text); option.value = text; filter.append(option); }
  row.append(filter); form.append(row); context.fields.trajectory_filter = filter;
  context.controls = () => ({sampling_seed:Number(context.fields.sampling_seed.value), epochs:Number(context.fields.epochs.value), trajectory_filter:filter.value});
  const save = element('button', 'Save settings revision'); save.type = 'button'; context.save = save; form.append(save);
  save.onclick = async () => {
    if (!live(context) || save.disabled || !validSettings(context)) return;
    invalidate(context); context.busy = true; context.error.textContent = ''; syncControls(context);
    try { await context.api(`/api/runs/${context.run.run_id}/settings`, {settings:context.controls()}); await context.refresh(); }
    catch (error) { report(error, context); }
    finally { if (live(context)) { context.busy = false; syncControls(context); } }
  };
  form.oninput = () => invalidate(context, 'Settings changed. Review an action again before launch.');
  form.onsubmit = event => event.preventDefault();
  form.append(element('p', 'Retry restarts an interrupted stage in a fresh attempt, using verified compatible prerequisites. No epoch/frame resume. Saving settings never queues work.'));
  details.append(form); host.append(details);
}
function artifacts(run, host) {
  const outputs = {sampling:'dataset.npz', training:'train/correspondence_slots_final.npz', binding:'binding.npz', retargeting:'motion.npz'};
  for (const stage of run.stages.filter(s => outputs[s.stage] && s.status === 'available')) {
    const details = element('details'); details.append(element('summary', `${stage.stage} saved artifacts`));
    const base = `/artifacts/${run.run_id}/${run.revision_id}/${stage.stage}/`;
    for (const [label, url] of [['Native output',base+outputs[stage.stage]], ['Resolved configuration',base+'humanoid_retarget_runtime_config.json'],
      ['Numerical validation',base+'validation.json'], ['Completion receipt',`/api/runs/${run.run_id}/revisions/${run.revision_id}/stages/${stage.stage}/receipt`]]) {
      const a = element('a', label); a.href = url; a.target = '_blank'; a.rel = 'noopener'; details.append(a, document.createElement('br'));
    }
    host.append(details);
  }
}
export function renderExecution({state, run, api, refresh, failure}) {
  const host = $('execution'); host.replaceChildren();
  const panel = $('viewport-execution'); panel.replaceChildren();
  const context = {run, api, refresh, failure, runNames:Object.fromEntries(state.runs.map(r => [r.run_id, r.name])),
    editable:Boolean(run && !run.read_only && run.is_latest), loaded:false, busy:false, version:0, fields:{}, actions:[]};
  current = context;
  activeJob = state.jobs.find(job => !terminal(job)) || null;
  const title = element('div', '', 'execution-heading');
  title.append(element('strong', 'Compute stages'), element('small', 'Review prerequisites, then launch explicitly.'));
  panel.append(title);
  const actions = element('div', '', 'execution-actions');
  for (const stage of ['sampling', 'binding', 'retargeting']) {
    const button = element('button', labels[stage]); button.type = 'button'; button.dataset.through = stage;
    button.title = `Review ${labels[stage]} prerequisite plan`;
    button.onclick = () => review(context, stage); context.actions.push(button); actions.append(button);
  }
  panel.append(actions);
  const hint = element('small', !run ? 'Select or create a draft to compute stages.' : run.read_only ? 'Historical result · read-only. No execution available.' : !run.is_latest ? 'Saved snapshot · select the latest revision to compute stages.' : 'Binding includes training. Retargeting includes all required prerequisites. Verified compatible stages are reused.');
  panel.append(hint);
  context.plan = element('div', '', 'execution-plan'); context.plan.setAttribute('role', 'status'); panel.append(context.plan);
  context.launch = element('button'); context.launch.type = 'button'; context.launch.className = 'execution-launch'; context.launch.hidden = true; panel.append(context.launch);
  context.error = element('p', '', 'execution-error'); context.error.setAttribute('role', 'alert'); panel.append(context.error);
  context.summary = element('div', '', 'execution-summary'); context.summary.setAttribute('role', 'status'); panel.append(context.summary);
  context.launch.onclick = async () => {
    const reviewed = context.reviewed;
    if (!live(context) || context.launch.disabled || !reviewed || reviewed.version !== context.version || activeJob) return;
    context.busy = true; context.error.textContent = ''; invalidate(context, 'Submitting reviewed plan…'); syncControls(context);
    try {
      const job = await api(`/api/runs/${run.run_id}/execute`, {through:reviewed.through, settings:reviewed.settings});
      updateJob(job); poll(job, api, refresh); await refresh();
    } catch (error) { if (live(context)) { context.plan.textContent = 'Launch failed. Review the action again to retry.'; report(error, context); } }
    finally { if (live(context)) { context.busy = false; syncControls(context); } }
  };
  if (run && !run.read_only) {
    settingsForm(context, host); artifacts(run, host);
    context.plan.textContent = 'Loading saved execution settings…';
    const version = context.version;
    api(`/api/runs/${run.run_id}/revisions/${run.revision_id}/settings`).then(settings => {
      if (!live(context) || version !== context.version) return;
      context.fields.epochs.value = settings.epochs; context.fields.sampling_seed.value = settings.sampling_seed;
      context.fields.trajectory_filter.value = settings.trajectory_filter;
      context.loaded = true; context.plan.textContent = ''; syncControls(context);
    }).catch(error => { if (live(context) && version === context.version) { context.plan.textContent = 'Execution settings unavailable. Reload to retry.'; report(error, context); } });
  }
  context.lastJob = state.jobs.filter(job => matches(job, run)).at(-1);
  displayJobs(context);
  if (activeJob) poll(activeJob, api, refresh);
}
