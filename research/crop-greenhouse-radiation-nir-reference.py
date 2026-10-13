"""Independent Decimal80 source composition and two-stream cavity; no app imports."""
from decimal import Decimal, localcontext
from hashlib import sha256
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
D = Decimal
UNITS = {'outdoor_global_radiation': 'W/m2_floor', 'solar_nir_fraction': '1',
    'leaf_area_index': 'm2_leaf/m2_floor', 'nir_extinction_coefficient': 'm2_floor/m2_leaf',
    'cover_nir_reflectance': '1', 'canopy_nir_reflectance': '1', 'floor_nir_reflectance': '1',
    'construction_interception_fraction': '1'}


def reference(scenario):
    with localcontext() as ctx:
        ctx.prec = 80
        v = {k: D.from_float(float(q['value'])) for k, q in scenario['values'].items()}
        one = D(1); c, f = v['cover_nir_reflectance'], v['floor_nir_reflectance']
        x, y = one-c, one-f
        t = (-v['nir_extinction_coefficient']*v['leaf_area_index']).exp()
        r = v['canopy_nir_reflectance']*(one-t)
        a = (one-v['canopy_nir_reflectance'])*(one-t)
        # Ordered source layer equations, with source subtraction absorption.
        d1 = one-c*r
        T = x*t/d1; Ru = c+x*x*r/d1; Rd = r+t*t*c/d1
        d2 = one-Rd*f
        source_floor = T*y/d2; source_reflected = Ru+T*T*f/d2
        source_canopy = one-source_floor-source_reflected
        # Separate cavity determinant and flux solution, not the product's two-layer loop.
        determinant = x*y+(c*y+x*f)*(t+a)+c*f*a*(a+2*t)
        canopy = a*x*(y+f*(a+2*t))/determinant
        floor = x*y*t/determinant
        reflected = c+x*x*(r*(y+f*(t+a))+f*t*t)/determinant
        assert max(abs(source_canopy-canopy), abs(source_floor-floor),
            abs(source_reflected-reflected)) < D('1e-70')
        optics = {'virtual_cover_transmittance': x, 'virtual_floor_transmittance': y,
            'canopy_transmittance': t, 'canopy_reflectance': r, 'canopy_single_pass_absorptance': a,
            'cover_canopy_transmittance': T, 'cover_canopy_reflectance_up': Ru,
            'cover_canopy_reflectance_down': Rd,
            'cover_canopy_absorptance_up': x*a/d1, 'cover_canopy_absorptance_down': a*(one+c*t/d1),
            'canopy_absorptance': canopy, 'floor_absorptance': floor, 'upward_reflectance': reflected}
        outside = v['outdoor_global_radiation']*v['solar_nir_fraction']
        available = (one-v['construction_interception_fraction'])*outside
        return {group: {k: str(q) for k, q in values.items()} for group, values in {
            'optics': optics, 'reflection_denominators': {'cover_canopy': d1, 'cover_canopy_floor': d2},
            'heat_components': {'canopy_absorbed_nir': available*canopy, 'floor_absorbed_nir': available*floor,
                'upward_virtual_nir': available*reflected,
                'construction_unallocated_nir': v['construction_interception_fraction']*outside},
            'diagnostics': {'outdoor_nir': outside, 'available_virtual_nir': available}}.items()}


def document():
    baseline = {'outdoor_global_radiation': 600, 'solar_nir_fraction': .5, 'leaf_area_index': 2,
        'nir_extinction_coefficient': .27, 'cover_nir_reflectance': .15,
        'canopy_nir_reflectance': .35, 'floor_nir_reflectance': .5,
        'construction_interception_fraction': .1}
    variations = [('nominal', {}), ('dark', {'outdoor_global_radiation': 0}),
        ('no-leaves', {'leaf_area_index': 0}), ('zero-extinction', {'nir_extinction_coefficient': 0}),
        ('lossless-canopy', {'canopy_nir_reflectance': 1}), ('black-canopy', {'canopy_nir_reflectance': 0}),
        ('reflective-cover', {'cover_nir_reflectance': 1}), ('reflective-floor', {'floor_nir_reflectance': 1}),
        ('transparent-cover', {'cover_nir_reflectance': 0}), ('black-floor', {'floor_nir_reflectance': 0}),
        ('construction-intercepts-all', {'construction_interception_fraction': 1}),
        ('no-NIR', {'solar_nir_fraction': 0}), ('sparse-canopy', {'leaf_area_index': 1e-16}),
        ('dense-canopy', {'leaf_area_index': 50}), ('near-reflectors-lossless', {
            'canopy_nir_reflectance': 1, 'cover_nir_reflectance': 1-2**-26, 'floor_nir_reflectance': 1-2**-27})]
    cases = []
    for name, changes in variations:
        values = {**baseline, **changes}
        scenario = {'input_id': 'synthetic-NIR-'+name, 'origin': 'synthetic',
            'values': {k: {'value': values[k], 'unit': unit} for k, unit in UNITS.items()}}
        cases.append({'case_id': name, 'scenario': scenario, 'expected_decimal': reference(scenario)})
    return {'fixture_version': 'crop-greenhouse-radiation-nir-reference-cases-v1',
        'scope': 'self_authored_synthetic_software_math_only', 'G0_G4': 'not_assessed',
        'generator_sha256': sha256(Path(__file__).read_bytes()).hexdigest(),
        'oracle': 'independent_Decimal80_ordered_source_and_expanded_cavity_no_app_import',
        'input_basis': 'exact_binary64_values', 'cases': cases}


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(); parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    with args.output.open('x') as output:
        output.write(json.dumps(document(), indent=2, sort_keys=True, allow_nan=False)+'\n')
