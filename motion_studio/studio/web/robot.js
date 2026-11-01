import {createRobotPreview} from '/robot-preview.js';
const $ = id => document.getElementById(id);
let preview, context, currentKey, asset, qpos, poses = [], requestVersion = 0, timer;
const node = (tag,text) => {const value=document.createElement(tag);if(text!==undefined)value.textContent=text;return value;};
const control = (label,element) => {const wrap=node('label',label);if(!element.hasAttribute('aria-label'))element.setAttribute('aria-label',label);wrap.append(element);return wrap;};

export function renderRobot(value) {
  context = value;
  const {state,run,api,refresh,failure} = value;
  const key = `${run?.run_id}/${run?.revision_id}/${state.robots?.map(x=>x.asset_id).join(',')}`;
  if (key === currentKey) return;
  currentKey = key; requestVersion++;
  const library = $('robot-assets'); library.replaceChildren();
  const importDetails=node('details');importDetails.append(node('summary','Import by local path'));
  const form = node('form');
  const path = node('input'); path.required=true;path.placeholder='/absolute/path/robot.xml';path.name='source_path';
  const derive = node('input');derive.type='checkbox';derive.name='derive_free_root';
  const submit = node('button','Import local MJCF');
  form.append(control('Robot MJCF file',path),control('Allow fixed-to-floating root derivation on a copy',derive),submit);
  form.onsubmit = async event => {
    event.preventDefault(); submit.disabled=true;
    try {await api('/api/robots',{source_path:path.value,derive_free_root:derive.checked});await refresh();}
    catch(error){failure(error);}finally{submit.disabled=false;}
  };
  importDetails.append(form);library.append(importDetails);
  const editor=$('robot-editor'), viewport=$('robot-preview'); editor.replaceChildren();
  viewport.hidden = true;
  if (!run || run.read_only || !run.is_latest) {library.append(node('p','Select a draft to prepare a robot pose.'));return;}
  const select=node('select');select.id='robot-select';
  const placeholder=node('option','Choose imported robot');placeholder.value='';select.append(placeholder);
  for (const item of state.robots || []) {
    const option=node('option',item.name);option.value=item.asset_id;select.append(option);
  }
  select.value=run.robot_asset_id||'';
  select.onchange=()=>load(select.value).catch(failure);
  library.append(control('Prepare robot in selected draft',select));
  async function load(id) {
    const version=++requestVersion;
    editor.replaceChildren();
    if(!id){viewport.hidden=true;return;}
    asset=state.robots.find(x=>x.asset_id===id);qpos=[...asset.default_qpos];
    poses=await api(`/api/robots/${id}/poses`);
    if(version!==requestVersion)return;
    const selected=poses.find(x=>x.pose_id===run.robot_pose_id);
    if(selected)qpos=[...selected.qpos];
    viewport.hidden=false;$('empty').hidden=true;
    if(!preview)preview=createRobotPreview(viewport);
    const geometry=await api(`/api/robots/${id}/geometry`);
    if(version!==requestVersion)return;
    preview.geometry(geometry); build(selected);
    await updatePreview(); preview.fit();
  }
  function build(selected) {
    editor.replaceChildren(node('h3','Robot pose'));
    editor.append(node('p','Metres · radians · root quaternion wxyz. Preview edits are unsaved until Save pose.'));
    if(asset.derived.length)editor.append(node('p',asset.derived.join('; ')));
    const torso=node('select');torso.id='robot-torso';
    for(const body of asset.bodies){const option=node('option',body);option.value=body;torso.append(option);}
    torso.value=selected?.torso_body||asset.root_body;
    editor.append(control('Torso / centering body',torso));
    const name=node('input');name.id='robot-pose-name';name.value=selected?.name||'T-pose';name.maxLength=120;
    editor.append(control('Named pose',name));
    const saved=node('select');saved.id='robot-saved-pose';saved.append(node('option','Load saved named pose'));
    for(const pose of poses){const option=node('option',pose.name);option.value=pose.pose_id;saved.append(option);}
    saved.onchange=()=>{const pose=poses.find(x=>x.pose_id===saved.value);if(pose){qpos=[...pose.qpos];build(pose);updatePreview().catch(failure);}};
    editor.append(saved);
    const official=node('button','Load official G1 T-pose');official.type='button';
    official.onclick=async()=>{official.disabled=true;try{
      const preset=await api(`/api/robots/${asset.asset_id}/official-pose`);
      qpos=[...preset.qpos];build(preset);await updatePreview();preview.fit();
    }catch(error){failure(error);official.disabled=false;}};
    if(asset.source_entry==='g1_29dof.xml')editor.append(official);

    const root=node('details');root.open=false;root.append(node('summary','Root translation / orientation'));
    ['X (m)','Y (m)','Z (m)','qw','qx','qy','qz'].forEach((label,i)=>{
      const input=node('input');input.type='number';input.step='.01';input.value=qpos[i];input.setAttribute('aria-label',`Root ${label}`);
      input.oninput=()=>{qpos[i]=Number(input.value);schedulePreview();};root.append(control(label,input));
    });
    editor.append(root);
    const normalize=node('button','Normalize root quaternion');normalize.type='button';
    normalize.onclick=()=>{const norm=Math.hypot(...qpos.slice(3,7));if(norm){qpos.splice(3,4,...qpos.slice(3,7).map(x=>x/norm));build({name:name.value,torso_body:torso.value});schedulePreview();}};
    editor.append(normalize);
    const search=node('input');search.placeholder='Search joints';search.setAttribute('aria-label','Search joints');editor.append(search);
    const joints=node('div');joints.className='robot-joints';
    for(const joint of asset.joints){
      const row=node('div');row.dataset.joint=joint.name.toLowerCase();
      row.append(node('small',`${joint.name} [${joint.minimum_rad.toFixed(4)}, ${joint.maximum_rad.toFixed(4)}] rad`));
      const numeric=node('input'),slider=node('input');numeric.type='number';slider.type='range';
      for(const input of [numeric,slider]){input.min=joint.minimum_rad;input.max=joint.maximum_rad;input.step='any';input.value=qpos[joint.qpos_index];input.setAttribute('aria-label',`${joint.name} ${input.type==='range'?'slider':'radians'}`);}
      numeric.oninput=()=>{qpos[joint.qpos_index]=Number(numeric.value);slider.value=numeric.value;schedulePreview();};
      slider.oninput=()=>{qpos[joint.qpos_index]=Number(slider.value);numeric.value=slider.value;schedulePreview();};
      row.append(numeric,slider);joints.append(row);
    }
    search.oninput=()=>{for(const row of joints.children)row.hidden=!row.dataset.joint.includes(search.value.toLowerCase());};
    const jointDetails=node('details');jointDetails.append(node('summary',`${asset.joints.length} joint controls`),search,joints);editor.append(jointDetails);
    const reset=node('button','Reset compiled reference pose');reset.type='button';
    reset.onclick=()=>{qpos=[...asset.default_qpos];build({name:name.value,torso_body:torso.value});updatePreview().catch(failure);};
    const save=node('button','Save pose to fresh revision');save.id='robot-save-pose';
    save.onclick=async()=>{save.disabled=true;try{await api(`/api/runs/${run.run_id}/robot-pose`,{asset_id:asset.asset_id,name:name.value,qpos,torso_body:torso.value});await refresh();}catch(error){failure(error);save.disabled=false;}};
    editor.append(reset,save,node('p','Saving preserves the source and prior revisions. New pose invalidates downstream computation.'));
  }
  if(run.robot_asset_id)load(run.robot_asset_id).catch(failure);
}
function schedulePreview(){clearTimeout(timer);timer=setTimeout(()=>updatePreview().catch(context.failure),200);}
async function updatePreview(){
  const id=asset?.asset_id,version=++requestVersion;if(!id)return;
  $('robot-preview-status').textContent='Updating compiled pose…';
  try{
    const result=await context.api(`/api/robots/${id}/preview`,{qpos});
    if(version===requestVersion){preview.pose(result);$('robot-preview-status').textContent='T-pose preview · metres / Z-up · floor follows mesh bounds (display only)';}
  }catch(error){if(version===requestVersion)$('robot-preview-status').textContent='Invalid pose; previous preview retained';throw error;}
}
