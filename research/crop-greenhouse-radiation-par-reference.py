"""Independent 80-digit original-form solar PAR and electron-transport oracle.

Source attribution and rights: crop-par-primary-source-review-20261013.md,
LICENSES/GreenLight-BSD-3-Clause-Clear.txt. No application imports.
"""
from decimal import Decimal, localcontext
from hashlib import sha256
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT/'fixtures/crop-growth-reference-parameters-v1.json'
UNITS = {'outdoor_global_radiation': 'W/m2_floor', 'leaf_area_index': 'm2_leaf/m2_floor',
    'solar_par_fraction': '1', 'solar_par_photon_conversion': 'umol_photons/J_PAR',
    'cover_par_transmittance': '1', 'cover_par_reflectance': '1',
    'construction_interception_fraction': '1'}


def reference(scenario):
    with localcontext() as ctx:
        ctx.prec = 80
        p = {k: Decimal(str(v['value'])) for k, v in json.loads(PROFILE.read_bytes())['parameters'].items()}
        v = {k: Decimal(str(q['value'])) for k, q in scenario['values'].items()}
        one = Decimal(1)
        incoming = v['outdoor_global_radiation']*v['solar_par_fraction']
        transmitted = incoming*v['cover_par_transmittance']
        incident = transmitted*(one-v['construction_interception_fraction'])
        lai = v['leaf_area_index']
        down_transmission = (-p['k1Par']*lai).exp()
        up_transmission = (-p['k2Par']*lai).exp()
        down_absorbed = incident*(one-p['rhoCanPar'])*(one-down_transmission)
        up_absorbed = incident*down_transmission*p['rhoFlrPar']*(one-p['rhoCanPar'])*(one-up_transmission)
        canopy = down_absorbed+up_absorbed
        floor = incident*down_transmission*(one-p['rhoFlrPar'])
        reflected = incident*p['rhoCanPar']*(one-down_transmission) + (
            incident*down_transmission*p['rhoFlrPar']*p['rhoCanPar']*(one-up_transmission))
        upward = incident*down_transmission*p['rhoFlrPar']*up_transmission
        result = {'outdoor_PAR': incoming, 'above_canopy_PAR': incident,
            'canopy_direct_absorbed_PAR': down_absorbed, 'canopy_floor_absorbed_PAR': up_absorbed,
            'canopy_absorbed': canopy, 'floor_absorbed': floor,
            'unresolved_reflected': reflected, 'upward_transmitted': upward,
            'cover_reflected': incoming*v['cover_par_reflectance'],
            'cover_absorbed': incoming*(one-v['cover_par_transmittance']-v['cover_par_reflectance']),
            'construction_intercepted': transmitted*v['construction_interception_fraction'],
            'par_above_canopy': incident*v['solar_par_photon_conversion'],
            'par_absorbed_canopy': canopy*v['solar_par_photon_conversion']}
        result['interior_sum'] = canopy+floor+reflected+upward
        result['exterior_PAR_sum'] = result['interior_sum']+sum(result[k] for k in (
            'cover_reflected', 'cover_absorbed', 'construction_intercepted'))
        # Original subtraction-root electron transport, distinct from product's rationalized form.
        if lai == 0 or incident == 0:
            transport = Decimal(0)
        else:
            kelvin = Decimal(20)+p['kelvin_offset']
            gas = p['gas_constant_scale']*p['R']
            potential = lai*p['j25LeafMax']*(p['eJ']*(kelvin-p['t25k'])/(gas*kelvin*p['t25k'])).exp()*(
                one+((p['S']*p['t25k']-p['H'])/(gas*p['t25k'])).exp())/(
                one+((p['S']*kelvin-p['H'])/(gas*kelvin)).exp())
            light = p['alpha']*result['par_absorbed_canopy']
            transport = (potential+light-((potential+light)**2-4*p['theta']*potential*light).sqrt())/(2*p['theta'])
        result['electron_transport_at_20C'] = transport
        return {k: str(value) for k, value in result.items()}


def document():
    baseline = {'outdoor_global_radiation': 600, 'leaf_area_index': 2,
        'solar_par_fraction': 0.5, 'solar_par_photon_conversion': 4.6,
        'cover_par_transmittance': 0.7, 'cover_par_reflectance': 0.15,
        'construction_interception_fraction': 0.1}
    variations = [('nominal', {}), ('dark', {'outdoor_global_radiation': 0}),
        ('no-leaves', {'leaf_area_index': 0}),
        ('opaque', {'cover_par_transmittance': 0, 'cover_par_reflectance': 0.6}),
        ('reflective-cover', {'cover_par_transmittance': 0, 'cover_par_reflectance': 1}),
        ('construction-intercepts-all', {'construction_interception_fraction': 1}),
        ('transparent-cover', {'cover_par_transmittance': 1, 'cover_par_reflectance': 0}),
        ('sparse-canopy', {'leaf_area_index': 1e-8, 'solar_par_photon_conversion': 5.1}),
        ('dense-canopy', {'leaf_area_index': 50}), ('no-PAR', {'solar_par_fraction': 0})]
    cases = []
    for name, changes in variations:
        values = {**baseline, **changes}
        scenario = {'input_id': 'synthetic-PAR-'+name, 'origin': 'synthetic',
            'values': {k: {'value': values[k], 'unit': unit} for k, unit in UNITS.items()}}
        cases.append({'case_id': name, 'scenario': scenario, 'expected_decimal': reference(scenario)})
    return {'fixture_version': 'crop-greenhouse-radiation-par-reference-cases-v1',
        'scope': 'self-authored synthetic software cases only; actual crop Runs0; G0_G4 not_assessed',
        'decimal_precision': 80, 'generator_sha256': sha256(Path(__file__).read_bytes()).hexdigest(),
        'profile_sha256': sha256(PROFILE.read_bytes()).hexdigest(),
        'comparison': {'relative': 2e-13, 'absolute': 0, 'expected_zero': 'exact'}, 'cases': cases}


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(); parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    with args.output.open('x') as output:
        output.write(json.dumps(document(), indent=2, sort_keys=True, allow_nan=False)+'\n')
