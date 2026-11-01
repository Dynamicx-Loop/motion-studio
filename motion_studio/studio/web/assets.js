import {showSourcePreview, hideSourcePreview} from './source-preview.js';
import {motionThumbnail, resetMotionThumbnails} from './motion-thumbnails.js';
import {motionLabel, motionSummary, motionItems} from './motion-library.js';
const $ = id => document.getElementById(id);
const node = (tag,text) => {const n=document.createElement(tag);if(text!==undefined)n.textContent=text;return n;};
let context, busy=false, inspectionDropBound=false;
const MIME='application/x-umr-robot-preset';
function sameSelection(value) {
  return value.run?.run_id === context.run?.run_id && value.run?.revision_id === context.run?.revision_id;
}
function requireSelection(value) {
  if (!sameSelection(value)) throw Error('Selection changed while preparing the asset. Select the intended draft and retry.');
}
async function editableDraft(value) {
  requireSelection(value);
  const {run,api}=value;
  if(run && !run.read_only && run.is_latest && !run.stages.some(s=>s.stage!=='preparation'&&s.status==='available'))return run;
  const draft=await api('/api/runs',{name:`Asset study · ${new Date().toLocaleTimeString()}`});
  requireSelection(value);
  await api('/api/selection',{run_id:draft.run_id});return draft;
}
async function action(work) {
  if(busy)return;busy=true;$('asset-status').textContent='Preparing local asset…';
  const value=context;
  try {await work(value);$('asset-status').textContent='Ready';}
  catch(error){value.failure(error);$('asset-status').textContent=error.message;}
  finally{busy=false;}
}
async function useRobot(id) {
  await action(async current=>{
    hideSourcePreview();
    const value=await current.api('/api/catalog/robots',{id}),run=await editableDraft(current);
    requireSelection(current);
    await current.api(`/api/runs/${run.run_id}/robot-pose`,{asset_id:value.asset.asset_id,
      name:value.pose.name,qpos:value.pose.qpos,torso_body:value.pose.torso_body});
    if(sameSelection(current))await current.refresh('preparation');
  });
}
const sampleAssets = new Map(), sampleIds = new Map(), sampleSettled = new Set();
function unresolvedSamples(){return (context.state.catalog?.motions||[]).some(item=>item.available&&!item.asset_id&&!sampleIds.has(item.id)&&!sampleSettled.has(item.id));}
function updateImportedVisibility(){
  const knownIds=new Set([...(context.state.catalog?.motions||[]).map(value=>value.asset_id),...sampleIds.values()]);
  for(const row of document.querySelectorAll('.motion-card[data-managed-id]'))row.hidden=knownIds.has(row.dataset.managedId)||unresolvedSamples();
}
async function resolveMotion(item) {
  if (item.asset) return {...item.asset,display_name:motionLabel(item)};
  if (!sampleAssets.has(item.id)) sampleAssets.set(item.id,context.api('/api/catalog/motions',{id:item.id}).catch(error=>{sampleAssets.delete(item.id);throw error;}));
  try {
    const asset=await sampleAssets.get(item.id);sampleIds.set(item.id,asset.asset_id);
    return {...asset,display_name:motionLabel(item)};
  } finally {sampleSettled.add(item.id);updateImportedVisibility();}
}
async function useMotion(item) {
  if(typeof item==='string')item=motionItems(context.state).find(value=>value.id===item);
  if(!item)return;
  await action(async current=>{
    hideSourcePreview();
    const asset=await resolveMotion(item),run=await editableDraft(current);
    requireSelection(current);
    await current.api(`/api/runs/${run.run_id}/motion`,{asset_id:asset.asset_id});
    if(sameSelection(current)){hideSourcePreview();await current.refresh('preparation');}
  });
}
async function previewMotion(item) {
  try {
    await showSourcePreview({asset:resolveMotion(item),api:context.api,failure:context.failure,onUse:()=>useMotion(item)});
  } catch(error){context.failure(error);}
}
function motionCard(item) {
  const available=item.available||Boolean(item.asset);
  const root=node('article');root.className='asset-card motion-card';root.dataset.assetId=item.id;root.dataset.assetType='motion';
  if(item.asset&&!item.sample){root.dataset.managedId=item.asset.asset_id;root.hidden=unresolvedSamples();}
  root.draggable=available;
  root.append(motionThumbnail(root,()=>resolveMotion(item).then(asset=>{
    metadata.textContent=motionSummary({...item,asset});
    const chosen=asset.asset_id===context.run?.motion_asset_id;use.disabled=!available||chosen;use.textContent=chosen?'Selected for retargeting':'Use for retargeting';
    return asset;
  }),context.api));
  const copy=node('div');copy.className='motion-card-copy';
  const badge=node('small',item.sample?'SAMPLE':'IMPORTED');badge.className='asset-badge';
  const title=node('strong',motionLabel(item));title.title=motionLabel(item);
  const metadata=node('small',motionSummary(item));metadata.className='motion-summary';
  const preview=node('button','Preview');preview.disabled=!available;preview.onclick=()=>previewMotion(item);
  const selected=item.asset?.asset_id===context.run?.motion_asset_id;
  const use=node('button',selected?'Selected for retargeting':'Use for retargeting');use.className='motion-use';use.disabled=!available||selected;use.onclick=()=>useMotion(item);
  const actions=node('div');actions.className='motion-card-actions';actions.append(preview,use);
  copy.append(badge,title,metadata,actions);
  const details=node('details');details.className='motion-details';details.append(node('summary','Details & provenance'));
  details.ontoggle=async()=>{
    if(!details.open||details.dataset.loaded)return;
    details.dataset.loaded='true';const content=node('div','Loading metadata…');details.append(content);
    try{
      const asset=await resolveMotion(item);metadata.textContent=motionSummary({...item,asset});
      const dl=node('dl');
      for(const [label,value] of [['Source file',asset.name],['Frames',asset.frame_count],['Original FPS',asset.fps],['Conventions',`${asset.gender} · ${asset.up_axis?.toUpperCase()}-up · ${asset.units} · ${asset.pose_layout}`],['Body shape',asset.betas?.join(', ')],['Reconstruction',asset.reconstruction],['Asset version',asset.asset_id],['Source SHA-256',asset.source_sha256],['Model',asset.model_path],['Model SHA-256',asset.model_sha256],['Metadata sources',JSON.stringify(asset.metadata_sources)]]){dl.append(node('dt',label),node('dd',value));}
      const original=node('a','Original NPZ');original.href=`/api/motions/${asset.asset_id}/source`;content.replaceChildren(dl,original);
    }catch(error){content.textContent=error.message;details.dataset.loaded='';}
  };
  root.append(copy,details);
  root.ondragstart=e=>{if(e.target.closest('button,details')){e.preventDefault();return;}$('inspection').style.pointerEvents='none';e.dataTransfer.setData('application/x-motion-studio-motion',item.id);e.dataTransfer.effectAllowed='copy';};
  root.ondragend=()=>{$('inspection').style.pointerEvents='';$('viewport').classList.remove('drop-active');};
  return root;
}
function card(item,type) {
  const root=node('article');root.className='asset-card';root.draggable=item.available;
  root.dataset.assetId=item.id;root.dataset.assetType=type;
  if(type==='robot'){
    const image=node('img');image.src=`/thumbnails/${item.id}.png`;image.alt=`${item.name} model in its native T-pose`;
    image.loading='lazy';root.append(image);
  } else {const icon=node('div','⌁');icon.className='motion-icon';root.append(icon);}
  root.append(node('strong',item.name),node('small',item.description));
  const use=node('button',type==='robot'?'Add robot':'Use & preview');use.disabled=!item.available;
  use.onclick=()=>type==='robot'?useRobot(item.id):useMotion(item.id);root.append(use);
  root.ondragstart=e=>{$('inspection').style.pointerEvents='none';e.dataTransfer.setData(type==='robot'?MIME:'application/x-motion-studio-motion',item.id);e.dataTransfer.setData('text/plain',`${type}:${item.id}`);e.dataTransfer.effectAllowed='copy';};
  root.ondragend=()=>{$('inspection').style.pointerEvents='';$('viewport').classList.remove('drop-active');};
  return root;
}
export function renderAssets(value) {
  context=value;
  $('builtin-robots').replaceChildren(...(value.state.catalog?.robots||[]).map(x=>card(x,'robot')));
  resetMotionThumbnails();
  $('sample-motions').replaceChildren(...motionItems(value.state).map(motionCard));
  updateImportedVisibility();
  // Identity lookup is small and independent of lazy mesh reconstruction. Failures
  // settle too, so an unavailable sample never hides unrelated imported clips.
  for(const item of value.state.catalog?.motions||[])if(item.available&&!item.asset_id&&!sampleIds.has(item.id))resolveMotion(item).catch(()=>{});
  for(const tab of document.querySelectorAll('[data-library-tab]'))tab.onclick=()=>{
    document.querySelectorAll('[data-library-panel]').forEach(panel=>panel.hidden=panel.dataset.libraryPanel!==tab.dataset.libraryTab);
    document.querySelectorAll('[data-library-tab]').forEach(button=>button.setAttribute('aria-selected',String(button===tab)));
  };
  const viewport=$('viewport');
  viewport.ondragover=e=>{e.preventDefault();viewport.classList.add('drop-active');e.dataTransfer.dropEffect='copy';};
  viewport.ondragleave=e=>{if(!viewport.contains(e.relatedTarget))viewport.classList.remove('drop-active');};
  viewport.ondrop=async e=>{
    e.preventDefault();viewport.classList.remove('drop-active');$('inspection').style.pointerEvents='';
    const robot=e.dataTransfer.getData(MIME),motion=e.dataTransfer.getData('application/x-motion-studio-motion');
    if(robot)return useRobot(robot);if(motion)return useMotion(motion);
    try{await prepareFiles(await droppedFiles(e.dataTransfer));}catch(error){context.failure(error);}
  };
  const inspection=$('inspection');
  const wireFrame=()=>{
    const doc=inspection.contentDocument;if(!doc)return;
    doc.ondragover=e=>viewport.ondragover(e);
    doc.ondrop=e=>viewport.ondrop(e);
    doc.ondragleave=e=>viewport.ondragleave(e);
  };
  if(!inspectionDropBound){inspection.addEventListener('load',wireFrame);inspectionDropBound=true;}
  wireFrame();
  $('robot-upload-files').onchange=e=>prepareFiles([...e.target.files]).catch(value.failure);
  $('robot-upload-folder').onchange=e=>prepareFiles([...e.target.files]).catch(value.failure);
  $('upload-robot').onsubmit=e=>{e.preventDefault();upload().catch(value.failure);};
}
let pending=[];
async function droppedFiles(transfer) {
  const entries=[...transfer.items].map(x=>x.webkitGetAsEntry?.()).filter(Boolean),result=[];
  async function walk(entry,prefix='') {
    if(entry.isFile){const file=await new Promise((ok,no)=>entry.file(ok,no));file.bundlePath=prefix+file.name;result.push(file);}
    else if(entry.isDirectory){const reader=entry.createReader();while(true){const batch=await new Promise((ok,no)=>reader.readEntries(ok,no));if(!batch.length)break;for(const child of batch)await walk(child,prefix+entry.name+'/');}}
  }
  if(entries.length)for(const entry of entries)await walk(entry);else result.push(...transfer.files);
  return result;
}
async function prepareFiles(files) {
  pending=files;
  if(!files.length)return;
  if(files.length>2048||files.reduce((n,f)=>n+f.size,0)>128*1024*1024)throw Error('Choose up to 2048 files / 128 MiB.');
  const entry=$('upload-entry');entry.replaceChildren();
  for(const file of files.filter(f=>f.name.toLowerCase().endsWith('.xml'))){const option=node('option',file.webkitRelativePath||file.bundlePath||file.name);option.value=option.textContent;entry.append(option);}
  $('upload-summary').textContent=`${files.length} file(s) ready. Select the main MJCF, then import.`;
  $('upload-robot').hidden=false;
  document.querySelector('.upload-details').open=true;
  $('upload-robot').scrollIntoView({block:'nearest'});
  $('robot-zip-entry').hidden=!(files.length===1 && files[0].name.toLowerCase().endsWith('.zip'));
  document.querySelector('[data-library-tab="robots"]').click();
}
async function upload() {
  const selectedFiles=[...pending],entryPath=$('robot-zip-entry').hidden?$('upload-entry').value:$('robot-zip-entry').value.trim(),deriveFreeRoot=$('upload-derive').checked;
  await action(async current=>{
    const files=[];
    for(const file of selectedFiles){const data=await new Promise((ok,no)=>{const reader=new FileReader();reader.onload=()=>ok(reader.result.split(',')[1]);reader.onerror=no;reader.readAsDataURL(file);});files.push({path:file.webkitRelativePath||file.bundlePath||file.name,data});}
    requireSelection(current);
    const asset=await current.api('/api/robot-upload',{files,entry_path:entryPath,derive_free_root:deriveFreeRoot});
    const run=await editableDraft(current);
    requireSelection(current);
    await current.api(`/api/runs/${run.run_id}/robot-pose`,{asset_id:asset.asset_id,name:'Imported reference pose',qpos:asset.default_qpos,torso_body:asset.root_body});
    if(sameSelection(current)){hideSourcePreview();await current.refresh('preparation');$('upload-robot').hidden=true;pending=[];}
  });
}
