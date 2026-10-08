import { ApiError,need,object,closed,date,member } from './api-validation';
import { type CropFarm } from './cropReplay';

const MAX_ROWS=262144,MAX_BYTES=2*1024*1024;
const PURPOSES=['harvest','thinning','disposal','sampling'] as const;
const KINDS=['model_terminal_outflow','explicit_fruit_removal'] as const;
const UNITS={carbohydrate:'mg_CH2O/m2_floor',number:'fruits_equivalent/m2_floor',
  dry_matter:'kg_DM/m2_floor',fresh_matter:'kg_FW/m2_floor'} as const;
const CLAIM='synthetic_harvest_allocation_math_only';
type Purpose=typeof PURPOSES[number];
type Kind=typeof KINDS[number];
type Pair=readonly [bigint,bigint];
type Quantity<U extends string>=Readonly<{value:number;unit:U}>;
export type HarvestExact=Readonly<{numerator:string;denominator:string}>;
export type HarvestQuantity<U extends string>=Quantity<U>&Readonly<{exact:HarvestExact}>;
type Quantities=Readonly<{[K in keyof typeof UNITS]:HarvestQuantity<typeof UNITS[K]>}>;
type Meta=Readonly<{code_sha256:string;dependency_sha256:Readonly<{current_query:string;canonical_json:string}>}>;
export type HarvestSource=Readonly<{result_id:string;payload_sha256:string;input_root_sha256:string;
  artifact_sha256:string;math_manifest_sha256:string;source_status:'completed'|'hold'}>;
type Population=Readonly<{population_id:string;scope:'all_model_fruit_cohorts';basis:'m2_floor';basis_evidence_id:string}>;
type Segment=Readonly<{segment_id:string;start_at:string;end_at:string;eta:Quantity<'mg_DM/mg_CH2O'>;dmc:Quantity<'kg_DM/kg_FW'>}>;
type MassParameters=Readonly<{version:'crop-removal-mass-parameters-v1';parameter_id:string;revision:string;
  origin:'synthetic';evidence_level:'assumed';evidence_id:string;available_at:string;population:Population;
  policy:'constant_per_original_interval';sha256:string;segment:Segment;rounding:'nearest_float64_from_exact_input_floats_per_row'}>;
type TerminalPosition=Readonly<{samples:readonly [number,number];sample_sha256:readonly [string,string]}>;
type EventPosition=Readonly<{event:number;input_id:string;event_sha256:string}>;
type Removal=Meta&Readonly<{schema_version:'crop-removal-ledger-v1';claim_scope:'research_removal_math_only';
  rights_or_gate_approval:false;row_id:string;source:HarvestSource;start_at:string;end_at:string;
  carbohydrate:Quantity<'mg_CH2O/m2_floor'>;number:Quantity<'fruits_equivalent/m2_floor'>}>&(
  Readonly<{kind:'model_terminal_outflow';position:TerminalPosition;cohorts:null}>|
  Readonly<{kind:'explicit_fruit_removal';position:EventPosition;cohorts:Readonly<{
    fruit_carbohydrate:readonly Quantity<'mg_CH2O/m2_floor'>[];fruit_number:readonly Quantity<'fruits_equivalent/m2_floor'>[]}>}>);
type Mass=Meta&Readonly<{version:'crop-removal-mass-v1';removal_sha256:string;parameter_sha256:string;segment_id:string;
  schema_version:'crop-removal-mass-v1';row_id:string;claim_scope:'synthetic_removal_mass_math_only';rights_or_gate_approval:false;
  removal:Removal;parameters:MassParameters;dry_matter:Quantity<'kg_DM/m2_floor'>;fresh_matter:Quantity<'kg_FW/m2_floor'>;
  fresh_mass_per_equivalent:Readonly<{value:number|null;unit:'kg_FW/fruit_equivalent'}>}>;
type Fraction=Readonly<{value:string;unit:'1'}>;
type Declaration=Readonly<{version:'crop-harvest-allocation-v1';allocation_id:string;revision:string;origin:'synthetic';
  evidence_level:'assumed';evidence_id:string;available_at:string;source:HarvestSource;population:Population;
  mass_parameter_sha256:string;policy:'proportional_original_population'}>;
