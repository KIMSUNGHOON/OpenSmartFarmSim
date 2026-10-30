import {expect,it} from 'vitest';
import {readFileSync} from 'node:fs';
import {quantityLayout} from './supplyMorphologyQuantityLayout';
const text=(name:string)=>readFileSync(new URL(`../public/supply-morphology-replay/own-public-v1/${name}`,import.meta.url),'utf8');
const index=JSON.parse(text('index.json')),root=JSON.parse(text('root.json'));
const paths=new Map<string,string>(index.blobs.map((d:{sha256:string;path:string})=>[d.sha256,d.path]));
const seeds=root.segments.map((s:{context:{sha256:string}})=>JSON.parse(text(paths.get(s.context.sha256)!)).descriptor.seed);
it('matches every actual expanded layout and ordered explicit inventories',()=>{
 for(const seed of seeds){const s=quantityLayout(seed);expect(s.size+2*s.h).toBe(seed.initial_sample.state.length);expect(s.n).toBe(seed.organs.leaves.length);}
});
it.each(['prefix','leaf_order','node_order','unit','duplicate_leaf','missing_compartment','parent','floor','extra'])('rejects inconsistent source layout %s',kind=>{
 const s=structuredClone(seeds[0]);
 if(kind==='prefix')s.state_layout.original_prefix_length++;
 if(kind==='leaf_order')s.state_layout.original.leaf_ids.reverse();
 if(kind==='node_order')s.state_layout.internode_ids.reverse();
 if(kind==='unit')s.state_layout.original.units.leaf_blocks.area='ha';
 if(kind==='duplicate_leaf')s.program.leaves[1].leaf_id=s.program.leaves[0].leaf_id;
 if(kind==='missing_compartment')s.program.stem_root_compartments.pop();
 if(kind==='parent')s.organs.leaves[0].parent_internode_id='missing';
 if(kind==='floor')s.program.model_floor_area.value=0;
 if(kind==='extra')s.state_layout.extra=true;
 expect(()=>quantityLayout(s)).toThrow();
});
