import {expect,it} from 'vitest';
import {readFileSync} from 'node:fs';
import {checkpointQuantities} from './supplyMorphologyQuantityAccounts';
import {quantityLayout} from './supplyMorphologyQuantityLayout';
const text=(name:string)=>readFileSync(new URL(`../public/supply-morphology-replay/own-public-v1/${name}`,import.meta.url),'utf8');
const index=JSON.parse(text('index.json')),root=JSON.parse(text('root.json'));
const paths=new Map<string,string>(index.blobs.map((d:{sha256:string;path:string})=>[d.sha256,d.path]));
const blob=(hash:string)=>JSON.parse(text(paths.get(hash)!));
const cases=root.segments.flatMap((s:{context:{sha256:string};checkpoints:{sha256:string}[]})=>{
 const seed=blob(s.context.sha256).descriptor.seed;
 return s.checkpoints.map(c=>({seed,cp:blob(c.sha256)}));
});
it('validates all33 original checkpoint transfer compositions, schedule clocks and accounts',()=>{
 expect(cases).toHaveLength(33);
 for(const {seed,cp}of cases)expect(()=>checkpointQuantities(quantityLayout(seed),cp,root.shoot_base_temperature)).not.toThrow();
});
it.each(['missing_flow','flow_unit','nonfinite','lifetime','seed_unit','point_unit','schedule','budget','residual','missing_account','account_unit'])('rejects quantity error %s independently of graph hashes',kind=>{
 const {seed,cp}=structuredClone(cases[1]);
 if(kind==='missing_flow')delete cp.branch_integrated_transfers.leaf_0_inflow;
 if(kind==='flow_unit')cp.branch_integrated_transfers.leaf_0_inflow.unit='kg';
 if(kind==='nonfinite')cp.branch_integrated_transfers.leaf_0_inflow.value=Infinity;
 if(kind==='lifetime'){const q=cp.lifetime_transfers_exact.leaf_0_inflow;q.numerator=(BigInt(q.numerator)+BigInt(q.denominator)).toString();}
 if(kind==='seed_unit')seed.lifetime_transfers_exact.leaf_0_inflow.unit='kg';
 if(kind==='point_unit')cp.point_totals_exact.buffer_debit.unit='kg';
 if(kind==='schedule')cp.schedule.age_exact={numerator:'0',denominator:'1',unit:'degC_day'};
 if(kind==='budget')cp.global_ledgers.carbohydrate.budget_exact={numerator:'-1',denominator:'1',unit:'mg_CH2O/m2_floor'};
 if(kind==='residual')cp.branch_ledgers.carbohydrate.residual_exact={numerator:'1000000000',denominator:'1',unit:'mg_CH2O/m2_floor'};
 if(kind==='missing_account')delete cp.global_ledgers.leaf_0_construction;
 if(kind==='account_unit')cp.global_ledgers.leaf_0_geometry.residual_exact.unit='m';
 expect(()=>checkpointQuantities(quantityLayout(seed),cp,root.shoot_base_temperature)).toThrow();
});