type Selector=Readonly<{kind:'model_terminal_outflow';first_sample:number;last_sample:number}>|
  Readonly<{kind:'explicit_fruit_removal';event:number}>;
type Rule=Readonly<{assignment_id:string;selector:Selector;purpose:Purpose;fraction:Fraction}>;
type Observation=Readonly<{observation_id:string;origin:'synthetic';evidence_level:'assumed';evidence_id:string;
  available_at:string;start_at:string;end_at:string;assignment_ids:readonly string[];fresh_matter:Quantity<'kg_FW/m2_floor'>}>;
type Parameters=Declaration&Readonly<{rules:readonly Rule[];observations:readonly Observation[]}>;
type Allocation=Readonly<{assignment_id:string;purpose:Purpose;fraction:Fraction;quantities:Quantities}>;
export type HarvestRow=Meta&Readonly<{version:'crop-harvest-allocation-result-v1';mass_row_sha256:string;
  allocation_sha256:string;schema_version:'crop-harvest-allocation-result-v1';row_id:string;claim_scope:typeof CLAIM;
  rights_or_gate_approval:false;mass:Mass;allocation_parameters:Declaration;allocations:readonly Allocation[];
  unassigned:Readonly<{fraction:HarvestQuantity<'1'>;quantities:Quantities}>;
  rounding:'nearest_float64_with_exact_rational_portions_of_stored_mass_row'}>;
type Total=Readonly<{rows:number;quantities:Quantities}>;
type Totals=Readonly<Record<Purpose|'unassigned',Total>>;
type Comparison=Readonly<{observation:Observation;status:'compared_synthetic_fixture'|'incomplete_selected_window';
  modeled_fresh_matter:HarvestQuantity<'kg_FW/m2_floor'>|null;observed_minus_modeled:HarvestQuantity<'kg_FW/m2_floor'>|null}>;
export type HarvestSummary=Readonly<{schema_version:'crop-harvest-allocation-summary-v1';code_sha256:string;
  claim_scope:typeof CLAIM;rights_or_gate_approval:false;source:HarvestSource;allocation_sha256:string;
  allocation_parameters:Parameters;row_count:number;row_chain_sha256:string;
  totals_by_kind_and_purpose:Readonly<Record<Kind,Totals>>;observation_comparisons:readonly Comparison[];
  rounding:'nearest_float64_with_exact_rational_sum_of_portions'}>;
export type HarvestReference=Readonly<{storage_status:'stored_unpublished_research';claim_scope:typeof CLAIM;
  scope:'software_research_only';gates:'not_assessed';temporal_provenance:'synthetic_research_program';rights_or_gate_approval:false;
  parent_result_id:string;source:HarvestSource;payload_sha256:string;artifact_sha256:string;row_count:number;
  row_chain_sha256:string;mass_parameter_sha256:string;allocation_parameter_sha256:string;publication_code_sha256:string;
  registry_schema_code_sha256:string;artifact_code_sha256:string;query_version:'crop-harvest-registered-current-query-v1';
  query_code_sha256:string;query_dependency_sha256:Readonly<{registry:string;artifact:string;crop_query:string}>;
  projection_code_sha256:string}>;
type Shared=Readonly<{schema_version:'crop-harvest-replay-v1';result_id:string;recorded_at:string;farm:CropFarm;reference:HarvestReference}>;
export type HarvestSummaryResponse=Shared&Readonly<{summary:HarvestSummary;page:null}>;
export type HarvestPageResponse=Shared&Readonly<{summary:null;page:Readonly<{offset:number;limit:number;
  total:number;next_offset:number|null;records:readonly HarvestRow[]}>}>;
export type HarvestReplayResponse=HarvestSummaryResponse|HarvestPageResponse;
export type HarvestLookup=CropFarm&Readonly<{result_id:string}>;
export type HarvestPageQuery=Readonly<{offset:number;limit:number}>;
type Request=(path:string,method?:string,body?:unknown,expected?:number,maxBytes?:number,
  timeoutMs?:number,signal?:AbortSignal)=>Promise<unknown>;
type LoadOptions=Readonly<{signal?:AbortSignal;summary?:HarvestSummaryResponse}>;
type IterateOptions=Readonly<{signal?:AbortSignal;limit?:number;onSummary?:(summary:HarvestSummaryResponse)=>void}>;
export type HarvestCompletion=Readonly<{kind:'records';count:number;total:number;complete:true}>;

