import { useEffect,useRef,useState } from 'react';
import { Scene,PerspectiveCamera,WebGLRenderer,Color,Mesh,MeshStandardMaterial,BoxGeometry,
  HemisphereLight,DirectionalLight,Vector3,DoubleSide } from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { createCanopy } from './cropGeometry';
import { createCohortDiagrams,type CohortScales } from './coupledCropGeometry';
import { displayNumber,CARBON_UNIT } from './cropReplay';
import { FRUIT_NUMBER_UNIT,type CoupledCropSample } from './coupledCropReplay';

type View={update:(sample:CoupledCropSample)=>void;rotate:(direction:number)=>void;reset:()=>void;dispose:()=>void};
function clearEvidence(canvas:HTMLCanvasElement){
  for(const key of ['sceneAt','leafSurfaceArea','cohortDrawing','drawCalls'])delete canvas.dataset[key];
}
function createView(canvas:HTMLCanvasElement,scales:CohortScales,failed:()=>void):View|null{
  const context=canvas.getContext('webgl2',{antialias:true,alpha:true});
  if(!context || context.isContextLost())return null;
  const renderer=new WebGLRenderer({canvas,context,antialias:true,alpha:true});
  const materials:MeshStandardMaterial[]=[],shapes:BoxGeometry[]=[];
  let controls:OrbitControls|undefined,observer:ResizeObserver|undefined,pending:number|null=null,disposed=false;
  let canopy:ReturnType<typeof createCanopy>|undefined,diagrams:ReturnType<typeof createCohortDiagrams>|undefined;
  function dispose(){
    if(disposed)return;disposed=true;observer?.disconnect();if(pending!==null)cancelAnimationFrame(pending);
    controls?.removeEventListener('change',render);controls?.dispose();canopy?.dispose();diagrams?.dispose();
    shapes.forEach(x=>x.dispose());materials.forEach(x=>x.dispose());renderer.dispose();clearEvidence(canvas);
  }
  const scene=new Scene(),camera=new PerspectiveCamera(38,1,.02,40);
  function render(){
    if(disposed)return;
    try{if(context!.isContextLost())throw new Error('crop_scene_unavailable');
      renderer.render(scene,camera);canvas.dataset.drawCalls=String(renderer.info.render.calls);
    }catch{failed();}
  }
  try{
    renderer.setPixelRatio(Math.min(devicePixelRatio,1.5));
    renderer.debug.onShaderError=()=>{throw new Error('crop_scene_unavailable');};
    scene.background=new Color('#f0f3e7');camera.position.set(3.3,2.9,4.7);
    controls=new OrbitControls(camera,canvas);controls.target.set(.2,.3,0);controls.enablePan=false;controls.enableDamping=false;
    controls.minDistance=4.2;controls.maxDistance=10;controls.maxPolarAngle=Math.PI/2.1;controls.update();controls.saveState();
    scene.add(new HemisphereLight('#ffffff','#778965',2.5));
    const light=new DirectionalLight('#fff9e4',2);light.position.set(-2,5,3);scene.add(light);
    const material=(color:string,side?:typeof DoubleSide)=>{const m=new MeshStandardMaterial({color,roughness:.85,...(side?{side}:{})});materials.push(m);return m;};
    canopy=createCanopy(material('#367744',DoubleSide));canopy.group.position.x=-1.4;scene.add(canopy.group);
    const floorShape=new BoxGeometry(1,.025,1);shapes.push(floorShape);
    const floor=new Mesh(floorShape,material('#c6d1b7'));floor.position.set(-1.4,-.022,0);scene.add(floor);
    diagrams=createCohortDiagrams(material('#7d943b'),material('#547a96'));scene.add(diagrams.group);
    observer=new ResizeObserver(()=>{if(pending!==null || disposed)return;
      pending=requestAnimationFrame(()=>{pending=null;if(disposed)return;const box=canvas.getBoundingClientRect();
        if(box.width<1 || box.height<1)return;
        renderer.setSize(box.width,box.height,false);camera.aspect=box.width/box.height;camera.updateProjectionMatrix();render();});
    });observer.observe(canvas);controls.addEventListener('change',render);
    return {update(sample){if(disposed)return;
      try{
        diagrams!.update(sample.state,scales);canopy!.update(sample.lai.value);const area=canopy!.area();
        if(!Number.isFinite(area) || Math.abs(area-sample.lai.value)>Math.max(1e-8,sample.lai.value*1e-6))throw new Error('crop_scene_unavailable');
        if(context!.isContextLost())throw new Error('crop_scene_unavailable');
        const drawing=(meshes:ReturnType<typeof createCohortDiagrams>['carbon'])=>meshes.map(mesh=>({index:mesh.userData.cohortIndex,
          value:mesh.userData.value,unit:mesh.userData.unit,height:mesh.scale.y,y:mesh.position.y,visible:mesh.visible}));
        canvas.dataset.sceneAt=sample.at;canvas.dataset.leafSurfaceArea=String(area);
        canvas.dataset.cohortDrawing=JSON.stringify({scales,carbon:drawing(diagrams!.carbon),number:drawing(diagrams!.number)});render();
      }catch{failed();}
    },rotate(direction){const delta=camera.position.clone().sub(controls!.target);
      delta.applyAxisAngle(new Vector3(0,1,0),direction*Math.PI/8);camera.position.copy(delta.add(controls!.target));controls!.update();render();},
    reset(){controls!.reset();render();},dispose};
  }catch(error){dispose();throw error;}
}

