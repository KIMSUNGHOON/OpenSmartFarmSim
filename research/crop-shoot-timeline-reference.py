"""Synthetic hand-derived event times; no model or event-inversion imports."""
import argparse
from datetime import datetime, timedelta
from math import gcd
import json
from pathlib import Path


def quantity(n, d=1, unit='degC_day'):
    common = gcd(n, d)
    return {'numerator': str(n // common), 'denominator': str(d // common), 'unit': unit}


def reference():
    cases = []
    definitions = [
        ('day', '2026-10-01T00:00:00Z', 0, (0,1), 5, (5,1), (5,1), [(86400,20)],
         [(5,1,28800,1), (10,1,57600,1), (15,1,86400,1)], (15,1), (20,1)),
        ('flat-first', '2026-10-01T00:00:00Z', 0, (0,1), 5, (1,2), (1,2), [(3600,5),(7200,20)],
         [(1,2,6480,1),(1,1,9360,1)], (5,4), (3,2)),
        ('flat-after-boundary', '2026-10-01T00:00:00Z', 0, (0,1), 0, (1,1), (1,1), [(3600,24),(3600,0)],
         [(1,1,3600,1)], (1,1), (2,1)),
        ('fractional-second', '2026-10-01T00:00:00Z', 0, (0,1), 0, (1,86400), (1,86400), [(1,3)],
         [(1,86400,1,3),(1,43200,2,3),(1,28800,1,1)], (1,28800), (1,21600)),
        ('resume-origin', '2026-10-01T00:00:00Z', 3600, (1,1), 0, (3,2), (1,2), [(3600,24)],
         [(3,2,5400,1),(2,1,7200,1)], (2,1), (5,2)),
        ('zero', '2026-10-01T00:00:00Z', 0, (0,1), 5, (1,1), (1,1), [(3600,5)],
         [], (0,1), (1,1)),
        ('leap', '2028-02-28T23:00:00Z', 0, (0,1), 0, (1,1), (1,1), [(7200,24)],
         [(1,1,3600,1),(2,1,7200,1)], (2,1), (3,1)),
    ]
    for name, origin, offset, age, base, threshold, step, program, manual_events, end_age, next_threshold in definitions:
        start = datetime.fromisoformat(origin)
        utc = lambda seconds: (start + timedelta(seconds=seconds)).strftime('%Y-%m-%dT%H:%M:%SZ')
        at = offset
        segments = []
        for duration, temperature in program:
            segments.append({'start_utc': utc(at), 'end_utc': utc(at+duration),
                             'air_temperature': {'value': temperature, 'unit': 'degC'}})
            at += duration
        state = {'origin': 'synthetic', 'age_basis': 'since_shoot_development_origin',
                 'shoot_id': 'synthetic-shoot', 'development_origin_id': 'synthetic-origin',
                 'schedule_id': 'synthetic-schedule-' + name, 'started_at': origin, 'at': utc(offset),
                 'base_temperature': {'value': float(base), 'unit': 'degC'}, 'age_exact': quantity(*age),
                 'next_threshold_exact': quantity(*threshold), 'phyllochron_exact': quantity(*step), 'next_sequence': 3}
        events = [{'sequence': 3+i, 'thermal_age_exact': quantity(n,d),
                   'elapsed_seconds_exact': quantity(sn,sd,'s'), 'utc_whole_second': utc(sn) if sd == 1 else None}
                  for i,(n,d,sn,sd) in enumerate(manual_events)]
        cases.append({'case_id': 'synthetic-' + name, 'inputs': {'input_id': name, 'state': state, 'segments': segments},
                      'events': events, 'checkpoint': {**state, 'at': utc(at), 'age_exact': quantity(*end_age),
                          'next_threshold_exact': quantity(*next_threshold), 'next_sequence': 3+len(events)}})
    return {'version': 'shoot-air-event-timeline-reference-v1', 'origin': 'synthetic_math_only',
            'method': 'hand-derived rational ages and elapsed seconds; calendar formatting only', 'cases': cases}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.write_text(json.dumps(reference(), indent=2, sort_keys=True) + '\n')
