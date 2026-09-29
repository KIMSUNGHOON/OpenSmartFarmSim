import { useEffect,useRef,useState } from 'react';
import { Scene,PerspectiveCamera,WebGLRenderer,Color,Mesh,MeshStandardMaterial,MeshBasicMaterial,
  BoxGeometry,CylinderGeometry,Vector3,Group,HemisphereLight,DirectionalLight,DoubleSide } from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import type { ThermalPoint } from './thermal-api';
import { temperatureColor } from './replay-format';

type View={update:(point:ThermalPoint)=>void;rotate:(direction:number)=>void;reset:()=>void;dispose:()=>void};
function createView(canvas:HTMLCanvasElement,range:readonly [number,number],maximumHeat:number,
    failed:()=>void):View|null {
  const context=canvas.getContext('webgl2',{antialias:true,alpha:true});
  if (!context || context.isContextLost()) return null;
  const renderer=new WebGLRenderer({canvas,context,antialias:true,alpha:true});
  renderer.setPixelRatio(Math.min(devicePixelRatio,1.5));
  renderer.debug.onShaderError=()=>{throw new Error('scene_shader_unavailable');};
  const scene=new Scene();scene.background=new Color('#f2f0e4');
  const camera=new PerspectiveCamera(38,1,0.1,80);camera.position.set(11,8,13);
  const controls=new OrbitControls(camera,canvas);controls.target.set(0,1.4,0);
  controls.enablePan=false;controls.enableDamping=false;controls.minDistance=9;controls.maxDistance=24;
  controls.maxPolarAngle=Math.PI/2.15;controls.update();controls.saveState();
  scene.add(new HemisphereLight('#ffffff','#7b8170',2.3));
  const light=new DirectionalLight('#fff8dc',2.2);light.position.set(-5,10,8);scene.add(light);
  const geometry: (BoxGeometry|CylinderGeometry)[]=[];
  const materials:(MeshStandardMaterial|MeshBasicMaterial)[]=[];
  const metal=new MeshStandardMaterial({color:'#405a4b',roughness:0.65,metalness:0.15});materials.push(metal);
  const glass=new MeshStandardMaterial({color:'#e9f4ed',transparent:true,opacity:0.12,side:DoubleSide,
    depthWrite:false,roughness:0.35});materials.push(glass);
  const floor=new MeshStandardMaterial({color:'#b9cdb5',roughness:0.95});materials.push(floor);
  const plinth=new MeshStandardMaterial({color:'#d3d0bf',roughness:0.95});materials.push(plinth);
  const heat=new MeshBasicMaterial({color:'#c7782c'});materials.push(heat);
  const house=new Group();scene.add(house);
  function box(size:readonly [number,number,number],position:readonly [number,number,number],material:MeshStandardMaterial|MeshBasicMaterial) {
    const shape=new BoxGeometry(...size);geometry.push(shape);const mesh=new Mesh(shape,material);
    mesh.position.set(...position);house.add(mesh);return mesh;
  }
  function beam(a:readonly [number,number,number],b:readonly [number,number,number]) {
    const start=new Vector3(...a),end=new Vector3(...b),delta=end.clone().sub(start);
    const shape=new CylinderGeometry(0.035,0.035,delta.length(),6);geometry.push(shape);
    const mesh=new Mesh(shape,metal);mesh.position.copy(start.add(end).multiplyScalar(0.5));
    mesh.quaternion.setFromUnitVectors(new Vector3(0,1,0),delta.normalize());house.add(mesh);
  }
  box([7.4,0.25,10.2],[0,-0.23,0],plinth);box([6,0.07,8],[0,-0.06,0],floor);
  box([0.02,3,8],[-3,1.5,0],glass);box([0.02,3,8],[3,1.5,0],glass);
  box([6,3,0.02],[0,1.5,-4],glass);box([6,3,0.02],[0,1.5,4],glass);
  const slope=Math.atan2(1.3,3),roofWidth=Math.hypot(3,1.3);
  box([roofWidth,0.02,8],[-1.5,3.65,0],glass).rotation.z=slope;
  box([roofWidth,0.02,8],[1.5,3.65,0],glass).rotation.z=-slope;
  for(const z of [-4,-2,0,2,4]) {
    beam([-3,0,z],[-3,3,z]);beam([3,0,z],[3,3,z]);
    beam([-3,3,z],[0,4.3,z]);beam([0,4.3,z],[3,3,z]);beam([-3,0,z],[3,0,z]);
  }
  for(const x of [-3,3]) {beam([x,0,-4],[x,0,4]);beam([x,3,-4],[x,3,4]);}
  beam([0,4.3,-4],[0,4.3,4]);
  const heatBar=box([0.3,1,0.3],[3.5,0.5,2.9],heat);
  let point:ThermalPoint|null=null,disposed=false;
  function render() {
    if(disposed || context!.isContextLost())return;
    try {
      const width=canvas.clientWidth,height=canvas.clientHeight;
      if(!width || !height)return;
      renderer.setSize(width,height,false);camera.aspect=width/height;camera.updateProjectionMatrix();
      renderer.render(scene,camera);
      if(point) {
        canvas.dataset.sceneAtUtc=point.at_utc;canvas.dataset.temperatureK=String(point.temperature_k);
        canvas.dataset.heatDeliveredWTh=String(point.heat_delivered_w_th);
      }
      canvas.dataset.drawCalls=String(renderer.info.render.calls);
    } catch {failed();}
  }
  controls.addEventListener('change',render);
  let resizeFrame:number|null=null;
  const resize=new ResizeObserver(()=>{if(resizeFrame!==null)return;
    resizeFrame=requestAnimationFrame(()=>{resizeFrame=null;render();});});resize.observe(canvas);
  return {
    update(value) {
      point=value;floor.color.setStyle(temperatureColor(value,range));
      heatBar.visible=value.heat_delivered_w_th>0;
      const height=maximumHeat>0 ? value.heat_delivered_w_th/maximumHeat*2.6 : 0;
      heatBar.scale.y=height;heatBar.position.y=height/2;render();
    },
    rotate(direction) {const delta=camera.position.clone().sub(controls.target);
      delta.applyAxisAngle(new Vector3(0,1,0),direction*Math.PI/8);camera.position.copy(delta.add(controls.target));controls.update();render();},
    reset() {controls.reset();render();},
    dispose() {disposed=true;resize.disconnect();if(resizeFrame!==null)cancelAnimationFrame(resizeFrame);
      controls.removeEventListener('change',render);controls.dispose();
      geometry.forEach(item=>item.dispose());materials.forEach(item=>item.dispose());renderer.dispose();
      delete canvas.dataset.sceneAtUtc;delete canvas.dataset.drawCalls;
    },
  };
}