function shape(v:unknown,keys:string){need(object(v));closed(v,keys.split(' '));return v;}
function list(v:unknown,max:number,min=0):unknown[]{need(Array.isArray(v)&&v.length>=min&&v.length<=max);return v;}
function integer(v:unknown,min=0,max=MAX_ROWS):v is number{return Number.isSafeInteger(v)&&typeof v==='number'&&v>=min&&v<=max;}
function digest(v:unknown):v is string{return typeof v==='string'&&/^[0-9a-f]{64}$/.test(v);}
function name(v:unknown):v is string{return typeof v==='string'&&/^[A-Za-z0-9][A-Za-z0-9_.:/-]{0,199}$/.test(v);}
function text(v:unknown,max=128):v is string{return typeof v==='string'&&v.length>0&&v.length<=max*2&&[...v].length<=max&&!/[\p{C}\p{Z}]/u.test(v.replaceAll(' ',''));}
function utc(v:unknown,whole=true):v is string{return date(v)&&v.endsWith('Z')&&(!whole||v.length===20);}
function id(v:unknown,version:string){return typeof v==='string'&&v.startsWith(version+':')&&digest(v.slice(version.length+1));}
function hashes(v:unknown,keys:string){const o=shape(v,keys);for(const k of keys.split(' '))need(digest(o[k]));}
function stable(v:unknown):string{if(Array.isArray(v))return '['+v.map(stable).join(',')+']';
  if(object(v))return '{'+Object.keys(v).sort().map(k=>JSON.stringify(k)+':'+stable(v[k])).join(',')+'}';return JSON.stringify(v);}
function same(a:unknown,b:unknown){need(stable(a)===stable(b));}
function gcd(a:bigint,b:bigint):bigint{a=a<0n?-a:a;while(b){const r=a%b;a=b;b=r;}return a;}
function pair(n:bigint,d:bigint):Pair{const g=gcd(n,d);return [n/g,d/g];}
function equal(a:Pair,b:Pair){need(a[0]*b[1]===b[0]*a[1]);}
function plus(a:Pair,b:Pair):Pair{return pair(a[0]*b[1]+b[0]*a[1],a[1]*b[1]);}
function floatPair(x:number):Pair{
  if(x===0)return [0n,1n];const view=new DataView(new ArrayBuffer(8));view.setFloat64(0,x);
  const bits=view.getBigUint64(0),exponent=Number((bits>>52n)&2047n),mantissa=(bits&((1n<<52n)-1n))|(exponent?1n<<52n:0n);
  const power=exponent?exponent-1075:-1074,n=(bits>>63n?-1n:1n)*mantissa;
  return power>=0?pair(n<<BigInt(power),1n):pair(n,1n<<BigInt(-power));
}
function rounded([n,d]:Pair):number{
  if(n===0n)return 0;const sign=n<0n?-1:1;n=n<0n?-n:n;
  let exponent=n.toString(2).length-d.toString(2).length;
  if(exponent>=0?n<(d<<BigInt(exponent)):(n<<BigInt(-exponent))<d)exponent--;
  if(exponent>1023)return sign*Infinity;if(exponent< -1075)return sign*0;
  const power=Math.max(exponent-52,-1074),a=power<0?n<<BigInt(-power):n,b=power>0?d<<BigInt(power):d;
  let q=a/b;const remainder=a%b;if(remainder*2n>b||(remainder*2n===b&&q%2n===1n))q++;
  return sign*Number(q)*2**power;
}
function amount(v:unknown,unit:string,signed=false):number{
  const q=shape(v,'value unit');need(q.unit===unit&&typeof q.value==='number'&&Number.isFinite(q.value)&&(signed||q.value>=0));return q.value;
}
function exactQuantity(v:unknown,unit:string,signed=false):Pair{
  const q=shape(v,'value unit exact');amount({value:q.value,unit:q.unit},unit,signed);
  const e=shape(q.exact,'numerator denominator');need(typeof e.numerator==='string'&&e.numerator.length<=2048&&/^(?:0|-?[1-9][0-9]*)$/.test(e.numerator)
    &&typeof e.denominator==='string'&&e.denominator.length<=2048&&/^[1-9][0-9]*$/.test(e.denominator));
  const n=BigInt(e.numerator),d=BigInt(e.denominator);need(gcd(n,d)===1n&&(signed||n>=0n)&&rounded([n,d])===q.value&&(n===0n||q.value!==0));return [n,d];
}
function quantities(v:unknown){const o=shape(v,'carbohydrate number dry_matter fresh_matter');
  return Object.fromEntries(Object.entries(UNITS).map(([k,u])=>[k,exactQuantity(o[k],u)])) as Record<keyof typeof UNITS,Pair>;}
