import {ApiError,closed,date,member,need,object} from './api-validation';
import type {CropFarm} from './cropReplay';

export const CROP_CATALOG_VERSION='crop-research-result-catalog-v1';
export const CROP_CATALOG_MAX_BYTES=65_536;
export type CropCatalogKind='calculation_cycle_v1'|'harvest_v1';
export type CropCatalogCursor=Readonly<{recorded_at:string;result_id:string}>;
export type CropCatalogQuery=Readonly<{kind:CropCatalogKind;farm:Readonly<CropFarm>;
  limit?:number;before?:CropCatalogCursor|null}>;
type ResolvedQuery=Readonly<{kind:CropCatalogKind;farm:Readonly<CropFarm>;limit:number;before:CropCatalogCursor|null}>;
type Status='completed'|'hold';
export type GrowthCatalogItem=Readonly<{result_id:string;recorded_at:string;calculation_status:Status;
  claim_scope:'synthetic_crop_math_only';study_id:string;revision:string;
  period:Readonly<{start:string;end:string}>;sample_count:number;event_count:number}>;
export type HarvestCatalogItem=Readonly<{result_id:string;recorded_at:string;calculation_status:Status;
  claim_scope:'synthetic_harvest_allocation_math_only';parent_result_id:string;row_count:number}>;
type Base=Readonly<{version:typeof CROP_CATALOG_VERSION;scope:'stored_research_metadata_only';
  farm:Readonly<CropFarm>;next_cursor:CropCatalogCursor|null;
  selection_validation_required:true;rights_or_gate_approval:false}>;
export type GrowthCatalogPage=Base&Readonly<{kind:'calculation_cycle_v1';items:readonly GrowthCatalogItem[]}>;
export type HarvestCatalogPage=Base&Readonly<{kind:'harvest_v1';items:readonly HarvestCatalogItem[]}>;
export type CropCatalogPage=GrowthCatalogPage|HarvestCatalogPage;
type Request=(path:string,method?:string,body?:unknown,expected?:number,maxBytes?:number,
  timeoutMs?:number,signal?:AbortSignal)=>Promise<unknown>;

