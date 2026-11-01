import {loadSourceMesh} from './source-mesh-data.js';
import {sourceMeshStage} from './source-mesh-stage.js';

// One WebGL context serves every library card. Cards retain only 2D posters;
// at most one hovered/focused/explicitly playing card advances at a time.
let stage, queue=Promise.resolve(), active, raf, generation=0;
const sources=new Map(),observers=new Set();
async function source(asset,api){
  const key=asset.asset_id;
  if(sources.has(key)){const value=sources.get(key);sources.delete(key);sources.set(key,value);return value;}
  const pending=loadSourceMesh(asset,api);sources.set(key,pending);
  while(sources.size>3)sources.delete(sources.keys().next().value);
  try{return await pending;}catch(error){sources.delete(key);throw error;}
}
function paint(entry,data,frame){
  if(!entry.canvas.isConnected)return;
  stage ||= sourceMeshStage({thumbnail:true});stage.frame(data,frame);stage.draw(entry.canvas.width,entry.canvas.height);
  entry.canvas.getContext('2d').drawImage(stage.renderer.domElement,0,0,entry.canvas.width,entry.canvas.height);
  entry.status.hidden=true;
}
function stop(){
  generation++;cancelAnimationFrame(raf);
  if(active){active.button.textContent='▶';active.button.setAttribute('aria-pressed','false');active.root.classList.remove('thumbnail-playing');active=undefined;}
}
async function start(entry,explicit=false){
  if(active===entry){if(explicit){entry.explicit=!entry.explicit;if(!entry.explicit)stop();}return;}
  stop();const token=generation;active=entry;entry.explicit=explicit;
  entry.button.textContent='Ⅱ';entry.button.setAttribute('aria-pressed','true');entry.root.classList.add('thumbnail-playing');
  try{
    const asset=await entry.getAsset(),data=await source(asset,entry.api);
    if(token!==generation||!entry.canvas.isConnected)return;
    const origin=performance.now();let previous=-1,last=0;
    async function tick(now){
      if(token!==generation||!entry.canvas.isConnected||document.hidden){if(token===generation)stop();return;}
      const frame=Math.floor((now-origin)*data.meta.fps/1000)%data.meta.frame_count;
      if(frame!==previous&&now-last>=1000/24){
        try{await data.replay.load(frame);if(token!==generation)return;data.replay.pin(frame);paint(entry,data,frame);previous=frame;last=now;}
        catch(error){if(token===generation){stop();entry.status.hidden=false;entry.status.textContent='Preview unavailable';}return;}
      }
      raf=requestAnimationFrame(tick);
    }
    raf=requestAnimationFrame(tick);
  }catch(error){if(token===generation){stop();entry.status.textContent='Preview unavailable';entry.status.hidden=false;}}
}
export function motionThumbnail(root,getAsset,api){
  const wrapper=document.createElement('div');wrapper.className='motion-thumbnail';
  const canvas=document.createElement('canvas');canvas.width=240;canvas.height=360;canvas.setAttribute('aria-label','Human mesh motion preview');canvas.setAttribute('role','img');
  const status=document.createElement('small');status.textContent='Loading mesh…';status.className='thumbnail-status';
  const button=document.createElement('button');button.type='button';button.className='thumbnail-play';button.textContent='▶';button.setAttribute('aria-label','Play motion thumbnail');button.setAttribute('aria-pressed','false');
  wrapper.append(canvas,status,button);
  const entry={root,canvas,status,button,getAsset,api,explicit:false};
  button.onclick=event=>{event.stopPropagation();start(entry,true);};
  root.addEventListener('pointerenter',()=>start(entry));
  root.addEventListener('pointerleave',()=>{if(active===entry&&!entry.explicit)stop();});
  button.onfocus=()=>start(entry);
  root.addEventListener('focusout',event=>{if(active===entry&&!entry.explicit&&!root.contains(event.relatedTarget))stop();});
  // Lazy posters avoid reconstructing the entire imported library at once.
  const observer=new IntersectionObserver(entries=>{
    if(!entries.some(item=>item.isIntersecting))return;observer.disconnect();observers.delete(observer);
    queue=queue.catch(()=>{}).then(async()=>{
      if(!canvas.isConnected)return;
      try{const asset=await getAsset();if(!canvas.isConnected)return;const data=await source(asset,api);if(active!==entry){await data.replay.load(0);paint(entry,data,0);}}
      catch(error){status.textContent='Preview unavailable';}
    });
  },{root:document.getElementById('library'),rootMargin:'120px'});
  observers.add(observer);observer.observe(root);
  return wrapper;
}
export function resetMotionThumbnails(){stop();for(const observer of observers)observer.disconnect();observers.clear();}
