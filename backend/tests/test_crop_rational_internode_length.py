from copy import deepcopy
from decimal import Decimal, localcontext
from fractions import Fraction
import json
from pathlib import Path

import pytest

from app.crop_rational_internode_length import (
    initialize_rational_internode_length, normalize_rational_internode_length_state,
    advance_rational_internode_length, RationalInternodeLengthHold,
)


def exact(n=0, d=1, unit='s'):
    value = Fraction(n, d)
    return {'numerator': str(value.numerator), 'denominator': str(value.denominator), 'unit': unit}


def curve():
    p = Path(__file__).resolve().parents[2] / 'fixtures/crop-internode-length-state-reference-v1.json'
    return json.loads(p.read_bytes())['cases'][0]['inputs']['curve']


def reference(age, c):
    with localcontext() as ctx:
        ctx.prec = 800
        a = Decimal(age.numerator) / Decimal(age.denominator)
        m, k, tm = (Decimal.from_float(float(c['values'][key]['value'])) for key in
                    ('maximum_length', 'steepness', 'inflection_age'))
        return m / (1 + (-k * (a - tm)).exp())


def initial(*, birth=Fraction(1, 3), at=None, age=Fraction(0), base=0, c=None):
    c = c or curve()
    return {'input_id': 'rational-length-initialize', 'clock_state': {
        'origin': 'synthetic', 'age_basis': 'since_internode_emergence',
        'temperature_basis': 'indoor_air_piecewise_constant', 'internode_id': 'explicit-node-3',
        'time_origin_utc': '2026-10-01T00:00:00Z',
        'emerged_elapsed_seconds_exact': exact(birth), 'at_elapsed_seconds_exact': exact(at if at is not None else birth),
        'base_temperature': {'value': base, 'unit': 'degC'}, 'age_exact': exact(age, unit='degC_day')},
        'curve': c, 'initial_length': {'value': float(reference(age, c)), 'unit': 'm'}}


def segment(start, end, air):
    return {'start_elapsed_seconds_exact': exact(start), 'end_elapsed_seconds_exact': exact(end),
            'air_temperature': {'value': air, 'unit': 'degC'}}


@pytest.mark.parametrize('birth,segments,age', [
    (Fraction(1, 3), [segment(Fraction(1, 3), 1, 3)], Fraction(1, 43200)),
    (Fraction(2, 3), [segment(Fraction(2, 3), 1, 3)], Fraction(1, 86400)),
    (Fraction(1, 3), [segment(Fraction(1, 3), Fraction(1, 2), 1), segment(Fraction(1, 2), 1, 3)], Fraction(1, 51840)),
    (Fraction(1, 3), [segment(Fraction(1, 3), 86400, 15)], Fraction(259199, 17280)),
    (Fraction(1, 3), [segment(Fraction(1, 3), 1, 0)], Fraction(0)),
])
def test_fractional_birth_independent_age_and_length(birth, segments, age):
    p = initial(birth=birth); before = deepcopy(p)
    start = initialize_rational_internode_length(inputs=p)
    request = {'input_id': 'rational-length-advance', 'state': start['state'], 'segments': segments}
    old = deepcopy(request)
    result = advance_rational_internode_length(inputs=request); state = result['state']
    assert state['clock_state']['age_exact'] == exact(age, unit='degC_day')
    assert state['length']['value'] == pytest.approx(float(reference(age, p['curve'])), rel=1e-12, abs=0)
    assert state['length']['unit'] == 'm' and state['anchor'] == start['state']['anchor']
    assert state['clock_state']['emerged_elapsed_seconds_exact'] == exact(birth)
    assert result['scope'] == 'software_research_only' and result['claim_scope'] == 'synthetic_crop_math_only'
    assert result['gates'] == 'not_assessed' and len(result['input_sha256']) == 64
    assert result['clock_model_version'] == 'internode-rational-air-thermal-clock-research-v1'
    assert result['point_model_version'] == 'internode-logistic-length-point-research-v1'
    assert len(result['clock_input_sha256']) == len(result['point_input_sha256']) == 64
    assert not {'length_change', 'emerged_at', 'utc_whole_second'} & set(result)
    assert p == before and request == old and advance_rational_internode_length(inputs=request) == result


