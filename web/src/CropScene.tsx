import { useEffect,useRef,useState } from 'react';
import { Scene,PerspectiveCamera,WebGLRenderer,Color,Mesh,MeshStandardMaterial,BoxGeometry,
  EdgesGeometry,LineSegments,LineBasicMaterial,HemisphereLight,DirectionalLight,Vector3,DoubleSide } from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { createCanopy,carbonHeights } from './cropGeometry';
import { STORES,STORE_COLORS,CARBON_UNIT,displayNumber,type CropSample,type Store } from './cropReplay';

type View={update:(sample:CropSample)=>void;rotate:(direction:number)=>void;reset:()=>void;dispose:()=>void};
function clearEvidence(canvas:HTMLCanvasElement){
  for(const key of Object.keys(canvas.dataset))if(/^(scene|leafSurface|carbon|draw|maximum)/.test(key))delete canvas.dataset[key];
}
function createView(canvas:HTMLCanvasElement,maximum:number,failed:()=>void):View|null{
  const context=canvas.getContext('webgl2',{antialias:true,alpha:true});
  if(!context || context.isContextLost())return null;
  const renderer=new WebGLRenderer({canvas,context,antialias:true,alpha:true});
  renderer.setPixelRatio(Math.min(devicePixelRatio,1.5));
  renderer.debug.onShaderError=()=>{throw new Error('crop_scene_unavailable');};
  const scene=new Scene();scene.background=new Color('#f0f3e7');
  const camera=new PerspectiveCamera(38,1,0.02,30);camera.position.set(2.6,1.8,2.7);
  const controls=new OrbitControls(camera,canvas);controls.target.set(0.35,0.35,0);
  controls.enablePan=false;controls.enableDamping=false;controls.minDistance=2.6;controls.maxDistance=7;
  controls.maxPolarAngle=Math.PI/2.1;controls.update();controls.saveState();
  scene.add(new HemisphereLight('#ffffff','#778965',2.5));
  const light=new DirectionalLight('#fff9e4',2);light.position.set(-2,5,3);scene.add(light);
  const floorShape=new BoxGeometry(1,0.025,1),barShape=new BoxGeometry(0.085,1,0.085);
  const frameShape=new BoxGeometry(1,0.75,1),edges=new EdgesGeometry(frameShape);
  const floorMaterial=new MeshStandardMaterial({color:'#c6d1b7',roughness:1});
  const leafMaterial=new MeshStandardMaterial({color:STORE_COLORS.leaf,roughness:0.85,side:DoubleSide});
  const frameMaterial=new LineBasicMaterial({color:'#64816a',transparent:true,opacity:0.65});
  const floor=new Mesh(floorShape,floorMaterial);floor.position.y=-0.022;scene.add(floor);
  const frame=new LineSegments(edges,frameMaterial);frame.position.y=0.375;scene.add(frame);
  const canopy=createCanopy(leafMaterial);scene.add(canopy.group);
  const materials=STORES.map(key=>new MeshStandardMaterial({color:STORE_COLORS[key],roughness:0.8}));
  const bars={} as Record<Store,Mesh<BoxGeometry>>;
  STORES.forEach((key,index)=>{const bar=new Mesh(barShape,materials[index]);bar.position.x=0.76+index*0.15;
    scene.add(bar);bars[key]=bar;});
  let disposed=false,pending:number|null=null;
  function render(){
    if(disposed)return;
    if(context!.isContextLost()){failed();return;}
    try{renderer.render(scene,camera);canvas.dataset.drawCalls=String(renderer.info.render.calls);}
    catch{failed();}
  }
  const observer=new ResizeObserver(()=>{
    if(pending!==null)return;
    pending=requestAnimationFrame(()=>{pending=null;
      if(disposed)return;
      const box=canvas.getBoundingClientRect();if(box.width<1 || box.height<1)return;
      renderer.setSize(box.width,box.height,false);camera.aspect=box.width/box.height;camera.updateProjectionMatrix();render();});
  });observer.observe(canvas);controls.addEventListener('change',render);
  return {update(sample){
    try{
      canopy.update(sample.lai.value);const area=canopy.area();
      if(!Number.isFinite(area) || Math.abs(area-sample.lai.value)>Math.max(1e-8,sample.lai.value*1e-6))throw new Error('crop_scene_unavailable');
      const heights=carbonHeights(sample,maximum);
      for(const key of STORES){bars[key].scale.y=heights[key];bars[key].position.y=heights[key]/2;bars[key].visible=heights[key]>0;}
      if(context!.isContextLost()){failed();return;}
      canvas.dataset.sceneAt=sample.at;canvas.dataset.leafSurfaceArea=String(area);
      canvas.dataset.maximumCarbon=String(maximum);
      canvas.dataset.carbonHeights=JSON.stringify(Object.fromEntries(STORES.map(key=>[key,bars[key].scale.y])));
      for(const key of STORES)canvas.setAttribute('data-carbon-'+key.replace('_','-'),String(sample.state[key].value));
      render();
    }catch{failed();}
  },rotate(direction){const delta=camera.position.clone().sub(controls.target);
    delta.applyAxisAngle(new Vector3(0,1,0),direction*Math.PI/8);camera.position.copy(delta.add(controls.target));controls.update();render();},
  reset(){controls.reset();render();},dispose(){disposed=true;observer.disconnect();if(pending!==null)cancelAnimationFrame(pending);
    controls.removeEventListener('change',render);controls.dispose();canopy.dispose();
    [floorShape,barShape,frameShape,edges].forEach(item=>item.dispose());
    [floorMaterial,leafMaterial,frameMaterial,...materials].forEach(item=>item.dispose());renderer.dispose();clearEvidence(canvas);
  }};
}

