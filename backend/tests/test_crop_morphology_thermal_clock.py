from copy import deepcopy
from datetime import datetime, timedelta
import json
from pathlib import Path

import pytest

from app.crop_morphology_thermal_clock import MorphologyClockHold, advance_internode_thermal_clock


REFERENCE = json.loads((Path(__file__).resolve().parents[2] /
    'fixtures/crop-morphology-thermal-clock-reference-v1.json').read_bytes())


def inputs(index=0):
    return deepcopy(REFERENCE['cases'][index]['inputs'])


@pytest.mark.parametrize('case', REFERENCE['cases'], ids=lambda c: c['case_id'])
def test_independent_decimal_age_and_identity_preservation(case):
    original = deepcopy(case['inputs'])
    result = advance_internode_thermal_clock(inputs=case['inputs'])
    assert result['thermal_age']['unit'] == 'degC_day'
    assert result['thermal_age']['value'] == pytest.approx(float(case['expected_age_degC_day']), rel=1e-12, abs=0)
    assert result['model_version'] == 'internode-air-thermal-clock-research-v1'
    assert result['scope'] == 'software_research_only' and result['gates'] == 'not_assessed'
    assert result['claim_scope'] == 'synthetic_crop_math_only'
    checkpoint = result['checkpoint']
    assert checkpoint['at'] == case['inputs']['segments'][-1]['end_utc']
    for key in ('internode_id', 'emerged_at', 'base_temperature', 'age_basis', 'temperature_basis', 'origin'):
        assert checkpoint[key] == case['inputs']['state'][key]
    assert case['inputs'] == original
    assert advance_internode_thermal_clock(inputs=case['inputs']) == result


def test_exact_fraction_and_every_interior_second_split_resume():
    p = inputs(1)
    p['segments'][0]['end_utc'] = '2026-10-02T00:00:41Z'
    whole = advance_internode_thermal_clock(inputs=p)
    for seconds in range(1, 41):
        at = (datetime.fromisoformat(p['state']['at']) + timedelta(seconds=seconds)).strftime('%Y-%m-%dT%H:%M:%SZ')
        prefix = deepcopy(p)
        prefix['segments'][0]['end_utc'] = at
        first = advance_internode_thermal_clock(inputs=prefix)
        suffix = deepcopy(p)
        suffix['state'] = first['checkpoint']
        suffix['segments'][0]['start_utc'] = at
        final = advance_internode_thermal_clock(inputs=suffix)
        assert final['checkpoint'] == whole['checkpoint']
        assert final['thermal_age'] == whole['thermal_age']
        assert final['input_sha256'] != whole['input_sha256']
    assert advance_internode_thermal_clock(inputs=inputs(4))['checkpoint']['age_exact'] == {
        'numerator': '1', 'denominator': '3', 'unit': 'degC_day'}


def test_variable_program_split_and_hash_binds_initial_state():
    p = inputs(2)
    full = advance_internode_thermal_clock(inputs=p)
    first = advance_internode_thermal_clock(inputs={**p, 'segments': p['segments'][:1]})
    second = advance_internode_thermal_clock(inputs={**p, 'state': first['checkpoint'], 'segments': p['segments'][1:]})
    assert second['checkpoint'] == full['checkpoint']
    p['state']['internode_id'] = 'synthetic-other-internode'
    other = advance_internode_thermal_clock(inputs=p)
    assert other['input_sha256'] != full['input_sha256']
    assert other['thermal_age'] == full['thermal_age']


@pytest.mark.parametrize('change', ['gap', 'overlap', 'reversed', 'initial-mismatch', 'offset',
    'fractional', 'leap-second', 'invalid-day', 'future-emergence'])
def test_rejects_time_gaps_reordering_and_noncanonical_UTC(change):
    p = inputs(2)
    if change == 'gap': p['segments'][1]['start_utc'] = '2026-10-02T06:00:01Z'
    elif change == 'overlap': p['segments'][1]['start_utc'] = '2026-10-02T05:59:59Z'
    elif change == 'reversed': p['segments'][0]['end_utc'] = p['segments'][0]['start_utc']
    elif change == 'initial-mismatch': p['state']['at'] = '2026-10-02T00:00:01Z'
    elif change == 'offset': p['segments'][0]['end_utc'] = '2026-10-02T06:00:00+00:00'
    elif change == 'fractional': p['segments'][0]['end_utc'] = '2026-10-02T06:00:00.1Z'
    elif change == 'leap-second': p['segments'][0]['end_utc'] = '2026-10-02T06:00:60Z'
    elif change == 'invalid-day': p['state']['emerged_at'] = '2026-02-29T00:00:00Z'
    elif change == 'future-emergence': p['state']['emerged_at'] = '2026-10-03T00:00:00Z'
    with pytest.raises(MorphologyClockHold, match='TIME_HOLD'):
        advance_internode_thermal_clock(inputs=p)


