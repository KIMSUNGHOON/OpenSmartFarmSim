"""Independent Decimal80 PAR/ventilation143-vector RK4; no application imports."""
import argparse
from copy import deepcopy
from decimal import Decimal, localcontext
from hashlib import sha256
import json
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[1]
D = Decimal
INPUTS = {
    'research/crop-greenhouse-ventilation-joint-reference.py': '02cbd0c0e4d69ed0f52610baa82fc670a2991e6b446a2ec220b09ce04f0ba077',
    'research/crop-greenhouse-radiation-par-reference.py': 'f5878ef40a338a9255123f5556b0ad6113a209f52c688752b0a83822122f53b5',
    'fixtures/crop-greenhouse-radiation-par-reference-cases-v1.json': '16db7514a941c866a993aa4978fabf7505c57b1c4daa9622c8589e79f901665c'}
PAR_FIELDS = ('outdoor', 'above_canopy', 'cover_reflected', 'cover_absorbed',
    'construction_intercepted', 'canopy_absorbed', 'floor_absorbed',
    'unresolved_reflected', 'upward_transmitted')


def environment():
    for name, digest in INPUTS.items():
        assert sha256((ROOT/name).read_bytes()).hexdigest() == digest, name
    vent = runpy.run_path(str(ROOT/'research/crop-greenhouse-ventilation-joint-reference.py'))
    assert sha256(vent['PRIOR'].read_bytes()).hexdigest() == vent['PRIOR_SHA256']
    prior = runpy.run_path(str(vent['PRIOR']))
    return {'vent': vent, 'prior': prior, 'env': prior['environment'](),
        'par': runpy.run_path(str(ROOT/'research/crop-greenhouse-radiation-par-reference.py'))['reference']}


def rhs(s, solar, weather, y, e):
    lai = e['env']['p']['sla']*y[1]
    optical = e['par']({**solar, 'values': {**solar['values'],
        'leaf_area_index': {'value': lai, 'unit': 'm2_leaf/m2_floor'}}})
    par = {k: D(v) for k, v in optical.items()}
    forcing = deepcopy(s['forcing'])
    other = D(str(forcing.pop('canopy_non_par_heat')['value']))
    forcing['canopy_external_heat'] = {'value': other+par['canopy_absorbed'], 'unit': 'W/m2_floor'}
    forcing['par_above_canopy'] = {'value': par['par_above_canopy'], 'unit': 'umol_photons/m2_floor/s'}
    values = {'outdoor': par['outdoor_PAR'], 'above_canopy': par['above_canopy_PAR'], **par}
    return e['vent']['rhs']({**s, 'forcing': forcing}, weather, y, e['env'], e['prior']) + (
        other, *(values[k] for k in PAR_FIELDS))


def trajectory(s, solar, weather, dt, count, e):
    flow = e['prior']['FLOW']+e['vent']['EXTRA']+('canopy_non_par_heat',)+tuple('solar_par_'+k for k in PAR_FIELDS)
    y = e['prior']['initial'](s)+(D(0),)*len(flow)
    for _ in range(count):
        a = rhs(s, solar, weather, y, e)
        b = rhs(s, solar, weather, tuple(v+dt*k/2 for v, k in zip(y, a, strict=True)), e)
        c = rhs(s, solar, weather, tuple(v+dt*k/2 for v, k in zip(y, b, strict=True)), e)
        d = rhs(s, solar, weather, tuple(v+dt*k for v, k in zip(y, c, strict=True)), e)
        y = tuple(v+dt*(p+2*q+2*r+t)/6 for v, p, q, r, t in zip(y, a, b, c, d, strict=True))
    params = e['env']['prior']['values'](s['parameters'])
    capacity = params['leaf_heat_capacity']*e['env']['p']['sla']*y[1]
    return {'state': list(map(str, y[:108])),
        'integrated_transfers': dict(zip(flow, map(str, y[108:]), strict=True)),
        'derived': {'canopy_temperature': str(params['reference_temperature']+y[105]/capacity),
            'leaf_area_index': str(e['env']['p']['sla']*y[1]), 'canopy_capacity': str(capacity)}}


def references():
    e = environment()
    source = json.loads((ROOT/'fixtures/crop-climate-joint-rhs-reference-cases-v1.json').read_bytes())['cases']
    solar_base = json.loads((ROOT/'fixtures/crop-greenhouse-radiation-par-reference-cases-v1.json').read_bytes())['cases'][0]['scenario']
    definitions = [('day-cool-dry', 0), ('day-warm-moist', 1), ('dark-mixed', 2),
        ('signed-non-PAR', 0), ('changed-leaf', 0), ('zero-ventilation', 0)]
    cases = []
    with localcontext() as context:
        context.prec = 80
        for index, (name, source_index) in enumerate(definitions):
            s, solar = deepcopy(source[source_index]['scenario']), deepcopy(solar_base)
            s['forcing']['canopy_non_par_heat'] = s['forcing'].pop('canopy_external_heat')
            del s['forcing']['par_above_canopy']
            del solar['values']['leaf_area_index']
            if index == 2: solar['values']['outdoor_global_radiation']['value'] = 0
            if index == 3: s['forcing']['canopy_non_par_heat']['value'] = -50
            if index == 4:
                s['plant_state']['leaf']['value'] *= 1.15
                s['climate_state']['canopy_sensible_energy']['value'] *= 1.15
            weather = e['vent']['weather'](name)
            if index == 1: weather = e['vent']['weather'](name, 28, 2800, .008)
            if index == 2: weather = e['vent']['weather'](name, 26, 1200, .010)
            if index == 5: weather = e['vent']['weather'](name, flow=0)
            row = {'case_id': name, 'scenario': s, 'solar': solar, 'ventilation': weather,
                'step_seconds': 2, 'step_count': 16,
                'expected_decimal': trajectory(s, solar, weather, D(2), 16, e)}
            if index < 3:
                row['fine_32s_dt0_25_decimal'] = trajectory(s, solar, weather, D('.25'), 128, e)
            cases.append(row)
    return {'version': 'crop-greenhouse-radiation-par-integration-reference-cases-v1',
        'generator_sha256': sha256(Path(__file__).read_bytes()).hexdigest(),
        'input_sha256': {**INPUTS, str(e['vent']['PRIOR'].relative_to(ROOT)): e['vent']['PRIOR_SHA256'],
            **e['prior']['INPUTS'], **e['env']['prior']['INPUTS']},
        'oracle': 'Decimal80_independent143_vector_RK4_no_app_import',
        'scope': 'self_authored_synthetic_math_only', 'G0_G4': 'not_assessed', 'cases': cases}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    with args.output.open('x') as output:
        output.write(json.dumps(references(), indent=2, sort_keys=True, allow_nan=False)+'\n')
