import {useEffect,useRef,useState} from 'react';
import {ACESFilmicToneMapping,Box3,Color,DirectionalLight,DoubleSide,HemisphereLight,InstancedMesh,Matrix4,Mesh,MeshPhysicalMaterial,
 MeshStandardMaterial,PCFShadowMap,PerspectiveCamera,PlaneGeometry,Scene,Vector3,WebGLRenderer,type DataTexture,type Material} from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {loadRoomLighting} from './roomLighting';
import {createSupplyMorphologyPlant} from './supplyMorphologyPlant';
import {tomatoAppearanceTextures} from './tomatoAppearanceTextures';
import type {SupplyStoredFrame} from './supplyMorphologyReplay';
import type {SupplyView} from './supplyMorphologySelection';
import rotateIcon from './supplyDesignIcons/rotate-clockwise-arrow.svg';

type View={update:(frame:SupplyStoredFrame,artifact:string,mode:SupplyView)=>void;reset:()=>void;key:(key:string)=>boolean;dispose:()=>void};
function createView(canvas:HTMLCanvasElement,fail:()=>void,environment:DataTexture):View|null{
 const context=canvas.getContext('webgl2',{antialias:true,alpha:false});if(!context)return null;
 const renderer=new WebGLRenderer({canvas,context}),scene=new Scene(),camera=new PerspectiveCamera(36,1,.001,40);
 const materials:Material[]=[];let controls:OrbitControls|undefined,observer:ResizeObserver|undefined;
 let plant:ReturnType<typeof createSupplyMorphologyPlant>|undefined,textures:ReturnType<typeof tomatoAppearanceTextures>|undefined;
 let pending:number|null=null,disposed=false,autoFrame=true,mode:SupplyView='connected';
 const floorGeometry=new PlaneGeometry(12,12),material=<T extends Material,>(m:T)=>{materials.push(m);return m;};
 const targetGroup=()=>mode==='connected'?plant?.forest:mode==='unbound'?plant?.unbound:plant?.root;
 const reset=()=>{
  if(!plant||!controls)return;autoFrame=true;const target=targetGroup();if(!target)return;
  const box=new Box3().setFromObject(target),center=box.getCenter(new Vector3()),size=box.getSize(new Vector3());
  const extent=Math.max(size.x,size.y,size.z,.02),rect=canvas.getBoundingClientRect();
  const distance=extent/(2*Math.tan(camera.fov*Math.PI/360))*1.5/Math.min(1,Math.max(.25,rect.width/Math.max(rect.height,1)));
  controls.target.copy(center);camera.aspect=rect.width/Math.max(rect.height,1);camera.updateProjectionMatrix();
  camera.position.copy(center).add(new Vector3(.8,.5,1.2).normalize().multiplyScalar(distance));camera.lookAt(center);controls.update();
  plant.root.updateMatrixWorld(true);const meshes:Mesh[]=[];target.traverseVisible(n=>{if(n instanceof Mesh)meshes.push(n);});
  const matrix=new Matrix4(),point=new Vector3();
  for(let attempt=0;attempt<5;attempt++){
   camera.updateMatrixWorld(true);let clip=0;
   for(const mesh of meshes){const p=mesh.geometry.getAttribute('position'),instances=mesh instanceof InstancedMesh?mesh.count:1;
    for(let k=0;k<instances;k++){
     if(mesh instanceof InstancedMesh){mesh.getMatrixAt(k,matrix);matrix.premultiply(mesh.matrixWorld);}else matrix.copy(mesh.matrixWorld);
     for(let j=0;j<p.count;j++){point.fromBufferAttribute(p,j).applyMatrix4(matrix).project(camera);clip=Math.max(clip,Math.abs(point.x),Math.abs(point.y));}
    }
   }
   if(!Number.isFinite(clip)||clip===0||Math.abs(clip-.82)<.02)break;
   camera.position.sub(center).multiplyScalar(Math.max(.4,Math.min(2,clip/.82))).add(center);camera.lookAt(center);controls.update();
  }
  schedule();
 };
 const render=()=>{
  pending=null;if(disposed||document.hidden)return;
  try{
   if(context.isContextLost())throw Error('supply_context_lost');const rect=canvas.getBoundingClientRect();if(rect.width<1||rect.height<1)return;
   renderer.setPixelRatio(Math.min(devicePixelRatio||1,1.5));renderer.setSize(rect.width,rect.height,false);
   camera.aspect=rect.width/rect.height;camera.updateProjectionMatrix();renderer.render(scene,camera);
   canvas.dataset.frame=String(Number(canvas.dataset.frame||0)+1);canvas.dataset.drawCalls=String(renderer.info.render.calls);
   canvas.dataset.triangles=String(renderer.info.render.triangles);canvas.dataset.gpuGeometries=String(renderer.info.memory.geometries);
   canvas.dataset.camera=JSON.stringify({position:camera.position.toArray(),target:controls?.target.toArray()});
  }catch{fail();}
 };
 function schedule(){if(!disposed&&!document.hidden&&pending===null)pending=requestAnimationFrame(render);}
 const interacted=()=>{autoFrame=false;};
 const resize=()=>{if(autoFrame)reset();else schedule();};
 const dispose=()=>{
  if(disposed)return;disposed=true;if(pending!==null)cancelAnimationFrame(pending);observer?.disconnect();
  document.removeEventListener('visibilitychange',schedule);controls?.removeEventListener('change',schedule);controls?.removeEventListener('start',interacted);controls?.dispose();
  plant?.dispose();textures?.dispose();environment?.dispose();floorGeometry.dispose();materials.forEach(m=>m.dispose());
  renderer.dispose();renderer.forceContextLoss();for(const key of Object.keys(canvas.dataset))delete canvas.dataset[key];
 };
 try{
  renderer.toneMapping=ACESFilmicToneMapping;renderer.toneMappingExposure=.95;renderer.shadowMap.enabled=true;renderer.shadowMap.type=PCFShadowMap;
  renderer.debug.onShaderError=()=>{throw Error('supply_shader_unavailable');};scene.background=new Color('#e9e9dc');
  scene.environment=environment;
  textures=tomatoAppearanceTextures();
  const stem=material(new MeshStandardMaterial({color:'#668638',roughness:.83,bumpMap:textures.skinBump,bumpScale:.00004}));
  const leaf=material(new MeshPhysicalMaterial({map:textures.leafColor,bumpMap:textures.leafBump,bumpScale:.0002,roughness:.73,
   side:DoubleSide,vertexColors:true,sheen:.2,sheenColor:new Color('#879f46'),envMapIntensity:.35}));
  const floor=new Mesh(floorGeometry,material(new MeshStandardMaterial({color:'#d4d8c8',roughness:.98})));floor.rotation.x=-Math.PI/2;floor.position.y=-.035;floor.receiveShadow=true;scene.add(floor);
  scene.add(new HemisphereLight('#fafbea','#667449',1.1));const sun=new DirectionalLight('#fff2d5',2.2);sun.position.set(-3,5,4);sun.castShadow=true;
  sun.shadow.mapSize.set(1024,1024);sun.shadow.camera.left=-4;sun.shadow.camera.right=5;sun.shadow.camera.top=3;sun.shadow.camera.bottom=-2;
  sun.shadow.camera.near=.1;sun.shadow.camera.far=15;sun.shadow.bias=-.00008;sun.shadow.normalBias=.0001;scene.add(sun,sun.target);
  const rim=new DirectionalLight('#eef5ff',.65);rim.position.set(2,3,-3);scene.add(rim);
  controls=new OrbitControls(camera,canvas);controls.enableDamping=false;controls.minDistance=.03;controls.maxDistance=30;controls.maxPolarAngle=Math.PI*.85;
  controls.addEventListener('change',schedule);controls.addEventListener('start',interacted);observer=new ResizeObserver(resize);observer.observe(canvas);
  document.addEventListener('visibilitychange',schedule);
  return {update(frame,artifact,nextMode){
   const first=!plant,changed=mode!==nextMode;mode=nextMode;plant?.dispose();plant=createSupplyMorphologyPlant(frame,{stem,leaf});
   plant.forest.visible=mode!=='unbound';plant.unbound.visible=mode!=='connected';scene.add(plant.root);
   const metadata=plant.placements().metadata;canvas.dataset.sceneAt=JSON.stringify(metadata.at);canvas.dataset.phase=metadata.phase;
   canvas.dataset.selectedIndex=String(metadata.index);canvas.dataset.artifactSha256=artifact;canvas.dataset.view=mode;
   canvas.dataset.storedLeafAreas=JSON.stringify(frame.leaves.map(l=>({leaf_id:l.id,area_m2:l.geometry.value})));
   canvas.dataset.renderedLeafAreas=JSON.stringify(plant.leafSurfaceAreas());canvas.dataset.placements=JSON.stringify(plant.placements());
   canvas.dataset.renderedLengths=JSON.stringify(plant.segments.map(m=>({internode_id:m.userData.internode_id,parent_internode_id:m.userData.parent_internode_id,length_m:m.scale.y,visible:m.visible})));
   if(first||changed||autoFrame)reset();renderer.compile(scene,camera);schedule();
  },reset,key(key){
   if(!controls)return false;const k=key.toLowerCase();if(k==='r'){reset();return true;}
   if(!['a','d','w','s'].includes(k))return false;autoFrame=false;
   const offset=camera.position.clone().sub(controls.target);
   if(k==='a'||k==='d')offset.applyAxisAngle(new Vector3(0,1,0),k==='a'?.16:-.16);else offset.multiplyScalar(k==='w'?.9:1.1);
   if(offset.length()>=controls.minDistance&&offset.length()<=controls.maxDistance)camera.position.copy(controls.target).add(offset);
   camera.lookAt(controls.target);controls.update();schedule();return true;
  },dispose};
 }catch{dispose();throw Error('supply_scene_unavailable');}
}