def test_split_resume_and_normalization_preserve_canonical_state():
    p = initial(); p['initial_length']['value'] *= 1 + 5e-13
    start = initialize_rational_internode_length(inputs=p)['state']
    assert start['length']['value'] != start['anchor']['requested_length']['value']
    pieces = [segment(Fraction(1, 3), Fraction(1, 2), 1), segment(Fraction(1, 2), 1, 3)]
    whole = advance_rational_internode_length(inputs={'input_id': 'whole', 'state': start, 'segments': pieces})
    first = advance_rational_internode_length(inputs={'input_id': 'first', 'state': start, 'segments': pieces[:1]})
    second = advance_rational_internode_length(inputs={'input_id': 'second', 'state': first['state'], 'segments': pieces[1:]})
    assert whole['state'] == second['state']
    assert normalize_rational_internode_length_state(state=whole['state']) == whole['state']
    assert whole['input_sha256'] != second['input_sha256']
    p = initial(base=5); a = initialize_rational_internode_length(inputs=p)
    p['clock_state']['base_temperature']['value'] = 5.0
    assert initialize_rational_internode_length(inputs=p) == a


@pytest.mark.parametrize('change', ['missing', 'zero', 'negative', 'bool', 'inf', 'wrong-unit', 'mismatch',
                                  'observed', 'bad-clock', 'extra'])
def test_explicit_initialization_holds(change):
    p = initial()
    if change == 'missing': del p['initial_length']
    elif change in ('zero', 'negative', 'bool', 'inf', 'mismatch'):
        p['initial_length']['value'] = {'zero': 0, 'negative': -1, 'bool': True, 'inf': float('inf'), 'mismatch': .1}[change]
    elif change == 'wrong-unit': p['initial_length']['unit'] = 'cm'
    elif change == 'observed': p['clock_state']['origin'] = 'observed'
    elif change == 'bad-clock': p['clock_state']['emerged_elapsed_seconds_exact']['denominator'] = '0'
    else: p['unexpected'] = True
    with pytest.raises(RationalInternodeLengthHold): initialize_rational_internode_length(inputs=p)


@pytest.mark.parametrize('change', ['version', 'extra', 'length', 'length-unit', 'curve-hash', 'curve', 'anchor-extra',
    'anchor-clock-id', 'anchor-origin', 'anchor-base', 'anchor-birth', 'anchor-hash', 'anchor-canonical',
    'anchor-requested', 'anchor-after-current', 'anchor-age-after-current', 'same-time-different-age'])
def test_modified_state_is_held(change):
    start = initialize_rational_internode_length(inputs=initial())['state']
    state = advance_rational_internode_length(inputs={'input_id': 'prepare', 'state': start,
        'segments': [segment(Fraction(1, 3), 1, 3)]})['state']
    anchor = state['anchor']; clock = anchor['clock_state']
    if change == 'version': state['model_version'] = 'unknown'
    elif change == 'extra': state['extra'] = 0
    elif change == 'length': state['length']['value'] *= 2
    elif change == 'length-unit': state['length']['unit'] = 'cm'
    elif change == 'curve-hash': state['curve_sha256'] = '0' * 64
    elif change == 'curve': state['curve']['values']['maximum_length']['value'] *= 2
    elif change == 'anchor-extra': anchor['extra'] = 0
    elif change == 'anchor-clock-id': clock['internode_id'] = 'different-node'
    elif change == 'anchor-origin': clock['time_origin_utc'] = '2026-09-30T00:00:00Z'
    elif change == 'anchor-base': clock['base_temperature']['value'] = -1
    elif change == 'anchor-birth': clock['emerged_elapsed_seconds_exact'] = exact()
    elif change == 'anchor-hash': anchor['curve_sha256'] = '0' * 64
    elif change == 'anchor-canonical': anchor['canonical_length']['value'] *= 2
    elif change == 'anchor-requested': anchor['requested_length']['value'] *= 2
    elif change == 'anchor-after-current': clock['at_elapsed_seconds_exact'] = exact(2)
    elif change == 'anchor-age-after-current':
        clock['at_elapsed_seconds_exact'] = exact(Fraction(2, 3)); clock['age_exact'] = exact(1, unit='degC_day')
    else: clock['at_elapsed_seconds_exact'] = exact(1)
    with pytest.raises(RationalInternodeLengthHold): normalize_rational_internode_length_state(state=state)


@pytest.mark.parametrize('segments', [[], [segment(0, 1, 3)], [segment(Fraction(1, 3), 1, -1)],
    [segment(Fraction(1, 3), Fraction(1, 3), 3)], [segment(Fraction(1, 3), 1, True)]])
def test_forcing_holds_do_not_modify_previous_state(segments):
    state = initialize_rational_internode_length(inputs=initial())['state']; before = deepcopy(state)
    with pytest.raises(RationalInternodeLengthHold):
        advance_rational_internode_length(inputs={'input_id': 'bad-forcing', 'state': state, 'segments': segments})
    assert state == before
