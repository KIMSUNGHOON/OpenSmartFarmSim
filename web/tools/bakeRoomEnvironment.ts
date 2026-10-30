import {PMREMGenerator,WebGLRenderer} from 'three';
import {RoomEnvironment} from 'three/addons/environments/RoomEnvironment.js';

document.getElementById('bake')!.addEventListener('click',async()=>{
 const status=document.getElementById('status')!,canvas=document.createElement('canvas');
 const renderer=new WebGLRenderer({canvas}),room=new RoomEnvironment(),generator=new PMREMGenerator(renderer);
 let target:ReturnType<PMREMGenerator['fromScene']>|undefined;
 try{
  status.textContent='Baking';target=generator.fromScene(room,.04);
  const pixels=new Uint16Array(target.width*target.height*4);
  await renderer.readRenderTargetPixelsAsync(target,0,0,target.width,target.height,pixels);
  const bytes=new Uint8Array(pixels.length*2),view=new DataView(bytes.buffer);
  for(let i=0;i<pixels.length;i++)view.setUint16(i*2,pixels[i]!,true);
  let binary='';for(let i=0;i<bytes.length;i+=8192)binary+=String.fromCharCode(...bytes.subarray(i,i+8192));
  const texture=target.texture;
  status.textContent=JSON.stringify({width:target.width,height:target.height,type:texture.type,format:texture.format,
   mapping:texture.mapping,colorSpace:texture.colorSpace,flipY:texture.flipY,minFilter:texture.minFilter,magFilter:texture.magFilter,
   byte_order:'little',base64:btoa(binary)});
  status.dataset.complete='true';
 }catch{status.textContent='Bake failed';status.dataset.failed='true';}
 finally{target?.dispose();generator.dispose();room.dispose();renderer.dispose();renderer.forceContextLoss();}
});
