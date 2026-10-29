'use strict';
const reportData = JSON.parse(document.getElementById('report-data').textContent);
const translations = JSON.parse(document.getElementById('report-i18n').textContent);
const byId = id => document.getElementById(id);
let language = new URL(location.href).searchParams.get('lang');
if (!['en','zh'].includes(language)) {
  try { language = localStorage.getItem('umr-report-language'); } catch (_) { /* file/private storage may be disabled */ }
}
if (!['en','zh'].includes(language)) language = 'en';
const tr = (text, variables = {}) => Object.entries(variables).reduce((s,[key,value])=>s.replaceAll('{'+key+'}',value), language==='zh' ? translations[text] ?? text : text);
const esc = text => String(text).replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
const percent = value => value === null || value === undefined ? 'N/A' : (value * 100).toFixed(1) + '%';
const segmentNames = {'head/face':'Head / face',head:'Head (native: includes neck)',hips:'Hips',torso:'Torso',neck:'Neck',leftUpLeg:'Left thigh',rightUpLeg:'Right thigh',leftForeArm:'Left forearm',rightForeArm:'Right forearm',leftShoulder:'Left shoulder / clavicle',rightShoulder:'Right shoulder / clavicle',leftUpperArm:'Left UpperArm (artificial subdivision)',rightUpperArm:'Right UpperArm (artificial subdivision)',leftArm:'Left arm',rightArm:'Right arm',leftLeg:'Left shin',rightLeg:'Right shin',leftFoot:'Left foot',rightFoot:'Right foot',leftHand:'Left hand',rightHand:'Right hand'};
const label = (segment, scheme='common') => {
  if(segment==='leftArm'||segment==='rightArm') {
    const side=segment==='leftArm'?'Left':'Right';
    return tr(side+(scheme==='common'?' upper arm (Arm + UpperArm)':' Arm (remaining upper-arm region)'));
  }
  return tr(segmentNames[segment] || segment);
};
const textOriginals = new WeakMap(), attributeOriginals = new WeakMap();
function translateDOM(root = document.body) {
  // Mutate text/attributes in place: selections, disclosures, frame and hash survive.
  const walker=document.createTreeWalker(root,NodeFilter.SHOW_TEXT);
  for(let node=walker.nextNode();node;node=walker.nextNode()) {
    if(node.parentElement.closest('script,style,code,pre,#language-toggle,[data-dynamic]')) continue;
    if(!textOriginals.has(node)) textOriginals.set(node,node.nodeValue);
    const original=textOriginals.get(node), key=original.trim();
    node.nodeValue = language==='zh' && translations[key] ? original.replace(key,translations[key]) : original;
  }
  for(const element of root.querySelectorAll('[aria-label],[alt]')) {
    if(element.id==='language-toggle') continue;
    if(!attributeOriginals.has(element)) attributeOriginals.set(element, Object.fromEntries(['aria-label','alt'].filter(a=>element.hasAttribute(a)).map(a=>[a,element.getAttribute(a)])));
    for(const [attribute,original] of Object.entries(attributeOriginals.get(element))) element.setAttribute(attribute,tr(original));
  }
  document.title=tr('UMR canonical Astro — static and motion evidence');
}
for(const id of ['center-chart','segment-table','transfer','explore-arm','explore-segment','inspector-status']) byId(id).dataset.dynamic='true';
let enlargedSource;
let inspectorStatus = byId('inspector-status').textContent;
function setInspectorStatus(message) { inspectorStatus=message;byId('inspector-status').textContent=tr(message); }
function renderCenterChart() {
  const region=byId('chart-region').value, metric=byId('chart-metric').value;
  const metricLabel=tr(metric==='precision'?'Compatible-zone precision':'Target-region coverage within 20 mm');
  const left=215,right=835,x=value=>left+value*(right-left);
  let svg=`<svg viewBox="0 0 1040 330" role="img" aria-label="${esc(label(region))}: ${metricLabel}, spine1 → bbox50"><title>${esc(label(region))}: ${metricLabel}</title>`;
  for(const tick of [0,.25,.5,.75,1]) svg+=`<line x1="${x(tick)}" y1="30" x2="${x(tick)}" y2="285" stroke="#dbe4e8"/><text x="${x(tick)}" y="310" text-anchor="middle" font-size="17" fill="#536874">${tick*100}%</text>`;
  let row=0;
  for(const robot of ['astro','g1']) for(const source of ['smplx','soma']) {
    const a=reportData.arms[`${source}_${robot}_spine1`].common.find(r=>r.segment===region)[metric];
    const b=reportData.arms[`${source}_${robot}_bbox50`].common.find(r=>r.segment===region)[metric];
    const y=55+row++*68,color=source==='smplx'?'#147e78':'#b06018';
    svg+=`<text x="12" y="${y+5}" font-size="20" fill="#173440">${robot==='g1'?'G1':'Astro'} · ${source==='smplx'?'SMPL-X':'SOMA'}</text><line x1="${x(a)}" y1="${y}" x2="${x(b)}" y2="${y}" stroke="${color}" stroke-width="3"/><circle cx="${x(a)}" cy="${y}" r="7" fill="white" stroke="${color}" stroke-width="2.5"/><circle cx="${x(b)}" cy="${y}" r="5" fill="${color}"/><text x="860" y="${y+5}" font-size="19" fill="#234756">${percent(a)} → ${percent(b)}</text>`;
  }
  byId('center-chart').innerHTML=`<div class="chart-title">${esc(label(region))} · ${metricLabel}</div><small>${tr('Higher values indicate more compatible assignments or greater sampled coverage; neither alone defines overall quality.')}</small>${svg}</svg>`;
}
for(const [key,arm] of Object.entries(reportData.arms)) byId('explore-arm').add(new Option(tr(arm.label),key));
byId('explore-arm').value='canonical_smplx_astro_bbox50_raw';
function renderSegments() {
  const arm=reportData.arms[byId('explore-arm').value],scheme=byId('explore-scheme').value;
  const rows=arm[scheme],old=byId('explore-segment').value;
  byId('explore-segment').replaceChildren(...rows.map(r=>new Option(label(r.segment,scheme),r.segment)));
  if(rows.some(r=>r.segment===old)) byId('explore-segment').value=old;
  const selected=byId('explore-segment').value;
  const headers=['Source region','Compatible / slots','Precision','Leakage','Coverage ≤20 mm','High-confidence compatible / slots'];
  byId('segment-table').innerHTML=`<div class="table-scroll"><table><caption>${esc(tr(arm.label))} · ${tr(scheme==='common'?'common 18':'native 19')} · ${tr('4096 total slots')}</caption><thead><tr>${headers.map(h=>`<th scope="col">${tr(h)}</th>`).join('')}</tr></thead><tbody>${rows.map(r=>`<tr class="${r.segment===selected?'selected-row':''}"><th scope="row">${esc(label(r.segment,scheme))}</th><td>${r.compatible} / ${r.slots}</td><td>${percent(r.precision)}</td><td>${percent(1-r.precision)}</td><td>${percent(r.coverage)}</td><td>${r.high_slots==null?'—':r.high_compatible+' / '+r.high_slots}</td></tr>`).join('')}</tbody></table></div>`;
  const transfer=arm['transfer_'+scheme][selected],row=rows.find(r=>r.segment===selected),zones=Object.entries(transfer).sort((a,b)=>b[1]-a[1]);
  byId('transfer').innerHTML=`<strong>${esc(label(selected,scheme))} → ${tr('target geometric zones')}</strong><div class="transfer-list">${zones.map(([zone,n])=>`<span>${esc(tr(zone))}: <strong>${n}</strong> (${percent(n/row.slots)})</span>`).join('')}</div><p class="caption">${tr('Total {n} source slots. Zone assignment is separate from mesh/body ownership. No points are removed from this distribution.',{n:row.slots})}</p>`;
}
function applyLanguage(next, save=false) {
  language=next;document.documentElement.lang=language==='zh'?'zh-CN':'en';
  byId('language-toggle').setAttribute('aria-label',language==='zh'?'切换为英文；当前语言：中文':'Switch to Chinese; current language English');
  byId('language-toggle').setAttribute('aria-pressed',String(language==='zh'));
  byId('language-toggle').textContent=language==='zh'?'EN / 中 ✓':'EN ✓ / 中';
  translateDOM();for(const option of byId('explore-arm').options)option.text=tr(reportData.arms[option.value].label);renderCenterChart();renderSegments();setInspectorStatus(inspectorStatus);
  if(enlargedSource) byId('large-image').alt=enlargedSource.alt;
  if(byId('inspector-host').firstElementChild) byId('inspector-host').firstElementChild.title=byId('inspector-kind').selectedOptions[0].text;
  if(save) {
    try {localStorage.setItem('umr-report-language',language);} catch (_) { /* optional preference */ }
    const url=new URL(location.href);url.searchParams.set('lang',language);
    try {history.replaceState(null,'',url);} catch (_) { /* file URL may restrict history */ }
  }
}
byId('language-toggle').addEventListener('click',()=>{
  const anchor=[...document.querySelectorAll('main>section')].find(s=>s.getBoundingClientRect().bottom>90);
  const offset=anchor?.getBoundingClientRect().top;
  applyLanguage(language==='en'?'zh':'en',true);
  // Stay at the same section and relative position even when paragraph heights change.
  if(anchor) window.scrollBy({top:anchor.getBoundingClientRect().top-offset,behavior:'instant'});
});
byId('chart-region').addEventListener('change',renderCenterChart);
byId('chart-metric').addEventListener('change',renderCenterChart);
for(const id of ['explore-arm','explore-scheme','explore-segment']) byId(id).addEventListener('change',renderSegments);
for(const button of document.querySelectorAll('[data-center]')) button.addEventListener('click',()=>{
  for(const other of document.querySelectorAll('[data-center]')) {
    const active=other===button;other.classList.toggle('active',active);other.setAttribute('aria-pressed',active);byId('figure-'+other.dataset.center).hidden=!active;
  }
});
for(const img of document.querySelectorAll('.zoomable')) img.addEventListener('click',()=>{
  enlargedSource=img;byId('large-image').src=img.src;byId('large-image').alt=img.alt;byId('image-dialog').showModal();
});
byId('close-image').addEventListener('click',()=>byId('image-dialog').close());
byId('print').addEventListener('click',()=>window.print());
function inspectorLink(){byId('inspector-link').href=`inspectors/${byId('inspector-kind').value}/index.html`;}
byId('inspector-kind').addEventListener('change',inspectorLink);
byId('load-inspector').addEventListener('click',()=>{
  inspectorLink();
  if(location.protocol==='file:') {
    setInspectorStatus('Start the report’s local HTTP server (command in Record & reproduction), then open http://127.0.0.1:8770/ to load the inspector. Narrative, figures and tables already work here.');return;
  }
  const frame=document.createElement('iframe');frame.src=byId('inspector-link').href;frame.title=byId('inspector-kind').selectedOptions[0].text;frame.allowFullscreen=true;
  byId('inspector-host').replaceChildren(frame);
  setInspectorStatus('Loading the saved inspector. Its meshes are local; Three.js is loaded from the original CDN. Use Open full window for more space.');
  frame.addEventListener('load',()=>setInspectorStatus('Inspector document loaded. Meshes may still be loading; any renderer errors appear inside its panel. This performs visualization only.'));
});
byId('unload-inspector').addEventListener('click',()=>{
  byId('inspector-host').replaceChildren();setInspectorStatus('Inspector unloaded. Its saved numerical results remain available above.');
});
applyLanguage(language);

for(const button of document.querySelectorAll('[data-canonical-center]')) button.addEventListener('click',()=>{
  for(const other of document.querySelectorAll('[data-canonical-center]')){
    const active=other===button;other.classList.toggle('active',active);other.setAttribute('aria-pressed',String(active));
    byId('canonical-figure-'+other.dataset.canonicalCenter).hidden=!active;
  }
});
function revealHash(){
  const id=decodeURIComponent(location.hash.slice(1)),target=document.getElementById(id);
  if(!target)return;
  let parent=target.parentElement;while(parent){if(parent.tagName==='DETAILS')parent.open=true;parent=parent.parentElement;}
}
addEventListener('hashchange',revealHash);revealHash();
