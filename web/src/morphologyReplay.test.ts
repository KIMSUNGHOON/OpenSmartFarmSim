import { describe,it,expect,vi } from 'vitest';
import { readFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { decodeMorphologyFrame,loadMorphologyReplay } from './morphologyReplay';
import { MORPHOLOGY_FIXTURE } from './morphologyReplayFixture';

const folder=new URL('../public/morphology-replay/',import.meta.url);
const index=JSON.parse(readFileSync(new URL('index.json',folder),'utf8'));
const raw=(i:number)=>JSON.parse(readFileSync(new URL(`frame-${i}.json`,folder),'utf8'));

describe('immutable morphology replay consumer',()=>{
  it('pins the public export and original artifact, and preserves every stored quantity and UTC',()=>{
    expect(createHash('sha256').update(readFileSync(new URL('index.json',folder))).digest('hex')).toBe(MORPHOLOGY_FIXTURE.index_sha256);
    expect(createHash('sha256').update(readFileSync(new URL('root.json',folder))).digest('hex')).toBe(MORPHOLOGY_FIXTURE.artifact_sha256);
    for(let i=0;i<12;i++){
      const value=raw(i),frame=decodeMorphologyFrame(value,index.frames[i]);expect(frame).toEqual(value);
      expect(frame.at).toBe(index.frames[i].at);expect(frame.internodes.length).toBe(3+Math.floor((i+1)/4));
      expect(frame).not.toHaveProperty('height');expect(frame).not.toHaveProperty('yield');
    }
  });
  it.each(['unit','origin','UTC','id','order','quantity','extra'])('holds malformed stored %s',change=>{
    const value=raw(11);
    if(change==='unit')value.internodes[0].length.unit='cm';
    if(change==='origin')value.claim_scope='validated_farm';
    if(change==='UTC')value.at='2026-10-03T00:00:00Z';
    if(change==='id')value.internodes[1].internode_id=value.internodes[0].internode_id;
    if(change==='order')value.internodes[1].sequence=99;
    if(change==='quantity')value.internodes[0].length.value=0;
    if(change==='extra')value.yield=1;
    expect(()=>decodeMorphologyFrame(value,index.frames[11])).toThrow();
  });
  it('reads one GET at a time, verifies bytes, and refuses a corrupted later frame',async()=>{
    let active=0,peak=0,calls=0,corrupt=false;
    vi.stubGlobal('fetch',async(url:string,options:RequestInit)=>{
      expect(options.cache).toBe('no-store');expect(options.method).toBeUndefined();active++;peak=Math.max(peak,active);calls++;
      const name=url.split('/').at(-1)!;const original=readFileSync(new URL(name,folder));
      const bytes=Uint8Array.from(corrupt&&name==='frame-5.json'?Buffer.from('{}'):original);
      return new Response(new ReadableStream({start(controller){controller.enqueue(bytes);controller.close();active--;}}));
    });
    try{
      const replay=await loadMorphologyReplay(new AbortController().signal);expect(replay.frames).toEqual(Array.from({length:12},(_,i)=>raw(i)));
      expect(calls).toBe(13);expect(peak).toBe(1);
      corrupt=true;await expect(loadMorphologyReplay(new AbortController().signal)).rejects.toThrow();
    }finally{vi.unstubAllGlobals();}
  });
});
