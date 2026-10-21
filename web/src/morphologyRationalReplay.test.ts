import { describe,it,expect,vi } from 'vitest';
import { readFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { decodeMorphologyFrame,loadMorphologyReplay,RATIONAL_MORPHOLOGY_SOURCE } from './morphologyReplay';
import { MORPHOLOGY_RATIONAL_FIXTURE } from './morphologyRationalReplayFixture';

const folder=new URL('../public/morphology-rational-replay/',import.meta.url);
const index=JSON.parse(readFileSync(new URL('index.json',folder),'utf8'));
const raw=(i:number)=>JSON.parse(readFileSync(new URL(`frame-${i}.json`,folder),'utf8'));

describe('rational-time immutable morphology consumer',()=>{
  it('preserves the original UTC, origin, exact births and lengths of all twelve v2 frames',()=>{
    expect(createHash('sha256').update(readFileSync(new URL('index.json',folder))).digest('hex')).toBe(MORPHOLOGY_RATIONAL_FIXTURE.index_sha256);
    expect(createHash('sha256').update(readFileSync(new URL('root.json',folder))).digest('hex')).toBe(MORPHOLOGY_RATIONAL_FIXTURE.artifact_sha256);
    for(let i=0;i<12;i++)expect(decodeMorphologyFrame(raw(i),index.frames[i],RATIONAL_MORPHOLOGY_SOURCE)).toEqual(raw(i));
    expect(raw(11).internodes.slice(3).map((n:{emerged_elapsed_seconds_exact:unknown})=>n.emerged_elapsed_seconds_exact)).toEqual(
      [432000,864000,1296000].map(n=>({numerator:String(n),denominator:'17',unit:'s'})));
    expect(()=>decodeMorphologyFrame(raw(11),index.frames[11])).toThrow();
  });
  it.each(['unit','unreduced','negative','zero-denominator','capacity','origin','future-birth','approximate-UTC','version','id','order','age-unit','length-unit','claim'])(
    'holds invalid v2 %s',change=>{
      const value=raw(11),node=value.internodes[3],birth=node.emerged_elapsed_seconds_exact;
      if(change==='unit')birth.unit='day';
      if(change==='unreduced'){birth.numerator='864000';birth.denominator='34';}
      if(change==='negative')birth.numerator='-1';
      if(change==='zero-denominator')birth.denominator='0';
      if(change==='capacity')birth.numerator='1'.repeat(1025);
      if(change==='origin')value.time_origin_utc='2026-10-03T00:00:00Z';
      if(change==='future-birth')birth.numerator='99999999';
      if(change==='approximate-UTC')node.emerged_at='2026-10-01T07:03:32Z';
      if(change==='version')value.schema_version='morphology-replay-frame-v1';
      if(change==='id')node.internode_id=value.internodes[0].internode_id;
      if(change==='order')node.sequence=99;
      if(change==='age-unit')node.age_exact.unit='day';
      if(change==='length-unit')node.length.unit='cm';
      if(change==='claim')value.gates='G2_passed';
      expect(()=>decodeMorphologyFrame(value,index.frames[11],RATIONAL_MORPHOLOGY_SOURCE)).toThrow();
    });
  it('uses thirteen sequential GETs for the selected v2 export and holds corrupt later bytes',async()=>{
    let active=0,peak=0,calls=0,corrupt=false;
    vi.stubGlobal('fetch',async(url:string,options:RequestInit)=>{
      expect(url.startsWith('./morphology-rational-replay/')).toBe(true);
      expect(options.cache).toBe('no-store');expect(options.method).toBeUndefined();active++;peak=Math.max(peak,active);calls++;
      const name=url.split('/').at(-1)!;const original=readFileSync(new URL(name,folder));
      const bytes=Uint8Array.from(corrupt&&name==='frame-6.json'?Buffer.from('{}'):original);
      return new Response(new ReadableStream({start(controller){controller.enqueue(bytes);controller.close();active--;}}));
    });
    try{
      const replay=await loadMorphologyReplay(new AbortController().signal,RATIONAL_MORPHOLOGY_SOURCE);
      expect(replay.frames).toEqual(Array.from({length:12},(_,i)=>raw(i)));expect(calls).toBe(13);expect(peak).toBe(1);
      corrupt=true;await expect(loadMorphologyReplay(new AbortController().signal,RATIONAL_MORPHOLOGY_SOURCE)).rejects.toThrow();
    }finally{vi.unstubAllGlobals();}
  });
});