function fraction(v:unknown):Pair{
  const o=shape(v,'value unit');need(o.unit==='1'&&typeof o.value==='string'&&/^(?:0(?:\.[0-9]{1,18})?|1(?:\.0{1,18})?)$/.test(o.value));
  const [whole,decimal='']=o.value.split('.'),n=BigInt(whole+decimal),d=10n**BigInt(decimal.length);need(n>0n&&n<=d);return [n,d];
}
function source(v:unknown){const o=shape(v,'result_id payload_sha256 input_root_sha256 artifact_sha256 math_manifest_sha256 source_status');
  need(id(o.result_id,'crop-cycle-verified-result-v1')&&member(o.source_status,['completed','hold'] as const));
  for(const k of ['payload_sha256','input_root_sha256','artifact_sha256','math_manifest_sha256'])need(digest(o[k]));}
function population(v:unknown){const o=shape(v,'population_id scope basis basis_evidence_id');
  need(text(o.population_id)&&text(o.basis_evidence_id)&&o.scope==='all_model_fruit_cohorts'&&o.basis==='m2_floor');}
function declaration(v:unknown,extra=''){
  const o=shape(v,'version allocation_id revision origin evidence_level evidence_id available_at source population mass_parameter_sha256 policy'+extra);
  need(o.version==='crop-harvest-allocation-v1'&&o.origin==='synthetic'&&o.evidence_level==='assumed'&&o.policy==='proportional_original_population'
    &&text(o.allocation_id)&&text(o.revision)&&text(o.evidence_id)&&utc(o.available_at)&&digest(o.mass_parameter_sha256));source(o.source);population(o.population);return o;
}
function observation(v:unknown){const o=shape(v,'observation_id origin evidence_level evidence_id available_at start_at end_at assignment_ids fresh_matter');
  need(text(o.observation_id)&&text(o.evidence_id)&&o.origin==='synthetic'&&o.evidence_level==='assumed'&&utc(o.available_at)
    &&utc(o.start_at)&&utc(o.end_at)&&o.start_at<=o.end_at);const ids=list(o.assignment_ids,256,1);need(ids.every(x=>text(x))&&new Set(ids).size===ids.length);
  amount(o.fresh_matter,UNITS.fresh_matter);return o;}
