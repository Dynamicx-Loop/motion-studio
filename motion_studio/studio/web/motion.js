// Motion preparation owns only imports, metadata inspection and draft selection.
export function renderMotion({state, run, api, refresh, failure}) {
  const root = document.getElementById('motion-assets');
  root.replaceChildren();
  const details = document.createElement('details');
  const summary = document.createElement('summary'); summary.textContent = 'Import SMPL-X motion';
  const form = document.createElement('form'); form.id = 'motion-import';
  function field(label, name, placeholder, options) {
    const wrapper = document.createElement('label'); wrapper.textContent = label;
    const input = document.createElement(options ? 'select' : 'input'); input.name = name;
    if (options) for (const [value, text] of options) {
      const option = document.createElement('option'); option.value = value; option.textContent = text;
      input.append(option);
    }
    else input.placeholder = placeholder;
    wrapper.append(input); form.append(wrapper); return input;
  }
  const path = field('Local NPZ path', 'source_path', '/absolute/path/to/motion.npz'); path.required = true;
  const note = document.createElement('small');
  note.textContent = 'Missing metadata must be supplied explicitly below. Existing aliases must agree. Single person, metres, axis-angle radians; all frames retained.';
  form.append(note);
  const fps = field('FPS (only if missing)', 'fps', 'Use recorded metadata'); fps.type = 'number'; fps.min = '0.000001'; fps.step = 'any';
  field('Gender (only if missing)', 'gender', '', [['', 'Use recorded metadata'], ['neutral', 'Neutral'], ['male', 'Male'], ['female', 'Female']]);
  field('Up-axis (only if missing)', 'up_axis', '', [['', 'Use recorded metadata'], ['y', 'Y-up'], ['z', 'Z-up']]);
  const submit = document.createElement('button'); submit.textContent = 'Import immutable motion'; form.append(submit);
  form.onsubmit = async event => {
    event.preventDefault(); submit.disabled = true;
    document.getElementById('error').textContent = '';
    const fields = Object.fromEntries(new FormData(form));
    const metadata = {};
    for (const key of ['fps', 'gender', 'up_axis']) if (fields[key] !== '') metadata[key] = key === 'fps' ? Number(fields[key]) : fields[key];
    try {
      const asset = await api('/api/motions', {source_path: fields.source_path, metadata});
      if (run && !run.read_only) await api(`/api/runs/${run.run_id}/motion`, {asset_id: asset.asset_id});
      await refresh();
    } catch (error) { failure(error); submit.disabled = false; }
  };
  details.append(summary, form); root.append(details);
  const library = document.createElement('div'); library.id = 'motion-library';
  for (const asset of state.motions || []) {
    const item = document.createElement('details'); item.open = run?.motion_asset_id === asset.asset_id;
    const title = document.createElement('summary'); title.textContent = `${asset.name} · ${asset.frame_count} frames · ${asset.fps} FPS`;
    const info = document.createElement('p');
    info.textContent = `${asset.gender} · ${asset.up_axis.toUpperCase()}-up · ${asset.pose_layout} · ${asset.units}. Shape: ${asset.betas.join(', ')}. ${asset.reconstruction}`;
    const provenance = document.createElement('p'); provenance.className = 'muted';
    provenance.textContent = `Version: ${asset.asset_id}. Source SHA-256: ${asset.source_sha256}. Model: ${asset.model_path}. Model SHA-256: ${asset.model_sha256}. Metadata: ${JSON.stringify(asset.metadata_sources)}.`;
    const select = document.createElement('button');
    select.textContent = run?.motion_asset_id === asset.asset_id ? 'Selected for draft' : 'Use in selected draft';
    select.disabled = !run || run.read_only || run.motion_asset_id === asset.asset_id;
    select.onclick = async () => {
      try { await api(`/api/runs/${run.run_id}/motion`, {asset_id: asset.asset_id}); await refresh(); }
      catch (error) { failure(error); }
    };
    item.append(title, info, provenance, select); library.append(item);
  }
  if (!(state.motions || []).length) library.textContent = 'No managed motions.';
  root.append(library);
}
