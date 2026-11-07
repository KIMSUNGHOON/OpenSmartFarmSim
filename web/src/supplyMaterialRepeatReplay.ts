import {integer,need} from './storedLeafReplayIO';
import {decodeRepeatManifest,decodeRepeatFrame,type RepeatManifest,type RepeatManifestExpectation,type RepeatFrame} from './supplyMaterialRepeatWire';

export type RepeatRead=(selection:{kind:'manifest'}|{kind:'frame';index:number},signal:AbortSignal)=>Promise<Uint8Array>;
export type RepeatSelection={rootSha256:string;index:number;manifest:RepeatManifest;frame:RepeatFrame};

export class SupplyMaterialRepeatRequest{
 private generation=0n;
 private controller?:AbortController;
 private value:RepeatSelection|null=null;
 private readonly read:RepeatRead;
 private readonly expected:RepeatManifestExpectation;
 constructor(read:RepeatRead,expected:RepeatManifestExpectation){
  need(typeof read==='function');this.read=read;this.expected=structuredClone(expected);
 }
 current():RepeatSelection|null{return this.value===null?null:structuredClone(this.value);}
 cancel():void{
  this.generation++;const previous=this.controller;this.controller=undefined;this.value=null;previous?.abort();
 }
 async select(index:number):Promise<RepeatSelection>{
  const previous=this.controller,generation=++this.generation,controller=new AbortController(),signal=controller.signal;
  this.controller=controller;this.value=null;
  const fence=()=>{signal.throwIfAborted();need(generation===this.generation);};
  try{
   previous?.abort();fence();integer(index,0,511);
   const manifestRaw=await this.read({kind:'manifest'},signal);fence();
   const manifest=await decodeRepeatManifest(manifestRaw,this.expected);fence();
   integer(index,0,manifest.frames.length-1);
   const frameRaw=await this.read({kind:'frame',index},signal);fence();
   const frame=await decodeRepeatFrame(frameRaw,manifest,index);fence();
   const selection:RepeatSelection={rootSha256:this.expected.rootSha256,index,manifest:structuredClone(manifest),frame};
   const result=structuredClone(selection);fence();this.value=selection;return result;
  }finally{if(generation===this.generation)this.controller=undefined;}
 }
}