export default function SupplyMorphologyScene({frame,artifact,mode}:{frame:SupplyStoredFrame;artifact:string;mode:SupplyView}){
 const canvas=useRef<HTMLCanvasElement>(null),view=useRef<View|null>(null);
 const [available,setAvailable]=useState<boolean|null>(null);
 useEffect(()=>{
  const target=canvas.current;if(!target)return;let active=true,owned:View|null=null;
  const controller=new AbortController();setAvailable(null);
  const fail=()=>{owned?.dispose();view.current=null;if(active)setAvailable(false);};
  const lost=(event:Event)=>{event.preventDefault();fail();};target.addEventListener('webglcontextlost',lost);
  loadRoomLighting(controller.signal).then(environment=>{
   if(!active){environment.dispose();return;}
   try{owned=createView(target,fail,environment);if(!owned)environment.dispose();view.current=owned;setAvailable(!!owned);}catch{environment.dispose();fail();}
  },()=>{if(active)fail();});
  return()=>{active=false;controller.abort();target.removeEventListener('webglcontextlost',lost);owned?.dispose();view.current=null;};
 },[]);
 useEffect(()=>{try{view.current?.update(frame,artifact,mode);}catch{view.current?.dispose();view.current=null;setAvailable(false);}},[frame,artifact,mode,available]);
 return <div className="supply-stage">
  <canvas ref={canvas} style={{visibility:available===false?'hidden':undefined}} tabIndex={available?0:-1} aria-label="저장된 잎과 줄기의 회전 가능한 3D"
   onKeyDown={e=>{if(view.current?.key(e.key))e.preventDefault();}}/>
  <span className="supply-stage-hint">드래그로 회전 · 휠로 확대</span>
  <button className="supply-camera-reset" disabled={!available} onClick={()=>view.current?.reset()}><img className="supply-icon" src={rotateIcon} alt=""/> 카메라 초기화</button>
  {available!==true&&<p className="supply-stage-fallback" role="status">{available===null?'저장된 3D를 준비하고 있습니다.':'3D 표시 보류: 같은 원 값은 데이터 표에서 확인하세요.'}</p>}
 </div>;
}
