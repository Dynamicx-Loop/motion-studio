import {OrbitControls} from '/vendor/OrbitControls.js';
import {loadSourceMesh} from './source-mesh-data.js';
import {sourceMeshStage} from './source-mesh-stage.js';
import {frameRequests} from './stage-inspection/playback.js';

let active, version = 0;
const node = (tag, text) => {const n = document.createElement(tag); if(text !== undefined)n.textContent=text; return n;};

export function hideSourcePreview() {
  version++;
  active?.dispose(); active = undefined;
  const container = document.getElementById('source-preview'), tools = document.getElementById('source-preview-tools');
  if(container){container.hidden=true;container.replaceChildren();}
  if(tools){tools.hidden=true;tools.replaceChildren();}
}

export async function showSourcePreview({asset, api, failure, onClose = () => {}, onUse}) {
  hideSourcePreview();
  const captured = version, container = document.getElementById('source-preview'), tools = document.getElementById('source-preview-tools');
  container.hidden=false;tools.hidden=false;
  const loading = node('p','Preparing human mesh preview…'); loading.className='source-loading'; container.append(loading);
  const close = node('button','Close preview'); close.type='button';
  close.onclick=()=>{hideSourcePreview();onClose();};tools.append(close);
  try {
    asset = await asset;
    if(captured !== version)return;
    const source = await loadSourceMesh(asset, api);
    if(captured !== version)return;
    const data = source.meta, stage = sourceMeshStage();
    container.replaceChildren(stage.renderer.domElement);
    stage.frame(source,0);
    const orbit = new OrbitControls(stage.camera,stage.renderer.domElement); orbit.target.copy(stage.target); orbit.update();
    const heading = node('div'); heading.className='source-preview-heading';
    const name = node('strong',asset.display_name || asset.name); const scope = node('small','Source human mesh · browse before retargeting'); heading.append(name,scope);
    if(onUse){const use=node('button','Use for retargeting');use.className='primary-action';use.onclick=()=>onUse(asset);heading.append(use);}
    const play=node('button','Play'),previous=node('button','←'),next=node('button','→');
    previous.setAttribute('aria-label','Previous source frame'); next.setAttribute('aria-label','Next source frame');
    const scrub=node('input');scrub.type='range';scrub.min=0;scrub.max=data.frame_count-1;scrub.step=1;scrub.value=0;scrub.setAttribute('aria-label','Source motion frame');
    const number=node('input');number.type='number';number.min=0;number.max=data.frame_count-1;number.step=1;number.value=0;number.setAttribute('aria-label','Exact source frame');
    const readout=node('output'),loop=node('input');loop.type='checkbox';loop.checked=true;loop.setAttribute('aria-label','Loop source motion');
    const loopLabel=node('label','Loop');loopLabel.append(loop);
    const centered=node('input');centered.type='checkbox';centered.checked=true;centered.setAttribute('aria-label','Center source horizontally');
    const centerLabel=node('label','Center view');centerLabel.append(centered);
    const playback=node('div');playback.className='source-playback';playback.append(play,previous,scrub,next,number);
    const secondary=node('div');secondary.className='source-preview-secondary';secondary.append(readout,loopLabel,centerLabel,close);
    const info=node('details');info.className='source-reconstruction-details';info.append(node('summary','Reconstruction details'),node('p',`${data.scope} ${data.coordinates} Preview mesh precision: ${data.quantization_m * 1000} mm. Center view changes only the display.`));
    tools.replaceChildren(heading,playback,secondary,info);
    let frame=0,playing=false,origin=0,raf,disposed=false;
    function draw(){if(!disposed)stage.draw(container.clientWidth,container.clientHeight);}
    function commit(value){
      frame=value;stage.frame(source,frame,centered.checked);
      scrub.value=number.value=frame;
      readout.textContent=`Frame ${frame} / ${data.frame_count-1} · ${(frame/data.fps).toFixed(3)} s · ${Number(data.fps.toFixed(4))} FPS`;
      previous.disabled=frame===0;next.disabled=frame===data.frame_count-1;draw();
    }
    const requests=frameRequests(source.replay,commit,(loading)=>{play.classList.toggle('buffering',loading);play.setAttribute('aria-busy',String(loading));});
    async function seek(value){await requests.request(Math.max(0,Math.min(data.frame_count-1,Math.trunc(value))));}
    function stop(){playing=false;play.textContent='Play';cancelAnimationFrame(raf);}
    async function tick(now){
      if(!playing||disposed)return;
      let target=Math.floor((now-origin)*data.fps/1000);
      if(target>=data.frame_count){if(loop.checked){target%=data.frame_count;origin=now-target*1000/data.fps;}else{await seek(data.frame_count-1);stop();return;}}
      try{if(target!==frame)await seek(target);if(playing&&!disposed)raf=requestAnimationFrame(tick);}
      catch(error){stop();failure(error);}
    }
    play.onclick=()=>{if(playing){stop();return;}if(frame===data.frame_count-1)seek(0).catch(failure);playing=true;play.textContent='Pause';origin=performance.now()-(frame===data.frame_count-1?0:frame)*1000/data.fps;raf=requestAnimationFrame(tick);};
    function manual(value){stop();seek(value).catch(failure);}
    centered.onchange=()=>commit(frame);
    scrub.oninput=()=>manual(Number(scrub.value));number.oninput=()=>{if(number.value!==''&&number.validity.valid)manual(Number(number.value));};number.onchange=number.onblur=()=>manual(Number(number.value));number.onkeydown=event=>{if(event.key==='Enter'){event.preventDefault();manual(Number(number.value));}};previous.onclick=()=>manual(frame-1);next.onclick=()=>manual(frame+1);
    orbit.addEventListener('change',draw);const resize=new ResizeObserver(draw);resize.observe(container);
    const visibility=()=>{if(document.hidden)stop();};document.addEventListener('visibilitychange',visibility);
    active={dispose(){disposed=true;stop();requests.cancel();resize.disconnect();orbit.dispose();stage.dispose();document.removeEventListener('visibilitychange',visibility);}};
    commit(0);
  } catch(error) {
    if(captured===version){container.replaceChildren(node('p','Human mesh preview unavailable. Retry the preview or check status for details.'));failure(error);}
  }
}
