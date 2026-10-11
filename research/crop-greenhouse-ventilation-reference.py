"""Independent Decimal ventilation oracle; no application imports."""
import argparse
from copy import deepcopy
from decimal import Decimal, localcontext
from hashlib import sha256
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / 'fixtures/crop-canopy-exchange-reference-parameters-v1.json'
PROFILE_SHA = '1e032ced2ffdaf8ba713184e89b628cce4173c9e7231f30710afeda8fbf20110'


def quantity(value, unit):
    return {'value': float(value), 'unit': unit}


def scenario(name, *, air=24, mass=.06, height=4, density=1.2, rv=461.5, outdoor=16, pressure=800, flow=.015):
    return {'input_id': name, 'origin': 'synthetic',
        'state': {'air_temperature': quantity(air, 'degC'),
            'air_vapor_mass': quantity(mass, 'kg_water/m2_floor')},
        'parameters': {'air_volume_per_floor_area': quantity(height, 'm3/m2_floor'),
            'air_capacity_density': quantity(density, 'kg_air/m3'),
            'vapor_gas_constant': quantity(rv, 'J/kg_water/K')},
        'forcing': {'outdoor_air_temperature': quantity(outdoor, 'degC'),
            'outdoor_vapor_pressure': quantity(pressure, 'Pa'),
            'volume_exchange_per_floor_area': quantity(flow, 'm3/m2_floor/s')}}


def document():
    raw = PROFILE.read_bytes()
    assert sha256(raw).hexdigest() == PROFILE_SHA
    profile = json.loads(raw)
    cases = [scenario('cool_dry'), scenario('warm_moist', air=18, mass=.025, height=3,
        outdoor=28, pressure=2800, flow=.008), scenario('zero_exchange', flow=0),
        scenario('dry_equilibrium', mass=0, outdoor=24, pressure=0),
        scenario('isothermal_humidity_gradient', mass=.04, outdoor=24, pressure=900),
        scenario('source_vapor_constant', rv=8314/18)]
    result = []
    with localcontext() as context:
        context.prec = 80
        cp = Decimal(str(profile['parameters']['air_heat_capacity']['value']))
        latent = Decimal(str(profile['parameters']['latent_heat']['value']))
        for item in cases:
            s, p, f = ({k: Decimal(str(q['value'])) for k, q in item[name].items()}
                for name in ('state', 'parameters', 'forcing'))
            inside = s['air_vapor_mass'] / p['air_volume_per_floor_area']
            outside = f['outdoor_vapor_pressure'] / (p['vapor_gas_constant'] *
                (f['outdoor_air_temperature'] + Decimal('273.15')))
            sensible = p['air_capacity_density'] * cp * f['volume_exchange_per_floor_area'] * (
                f['outdoor_air_temperature'] - s['air_temperature'])
            vapor = f['volume_exchange_per_floor_area'] * (outside - inside)
            vapor_energy = latent * vapor
            result.append({'case_id': item['input_id'], 'scenario': deepcopy(item),
                'expected_decimal': {k: str(v) for k, v in {
                    'indoor_vapor_density': inside, 'outdoor_vapor_density': outside,
                    'air_external_sensible_heat': sensible, 'air_external_vapor': vapor,
                    'latent_energy': vapor_energy, 'reduced_energy_to_air': sensible + vapor_energy}.items()}})
    return {'schema_version': 'prescribed-ventilation-decimal-reference-v1',
        'generator_sha256': sha256(Path(__file__).read_bytes()).hexdigest(),
        'profile_sha256': PROFILE_SHA, 'source_sha256': profile['source_sha256'],
        'notice_sha256': profile['notice_sha256'], 'decimal_precision': 80,
        'numeric_inputs': 'Decimal(str(explicit_binary64_input))',
        'comparison': {'relative': 2e-14, 'absolute': 0, 'expected_zero': 'exact'},
        'scope': 'self_authored_synthetic_math_only', 'G0_G4': 'not_assessed', 'cases': result}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    with args.output.open('x') as output:
        json.dump(document(), output, indent=2, sort_keys=True, allow_nan=False)
        output.write('\n')
