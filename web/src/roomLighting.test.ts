import {readFileSync} from 'node:fs';
import {gunzipSync} from 'node:zlib';
import {afterEach,expect,it,vi} from 'vitest';
import {CubeUVReflectionMapping,HalfFloatType,LinearFilter,LinearSRGBColorSpace} from 'three';
import {decodeRoomLighting,loadRoomLighting,ROOM_LIGHTING} from './roomLighting';
const gzip=readFileSync(new URL('./roomLighting-v1.rgba16le.gz',import.meta.url)),plain=gunzipSync(gzip);
const raw=()=>Uint8Array.from(plain).buffer;
afterEach(()=>vi.unstubAllGlobals());
it('reuses the exact baked half-float cube-UV lighting with no runtime convolution',async()=>{
 const texture=await decodeRoomLighting(raw());
 expect([texture.image.width,texture.image.height,texture.type,texture.mapping,texture.minFilter,texture.magFilter,texture.colorSpace])
  .toEqual([768,1024,HalfFloatType,CubeUVReflectionMapping,LinearFilter,LinearFilter,LinearSRGBColorSpace]);
 const data=texture.image.data as Uint16Array;
 expect(data.length*2).toBe(ROOM_LIGHTING.bytes);expect(texture.flipY).toBe(false);expect(texture.generateMipmaps).toBe(false);
 for(let i=0;i<data.length;i++)if((data[i]!&0x7c00)===0x7c00)throw Error('non_finite_environment');
 expect(data.some(v=>v!==0)).toBe(true);texture.dispose();
});
it('loads the exact bounded gzip, and cancels an already aborted load',async()=>{
 vi.stubGlobal('fetch',vi.fn(async()=>new Response(Uint8Array.from(gzip).buffer)));
 const texture=await loadRoomLighting(new AbortController().signal);expect(texture.image.width).toBe(768);texture.dispose();
 const controller=new AbortController();controller.abort();await expect(loadRoomLighting(controller.signal)).rejects.toThrow();
});
it.each(['short','oversize','tampered'] as const)('rejects %s lighting before any texture is published',async kind=>{
 const data=kind==='oversize'?new Uint8Array(gzip.length+1):Uint8Array.from(gzip.subarray(0,kind==='short'?100:gzip.length));
 if(kind==='tampered')data[321]=data[321]!^1;
 vi.stubGlobal('fetch',vi.fn(async()=>new Response(data.buffer)));await expect(loadRoomLighting(new AbortController().signal)).rejects.toThrow();
});
it('rejects truncation and any changed baked lighting byte',async()=>{
 await expect(decodeRoomLighting(raw().slice(0,-1))).rejects.toThrow('integrity');
 const changed=new Uint8Array(raw());changed[321]=changed[321]!^1;await expect(decodeRoomLighting(changed.buffer)).rejects.toThrow('integrity');
});
