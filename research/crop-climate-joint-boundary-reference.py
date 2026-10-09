"""Decimal80 automatic event-grid oracle, with no product imports."""
from copy import deepcopy
from decimal import Decimal,localcontext
from hashlib import sha256
import json
from pathlib import Path
import runpy

ROOT=Path(__file__).resolve().parents[1]
D=Decimal
INPUTS={
    'research/crop-climate-joint-management-reference.py':'7982b0af6adc72a894255db06e7b4b3db2088a4fe58c84830a87b37235ed0fa4',
    'fixtures/crop-climate-joint-management-reference-cases-v1.json':'74f3aa4e9f75acc83a60c2c8bfecd3aadfc7a4359685b3e4e2ab45c6f93eb747'}


def environment():
    for name,digest in INPUTS.items():assert sha256((ROOT/name).read_bytes()).hexdigest()==digest,name
    management=runpy.run_path(str(ROOT/'research/crop-climate-joint-management-reference.py'))
    prior,env=management['environment']()
    return management,prior,env


def balances(s,y,t,e,prior,env):
    a=prior['initial'](s);p=env['prior']['values'](s['parameters']);ep=env['ep']
    ca=p['air_volume_per_floor_area']*p['air_capacity_density']*ep['air_heat_capacity']
    carbon=lambda z:sum(z[:3])+sum(z[5:55])
    material=-t['incoming_capacity_heat']+t['maintenance_capacity_heat']+t['removal_capacity_heat']+e['canopy_sensible_energy']
    out={
        'carbohydrate':carbon(y)-carbon(a)-t['photosynthesis']+sum(t[k] for k in prior['FLOW'][1:8])+e['leaf']+e['stem_root']+e['fruit_carbohydrate'],
        'number':sum(y[55:105])-sum(a[55:105])-t['fruit_number_inflow']+t['terminal_fruit_number']+e['fruit_number'],
        'canopy_sensible':y[105]-a[105]-t['canopy_external_heat']+t['canopy_to_air_sensible']+t['canopy_to_vapor_latent']+material,
        'air_sensible':ca*(y[106]-a[106])-t['air_external_sensible_heat']-t['canopy_to_air_sensible'],
        'vapor_and_water_boundaries':y[107]-a[107]-t['canopy_to_air_vapor']-t['air_external_vapor'],
        'crop_capacity':p['leaf_heat_capacity']*env['p']['sla']*(y[1]-a[1])-t['capacity_allocation']+t['capacity_maintenance']+t['capacity_removal']+e['canopy_capacity'],
        'reduced_energy':y[105]-a[105]+ca*(y[106]-a[106])+ep['latent_heat']*(y[107]-a[107])-t['canopy_external_heat']-t['air_external_sensible_heat']-ep['latent_heat']*t['air_external_vapor']+material}
    assert max(map(abs,out.values()))<D('1e-60')
    return {k:str(v) for k,v in out.items()}


def trajectory(case,dt,management,prior,env):
    s=case['scenario'];base_dt=D(str(case['step_seconds']));duration=base_dt*case['step_count']
    count=int(duration/dt);assert dt*count==duration
    def index(i):
        scaled=D(i)*base_dt/dt;assert scaled==int(scaled);return int(scaled)
    schedule={index(row['step_index']):row['event'] for row in case['events']}
    outputs={index(i) for i in case['output_steps']}
    y=prior['initial'](s)+(D(0),)*22;e={k:D(0) for k in management['EVENT_FIELDS']}
    samples=[];journal=[]
    for i in range(count+1):
        if i:
            a=prior['rhs'](s,y,env)
            b=prior['rhs'](s,tuple(v+dt*k/2 for v,k in zip(y,a,strict=True)),env)
            c=prior['rhs'](s,tuple(v+dt*k/2 for v,k in zip(y,b,strict=True)),env)
            d=prior['rhs'](s,tuple(v+dt*k for v,k in zip(y,c,strict=True)),env)
            y=tuple(v+dt*(w+2*x+2*z+t)/6 for v,w,x,z,t in zip(y,a,b,c,d,strict=True))
        if i in schedule:
            before=list(map(str,y[:108]));current=prior['trial'](s,y[:108])
            _,removed=management['removal'](current,schedule[i],prior,env)
            increment={k:sum(map(D,v)) if isinstance(v,list) else D(v) for k,v in removed['removed'].items()}
            e={k:e[k]+increment[k] for k in e};y=tuple(map(D,removed['state']))+y[108:]
            journal.append({'step_index':i,'elapsed_seconds':str(i*dt),'before':before,
                'after':removed['state'],'removed_totals':{k:str(v) for k,v in increment.items()}})
        t=dict(zip(prior['FLOW'],y[108:],strict=True));residuals=balances(s,y,t,e,prior,env)
        if i in outputs:
            samples.append({'step_index':i,'elapsed_seconds':str(i*dt),'state':list(map(str,y[:108])),
                'integrated_transfers':{k:str(v) for k,v in t.items()},'event_totals':{k:str(v) for k,v in e.items()},
                'event_count':len(journal),'derived':management['derived'](s,y,env),'balance_residuals':residuals})
    return {'samples':samples,'events':journal}


def references():
    management,prior,env=environment()
    previous=json.loads((ROOT/'fixtures/crop-climate-joint-management-reference-cases-v1.json').read_bytes())
    warm=previous['programs'][0];cases=[]
    def case(name,s,events):
        return {'case_id':name,'scenario':deepcopy(s),'events':deepcopy(events),'output_steps':[0,8,16],
            'step_seconds':2,'step_count':16}
    def scheduled(index,event):return {'step_index':index,'event':event}
    cases.append(case('no-events',warm['scenario'],[]))
    for row in previous['programs']:
        cases.append(case(row['case_id'],row['scenario'],[scheduled(row['event_at_seconds']//2,row['event'])]))
    make=management['event'];mixed=[D('.25') if i%2 else D('.5') for i in range(50)]
    cases.append(case('multiple',warm['scenario'],[
        scheduled(0,make('multi-start',1000,500,mixed)),
        scheduled(8,make('multi-mid',500,100,[D('.1')]*50)),
        scheduled(16,make('multi-end',1000,100,mixed))]))
    for old_index,name in ((5,'negative-reference'),(6,'zero-reference')):
        old=previous['cases'][old_index]
        cases.append(case(name,old['scenario'],[scheduled(8,old['event'])]))
    with localcontext() as context:
        context.prec=80
        for row in cases:
            row['expected_decimal']=trajectory(row,D(2),management,prior,env)
            if row['case_id'] in ('warm-mid','reverse-mid','dark-mid'):
                row['fine_32s_dt0_25_decimal']=trajectory(row,D('.25'),management,prior,env)
    return {'version':'crop-climate-joint-boundary-reference-cases-v1','scope':'synthetic_software_reference_only',
        'oracle':'Decimal80_one_130_vector_RK4_pinned_independent_retention_capacity_energy_no_app_import',
        'input_sha256':{**env['prior']['INPUTS'],**prior['INPUTS'],**management['INPUTS'],**INPUTS},'cases':cases,
        'hold':'bounded constant-forcing grid only; UTC/continuation/storage/UI, greenhouse/cultivar/farm and claim gates not assessed'}


if __name__=='__main__':print(json.dumps(references(),sort_keys=True,indent=2))