export default function ZoneScene({point,range,maximumHeat}:{point:ThermalPoint;range:readonly [number,number];maximumHeat:number}) {
  const canvas=useRef<HTMLCanvasElement>(null),view=useRef<View|null>(null);
  const latest=useRef(point);latest.current=point;
  const [available,setAvailable]=useState<boolean|null>(null),[epoch,setEpoch]=useState(0);
  useEffect(()=>{
    const target=canvas.current;if(!target)return;
    let active=true;
    const fail=()=>{if(active)setAvailable(false);delete target.dataset.sceneAtUtc;};
    const lost=(event:Event)=>{event.preventDefault();fail();};
    const restored=()=>{if(active)setEpoch(value=>value+1);};
    target.addEventListener('webglcontextlost',lost);target.addEventListener('webglcontextrestored',restored);
    try {view.current=createView(target,range,maximumHeat,fail);setAvailable(!!view.current);view.current?.update(latest.current);}
    catch {fail();}
    return ()=>{active=false;view.current?.dispose();view.current=null;
      target.removeEventListener('webglcontextlost',lost);target.removeEventListener('webglcontextrestored',restored);};
  },[range,maximumHeat,epoch]);
  useEffect(()=>{view.current?.update(point);},[point]);
  return <div className="zone-scene" data-selected-at={point.at_utc}>
    <div className="scene-topline"><span className="badge">개념적 단일 구역</span><span role="status">{available===null ? '3D 준비 중' : available ? '3D 준비됨' : '3D 대신 표와 그래프로 확인'}</span></div>
    <canvas ref={canvas} className={available===false ? 'zone-canvas unavailable' : 'zone-canvas'} aria-hidden="true"/>
    {available===false && <div className="scene-fallback"><strong>이 환경에서 3D를 사용할 수 없습니다.</strong>
      <p>같은 시각의 모든 수치와 시간 선택은 표·그래프에서 계속 사용할 수 있습니다.</p>
      <button className="button secondary" onClick={()=>setEpoch(value=>value+1)}>3D 다시 시도</button></div>}
    <div className="scene-camera" aria-label="장면 시점 조작"><button className="button secondary" disabled={!available} onClick={()=>view.current?.rotate(-1)}>왼쪽에서 보기</button>
      <button className="button secondary" disabled={!available} onClick={()=>view.current?.reset()}>기본 시점</button>
      <button className="button secondary" disabled={!available} onClick={()=>view.current?.rotate(1)}>오른쪽에서 보기</button></div>
    <p className="muted">형상·크기·설비 배치는 설명용 개념도입니다. 온도는 바닥 색, 모델 공급열은 옆의 막대로 표시합니다.</p>
  </div>;
}
