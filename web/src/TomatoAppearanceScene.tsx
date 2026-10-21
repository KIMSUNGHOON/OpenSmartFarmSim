import { useEffect,useRef,useState } from 'react';
import { ACESFilmicToneMapping,BoxGeometry,Color,DirectionalLight,DoubleSide,Fog,
  HemisphereLight,Mesh,MeshPhysicalMaterial,MeshStandardMaterial,PCFSoftShadowMap,
  PerspectiveCamera,PlaneGeometry,PMREMGenerator,Scene,Vector3,WebGLRenderer,
  type BufferGeometry,type Material,type Object3D } from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import { createTomatoAppearance,TOMATO_APPEARANCE_VERSION } from './tomatoAppearance';
import { tomatoAppearanceTextures } from './tomatoAppearanceTextures';
import type { TomatoLeafBinding } from './tomatoLeafReplay';

type CameraView='plant'|'truss'|'leaf';
type View={camera:(view:CameraView)=>void;rotate:(direction:number)=>void;update:(binding:TomatoLeafBinding|null)=>void;dispose:()=>void};

function createView(canvas:HTMLCanvasElement,onFailure:()=>void):View|null {
  const context=canvas.getContext('webgl2',{antialias:true,alpha:false});
  if(!context||context.isContextLost())return null;
  const renderer=new WebGLRenderer({canvas,context,antialias:true});
  const scene=new Scene(),camera=new PerspectiveCamera(36,1,.015,40),owned:BufferGeometry[]=[],materials:Material[]=[];
  let observer:ResizeObserver|undefined,controls:OrbitControls|undefined,pending:number|null=null,disposed=false;
  let plant:ReturnType<typeof createTomatoAppearance>|undefined,textures:ReturnType<typeof tomatoAppearanceTextures>|undefined;
  let environment:ReturnType<PMREMGenerator['fromScene']>|undefined;
  let binding:TomatoLeafBinding|null=null,referenceLeafArea=0;
  const distantPlants:Object3D[]= [];
  function render(){
    if(disposed||document.hidden)return;
    try{
      if(context!.isContextLost())throw Error('appearance_context_lost');
      const box=canvas.getBoundingClientRect();if(box.width<1||box.height<1)return;
      const ratio=Math.min(window.devicePixelRatio||1,1.5);
      if(renderer.getPixelRatio()!==ratio)renderer.setPixelRatio(ratio);
      if(canvas.width!==Math.floor(box.width*ratio)||canvas.height!==Math.floor(box.height*ratio)){
        renderer.setSize(box.width,box.height,false);camera.aspect=box.width/box.height;camera.updateProjectionMatrix();
      }
      renderer.render(scene,camera);
      if(binding){
        canvas.dataset.sceneAt=binding.at;canvas.dataset.resultId=binding.result_id;
        canvas.dataset.rawLai=String(binding.lai);canvas.dataset.referenceLai=String(binding.reference_lai);
        canvas.dataset.leafAreaRatio=String(plant!.leafSurfaceArea()/referenceLeafArea);
        canvas.dataset.payloadSha256=binding.payload_sha256;canvas.dataset.mapping=binding.mapping;
        canvas.dataset.reproductiveGeometry='withheld';
      }else{
        for(const key of ['sceneAt','resultId','rawLai','referenceLai','leafAreaRatio','payloadSha256','mapping','reproductiveGeometry'])delete canvas.dataset[key];
      }
      canvas.dataset.appearanceVersion=TOMATO_APPEARANCE_VERSION;
      canvas.dataset.drawCalls=String(renderer.info.render.calls);canvas.dataset.triangles=String(renderer.info.render.triangles);
      canvas.dataset.frame=String(Number(canvas.dataset.frame||0)+1);
    }catch{onFailure();}
  }
  function schedule(){if(!disposed&&pending===null)pending=requestAnimationFrame(()=>{pending=null;render();});}
  function dispose(){
    if(disposed)return;disposed=true;observer?.disconnect();if(pending!==null)cancelAnimationFrame(pending);
    document.removeEventListener('visibilitychange',schedule);controls?.removeEventListener('change',schedule);controls?.dispose();
    plant?.dispose();textures?.dispose();environment?.dispose();owned.forEach(g=>g.dispose());materials.forEach(m=>m.dispose());
    renderer.dispose();renderer.forceContextLoss();
    for(const key of ['appearanceVersion','drawCalls','triangles','frame','cameraView','sceneAt','resultId','rawLai',
      'referenceLai','leafAreaRatio','payloadSha256','mapping','reproductiveGeometry'])delete canvas.dataset[key];
  }
  function material<T extends Material>(m:T):T{materials.push(m);return m;}
  function box(x:number,y:number,z:number,position:Vector3,mat:Material){
    const g=new BoxGeometry(x,y,z);owned.push(g);const mesh=new Mesh(g,mat);mesh.position.copy(position);scene.add(mesh);return mesh;
  }
  function setCamera(view:CameraView){
    if(!plant||!controls)return;
    const narrow=canvas.getBoundingClientRect().width<650;
    if(view==='plant'){controls.target.set(.025,.91,0);camera.position.set(narrow?2.2:1.8,1.22,narrow?3.15:2.58);}
    else if(view==='truss'){
      controls.target.copy(plant.trussFocus).add(new Vector3(.015,.04,0));
      camera.position.copy(controls.target).add(new Vector3(.38,.17,.64));
    }else{
      controls.target.copy(plant.leafFocus);camera.position.copy(controls.target).add(new Vector3(.25,.22,.62));
    }
    camera.lookAt(controls.target);controls.update();canvas.dataset.cameraView=view;schedule();
  }
  try{
    renderer.setPixelRatio(Math.min(devicePixelRatio,1.5));renderer.toneMapping=ACESFilmicToneMapping;renderer.toneMappingExposure=.9;
    renderer.shadowMap.enabled=true;renderer.shadowMap.type=PCFSoftShadowMap;
    renderer.debug.onShaderError=()=>{throw Error('appearance_shader_unavailable');};
    scene.background=new Color('#e9e9dc');scene.fog=new Fog('#e9e9dc',4,14);
    const room=new RoomEnvironment(),pmrem=new PMREMGenerator(renderer);
    try{environment=pmrem.fromScene(room,.05);scene.environment=environment.texture;}finally{room.dispose();pmrem.dispose();}
    textures=tomatoAppearanceTextures();
    const leaf=material(new MeshPhysicalMaterial({map:textures.leafColor,bumpMap:textures.leafBump,bumpScale:.0011,
      roughness:.69,metalness:0,side:DoubleSide,vertexColors:true,envMapIntensity:.36,
      sheen:.2,sheenColor:new Color('#7f9b39'),sheenRoughness:.9}));
    const stem=material(new MeshStandardMaterial({color:'#566e2b',roughness:.86,bumpMap:textures.skinBump,bumpScale:.0002}));
    const fruit=material(new MeshPhysicalMaterial({roughness:.44,metalness:0,clearcoat:.14,clearcoatRoughness:.36,
      bumpMap:textures.skinBump,bumpScale:.00016,vertexColors:true,envMapIntensity:.45}));
    const calyx=material(new MeshStandardMaterial({color:'#4e7026',roughness:.85,side:DoubleSide}));
    const flower=material(new MeshStandardMaterial({color:'#f4cc36',roughness:.75,side:DoubleSide}));
    plant=createTomatoAppearance({leaf,stem,fruit,calyx,flower});scene.add(plant.root);referenceLeafArea=plant.leafSurfaceArea();
    const floorMaterial=material(new MeshStandardMaterial({color:'#a8ad9a',roughness:.98}));
    const floorShape=new PlaneGeometry(30,30);owned.push(floorShape);const floor=new Mesh(floorShape,floorMaterial);
    floor.rotation.x=-Math.PI/2;floor.position.y=-.045;floor.receiveShadow=true;scene.add(floor);
    const bed=material(new MeshStandardMaterial({color:'#ddddd0',roughness:.94}));
    box(.36,.16,.5,new Vector3(0,-.007,0),bed).receiveShadow=true;
    const substrate=material(new MeshStandardMaterial({color:'#5c4c33',roughness:1,bumpMap:textures.skinBump,bumpScale:.008}));
    box(.28,.025,.4,new Vector3(0,.078,0),substrate);
    const support=material(new MeshStandardMaterial({color:'#b6aa81',roughness:.93}));
    box(.0016,2.4,.0016,new Vector3(.008,1.22,-.012),support);
    const frame=material(new MeshStandardMaterial({color:'#c7cdc5',metalness:.7,roughness:.39}));
    // Context only; this is not a measured greenhouse or equipment layout.
    for(const z of [-1.8,-3.8,-6]){
      for(const x of [-2,2])box(.035,3.2,.04,new Vector3(x,1.55,z),frame);
      box(4,.035,.04,new Vector3(0,3.05,z),frame);
      const beam=box(2.85,.035,.04,new Vector3(-1,3.6,z),frame);beam.rotation.z=.5;
      const beam2=box(2.85,.035,.04,new Vector3(1,3.6,z),frame);beam2.rotation.z=-.5;
    }
    for(const x of [-2,2])box(.035,.035,8,new Vector3(x,3.05,-2.2),frame);
    box(.035,.035,8,new Vector3(0,4.14,-2.2),frame);
    // Distant meshes reuse the authored geometry. No per-frame growth or wind.
    for(const x of [-1.2,1.2])for(const z of [-2,-3.4,-4.8]){
      const distant=plant.root.clone(true);distant.position.set(x,0,z);distant.rotation.y=z;
      distant.traverse(object=>{if(object instanceof Mesh){object.castShadow=false;object.receiveShadow=false;}});
      scene.add(distant);distantPlants.push(distant);box(.35,.16,.5,new Vector3(x,-.007,z),bed);
    }
    scene.add(new HemisphereLight('#f7f9e9','#6b7550',.9));
    const sun=new DirectionalLight('#fff3d4',2);sun.position.set(-2.4,4,2.2);sun.castShadow=true;
    sun.shadow.mapSize.set(2048,2048);sun.shadow.camera.left=-1.2;sun.shadow.camera.right=1.2;
    sun.shadow.camera.top=2.1;sun.shadow.camera.bottom=-1.3;sun.shadow.camera.near=.1;sun.shadow.camera.far=9;
    sun.shadow.bias=-.00008;sun.shadow.normalBias=.001;sun.target.position.set(0,.8,0);scene.add(sun,sun.target);
    const rim=new DirectionalLight('#edf5ff',.6);rim.position.set(1.6,2,-2.5);scene.add(rim);
    controls=new OrbitControls(camera,canvas);controls.enableDamping=false;controls.enablePan=true;
    controls.minDistance=.15;controls.maxDistance=6;controls.maxPolarAngle=Math.PI*.85;
    controls.addEventListener('change',schedule);observer=new ResizeObserver(schedule);observer.observe(canvas);
    document.addEventListener('visibilitychange',schedule);setCamera('plant');schedule();
    return {camera:setCamera,update(value){
      if(disposed)return;
      try{
        plant!.setLeafAreaRatio(value?.area_ratio??null);binding=value;
        for(const distant of distantPlants)distant.visible=!value;
        const actual=plant!.leafSurfaceArea()/referenceLeafArea;
        if(!Number.isFinite(actual)||Math.abs(actual-(value?.area_ratio??1))>1e-6)throw Error('appearance_leaf_area_mismatch');
        schedule();
      }catch{onFailure();}
    },rotate(direction){if(!controls)return;
      const delta=camera.position.clone().sub(controls.target).applyAxisAngle(new Vector3(0,1,0),direction*Math.PI/8);
      camera.position.copy(delta.add(controls.target));controls.update();schedule();},dispose};
  }catch{dispose();throw Error('appearance_scene_unavailable');}
}

