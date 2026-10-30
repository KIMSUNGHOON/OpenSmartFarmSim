import {CubeUVReflectionMapping,DataTexture,HalfFloatType,LinearFilter,LinearSRGBColorSpace,RGBAFormat} from 'three';
import lightingURL from './roomLighting-v1.rgba16le.gz?url';

export const ROOM_LIGHTING={width:768,height:1024,bytes:6291456,gzip_bytes:1194775,
 sha256:'618988bf92870cd877e6fbc89f7c4d546ae028664978c6c8d6c57fc11f207202',
 gzip_sha256:'04cfd8ebd12bcdd03b994a737a846a97816aeb48a53913c614ff9667281b1234'} as const;
async function digest(bytes:ArrayBuffer){return [...new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))].map(v=>v.toString(16).padStart(2,'0')).join('');}
async function bounded(stream:ReadableStream<Uint8Array>,limit:number,signal:AbortSignal){
 const reader=stream.getReader(),parts:Uint8Array[]=[];let total=0;
 const abort=()=>{void reader.cancel().catch(()=>{});};signal.addEventListener('abort',abort,{once:true});
 try{for(;;){signal.throwIfAborted();const {done,value}=await reader.read();if(done)break;
  total+=value.byteLength;if(total>limit)throw Error('room_lighting_size');parts.push(value);
 }signal.throwIfAborted();if(total!==limit)throw Error('room_lighting_size');
 const joined=new Uint8Array(total);let at=0;for(const part of parts){joined.set(part,at);at+=part.length;}return joined.buffer;
 }finally{signal.removeEventListener('abort',abort);await reader.cancel().catch(()=>{});reader.releaseLock();}
}
export async function decodeRoomLighting(raw:ArrayBuffer){
 if(raw.byteLength!==ROOM_LIGHTING.bytes||await digest(raw)!==ROOM_LIGHTING.sha256)throw Error('room_lighting_integrity');
 const view=new DataView(raw),pixels=new Uint16Array(raw.byteLength/2);
 for(let i=0;i<pixels.length;i++)pixels[i]=view.getUint16(i*2,true);
 const texture=new DataTexture(pixels,ROOM_LIGHTING.width,ROOM_LIGHTING.height,RGBAFormat,HalfFloatType);
 texture.mapping=CubeUVReflectionMapping;texture.colorSpace=LinearSRGBColorSpace;
 texture.magFilter=LinearFilter;texture.minFilter=LinearFilter;texture.needsUpdate=true;return texture;
}
export async function loadRoomLighting(requestSignal:AbortSignal){
 const signal=AbortSignal.any([requestSignal,AbortSignal.timeout(15000)]);
 const response=await fetch(lightingURL,{signal,redirect:'error',credentials:'same-origin',cache:'force-cache'});
 if(response.status!==200||!response.body)throw Error('room_lighting_unavailable');
 const gzip=await bounded(response.body,ROOM_LIGHTING.gzip_bytes,signal);
 if(await digest(gzip)!==ROOM_LIGHTING.gzip_sha256)throw Error('room_lighting_integrity');
 const plain=await bounded(new Response(gzip).body!.pipeThrough(new DecompressionStream('gzip')),ROOM_LIGHTING.bytes,signal);
 signal.throwIfAborted();const texture=await decodeRoomLighting(plain);
 if(signal.aborted){texture.dispose();signal.throwIfAborted();}return texture;
}
