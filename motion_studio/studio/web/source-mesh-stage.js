import * as THREE from 'three';
import {sourcePositions} from './source-mesh-data.js';

// Used by the main viewer and one shared offscreen thumbnail renderer.
export function sourceMeshStage({thumbnail = false} = {}) {
  const scene = new THREE.Scene(); scene.background = new THREE.Color('#f1f4f7');
  const camera = new THREE.PerspectiveCamera(38, 1, .01, 2000); camera.up.set(0, 0, 1);
  const renderer = new THREE.WebGLRenderer({antialias:true, alpha:false});
  renderer.setPixelRatio(thumbnail ? 1 : Math.min(devicePixelRatio, 2));
  scene.add(new THREE.HemisphereLight(0xffffff, 0x76869b, 2.4));
  const key = new THREE.DirectionalLight(0xffffff, 3); key.position.set(3, -4, 7); scene.add(key);
  const fill = new THREE.DirectionalLight(0xd3e4ff, 1.3); fill.position.set(-3, 2, 4); scene.add(fill);
  const grid = new THREE.GridHelper(40, 80, 0xb8c6d5, 0xdce3eb); grid.rotation.x = Math.PI / 2; scene.add(grid);
  const material = new THREE.MeshStandardMaterial({color:0x799cc1, roughness:.72, metalness:.03, side:THREE.DoubleSide});
  let mesh, current, renderWidth, renderHeight, envelope;
  const target = new THREE.Vector3();
  function setSource(source, index) {
    if (source === current) return;
    current = source;
    if (mesh) {scene.remove(mesh); mesh.geometry.dispose();}
    const positions = sourcePositions(source, index);
    const geometry = new THREE.BufferGeometry();
    geometry.setIndex(new THREE.BufferAttribute(source.faces, 1));
    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3).setUsage(THREE.DynamicDrawUsage));
    geometry.computeVertexNormals(); geometry.computeBoundingBox();
    const box = geometry.boundingBox, root = source.meta.root_positions[0];
    const minZ = Math.min(box.min.z, source.meta.bounds?.min?.[2] ?? box.min.z);
    const maxZ = Math.max(box.max.z, source.meta.bounds?.max?.[2] ?? box.max.z);
    const height = Math.max(maxZ - minZ, 1.5);
    // Centered playback retains the entire clip's vertical envelope. Reserve
    // arm reach around the pelvis even when frame zero starts lying down.
    const reach = Math.max(height * .55, Math.abs(box.min.x-root[0]), Math.abs(box.max.x-root[0]), Math.abs(box.min.y-root[1]), Math.abs(box.max.y-root[1]));
    target.set(root[0], root[1], (minZ+maxZ)/2);
    envelope = new THREE.Box3(new THREE.Vector3(root[0]-reach,root[1]-reach,minZ),new THREE.Vector3(root[0]+reach,root[1]+reach,maxZ));
    camera.position.copy(target).add(new THREE.Vector3(.75,-1,.3));
    fitCamera();grid.position.set(root[0], root[1], source.meta.ground_z ?? minZ);
    mesh = new THREE.Mesh(geometry, material); mesh.frustumCulled = false; scene.add(mesh);
  }
  function fitCamera() {
    if(!envelope)return;
    const direction=camera.position.clone().sub(target).normalize();
    const right=new THREE.Vector3().crossVectors(camera.up,direction).normalize();
    const up=new THREE.Vector3().crossVectors(direction,right).normalize();
    const tanV=Math.tan(THREE.MathUtils.degToRad(camera.fov/2)),tanH=tanV*camera.aspect;
    let distance=0;
    for(const x of [envelope.min.x,envelope.max.x])for(const y of [envelope.min.y,envelope.max.y])for(const z of [envelope.min.z,envelope.max.z]){
      const point=new THREE.Vector3(x,y,z).sub(target),depth=point.dot(direction);
      distance=Math.max(distance,Math.abs(point.dot(right))*1.12/tanH+depth,Math.abs(point.dot(up))*1.12/tanV+depth);
    }
    camera.position.copy(target).addScaledVector(direction,distance);camera.lookAt(target);
  }
  function frame(source, index, centered = true) {
    setSource(source, index);
    mesh.geometry.attributes.position.array.set(sourcePositions(source, index, centered));
    mesh.geometry.attributes.position.needsUpdate = true;
    mesh.geometry.computeVertexNormals();
  }
  function draw(width, height) {
    width = Math.max(1, Math.round(width)); height = Math.max(1, Math.round(height));
    if (renderWidth !== width || renderHeight !== height) {
      renderer.setSize(width, height, false);renderWidth=width;renderHeight=height;camera.aspect=width/height;fitCamera();
    }
    camera.updateProjectionMatrix(); renderer.render(scene, camera);
  }
  return {renderer, camera, target, frame, draw,
    dispose() {mesh?.geometry.dispose(); material.dispose(); grid.geometry.dispose(); grid.material.dispose(); renderer.dispose(); renderer.forceContextLoss();}};
}
