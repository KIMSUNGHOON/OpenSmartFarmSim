"""Independent Decimal probes of a synthetic logistic area derivative.

No product module or external crop coefficients are used.
"""
import argparse
from decimal import Decimal, localcontext
import json
from pathlib import Path


def reference():
    cases = []
    probes = [
        ('symmetric', '.04', '.5', '4', [0, 2, 4, 6, 8]),
        ('fractional', '.0625', '.125', '7.25', [0, 3.5, 7.25, 11, 14.5]),
        ('wide', '.2', '.005', '120', [0, 60, 120, 180, 240]),
        ('exponent-overflow-naive', '1e308', '1', '1000', [0, 1000, 2000]),
        ('product-overflow-naive', '1e308', '4', '1', [1]),
        ('balanced-scales', '1e-300', '1e300', '0', [0]),
    ]
    with localcontext() as context:
        context.prec = 100
        for name, maximum, steepness, inflection, ages in probes:
            area, k, midpoint = map(Decimal, (maximum, steepness, inflection))
            for age in ages:
                exponential = (-k * (Decimal(str(age)) - midpoint)).exp()
                expected = k * area * exponential / (1 + exponential) ** 2
                identifier = f'synthetic-{name}-{age}'
                cases.append({'case_id': identifier, 'inputs': {
                    'input_id': identifier, 'origin': 'synthetic',
                    'thermal_age_basis': 'since_leaf_emergence', 'values': {
                        'thermal_age': {'value': age, 'unit': 'degC_day'},
                        'maximum_area': {'value': float(maximum), 'unit': 'm2'},
                        'steepness': {'value': float(steepness), 'unit': '1/degC_day'},
                        'inflection_age': {'value': float(inflection), 'unit': 'degC_day'},
                    }}, 'expected_m2_per_degC_day': str(expected)})
    return {'version': 'leaf-area-rate-decimal-reference-v1', 'precision': 100,
            'origin': 'synthetic_arithmetic_probes_not_crop_parameters',
            'contract': 'crop-leaf-expansion-rate-v1', 'cases': cases}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.write_text(json.dumps(reference(), indent=2, sort_keys=True) + '\n')
