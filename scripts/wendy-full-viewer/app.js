import * as T from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
const el=id=>document.getElementById(id);
async function binary(name,Type){const r=await fetch(name);if(!r.ok)throw Error(name+': '+r.status);return new Type(await r.arrayBuffer());}
async function main(){
const m=await(await fetch('manifest.json')).json();
const [f,s]=await Promise.all([binary('faces.bin',Uint32Array),binary('source.bin',Float32Array)]);
const cache=new Map(),pending=new Map();let failed=false;
async function loadChunk(k){
 if(k<0||k>=Math.ceil(m.frames/m.chunk_frames))return;
 if(cache.has(k))return cache.get(k);
 if(pending.has(k))return pending.get(k);
 const job=binary(`vertices-${String(k).padStart(3,'0')}.bin`,Float32Array).then(a=>{cache.set(k,a);while(cache.size>6)cache.delete(cache.keys().next().value);pending.delete(k);return a;}).catch(e=>{failed=true;el('error').textContent=e.message;throw e;});pending.set(k,job);return job;
}
await loadChunk(0);
const scene=new T.Scene();scene.background=new T.Color('#121b25');
const renderer=new T.WebGLRenderer({antialias:true});renderer.setPixelRatio(Math.min(devicePixelRatio,2));document.body.prepend(renderer.domElement);
const camera=new T.PerspectiveCamera(40,1,.01,100);const controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=true;
const cx=m.center[0],cz=m.center[2],target=new T.Vector3(cx-.4,.85,cz);
function view(x,y,z){camera.position.set(target.x+x,target.y+y,target.z+z);controls.target.copy(target);controls.update();}view(0,0,4.7);
el('front').onclick=()=>view(0,0,4.7);el('side').onclick=()=>view(4.7,0,0);el('reset').onclick=()=>view(2.5,1.2,5);
scene.add(new T.HemisphereLight(0xd7edff,0x566575,2));const light=new T.DirectionalLight(0xffffff,3);light.position.set(2,5,4);scene.add(light);
const grid=new T.GridHelper(10,40,0x60768a,0x2a3b4d);grid.position.set(cx,0,cz);scene.add(grid);
const geometry=new T.BufferGeometry(),pos=new T.BufferAttribute(new Float32Array(m.vertices*3),3);pos.setUsage(T.DynamicDrawUsage);geometry.setAttribute('position',pos);geometry.setIndex(new T.BufferAttribute(f,1));
const mesh=new T.Mesh(geometry,new T.MeshStandardMaterial({color:0x73b7e5,roughness:.75,side:T.DoubleSide}));mesh.frustumCulled=false;scene.add(mesh);
const edges=m.source_parents.flatMap((p,i)=>p<0?[]:[[p,i]]),lineGeo=new T.BufferGeometry(),linePos=new T.BufferAttribute(new Float32Array(edges.length*6),3);lineGeo.setAttribute('position',linePos);
const lines=new T.LineSegments(lineGeo,new T.LineBasicMaterial({color:0xffad54,depthTest:false}));lines.frustumCulled=false;lines.renderOrder=2;lines.visible=false;scene.add(lines);
let playing=true,t=0,last=null,current=-1;el('frame').max=m.frames-1;
function pause(){playing=false;el('play').textContent='Play';}
function seek(i){pause();t=Math.max(0,Math.min(m.frames-1,i))/m.fps;}
el('play').onclick=()=>{playing=!playing;el('play').textContent=playing?'Pause':'Play';};
el('frame').oninput=()=>seek(Number(el('frame').value));el('back').onclick=()=>seek(Math.round(t*m.fps)-1);el('next').onclick=()=>seek(Math.round(t*m.fps)+1);
el('mesh').onchange=()=>mesh.visible=el('mesh').checked;el('source').onchange=()=>lines.visible=el('source').checked;el('overlay').onchange=()=>{current=-1;};
el('summary').textContent=`${m.frames.toLocaleString()} frames · ${(m.frames/m.fps).toFixed(2)} s · ${m.fps.toFixed(0)} Hz`;
el('metrics').textContent=`Mean joint fit residual: ${(m.report.residual_mean_m*100).toFixed(1)} cm. Lowest mesh point: ${(m.report.mesh_min_y_m*100).toFixed(1)} cm.`;
function frame(i,v){const offset=(i%m.chunk_frames)*m.vertices*3;pos.array.set(v.subarray(offset,offset+m.vertices*3));pos.needsUpdate=true;geometry.computeVertexNormals();
 let k=0;for(const edge of edges)for(const j of edge)for(let a=0;a<3;a++)linePos.array[k++]=s[(i*m.source_joints+j)*3+a];linePos.needsUpdate=true;
 lines.position.x=el('overlay').checked?0:1.8;el('frame').value=i;el('status').textContent=`${(i/m.fps).toFixed(3)} / ${(m.frames/m.fps).toFixed(2)} s · frame ${i+1}/${m.frames}`;current=i;
}
function resize(){renderer.setSize(innerWidth,innerHeight);camera.aspect=innerWidth/innerHeight;camera.updateProjectionMatrix();}window.addEventListener('resize',resize);resize();
function animate(now){
 const next=last!==null&&playing?(t+(now-last)/1000*Number(el('speed').value))%(m.frames/m.fps):t;last=now;
 const i=Math.min(m.frames-1,Math.floor(next*m.fps+1e-7)),chunk=Math.floor(i/m.chunk_frames),v=cache.get(chunk);
 if(v){t=next;if(i!==current)frame(i,v);el('loading').textContent='';if(!failed)loadChunk(chunk+1).catch(()=>{});}
 else{el('loading').textContent='Loading motion…';if(!failed)loadChunk(chunk).catch(()=>{});}
 controls.update();renderer.render(scene,camera);requestAnimationFrame(animate);
}requestAnimationFrame(animate);
}
main().catch(e=>{el('error').textContent=e.stack;console.error(e);});
