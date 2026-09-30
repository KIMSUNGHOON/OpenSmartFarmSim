import type { AuthoredFarmRequest } from './authored-farm-api';

export type Row=Record<string,string>;
export type FarmDraft={fields:Row;forcing:Row[];crops:Row[];rightsConfirmed:boolean};

const IDENTIFIER=/^[A-Za-z0-9][A-Za-z0-9_.:/-]{0,199}$/;
const DIGEST=/^[0-9a-f]{64}$/;
const DECIMAL=/^-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?$/;
const DAY=/^\d{4}-\d{2}-\d{2}$/;
const UTC=/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$/;

export class FarmDraftError extends Error {
  constructor(public readonly field:string, message:string) {super(message);}
}

function required(row:Row,key:string,label:string,max=200):string {
  const value=(row[key] ?? '').trim();
  if(!value || value.length>max)throw new FarmDraftError(key,`${label}을(를) 입력해 주세요.`);
  return value;
}
function identifier(row:Row,key:string,label:string):string {
  const value=required(row,key,label);
  if(!IDENTIFIER.test(value))throw new FarmDraftError(key,`${label} 형식을 확인해 주세요.`);
  return value;
}
function digest(row:Row,key:string,label:string):string {
  const value=required(row,key,label,64);
  if(!DIGEST.test(value))throw new FarmDraftError(key,`${label}은 소문자 SHA-256 64자리여야 합니다.`);
  return value;
}
function decimal(row:Row,key:string,label:string):string {
  const value=required(row,key,label,64);
  if(!DECIMAL.test(value))throw new FarmDraftError(key,`${label}은(는) 단위에 맞는 십진 문자열이어야 합니다.`);
  return value;
}
function day(row:Row,key:string,label:string):string {
  const value=required(row,key,label,10);
  const parsed=Date.parse(value+'T00:00:00Z');
  if(!DAY.test(value) || Number.isNaN(parsed) ||
      new Date(parsed).toISOString().slice(0,10)!==value)
    throw new FarmDraftError(key,`${label}은 YYYY-MM-DD 형식이어야 합니다.`);
  return value;
}
function utc(row:Row,key:string,label:string):string {
  const value=required(row,key,label,20);
  const parsed=Date.parse(value);
  if(!UTC.test(value) || Number.isNaN(parsed) ||
      new Date(parsed).toISOString().slice(0,19)+'Z'!==value)
    throw new FarmDraftError(key,`${label}은 YYYY-MM-DDTHH:mm:ssZ 형식이어야 합니다.`);
  return value;
}
function choice(row:Row,key:string,label:string,choices:readonly string[]):string {
  const value=required(row,key,label);
  if(!choices.includes(value))throw new FarmDraftError(key,`${label}을(를) 다시 선택해 주세요.`);
  return value;
}

