import { useEffect,useRef,useState } from 'react';
import { ACESFilmicToneMapping,BoxGeometry,Color,DirectionalLight,DoubleSide,HemisphereLight,Mesh,
  MeshPhysicalMaterial,MeshStandardMaterial,PCFShadowMap,PerspectiveCamera,PlaneGeometry,
  PMREMGenerator,Scene,WebGLRenderer,type Material } from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import { createMorphologyGeometry,MORPHOLOGY_MAPPING } from './morphologyGeometry';
import { tomatoAppearanceTextures } from './tomatoAppearanceTextures';
import type { MorphologyFrame } from './morphologyReplay';

type View={update:(frame:MorphologyFrame)=>void;reset:()=>void;dispose:()=>void};
function createView(canvas:HTMLCanvasElement,maximum:number,fail:()=>void):View|null{
  const context=canvas.getContext('webgl2',{antialias:true,alpha:false});if(!context)return null;
  const renderer=new WebGLRenderer({canvas,context}),scene=new Scene(),camera=new PerspectiveCamera(36,1,.001,10);
  const materials:Material[]=[],geometries:(PlaneGeometry|BoxGeometry)[]=[];
  let controls:OrbitControls|undefined,observer:ResizeObserver|undefined,plant:ReturnType<typeof createMorphologyGeometry>|undefined;
  let environment:ReturnType<PMREMGenerator['fromScene']>|undefined,textures:ReturnType<typeof tomatoAppearanceTextures>|undefined;
  let frame:MorphologyFrame|undefined,pending:number|null=null,disposed=false;
  const material=<T extends Material,>(value:T)=>{materials.push(value);return value;};
  const render=()=>{
    pending=null;if(disposed||document.hidden)return;
    try{
      if(context.isContextLost())throw Error('context lost');const box=canvas.getBoundingClientRect();if(box.width<1||box.height<1)return;
      const ratio=Math.min(devicePixelRatio||1,1.5);renderer.setPixelRatio(ratio);
      renderer.setSize(box.width,box.height,false);camera.aspect=box.width/box.height;camera.updateProjectionMatrix();renderer.render(scene,camera);
      if(frame&&plant){
        canvas.dataset.sceneAt=frame.at;canvas.dataset.artifactSha256=frame.artifact_sha256;canvas.dataset.resultSha256=frame.result_sha256;
        canvas.dataset.selectedIndex=String(frame.index);canvas.dataset.internodeCount=String(frame.internodes.length);
        canvas.dataset.storedLengths=JSON.stringify(frame.internodes.map(n=>n.length.value));
        canvas.dataset.renderedLengths=JSON.stringify(plant.segments.map(m=>m.scale.y));
        canvas.dataset.renderedInternodeIds=JSON.stringify(plant.segments.map(m=>m.userData.internode_id));
        canvas.dataset.authoredLeafCount=String(plant.authoredLeafCount);canvas.dataset.axisLength=String(frame.tracked_axis_length.value);
      }
      canvas.dataset.mapping=MORPHOLOGY_MAPPING;canvas.dataset.drawCalls=String(renderer.info.render.calls);
      canvas.dataset.frame=String(Number(canvas.dataset.frame||0)+1);
    }catch{fail();}
  };
  const schedule=()=>{if(!disposed&&pending===null)pending=requestAnimationFrame(render);};
  function dispose(){
    if(disposed)return;disposed=true;if(pending!==null)cancelAnimationFrame(pending);observer?.disconnect();
    document.removeEventListener('visibilitychange',schedule);controls?.removeEventListener('change',schedule);controls?.dispose();
    plant?.dispose();textures?.dispose();environment?.dispose();geometries.forEach(g=>g.dispose());materials.forEach(m=>m.dispose());
    renderer.dispose();renderer.forceContextLoss();for(const k of Object.keys(canvas.dataset))delete canvas.dataset[k];
  }
  try{
    renderer.toneMapping=ACESFilmicToneMapping;renderer.toneMappingExposure=.95;renderer.shadowMap.enabled=true;renderer.shadowMap.type=PCFShadowMap;
    renderer.debug.onShaderError=()=>{throw Error('shader unavailable');};scene.background=new Color('#e9e9dc');
    const room=new RoomEnvironment(),pmrem=new PMREMGenerator(renderer);
    try{environment=pmrem.fromScene(room,.04);scene.environment=environment.texture;}finally{room.dispose();pmrem.dispose();}
    textures=tomatoAppearanceTextures();
    const stem=material(new MeshStandardMaterial({color:'#668638',roughness:.83,bumpMap:textures.skinBump,bumpScale:.00004}));
    const leaf=material(new MeshPhysicalMaterial({map:textures.leafColor,bumpMap:textures.leafBump,bumpScale:.0002,
      roughness:.73,side:DoubleSide,vertexColors:true,sheen:.2,sheenColor:new Color('#879f46'),envMapIntensity:.35}));
    const soil=material(new MeshStandardMaterial({color:'#62523a',roughness:1,bumpMap:textures.skinBump,bumpScale:.001}));
    const bed=material(new MeshStandardMaterial({color:'#d5d4c6',roughness:.95}));
    const floorGeometry=new PlaneGeometry(5,5);geometries.push(floorGeometry);
    const floor=new Mesh(floorGeometry,material(new MeshStandardMaterial({color:'#b7bcaa',roughness:.98})));
    floor.rotation.x=-Math.PI/2;floor.position.y=-.035;floor.receiveShadow=true;scene.add(floor);
    const bedGeometry=new BoxGeometry(.105,.03,.11),soilGeometry=new BoxGeometry(.098,.003,.103);geometries.push(bedGeometry,soilGeometry);
    const box=new Mesh(bedGeometry,bed);box.position.y=-.018;box.receiveShadow=true;scene.add(box);
    const substrate=new Mesh(soilGeometry,soil);substrate.position.y=-.002;substrate.receiveShadow=true;scene.add(substrate);
    scene.add(new HemisphereLight('#fafbea','#667449',1.1));
    const sun=new DirectionalLight('#fff2d5',2.2);sun.position.set(-.3,.6,.4);sun.castShadow=true;
    sun.shadow.mapSize.set(1024,1024);sun.shadow.camera.left=-.18;sun.shadow.camera.right=.18;
    sun.shadow.camera.top=.25;sun.shadow.camera.bottom=-.1;sun.shadow.camera.near=.01;sun.shadow.camera.far=2;
    sun.shadow.bias=-.00004;sun.shadow.normalBias=.0001;sun.target.position.set(0,.05,0);scene.add(sun,sun.target);
    const rim=new DirectionalLight('#eef5ff',.65);rim.position.set(.2,.3,-.3);scene.add(rim);
    controls=new OrbitControls(camera,canvas);controls.enableDamping=false;controls.minDistance=.06;controls.maxDistance=1.5;
    controls.maxPolarAngle=Math.PI*.85;controls.addEventListener('change',schedule);
    const reset=()=>{controls!.target.set(.006,maximum*.48,0);camera.position.set(maximum*1.4,maximum*.85,maximum*2.7);
      camera.lookAt(controls!.target);controls!.update();schedule();};
    observer=new ResizeObserver(schedule);observer.observe(canvas);document.addEventListener('visibilitychange',schedule);reset();
    return {update(value){if(disposed)return;plant?.dispose();plant=createMorphologyGeometry(value,{stem,leaf});scene.add(plant.root);frame=value;schedule();},reset,dispose};
  }catch{dispose();throw Error('morphology WebGL unavailable');}
}

