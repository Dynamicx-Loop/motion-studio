import {inspectionGroups, inspectionChannel as channel} from './stage-inspection/bridge.js';

// A session belongs to one iframe navigation, not just one run/stage label.
let active, serial = 0;
const $ = id => document.getElementById(id);
function node(tag, text) {
  const element = document.createElement(tag);
  if (text !== undefined) element.textContent = text;
  return element;
}
function send(id, element) {
  if (!active?.ready) return;
  $('inspection').contentWindow.postMessage({channel, session:active.session, type:'command', id,
    value:element.value, checked:element.checked}, location.origin);
}
function layout(model) {
  const host = $('inspection-properties');
  host.replaceChildren();
  const heading = node('h3'); heading.id = 'inspection-property-title'; host.append(heading);
  const status = node('p'); status.id = 'inspection-property-status'; status.setAttribute('role', 'status'); host.append(status);
  active.fields = {}; active.groups = {};
  for (const [title, ids] of inspectionGroups) {
    const group = node('section'); active.groups[title] = group; group.className = 'inspection-property-group'; group.append(node('h4', title));
    const row = node('div'); row.className = 'inspection-property-actions';
    group.append(row);
    for (const id of ids) {
      const definition = model.controls[id];
      const element = node(definition.tag);
      element.id = `inspection-control-${id}`;
      element.setAttribute('data-inspection-control', id);
      if (definition.tag === 'button') {
        element.type = 'button'; element.onclick = () => send(id, element); row.append(element);
      } else {
        if (definition.tag === 'input') element.type = definition.type;
        const label = node('label');
        const caption = definition.label || ({timeline:'Timeline',frame:'Frame',slot:'Slot ID',segment:'Source segment',speed:'Speed',
          loop:'Loop playback',center:'Keep both centered horizontally',reference:'Reference pose',xray:'Points through geometry',
          surfaces:'Show meshes',lines:'Sparse paired lines'}[id]);
        if (definition.type === 'checkbox') label.append(element, document.createTextNode(caption));
        else label.append(document.createTextNode(caption), element);
        const event = definition.tag === 'select' ? 'onchange' : 'oninput';
        element[event] = () => send(id, element); group.append(label);
      }
      active.fields[id] = element;
    }
    if (title === 'Playback') {const time = node('p'); time.id = 'inspection-property-time'; group.append(time);}
    host.append(group);
  }
  const info = node('pre'); info.id = 'inspection-property-info'; host.append(info);
  const details = node('details'); details.append(node('summary', 'Segment color key'));
  const legend = node('div'); legend.id = 'inspection-property-legend'; details.append(legend); host.append(details);
  const disclosure = node('details'); disclosure.append(node('summary', 'Inspection scope'));
  const summary = node('p'); summary.id = 'inspection-property-summary';
  const scope = node('p'); scope.id = 'inspection-property-scope'; disclosure.append(summary,scope,
    node('p', 'Drag to orbit; scroll to zoom; click a point. Source semantic labels, paired slot identity and target body/geom ownership are separate. Sampling indices do not establish correspondence. Motion preserves exact saved frames/FPS; reconstructed hands are neutral and facial channels omitted. Centering and reference floor offsets affect display only. No contact or dynamics claim.'));
  host.append(disclosure);
  const error = node('p'); error.id = 'inspection-property-error'; error.setAttribute('role', 'alert'); host.append(error);
  const retry = node('button', 'Reload stage viewer'); retry.onclick = () => {
    if (active) showInspectionProperties(active.url, {reload:true});
  }; host.append(retry);
}
function apply(model) {
  if (!active.fields) layout(model);
  active.ready = model.ready;
  const staticPose = model.ready && model.controls.play.disabled && model.controls.frame.disabled;
  active.groups.Playback.hidden = staticPose;
  for (const [id, value] of Object.entries(model.controls)) {
    const element = active.fields[id];
    if (!element) continue;
    if (value.options && JSON.stringify(value.options) !== element.dataset.options) {
      element.replaceChildren(...value.options.map(([key, title]) => {const option = node('option', title); option.value = key; return option;}));
      element.dataset.options = JSON.stringify(value.options);
    }
    for (const property of ['min','max','step','value','checked']) if (value[property] !== undefined) element[property] = value[property];
    element.disabled = !model.ready || value.disabled;
    if (value.tag === 'button') element.textContent = value.text;
  }
  for (const [id, value] of Object.entries({title:model.text.title,status:model.text.loading || (staticPose ? 'Static reference pose · human left, robot right' : model.text.comparison),
    time:model.text.time,info:model.text.info,summary:model.text.summary,scope:model.text.scope,error:model.text.error})) {
    const element = $(`inspection-property-${id}`);
    if (element.textContent !== value) element.textContent = value;
  }
  const key = JSON.stringify(model.legend);
  if (key !== active.legend) {
    active.legend = key;
    $('inspection-property-legend').replaceChildren(...model.legend.map(([title, color]) => {
      const row = node('div', title); row.style.borderLeft = color; return row;
    }));
  }
}
window.addEventListener('message', event => {
  const message = event.data;
  if (!active || event.source !== $('inspection').contentWindow || event.origin !== location.origin ||
      message?.channel !== channel || message.type !== 'state' || message.session !== active.session) return;
  apply(message);
});

export function showInspectionProperties(url, {reload = false} = {}) {
  const host = $('inspection-properties');
  if (!url) {
    active = undefined; host.replaceChildren(); host.hidden = true; return undefined;
  }
  if (!reload && active?.url === url) return active.src;
  const session = `${Date.now()}-${++serial}`;
  const src = `/stage-inspection/index.html?bundle=${encodeURIComponent(url)}&session=${session}`;
  active = {url, src, session, ready:false}; host.hidden = false;
  const loading = node('p', 'Loading stage viewer controls…'); loading.setAttribute('role', 'status'); host.replaceChildren(loading);
  const retry = node('button', 'Reload stage viewer'); retry.onclick = () => showInspectionProperties(url, {reload:true}); host.append(retry);
  $('inspection').src = src;
  return src;
}
