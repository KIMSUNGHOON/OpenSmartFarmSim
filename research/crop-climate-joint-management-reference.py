"""Decimal80 removal and bounded composition oracle; no product imports."""
from copy import deepcopy
from decimal import Decimal,localcontext
from hashlib import sha256
import json
from pathlib import Path
import runpy

ROOT=Path(__file__).resolve().parents[1]
D=Decimal
INPUTS={
    'research/crop-climate-joint-integration-reference.py':'1a0fc4170c12d90f72e6311f7273f28e7c8a734980f83bff2986a281f8191a21',
    'contracts/crop-plant-cohort-integration-v1.md':'4eba6541571d1cc42b5e77c7f0c5ce3fd7a1c8f7a7c94d718752dcccb3135e6e',
    'contracts/crop-canopy-energy-transport-v1.md':'9a52267bb5cf921748f875bbe53d43da6927ab53922309972af7979c2a6bad11'}
EVENT_FIELDS=('leaf','stem_root','fruit_carbohydrate','fruit_number','canopy_sensible_energy','canopy_capacity')


def environment():
    for name,digest in INPUTS.items():assert sha256((ROOT/name).read_bytes()).hexdigest()==digest,name
    prior=runpy.run_path(str(ROOT/'research/crop-climate-joint-integration-reference.py'))
    return prior,prior['environment']()


def derived(s,y,env):
    parameters=env['prior']['values'](s['parameters']);lai=env['p']['sla']*y[1];cap=parameters['leaf_heat_capacity']*lai
    return {'canopy_temperature':str(parameters['reference_temperature']+y[105]/cap),
        'leaf_area_index':str(lai),'canopy_capacity':str(cap)}


def removal(s,event,prior,env):
    y=prior['initial'](s);v=event['values'];leaf,stem=(D(str(v[k]['value'])) for k in ('leaf','stem_root'))
    fractions=[D(str(q['value'])) for q in v['fruit_fraction']]
    assert 0<=leaf<y[1] and 0<=stem<=y[2] and len(fractions)==50 and all(0<=f<=1 for f in fractions)
    params=env['prior']['values'](s['parameters']);sla=env['p']['sla'];cap=params['leaf_heat_capacity']
    capacity_removed=cap*sla*leaf;tc=params['reference_temperature']+y[105]/(cap*sla*y[1])
    energy_removed=capacity_removed*(tc-params['reference_temperature'])
    c_removed=[a*f for a,f in zip(y[5:55],fractions,strict=True)]
    n_removed=[a*f for a,f in zip(y[55:105],fractions,strict=True)]
    # Independent retention path and removed-capacity energy, rather than U*capacity ratio.
    after=(*y[:1],y[1]-leaf,y[2]-stem,*y[3:5],
        *(a*(1-f) for a,f in zip(y[5:55],fractions,strict=True)),
        *(a*(1-f) for a,f in zip(y[55:105],fractions,strict=True)),y[105]-energy_removed,*y[106:])
    candidate=prior['trial'](s,after)
    expected={'state':list(map(str,after)),'removed':{'leaf':str(leaf),'stem_root':str(stem),
        'fruit_carbohydrate':list(map(str,c_removed)),'fruit_number':list(map(str,n_removed)),
        'canopy_sensible_energy':str(energy_removed),'canopy_capacity':str(capacity_removed)},
        'totals':{'carbohydrate':str(leaf+stem+sum(c_removed)),'number':str(sum(n_removed))},
        'derived':derived(s,after,env)}
    assert abs(D(expected['derived']['canopy_temperature'])-tc)<D('1e-65')
    return candidate,expected