export default function CoupledCropScene({sample,scales,rangeLabel}:{sample:CoupledCropSample;scales:CohortScales;rangeLabel?:string}){
  const canvas=useRef<HTMLCanvasElement>(null),view=useRef<View|null>(null),latest=useRef(sample);latest.current=sample;
  const [available,setAvailable]=useState<boolean|null>(null),[epoch,setEpoch]=useState(0);
  useEffect(()=>{
    const target=canvas.current;if(!target)return;let active=true;
    const fail=()=>{view.current?.dispose();view.current=null;clearEvidence(target);if(active)setAvailable(false);};
    const lost=(event:Event)=>{event.preventDefault();fail();},restored=()=>{if(active)setEpoch(n=>n+1);};
    target.addEventListener('webglcontextlost',lost);target.addEventListener('webglcontextrestored',restored);
    try{view.current=createView(target,scales,fail);setAvailable(!!view.current);view.current?.update(latest.current);}catch{fail();}
    return()=>{active=false;target.removeEventListener('webglcontextlost',lost);target.removeEventListener('webglcontextrestored',restored);
      view.current?.dispose();view.current=null;};
  },[scales,epoch]);
  useEffect(()=>{view.current?.update(sample);},[sample]);
  return <div className="coupled-scene" data-selected-at={sample.at}>
    <div className="crop-scene-status"><span className="badge">저장 수치 3D</span><span role="status">
      {available===null?'연결 연구 3D 준비 중':available?'연결 연구 3D 준비됨':'표·그래프로 확인'}</span></div>
    <canvas ref={canvas} className={'coupled-canvas crop-canvas'+(available===false?' unavailable':'')} aria-hidden="true"/>
    {available===false && <div className="crop-scene-fallback"><strong>연결 연구 3D를 사용할 수 없습니다.</strong>
      <p>같은 시점의 정확한 값과 시간 조작은 아래 표에서 사용할 수 있습니다.</p>
      <button className="button secondary" onClick={()=>setEpoch(n=>n+1)}>연결 연구 3D 다시 시도</button></div>}
    <div className="crop-camera" aria-label="연결 연구 시점 조작">
      <button className="button secondary" aria-label="연결 연구 왼쪽에서 보기" disabled={!available} onClick={()=>view.current?.rotate(-1)}>왼쪽</button>
      <button className="button secondary" aria-label="연결 연구 기본 시점" disabled={!available} onClick={()=>view.current?.reset()}>기본 시점</button>
      <button className="button secondary" aria-label="연결 연구 오른쪽에서 보기" disabled={!available} onClick={()=>view.current?.rotate(1)}>오른쪽</button></div>
    <p className="crop-caption">왼쪽: 논리 바닥 1m²당 잎 한 면 {displayNumber(sample.lai.value)}m². 배치·지지선은 실제 키·잎수·재식밀도가 아닙니다.</p>
    {scales.logarithmic && <p className="crop-caption startup-log-scale">3D 막대 높이는 {rangeLabel?'현재 읽은 범위':'전체 저장 시점'}의 로그 비교 척도입니다.
      {(['carbon','number'] as const).map(kind=>{const b=scales.logarithmic![kind];return <span key={kind}> {kind==='carbon'?'C':'N'}:
        {b?` 10^${b.lower} → 10^${b.upper}`:' 양수 없음'}. </span>;})}
      영 값은 숨깁니다. 그래프·표는 원 단위와 원값을 유지합니다.</p>}
    {rangeLabel && <p className="crop-caption">{rangeLabel}. 범위를 바꾸면 비교 축도 바뀔 수 있습니다.</p>}
    <p className="crop-caption">중앙: 과실 탄소 C, 공통 최대 {displayNumber(scales.carbon)} {CARBON_UNIT}.
      오른쪽: 개수 상당량 N, 공통 최대 {displayNumber(scales.number)} {FRUIT_NUMBER_UNIT}. 각 10열×5행은 구획 1–50이며 열매 크기·개수·숙기·수확량을 뜻하지 않습니다.</p>
  </div>;
}
