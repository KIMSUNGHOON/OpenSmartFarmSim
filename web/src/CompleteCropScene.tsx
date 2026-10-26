import {useEffect,useRef,useState} from 'react';
import {ACESFilmicToneMapping,Box3,BoxGeometry,Color,DirectionalLight,DoubleSide,HemisphereLight,Mesh,
 MeshPhysicalMaterial,MeshStandardMaterial,PCFShadowMap,PerspectiveCamera,PlaneGeometry,PMREMGenerator,Scene,
 Vector3,WebGLRenderer,type BufferGeometry,type Material} from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {RoomEnvironment} from 'three/addons/environments/RoomEnvironment.js';
import {createCompleteCropPlant,COMPLETE_CROP_MAPPING,COMPLETE_CROP_POSE} from './completeCropPlant';
import {tomatoAppearanceTextures} from './tomatoAppearanceTextures';
import type {CompleteCropFrame} from './completeCropReplay';

type View={update:(frame:CompleteCropFrame,artifact:string)=>void;reset:()=>void;dispose:()=>void};
function createView(canvas:HTMLCanvasElement,fail:()=>void):View|null{
 const context=canvas.getContext('webgl2',{antialias:true,alpha:false});if(!context)return null;
 const renderer=new WebGLRenderer({canvas,context}),scene=new Scene(),camera=new PerspectiveCamera(36,1,.001,30);
 const materials:Material[]=[],geometries:BufferGeometry[]=[];
 let controls:OrbitControls|undefined,observer:ResizeObserver|undefined,plant:ReturnType<typeof createCompleteCropPlant>|undefined;
 let textures:ReturnType<typeof tomatoAppearanceTextures>|undefined,environment:ReturnType<PMREMGenerator['fromScene']>|undefined;
 let current:CompleteCropFrame|undefined,artifact='',pending:number|null=null,disposed=false,autoFrame=true,lastPortrait:boolean|undefined;
 const material=<T extends Material,>(m:T)=>{materials.push(m);return m;};
 const interacted=()=>{autoFrame=false;};
 const fit=(initial=false)=>{
  if(!autoFrame||!plant||!controls)return;
  for(let i=0;i<6;i++){
   const extent=Math.max(...Object.values(plant.projectedLeafBounds(camera)).map(Math.abs));if(extent<=.91&&(!initial||extent>=.78))break;
   camera.position.sub(controls.target).multiplyScalar(initial?Math.max(.2,extent/.85):Math.max(1.04,extent/.89)).add(controls.target);camera.lookAt(controls.target);camera.updateMatrixWorld(true);
  }
 };
 const render=()=>{
  pending=null;if(disposed||document.hidden)return;
  try{
   if(context.isContextLost())throw Error('complete_crop_context_lost');const rect=canvas.getBoundingClientRect();if(rect.width<1||rect.height<1)return;
   renderer.setPixelRatio(Math.min(devicePixelRatio||1,1.5));renderer.setSize(rect.width,rect.height,false);
   camera.aspect=rect.width/rect.height;camera.updateProjectionMatrix();fit();renderer.render(scene,camera);
   if(current&&plant){
    canvas.dataset.sceneAt=JSON.stringify(current.at);canvas.dataset.artifactSha256=artifact;canvas.dataset.selectedIndex=String(current.index);
    canvas.dataset.phase=current.phase;canvas.dataset.checkpointSha256=current.checkpoint_sha256??'';
    canvas.dataset.storedLeafAreas=JSON.stringify(current.leaves.map(l=>({leaf_id:l.leaf_id,area_m2:l.area.value})));
    canvas.dataset.renderedLeafAreas=JSON.stringify(plant.leafSurfaceAreas());canvas.dataset.attachments=JSON.stringify(plant.attachments());
    canvas.dataset.renderedLengths=JSON.stringify(plant.segments.map(m=>({internode_id:m.userData.internode_id,length_m:m.scale.y})));
    canvas.dataset.leafClipBounds=JSON.stringify(plant.projectedLeafBounds(camera));
   }
   canvas.dataset.mapping=COMPLETE_CROP_MAPPING;canvas.dataset.pose=COMPLETE_CROP_POSE;
   canvas.dataset.drawCalls=String(renderer.info.render.calls);canvas.dataset.triangles=String(renderer.info.render.triangles);
   canvas.dataset.frame=String(Number(canvas.dataset.frame||0)+1);
  }catch{fail();}
 };
 const schedule=()=>{if(!disposed&&!document.hidden&&pending===null)pending=requestAnimationFrame(render);};
 function dispose(){
  if(disposed)return;disposed=true;if(pending!==null)cancelAnimationFrame(pending);observer?.disconnect();
  document.removeEventListener('visibilitychange',schedule);controls?.removeEventListener('change',schedule);controls?.removeEventListener('start',interacted);controls?.dispose();
  plant?.dispose();textures?.dispose();environment?.dispose();geometries.forEach(g=>g.dispose());materials.forEach(m=>m.dispose());
  renderer.dispose();renderer.forceContextLoss();for(const key of Object.keys(canvas.dataset))delete canvas.dataset[key];
 }
 try{
  renderer.toneMapping=ACESFilmicToneMapping;renderer.toneMappingExposure=.95;renderer.shadowMap.enabled=true;renderer.shadowMap.type=PCFShadowMap;
  renderer.debug.onShaderError=()=>{throw Error('complete_crop_shader_unavailable');};scene.background=new Color('#e9e9dc');
  const room=new RoomEnvironment(),pmrem=new PMREMGenerator(renderer);
  try{environment=pmrem.fromScene(room,.04);scene.environment=environment.texture;}finally{room.dispose();pmrem.dispose();}
  textures=tomatoAppearanceTextures();
  const stem=material(new MeshStandardMaterial({color:'#668638',roughness:.83,bumpMap:textures.skinBump,bumpScale:.00004}));
  const leaf=material(new MeshPhysicalMaterial({map:textures.leafColor,bumpMap:textures.leafBump,bumpScale:.0002,
   roughness:.73,side:DoubleSide,vertexColors:true,sheen:.2,sheenColor:new Color('#879f46'),envMapIntensity:.35}));
  const floorGeometry=new PlaneGeometry(8,8),bedGeometry=new BoxGeometry(.105,.03,.11),soilGeometry=new BoxGeometry(.098,.003,.103);
  geometries.push(floorGeometry,bedGeometry,soilGeometry);
  const floor=new Mesh(floorGeometry,material(new MeshStandardMaterial({color:'#b7bcaa',roughness:.98})));floor.rotation.x=-Math.PI/2;floor.position.y=-.035;floor.receiveShadow=true;scene.add(floor);
  const bed=new Mesh(bedGeometry,material(new MeshStandardMaterial({color:'#d5d4c6',roughness:.95})));bed.position.y=-.018;bed.receiveShadow=true;scene.add(bed);
  const soil=new Mesh(soilGeometry,material(new MeshStandardMaterial({color:'#62523a',roughness:1,bumpMap:textures.skinBump,bumpScale:.001})));soil.position.y=-.002;soil.receiveShadow=true;scene.add(soil);
  scene.add(new HemisphereLight('#fafbea','#667449',1.1));
  const sun=new DirectionalLight('#fff2d5',2.2);sun.position.set(-3,5,4);sun.castShadow=true;sun.shadow.mapSize.set(1024,1024);
  sun.shadow.camera.left=-2;sun.shadow.camera.right=2;sun.shadow.camera.top=2.5;sun.shadow.camera.bottom=-1;sun.shadow.camera.near=.1;sun.shadow.camera.far=15;
  sun.shadow.bias=-.00008;sun.shadow.normalBias=.0001;sun.target.position.set(0,.05,0);scene.add(sun,sun.target);
  const rim=new DirectionalLight('#eef5ff',.65);rim.position.set(2,3,-3);scene.add(rim);
  controls=new OrbitControls(camera,canvas);controls.enableDamping=false;controls.minDistance=.06;controls.maxDistance=12;controls.maxPolarAngle=Math.PI*.85;
  controls.addEventListener('change',schedule);controls.addEventListener('start',interacted);
  const reset=()=>{
   if(!plant)return;autoFrame=true;const box=new Box3().setFromObject(plant.root),rect=canvas.getBoundingClientRect();
   const portrait=rect.width/Math.max(1,rect.height)<1,size=box.getSize(new Vector3()).length();lastPortrait=portrait;
   controls!.target.copy(box.getCenter(new Vector3()));camera.position.copy(controls!.target).add(new Vector3(1.4,.8,2.7).normalize().multiplyScalar(Math.max(.15,size*(portrait?2.8:1.6))));
   camera.lookAt(controls!.target);camera.aspect=rect.width/Math.max(1,rect.height);camera.updateProjectionMatrix();camera.updateMatrixWorld(true);fit(true);controls!.update();schedule();
  };
  observer=new ResizeObserver(()=>{const r=canvas.getBoundingClientRect();if((r.width/Math.max(1,r.height)<1)!==lastPortrait)reset();schedule();});observer.observe(canvas);
  document.addEventListener('visibilitychange',schedule);
  return {update(frame,hash){if(disposed||current===frame&&artifact===hash)return;const first=!plant;
   plant?.dispose();plant=createCompleteCropPlant(frame,{stem,leaf});scene.add(plant.root);current=frame;artifact=hash;if(first)reset();schedule();},reset,dispose};
 }catch{dispose();throw Error('complete_crop_scene_unavailable');}
}

