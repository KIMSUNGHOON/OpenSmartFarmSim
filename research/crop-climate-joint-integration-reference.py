"""Independent Decimal80 coupled RK4; pinned equations, no product imports."""
from decimal import Decimal,localcontext
from hashlib import sha256
import json
from pathlib import Path
import runpy

ROOT=Path(__file__).resolve().parents[1]
D=Decimal
INPUTS={
    'research/crop-climate-joint-rhs-reference.py':'b8edd43caf19205f8b2e64b98f4e1c7d84ceba5bf086955aff3c46ff2a7beee5',
    'fixtures/crop-climate-joint-rhs-reference-cases-v1.json':'2c95b2808297c96cad80eaebcd4ba37797706901f44115713dfddccdfffc9658'}
PLANT=('buffer','leaf','stem_root','temperature_filtered_24h','temperature_sum')
CLIMATE=('canopy_sensible_energy','air_temperature','air_vapor_mass')
FLOW=('photosynthesis','growth_respiration','maintenance_leaf','maintenance_stem_root',
    'maintenance_fruit','removal_leaf','removal_stem_root','terminal_fruit_carbohydrate',
    'fruit_number_inflow','terminal_fruit_number','canopy_to_air_sensible','canopy_to_vapor_latent',
    'incoming_capacity_heat','maintenance_capacity_heat','removal_capacity_heat','canopy_external_heat',
    'air_external_sensible_heat','canopy_to_air_vapor','air_external_vapor',
    'capacity_allocation','capacity_maintenance','capacity_removal')


def environment():
    for name,digest in INPUTS.items():assert sha256((ROOT/name).read_bytes()).hexdigest()==digest,name
    prior=runpy.run_path(str(ROOT/'research/crop-climate-joint-rhs-reference.py'))
    for name,digest in prior['INPUTS'].items():assert sha256((ROOT/name).read_bytes()).hexdigest()==digest,name
    def profile(name,source=False):
        rows=json.loads((ROOT/('fixtures/'+name)).read_bytes())['parameters']
        return {k:D(v['source_value'] if source else str(v['value'])) for k,v in rows.items()}
    return {'prior':prior,'p':profile('crop-growth-reference-parameters-v1.json'),
        'cp':profile('crop-fruit-cohort-reference-parameters-v1.json',True),
        'ep':profile('crop-canopy-exchange-reference-parameters-v1.json'),
        'startup':runpy.run_path(str(ROOT/'research/crop-plant-startup-reference.py'))['calculate'],
        'plant':runpy.run_path(str(ROOT/'research/crop-integration-reference.py'))['decimal_rhs'],
        'thermal':runpy.run_path(str(ROOT/'research/crop-canopy-air-dynamics-reference.py'))['rhs'],
        'capacity':runpy.run_path(str(ROOT/'research/crop-canopy-energy-transport-reference.py'))['transport']}


def initial(s):
    return tuple(D(str(q['value'])) for q in [*[s['plant_state'][k] for k in PLANT],
        *s['cohort_state']['fruit_carbohydrate'],*s['cohort_state']['fruit_number'],
        *[s['climate_state'][k] for k in CLIMATE]])


def trial(s,y):
    def block(original,keys,values):return {k:{**original[k],'value':v} for k,v in zip(keys,values,strict=True)}
    return {**s,'plant_state':block(s['plant_state'],PLANT,y[:5]),
        'cohort_state':{k:[{**q,'value':v} for q,v in zip(s['cohort_state'][k],part,strict=True)]
            for k,part in zip(('fruit_carbohydrate','fruit_number'),(y[5:55],y[55:105]),strict=True)},
        'climate_state':block(s['climate_state'],CLIMATE,y[105:108])}


