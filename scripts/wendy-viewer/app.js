import * as T from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
const el=id=>document.getElementById(id);
async function binary(name,Type){const r=await fetch(name);if(!r.ok)throw Error(name+': '+r.status);return new Type(await r.arrayBuffer());}
async function main(){
const m=await (await fetch('manifest.json')).json();
const [v,f,s]=await Promise.all([binary('vertices.bin',Float32Array),binary('faces.bin',Uint32Array),binary('source.bin',Float32Array)]);
const scene=new T.Scene();scene.background=new T.Color('#121b25');
const renderer=new T.WebGLRenderer({antialias:true});renderer.setPixelRatio(Math.min(devicePixelRatio,2));document.body.prepend(renderer.domElement);
const camera=new T.PerspectiveCamera(40,1,.01,100);const controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=true;
const cx=m.center[0],cz=m.center[2];const target=new T.Vector3(cx-.35,.85,cz);
function view(x,y,z){camera.position.set(target.x+x,target.y+y,target.z+z);controls.target.copy(target);controls.update();}view(0,0,6);
el('front').onclick=()=>view(0,0,6);el('side').onclick=()=>view(6,0,0);el('reset').onclick=()=>view(2.5,1.2,6);
scene.add(new T.HemisphereLight(0xd7edff,0x566575,2));const light=new T.DirectionalLight(0xffffff,3);light.position.set(2,5,4);scene.add(light);
const grid=new T.GridHelper(10,40,0x60768a,0x2a3b4d);grid.position.set(cx,0,cz);scene.add(grid);
const geometry=new T.BufferGeometry();const pos=new T.BufferAttribute(new Float32Array(m.vertices*3),3);pos.setUsage(T.DynamicDrawUsage);geometry.setAttribute('position',pos);geometry.setIndex(new T.BufferAttribute(f,1));
const mesh=new T.Mesh(geometry,new T.MeshStandardMaterial({color:0x73b7e5,roughness:.75,side:T.DoubleSide}));mesh.frustumCulled=false;scene.add(mesh);
const edges=m.source_parents.flatMap((p,i)=>p<0?[]:[[p,i]]);const lineGeo=new T.BufferGeometry();const linePos=new T.BufferAttribute(new Float32Array(edges.length*6),3);lineGeo.setAttribute('position',linePos);
const lines=new T.LineSegments(lineGeo,new T.LineBasicMaterial({color:0xffad54,depthTest:false}));lines.frustumCulled=false;lines.renderOrder=2;scene.add(lines);lines.visible=el('source').checked;
const robotGroup=new T.Group();scene.add(robotGroup);let robotTransforms=null;let tunedTransforms=null;let baselineTransforms=null;const robotParts=[];
if(m.robot){
 robotTransforms=await binary(m.robot.transforms,Float32Array);tunedTransforms=robotTransforms;
 if(m.robot_baseline)baselineTransforms=await binary(m.robot_baseline.transforms,Float32Array);
 for(const part of m.robot.meshes){
  const [rv,rf]=await Promise.all([binary(part.vertices,Float32Array),binary(part.faces,Uint32Array)]);
  const g=new T.BufferGeometry();g.setAttribute('position',new T.BufferAttribute(rv,3));g.setIndex(new T.BufferAttribute(rf,1));g.computeVertexNormals();
  const mat=new T.MeshStandardMaterial({color:new T.Color(...part.color),roughness:.6,metalness:.25,side:T.DoubleSide});
  const obj=new T.Mesh(g,mat);obj.matrixAutoUpdate=false;obj.frustumCulled=false;robotParts.push(obj);robotGroup.add(obj);
 }
 robotGroup.position.set(cx+1-m.robot.center[0],0,cz-m.robot.center[2]);
}else{el('robot').disabled=true;}
el('robot').onchange=()=>robotGroup.visible=el('robot').checked;

let playing=true,t=0,last=null,current=-1;el('frame').max=m.frames-1;
el('variant').disabled=!baselineTransforms;
el('variant').onchange=()=>{
 const baseline=el('variant').value==='baseline';robotTransforms=baseline?baselineTransforms:tunedTransforms;
 const info=baseline?m.robot_baseline:m.robot;
 robotGroup.position.set(cx+1-info.center[0],0,cz-info.center[2]);current=-1;showMetrics(info);
};

el('play').onclick=()=>{playing=!playing;el('play').textContent=playing?'Pause':'Play';};
el('frame').oninput=()=>{playing=false;el('play').textContent='Play';t=Number(el('frame').value)/m.fps;};
el('mesh').onchange=()=>mesh.visible=el('mesh').checked;el('source').onchange=()=>lines.visible=el('source').checked;
el('overlay').onchange=()=>{current=-1;};
function showMetrics(info){
 el('metrics').textContent=`${el('variant').value==='baseline'?'Original':'Tuned'} Astro · 360 frames · 120 Hz. `;
 if(info?.report.torso)el('metrics').textContent+=`Mean torso-axis difference: ${info.report.torso.torso_axis_error_mean_deg.toFixed(1)}°. `;
 if(info)el('metrics').textContent+=`Lowest robot mesh: ${(info.report.min_visual_mesh_height_m*100).toFixed(1)} cm.`;
}
showMetrics(m.robot);
function frame(i){pos.array.set(v.subarray(i*m.vertices*3,(i+1)*m.vertices*3));pos.needsUpdate=true;geometry.computeVertexNormals();
let k=0;for(const edge of edges)for(const j of edge)for(let a=0;a<3;a++)linePos.array[k++]=s[(i*m.source_joints+j)*3+a];linePos.needsUpdate=true;
const overlay=el('overlay').checked;mesh.position.x=-1;lines.position.x=overlay?-1:1;
if(robotTransforms){for(let k=0;k<robotParts.length;k++){
 const a=(i*robotParts.length+k)*12, r=robotTransforms;
 robotParts[k].matrix.set(r[a],r[a+1],r[a+2],r[a+9],r[a+3],r[a+4],r[a+5],r[a+10],r[a+6],r[a+7],r[a+8],r[a+11],0,0,0,1);
 robotParts[k].matrixWorldNeedsUpdate=true;
}}

el('frame').value=i;el('status').textContent=`${i+1}/${m.frames} · ${((m.start_frame+i)/m.fps).toFixed(3)} s`;current=i;}
function resize(){renderer.setSize(innerWidth,innerHeight);camera.aspect=innerWidth/innerHeight;camera.updateProjectionMatrix();}window.addEventListener('resize',resize);resize();
function animate(now){if(last!==null&&playing)t=(t+(now-last)/1000*Number(el('speed').value))%(m.frames/m.fps);last=now;const i=Math.min(m.frames-1,Math.floor(t*m.fps));if(i!==current)frame(i);controls.update();renderer.render(scene,camera);requestAnimationFrame(animate);}requestAnimationFrame(animate);
}
main().catch(e=>{el('error').textContent=e.stack;console.error(e);});
