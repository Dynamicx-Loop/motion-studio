import * as T from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
const el=id=>document.getElementById(id);
async function binary(name,Type){const r=await fetch(name);if(!r.ok)throw Error(name+': '+r.status);return new Type(await r.arrayBuffer());}
async function main(){
const m=await(await fetch('manifest.json')).json(),scene=new T.Scene();scene.background=new T.Color('#121b25');
const renderer=new T.WebGLRenderer({antialias:true});renderer.setPixelRatio(Math.min(devicePixelRatio,2));document.body.prepend(renderer.domElement);
const camera=new T.PerspectiveCamera(40,1,.01,100),controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=true;
function view(x,y,z){camera.position.set(x,y+.65,z);controls.target.set(0,.65,0);controls.update();}view(0,1,6.5);
el('front').onclick=()=>view(0,.3,6.5);el('side').onclick=()=>view(6,1,3);el('reset').onclick=()=>view(0,1,6.5);
scene.add(new T.HemisphereLight(0xd7edff,0x566575,2));const light=new T.DirectionalLight(0xffffff,3);light.position.set(2,5,4);scene.add(light);scene.add(new T.GridHelper(12,48,0x60768a,0x2a3b4d));
for(const option of el('robot').options)option.disabled=!m.robots[option.value];
const actors={};
for(const [robot,info] of Object.entries(m.robots)){
 const geometry=await Promise.all(info.parts.map(async part=>{const [v,f]=await Promise.all([binary(part.vertices,Float32Array),binary(part.faces,Uint32Array)]);const g=new T.BufferGeometry();g.setAttribute('position',new T.BufferAttribute(v,3));g.setIndex(new T.BufferAttribute(f,1));g.computeVertexNormals();return g;}));
 actors[robot]=await Promise.all(info.variants.map(async (v,j)=>{const transforms=await binary(v.transforms,Float32Array),group=new T.Group();scene.add(group);const parts=geometry.map((g,k)=>{const base=new T.Color(...info.parts[k].color);base.lerp(new T.Color(j?0xffb366:0x73b7e5),.8);const mesh=new T.Mesh(g,new T.MeshStandardMaterial({color:base,roughness:.6,metalness:.2,side:T.DoubleSide}));mesh.matrixAutoUpdate=false;mesh.frustumCulled=false;group.add(mesh);return mesh;});return {group,parts,transforms};}));
}
let playing=true,t=0,last=null,current=-1;el('frame').max=m.frames-1;
function placement(){for(const [robot,pair] of Object.entries(actors)){const c=m.robots[robot].center;pair.forEach((a,j)=>{a.group.visible=robot===el('robot').value;a.group.position.set(-c[0]+(el('overlay').checked?0:(j?1.3:-1.3)),0,-c[2]);a.parts.forEach(mesh=>{mesh.material.transparent=el('overlay').checked;mesh.material.opacity=el('overlay').checked?.55:1;mesh.material.depthWrite=!el('overlay').checked;});});}current=-1;const r=m.robots[el('robot').value].report;el('summary').textContent=` · Mean joint difference: ${r.joint_angle_difference_deg.mean.toFixed(3)}° · Mean root difference: ${(r.root_position_difference_m.mean*1000).toFixed(2)} mm`;}
placement();el('robot').onchange=placement;el('overlay').onchange=placement;
function seek(i){playing=false;el('play').textContent='Play';t=Math.max(0,Math.min(m.frames-1,i))/m.fps;}
el('worst').onclick=()=>seek(m.robots[el('robot').value].report.largest_joint_difference_at.frame_index);
el('play').onclick=()=>{playing=!playing;el('play').textContent=playing?'Pause':'Play';};el('frame').oninput=()=>seek(Number(el('frame').value));el('back').onclick=()=>seek(Math.round(t*m.fps)-1);el('next').onclick=()=>seek(Math.round(t*m.fps)+1);
function frame(i){for(const a of actors[el('robot').value]){const r=a.transforms;for(let k=0;k<a.parts.length;k++){const s=(i*a.parts.length+k)*12;a.parts[k].matrix.set(r[s],r[s+1],r[s+2],r[s+9],r[s+3],r[s+4],r[s+5],r[s+10],r[s+6],r[s+7],r[s+8],r[s+11],0,0,0,1);a.parts[k].matrixWorldNeedsUpdate=true;}}el('frame').value=i;el('status').textContent=`${(i/m.fps).toFixed(3)} s · frame ${i+1}/${m.frames}`;el('metrics').textContent=`Joint RMS difference: ${m.robots[el('robot').value].frame_joint_rms_deg[i].toFixed(3)}°`;current=i;}
function resize(){renderer.setSize(innerWidth,innerHeight);camera.aspect=innerWidth/innerHeight;camera.updateProjectionMatrix();}window.addEventListener('resize',resize);resize();
function animate(now){if(last!==null&&playing)t=(t+(now-last)/1000*Number(el('speed').value))%(m.frames/m.fps);last=now;const i=Math.min(m.frames-1,Math.floor(t*m.fps+1e-7));if(i!==current)frame(i);controls.update();renderer.render(scene,camera);requestAnimationFrame(animate);}requestAnimationFrame(animate);
}main().catch(e=>{el('error').textContent=e.stack;console.error(e);});