export default function CropScene({sample,maximum}:{sample:CropSample;maximum:number}){
  const canvas=useRef<HTMLCanvasElement>(null),view=useRef<View|null>(null),latest=useRef(sample);latest.current=sample;
  const [available,setAvailable]=useState<boolean|null>(null),[epoch,setEpoch]=useState(0);
  useEffect(()=>{
    const target=canvas.current;if(!target)return;
    let active=true;
    const fail=()=>{clearEvidence(target);if(active)setAvailable(false);};
    const lost=(event:Event)=>{event.preventDefault();fail();};
    const restored=()=>{if(active)setEpoch(value=>value+1);};
    target.addEventListener('webglcontextlost',lost);target.addEventListener('webglcontextrestored',restored);
    try{view.current=createView(target,maximum,fail);setAvailable(!!view.current);view.current?.update(latest.current);}
    catch{view.current?.dispose();view.current=null;fail();}
    return()=>{active=false;target.removeEventListener('webglcontextlost',lost);target.removeEventListener('webglcontextrestored',restored);
      view.current?.dispose();view.current=null;};
  },[maximum,epoch]);
  useEffect(()=>{view.current?.update(sample);},[sample]);
  return <div className="crop-scene" data-selected-at={sample.at}>
    <div className="crop-scene-status"><span className="badge">LAI 기반 모식도</span>
      <span role="status">{available===null?'성장 3D 준비 중':available?'성장 3D 준비됨':'표·그래프로 확인'}</span></div>
    <canvas ref={canvas} className={'crop-canvas'+(available===false?' unavailable':'')} aria-hidden="true"/>
    {available===false && <div className="crop-scene-fallback"><strong>성장 3D를 사용할 수 없습니다.</strong>
      <p>같은 시점의 수치와 시간 조작은 표·그래프에서 사용할 수 있습니다.</p>
      <button className="button secondary" onClick={()=>setEpoch(value=>value+1)}>성장 3D 다시 시도</button></div>}
    <div className="crop-camera" aria-label="성장 모식도 시점 조작">
      <button className="button secondary" aria-label="성장 왼쪽에서 보기" disabled={!available} onClick={()=>view.current?.rotate(-1)}>왼쪽</button>
      <button className="button secondary" aria-label="성장 기본 시점" disabled={!available} onClick={()=>view.current?.reset()}>기본 시점</button>
      <button className="button secondary" aria-label="성장 오른쪽에서 보기" disabled={!available} onClick={()=>view.current?.rotate(1)}>오른쪽</button></div>
    <p className="crop-caption">바닥 1m² 기준 잎 면적 {displayNumber(sample.lai.value)}m².
      잎의 배치·패치 수와 지지선은 모식 표현이며 식물의 키·잎수·착과수·숙기를 계산하지 않습니다.</p>
    <p className="crop-caption">옆의 네 막대는 기관 탄소량 비교입니다. 공통 최대 {displayNumber(maximum)} {CARBON_UNIT}를 사용하며 열매 크기·수확량을 뜻하지 않습니다.</p>
  </div>;
}
