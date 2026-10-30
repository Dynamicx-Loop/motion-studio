import * as THREE from 'three';
import {OrbitControls} from '/vendor/OrbitControls.js';

// Prepared pose display uses compiled geom-local vertices plus exact mj_forward transforms.
export function createRobotPreview(container) {
  const scene = new THREE.Scene(); scene.background = new THREE.Color('#15232f');
  const camera = new THREE.PerspectiveCamera(45, 1, .005, 1000); camera.up.set(0,0,1);
  const renderer = new THREE.WebGLRenderer({antialias:true});
  renderer.setPixelRatio(Math.min(devicePixelRatio,2)); container.append(renderer.domElement);
  const controls = new OrbitControls(camera, renderer.domElement);
  scene.add(new THREE.HemisphereLight(0xddeeff,0x667788,2));
  const light = new THREE.DirectionalLight(0xffffff,2); light.position.set(3,-4,7); scene.add(light);
  const grid = new THREE.GridHelper(10,20,0x657b8e,0x314452); grid.rotation.x = Math.PI/2; scene.add(grid);
  const group = new THREE.Group(); scene.add(group);
  let meshes = [], framePending = false;
  function draw() {
    framePending = false;
    const width = Math.max(container.clientWidth,1), height = Math.max(container.clientHeight,1);
    renderer.setSize(width,height,false); camera.aspect = width/height; camera.updateProjectionMatrix();
    renderer.render(scene,camera);
  }
  function requestDraw() {if (!framePending) {framePending = true; requestAnimationFrame(draw);}}
  controls.addEventListener('change',requestDraw);
  new ResizeObserver(requestDraw).observe(container);
  return {
    geometry(data) {
      for (const mesh of meshes) {group.remove(mesh); mesh.geometry.dispose(); mesh.material.dispose();}
      meshes = data.geometries.map(item => {
        const geometry = new THREE.BufferGeometry();
        geometry.setAttribute('position',new THREE.Float32BufferAttribute(item.vertices.flat(),3));
        geometry.setIndex(item.faces.flat()); geometry.computeVertexNormals();
        const rgba = item.rgba;
        const mesh = new THREE.Mesh(geometry,new THREE.MeshStandardMaterial({
          color:new THREE.Color(...rgba.slice(0,3)),roughness:.7,metalness:.15,
          side:THREE.DoubleSide,transparent:rgba[3]<1,opacity:rgba[3]}));
        group.add(mesh); return mesh;
      });
      this.pose(data);
      const box = new THREE.Box3().setFromObject(group), center = box.getCenter(new THREE.Vector3());
      const radius = Math.max(box.getSize(new THREE.Vector3()).length(),.3);
      controls.target.copy(center); camera.position.copy(center).add(new THREE.Vector3(radius,-radius,radius*.6));
      controls.update(); requestDraw();
    },
    pose(data) {
      data.transforms.forEach((transform,i) => {
        const mesh = meshes[i]; if (!mesh) return;
        const r = transform.rotation;
        const matrix = new THREE.Matrix4().set(r[0],r[1],r[2],0,r[3],r[4],r[5],0,r[6],r[7],r[8],0,0,0,0,1);
        mesh.quaternion.setFromRotationMatrix(matrix); mesh.position.fromArray(transform.position);
      });
      requestDraw();
    }
  };
}
