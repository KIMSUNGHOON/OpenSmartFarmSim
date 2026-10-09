import { describe,expect,it } from 'vitest';
import { buildFarmAuthoringRequest,FarmDraftError,type FarmDraft } from './farm-authoring-input';

const a='a'.repeat(64);
function draft():FarmDraft {
  return {rightsConfirmed:true,fields:{
    scenario_id:'farm-1',scenario_revision:'r1',research_job_id:'00000000-0000-4000-8000-000000000001',
    snapshot_id:'thermal-snapshot-v1:'+a,decision_context_id:'context-1',
    decision_at:'2026-09-28T00:00:00Z',market_hold_report_id:'hold-1',
    period_start:'2026-10-01',period_end:'2026-11-30',economic_scenario_id:'economic-1',
    economic_revision:'r1',economic_sha256:a,economic_candidate_id:a,
    source_ref:'self-authored-input',record_revision:'r1',available_at:'2026-09-28T00:00:00Z',
    zone_id:'zone-1',tenure:'unknown',decision_basis:'existing_facility_crop_change',
    floor_area:'100',cultivable_area:'80',indoor_volume:'400',
    effective_heat_capacity:'1000000',dry_air_mass:'400',
    envelope_conductance:'200',absorbed_solar_fraction:'0.5',
    initial_temperature:'293',initial_humidity_ratio:'0.008',
    heater_capacity:'500',heater_setpoint:'293',heater_available:'yes',
    objective:'conditional_operating_margin',capex_mode:'known',capex_ceiling:'1000',
    cash_mode:'unknown',declaration_id:'rights-farm-1',rights_revision:'r1'},
    forcing:[{start:'2026-10-01T00:00:00Z',end:'2026-10-01T00:01:00Z',
      ventilation:'0.02',canopy:'0.0001',ground:'-20'}],
    crops:[{crop_id:'crop-1',batch_id:'batch-1',species:'user-crop-intent',
      variety:'unspecified',area:'80',occupancy_start:'2026-10-01T00:00:00Z',
      occupancy_end:'2026-10-25T00:00:00Z',release_at:'2026-10-26T00:00:00Z',
      harvest_start:'2026-10-14T00:00:00Z',harvest_end:'2026-10-16T00:00:00Z',
      sales_start:'2026-10-15T00:00:00Z',sales_end:'2026-10-18T00:00:00Z',
      collection_start:'2026-10-15T00:00:00Z',collection_end:'2026-10-24T00:00:00Z',
      grades:'grade-1,grade-2',channels:'direct'}]};
}

describe('authored farm request builder',()=>{
  it('keeps every explicit numeric value and units while binding one user rights declaration',()=>{
    const request=buildFarmAuthoringRequest(draft());
    const farm=request.farm as Record<string,any>;
    const rights=request.rights as Record<string,any>;
    expect(farm.facility.floor_area).toMatchObject({value:'100',unit:'m²',origin:'user',
      evidence_level:'assumed',available_at:'2026-09-28T00:00:00Z'});
    expect(farm.initial_state.humidity_ratio.value).toBe('0.008');
    expect(farm.heater.efficiency_status).toBe('unavailable');
    expect(farm.forcing[0].ground_heat_flow).toMatchObject({value:'-20',unit:'W'});
    expect(farm.crops[0].profile_status).toBe('unavailable');
    expect(farm.crops[0].grades).toEqual(['grade-1','grade-2']);
    expect(farm.constraints).toMatchObject({capex_ceiling:{value:'1000',unit:'KRW'},
      minimum_cash:null});
    expect(farm.market_context).toEqual({kind:'unavailable',hold_report_id:'hold-1'});
    expect(rights).toMatchObject({scenario_id:'farm-1',scenario_revision:'r1',
      ownership_asserted:true,access:true,store:true,transform:true,use:true,display:true,
      redistribute:false,scope_start:'2026-10-01',scope_end:'2026-11-30'});
  });

  it('requires explicit values and rights instead of manufacturing assumptions',()=>{
    const missing=draft();delete missing.fields.effective_heat_capacity;
    expect(()=>buildFarmAuthoringRequest(missing)).toThrow(FarmDraftError);
    const noRights=draft();noRights.rightsConfirmed=false;
    expect(()=>buildFarmAuthoringRequest(noRights)).toThrow('권리');
    const badMoney=draft();badMoney.fields.capex_ceiling='1e6';
    expect(()=>buildFarmAuthoringRequest(badMoney)).toThrow('십진 문자열');
    const badSource=draft();badSource.fields.available_at='';
    expect(()=>buildFarmAuthoringRequest(badSource)).toThrow('시각');
    const invalidDay=draft();invalidDay.fields.period_start='2026-02-30';
    expect(()=>buildFarmAuthoringRequest(invalidDay)).toThrow('YYYY-MM-DD');
    const invalidUtc=draft();invalidUtc.fields.decision_at='2026-02-30T00:00:00Z';
    expect(()=>buildFarmAuthoringRequest(invalidUtc)).toThrow('YYYY-MM-DDTHH:mm:ssZ');
  });

  it('preserves exact server decision and user input microseconds in the submitted bytes',()=>{
    const precise=draft();precise.fields.decision_at='2026-09-28T00:00:00.123456Z';
    precise.fields.available_at='2026-09-28T00:00:00.123455Z';
    precise.forcing[0]!.start='2026-10-01T00:00:00.000001Z';
    const request=buildFarmAuthoringRequest(precise);
    expect(request.farm.decision_at).toBe(precise.fields.decision_at);
    expect((request.farm.facility as any).floor_area.available_at).toBe(precise.fields.available_at);
    expect((request.farm.forcing as any[])[0].start).toBe(precise.forcing[0]!.start);
    precise.fields.decision_at='2026-09-28T00:00:00.1234567Z';
    expect(()=>buildFarmAuthoringRequest(precise)).toThrow(FarmDraftError);
  });
});