export default function TomatoAppearanceScene({leafBinding,embedded=false}:{leafBinding?:TomatoLeafBinding;embedded?:boolean}){
  const canvas=useRef<HTMLCanvasElement>(null),view=useRef<View|null>(null);
  const latest=useRef(leafBinding);latest.current=leafBinding;
  const [available,setAvailable]=useState<boolean|null>(null),[selected,setSelected]=useState<CameraView>('plant'),[epoch,setEpoch]=useState(0);
  useEffect(()=>{
    const target=canvas.current;if(!target)return;let active=true,owned:View|null=null;
    const fail=()=>{owned?.dispose();view.current=null;if(active)setAvailable(false);};
    const lost=(event:Event)=>{event.preventDefault();fail();},restored=()=>{if(active)setEpoch(n=>n+1);};
    target.addEventListener('webglcontextlost',lost);target.addEventListener('webglcontextrestored',restored);
    try{owned=createView(target,fail);view.current=owned;owned?.update(latest.current??null);setAvailable(!!owned);setSelected('plant');}catch{fail();}
    return()=>{active=false;target.removeEventListener('webglcontextlost',lost);target.removeEventListener('webglcontextrestored',restored);owned?.dispose();view.current=null;};
  },[epoch]);
  useEffect(()=>{view.current?.update(leafBinding??null);},[leafBinding]);
  return <section className={'tomato-appearance'+(embedded?' tomato-appearance--embedded':'')}
    data-selected-at={leafBinding?.at} data-result-id={leafBinding?.result_id} aria-label="방울토마토 외형 연구용 3D">
    <div className="appearance-toolbar"><div><span className="appearance-label">CHERRY TOMATO / APPEARANCE STUDY 01</span>
      {embedded?<h3>방울토마토 잎 면적 연결</h3>:<h1>방울토마토 3D</h1>}
      <p>{leafBinding?'저장된 잎 면적의 상대 변화를 대표 외형에 반영합니다.':'잎과 줄기, 송이 과실을 가까이에서 살펴보세요.'}</p></div>
      <span className="appearance-scope">{leafBinding?'합성 저장 계산 · 잎 면적만 연결':'외형 연구용 · 생장 계산 연결 전'}</span></div>
    <div className="appearance-stage">
      <canvas ref={canvas} aria-label="회전 가능한 방울토마토 3D 장면" tabIndex={available?0:-1} />
      <p className="appearance-instructions">드래그하여 회전 · 스크롤하여 확대</p>
      {available!==true&&<p className="appearance-fallback" role="status">{available===null?'작물의 형태와 표면을 준비하고 있습니다.':'이 환경에서 3D를 표시할 수 없습니다. WebGL2를 지원하는 브라우저에서 다시 시도하세요.'}</p>}
      <div className="appearance-cameras" role="group" aria-label="작물 관찰 시점">
        {([['plant','전체 식물'],['truss','과실 송이'],['leaf','잎 가까이']] as const).map(([key,label])=><button key={key}
          disabled={!available||Boolean(leafBinding&&key==='truss')} aria-pressed={selected===key} onClick={()=>{view.current?.camera(key);setSelected(key);}}>{label}</button>)}
        <button disabled={!available} aria-label="왼쪽으로 회전" onClick={()=>view.current?.rotate(-1)}>↶</button>
        <button disabled={!available} aria-label="오른쪽으로 회전" onClick={()=>view.current?.rotate(1)}>↷</button>
      </div>
    </div>
    <footer className="appearance-footer"><p role="status">{available?'실제 WebGL 3D · 회전 및 확대 가능':available===null?'3D 준비 중':'3D 표시 보류'}</p>
      <p>{leafBinding?'잎 면적만 같은 저장 시점에 연결합니다. 키·잎 수·기관 배치는 고정 외형이며 과실·숙기·수확 표현은 보류합니다.':
        '직접 제작한 대표 외형입니다. 품종별 형태·과실 개수·색·시설 배치는 제작 가정이며, 계산된 생장이나 수확 예측이 아닙니다.'}</p></footer>
    {leafBinding&&<p className="appearance-binding">{leafBinding.at} UTC · LAI {leafBinding.lai} m²_leaf/m²_floor<br/>
      외형 기준은 이 저장 결과의 최대 LAI {leafBinding.reference_lai}입니다. 그림의 크기는 실제 길이·재식밀도가 아닙니다.</p>}
  </section>;
}