def rhs(s,y,env):
    p,cp,ep=(env[k] for k in ('p','cp','ep'));values=env['prior']['values']
    current=trial(s,y);plant,params,f,removed=(values(current[k]) for k in ('plant_state','parameters','forcing','removals'))
    lai=p['sla']*plant['leaf'];ccan=params['leaf_heat_capacity']*lai
    tc=params['reference_temperature']+y[105]/ccan
    captured=[]
    def plant_rhs(*args):
        result=env['plant'](*args);captured.append(result);return result
    crop=env['startup'](env['prior']['legacy_case'](current,tc),p,cp,plant_rhs)
    assert len(captured)==1
    z=captured[0]
    material=env['capacity']({'leaf_carbohydrate':plant['leaf'],
        'leaf_allocation':z[1]+z[8]+removed['leaf'],'leaf_maintenance':z[8],'leaf_removal':removed['leaf'],
        'leaf_heat_capacity':params['leaf_heat_capacity'],'canopy_temperature':tc,
        'incoming_capacity_temperature':f['incoming_capacity_temperature'],
        'reference_temperature':params['reference_temperature']},p['sla'])
    _,_,thermal=env['thermal']((tc,y[106],y[107]),
        {'leaf_area_index':lai,**{k:params[k] for k in params if k!='reference_temperature'}},
        {k:f[k] for k in ('canopy_external_heat','air_external_sensible_heat','air_external_vapor')},ep)
    vapor,heat,latent=(thermal[k] for k in ('water_vapor','sensible_heat','latent_heat'))
    rates=tuple(D(crop['plant_derivatives'][k]) for k in PLANT)+tuple(map(D,crop['dC']+crop['dN']))+(
        f['canopy_external_heat']-heat-latent+material['energy_net'],
        (f['air_external_sensible_heat']+heat)/thermal['air_capacity'],vapor+f['air_external_vapor'])
    flux=(D(crop['photosynthesis']),D(crop['growth_respiration']),z[8],z[9],D(crop['fruit_maintenance']),
        removed['leaf'],removed['stem_root'],D(crop['terminal_carbohydrate']),
        values(s['fruit_entry'])['fruit_number_inflow'],D(crop['terminal_number']),heat,latent,
        material['energy_incoming'],material['energy_maintenance_outgoing'],material['energy_removal_outgoing'],
        f['canopy_external_heat'],f['air_external_sensible_heat'],vapor,f['air_external_vapor'],
        material['capacity_allocation'],material['capacity_maintenance'],material['capacity_removal'])
    return rates+flux


def trajectory(s,dt,count,env):
    # Advance one 130-vector rather than the product's separate state/ledger loops.
    y=initial(s)+(D(0),)*len(FLOW)
    for _ in range(count):
        a=rhs(s,y,env)
        b=rhs(s,tuple(v+dt*k/2 for v,k in zip(y,a,strict=True)),env)
        c=rhs(s,tuple(v+dt*k/2 for v,k in zip(y,b,strict=True)),env)
        d=rhs(s,tuple(v+dt*k for v,k in zip(y,c,strict=True)),env)
        y=tuple(v+dt*(w+2*x+2*z+t)/6 for v,w,x,z,t in zip(y,a,b,c,d,strict=True))
    params=env['prior']['values'](s['parameters']);ccan=params['leaf_heat_capacity']*env['p']['sla']*y[1]
    tc=params['reference_temperature']+y[105]/ccan
    return {'state':list(map(str,y[:108])),'integrated_transfers':dict(zip(FLOW,map(str,y[108:]),strict=True)),
        'derived':{'canopy_temperature':str(tc),'leaf_area_index':str(env['p']['sla']*y[1]),'canopy_capacity':str(ccan)}}


def references():
    env=environment();source=json.loads((ROOT/'fixtures/crop-climate-joint-rhs-reference-cases-v1.json').read_bytes())['cases']
    cases=[]
    with localcontext() as context:
        context.prec=80
        for index in (0,1,2,5,6,3):
            case=source[index];s=case['scenario']
            row={'case_id':case['case_id'],'scenario':s,'step_seconds':2,'step_count':16,
                'expected_decimal':trajectory(s,D(2),16,env)}
            if index<3:row['fine_32s_dt0_25_decimal']=trajectory(s,D('.25'),128,env)
            cases.append(row)
    return {'version':'crop-climate-joint-integration-reference-cases-v1','scope':'synthetic_software_reference_only',
        'oracle':'Decimal80_independent_130_vector_RK4_pinned_crop_exchange_capacity_no_app_import',
        'input_sha256':{**env['prior']['INPUTS'],**INPUTS},'cases':cases,
        'hold':'empty-entry same-step algorithm only; time convergence and cultivar/farm validity not assessed'}


if __name__=='__main__':print(json.dumps(references(),sort_keys=True,indent=2))