function parameters(v:unknown){const o=declaration(v,' rules observations'),rules=list(o.rules,256),observations=list(o.observations,64);
  const seen=new Map<string,string>(),edges=new Map<number,Pair>(),events=new Map<number,Pair>();
  for(const raw of rules){const r=shape(raw,'assignment_id selector purpose fraction');need(text(r.assignment_id)&&!seen.has(r.assignment_id)&&member(r.purpose,PURPOSES));seen.set(r.assignment_id,r.purpose);
    const weight=fraction(r.fraction);need(object(r.selector));const sel=r.selector;
    if(sel.kind==='model_terminal_outflow'){shape(sel,'kind first_sample last_sample');need(integer(sel.first_sample)&&integer(sel.last_sample)&&sel.first_sample<sel.last_sample);
      edges.set(sel.first_sample,plus(edges.get(sel.first_sample)??[0n,1n],weight));edges.set(sel.last_sample,plus(edges.get(sel.last_sample)??[0n,1n],[-weight[0],weight[1]]));}
    else{shape(sel,'kind event');need(sel.kind==='explicit_fruit_removal'&&integer(sel.event));const total=plus(events.get(sel.event)??[0n,1n],weight);need(total[0]<=total[1]);events.set(sel.event,total);}}
  let running:Pair=[0n,1n];for(const [,delta] of [...edges].sort(([a],[b])=>a-b)){running=plus(running,delta);need(running[0]>=0n&&running[0]<=running[1]);}equal(running,[0n,1n]);
  const obs=new Set(),linked=new Set();for(const raw of observations){const ob=observation(raw);need(!obs.has(ob.observation_id));obs.add(ob.observation_id);
    for(const assignment of ob.assignment_ids as unknown[]){need(typeof assignment==='string'&&seen.get(assignment)==='harvest'&&!linked.has(assignment));linked.add(assignment);}}
  return o;
}
function reference(v:unknown){const o=shape(v,'storage_status claim_scope scope gates temporal_provenance rights_or_gate_approval parent_result_id source payload_sha256 artifact_sha256 row_count row_chain_sha256 mass_parameter_sha256 allocation_parameter_sha256 publication_code_sha256 registry_schema_code_sha256 artifact_code_sha256 query_version query_code_sha256 query_dependency_sha256 projection_code_sha256');
  need(o.storage_status==='stored_unpublished_research'&&o.claim_scope===CLAIM&&o.scope==='software_research_only'&&o.gates==='not_assessed'
    &&o.temporal_provenance==='synthetic_research_program'&&o.rights_or_gate_approval===false&&id(o.parent_result_id,'crop-cycle-verified-result-v1')
    &&integer(o.row_count)&&o.query_version==='crop-harvest-registered-current-query-v1');source(o.source);
  need(object(o.source)&&o.parent_result_id===o.source.result_id);hashes(o.query_dependency_sha256,'registry artifact crop_query');
  for(const k of ['payload_sha256','artifact_sha256','row_chain_sha256','mass_parameter_sha256','allocation_parameter_sha256','publication_code_sha256',
    'registry_schema_code_sha256','artifact_code_sha256','query_code_sha256','projection_code_sha256'])need(digest(o[k]));
  need(object(o.query_dependency_sha256)&&o.query_dependency_sha256.registry===o.publication_code_sha256&&o.query_dependency_sha256.artifact===o.artifact_code_sha256);return o;
}
function claim(o:Record<string,unknown>,schema:string,scope:string){need(o.schema_version===schema&&o.claim_scope===scope&&o.rights_or_gate_approval===false&&digest(o.code_sha256));}
function row(v:unknown,ref:Record<string,unknown>){
  const o=shape(v,'version code_sha256 dependency_sha256 mass_row_sha256 allocation_sha256 schema_version row_id claim_scope rights_or_gate_approval mass allocation_parameters allocations unassigned rounding');
  claim(o,'crop-harvest-allocation-result-v1',CLAIM);need(o.version===o.schema_version&&id(o.row_id,o.schema_version as string)
    &&digest(o.mass_row_sha256)&&o.allocation_sha256===ref.allocation_parameter_sha256&&o.rounding==='nearest_float64_with_exact_rational_portions_of_stored_mass_row');hashes(o.dependency_sha256,'current_query canonical_json');
  const m=shape(o.mass,'version code_sha256 dependency_sha256 removal_sha256 parameter_sha256 segment_id schema_version row_id claim_scope rights_or_gate_approval removal parameters dry_matter fresh_matter fresh_mass_per_equivalent');
  claim(m,'crop-removal-mass-v1','synthetic_removal_mass_math_only');need(m.version===m.schema_version&&id(m.row_id,m.schema_version as string)&&digest(m.removal_sha256)&&m.parameter_sha256===ref.mass_parameter_sha256&&text(m.segment_id));
  const r=shape(m.removal,'schema_version code_sha256 dependency_sha256 claim_scope rights_or_gate_approval row_id source kind position start_at end_at carbohydrate number cohorts');
  claim(r,'crop-removal-ledger-v1','research_removal_math_only');need(id(r.row_id,r.schema_version as string)&&member(r.kind,KINDS)&&utc(r.start_at)&&utc(r.end_at));source(r.source);same(r.source,ref.source);
  hashes(m.dependency_sha256,'current_query canonical_json');hashes(r.dependency_sha256,'current_query canonical_json');
  need(m.code_sha256===o.code_sha256&&r.code_sha256===o.code_sha256);same(o.dependency_sha256,m.dependency_sha256);same(o.dependency_sha256,r.dependency_sha256);
  const carbon=amount(r.carbohydrate,UNITS.carbohydrate),number=amount(r.number,UNITS.number);
  if(r.kind==='model_terminal_outflow'){const p=shape(r.position,'samples sample_sha256'),indices=list(p.samples,2,2);list(p.sample_sha256,2,2).forEach(x=>need(digest(x)));
    need(integer(indices[0])&&integer(indices[1])&&indices[1]===indices[0]+1&&r.start_at<r.end_at&&r.cohorts===null);}
  else{const p=shape(r.position,'event input_id event_sha256');need(integer(p.event)&&typeof p.input_id==='string'&&p.input_id.length>0&&p.input_id.length<=MAX_BYTES&&digest(p.event_sha256)&&r.start_at===r.end_at);
    const cohorts=shape(r.cohorts,'fruit_carbohydrate fruit_number');for(const [k,u,total] of [['fruit_carbohydrate',UNITS.carbohydrate,carbon],['fruit_number',UNITS.number,number]] as const){
      let sum:Pair=[0n,1n];for(const q of list(cohorts[k],50,50))sum=plus(sum,floatPair(amount(q,u)));need(rounded(sum)===total);}}
  const p=shape(m.parameters,'version parameter_id revision origin evidence_level evidence_id available_at population policy sha256 segment rounding');
  need(p.version==='crop-removal-mass-parameters-v1'&&p.origin==='synthetic'&&p.evidence_level==='assumed'&&p.policy==='constant_per_original_interval'
    &&p.rounding==='nearest_float64_from_exact_input_floats_per_row'&&text(p.parameter_id)&&text(p.revision)&&text(p.evidence_id)&&utc(p.available_at)&&p.sha256===ref.mass_parameter_sha256);population(p.population);
  const seg=shape(p.segment,'segment_id start_at end_at eta dmc');need(text(seg.segment_id)&&seg.segment_id===m.segment_id&&utc(seg.start_at)&&utc(seg.end_at)
    &&seg.start_at<seg.end_at&&seg.start_at<=r.start_at&&r.end_at<=seg.end_at&&amount(seg.eta,'mg_DM/mg_CH2O')>0);const dmc=amount(seg.dmc,'kg_DM/kg_FW');need(dmc>0&&dmc<=1);
  const original={carbohydrate:carbon,number,dry_matter:amount(m.dry_matter,UNITS.dry_matter),fresh_matter:amount(m.fresh_matter,UNITS.fresh_matter)};
  const per=shape(m.fresh_mass_per_equivalent,'value unit');need(per.unit==='kg_FW/fruit_equivalent'&&((per.value===null)===(number===0)));
  if(per.value!==null)amount(per,'kg_FW/fruit_equivalent');
  const decl=declaration(o.allocation_parameters);same(decl.source,ref.source);need(decl.mass_parameter_sha256===ref.mass_parameter_sha256);same(decl.population,p.population);
  const parts=list(o.allocations,256),seen=new Set();let assigned:Pair=[0n,1n];
  const portion=(q:unknown,weight:Pair)=>{const all=quantities(q);for(const k of Object.keys(UNITS) as (keyof typeof UNITS)[]){const given=floatPair(original[k]);equal(all[k],[given[0]*weight[0],given[1]*weight[1]]);}};
  for(const raw of parts){const part=shape(raw,'assignment_id purpose fraction quantities');need(text(part.assignment_id)&&!seen.has(part.assignment_id)&&member(part.purpose,PURPOSES));seen.add(part.assignment_id);
    const weight=fraction(part.fraction);assigned=plus(assigned,weight);portion(part.quantities,weight);}
  const unassigned=shape(o.unassigned,'fraction quantities'),weight=exactQuantity(unassigned.fraction,'1');need(weight[0]<=weight[1]);equal(plus(assigned,weight),[1n,1n]);portion(unassigned.quantities,weight);
}
function summary(v:unknown,ref:Record<string,unknown>){const o=shape(v,'schema_version code_sha256 claim_scope rights_or_gate_approval source allocation_sha256 allocation_parameters row_count row_chain_sha256 totals_by_kind_and_purpose observation_comparisons rounding');
  claim(o,'crop-harvest-allocation-summary-v1',CLAIM);same(o.source,ref.source);need(o.allocation_sha256===ref.allocation_parameter_sha256&&o.row_count===ref.row_count&&o.row_chain_sha256===ref.row_chain_sha256&&o.rounding==='nearest_float64_with_exact_rational_sum_of_portions');
  const p=parameters(o.allocation_parameters);same(p.source,ref.source);need(p.mass_parameter_sha256===ref.mass_parameter_sha256);
  const totals=shape(o.totals_by_kind_and_purpose,KINDS.join(' '));for(const kind of KINDS){const by=shape(totals[kind],[...PURPOSES,'unassigned'].join(' '));
    for(const purpose of [...PURPOSES,'unassigned']){const total=shape(by[purpose],'rows quantities');need(integer(total.rows,0,Number(ref.row_count)*(purpose==='unassigned'?1:256)));const qs=quantities(total.quantities);if(total.rows===0)need(Object.values(qs).every(q=>q[0]===0n));}}
  const comparisons=list(o.observation_comparisons,64),observations=p.observations as unknown[];need(comparisons.length===observations.length);
  for(const [i,raw] of comparisons.entries()){const c=shape(raw,'observation status modeled_fresh_matter observed_minus_modeled');same(c.observation,observations[i]);observation(c.observation);
    need(member(c.status,['compared_synthetic_fixture','incomplete_selected_window'] as const));if(c.status==='incomplete_selected_window')need(c.modeled_fresh_matter===null&&c.observed_minus_modeled===null);
    else{const modeled=exactQuantity(c.modeled_fresh_matter,UNITS.fresh_matter),difference=exactQuantity(c.observed_minus_modeled,UNITS.fresh_matter,true);
      need(object(c.observation));const observed=floatPair(amount(c.observation.fresh_matter,UNITS.fresh_matter));equal(difference,plus(observed,[-modeled[0],modeled[1]]));}}
}
type RowCursor=Readonly<{end:string;kind:Kind;massIdentity:string;allocationIdentity:string}>;
function ordered(rows:readonly HarvestRow[],previous:RowCursor|null=null){
  for(const current of rows){
    const removal=current.mass.removal,{segment:_segment,...parameters}=current.mass.parameters;
    const cursor:RowCursor={end:removal.end_at,kind:removal.kind,
      massIdentity:stable({parameters,code:current.code_sha256,dependencies:current.dependency_sha256}),
      allocationIdentity:stable(current.allocation_parameters)};
    if(previous){
      need(cursor.massIdentity===previous.massIdentity&&cursor.allocationIdentity===previous.allocationIdentity);
      need(previous.end<cursor.end||(previous.end===cursor.end&&previous.kind==='model_terminal_outflow'&&cursor.kind==='explicit_fruit_removal'));
    }
    previous=cursor;
  }
  return previous;
}
export function validHarvestLookup(v:unknown):v is HarvestLookup{return object(v)&&Object.keys(v).length===5&&id(v.result_id,'crop-harvest-registered-result-v1')
  &&name(v.scenario_id)&&name(v.scenario_revision)&&digest(v.registration_sha256)&&name(v.crop_id);}
