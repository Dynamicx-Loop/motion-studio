import * as T from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
const el=id=>document.getElementById(id);
async function binary(name,Type){const r=await fetch(name);if(!r.ok)throw Error(name+': '+r.status);return new Type(await r.arrayBuffer());}
async function main(){
const m=await(await fetch('manifest.json')).json(),faces=await binary('faces.bin',Uint32Array);
const cache=new Map(),pending=new Map();let failed=false;
async function load(k){
 if(k<0||k>=Math.ceil(m.frames/m.chunk_frames))return;
 if(cache.has(k))return cache.get(k);if(pending.has(k))return pending.get(k);
 const p=Promise.all([0,1].map(j=>binary(`${j}-${String(k).padStart(3,'0')}.bin`,Float32Array))).then(v=>{cache.set(k,v);pending.delete(k);while(cache.size>4)cache.delete(cache.keys().next().value);return v;}).catch(e=>{failed=true;el('error').textContent=e.message;throw e;});pending.set(k,p);return p;
}
await load(0);
const scene=new T.Scene();scene.background=new T.Color('#121b25');
const renderer=new T.WebGLRenderer({antialias:true});renderer.setPixelRatio(Math.min(devicePixelRatio,2));document.body.prepend(renderer.domElement);
const camera=new T.PerspectiveCamera(40,1,.01,100),controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=true;
function view(x,y,z){camera.position.set(x,y+.8,z);controls.target.set(0,.8,0);controls.update();}view(0,1.2,8);
el('front').onclick=()=>view(0,.4,8);el('side').onclick=()=>view(7,1,3);el('reset').onclick=()=>view(0,1.2,8);
scene.add(new T.HemisphereLight(0xd7edff,0x566575,2));const light=new T.DirectionalLight(0xffffff,3);light.position.set(2,5,4);scene.add(light);scene.add(new T.GridHelper(12,48,0x60768a,0x2a3b4d));
const meshes=[0,1].map(j=>{const g=new T.BufferGeometry();g.setAttribute('position',new T.BufferAttribute(new Float32Array(m.vertices*3),3).setUsage(T.DynamicDrawUsage));g.setIndex(new T.BufferAttribute(faces,1));const mesh=new T.Mesh(g,new T.MeshStandardMaterial({color:j?0xffb366:0x73b7e5,roughness:.75,side:T.DoubleSide}));mesh.frustumCulled=false;scene.add(mesh);return mesh;});
function placement(){meshes.forEach((mesh,j)=>{mesh.position.set(-m.center[0]+(el('overlay').checked?0:(j?1.5:-1.5)),0,-m.center[2]);mesh.material.transparent=el('overlay').checked;mesh.material.opacity=el('overlay').checked?.55:1;mesh.material.depthWrite=!el('overlay').checked;});}placement();el('overlay').onchange=placement;
let playing=true,t=0,last=null,current=-1;el('frame').max=m.frames-1;
function seek(i){playing=false;el('play').textContent='Play';t=Math.max(0,Math.min(m.frames-1,i))/m.fps;}
el('play').onclick=()=>{playing=!playing;el('play').textContent=playing?'Pause':'Play';};el('frame').oninput=()=>seek(Number(el('frame').value));el('back').onclick=()=>seek(Math.round(t*m.fps)-1);el('next').onclick=()=>seek(Math.round(t*m.fps)+1);
el('summary').textContent=`${m.frames.toLocaleString()} frames · ${(m.frames/m.fps).toFixed(2)} seconds · ${m.fps.toFixed(3)} Hz`;
function frame(i,v){const offset=(i%m.chunk_frames)*m.vertices*3;meshes.forEach((mesh,j)=>{const p=mesh.geometry.attributes.position;p.array.set(v[j].subarray(offset,offset+m.vertices*3));p.needsUpdate=true;mesh.geometry.computeVertexNormals();});el('frame').value=i;el('status').textContent=`${(i/m.fps).toFixed(3)} s · frame ${i+1}/${m.frames}`;el('metrics').textContent=`Mesh difference incl. hands: ${(m.frame_mesh_error_m[i]*1000).toFixed(2)} mm`;current=i;}
function resize(){renderer.setSize(innerWidth,innerHeight);camera.aspect=innerWidth/innerHeight;camera.updateProjectionMatrix();}window.addEventListener('resize',resize);resize();
function animate(now){const next=last!==null&&playing?(t+(now-last)/1000*Number(el('speed').value))%(m.frames/m.fps):t;last=now;const i=Math.min(m.frames-1,Math.floor(next*m.fps+1e-7)),k=Math.floor(i/m.chunk_frames),v=cache.get(k);if(v){t=next;if(i!==current)frame(i,v);el('loading').textContent='';if(!failed)load(k+1).catch(()=>{});}else{el('loading').textContent='Loading motion…';if(!failed)load(k).catch(()=>{});}controls.update();renderer.render(scene,camera);requestAnimationFrame(animate);}requestAnimationFrame(animate);
}main().catch(e=>{el('error').textContent=e.stack;console.error(e);});
