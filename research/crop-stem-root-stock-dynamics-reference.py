"""App-free Decimal110 individual stem/root, leaf and climate ODE/RK4."""
from copy import deepcopy
from decimal import Decimal, localcontext
from hashlib import sha256
import json
from pathlib import Path
import runpy, sys

ROOT = Path(__file__).resolve().parents[1]
D = Decimal
PREVIOUS = 'research/crop-leaf-carbon-stock-dynamics-reference.py'
SOURCE = 'fixtures/crop-leaf-carbon-stock-dynamics-reference-v1.json'


def q(value, unit): return {'value': value, 'unit': unit}


def program(old, index):
    p = deepcopy(old); C = p['scenario']['plant_state'].pop('stem_root')['value']; R = p['scenario']['removals'].pop('stem_root')['value']
    shares, weights = [((.1,.2,.3,.4),(1.,2.,3.,4.)), ((0.,.5,0.,.5),(0.,0.,0.,0.)),
                       ((0.,0.,0.,0.),(0.,1.,0.,3.)), ((1.,0.,0.,0.),(1.,0.,0.,0.)),
                       ((.25,.25,.25,.25),(0.,1.,0.,3.)), ((1/3,1/3,1/3,0.),(1.,2.,3.,4.))][index]
    p['stem_root_stock_policy'] = 'stem-root-stocks-uniform-maintenance-explicit-removal-v1'
    p['stem_root_compartments'] = [{'compartment_id': 'own-root' if i == 0 else f'own-internode-{i}',
        'kind': 'root_system' if i == 0 else 'internode', 'initial_carbon': q(C*share,'mg_CH2O/m2_floor'),
        'sink_weight': q(w,'1'), 'carbon_removal': q(R*share,'mg_CH2O/m2_floor/s')}
        for i,(share,w) in enumerate(zip(shares,weights,strict=True))]
    return p


def adapter(p, carbon):
    adapted = {k:deepcopy(v) for k,v in p.items() if k not in ('stem_root_stock_policy','stem_root_compartments')}
    adapted['scenario']['plant_state']['stem_root'] = q(sum(carbon),'mg_CH2O/m2_floor')
    adapted['scenario']['removals']['stem_root'] = q(sum(D(str(r['carbon_removal']['value'])) for r in p['stem_root_compartments']),'mg_CH2O/m2_floor/s')
    return adapted


def environment():
    previous = runpy.run_path(str(ROOT/PREVIOUS)); env = previous['environment']()
    env['leaf'] = previous; env['raw'].update({name:(ROOT/name).read_bytes() for name in (PREVIOUS,SOURCE)})
    return env


def initial(p, env):
    carbon = tuple(D(str(r['initial_carbon']['value'])) for r in p['stem_root_compartments'])
    y = env['leaf']['initial'](adapter(p,carbon),env)
    return y[:1] + y[2:] + carbon


def flow_names(p, env):
    return (*env['leaf']['flow_names'](p,env), *(f'stem_root_{i}_{k}' for i in range(len(p['stem_root_compartments'])) for k in ('inflow','maintenance','removal')))


def rhs(p, y, env):
    n = len(p['leaves']); m = len(p['stem_root_compartments']); offset = 106+3*n
    carbon = y[offset:offset+m]; total = sum(carbon); assert total >= 0 and all(c >= 0 for c in carbon)
    old_y = y[:1]+(total,)+y[1:offset]; width = len(old_y)
    evaluated = env['leaf']['rhs'](adapter(p,carbon),old_y,env); old_rates = evaluated[:width]; flow = list(evaluated[width:])
    removed = [D(str(r['carbon_removal']['value'])) for r in p['stem_root_compartments']]
    weights = [D(str(r['sink_weight']['value'])) for r in p['stem_root_compartments']]; W = sum(weights)
    G = old_rates[1]+flow[3]+sum(removed)
    inflow = [G*w/W if W else D(0) for w in weights]
    assert total > 0 or flow[3] == 0
    maintenance = [flow[3]*c/total if total else D(0) for c in carbon]
    derivatives = [g-m-r for g,m,r in zip(inflow,maintenance,removed,strict=True)]
    assert all(c != 0 or rate >= 0 for c,rate in zip(carbon,derivatives,strict=True))
    deferred = G-sum(inflow); cost = env['p']['cStemG']
    rates = list(old_rates[:1]+old_rates[2:])+derivatives
    rates[0] += (1+cost)*deferred; flow[1] -= cost*deferred; flow[3] = sum(maintenance)
    return tuple(rates+flow+[v for row in zip(inflow,maintenance,removed,strict=True) for v in row])


def trajectory(p, dt, count, env):
    start = initial(p,env); width = len(start); names = flow_names(p,env); y = start+(D(0),)*len(names)
    for _ in range(count):
        a = rhs(p,y,env); b = rhs(p,tuple(v+dt*k/2 for v,k in zip(y,a,strict=True)),env)
        c = rhs(p,tuple(v+dt*k/2 for v,k in zip(y,b,strict=True)),env)
        d = rhs(p,tuple(v+dt*k for v,k in zip(y,c,strict=True)),env)
        y = tuple(v+dt*(w+2*x+2*z+t)/6 for v,w,x,z,t in zip(y,a,b,c,d,strict=True))
    n = len(p['leaves']); params = env['previous']['values'](p['scenario']['parameters'])
    lai = sum(y[106+n:106+2*n])/D(str(p['model_floor_area']['value']))
    gaps = [y[106+n+i]-env['previous']['area'](y[106+i],leaf['curve']) for i,leaf in enumerate(p['leaves'])]
    first = [start[106+n+i]-env['previous']['area'](start[106+i],leaf['curve']) for i,leaf in enumerate(p['leaves'])]
    return {'state':list(map(str,y[:width])), 'integrated_transfers':dict(zip(names,map(str,y[width:]),strict=True)),
        'derived':{'canopy_temperature':str(params['reference_temperature']+y[103]/(params['leaf_heat_capacity']*lai)),
            'leaf_area_index':str(lai),'leaf_carbohydrate':str(sum(y[106+2*n:106+3*n])),
            'stem_root_carbohydrate':str(sum(y[106+3*n:width])), 'air_temperature':str(y[104]),'air_vapor_mass':str(y[105])},
        'curve_residuals':list(map(str,gaps)), 'curve_invariant_changes':[str(v-w) for v,w in zip(gaps,first,strict=True)]}


def generate():
    env = environment(); cases = []
    with localcontext() as context:
        context.prec = 110
        for index,source in enumerate(json.loads(env['raw'][SOURCE])['cases']):
            p = program(source['program'],index)
            row = {'case_id':source['case_id']+'-stem-root-stocks','program':p,'step_seconds':2,'step_count':16,
                   'expected':trajectory(p,D(2),16,env)}
            if index == 0: row['fine_32s_dt0_25'] = trajectory(p,D('.25'),128,env)
            cases.append(row)
    assert len(cases) == 6 and not any(n == 'app' or n.startswith('app.') for n in sys.modules)
    return {'schema_version':'stem-root-stock-dynamics-decimal-reference-v1','origin':'own_synthetic_software_fixture',
        'independent_precision':110,'G0_G4':'not_assessed','cases':cases,'generator_sha256':sha256(Path(__file__).read_bytes()).hexdigest(),
        'input_sha256':{name:sha256(raw).hexdigest() for name,raw in env['raw'].items()}}


if __name__ == '__main__':
    destination = Path(sys.argv[1]); assert not destination.exists(); result = generate()
    destination.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'cases':len(result['cases']),'precision':110,'app_imports':0,'sha256':sha256(destination.read_bytes()).hexdigest()}))