export default function MorphologyScene({frame,maximum}:{frame:MorphologyFrame;maximum:number}){
  const canvas=useRef<HTMLCanvasElement>(null),view=useRef<View|null>(null),latest=useRef(frame);latest.current=frame;
  const [available,setAvailable]=useState<boolean|null>(null),[epoch,setEpoch]=useState(0);
  useEffect(()=>{
    const target=canvas.current;if(!target)return;let active=true,owned:View|null=null;
    const fail=()=>{owned?.dispose();view.current=null;if(active)setAvailable(false);};
    const lost=(event:Event)=>{event.preventDefault();fail();},restored=()=>{if(active)setEpoch(n=>n+1);};
    target.addEventListener('webglcontextlost',lost);target.addEventListener('webglcontextrestored',restored);
    try{owned=createView(target,maximum,fail);view.current=owned;owned?.update(latest.current);setAvailable(!!owned);}catch{fail();}
    return()=>{active=false;target.removeEventListener('webglcontextlost',lost);target.removeEventListener('webglcontextrestored',restored);owned?.dispose();view.current=null;};
  },[maximum,epoch]);
  useEffect(()=>{try{view.current?.update(frame);}catch{view.current?.dispose();view.current=null;setAvailable(false);}},[frame]);
  return <section className="morphology-stage" aria-label="저장된 줄기 길이의 3D">
    <canvas ref={canvas} tabIndex={available?0:-1} aria-label="회전 가능한 합성 토마토 줄기 3D"/>
    <p className="morphology-hint">드래그로 회전 · 스크롤로 확대</p>
    {available!==true&&<p className="morphology-fallback" role="status">{available===null?'저장 결과의 형태를 준비하고 있습니다.':'3D 표시 보류: WebGL2를 사용할 수 없습니다. 원 값은 아래 표에서 확인하세요.'}</p>}
    <button className="morphology-camera" disabled={!available} onClick={()=>view.current?.reset()}>전체 보기</button>
  </section>;
}
