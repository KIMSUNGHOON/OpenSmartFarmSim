"""Independent direct antiderivative differences with 800-digit Decimal."""
import argparse
from copy import deepcopy
from decimal import Decimal, localcontext
import json
from pathlib import Path


def reference():
    root = Path(__file__).resolve().parents[1]
    clocks = json.loads((root / 'fixtures/crop-morphology-thermal-clock-reference-v1.json').read_bytes())['cases']
    probes = []
    for index in (0, 1, 2, 4, 6):
        probes.append((f'ordinary-{index}', deepcopy(clocks[index]['inputs']), .12, .05, 40))
    tiny = deepcopy(clocks[5]['inputs'])
    tiny['state']['emerged_at'] = '2026-09-30T00:00:00Z'
    tiny['state']['age_exact'] = {'numerator': '20', 'denominator': '1', 'unit': 'degC_day'}
    probes.append(('tiny-thermal-increment', tiny, .12, .02, 20))
    for name, temperature, maximum, steepness, inflection in (
        ('negative-exponent-rescue', 1, 1e308, 1, 1000),
        ('whole-curve', 2000, .12, 1, 1000),
    ):
        clock = deepcopy(clocks[0]['inputs'])
        clock['state']['base_temperature']['value'] = 0
        clock['segments'][0]['air_temperature']['value'] = temperature
        probes.append((name, clock, maximum, steepness, inflection))
    tiny = deepcopy(clocks[5]['inputs'])
    tiny['state']['emerged_at'] = '2026-09-30T00:00:00Z'
    tiny['state']['age_exact'] = {'numerator': '1', 'denominator': '1', 'unit': 'degC_day'}
    tiny['state']['base_temperature']['value'] = 0
    tiny['segments'][0]['air_temperature']['value'] = float.fromhex('0x0.0000000000001p-1022')
    probes.append(('exact-age-difference-rescue', tiny, 1e308, 1, 1))
    cases = []
    with localcontext() as context:
        context.prec = 800
        from datetime import datetime
        for name, clock, maximum, steepness, inflection in probes:
            state = clock['state']
            a0 = Decimal(state['age_exact']['numerator']) / Decimal(state['age_exact']['denominator'])
            a1 = a0
            base = Decimal.from_float(float(state['base_temperature']['value']))
            for segment in clock['segments']:
                duration = datetime.fromisoformat(segment['end_utc']) - datetime.fromisoformat(segment['start_utc'])
                seconds = duration.days * 86400 + duration.seconds
                a1 += (Decimal.from_float(float(segment['air_temperature']['value'])) - base) * seconds / 86400
            m, k, tm = map(lambda value: Decimal.from_float(float(value)), (maximum, steepness, inflection))
            before = m / (1 + (-k * (a0 - tm)).exp())
            after = m / (1 + (-k * (a1 - tm)).exp())
            cases.append({'case_id': 'synthetic-' + name, 'inputs': {
                'input_id': 'synthetic-' + name, 'clock_state': state, 'segments': clock['segments'],
                'curve': {'profile_id': 'synthetic-' + name, 'origin': 'synthetic', 'values': {
                    'maximum_length': {'value': maximum, 'unit': 'm'},
                    'steepness': {'value': steepness, 'unit': '1/degC_day'},
                    'inflection_age': {'value': inflection, 'unit': 'degC_day'}}}},
                'expected_change_m': str(after - before)})
    return {'version': 'internode-length-change-reference-v1', 'precision': 800,
            'origin': 'synthetic_arithmetic_not_cultivar_parameters', 'cases': cases}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.write_text(json.dumps(reference(), indent=2, sort_keys=True) + '\n')
