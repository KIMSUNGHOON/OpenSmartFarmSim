"""Independent integer common-grid enumeration; no product/Fraction imports."""
import argparse
from math import gcd, lcm
import json
from pathlib import Path


def quantity(n, d=1):
    factor = gcd(n, d)
    return {'numerator': str(n // factor), 'denominator': str(d // factor), 'unit': 'degC_day'}


def reference():
    probes = [('before', (0,1), (29,2), (15,1), (10,1)),
              ('exact', (0,1), (15,1), (15,1), (10,1)),
              ('after', (0,1), (31,2), (15,1), (10,1)),
              ('multiple', (10,1), (55,1), (15,1), (10,1)),
              ('zero', (10,1), (10,1), (15,1), (10,1)),
              ('thirds', (1,6), (13,6), (1,2), (1,3)),
              ('large-age-tiny-step', (2**53,1), (2**53*10+3,10), (2**53*10+1,10), (1,10)),
              ('tiny', (0,1), (3,10**300), (1,10**300), (1,10**300))]
    cases = []
    for name, start, end, threshold, step in probes:
        grid = lcm(start[1], end[1], threshold[1], step[1])
        end_tick = end[0] * (grid // end[1])
        next_tick = threshold[0] * (grid // threshold[1])
        step_tick = step[0] * (grid // step[1])
        sequence = 5
        events = []
        while next_tick <= end_tick:
            events.append({'sequence': sequence, 'thermal_age_exact': quantity(next_tick, grid)})
            next_tick += step_tick
            sequence += 1
        state = {'origin': 'synthetic', 'age_basis': 'since_shoot_development_origin',
                 'shoot_id': 'synthetic-shoot', 'development_origin_id': 'synthetic-origin',
                 'schedule_id': 'synthetic-schedule-' + name, 'at_age_exact': quantity(*start),
                 'next_threshold_exact': quantity(*threshold), 'phyllochron_exact': quantity(*step),
                 'next_sequence': 5}
        cases.append({'case_id': 'synthetic-' + name, 'inputs': {'input_id': name, 'state': state,
                      'end_age_exact': quantity(*end)}, 'events': events,
                      'checkpoint': {**state, 'at_age_exact': quantity(*end),
                                     'next_threshold_exact': quantity(next_tick, grid), 'next_sequence': sequence}})
    return {'version': 'phytomer-thermal-events-reference-v1', 'origin': 'synthetic_math_only',
            'method': 'independent integer grid with iterative enumeration', 'cases': cases}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.write_text(json.dumps(reference(), indent=2, sort_keys=True) + '\n')
