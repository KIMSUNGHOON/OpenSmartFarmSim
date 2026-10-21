import { afterEach,describe,it,expect,vi } from 'vitest';
import { readFileSync } from 'node:fs';
import { decodeLeafAreaFrame,loadLeafAreaReplay } from './leafAreaReplay';

const file=(name:string)=>readFileSync(new URL('../public/leaf-area-replay/'+name,import.meta.url));
const value=(name:string)=>JSON.parse(file(name).toString());
afterEach(()=>vi.unstubAllGlobals());
describe('original stored leaf area replay',()=>{
  it('keeps all twelve original UTCs, IDs, square metres and the unchanged stem frame',()=>{
    const root=value('root.json'),index=value('index.json');
    for(let i=0;i<12;i++){
      const raw=value(`frame-${i}.json`),frame=decodeLeafAreaFrame(raw,index.frames[i],root);
      expect(frame.at).toBe(frame.stem.at);expect(frame.leaves).toEqual(raw.leaves);
      expect(frame.tracked_leaf_area.unit).toBe('m2');expect(frame.tracked_leaf_count).toBe(3);
      expect(frame.stem).toEqual(JSON.parse(readFileSync(new URL(`../public/morphology-rational-replay/frame-${i}.json`,import.meta.url),'utf8')));
    }
  });
  it.each(['unit','leaf-id','attachment','age','curve','negative','at','scope','stem-result'])('rejects %s mixing',kind=>{
    const raw=value('frame-0.json'),root=value('root.json'),descriptor=value('index.json').frames[0];
    if(kind==='unit')raw.leaves[0].area.unit='cm2';
    if(kind==='leaf-id')raw.leaves[0].leaf_id='unreviewed-leaf';
    if(kind==='attachment')raw.leaves[0].attachment_internode_id='missing-stem-node';
    if(kind==='age')raw.leaves[0].age_exact={numerator:'2',denominator:'2',unit:'degC_day'};
    if(kind==='curve')raw.leaves[0].curve_sha256='0'.repeat(64);
    if(kind==='negative')raw.leaves[0].area.value=-1;
    if(kind==='at')raw.at='2026-10-02T00:00:00Z';
    if(kind==='scope')raw.gates='passed';
    if(kind==='stem-result')raw.stem.result_sha256='0'.repeat(64);
    expect(()=>decodeLeafAreaFrame(raw,descriptor,root)).toThrow();
  });
  it('loads only the seventeen checked original files without a calculation request',async()=>{
    const fetcher=vi.fn(async(input:RequestInfo|URL)=>new Response(new Uint8Array(file(String(input).split('/').at(-1)!))));
    vi.stubGlobal('fetch',fetcher);const data=await loadLeafAreaReplay(new AbortController().signal);
    expect(data.frames).toHaveLength(12);expect(fetcher).toHaveBeenCalledTimes(17);
    expect(fetcher.mock.calls.every(([url])=>String(url).startsWith('./leaf-area-replay/'))).toBe(true);
  });
  it('rejects changed response bytes with no replacement data',async()=>{
    vi.stubGlobal('fetch',async(input:RequestInfo|URL)=>{const name=String(input).split('/').at(-1)!;
      return new Response(new Uint8Array(name==='frame-7.json'?Buffer.concat([file(name),Buffer.from(' ')]):file(name)));});
    await expect(loadLeafAreaReplay(new AbortController().signal)).rejects.toThrow();
  });
});
