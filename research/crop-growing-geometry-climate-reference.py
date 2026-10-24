"""Independent Decimal100+ growing-geometry vector RK4, no app imports."""
from copy import deepcopy
from decimal import Decimal,localcontext
from hashlib import sha256
import json
from pathlib import Path
import runpy
import sys

ROOT=Path(__file__).resolve().parents[1];D=Decimal
INPUTS=('fixtures/crop-growth-reference-parameters-v1.json','fixtures/crop-fruit-cohort-reference-parameters-v1.json',
 'fixtures/crop-canopy-exchange-reference-parameters-v1.json','fixtures/crop-climate-joint-rhs-reference-cases-v1.json',
 'research/crop-explicit-lai-carbon-reference.py','research/crop-plant-startup-reference.py',
 'research/crop-canopy-air-dynamics-reference.py','fixtures/crop-fruit-transport-reference-parameters-v1.json')
PLANT=('buffer','leaf','stem_root','temperature_filtered_24h','temperature_sum')
CLIMATE=('canopy_sensible_energy','air_temperature','air_vapor_mass')
FLOW=('photosynthesis','growth_respiration','maintenance_leaf','maintenance_stem','maintenance_fruit',
 'removal_leaf','removal_stem','terminal_carbon','entry_number','terminal_number','sensible','latent',
 'incoming_heat','outgoing_heat','canopy_external','air_external','vapor','external_vapor','capacity_in','capacity_out',
 'indoor_air_temperature_time')


def q(value,unit):return {'value':value,'unit':unit}
def values(block):return {name:D(str(row['value']))for name,row in block.items()}


def program(source):
    s=deepcopy(source['scenario']);s['forcing']['outgoing_capacity_temperature']=q(float(source['expected_decimal']['derived']['canopy_temperature']),'degC')
    leaves=[]
    for i,(m,k,a,b)in enumerate([(.5,.02,100,5),(.75,.015,120,7),(1.41,.01,140,9)]):
        leaves.append({'leaf_id':f'own-leaf-{i}','thermal_age':q(a,'degC_day'),'base_temperature':q(b,'degC'),
            'initial_area':q(m/2,'m2'),'curve':{'profile_id':f'own-curve-{i}','origin':'synthetic','values':{
                'maximum_area':q(m,'m2'),'steepness':q(k,'1/degC_day'),'inflection_age':q(a,'degC_day')}}})
    return {'input_id':s['input_id'],'origin':'synthetic','scenario':s,'leaves':leaves,
        'normalization':'zero_lower_asymptote_sigmoid_v1','thermal_age_policy':'dynamic_indoor_air_no_clip_v1',
        'capacity_policy':'declared_outflow_plus_area_capacity_derivative_v1',
        'model_floor_area':q(1,'m2_floor'),'capacity_outflow':q(.0001,'J/m2_floor/K/s')}


def optical(p,buffer,lai,tc,par,co2):
    if par==0:return D(0)
    gamma=p['cGamma']*(p['compensation_pivot_c']+(tc-p['compensation_pivot_c'])/lai)
    ci=p['etaCo2AirStom']*co2;assert 0<=gamma<=ci
    absorbed=par*(1-p['rhoCanPar'])*((1-(-p['k1Par']*lai).exp())+
        p['rhoFlrPar']*(-p['k1Par']*lai).exp()*(1-(-p['k2Par']*lai).exp()))
    kelvin=tc+p['kelvin_offset'];gas=p['gas_constant_scale']*p['R'];reference=p['t25k']
    maximum=(lai*p['j25LeafMax']*(p['eJ']*(kelvin-reference)/(gas*kelvin*reference)).exp()*
        (1+((p['S']*reference-p['H'])/(gas*reference)).exp())/(1+((p['S']*kelvin-p['H'])/(gas*kelvin)).exp()))
    light=p['alpha']*absorbed
    electron=(maximum+light-((maximum+light)**2-4*p['theta']*maximum*light).sqrt())/(2*p['theta'])
    gross=electron*(ci-gamma)/(p['electron_per_fixed_co2']*(ci+p['compensation_denominator_factor']*gamma))
    return p['mCh2o']*(gross-gross*gamma/ci)/(1+(p['buffer_full_slope']*(buffer-p['cBufMax'])).exp())