export default function CompleteCropScene({frame,artifact}:{frame:CompleteCropFrame;artifact:string}){
 const canvas=useRef<HTMLCanvasElement>(null),view=useRef<View|null>(null),latest=useRef({frame,artifact});latest.current={frame,artifact};
 const [available,setAvailable]=useState<boolean|null>(null),[epoch,setEpoch]=useState(0);
 useEffect(()=>{
  const target=canvas.current;if(!target)return;let active=true,owned:View|null=null;
  const fail=()=>{owned?.dispose();view.current=null;if(active)setAvailable(false);};
  const lost=(event:Event)=>{event.preventDefault();fail();},restored=()=>{if(active)setEpoch(n=>n+1);};
  target.addEventListener('webglcontextlost',lost);target.addEventListener('webglcontextrestored',restored);
  try{owned=createView(target,fail);view.current=owned;owned?.update(latest.current.frame,latest.current.artifact);setAvailable(!!owned);}catch{fail();}
  return()=>{active=false;target.removeEventListener('webglcontextlost',lost);target.removeEventListener('webglcontextrestored',restored);owned?.dispose();view.current=null;};
 },[epoch]);
 useEffect(()=>{try{view.current?.update(frame,artifact);}catch{view.current?.dispose();view.current=null;setAvailable(false);}},[frame,artifact]);
 return <section className="morphology-stage" aria-label="저장된 잎 면적과 절간 길이의 3D">
  <canvas ref={canvas} tabIndex={available?0:-1} aria-label="회전 가능한 저장 합성 작물 3D"/>
  <p className="morphology-hint">드래그로 회전 · 스크롤로 확대</p>
  {available!==true&&<p className="morphology-fallback" role="status">{available===null?'저장된 형태를 준비하고 있습니다.':'3D 표시 보류: WebGL2를 사용할 수 없습니다. 같은 원 값은 표에서 확인하세요.'}</p>}
  <button className="morphology-camera" disabled={!available} onClick={()=>view.current?.reset()}>전체 보기</button>
 </section>;
}