export function decodeHarvestReplayResponse(v:unknown,lookup:HarvestLookup):HarvestReplayResponse{
  need(validHarvestLookup(lookup));const o=shape(v,'schema_version result_id recorded_at farm reference summary page');
  need(o.schema_version==='crop-harvest-replay-v1'&&o.result_id===lookup.result_id&&utc(o.recorded_at,false));
  const farm=shape(o.farm,'scenario_id scenario_revision registration_sha256 crop_id');for(const k of Object.keys(farm))need(farm[k]===lookup[k as keyof CropFarm]);
  const ref=reference(o.reference);need((o.summary===null)!==(o.page===null));
  if(o.page===null)summary(o.summary,ref);
  else{const p=shape(o.page,'offset limit total next_offset records');need(integer(p.offset)&&integer(p.limit,1,64)&&p.total===ref.row_count&&integer(p.total));
    const rows=list(p.records,64),stop=p.offset+rows.length;need(stop<=p.total&&rows.length===Math.min(p.limit,p.total-p.offset)&&p.next_offset===(stop<p.total?stop:null));
    for(const value of rows)row(value,ref);ordered(rows as HarvestRow[]);}
  return o as HarvestReplayResponse;
}
function shared(v:HarvestReplayResponse){const {summary:_summary,page:_page,...identity}=v;return identity;}
function matched(s:HarvestSummaryResponse,p:HarvestPageResponse){same(shared(s),shared(p));
  const {rules,observations:_observations,...decl}=s.summary.allocation_parameters;
  for(const row of p.page.records){need(row.code_sha256===s.summary.code_sha256);same(row.allocation_parameters,decl);const r=row.mass.removal;
    const applies=rules.filter(rule=>rule.selector.kind==='model_terminal_outflow'?
      r.kind==='model_terminal_outflow'&&rule.selector.first_sample<=r.position.samples[0]&&r.position.samples[0]<rule.selector.last_sample:
      r.kind==='explicit_fruit_removal'&&rule.selector.event===r.position.event);
    same(row.allocations.map(({assignment_id,purpose,fraction})=>({assignment_id,purpose,fraction})),applies.map(({assignment_id,purpose,fraction})=>({assignment_id,purpose,fraction})));}}