def area(age,curve):
    c=values(curve['values']);return c['maximum_area']/(1+(-c['steepness']*(age-c['inflection_age'])).exp())


def initial(p):
    s=p['scenario']
    y=tuple(D(str(row['value']))for row in [*[s['plant_state'][name]for name in PLANT],
        *s['cohort_state']['fruit_carbohydrate'],*s['cohort_state']['fruit_number'],*[s['climate_state'][name]for name in CLIMATE]])
    ages=tuple(D(str(leaf['thermal_age']['value']))for leaf in p['leaves'])
    areas=tuple(area(age,leaf['curve'])for age,leaf in zip(ages,p['leaves'],strict=True))
    return y+ages+areas


def environment():
    raw={name:(ROOT/name).read_bytes()for name in INPUTS}
    def profile(index,source=False):
        return {name:D(row['source_value']if source else str(row['value']))for name,row in json.loads(raw[INPUTS[index]])['parameters'].items()}
    return {'raw':raw,'p':profile(0),'cp':profile(1,True),'ep':profile(2),
        'nonoptical':runpy.run_path(str(ROOT/INPUTS[4]))['non_optical'],
        'whole':runpy.run_path(str(ROOT/INPUTS[5]))['calculate'],'thermal':runpy.run_path(str(ROOT/INPUTS[6]))['rhs']}


def rhs(program,y,env):
    n=len(program['leaves']);s=program['scenario'];p,cp,ep=(env[name]for name in ('p','cp','ep'))
    ages=y[108:108+n];areas=y[108+n:108+2*n]
    age_rates=tuple((y[106]-D(str(leaf['base_temperature']['value'])))/86400 for leaf in program['leaves'])
    assert all(v>=0 for v in age_rates)
    area_rates=[]
    for age,rate,leaf in zip(ages,age_rates,program['leaves'],strict=True):
        c=values(leaf['curve']['values']);exponent=(-c['steepness']*(age-c['inflection_age'])).exp()
        area_rates.append(c['steepness']*c['maximum_area']*exponent/(1+exponent)**2*rate)
    floor=D(str(program['model_floor_area']['value']));lai=sum(areas)/floor;ldot=sum(area_rates)/floor
    params=values(s['parameters']);f=values(s['forcing']);removed=values(s['removals'])
    capacity=params['leaf_heat_capacity']*lai;tc=params['reference_temperature']+y[105]/capacity
    assert D(10)<=tc<=D(34)and D(10)<=y[106]<=D(34)
    state={name:{**s['plant_state'][name],'value':v}for name,v in zip(PLANT,y[:5],strict=True)}
    cohorts={name:[{**row,'value':v}for row,v in zip(s['cohort_state'][name],part,strict=True)]
        for name,part in zip(('fruit_carbohydrate','fruit_number'),(y[5:55],y[55:105]),strict=True)}
    metadata={'input_id':'independent-growing-stage','origin':'synthetic'}
    forcing={'canopy_temperature':q(tc,'degC'),**{name:s['forcing'][name]for name in ('par_above_canopy','co2')}}
    case={'state':{**metadata,'values':state},'cohort_state':{**metadata,'values':{**cohorts,
        **s['relative_growth_rate'],**{name:state[name]for name in ('temperature_filtered_24h','temperature_sum')}}},
        'forcing':{**metadata,'values':forcing},**{name:{**metadata,'values':s[name]}for name in ('removals','fruit_entry')}}
    photo=optical(p,y[0],lai,tc,f['par_above_canopy'],f['co2']);captured=[]
    def carbon_rhs(*args):
        result=env['nonoptical'](*args,photo);captured.append(result);return result
    crop=env['whole'](case,p,cp,carbon_rhs);assert len(captured)==1;z=captured[0]
    _,_,heat=env['thermal']((tc,y[106],y[107]),{'leaf_area_index':lai,**params},
        {name:f[name]for name in ('canopy_external_heat','air_external_sensible_heat','air_external_vapor')},ep)
    e,h,le=(heat[name]for name in ('water_vapor','sensible_heat','latent_heat'))
    gout=D(str(program['capacity_outflow']['value']));gin=gout+params['leaf_heat_capacity']*ldot
    incoming=gin*(f['incoming_capacity_temperature']-params['reference_temperature'])
    outgoing=gout*(f['outgoing_capacity_temperature']-params['reference_temperature'])
    rates=tuple(D(crop['plant_derivatives'][name])for name in PLANT)+tuple(map(D,crop['dC']+crop['dN']))+(
        f['canopy_external_heat']-h-le+incoming-outgoing,(f['air_external_sensible_heat']+h)/heat['air_capacity'],e+f['air_external_vapor'])+age_rates+tuple(area_rates)
    flow=(D(crop['photosynthesis']),D(crop['growth_respiration']),z[8],z[9],D(crop['fruit_maintenance']),
        removed['leaf'],removed['stem_root'],D(crop['terminal_carbohydrate']),values(s['fruit_entry'])['fruit_number_inflow'],
        D(crop['terminal_number']),h,le,incoming,outgoing,f['canopy_external_heat'],f['air_external_sensible_heat'],
        e,f['air_external_vapor'],gin,gout,y[106])
    return rates+flow