export function buildFarmAuthoringRequest(draft:FarmDraft):AuthoredFarmRequest {
  const f=draft.fields;
  if(!draft.rightsConfirmed)throw new FarmDraftError('rights','본인이 작성한 가정의 권리와 사용 범위를 확인해 주세요.');
  const scenario_id=identifier(f,'scenario_id','농장 시나리오 ID');
  const scenario_revision=identifier(f,'scenario_revision','농장 판본');
  const record_revision=identifier(f,'record_revision','가정 기록 판본');
  const source_ref=identifier(f,'source_ref','사용자 가정 출처 참조');
  const available_at=utc(f,'available_at','가정을 알 수 있던 시각');
  const evidence=(input_id:string)=>({input_id,revision:record_revision,source_ref,
    origin:'user' as const,evidence_level:'assumed' as const,available_at});
  const quantity=(row:Row,key:string,label:string,unit:string,id=key)=>({
    ...evidence(id),value:decimal(row,key,label),unit});
  const window=(row:Row,prefix:string,label:string)=>({
    start:utc(row,prefix+'_start',label+' 시작'),end:utc(row,prefix+'_end',label+' 종료')});
  const fixed=<T extends string>(key:string,label:string,choices:readonly T[]):T=>
    choice(f,key,label,choices) as T;
  const capexMode=fixed('capex_mode','설비 투자 한도 상태',['known','unknown'] as const);
  const cashMode=fixed('cash_mode','최소 현금 상태',['known','unknown'] as const);
  if(!draft.forcing.length || draft.forcing.length>32)
    throw new FarmDraftError('forcing','원본 기상 구간마다 강제 조건 한 줄이 필요합니다(최대 32개).');
  if(draft.crops.length>32)throw new FarmDraftError('crops','작물 의도는 최대 32개입니다.');
  const crops=draft.crops.map((row,index)=>{
    const n=index+1;
    const list=(key:string,label:string)=>{
      const values=required(row,key,label,2000).split(',').map(value=>value.trim());
      if(values.length>32 || values.some(value=>!IDENTIFIER.test(value)) ||
          new Set(values).size!==values.length)
        throw new FarmDraftError(`crop-${n}-${key}`,`${label}을 쉼표로 구분하고 중복 없이 입력해 주세요.`);
      return values;
    };
    return {crop_id:identifier(row,'crop_id',`${n}번 작물 ID`),
      batch_id:identifier(row,'batch_id',`${n}번 배치 ID`),
      species:required(row,'species',`${n}번 작물명`),variety:required(row,'variety',`${n}번 품종명`),
      profile_status:'unavailable' as const,provenance:evidence(`crop-${n}-intent`),
      area:quantity(row,'area',`${n}번 점유 면적`,'m²',`crop-${n}-area`),
      occupancy:window(row,'occupancy',`${n}번 점유 기간`),
      release_at:utc(row,'release_at',`${n}번 정리 완료 시각`),
      harvest_window:window(row,'harvest',`${n}번 수확 예상 기간`),
      sales_window:window(row,'sales',`${n}번 판매 예상 기간`),
      collection_window:window(row,'collection',`${n}번 수금 예상 기간`),
      grades:list('grades',`${n}번 등급`),channels:list('channels',`${n}번 판매 경로`)};
  });
  const request={schema_version:'farm-authoring-request-v1' as const,
    farm:{schema_version:'farm-inputs-v1',scenario_id,scenario_revision,
      research_job_id:required(f,'research_job_id','조사 작업 ID',36),
      snapshot_id:required(f,'snapshot_id','원본 열 스냅샷 ID',84),
      decision_context_id:identifier(f,'decision_context_id','결정 문맥 ID'),
      decision_at:utc(f,'decision_at','결정 시각'),
      market_context:{kind:'unavailable',hold_report_id:identifier(f,'market_hold_report_id','시장 보류 ID')},
      goal_id:'historical-thermal-replay',period_start:day(f,'period_start','평가 시작일'),
      period_end:day(f,'period_end','평가 종료일'),
      economic:{scenario_id:identifier(f,'economic_scenario_id','경제 시나리오 ID'),
        revision:identifier(f,'economic_revision','경제 판본'),
        sha256:digest(f,'economic_sha256','경제 입력 해시'),
        candidate_id:digest(f,'economic_candidate_id','경제 후보 ID')},
      facility:{zone_id:identifier(f,'zone_id','구역 ID'),facility_type:'single_zone_greenhouse',
        tenure:fixed('tenure','시설 소유 상태',['owned','leased','unknown'] as const),
        decision_basis:fixed('decision_basis','결정 유형',
          ['new_facility','existing_facility_crop_change'] as const),
        provenance:evidence('facility-intent'),
        floor_area:quantity(f,'floor_area','바닥 면적','m²'),
        cultivable_area:quantity(f,'cultivable_area','재배 가능 면적','m²'),
        indoor_volume:quantity(f,'indoor_volume','실내 부피','m³'),
        effective_heat_capacity:quantity(f,'effective_heat_capacity','유효 열용량','J/K'),
        dry_air_mass:quantity(f,'dry_air_mass','건조 공기 질량','kg_da'),
        envelope_conductance:quantity(f,'envelope_conductance','외피 열관류','W/K'),
        absorbed_solar_fraction:quantity(f,'absorbed_solar_fraction','흡수 일사 비율','1')},
      initial_state:{temperature:quantity(f,'initial_temperature','초기 온도','K'),
        humidity_ratio:quantity(f,'initial_humidity_ratio','초기 절대습도','kg_v/kg_da')},
      heater:{mode:'indirect_sensible',capacity_basis:'delivered_thermal_power',
        control_version:'thermal-indirect-sensible-end-target-v1',
        capacity:quantity(f,'heater_capacity','난방 공급열 용량','W_th'),
        setpoint:quantity(f,'heater_setpoint','난방 설정온도','K'),
        available:{...evidence('heater-available'),
          value:fixed('heater_available','난방 사용 가능 여부',['yes','no'] as const)==='yes'},
        efficiency_status:'unavailable',metering_status:'unavailable'},
      forcing:draft.forcing.map((row,index)=>({
        start:utc(row,'start',`${index+1}번 구간 시작`),
        end:utc(row,'end',`${index+1}번 구간 종료`),
        ventilation_dry_air_flow:quantity(row,'ventilation',`${index+1}번 환기 유량`,
          'kg_da/s',`forcing-${index+1}-ventilation`),
        canopy_evaporation:quantity(row,'canopy',`${index+1}번 증발량`,
          'kg_v/s',`forcing-${index+1}-canopy`),
        ground_heat_flow:quantity(row,'ground',`${index+1}번 지중 열류`,
          'W',`forcing-${index+1}-ground`)})),
      crops,objective:fixed('objective','조건부 평가 목표',
        ['conditional_operating_profit','conditional_operating_margin','minimum_cash'] as const),
      constraints:{capex_ceiling:capexMode==='unknown' ? null :
        quantity(f,'capex_ceiling','설비 투자 한도','KRW'),
        minimum_cash:cashMode==='unknown' ? null :
        quantity(f,'minimum_cash','최소 현금','KRW')}},
    rights:{schema_version:'farm-assumption-rights-v1',scenario_id,scenario_revision,
      declaration_id:identifier(f,'declaration_id','권리 선언 ID'),
      revision:identifier(f,'rights_revision','권리 선언 판본'),
      origin:'user',evidence_level:'assumed',ownership_asserted:true,
      access:true,store:true,transform:true,use:true,display:true,redistribute:false,
      available_at,scope_start:day(f,'period_start','평가 시작일'),
      scope_end:day(f,'period_end','평가 종료일')}};
  if(new TextEncoder().encode(JSON.stringify(request)).length>65_536)
    throw new FarmDraftError('size','입력 전체가 64 KiB 제한을 넘었습니다.');
  return request;
}
