"""Independent Decimal evaluation of Smolenova et al. 2025, Eq(4).

All parameter sets below are arithmetic probes, not fitted crop parameters.
"""
import argparse
from decimal import Decimal, localcontext
import json
from pathlib import Path


def reference():
    cases = []
    probes = [
        ('symmetric', '.12', '.05', '40', [0, 20, 40, 60, 80]),
        ('narrow', '4', '2', '3', [0, 1, 2, 3, 4, 5, 6]),
        ('wide', '2', '.005', '120', [0, 60, 120, 180, 240]),
        ('large-exponent', '1e308', '1', '1000', [0, 1000, 2000]),
    ]
    with localcontext() as context:
        context.prec = 100
        for name, maximum, steepness, inflection, ages in probes:
            length, k, midpoint = map(Decimal, (maximum, steepness, inflection))
            for age in ages:
                exponential = (-k * (Decimal(age) - midpoint)).exp()
                expected = k * length * exponential / (1 + exponential) ** 2
                cases.append({'case_id': f'synthetic-{name}-{age}', 'inputs': {
                    'input_id': f'synthetic-{name}-{age}', 'origin': 'synthetic',
                    'thermal_age_basis': 'since_internode_emergence', 'values': {
                        'thermal_age': {'value': age, 'unit': 'degC_day'},
                        'maximum_length': {'value': float(maximum), 'unit': 'm'},
                        'steepness': {'value': float(steepness), 'unit': '1/degC_day'},
                        'inflection_age': {'value': float(inflection), 'unit': 'degC_day'},
                    }}, 'expected_m_per_degC_day': str(expected)})
    return {'version': 'internode-elongation-decimal-reference-v1', 'precision': 100,
            'origin': 'synthetic_arithmetic_probes_not_crop_parameters',
            'equation': '10.1093/insilicoplants/diaf022:Eq4:dimension-reviewed-v1', 'cases': cases}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.write_text(json.dumps(reference(), indent=2, sort_keys=True) + '\n')
