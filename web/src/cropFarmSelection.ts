import {ApiError,closed,date,need,object} from './api-validation';

export const CROP_FARM_SELECTION_VERSION='crop-research-farm-selection-v1';
export type CropFarmRegistration=Readonly<{scenario_id:string;scenario_revision:string;registration_sha256:string}>;
export type RegisteredCropSelection=Readonly<{crop_id:string;batch_id:string;species:string;variety:string;
  occupancy:Readonly<{start:string;end:string}>;profile_status:'unavailable';origin:'user';evidence_level:'assumed'}>;
export type CropFarmSelection=Readonly<{version:typeof CROP_FARM_SELECTION_VERSION;
  scope:'registered_user_inputs_only';farm:CropFarmRegistration;items:readonly RegisteredCropSelection[];
  selection_validation_required:true;rights_or_gate_approval:false}>;
type Request=(path:string,method?:string,body?:unknown,expected?:number,maxBytes?:number,
  timeoutMs?:number,signal?:AbortSignal)=>Promise<unknown>;
const EDGE_SPACE=/[\u0020\u0085\u00a0\u1680\u2000-\u200a\u2028\u2029\u202f\u205f\u3000]/u;
function shape(value:unknown,keys:string){need(object(value));closed(value,keys.split(' '));return value;}
function name(value:unknown):value is string{return typeof value==='string'&&/^[A-Za-z0-9][A-Za-z0-9_.:/-]{0,199}$/.test(value);}
function label(value:unknown):value is string{
  if(typeof value!=='string'||/[\x00-\x1f]/u.test(value))return false;
  const chars=Array.from(value);
  return chars.length>=1&&chars.length<=200&&!EDGE_SPACE.test(chars[0]!)&&!EDGE_SPACE.test(chars.at(-1)!)
    &&chars.every(char=>{const code=char.codePointAt(0)!;return code<0xd800||code>0xdfff;});
}
function stamp(value:unknown):value is string{
  return date(value)&&/^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d{6}Z$/.test(value);
}
function registration(value:unknown):CropFarmRegistration{
  const v=shape(value,'scenario_id scenario_revision registration_sha256');
  need(name(v.scenario_id)&&name(v.scenario_revision)&&typeof v.registration_sha256==='string'&&/^[0-9a-f]{64}$/.test(v.registration_sha256));
  return {scenario_id:v.scenario_id,scenario_revision:v.scenario_revision,registration_sha256:v.registration_sha256};
}
function crop(value:unknown):RegisteredCropSelection{
  const v=shape(value,'crop_id batch_id species variety occupancy profile_status origin evidence_level');
  need(name(v.crop_id)&&name(v.batch_id)&&label(v.species)&&label(v.variety)&&v.profile_status==='unavailable'
    &&v.origin==='user'&&v.evidence_level==='assumed');
  const p=shape(v.occupancy,'start end');need(stamp(p.start)&&stamp(p.end)&&p.start<p.end);
  return {crop_id:v.crop_id,batch_id:v.batch_id,species:v.species,variety:v.variety,occupancy:{start:p.start,end:p.end},
    profile_status:'unavailable',origin:'user',evidence_level:'assumed'};
}
export function decodeCropFarmSelection(value:unknown,requested:CropFarmRegistration):CropFarmSelection{
  const expected=registration(requested),v=shape(value,'version scope farm items selection_validation_required rights_or_gate_approval');
  need(v.version===CROP_FARM_SELECTION_VERSION&&v.scope==='registered_user_inputs_only'
    &&v.selection_validation_required===true&&v.rights_or_gate_approval===false);
  const farm=registration(v.farm);need(JSON.stringify(farm)===JSON.stringify(expected));
  need(Array.isArray(v.items)&&v.items.length<=32);const items=v.items.map(crop);
  need(items.every((item,i)=>i===0||items[i-1]!.crop_id<item.crop_id));
  return {version:CROP_FARM_SELECTION_VERSION,scope:'registered_user_inputs_only',farm,items,
    selection_validation_required:true,rights_or_gate_approval:false};
}
function canceled(signal?:AbortSignal){if(signal?.aborted)throw new ApiError('request_canceled');}
export function createCropFarmSelectionApi(request:Request){
  return {async cropFarmSelection(farm:CropFarmRegistration,signal?:AbortSignal):Promise<CropFarmSelection>{
    canceled(signal);const expected=registration(farm),identity=JSON.stringify(expected);
    const raw=await request('/v1/crop-research-result-catalog/farm-crops?'+new URLSearchParams(expected),
      'GET',undefined,200,65_536,30_000,signal);
    canceled(signal);need(JSON.stringify(registration(farm))===identity);
    return decodeCropFarmSelection(raw,expected);
  }};
}