@pytest.mark.parametrize('change', ['age-missing', 'age-extra', 'age-negative', 'age-zero-denominator',
    'age-leading-zero', 'age-not-reduced', 'age-not-string', 'nonzero-emergence', 'age-unit',
    'state-extra', 'top-extra', 'segment-extra', 'origin', 'old-clock', 'old-temperature', 'id', 'not-object'])
def test_rejects_incomplete_or_unsupported_state(change):
    p = inputs()
    a = p['state']['age_exact']
    if change == 'age-missing': del p['state']['age_exact']
    elif change == 'age-extra': a['value'] = 0
    elif change == 'age-negative': a['numerator'] = '-1'
    elif change == 'age-zero-denominator': a['denominator'] = '0'
    elif change == 'age-leading-zero': a['numerator'] = '00'
    elif change == 'age-not-reduced': a.update(numerator='2', denominator='4')
    elif change == 'age-not-string': a['numerator'] = 0
    elif change == 'nonzero-emergence': a['numerator'] = '1'
    elif change == 'age-unit': a['unit'] = 'day'
    elif change == 'state-extra': p['state']['height'] = 1
    elif change == 'top-extra': p['temperature_sum'] = 1
    elif change == 'segment-extra': p['segments'][0]['quality'] = 'assumed'
    elif change == 'origin': p['state']['origin'] = 'reference_observation'
    elif change == 'old-clock': p['state']['age_basis'] = 'canopy_temperature_sum'
    elif change == 'old-temperature': p['state']['temperature_basis'] = 'canopy'
    elif change == 'id': p['state']['internode_id'] = ''
    elif change == 'not-object': p = None
    with pytest.raises(MorphologyClockHold):
        advance_internode_thermal_clock(inputs=p)


@pytest.mark.parametrize('where', ['base', 'air'])
@pytest.mark.parametrize('bad', ['unit', True, '20', float('nan'), float('inf'), 10**1000])
def test_rejects_invalid_temperatures(where, bad):
    p = inputs()
    q = p['state']['base_temperature'] if where == 'base' else p['segments'][0]['air_temperature']
    if bad == 'unit': q['unit'] = 'K'
    else: q['value'] = bad
    with pytest.raises(MorphologyClockHold):
        advance_internode_thermal_clock(inputs=p)


def test_below_base_is_held_instead_of_silently_clipping():
    p = inputs()
    p['segments'][0]['air_temperature']['value'] = 4
    with pytest.raises(MorphologyClockHold, match='TEMPERATURE_DOMAIN_HOLD'):
        advance_internode_thermal_clock(inputs=p)


@pytest.mark.parametrize('change', ['empty', 'too-many', 'large-carry', 'carry-growth', 'underflow', 'overflow'])
def test_capacity_and_unrepresentable_output_are_held(change):
    p = inputs(1)
    if change == 'empty': p['segments'] = []
    elif change == 'too-many': p['segments'] *= 513
    elif change == 'large-carry': p['state']['age_exact']['denominator'] = '1' + '0' * 1024
    elif change == 'carry-growth':
        p['state']['age_exact']['denominator'] = str(10**1023 + 1)
        p['state']['base_temperature']['value'] = 0
        p['segments'][0]['air_temperature']['value'] = float.fromhex('0x0.0000000000001p-1022')
        p['segments'][0]['end_utc'] = '2026-10-02T00:00:01Z'
    elif change == 'underflow':
        p['state']['age_exact']['denominator'] = '1' + '0' * 900
        p['segments'][0]['air_temperature']['value'] = 5
    elif change == 'overflow':
        p['state']['age_exact']['numerator'] = '1' + '0' * 400
    with pytest.raises(MorphologyClockHold):
        advance_internode_thermal_clock(inputs=p)