def trajectory(p,dt,count,env):
    start=initial(p);width=len(start);y=start+(D(0),)*len(FLOW)
    for _ in range(count):
        a=rhs(p,y,env);b=rhs(p,tuple(v+dt*k/2 for v,k in zip(y,a,strict=True)),env)
        c=rhs(p,tuple(v+dt*k/2 for v,k in zip(y,b,strict=True)),env)
        d=rhs(p,tuple(v+dt*k for v,k in zip(y,c,strict=True)),env)
        y=tuple(v+dt*(w+2*x+2*z+t)/6 for v,w,x,z,t in zip(y,a,b,c,d,strict=True))
    n=len(p['leaves']);params=values(p['scenario']['parameters']);lai=sum(y[108+n:width])/D(str(p['model_floor_area']['value']))
    canonical=[area(y[108+i],leaf['curve'])for i,leaf in enumerate(p['leaves'])]
    gaps=[y[108+n+i]-value for i,value in enumerate(canonical)]
    initial_gaps=[start[108+n+i]-area(start[108+i],leaf['curve'])for i,leaf in enumerate(p['leaves'])]
    return {'state':list(map(str,y[:width])),'integrated_transfers':dict(zip(FLOW,map(str,y[width:]),strict=True)),
        'derived':{'canopy_temperature':str(params['reference_temperature']+y[105]/(params['leaf_heat_capacity']*lai)),
            'leaf_area_index':str(lai),'air_temperature':str(y[106]),'air_vapor_mass':str(y[107]),
            'fruit_carbohydrate_total':str(sum(y[5:55]))},
        'curve_residuals':list(map(str,gaps)),'initial_curve_residuals':list(map(str,initial_gaps)),
        'curve_invariant_changes':[str(v-w)for v,w in zip(gaps,initial_gaps,strict=True)]}


def generate():
    env=environment();cases=[]
    with localcontext()as context:
        context.prec=110
        old=json.loads(env['raw'][INPUTS[3]])['cases']
        for index in (0,1,2,5,6,3):
            p=program(old[index]);row={'case_id':old[index]['case_id'],'program':p,'step_seconds':2,'step_count':16,
                'expected':trajectory(p,D(2),16,env)}
            if index in (0,1,2):row['fine_32s_dt0_25']=trajectory(p,D('.25'),128,env)
            cases.append(row)
    assert not any(name=='app'or name.startswith('app.')for name in sys.modules)
    return {'schema_version':'growing-geometry-climate-decimal-reference-v1','origin':'own_synthetic_software_fixture',
        'independent_precision':110,'G0_G4':'not_assessed','cases':cases,
        'generator_sha256':sha256(Path(__file__).read_bytes()).hexdigest(),
        'input_sha256':{name:sha256(raw).hexdigest()for name,raw in env['raw'].items()}}


if __name__=='__main__':
    output=Path(sys.argv[1]);data=generate();output.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps({'cases':len(data['cases']),'app_imports':0,'sha256':sha256(output.read_bytes()).hexdigest()}))