function canceled(signal?:AbortSignal){if(signal?.aborted)throw new ApiError('request_canceled');}
export function createHarvestReplayApi(request:Request){let inFlight=false;
  async function read(lookup:HarvestLookup,view:'summary'|'records',signal?:AbortSignal,query?:HarvestPageQuery){
    need(validHarvestLookup(lookup));canceled(signal);need(!inFlight);const identity=stable(lookup),search=new URLSearchParams({...lookup});search.delete('result_id');search.set('view',view);
    if(query){search.set('offset',String(query.offset));search.set('limit',String(query.limit));}inFlight=true;
    try{const raw=await request('/v1/crop-harvest-research-results/'+encodeURIComponent(lookup.result_id)+'?'+search,'GET',undefined,200,MAX_BYTES,30_000,signal);
      canceled(signal);need(stable(lookup)===identity);return decodeHarvestReplayResponse(raw,lookup);}finally{inFlight=false;}}
  async function harvestSummary(lookup:HarvestLookup,signal?:AbortSignal):Promise<HarvestSummaryResponse>{const value=await read(lookup,'summary',signal);need(value.summary!==null);return value;}
  async function harvestPage(lookup:HarvestLookup,query:HarvestPageQuery,options:LoadOptions={}):Promise<HarvestPageResponse>{
    const q=shape(query,'offset limit');need(integer(q.offset)&&integer(q.limit,1,64)&&object(options)&&Object.keys(options).every(k=>k==='signal'||k==='summary'));
    const selected=options.summary,queryIdentity=stable(query),summaryIdentity=stable(selected);
    if(selected){need(decodeHarvestReplayResponse(selected,lookup).summary!==null&&query.offset<=selected.reference.row_count);}
    const value=await read(lookup,'records',options.signal,query);need(value.page!==null&&stable(query)===queryIdentity&&stable(selected)===summaryIdentity&&value.page.offset===query.offset&&value.page.limit===query.limit);
    if(selected)matched(selected,value);return value;
  }
  async function* harvestPages(lookup:HarvestLookup,options:IterateOptions={}):AsyncGenerator<HarvestPageResponse,HarvestCompletion|undefined,void>{
    need(validHarvestLookup(lookup)&&object(options)&&Object.keys(options).every(k=>k==='signal'||k==='limit'||k==='onSummary'));
    const limit=options.limit??64,signal=options.signal,identity=stable(lookup);need(integer(limit,1,64)&&(options.onSummary===undefined||typeof options.onSummary==='function'));
    const s=await harvestSummary(lookup,signal),summaryIdentity=stable(s),total=s.reference.row_count;options.onSummary?.(s);
    let offset=0,previous:RowCursor|null=null;for(;;){canceled(signal);need(stable(lookup)===identity&&stable(s)===summaryIdentity);
      const value=await harvestPage(lookup,{offset,limit},{signal,summary:s});previous=ordered(value.page.records,previous);
      const count=offset+value.page.records.length,next=value.page.next_offset;yield value;
      canceled(signal);need(stable(lookup)===identity&&stable(s)===summaryIdentity);if(next===null){need(count===total);return {kind:'records',count,total,complete:true};}offset=next;}}
  return {harvestSummary,harvestPage,harvestPages};
}