function shape(value:unknown,keys:string){need(object(value));closed(value,keys.split(' '));return value;}
function name(value:unknown):value is string{return typeof value==='string'&&/^[A-Za-z0-9][A-Za-z0-9_.:/-]{0,199}$/.test(value);}
function digest(value:unknown):value is string{return typeof value==='string'&&/^[0-9a-f]{64}$/.test(value);}
function integer(value:unknown,max:number):value is number{return typeof value==='number'&&Number.isSafeInteger(value)&&value>=0&&value<=max;}
function utc(value:unknown):value is string{return date(value)&&value.endsWith('Z');}
function stamp(value:unknown):value is string{return utc(value)&&/^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d{6}Z$/.test(value);}
function instant(value:string){return value.slice(0,19)+'.'+(value[19]==='.'?value.slice(20,-1):'').padEnd(6,'0')+'Z';}
function resultID(value:unknown,kind:CropCatalogKind):value is string{
  const prefix=kind==='calculation_cycle_v1'?'crop-cycle-verified-result-v1:':'crop-harvest-registered-result-v1:';
  return typeof value==='string'&&value.startsWith(prefix)&&digest(value.slice(prefix.length));
}
function farm(value:unknown):CropFarm{
  const v=shape(value,'scenario_id scenario_revision registration_sha256 crop_id');
  need(name(v.scenario_id)&&name(v.scenario_revision)&&digest(v.registration_sha256)&&name(v.crop_id));
  return {scenario_id:v.scenario_id,scenario_revision:v.scenario_revision,
    registration_sha256:v.registration_sha256,crop_id:v.crop_id};
}
function cursor(value:unknown,kind:CropCatalogKind):CropCatalogCursor{
  const v=shape(value,'recorded_at result_id');need(stamp(v.recorded_at)&&resultID(v.result_id,kind));
  return {recorded_at:v.recorded_at,result_id:v.result_id};
}
function query(value:unknown):ResolvedQuery{
  need(object(value)&&Object.keys(value).every(k=>['kind','farm','limit','before'].includes(k)));
  need(member(value.kind,['calculation_cycle_v1','harvest_v1'] as const));
  const limit=Object.hasOwn(value,'limit')?value.limit:10;need(integer(limit,20)&&limit>=1);
  const before=Object.hasOwn(value,'before')&&value.before!==null?cursor(value.before,value.kind):null;
  return {kind:value.kind,farm:farm(value.farm),limit,before};
}
function growth(value:unknown):GrowthCatalogItem{
  const v=shape(value,'result_id recorded_at calculation_status claim_scope study_id revision period sample_count event_count');
  need(resultID(v.result_id,'calculation_cycle_v1')&&stamp(v.recorded_at)&&
    member(v.calculation_status,['completed','hold'] as const)&&v.claim_scope==='synthetic_crop_math_only'&&
    name(v.study_id)&&name(v.revision)&&integer(v.sample_count,131072)&&integer(v.event_count,131072));
  const p=shape(v.period,'start end');need(utc(p.start)&&utc(p.end)&&instant(p.start)<instant(p.end));
  return {result_id:v.result_id,recorded_at:v.recorded_at,calculation_status:v.calculation_status,
    claim_scope:v.claim_scope,study_id:v.study_id,revision:v.revision,period:{start:p.start,end:p.end},
    sample_count:v.sample_count,event_count:v.event_count};
}
function harvest(value:unknown):HarvestCatalogItem{
  const v=shape(value,'result_id recorded_at calculation_status claim_scope parent_result_id row_count');
  need(resultID(v.result_id,'harvest_v1')&&stamp(v.recorded_at)&&member(v.calculation_status,['completed','hold'] as const)&&
    v.claim_scope==='synthetic_harvest_allocation_math_only'&&resultID(v.parent_result_id,'calculation_cycle_v1')&&integer(v.row_count,262144));
  return {result_id:v.result_id,recorded_at:v.recorded_at,calculation_status:v.calculation_status,
    claim_scope:v.claim_scope,parent_result_id:v.parent_result_id,row_count:v.row_count};
}
function earlier(a:CropCatalogCursor,b:CropCatalogCursor){
  return a.recorded_at<b.recorded_at||(a.recorded_at===b.recorded_at&&a.result_id<b.result_id);
}
function page<T extends CropCatalogCursor>(items:T[],next:unknown,requested:ResolvedQuery){
  need(items.length<=requested.limit&&new Set(items.map(item=>item.result_id)).size===items.length);
  for(let i=0;i<items.length;i++){
    const item=items[i]!;need((i===0||earlier(item,items[i-1]!))&&(!requested.before||earlier(item,requested.before)));
  }
  const next_cursor=next===null?null:cursor(next,requested.kind);
  if(next_cursor){
    const last=items.at(-1);need(items.length===requested.limit&&last&&last.result_id===next_cursor.result_id&&last.recorded_at===next_cursor.recorded_at);
  }
  return {items,next_cursor};
}

export function decodeCropCatalogPage(value:unknown,requested:CropCatalogQuery):CropCatalogPage{
  const expected=query(requested),v=shape(value,'version scope kind farm items next_cursor selection_validation_required rights_or_gate_approval');
  need(v.version===CROP_CATALOG_VERSION&&v.scope==='stored_research_metadata_only'&&v.kind===expected.kind&&
    v.selection_validation_required===true&&v.rights_or_gate_approval===false);
  const selected=farm(v.farm);need(JSON.stringify(selected)===JSON.stringify(expected.farm));
  need(Array.isArray(v.items)&&v.items.length<=20);
  const base:Omit<Base,'next_cursor'>={version:CROP_CATALOG_VERSION,scope:'stored_research_metadata_only',
    farm:selected,selection_validation_required:true as const,rights_or_gate_approval:false as const};
  return expected.kind==='calculation_cycle_v1'?
    {...base,kind:expected.kind,...page(v.items.map(growth),v.next_cursor,expected)}:
    {...base,kind:expected.kind,...page(v.items.map(harvest),v.next_cursor,expected)};
}

function canceled(signal?:AbortSignal){if(signal?.aborted)throw new ApiError('request_canceled');}
export function createCropResultCatalogApi(request:Request){
  return {async cropResultCatalog(selection:CropCatalogQuery,signal?:AbortSignal):Promise<CropCatalogPage>{
    canceled(signal);const expected=query(selection),identity=JSON.stringify(expected);
    const search=new URLSearchParams({kind:expected.kind,...expected.farm,limit:String(expected.limit)});
    if(expected.before){search.set('before_recorded_at',expected.before.recorded_at);search.set('before_result_id',expected.before.result_id);}
    const raw=await request('/v1/crop-research-result-catalog?'+search,'GET',undefined,200,CROP_CATALOG_MAX_BYTES,30_000,signal);
    canceled(signal);need(JSON.stringify(query(selection))===identity);
    return decodeCropCatalogPage(raw,expected);
  }};
}
