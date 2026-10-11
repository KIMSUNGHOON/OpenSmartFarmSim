"""Independent Decimal80 stage ventilation plus pinned crop/canopy equations."""
import argparse
from copy import deepcopy
from decimal import Decimal, localcontext
from hashlib import sha256
import json
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[1]
D = Decimal
PRIOR = ROOT/'research/crop-climate-joint-integration-reference.py'
PRIOR_SHA256 = '1a0fc4170c12d90f72e6311f7273f28e7c8a734980f83bff2986a281f8191a21'
EXTRA = ('ventilation_sensible_heat', 'ventilation_vapor', 'ventilation_latent_energy')


def weather(name, temperature=16, pressure=800, flow=.015):
    return {'input_id': name, 'origin': 'synthetic', 'forcing': {
        'outdoor_air_temperature': {'value': float(temperature), 'unit': 'degC'},
        'outdoor_vapor_pressure': {'value': float(pressure), 'unit': 'Pa'},
        'volume_exchange_per_floor_area': {'value': float(flow), 'unit': 'm3/m2_floor/s'}}}


def rhs(s, w, y, env, prior):
    params = env['prior']['values'](s['parameters'])
    forcing = env['prior']['values'](w['forcing'])
    outside = forcing['outdoor_vapor_pressure'] / (params['vapor_gas_constant'] * (
        forcing['outdoor_air_temperature'] + D('273.15')))
    heat = params['air_capacity_density']*env['ep']['air_heat_capacity']*forcing[
        'volume_exchange_per_floor_area']*(forcing['outdoor_air_temperature']-y[106])
    vapor = forcing['volume_exchange_per_floor_area']*(outside-y[107]/params['air_volume_per_floor_area'])
    combined = {**s, 'forcing': {**s['forcing'],
        'air_external_sensible_heat': {**s['forcing']['air_external_sensible_heat'],
            'value': D(str(s['forcing']['air_external_sensible_heat']['value']))+heat},
        'air_external_vapor': {**s['forcing']['air_external_vapor'],
            'value': D(str(s['forcing']['air_external_vapor']['value']))+vapor}}}
    return prior['rhs'](combined, y, env)+(heat, vapor, env['ep']['latent_heat']*vapor)


def trajectory(s, w, dt, count, env, prior):
    y = prior['initial'](s)+(D(0),)*25
    for _ in range(count):
        a = rhs(s, w, y, env, prior)
        b = rhs(s, w, tuple(v+dt*k/2 for v, k in zip(y, a, strict=True)), env, prior)
        c = rhs(s, w, tuple(v+dt*k/2 for v, k in zip(y, b, strict=True)), env, prior)
        d = rhs(s, w, tuple(v+dt*k for v, k in zip(y, c, strict=True)), env, prior)
        y = tuple(v+dt*(p+2*q+2*r+t)/6 for v, p, q, r, t in zip(y, a, b, c, d, strict=True))
    params = env['prior']['values'](s['parameters'])
    capacity = params['leaf_heat_capacity']*env['p']['sla']*y[1]
    temperature = params['reference_temperature']+y[105]/capacity
    return {'state': list(map(str, y[:108])),
        'integrated_transfers': dict(zip(prior['FLOW']+EXTRA, map(str, y[108:]), strict=True)),
        'derived': {'canopy_temperature': str(temperature),
            'leaf_area_index': str(env['p']['sla']*y[1]), 'canopy_capacity': str(capacity)}}


def references():
    assert sha256(PRIOR.read_bytes()).hexdigest() == PRIOR_SHA256
    prior = runpy.run_path(str(PRIOR))
    env = prior['environment']()
    source = json.loads((ROOT/'fixtures/crop-climate-joint-rhs-reference-cases-v1.json').read_bytes())['cases']
    definitions = [(0, weather('cool-dry')), (1, weather('warm-moist', 28, 2800, .008)),
        (2, weather('dark-mixed', 26, 1200, .010)), (0, weather('zero-ventilation', flow=0)),
        (5, weather('reference30')), (6, weather('reference22-zero-energy'))]
    cases = []
    with localcontext() as context:
        context.prec = 80
        for number, (index, forcing) in enumerate(definitions):
            s = deepcopy(source[index]['scenario'])
            row = {'case_id': forcing['input_id'], 'scenario': s, 'ventilation': forcing,
                'step_seconds': 2, 'step_count': 16,
                'expected_decimal': trajectory(s, forcing, D(2), 16, env, prior)}
            if number < 3:
                row['fine_32s_dt0_25_decimal'] = trajectory(s, forcing, D('.25'), 128, env, prior)
            cases.append(row)
    return {'version': 'joint-prescribed-ventilation-reference-cases-v1',
        'generator_sha256': sha256(Path(__file__).read_bytes()).hexdigest(),
        'input_sha256': {str(PRIOR.relative_to(ROOT)): sha256(PRIOR.read_bytes()).hexdigest(),
            **prior['INPUTS'], **env['prior']['INPUTS']},
        'oracle': 'Decimal80_independent_133_vector_RK4_no_app_import',
        'scope': 'self_authored_synthetic_math_only', 'G0_G4': 'not_assessed', 'cases': cases}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    with args.output.open('x') as output:
        json.dump(references(), output, indent=2, sort_keys=True, allow_nan=False)
        output.write('\n')
