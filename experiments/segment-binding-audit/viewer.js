import * as THREE from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
const $=id=>document.getElementById(id);
try {
const payload=await(await fetch('audit.json')).json(),data=payload.arms;
const scene=new THREE.Scene();scene.background=new THREE.Color('#101722');
const renderer=new THREE.WebGLRenderer({antialias:true});renderer.setPixelRatio(Math.min(devicePixelRatio,2));document.body.appendChild(renderer.domElement);
const camera=new THREE.PerspectiveCamera(38,1,.01,30),controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=true;
scene.add(new THREE.HemisphereLight(0xffffff,0x5b677d,2));const light=new THREE.DirectionalLight(0xffffff,2);light.position.set(1,3,4);scene.add(light);
scene.add(new THREE.GridHelper(8,32,0x576675,0x273244));
const sourceNames=[...new Set(data.visual.source_labels)].sort();for(const n of sourceNames)$('segment').add(new Option(n,n));
const allRegions=[...new Set(Object.values(data).flatMap(a=>a.regions))].sort();
function color(name){let i=sourceNames.indexOf(name);if(i<0)i=allRegions.indexOf(name);if(i<0)i=[...name].reduce((s,c)=>s+c.charCodeAt(0),0);return new THREE.Color().setHSL((i*.61803398875)%1,.7,.58);}
async function loadMesh(meta,human=false){const arr={};await Promise.all(['vertices','faces','regions',...(human?[]:['bodies'])].map(async key=>{const b=await(await fetch(meta[key].file)).arrayBuffer();arr[key]=key==='vertices'?new Float32Array(b):key==='faces'?new Uint32Array(b):new Uint16Array(b);}));return {meta,arr,human};}
const humanMesh=await loadMesh(payload.human_mesh,true),meshes={};
await Promise.all(Object.entries(data).map(async([a,d])=>{meshes[a]=await loadMesh(d.mesh);if(d.visual_mesh)meshes[a+'shell']=await loadMesh(d.visual_mesh);}));
let objects=[],clouds=[],selected=[],current,displayPoints;
function add(o){scene.add(o);objects.push(o);return o;}
function clear(){for(const o of objects){scene.remove(o);o.geometry?.dispose();o.material?.dispose();}objects=[];clouds=[];}
function floor(mesh){let y=Infinity;for(let i=1;i<mesh.arr.vertices.length;i+=3)y=Math.min(y,mesh.arr.vertices[i]);return y;}
function shift(points,x,y){return points.map(p=>[p[0]+x,p[1]-y,p[2]]);}
function meshObject(m,x,y,kind,ghost=false){const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.BufferAttribute(m.arr.vertices,3));g.setIndex(new THREE.BufferAttribute(m.arr.faces,1));g.computeVertexNormals();
if(kind!=='neutral'){const labels=kind==='body'?m.arr.bodies:m.arr.regions,names=m.human?m.meta.names:kind==='body'?m.meta.body_names:m.meta.region_names;const c=new Float32Array(labels.length*3);for(let i=0;i<labels.length;i++)color(names[labels[i]]).toArray(c,i*3);g.setAttribute('color',new THREE.BufferAttribute(c,3));}
const mat=new THREE.MeshStandardMaterial({color:kind==='neutral'?0x88939d:0xffffff,vertexColors:kind!=='neutral',side:THREE.DoubleSide,roughness:.8,transparent:ghost,opacity:ghost?.25:1,depthWrite:!ghost});const o=new THREE.Mesh(g,mat);o.position.set(x,-y,0);return add(o);}
function line(points,col=0xffff91){const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(points.flat(),3));return add(new THREE.LineSegments(g,new THREE.LineBasicMaterial({color:col,transparent:true,opacity:.8,depthTest:false})));}
function dots(points,colors,ids,size=.013){const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(points.flat(),3));g.setAttribute('color',new THREE.Float32BufferAttribute(colors.flat(),3));const o=add(new THREE.Points(g,new THREE.PointsMaterial({size,vertexColors:true,depthTest:!$('xray').checked})));o.renderOrder=3;o.userData.ids=ids;clouds.push(o);return o;}
function landmarks(d,offset,y){const a=d.anchors,p=n=>{const q=a[n];return[q[1]+offset,q[2]-y,q[0]];};let lines=[];for(const side of ['left','right']){for(const chain of [['shoulder_roll','elbow','wrist_roll'],['hip_pitch','knee','ankle_roll']])for(let i=0;i<chain.length-1;i++)lines.push(p(side+'_'+chain[i]+'_joint'),p(side+'_'+chain[i+1]+'_joint'));for(const joint of ['elbow','wrist_roll','knee','ankle_roll']){const q=p(side+'_'+joint+'_joint');lines.push([q[0]-.04,q[1],q[2]], [q[0]+.04,q[1],q[2]],[q[0],q[1]-.04,q[2]],[q[0],q[1]+.04,q[2]]);}}
const waist=p('waist_yaw_joint');lines.push([offset-.16,waist[1],0],[offset+.16,waist[1],0]);line(lines);}
function update(){clear();const arm=$('arm').value;current=data[arm];const rm=meshes[arm],hy=floor(humanMesh),ry=floor(rm);const h=shift(current.human,-1.05,hy),r=shift(current.projected,1.05,ry);displayPoints={h,r};
const filter=$('segment').value;selected=current.source_labels.map((_,i)=>i).filter(i=>filter==='all'||current.source_labels[i]===filter);
let id=Math.min(4095,Math.max(0,Math.trunc(+$('slot').value)||0));if(!selected.includes(id))id=selected[0];$('slot').value=id;
const surface=$('surface').value;if(surface!=='none'){meshObject(humanMesh,-1.05,hy,surface==='body'?'neutral':surface);meshObject(rm,1.05,ry,surface);}if($('shell').checked&&arm==='primitive')meshObject(meshes.primitiveshell,1.05,ry,'neutral',true);
const bad=new Set(current.invalid);for(const [which,points] of [['human',h],['robot',r]])dots(selected.map(i=>points[i]),selected.map(i=>bad.has(i)&&which==='robot'?[1,.05,.07]:color(which==='robot'&&$('color').value==='region'?current.regions[i]:current.source_labels[i]).toArray()),selected);
if($('lines').checked)line(selected.filter((_,i)=>i%32===0).flatMap(i=>[h[i],r[i]]),0x70829a);
line([h[id],r[id]],0xffffff);for(const p of [h[id],r[id]]){const o=add(new THREE.Mesh(new THREE.SphereGeometry(.016,12,8),new THREE.MeshBasicMaterial({color:0xffffff,depthTest:false})));o.position.set(...p);o.renderOrder=5;}
if($('planes').checked)landmarks(current,1.05,ry);
const metric=current.metrics.per_segment.find(x=>x.source===current.source_labels[id]);$('info').textContent=`Slot ${id} · ${current.source_labels[id]}\n55-class source ID: ${current.source55[id]}\nTarget zone: ${current.regions[id]}\nMesh: ${current.meshes[id]}\nBody: ${current.bodies[id]}\nMoving owner: ${current.rigid[id]}\nGeom ID: ${current.geom_ids[id]}\nProjection: ${bad.has(id)?'REJECTED buried':'accepted'}\nShown: ${selected.length} slots\nSegment zone compatibility: ${(metric.zone_precision*100).toFixed(1)}%\n(Strict diagnostic convention)`;
$('status').textContent=arm==='primitive'?'REJECTED production binding: 470 buried projections, 36 cross-body. Diagnostic only.':'Production binding accepted mechanically; anatomy and motion quality are separate.';$('status').style.color=arm==='primitive'?'#b91c1c':'#334155';
$('title').textContent=`Human source segments                         ${arm==='g1'?'G1 matched control':arm==='primitive'?'Astro primitive diagnostic':'Astro visual'} · ${filter}`;
const legend=$('color').value==='region'||surface==='region'?allRegions:sourceNames;$('legend').innerHTML=legend.map(n=>`<span style="border-left:8px solid #${color(n).getHexString()};padding-left:4px">${n}</span>`).join('');}
let viewMode='front';
function view(mode){viewMode=mode;const d=1.12*Math.max(2.0/(Math.tan(THREE.MathUtils.degToRad(camera.fov/2))*camera.aspect),.95/Math.tan(THREE.MathUtils.degToRad(camera.fov/2)));controls.target.set(0,.83,0);camera.position.set(mode==='side'?d:0,.83,mode==='rear'?-d:mode==='side'?0:d);controls.update();}
for(const k of ['arm','segment','slot','surface','color','xray','shell','lines','planes'])$(k).addEventListener('input',update);
for(const [id,step] of [['prev',-1],['next',1]])$(id).onclick=()=>{const k=selected.indexOf(+$('slot').value);$('slot').value=selected[(k+step+selected.length)%selected.length];update();};for(const k of ['front','rear','side'])$(k).onclick=()=>view(k);
const ray=new THREE.Raycaster();ray.params.Points.threshold=.018;let down;
renderer.domElement.addEventListener('pointerdown',e=>down=[e.clientX,e.clientY]);renderer.domElement.addEventListener('pointerup',e=>{if(!down||Math.hypot(e.clientX-down[0],e.clientY-down[1])>4)return;const box=renderer.domElement.getBoundingClientRect();ray.setFromCamera(new THREE.Vector2((e.clientX-box.left)/box.width*2-1,1-(e.clientY-box.top)/box.height*2),camera);const hit=ray.intersectObjects(clouds)[0];if(hit){$('slot').value=hit.object.userData.ids[hit.index];update();}});
function resize(){renderer.setSize(innerWidth-290,innerHeight);renderer.domElement.style.marginLeft='290px';camera.aspect=(innerWidth-290)/innerHeight;camera.updateProjectionMatrix();view(viewMode);}addEventListener('resize',resize);resize();view('front');update();renderer.setAnimationLoop(()=>{controls.update();renderer.render(scene,camera);});window.auditInspector={data,scene,camera,update,view,get selected(){return selected;},get slot(){return +$('slot').value;}};
}catch(e){$('error').textContent=e.stack||String(e);}
