"""App-free Decimal110 stock/area/climate ODE and RK4; synthetic software reference."""
from copy import deepcopy
from decimal import Decimal,localcontext
from hashlib import sha256
import json
from pathlib import Path
import runpy,sys

ROOT=Path(__file__).resolve().parents[1];D=Decimal
PREVIOUS='research/crop-growing-geometry-climate-reference.py'
SOURCE='fixtures/crop-growing-geometry-climate-reference-v1.json'


def q(v,unit):return {'value':v,'unit':unit}


def program(old,index):
    p=deepcopy(old);C=p['scenario']['plant_state'].pop('leaf')['value'];R=p['scenario']['removals'].pop('leaf')['value']
    p['leaf_stock_policy']='leaf-stocks-uniform-maintenance-explicit-removal-v1'
    weights,shares=(((1.,2.,4.),(.25,.25,.5)),((0.,0.,0.),(.25,.25,.5)),((0.,1.,2.),(0.,.5,.5)))[index%3]
    for leaf,w,share in zip(p['leaves'],weights,shares,strict=True):
        leaf.update(initial_carbon=q(C*share,'mg_CH2O/m2_floor'),sink_weight=q(w,'1'),carbon_removal=q(R*share,'mg_CH2O/m2_floor/s'))
    return p


def adapter(p,carbon):
    adapted={k:deepcopy(v)for k,v in p.items()if k!='leaf_stock_policy'}
    adapted['leaves']=[{k:v for k,v in leaf.items()if k not in('initial_carbon','sink_weight','carbon_removal')}for leaf in adapted['leaves']]
    adapted['scenario']['plant_state']['leaf']=q(sum(carbon),'mg_CH2O/m2_floor')
    adapted['scenario']['removals']['leaf']=q(sum(D(str(x['carbon_removal']['value']))for x in p['leaves']),'mg_CH2O/m2_floor/s')
    return adapted


def environment():
    previous=runpy.run_path(str(ROOT/PREVIOUS));env=previous['environment']()
    env['previous']=previous;env['raw'].update({name:(ROOT/name).read_bytes()for name in(PREVIOUS,SOURCE)})
    return env


def initial(p,env):
    carbon=tuple(D(str(x['initial_carbon']['value']))for x in p['leaves'])
    y=env['previous']['initial'](adapter(p,carbon));return y[:1]+y[2:]+carbon


def flow_names(p,env):return (*env['previous']['FLOW'],*(f'leaf_{i}_{k}'for i in range(len(p['leaves']))for k in('inflow','maintenance','removal')))


def rhs(p,y,env):
    n=len(p['leaves']);carbon=y[107+2*n:107+3*n];total=sum(carbon);assert total>0 and all(v>=0 for v in carbon)
    old_y=y[:1]+(total,)+y[1:107+2*n];adapted=adapter(p,carbon);old_width=len(old_y)
    evaluated=env['previous']['rhs'](adapted,old_y,env);old_rates=evaluated[:old_width];flow=list(evaluated[old_width:])
    removed=[D(str(x['carbon_removal']['value']))for x in p['leaves']]
    weights=[D(str(x['sink_weight']['value']))for x in p['leaves']];W=sum(weights)
    G=old_rates[1]+flow[2]+sum(removed);inflow=[G*w/W if W else D(0)for w in weights]
    maintenance=[flow[2]*c/total for c in carbon];derivatives=[g-m-r for g,m,r in zip(inflow,maintenance,removed,strict=True)]
    assert all(c!=0 or rate>=0 for c,rate in zip(carbon,derivatives,strict=True))
    deferred=G-sum(inflow);cost=env['p']['cLeafG'];rates=list(old_rates[:1]+old_rates[2:])+derivatives
    rates[0]+=(1+cost)*deferred;flow[1]-=cost*deferred;flow[2]=sum(maintenance)
    return tuple(rates+flow+[v for row in zip(inflow,maintenance,removed,strict=True)for v in row])


def trajectory(p,dt,count,env):
    start=initial(p,env);width=len(start);names=flow_names(p,env);y=start+(D(0),)*len(names)
    for _ in range(count):
        a=rhs(p,y,env);b=rhs(p,tuple(v+dt*k/2 for v,k in zip(y,a,strict=True)),env)
        c=rhs(p,tuple(v+dt*k/2 for v,k in zip(y,b,strict=True)),env)
        d=rhs(p,tuple(v+dt*k for v,k in zip(y,c,strict=True)),env)
        y=tuple(v+dt*(w+2*x+2*z+t)/6 for v,w,x,z,t in zip(y,a,b,c,d,strict=True))
    n=len(p['leaves']);params=env['previous']['values'](p['scenario']['parameters'])
    lai=sum(y[107+n:107+2*n])/D(str(p['model_floor_area']['value']))
    canonical=[env['previous']['area'](y[107+i],leaf['curve'])for i,leaf in enumerate(p['leaves'])]
    gaps=[y[107+n+i]-v for i,v in enumerate(canonical)]
    initial_gaps=[start[107+n+i]-env['previous']['area'](start[107+i],leaf['curve'])for i,leaf in enumerate(p['leaves'])]
    return {'state':list(map(str,y[:width])),'integrated_transfers':dict(zip(names,map(str,y[width:]),strict=True)),
        'derived':{'canopy_temperature':str(params['reference_temperature']+y[104]/(params['leaf_heat_capacity']*lai)),
            'leaf_area_index':str(lai),'leaf_carbohydrate':str(sum(y[107+2*n:width])),
            'air_temperature':str(y[105]),'air_vapor_mass':str(y[106])},
        'curve_residuals':list(map(str,gaps)),'curve_invariant_changes':[str(v-w)for v,w in zip(gaps,initial_gaps,strict=True)]}


def generate():
    env=environment();cases=[]
    with localcontext()as context:
        context.prec=110
        for index,source in enumerate(json.loads(env['raw'][SOURCE])['cases']):
            p=program(source['program'],index);row={'case_id':source['case_id']+'-individual-stock','program':p,
                'step_seconds':2,'step_count':16,'expected':trajectory(p,D(2),16,env)}
            if index==0:row['fine_32s_dt0_25']=trajectory(p,D('.25'),128,env)
            cases.append(row)
    assert len(cases)==6 and not any(name=='app'or name.startswith('app.')for name in sys.modules)
    return {'schema_version':'leaf-carbon-stock-dynamics-decimal-reference-v1','origin':'own_synthetic_software_fixture',
        'independent_precision':110,'G0_G4':'not_assessed','cases':cases,'generator_sha256':sha256(Path(__file__).read_bytes()).hexdigest(),
        'input_sha256':{name:sha256(raw).hexdigest()for name,raw in env['raw'].items()}}


if __name__=='__main__':
    destination=Path(sys.argv[1]);assert not destination.exists();result=generate()
    destination.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'cases':len(result['cases']),'precision':110,'app_imports':0,'sha256':sha256(destination.read_bytes()).hexdigest()}))
