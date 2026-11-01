// Owned v1 renderer contract. Only the renderer owns frame/slot/display state.
export const inspectionGroups = [
  ['Playback', ['play', 'back-frame', 'next-frame', 'timeline', 'frame', 'speed', 'loop', 'center', 'reference']],
  ['Segments & bindings', ['segment', 'slot', 'previous', 'next', 'xray', 'surfaces', 'lines']],
  ['Camera', ['front', 'rear', 'side']]
];
const textIds = ['title', 'summary', 'comparison', 'scope', 'loading', 'time', 'info', 'error'];
const channel = 'motion-studio-inspection-v1';

export function inspectionBridge(view = window, doc = document) {
  const query = new URLSearchParams(view.location.search);
  const bundle = query.get('bundle'), session = query.get('session');
  let base = new URL('.', view.location.href), embedded = false, ready = false, queued = false;
  if (bundle !== null) {
    base = new URL(bundle, view.location.href);
    if (base.origin !== view.location.origin || !base.pathname.startsWith('/inspection/') ||
        !base.pathname.endsWith('/index.html') || base.search || base.hash || !session || view.parent === view)
      throw Error('Invalid embedded inspection resource');
    base = new URL('.', base); embedded = true;
    doc.documentElement.classList.add('embedded');
  }
  const ids = inspectionGroups.flatMap(([, controls]) => controls);
  function publish() {
    if (!embedded || queued) return;
    queued = true;
    queueMicrotask(() => {
      queued = false;
      const controls = Object.fromEntries(ids.map(id => {
        const element = doc.getElementById(id);
        return [id, {tag:element.tagName.toLowerCase(), type:element.type,
          label:element.closest('label')?.childNodes[0]?.textContent.trim() || element.getAttribute('aria-label') || '',
          value:element.value, checked:element.checked, disabled:element.disabled,
          min:element.min, max:element.max, step:element.step, text:element.tagName === 'BUTTON' ? element.textContent : '',
          options:element.tagName === 'SELECT' ? Array.from(element.options, option => [option.value, option.textContent]) : undefined}];
      }));
      const text = Object.fromEntries(textIds.map(id => [id, doc.getElementById(id).textContent]));
      const legend = Array.from(doc.getElementById('legend').children, row => [row.textContent, row.style.borderLeft]);
      view.parent.postMessage({channel, session, type:'state', ready, controls, text, legend}, view.location.origin);
    });
  }
  if (embedded) view.addEventListener('message', event => {
    const message = event.data;
    if (event.source !== view.parent || event.origin !== view.location.origin ||
        message?.channel !== channel || message.session !== session || message.type !== 'command' || !ready || !ids.includes(message.id)) return;
    const element = doc.getElementById(message.id);
    if (element.disabled) return;
    if (element.tagName === 'BUTTON') element.click();
    else {
      if (element.type === 'checkbox') {
        if (typeof message.checked !== 'boolean') return;
        element.checked = message.checked;
      } else {
        if (typeof message.value !== 'string') return;
        if (element.tagName === 'SELECT' && !Array.from(element.options).some(option => option.value === message.value)) return;
        if (['range', 'number'].includes(element.type) && !Number.isFinite(Number(message.value))) return;
        element.value = message.value;
      }
      element.dispatchEvent(new Event('input', {bubbles:true}));
      element.dispatchEvent(new Event('change', {bubbles:true}));
    }
    publish();
  });
  publish();
  return {
    embedded,
    resource(path) {
      const result = new URL(path, base);
      if (result.origin !== base.origin || !result.pathname.startsWith(base.pathname)) throw Error('Inspection resource escapes its bundle');
      return result.href;
    },
    publish,
    ready() {ready = true; publish();}
  };
}

export const inspectionChannel = channel;