def compose(s,event,at,dt,prior,env):
    current=deepcopy(s);transfers={k:D(0) for k in prior['FLOW']};event_totals={k:D(0) for k in EVENT_FIELDS}
    initial=prior['initial'](s);previous=0;count=int(D(32)/dt);event_index=int(D(at)/dt)
    assert count*dt==32 and event_index*dt==at
    for boundary in sorted({event_index,count}):
        if boundary>previous:
            part=prior['trajectory'](current,dt,boundary-previous,env)
            for k,v in part['integrated_transfers'].items():transfers[k]+=D(v)
            current=prior['trial'](current,tuple(map(D,part['state'])))
        if boundary==event_index:
            before_event=list(map(str,prior['initial'](current)))
            current,removed=removal(current,event,prior,env)
            after_event=removed['state']
            for k in EVENT_FIELDS:
                value=removed['removed'][k];event_totals[k]=sum(map(D,value)) if isinstance(value,list) else D(value)
        previous=boundary
    final=prior['initial'](current);p=env['prior']['values'](s['parameters']);ca=p['air_volume_per_floor_area']*p['air_capacity_density']*env['ep']['air_heat_capacity']
    carbon=lambda y:sum(y[:3])+sum(y[5:55]);t=transfers;e=event_totals
    residuals={
        'carbohydrate':carbon(final)-carbon(initial)-t['photosynthesis']+sum(t[k] for k in prior['FLOW'][1:8])+e['leaf']+e['stem_root']+e['fruit_carbohydrate'],
        'number':sum(final[55:105])-sum(initial[55:105])-t['fruit_number_inflow']+t['terminal_fruit_number']+e['fruit_number'],
        'canopy_sensible':final[105]-initial[105]-t['canopy_external_heat']+t['canopy_to_air_sensible']+t['canopy_to_vapor_latent']-t['incoming_capacity_heat']+t['maintenance_capacity_heat']+t['removal_capacity_heat']+e['canopy_sensible_energy'],
        'air_sensible':ca*(final[106]-initial[106])-t['air_external_sensible_heat']-t['canopy_to_air_sensible'],
        'vapor_and_water_boundaries':final[107]-initial[107]-t['canopy_to_air_vapor']-t['air_external_vapor'],
        'crop_capacity':p['leaf_heat_capacity']*env['p']['sla']*(final[1]-initial[1])-t['capacity_allocation']+t['capacity_maintenance']+t['capacity_removal']+e['canopy_capacity']}
    residuals['reduced_energy']=final[105]-initial[105]+ca*(final[106]-initial[106])+env['ep']['latent_heat']*(final[107]-initial[107])-t['canopy_external_heat']-t['air_external_sensible_heat']-env['ep']['latent_heat']*t['air_external_vapor']-t['incoming_capacity_heat']+t['maintenance_capacity_heat']+t['removal_capacity_heat']+e['canopy_sensible_energy']
    assert max(map(abs,residuals.values()))<D('1e-60')
    return {'state':list(map(str,final)),'integrated_transfers':{k:str(v) for k,v in transfers.items()},
        'event_totals':{k:str(v) for k,v in event_totals.items()},'before_event_state':before_event,
        'after_event_state':after_event,'derived':derived(s,final,env),'balance_residuals':{k:str(v) for k,v in residuals.items()}}


def event(name,leaf,stem,fractions):
    q=lambda v,u:{'value':float(v),'unit':u}
    return {'input_id':'synthetic-joint-event-'+name,'origin':'synthetic','values':{
        'leaf':q(leaf,'mg_CH2O/m2_floor'),'stem_root':q(stem,'mg_CH2O/m2_floor'),
        'fruit_fraction':[q(v,'1') for v in fractions]}}


def references():
    prior,env=environment();source=json.loads((ROOT/'fixtures/crop-climate-joint-rhs-reference-cases-v1.json').read_bytes())['cases']
    none=[0]*50;quarter=[D('.25')]*50;mixed=[D('.25') if i%2 else D('.5') for i in range(50)]
    choices=[('zero',0,0,0,none),('leaf',0,1000,0,none),('stem',0,0,500,none),
        ('cohorts',0,0,0,quarter),('mixed',0,1000,500,mixed),('negative-energy',5,1000,500,mixed),
        ('zero-energy',6,1000,500,mixed),('all-fruit',0,0,0,[1]*50),
        ('all-stem',0,0,source[0]['scenario']['plant_state']['stem_root']['value'],none)]
    cases=[];programs=[]
    with localcontext() as context:
        context.prec=80
        for name,index,leaf,stem,fractions in choices:
            s=source[index]['scenario'];ev=event(name,leaf,stem,fractions)
            _,expected=removal(s,ev,prior,env)
            cases.append({'case_id':name,'scenario':s,'event':ev,'expected_decimal':expected})
        for name,index,at in (('warm-mid',0,16),('reverse-mid',1,16),('dark-mid',2,16),('initial',0,0),('final',0,32)):
            s=source[index]['scenario'];ev=event(name,1000,500,mixed)
            row={'case_id':name,'scenario':s,'event':ev,'event_at_seconds':at,'step_seconds':2,'duration_seconds':32,
                'expected_decimal':compose(s,ev,at,D(2),prior,env)}
            if at==16:row['fine_32s_dt0_25_decimal']=compose(s,ev,at,D('.25'),prior,env)
            programs.append(row)
    return {'version':'crop-climate-joint-management-reference-cases-v1','scope':'synthetic_software_reference_only',
        'oracle':'Decimal80_independent_retention_and_capacity_energy_with_pinned_joint_RK4_no_app_import',
        'input_sha256':{**env['prior']['INPUTS'],**prior['INPUTS'],**INPUTS},'cases':cases,'programs':programs,
        'hold':'manual bounded composition only; automatic continuation/UTC/storage/UI, empty-sink convergence, tissue/farm/cultivar validation not assessed'}


if __name__=='__main__':print(json.dumps(references(),sort_keys=True,indent=2))
