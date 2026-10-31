import {expect,it} from 'vitest';
import {document,type WireDocument} from './supplyMorphologyGraphValues';
import {materialSourceGraph,materialFrameValue,storedChainProof,type GetRecord,type Chain} from './supplyMaterialGraphChecks';
import {alter,text} from './supplyMaterialTestData';
const root=document(text('root.json')),hash=(s:unknown)=>document(text(`blob-${s}.json`));
const get:GetRecord=(s)=>hash(s),original=hash((root.value.source as {original_root:{sha256:string}}).original_root.sha256);
const source=await materialSourceGraph(root,get,original,new AbortController().signal);
it('verifies every base/forcing/material stored operation without a new RHS',()=>{
 for(const kind of ['base','forcing','material']as const)expect(()=>storedChainProof(source[kind],kind)).not.toThrow();
});
function changedPage(path:string[],value:unknown):Chain{
 const chain=structuredClone(source.material),link=chain.links[1]!;
 link.page=document(alter(link.page!.raw,path,value));return chain;
}
it.each([
 [['evidence','stages','0','stage'],'k4'],[['evidence','stages','1','state','0'],1.5],
 [['evidence','stages','0','rates','0'],1.5],[['evidence','stages','0','flux','0'],1.5],
 [['evidence','endpoint','state','0'],1.5],[['evidence','flux_order','0','unit'],'kg'],
 [['evidence','step_seconds_exact','unit'],'day'],[['kind'],'forcing_switch']
 ]as Array<[string[],unknown]>)('rejects saved operation mutation %j', (path,value)=>expect(()=>storedChainProof(changedPage(path,value),'material')).toThrow());
it.each([
 [['numeric','event_sequence'],true],[['integration_count'],false],[['span_index'],true],
 [['numeric','schema_version'],'supply-season-current-v1'],[['phase'],'forcing_after'],
 [['effective_rights','display'],false],[['numeric','global_ledgers','carbohydrate','budget_exact','unit'],'kg']
 ]as Array<[string[],unknown]>)('rejects new confirmed state semantics %j',(path,value)=>{
 const g=structuredClone(source),link=g.material.links[0]!;link.current=document(alter(link.current.raw,path,value));
 // Preserve original float tokens for an unchanged frame.
 const raw=document(text('frame-1.json')).fields.frame!;
 expect(()=>materialFrameValue(document(raw),1,g,root)).toThrow();
});
it('rejects integer-looking float event counters rather than coercing them',()=>{
 const g=structuredClone(source),link=g.material.links[0]!,fields=link.current.fields;
 const raw=fields.numeric!.replace('"event_sequence":11','"event_sequence":11.0');
 link.current=document(link.current.raw.replace(fields.numeric!,raw));
 expect(()=>materialFrameValue(document(document(text('frame-1.json')).fields.frame!),1,g,root)).toThrow();
});
it('retains distinct before and after evidence at the same exact time',()=>{
 const values:WireDocument[]=[0,1].map(i=>document(document(text(`frame-${i}.json`)).fields.frame!));
 const before=materialFrameValue(values[0]!,0,source,root),after=materialFrameValue(values[1]!,1,source,root);
 expect(before.at).toEqual(after.at);expect(before.leaves.length).toBe(11);expect(after.leaves.length).toBe(12);
 expect(before.snapshot.state.length).toBe(176);expect(after.snapshot.state.length).toBe(182);
});
