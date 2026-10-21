"""Independent direct logistic lengths, 800-digit Decimal, synthetic only."""
import argparse
from decimal import Decimal, localcontext
from datetime import datetime
import json
from pathlib import Path


def reference():
    changes = json.loads((Path(__file__).resolve().parents[1] /
        'fixtures/crop-internode-length-change-reference-v1.json').read_bytes())['cases']
    cases = []
    with localcontext() as context:
        context.prec = 800
        for index in (0, 1, 2, 3, 4, 5, 6, 8):
            p = changes[index]['inputs']
            exact = p['clock_state']['age_exact']
            age = Decimal(exact['numerator']) / Decimal(exact['denominator'])
            m, k, tm = [Decimal.from_float(float(p['curve']['values'][key]['value']))
                        for key in ('maximum_length', 'steepness', 'inflection_age')]
            length = m / (1 + (-k * (age - tm)).exp())
            end_age = age
            base = Decimal.from_float(float(p['clock_state']['base_temperature']['value']))
            for segment in p['segments']:
                duration = datetime.fromisoformat(segment['end_utc']) - datetime.fromisoformat(segment['start_utc'])
                seconds = duration.days * 86400 + duration.seconds
                end_age += (Decimal.from_float(float(segment['air_temperature']['value'])) - base) * seconds / 86400
            end_length = m / (1 + (-k * (end_age - tm)).exp())
            cases.append({'case_id': p['input_id'], 'inputs': {
                'input_id': p['input_id'], 'clock_state': p['clock_state'], 'curve': p['curve'],
                'initial_length': {'value': float(length), 'unit': 'm'}},
                'expected_length_m': str(length), 'expected_end_length_m': str(end_length), 'segments': p['segments']})
    return {'version': 'internode-length-state-reference-v1', 'precision': 800,
            'origin': 'synthetic_arithmetic_not_cultivar_parameters', 'cases': cases}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.write_text(json.dumps(reference(), indent=2, sort_keys=True) + '\n')
