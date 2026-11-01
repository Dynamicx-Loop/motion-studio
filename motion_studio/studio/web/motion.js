// Motion preparation owns only imports, metadata inspection and draft selection.
export function renderMotion({state, run, api, refresh, failure}) {
  const root = document.getElementById('motion-assets');
  root.replaceChildren();
  const details = document.createElement('details');
  const summary = document.createElement('summary'); summary.textContent = 'Import a motion';
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
  const submit = document.createElement('button'); submit.textContent = 'Add to motion library'; form.append(submit);
  form.onsubmit = async event => {
    event.preventDefault(); submit.disabled = true;
    document.getElementById('error').textContent = '';
    const fields = Object.fromEntries(new FormData(form));
    const metadata = {};
    for (const key of ['fps', 'gender', 'up_axis']) if (fields[key] !== '') metadata[key] = key === 'fps' ? Number(fields[key]) : fields[key];
    try {
      const asset = await api('/api/motions', {source_path: fields.source_path, metadata});
      await refresh();
    } catch (error) { failure(error); submit.disabled = false; }
  };
  details.append(summary, form); root.append(details);
}
