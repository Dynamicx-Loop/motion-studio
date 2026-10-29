// Derived from UMR's MIT-licensed AdaPT correspondence viewer's point-cloud approach.
import * as THREE from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
const $ = id => document.getElementById(id);
try {
const response=await fetch('./pairings.json');if(!response.ok)throw Error(response.status);
const data=await response.json(), scene=new THREE.Scene();scene.background=new THREE.Color('#101722');
const renderer=new THREE.WebGLRenderer({antialias:true});renderer.setPixelRatio(Math.min(devicePixelRatio,2));document.body.appendChild(renderer.domElement);
const camera=new THREE.PerspectiveCamera(40,1,0.01,100), controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=true;
function reset(){camera.position.set(-0.5,1.0,5.4);controls.target.set(-0.5,0.8,0);controls.update();}reset();
scene.add(new THREE.GridHelper(10,40,0x526175,0x273244));
let clouds=[], helpers=[], current=null;
const colors=data.visual.human.map(p=>[(p[0]+1)/2,Math.max(0,Math.min(1,(p[1]+0.95)/1.65)),Math.max(0,Math.min(1,(p[2]+0.2)/0.4))]);
function positions(array,x){const y=Math.min(...array.map(p=>p[1]));return array.map(p=>[p[0]+x,p[1]-y,p[2]]);}
function cloud(points,color,size=0.01){const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(points.flat(),3));g.setAttribute('color',new THREE.Float32BufferAttribute(color.flat(),3));const o=new THREE.Points(g,new THREE.PointsMaterial({size,vertexColors:true}));scene.add(o);return o;}
function lines(points,color,opacity=1){const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(points.flat(),3));const o=new THREE.LineSegments(g,new THREE.LineBasicMaterial({color,transparent:true,opacity}));scene.add(o);helpers.push(o);return o;}
function clear(objects){for(const o of objects){scene.remove(o);o.geometry.dispose();o.material.dispose();}}
function update(){clear(clouds);clear(helpers);clouds=[];helpers=[];current=data[$('arm').value];const h=positions(current.human,-1.15),r=positions(current[$('mode').value],1.15),bad=new Set(current.invalid),seg=$('segment').value;
const selected=[];for(let i=0;i<4096;i++)if(seg==='all'||current.source_labels[i]===seg)selected.push(i);
for(const points of [h,r]){const object=cloud(selected.map(i=>points[i]),selected.map(i=>points===r&&bad.has(i)?[1,0.05,0.08]:colors[i]),+$('size').value);object.userData.slotIds=selected;clouds.push(object);}
if($('input').checked){const p=positions(current.input,1.15);clouds.push(cloud(p,p.map(()=>[0.32,0.38,0.46]),0.004));}
if($('lines').checked){const pairs=[];for(const i of selected)if(i%32===0)pairs.push(h[i],r[i]);lines(pairs,0xc4d0dd,0.2);}
let id=Math.max(0,Math.min(4095,Math.trunc(+$('slot').value)||0));if(!selected.includes(id))id=selected[0];$('slot').value=id;lines([h[id],r[id]],0xffffff,0.9);
for(const p of [h[id],r[id]]){const m=new THREE.Mesh(new THREE.SphereGeometry(0.022,12,8),new THREE.MeshBasicMaterial({color:0xffb52e,depthTest:false}));m.position.set(...p);scene.add(m);helpers.push(m);}
$('verdict').textContent=current.invalid.length?'Training finished. Production primitive binding REJECTED: 470 buried projections. Diagnostic inspection only.':'Training finished. Production visual binding accepted.';
$('verdict').style.color=current.invalid.length?'#b91c1c':'#166534';
$('robotTitle').textContent=`Astro · ${$('arm').value} · ${$('mode').value}`;
$('info').textContent=`Slot ${id} of 4096\nSource: ${current.source_labels[id]}\nRobot body: ${current.bodies[id]}\nProjection: ${bad.has(id)?'REJECTED — buried':'accepted'}\nArm rejected: ${current.invalid.length}/4096\nRaw → surface: ${(1000*Math.hypot(...current.learned[id].map((v,k)=>v-current.projected[id][k]))).toFixed(2)} mm\nShown segment: ${selected.length} slots`;
}
for(const name of [...new Set(data.visual.source_labels)].sort()){$('segment').add(new Option(name,name));}
for(const id of ['arm','mode','segment','slot','lines','input','size'])$(id).addEventListener('input',update);
$('previous').onclick=()=>{$('slot').value=Math.max(0,+$('slot').value-1);update();};$('next').onclick=()=>{$('slot').value=Math.min(4095,+$('slot').value+1);update();};$('reset').onclick=reset;
const ray=new THREE.Raycaster();ray.params.Points.threshold=0.018;let down=null;
renderer.domElement.addEventListener('pointerdown',e=>{down=[e.clientX,e.clientY];});renderer.domElement.addEventListener('pointerup',e=>{if(!down||Math.hypot(e.clientX-down[0],e.clientY-down[1])>4)return;ray.setFromCamera(new THREE.Vector2(e.clientX/innerWidth*2-1,1-e.clientY/innerHeight*2),camera);const hit=ray.intersectObjects(clouds.filter(c=>c.userData.slotIds))[0];if(hit){$('slot').value=hit.object.userData.slotIds[hit.index];update();}});
function resize(){renderer.setSize(innerWidth,innerHeight);camera.aspect=innerWidth/innerHeight;camera.updateProjectionMatrix();}addEventListener('resize',resize);resize();update();renderer.setAnimationLoop(()=>{controls.update();renderer.render(scene,camera);});
window.pairingInspector={data,renderer,scene,camera,update};
}catch(error){$('error').textContent=error.stack||String(error);}
