from copy import deepcopy
from decimal import Decimal, localcontext
from fractions import Fraction
from hashlib import sha256
from math import fsum, inf, nan
import json
import os
from pathlib import Path

import psycopg
import pytest

from app import crop_harvest as harvest
from test_crop_cycle_calculation_current_query import prepared as stored_result, forbid_calculation
from test_crop_cycle_calculation_server_custody_farms import server_setup
from test_crop_cycle_calculation_farm_binding import setup as original_bound_setup
import test_crop_cycle_calculation_farm_binding as farm_fixture
import test_crop_cycle_calculation_server_custody_farms as server_fixture
from test_crop_startup_result_store import shifted
from test_crop_cycle_calculation_result_store_farms import counts, login_scope, original_login_scope
from test_farm_authoring_storage import authoring
from test_farm_replay_scenario import farm_setup
from login_database import login_database, assert_host_scram


SOURCE = {'result_id': 'owned:' + '0' * 64, 'input_root_sha256': '1' * 64,
          'artifact_sha256': '2' * 64, 'payload_sha256': '3' * 64,
          'math_manifest_sha256': '4' * 64}


def quantity(value, unit):
    return {'value': value, 'unit': unit}


def sample(at, carbon, number):
    return {'at': at, 'cumulative': {
        'terminal_carbohydrate': quantity(carbon, 'mg_CH2O/m2_floor'),
        'terminal_number': quantity(number, 'fruits_equivalent/m2_floor')}}


def event(at='2026-10-01T00:05:00Z', *, leaf=1000000, stem=2000000, fruit=True):
    carbon = [1, 2.5] + [0] * 48 if fruit else [0] * 50
    number = [.25, .75] + [0] * 48 if fruit else [0] * 50
    return {'at': at, 'input_id': 'owned-management-1', 'removed': {
        'leaf': quantity(leaf, 'mg_CH2O/m2_floor'),
        'stem_root': quantity(stem, 'mg_CH2O/m2_floor'),
        'fruit_carbohydrate': [quantity(v, 'mg_CH2O/m2_floor') for v in carbon],
        'fruit_number': [quantity(v, 'fruits_equivalent/m2_floor') for v in number]}}


def test_terminal_independent_interval_amounts_without_another_time_factor():
    before = sample('2026-10-01T00:00:00Z', 7, 2)
    after = sample('2026-10-01T00:05:00Z', 10, 3)
    row = harvest._terminal_row(SOURCE, (4, before), (5, after))
    assert row['kind'] == 'model_terminal_outflow'
    assert row['carbohydrate'] == quantity(3., 'mg_CH2O/m2_floor')
    assert row['number'] == quantity(1., 'fruits_equivalent/m2_floor')
    assert row['start_at'] == before['at'] and row['end_at'] == after['at']
    assert row['position']['samples'] == [4, 5] and row['cohorts'] is None


@pytest.mark.parametrize('fruit,carbon,number', [(True, 3.5, 1.), (False, 0., 0.)])
def test_leaf_stem_never_enter_fruit_removal(fruit, carbon, number):
    raw = event(fruit=fruit)
    row = harvest._event_row(SOURCE, (0, raw))
    assert row['kind'] == 'explicit_fruit_removal'
    assert row['carbohydrate'] == quantity(carbon, 'mg_CH2O/m2_floor')
    assert row['number'] == quantity(number, 'fruits_equivalent/m2_floor')
    assert row['cohorts']['fruit_carbohydrate'] == raw['removed']['fruit_carbohydrate']
    assert row['cohorts']['fruit_number'] == raw['removed']['fruit_number']
    assert row['position']['event'] == 0


def test_source_and_vectors_are_copied_and_row_identity_is_deterministic():
    source = deepcopy(SOURCE);raw = event()
    first = harvest._event_row(source, (8, raw))
    assert harvest._event_row(source, (8, raw)) == first
    assert harvest._event_row(source, (9, raw))['row_id'] != first['row_id']
    source['result_id'] = 'changed';raw['removed']['fruit_number'][0]['value'] = 99
    assert first['source'] == SOURCE and first['number']['value'] == 1.
    assert first['cohorts']['fruit_number'][0]['value'] == .25


@pytest.mark.parametrize('value', [-1, nan, inf, -inf, True, '3', None, 10**400])
def test_bad_physical_values_hold(value):
    before = sample('2026-10-01T00:00:00Z', 0, 0)
    after = sample('2026-10-01T00:05:00Z', value, 1)
    with pytest.raises(harvest.CropRemovalHold):
        harvest._terminal_row(SOURCE, (0, before), (1, after))


@pytest.mark.parametrize('change', ['carbon-unit', 'number-unit', 'extra-key', 'negative-delta',
                                  'same-time', 'reverse-time', 'invalid-date', 'noncanonical-time',
                                  'missing-index', 'reverse-index', 'bool-index'])
def test_terminal_units_order_and_missing_boundaries_hold(change):
    before = sample('2026-10-01T00:00:00Z', 2, 1)
    after = sample('2026-10-01T00:05:00Z', 3, 2);start, end = 0, 1
    if change == 'carbon-unit':after['cumulative']['terminal_carbohydrate']['unit'] = 'kg'
    elif change == 'number-unit':after['cumulative']['terminal_number']['unit'] = 'fruits'
    elif change == 'extra-key':after['cumulative']['terminal_number']['other'] = 0
    elif change == 'negative-delta':after['cumulative']['terminal_carbohydrate']['value'] = 1
    elif change == 'same-time':after['at'] = before['at']
    elif change == 'reverse-time':before['at'], after['at'] = after['at'], before['at']
    elif change == 'invalid-date':after['at'] = '2026-02-30T00:05:00Z'
    elif change == 'noncanonical-time':after['at'] = '2026-10-01T00:05:00+00:00'
    elif change == 'missing-index':end = 2
    elif change == 'reverse-index':start, end = 1, 0
    else:start = True
    with pytest.raises(harvest.CropRemovalHold):
        harvest._terminal_row(SOURCE, (start, before), (end, after))


@pytest.mark.parametrize('change', ['short-C', 'long-N', 'negative', 'nonfinite', 'bool', 'unit',
                                  'leaf-unit', 'stem-negative', 'overflow', 'missing-input-id'])
def test_event_vectors_and_numeric_failures_hold(change):
    raw = event();removed = raw['removed']
    if change == 'short-C':removed['fruit_carbohydrate'].pop()
    elif change == 'long-N':removed['fruit_number'].append(quantity(0, 'fruits_equivalent/m2_floor'))
    elif change == 'negative':removed['fruit_number'][0]['value'] = -1
    elif change == 'nonfinite':removed['fruit_number'][0]['value'] = nan
    elif change == 'bool':removed['fruit_number'][0]['value'] = True
    elif change == 'unit':removed['fruit_number'][0]['unit'] = 'fruits'
    elif change == 'leaf-unit':removed['leaf']['unit'] = 'kg'
    elif change == 'stem-negative':removed['stem_root']['value'] = -1
    elif change == 'overflow':
        removed['fruit_carbohydrate'][0]['value'] = 1e308
        removed['fruit_carbohydrate'][1]['value'] = 1e308
    else:del raw['input_id']
    with pytest.raises(harvest.CropRemovalHold):harvest._event_row(SOURCE, (0, raw))


class OwnedPages:
    def __init__(self, *, held=False):
        self.samples = [sample('2026-10-01T00:' + at + ':00Z', carbon, number)
                        for at, carbon, number in [('00', 0, 0), ('05', 1, .25), ('10', 4, 1), ('15', 8, 2)]]
        self.events = [event('2026-10-01T00:' + at + ':00Z') for at in ('00', '05', '15')]
        for i, row in enumerate(self.events):row['input_id'] = 'owned-event-' + str(i)
        packet = {'claim_scope': 'synthetic_crop_math_only', 'input_root_sha256': '1' * 64,
                  'artifact': {'sha256': '2' * 64, 'sample_count': 4, 'event_count': 3}}
        self.original = {'record': {'result_id': SOURCE['result_id'], 'payload_sha256': '3' * 64,
                                    'payload_raw': harvest._canonical(packet)},
                         'terminal': {'status': 'hold' if held else 'completed', 'manifest': {'owned': 'unit-software'}},
                         'identity': {'artifact_sha256': '2' * 64}, 'page': None}
        self.calls = []

    def __call__(self, *, kind=None, start=0, limit=None):
        value = deepcopy(self.original);self.calls.append((kind, start, limit))
        if kind is not None:
            rows = self.samples if kind == 'samples' else self.events
            records = deepcopy(rows[start:start + limit])
            value['page'] = {'kind': kind, 'start': start, 'next': start + len(records),
                             'total': len(rows), 'records': records}
        return value


def test_whole_and_split_windows_keep_each_initial_boundary_and_final_event_once():
    reader = OwnedPages()
    whole = list(harvest._read_ledger(reader, sample_page_size=2, event_page_size=1))
    split = list(harvest._read_ledger(reader, last_sample=1, sample_page_size=1))
    split += list(harvest._read_ledger(reader, first_sample=1, sample_page_size=1))
    assert split == whole and len({row['row_id'] for row in whole}) == len(whole) == 6
    assert [row['kind'] for row in whole] == ['explicit_fruit_removal', 'model_terminal_outflow',
        'explicit_fruit_removal', 'model_terminal_outflow', 'model_terminal_outflow', 'explicit_fruit_removal']
    assert sum(row['carbohydrate']['value'] for row in whole if row['kind'] == 'model_terminal_outflow') == 8
    assert sum(row['carbohydrate']['value'] for row in whole if row['kind'] == 'explicit_fruit_removal') == 10.5
    assert sum(row['number']['value'] for row in whole if row['kind'] == 'model_terminal_outflow') == 2
    assert sum(row['number']['value'] for row in whole if row['kind'] == 'explicit_fruit_removal') == 3


@pytest.mark.parametrize('size', [1, 2, 3, 64])
def test_page_size_does_not_change_rows_and_reader_remains_bounded(size):
    reader = OwnedPages()
    expected = list(harvest._read_ledger(reader))
    actual = list(harvest._read_ledger(reader, sample_page_size=size, event_page_size=1))
    assert actual == expected
    assert all(limit <= (64 if kind == 'samples' else 8) for kind, _, limit in reader.calls if kind)


def test_zero_length_windows_only_include_the_initial_event():
    first = list(harvest._read_ledger(OwnedPages(), last_sample=0))
    assert len(first) == 1 and first[0]['position']['event'] == 0
    assert list(harvest._read_ledger(OwnedPages(), first_sample=1, last_sample=1)) == []


@pytest.mark.parametrize('options', [{'first_sample': -1}, {'first_sample': True}, {'last_sample': 4},
    {'first_sample': 3, 'last_sample': 2}, {'sample_page_size': 65}, {'sample_page_size': True},
    {'event_page_size': 9}, {'event_page_size': 0}])
def test_invalid_windows_and_incomplete_future_hold(options):
    with pytest.raises(harvest.CropRemovalHold):list(harvest._read_ledger(OwnedPages(held=True), **options))


def test_confirmed_hold_past_keeps_source_status_and_never_becomes_completion():
    rows = list(harvest._read_ledger(OwnedPages(held=True), last_sample=2))
    assert rows and all(row['source']['source_status'] == 'hold' for row in rows)
    assert all(row['rights_or_gate_approval'] is False for row in rows)
    assert all(row['claim_scope'] == 'research_removal_math_only' for row in rows)


@pytest.mark.parametrize('change', ['empty', 'duplicate-cursor', 'gap', 'wrong-total', 'wrong-kind',
    'duplicate-time', 'reverse-time', 'different-result', 'different-root', 'different-identity', 'wrong-unit'])
def test_bad_or_mixed_pages_are_rejected(change):
    original = OwnedPages()
    def changed(**kwargs):
        value = original(**kwargs)
        if kwargs.get('kind') == 'samples' and kwargs.get('start') == 1:
            page = value['page']
            if change == 'empty':page.update(records=[], next=1)
            elif change == 'duplicate-cursor':page['start'] = 0
            elif change == 'gap':page['next'] += 1
            elif change == 'wrong-total':page['total'] += 1
            elif change == 'wrong-kind':page['kind'] = 'events'
            elif change == 'duplicate-time':page['records'][0]['at'] = original.samples[0]['at']
            elif change == 'reverse-time':page['records'][0]['at'] = '2026-09-30T23:59:59Z'
            elif change == 'different-result':value['record']['result_id'] = 'other:' + '0' * 64
            elif change == 'different-root':value['record']['payload_raw'] = b'{}'
            elif change == 'different-identity':value['identity']['artifact_sha256'] = '9' * 64
            else:page['records'][0]['cumulative']['terminal_number']['unit'] = 'kg'
        return value
    with pytest.raises(harvest.CropRemovalHold):
        list(harvest._read_ledger(changed, sample_page_size=1))


def test_late_source_withdrawal_cannot_finish_a_window():
    original = OwnedPages();summaries = []
    def changed(**kwargs):
        value = original(**kwargs)
        if not kwargs:
            summaries.append(True)
            if len(summaries) == 2:value['identity']['artifact_sha256'] = '9' * 64
        return value
    with pytest.raises(harvest.CropRemovalHold):list(harvest._read_ledger(changed))


def test_public_entry_rejects_arbitrary_rows_or_approval_objects():
    for reader in (OwnedPages(), object(), {'approved': True}):
        with pytest.raises(harvest.CropRemovalHold):
            list(harvest.iter_removal_ledger(reader, 'tenant-1', SOURCE['result_id'], {}))


def mass_values(carbon=12., count=3., eta=1.25, dmc=.125):
    return harvest._mass_values(quantity(carbon, 'mg_CH2O/m2_floor'),
        quantity(count, 'fruits_equivalent/m2_floor'), quantity(eta, 'mg_DM/mg_CH2O'),
        quantity(dmc, 'kg_DM/kg_FW'))


def test_explicit_mass_units_independent_values_and_inverse():
    result = mass_values()
    assert result['dry_matter'] == quantity(.000015, 'kg_DM/m2_floor')
    assert result['fresh_matter'] == quantity(.00012, 'kg_FW/m2_floor')
    assert result['fresh_mass_per_equivalent'] == quantity(.00004, 'kg_FW/fruit_equivalent')
    with localcontext() as ctx:
        ctx.prec = 80
        inverse = Decimal(str(result['fresh_matter']['value'])) * Decimal('.125') * 1_000_000 / Decimal('1.25')
    assert inverse == 12


@pytest.mark.parametrize('carbon,count,eta,dmc', [(1e308, 1, 2, .5),
    (1e-310, 1, 1e300, .25), (1e300, 1e300, 1e-300, .5), (4, .02, .8, .2)])
def test_mass_extremes_round_from_exact_input_floats_against_decimal(carbon, count, eta, dmc):
    result = mass_values(carbon, count, eta, dmc)
    with localcontext() as ctx:
        ctx.prec = 2200
        c, n, e, d = (Decimal.from_float(float(v)) for v in (carbon, count, eta, dmc))
        dry = c * e / 1_000_000;fresh = dry / d
        expected = [float(dry), float(fresh), float(fresh / n)]
    assert [result[key]['value'] for key in ('dry_matter', 'fresh_matter', 'fresh_mass_per_equivalent')] == expected


@pytest.mark.parametrize('carbon,count,eta,dmc', [(1e-320, 1, 1, .1),
    (1e308, 1, 1e308, .5), (1, 1, 1, 5e-324), (1, 5e-324, 1, .5),
    (1e-300, 1e308, 1, .5), (1, 1, 0, .5), (1, 1, 1, 0),
    (1, 1, 1, 1.01), (1, 1, True, .5), (1, 1, 1, nan), (-1, 1, 1, .5)])
def test_mass_unrepresentable_or_invalid_values_hold(carbon, count, eta, dmc):
    with pytest.raises(harvest.CropRemovalHold):mass_values(carbon, count, eta, dmc)


def test_zero_mass_and_zero_equivalent_have_distinct_meanings():
    assert mass_values(0, 1)['fresh_mass_per_equivalent']['value'] == 0
    assert mass_values(1, 0)['fresh_mass_per_equivalent']['value'] is None
    assert mass_values(0, 0)['dry_matter']['value'] == 0
    with pytest.raises(harvest.CropRemovalHold):mass_values(0, 0, dmc=0)


def test_mass_percent_and_other_area_or_quantity_units_are_not_substituted():
    valid = [quantity(12, 'mg_CH2O/m2_floor'), quantity(3, 'fruits_equivalent/m2_floor'),
             quantity(1.25, 'mg_DM/mg_CH2O'), quantity(.125, 'kg_DM/kg_FW')]
    for index, unit in enumerate(['mg_CH2O/m2_crop', 'fruits', '1', '%']):
        wrong = deepcopy(valid);wrong[index]['unit'] = unit
        with pytest.raises(harvest.CropRemovalHold):harvest._mass_values(*wrong)


def mass_profile(source, *, split=False):
    first = {'segment_id': 'owned-first', 'start_at': '2026-10-01T00:00:00Z',
             'end_at': '2026-10-01T00:15:00Z', 'eta': quantity(1., 'mg_DM/mg_CH2O'),
             'dmc': quantity(.5, 'kg_DM/kg_FW')}
    segments = [first]
    if split:
        first['end_at'] = '2026-10-01T00:05:00Z'
        segments.append({**deepcopy(first), 'segment_id': 'owned-second',
            'start_at': first['end_at'], 'end_at': '2026-10-01T00:15:00Z',
            'dmc': quantity(.25, 'kg_DM/kg_FW')})
    return {'version': 'crop-removal-mass-parameters-v1', 'parameter_id': 'owned-synthetic-mass',
            'revision': 'r1', 'origin': 'synthetic', 'evidence_level': 'assumed',
            'evidence_id': 'owned-algebra-fixture', 'available_at': '2026-09-30T00:00:00Z',
            'source': deepcopy(source), 'population': {'population_id': 'owned-model-fruit',
            'scope': 'all_model_fruit_cohorts', 'basis': 'm2_floor', 'basis_evidence_id': 'owned-model-floor'},
            'policy': 'constant_per_original_interval', 'segments': segments}


def test_mass_profile_boundaries_and_interval_sum_not_average_DMC():
    removals = list(harvest._read_ledger(OwnedPages()))
    raw = harvest._canonical(mass_profile(removals[0]['source'], split=True))
    parameters = harvest._mass_parameters(raw)
    rows = [harvest._mass_row(row, parameters) for row in removals]
    assert [row['parameters']['segment']['segment_id'] for row in rows] == ['owned-first'] * 2 + ['owned-second'] * 4
    assert fsum(row['dry_matter']['value'] for row in rows) == pytest.approx(.0000185)
    assert fsum(row['fresh_matter']['value'] for row in rows) == pytest.approx(.000065)
    assert all(row['parameters']['sha256'] == sha256(raw).hexdigest() for row in rows)
    assert [row['removal'] for row in rows] == removals and len({row['row_id'] for row in rows}) == 6
    assert harvest._mass_row(removals[0], parameters) == rows[0]
    rows[0]['parameters']['segment']['dmc']['value'] = 1
    assert parameters[0]['segments'][0]['dmc']['value'] == .5


@pytest.mark.parametrize('change', ['eta-missing', 'dmc-missing', 'population-missing', 'basis-missing',
    'wrong-area', 'wrong-population', 'real-origin', 'approved-evidence', 'empty-evidence',
    'wrong-policy', 'missing-available', 'extra-approval', 'duplicate-segment', 'gap', 'overlap',
    'reverse-time', 'percent', 'empty-segments', 'bad-hash'])
def test_mass_profile_incomplete_or_unsupported_evidence_holds(change):
    row = harvest._event_row({**SOURCE, 'source_status': 'completed'}, (0, event()))
    profile = mass_profile(row['source'], split=True);segment = profile['segments'][0]
    if change == 'eta-missing':del segment['eta']
    elif change == 'dmc-missing':del segment['dmc']
    elif change == 'population-missing':del profile['population']['population_id']
    elif change == 'basis-missing':del profile['population']['basis_evidence_id']
    elif change == 'wrong-area':profile['population']['basis'] = 'm2_crop'
    elif change == 'wrong-population':profile['population']['scope'] = 'selected_grade'
    elif change == 'real-origin':profile['origin'] = 'measured'
    elif change == 'approved-evidence':profile['evidence_level'] = 'approved'
    elif change == 'empty-evidence':profile['evidence_id'] = ''
    elif change == 'wrong-policy':profile['policy'] = 'interpolate'
    elif change == 'missing-available':del profile['available_at']
    elif change == 'extra-approval':profile['approved'] = True
    elif change == 'duplicate-segment':profile['segments'][1]['segment_id'] = segment['segment_id']
    elif change == 'gap':profile['segments'][1]['start_at'] = '2026-10-01T00:06:00Z'
    elif change == 'overlap':profile['segments'][1]['start_at'] = '2026-10-01T00:04:00Z'
    elif change == 'reverse-time':segment['end_at'] = segment['start_at']
    elif change == 'percent':segment['dmc']['unit'] = '%'
    elif change == 'empty-segments':profile['segments'] = []
    else:profile['source']['artifact_sha256'] = 'invalid'
    with pytest.raises(harvest.CropRemovalHold):harvest._mass_parameters(harvest._canonical(profile))


def test_mass_source_or_time_mismatch_and_unresolved_interval_holds():
    removals = list(harvest._read_ledger(OwnedPages()));profile = mass_profile(removals[0]['source'], split=True)
    bad = deepcopy(profile);bad['source']['result_id'] = 'different'
    with pytest.raises(harvest.CropRemovalHold):harvest._mass_row(removals[0], harvest._mass_parameters(harvest._canonical(bad)))
    profile['segments'][0]['end_at'] = profile['segments'][1]['start_at'] = '2026-10-01T00:07:00Z'
    with pytest.raises(harvest.CropRemovalHold):harvest._mass_row(removals[3], harvest._mass_parameters(harvest._canonical(profile)))
    profile['segments'] = [profile['segments'][1]]
    with pytest.raises(harvest.CropRemovalHold):harvest._mass_row(removals[0], harvest._mass_parameters(harvest._canonical(profile)))


def test_mass_parameter_bytes_are_canonical_bounded_and_reject_duplicate_keys():
    for raw in (b'{"version":1,"version":2}', b'{}\n', b' ' * 262145, bytearray(b'{}')):
        with pytest.raises(harvest.CropRemovalHold):harvest._mass_parameters(raw)


def test_streamed_mass_and_separate_kind_totals_preserve_split_and_paging():
    reader = OwnedPages();source = list(harvest._read_ledger(reader))[0]['source']
    raw = harvest._canonical(mass_profile(source, split=True))
    whole = list(harvest._read_mass(reader, raw, sample_page_size=1, event_page_size=1))
    split = list(harvest._read_mass(reader, raw, last_sample=1))
    split += list(harvest._read_mass(reader, raw, first_sample=1))
    assert split == whole
    result = harvest._mass_totals(iter(whole), harvest._mass_parameters(raw))
    terminal = result['totals_by_kind']['model_terminal_outflow']
    events = result['totals_by_kind']['explicit_fruit_removal']
    assert terminal['rows'] == events['rows'] == 3
    assert terminal['fresh_matter']['value'] == pytest.approx(.000030)
    assert events['fresh_matter']['value'] == pytest.approx(.000035)
    assert result['row_count'] == 6 and result['rights_or_gate_approval'] is False
    assert result['row_chain_sha256'] == sha256(b''.join(harvest._canonical(row) + b'\n' for row in whole)).hexdigest()
    held = OwnedPages(held=True);held_raw = harvest._canonical(mass_profile(harvest._source(held())))
    assert all(row['removal']['source']['source_status'] == 'hold' for row in harvest._read_mass(held, held_raw))


def test_empty_mass_window_still_verifies_source_and_requires_parameters():
    reader = OwnedPages();profile = mass_profile(harvest._source(reader()))
    assert list(harvest._read_mass(reader, harvest._canonical(profile), first_sample=1, last_sample=1)) == []
    profile['source']['result_id'] = 'foreign'
    with pytest.raises(harvest.CropRemovalHold):
        list(harvest._read_mass(reader, harvest._canonical(profile), first_sample=1, last_sample=1))
    with pytest.raises(harvest.CropRemovalHold):list(harvest._read_mass(reader, b'{}', first_sample=1, last_sample=1))


def test_late_mass_read_withdrawal_cannot_return_a_completed_summary():
    reader = OwnedPages();raw = harvest._canonical(mass_profile(harvest._source(reader())))
    summaries = []
    def withdrawn(**kwargs):
        value = reader(**kwargs)
        if not kwargs:
            summaries.append(True)
            if len(summaries) == 4:value['identity']['artifact_sha256'] = '9' * 64
        return value
    with pytest.raises(harvest.CropRemovalHold):
        harvest._mass_totals(harvest._read_mass(withdrawn, raw), harvest._mass_parameters(raw))


def test_mass_totals_overflow_holds_and_public_entry_rejects_arbitrary_approval():
    reader = OwnedPages();raw = harvest._canonical(mass_profile(harvest._source(reader())))
    rows = list(harvest._read_mass(reader, raw));rows[0]['fresh_matter']['value'] = 1e308
    rows[2]['fresh_matter']['value'] = 1e308
    with pytest.raises(harvest.CropRemovalHold):harvest._mass_totals(iter(rows), harvest._mass_parameters(raw))
    for arbitrary in (reader, {'approved': True}, object()):
        with pytest.raises(harvest.CropRemovalHold):
            list(harvest.iter_removal_mass(arbitrary, 'tenant-1', SOURCE['result_id'], {}, raw))


def test_allocation_decimal_fractions_and_exact_portions_conserve_original():
    reader = OwnedPages();raw = harvest._canonical(mass_profile(harvest._source(reader())))
    mass = next(harvest._read_mass(reader, raw))
    weights = [harvest._allocation_fraction(quantity(value, '1')) for value in ('0.1', '0.9')]
    assert sum(weights) == 1
    portions = [harvest._portion(mass, weight) for weight in weights]
    with localcontext() as ctx:
        ctx.prec = 2200
        for key, original in [('carbohydrate', mass['removal']['carbohydrate']),
                              ('number', mass['removal']['number']),
                              ('dry_matter', mass['dry_matter']), ('fresh_matter', mass['fresh_matter'])]:
            exact = [Decimal(part[key]['exact']['numerator']) / Decimal(part[key]['exact']['denominator']) for part in portions]
            assert sum(exact) == Decimal.from_float(original['value'])
            assert exact[0] == Decimal.from_float(original['value']) * Decimal('.1')
            assert [part[key]['value'] for part in portions] == [float(value) for value in exact]


@pytest.mark.parametrize('value', ['0', '-.1', '1.01', 'nan', '1/2', '.5', '0.0000000000000000001', .5, True, None])
def test_allocation_fraction_invalid_or_ambiguous_values_hold(value):
    with pytest.raises(harvest.CropRemovalHold):harvest._allocation_fraction(quantity(value, '1'))


def test_allocation_quantity_rounding_is_explicit_and_numeric_failures_hold():
    value = harvest._rational_quantity(Fraction(-1, 10), 'kg_FW/m2_floor')
    assert value['value'] == -.1 and value['exact'] == {'numerator': '-1', 'denominator': '10'}
    for value in (Fraction(1, 10**400), Fraction(10**400)):
        with pytest.raises(harvest.CropRemovalHold):harvest._rational_quantity(value, 'kg_FW/m2_floor')


def allocation_profile(parameters, last_sample=3, last_event=2):
    mass, digest = parameters
    def rule(name, purpose, fraction, selector):
        return {'assignment_id': name, 'purpose': purpose, 'fraction': quantity(fraction, '1'), 'selector': selector}
    terminal = {'kind': 'model_terminal_outflow', 'first_sample': 0, 'last_sample': last_sample}
    initial = {'kind': 'explicit_fruit_removal', 'event': 0}
    return {'version': 'crop-harvest-allocation-v1', 'allocation_id': 'owned-allocation', 'revision': '1',
        'origin': 'synthetic', 'evidence_level': 'assumed', 'evidence_id': 'owned-allocation-arithmetic',
        'available_at': '2026-09-30T00:00:00Z', 'source': deepcopy(mass['source']),
        'population': deepcopy(mass['population']), 'mass_parameter_sha256': digest,
        'policy': 'proportional_original_population', 'rules': [
            rule('terminal-harvest', 'harvest', '0.6', terminal),
            rule('terminal-thinning', 'thinning', '0.2', {**terminal, 'last_sample': 1}),
            rule('initial-harvest', 'harvest', '0.1', initial),
            rule('initial-sampling', 'sampling', '0.2', initial),
            rule('initial-thinning', 'thinning', '0.1', initial),
            rule('last-disposal', 'disposal', '0.5', {'kind': 'explicit_fruit_removal', 'event': last_event})],
        'observations': [{'observation_id': 'owned-observation', 'origin': 'synthetic', 'evidence_level': 'assumed',
            'evidence_id': 'owned-comparison-fixture', 'available_at': '2026-10-02T00:00:00Z',
            'start_at': mass['segments'][0]['start_at'], 'end_at': mass['segments'][-1]['end_at'],
            'assignment_ids': ['terminal-harvest', 'initial-harvest'],
            'fresh_matter': quantity(.000012, 'kg_FW/m2_floor')}]}


def test_allocation_parameters_bind_population_mass_and_confirmed_source_positions():
    reader = OwnedPages();parameters = harvest._mass_parameters(harvest._canonical(mass_profile(harvest._source(reader()))))
    profile = allocation_profile(parameters);raw = harvest._canonical(profile)
    assert harvest._allocation_parameters(raw, parameters) == (profile, sha256(raw).hexdigest())
    harvest._allocation_scope(profile, reader())
    # Adjacent ranges may each allocate 100%; they do not overlap an original interval.
    profile['observations'] = [];profile['rules'] = profile['rules'][:2]
    profile['rules'][0]['fraction']['value'] = '1';profile['rules'][0]['selector']['last_sample'] = 1
    profile['rules'][1]['fraction']['value'] = '1';profile['rules'][1]['selector'].update(first_sample=1, last_sample=3)
    harvest._allocation_parameters(harvest._canonical(profile), parameters)


@pytest.mark.parametrize('change', ['terminal-overlap', 'event-overlap', 'duplicate-id', 'bad-purpose',
    'bool-index', 'empty-range', 'bad-kind', 'source', 'population', 'mass-hash', 'real-profile', 'real-observation',
    'bad-period', 'unknown-assignment', 'duplicate-observation-link', 'nonharvest-link', 'duplicate-observation',
    'unknown-field', 'oversize-rules', 'oversize-observations', 'wrong-observed-unit', 'missing-evidence'])
def test_allocation_invalid_binding_overlap_or_observation_holds(change):
    reader = OwnedPages();parameters = harvest._mass_parameters(harvest._canonical(mass_profile(harvest._source(reader()))))
    p = allocation_profile(parameters);rules = p['rules'];observation = p['observations'][0]
    if change == 'terminal-overlap':rules[1]['fraction']['value'] = '0.5'
    elif change == 'event-overlap':rules[2]['fraction']['value'] = '0.9'
    elif change == 'duplicate-id':rules[1]['assignment_id'] = rules[0]['assignment_id']
    elif change == 'bad-purpose':rules[0]['purpose'] = 'sales'
    elif change == 'bool-index':rules[2]['selector']['event'] = True
    elif change == 'empty-range':rules[0]['selector']['last_sample'] = 0
    elif change == 'bad-kind':rules[0]['selector']['kind'] = 'harvest'
    elif change == 'source':p['source']['artifact_sha256'] = '9' * 64
    elif change == 'population':p['population']['basis'] = 'm2_canopy'
    elif change == 'mass-hash':p['mass_parameter_sha256'] = '9' * 64
    elif change == 'real-profile':p['origin'] = 'measured'
    elif change == 'real-observation':observation['origin'] = 'measured'
    elif change == 'bad-period':observation['start_at'] = '2026-10-03T00:00:00Z'
    elif change == 'unknown-assignment':observation['assignment_ids'] = ['unknown']
    elif change == 'duplicate-observation-link':observation['assignment_ids'].append('terminal-harvest')
    elif change == 'nonharvest-link':observation['assignment_ids'].append('initial-sampling')
    elif change == 'duplicate-observation':p['observations'].append(deepcopy(observation))
    elif change == 'unknown-field':p['approved'] = True
    elif change == 'oversize-rules':p['rules'] *= 50
    elif change == 'oversize-observations':p['observations'] *= 65
    elif change == 'wrong-observed-unit':observation['fresh_matter']['unit'] = 'kg'
    else:observation['evidence_id'] = ''
    with pytest.raises(harvest.CropRemovalHold):harvest._allocation_parameters(harvest._canonical(p), parameters)


def assert_allocation_arithmetic(rows, summary, profile):
    def exact(value):
        return Decimal(value['exact']['numerator']) / Decimal(value['exact']['denominator'])
    with localcontext() as ctx:
        ctx.prec = 2200
        for row in rows:
            mass = row['mass'];original = {**mass['removal'], **{key: mass[key] for key in ('dry_matter', 'fresh_matter')}}
            weights = [Decimal(part['fraction']['value']) for part in row['allocations']]
            weights.append(Decimal(1) - sum(weights, Decimal(0)))
            assert exact(row['unassigned']['fraction']) == weights[-1]
            for key in ('carbohydrate', 'number', 'dry_matter', 'fresh_matter'):
                portions = [part['quantities'][key] for part in row['allocations'] + [row['unassigned']]]
                source = Decimal.from_float(original[key]['value'])
                assert sum((exact(part) for part in portions), Decimal(0)) == source
                for part, weight in zip(portions, weights, strict=True):
                    assert exact(part) == source * weight and part['value'] == float(source * weight)
                    assert part['unit'] == original[key]['unit']
        for kind, purposes in summary['totals_by_kind_and_purpose'].items():
            for purpose, total in purposes.items():
                parts = [part for row in rows if row['mass']['removal']['kind'] == kind
                         for part in row['allocations'] + [{'purpose': 'unassigned', **row['unassigned']}]
                         if part['purpose'] == purpose]
                assert total['rows'] == len(parts)
                for key, quantity in total['quantities'].items():
                    value = sum((exact(part['quantities'][key]) for part in parts), Decimal(0))
                    assert exact(quantity) == value and quantity['value'] == float(value)
        for comparison in summary['observation_comparisons']:
            if comparison['status'] != 'compared_synthetic_fixture':continue
            observation = comparison['observation']
            model = sum((exact(part['quantities']['fresh_matter']) for row in rows for part in row['allocations']
                         if part['assignment_id'] in observation['assignment_ids']), Decimal(0))
            assert exact(comparison['modeled_fresh_matter']) == model
            difference = Decimal.from_float(observation['fresh_matter']['value']) - model
            assert exact(comparison['observed_minus_modeled']) == difference
            assert comparison['observed_minus_modeled']['value'] == float(difference)
    assert summary['row_count'] == len(rows)
    assert summary['allocation_parameters'] == profile
    assert summary['row_chain_sha256'] == sha256(b''.join(harvest._canonical(row) + b'\n' for row in rows)).hexdigest()


def test_allocation_whole_split_pages_exact_conservation_and_separate_observation():
    reader = OwnedPages();raw = harvest._canonical(mass_profile(harvest._source(reader()), split=True))
    parameters = harvest._mass_parameters(raw);profile = allocation_profile(parameters);allocation = harvest._canonical(profile)
    rows = list(harvest._read_allocations(reader, raw, allocation))
    assert rows == list(harvest._read_allocations(reader, raw, allocation, last_sample=1)) + list(
        harvest._read_allocations(reader, raw, allocation, first_sample=1))
    assert rows == list(harvest._read_allocations(reader, raw, allocation, sample_page_size=1, event_page_size=1))
    assert len({row['row_id'] for row in rows}) == len(rows) == 6
    assert [row['mass'] for row in rows] == list(harvest._read_mass(reader, raw))
    assert [part['assignment_id'] for part in rows[0]['allocations']] == ['initial-harvest', 'initial-sampling', 'initial-thinning']
    assert [part['assignment_id'] for part in rows[1]['allocations']] == ['terminal-harvest', 'terminal-thinning']
    assert rows[2]['allocations'] == [] and rows[2]['unassigned']['fraction']['value'] == 1
    assert rows[-1]['allocations'][0]['purpose'] == 'disposal'
    summary = harvest._allocation_totals(iter(rows), harvest._allocation_parameters(allocation, parameters))
    assert_allocation_arithmetic(rows, summary, profile)
    assert summary['observation_comparisons'][0]['status'] == 'compared_synthetic_fixture'
    assert all(row['rights_or_gate_approval'] is False for row in rows)
    assert all(row['claim_scope'] == 'synthetic_harvest_allocation_math_only' for row in rows)
    assert all(limit <= (64 if kind == 'samples' else 8) for kind, _, limit in reader.calls if kind)


@pytest.mark.parametrize('window', [{'last_sample': 1}, {'first_sample': 1}, {'first_sample': 1, 'last_sample': 1}])
def test_observation_partial_window_is_explicit_not_split_or_added(window):
    reader = OwnedPages();raw = harvest._canonical(mass_profile(harvest._source(reader())))
    parameters = harvest._mass_parameters(raw);allocation = harvest._canonical(allocation_profile(parameters))
    summary = harvest._allocation_totals(harvest._read_allocations(reader, raw, allocation, **window),
                                         harvest._allocation_parameters(allocation, parameters))
    comparison = summary['observation_comparisons'][0]
    assert comparison['status'] == 'incomplete_selected_window'
    assert comparison['modeled_fresh_matter'] is comparison['observed_minus_modeled'] is None
    assert comparison['observation']['fresh_matter']['value'] == .000012


def test_no_rules_preserves_every_amount_as_unassigned_and_hold_stays_hold():
    reader = OwnedPages(held=True);raw = harvest._canonical(mass_profile(harvest._source(reader())))
    parameters = harvest._mass_parameters(raw);profile = allocation_profile(parameters)
    profile.update(rules=[], observations=[]);allocation = harvest._canonical(profile)
    rows = list(harvest._read_allocations(reader, raw, allocation))
    assert all(row['allocations'] == [] and row['unassigned']['fraction']['value'] == 1 for row in rows)
    assert all(row['mass']['removal']['source']['source_status'] == 'hold' for row in rows)
    summary = harvest._allocation_totals(iter(rows), harvest._allocation_parameters(allocation, parameters))
    assert_allocation_arithmetic(rows, summary, profile)


@pytest.mark.parametrize('kind', ['terminal', 'event'])
def test_allocation_missing_future_selector_rejected_even_for_empty_window(kind):
    reader = OwnedPages(held=True);raw = harvest._canonical(mass_profile(harvest._source(reader())))
    parameters = harvest._mass_parameters(raw);profile = allocation_profile(parameters)
    if kind == 'terminal':profile['rules'][0]['selector']['last_sample'] = 4
    else:profile['rules'][-1]['selector']['event'] = 3
    with pytest.raises(harvest.CropRemovalHold):
        list(harvest._read_allocations(reader, raw, harvest._canonical(profile), first_sample=1, last_sample=1))


def test_observation_period_mismatch_and_final_authority_withdrawal_hold_summary():
    reader = OwnedPages();raw = harvest._canonical(mass_profile(harvest._source(reader())))
    mass = harvest._mass_parameters(raw);profile = allocation_profile(mass)
    profile['observations'][0]['start_at'] = '2026-10-01T00:01:00Z';allocation = harvest._canonical(profile)
    with pytest.raises(harvest.CropRemovalHold):
        harvest._allocation_totals(harvest._read_allocations(reader, raw, allocation), harvest._allocation_parameters(allocation, mass))
    profile['observations'] = [];allocation = harvest._canonical(profile);summaries = []
    def withdrawn(**kwargs):
        value = reader(**kwargs)
        if not kwargs:
            summaries.append(True)
            if len(summaries) == 6:value['identity']['artifact_sha256'] = '9' * 64
        return value
    with pytest.raises(harvest.CropRemovalHold):
        harvest._allocation_totals(harvest._read_allocations(withdrawn, raw, allocation), harvest._allocation_parameters(allocation, mass))
    assert len(summaries) == 6
    for arbitrary in (reader, {'approved': True}, object()):
        with pytest.raises(harvest.CropRemovalHold):
            list(harvest.iter_harvest_allocations(arbitrary, 'tenant-1', SOURCE['result_id'], {}, raw, allocation))


def save_native(name, value):
    target = os.environ.get('OSSF_REMOVAL_LEDGER_EVIDENCE')
    if target:
        raw = (json.dumps(value, sort_keys=True, indent=2) + '\n').encode()
        with (Path(target) / name).open('xb') as handle:
            os.fchmod(handle.fileno(), 0o400);handle.write(raw);handle.flush();os.fsync(handle.fileno())


@pytest.fixture
def bound_setup(authoring, tmp_path, monkeypatch):
    def managed():
        value = shifted('full-removal-reentry')
        leaf_only = deepcopy(value['events'][-1])
        leaf_only['at'] = '2026-10-01T00:01:30Z'
        leaf_only['removals']['input_id'] = 'owned-removal-ledger-leaf-stem-only'
        removed = leaf_only['removals']['values']
        removed['leaf']['value'] = 5;removed['stem_root']['value'] = 3
        for fraction in removed['fruit_fraction']:fraction['value'] = 0
        value['events'].insert(2, leaf_only)
        return value
    monkeypatch.setattr(farm_fixture, 'shifted', managed)
    monkeypatch.setattr(server_fixture, 'shifted', managed)
    yield from original_bound_setup.__wrapped__(authoring, tmp_path)


@pytest.fixture(scope='module')
def native_cleanup(login_database, tmp_path_factory):
    yield
    with psycopg.connect(login_database['admin']) as conn:
        schemas = conn.execute("SELECT count(*) FROM pg_namespace WHERE nspname ~ '^login_test_'").fetchone()[0]
        roles = conn.execute("SELECT count(*) FROM pg_roles WHERE rolname ~ '^login_(owner_|[0-9a-f]{32}_)'").fetchone()[0]
        assert_host_scram(conn)
    passfiles = list(tmp_path_factory.getbasetemp().rglob('*.pgpass'))
    assert schemas == roles == len(passfiles) == 0
    save_native('database-cleanup.json', {'schemas_after': schemas, 'roles_after': roles,
                                        'passfiles_after': len(passfiles), 'actual_host_SCRAM': True})


@pytest.mark.parametrize('original_login_scope', [{'market_calculation': True,
    'market_source_storage': True, 'thermal_scenario_storage': True,
    'break_even_calculation': True, 'crop_cycle_result_storage': True}], indirect=True)
def test_actual_stored_current_rights_raw_values_UTC_RHS0_and_FD(stored_result, native_cleanup, monkeypatch):
    service, record, farm, rights, principal, expected = stored_result
    assert len(expected['samples']) == 3 and len(expected['events']) == 4
    forbid_calculation(monkeypatch)
    monkeypatch.setattr(type(service.authority), 'issue', lambda *a, **k: pytest.fail('ledger issued result proof'))
    before = len(os.listdir('/proc/self/fd'));db_before = counts(service.store.server.binding)
    def inventory():
        return {str(path): (sha256(path.read_bytes()).hexdigest(), path.stat().st_mode & 0o777, path.stat().st_ino)
                for directory in (service.store.server.directory, service.evidence_resolver.values['input_directory'])
                for path in directory.rglob('*') if path.is_file()}
    files_before = inventory()
    call = lambda **kwargs: harvest.iter_removal_ledger(service, 'tenant-1', record['result_id'], farm, **kwargs)
    rows = list(call())
    split = list(call(last_sample=1)) + list(call(first_sample=1))
    assert split == rows and len({row['row_id'] for row in rows}) == len(rows)
    assert list(call(sample_page_size=1, event_page_size=1)) == rows
    terminal = [row for row in rows if row['kind'] == 'model_terminal_outflow']
    events = [row for row in rows if row['kind'] == 'explicit_fruit_removal']
    assert len(terminal) == len(expected['samples']) - 1 and len(events) == len(expected['events'])
    assert events[0]['carbohydrate']['value'] == 4
    assert events[0]['number']['value'] == pytest.approx(.02)
    assert events[2]['carbohydrate']['value'] == events[2]['number']['value'] == 0
    assert expected['events'][2]['removed']['leaf']['value'] == 5
    assert expected['events'][2]['removed']['stem_root']['value'] == 3
    for row in terminal:
        left, right = row['position']['samples']
        assert row['start_at'] == expected['samples'][left]['at'] and row['end_at'] == expected['samples'][right]['at']
        for key, original in (('carbohydrate', 'terminal_carbohydrate'), ('number', 'terminal_number')):
            assert row[key]['value'] == (expected['samples'][right]['cumulative'][original]['value']
                                         - expected['samples'][left]['cumulative'][original]['value'])
    for row in events:
        raw = expected['events'][row['position']['event']]
        assert row['start_at'] == row['end_at'] == raw['at']
        assert row['cohorts'] == {key: raw['removed'][key] for key in ('fruit_carbohydrate', 'fruit_number')}
        assert row['position']['event_sha256'] == sha256(harvest._canonical(raw)).hexdigest()
        for key, original in (('carbohydrate', 'fruit_carbohydrate'), ('number', 'fruit_number')):
            assert row[key]['value'] == fsum(value['value'] for value in raw['removed'][original])
    for row in rows:
        assert row['source']['result_id'] == record['result_id']
        assert row['source']['payload_sha256'] == record['payload_sha256']
        assert row['rights_or_gate_approval'] is False
    profile = mass_profile(rows[0]['source'], split=True)
    profile['segments'][0]['end_at'] = profile['segments'][1]['start_at'] = '2026-10-01T00:01:00Z'
    profile['segments'][1]['end_at'] = '2026-10-01T00:02:00Z'
    parameter_raw = harvest._canonical(profile)
    mass_call = lambda **kwargs: harvest.iter_removal_mass(service, 'tenant-1', record['result_id'], farm,
                                                          parameter_raw, **kwargs)
    summary_call = lambda: harvest.summarize_removal_mass(service, 'tenant-1', record['result_id'], farm, parameter_raw)
    mass_rows = list(mass_call())
    assert [row['removal'] for row in mass_rows] == rows
    assert list(mass_call(last_sample=1)) + list(mass_call(first_sample=1)) == mass_rows
    assert list(mass_call(sample_page_size=1, event_page_size=1)) == mass_rows
    mass_summary = summary_call()
    assert mass_summary['row_count'] == len(rows) == 6
    assert [row['parameters']['segment']['segment_id'] for row in mass_rows] == ['owned-first'] * 2 + ['owned-second'] * 4
    with localcontext() as ctx:
        ctx.prec = 2200
        for row, removal in zip(mass_rows, rows, strict=True):
            c = Decimal.from_float(removal['carbohydrate']['value'])
            n = Decimal.from_float(removal['number']['value'])
            e = Decimal.from_float(row['parameters']['segment']['eta']['value'])
            d = Decimal.from_float(row['parameters']['segment']['dmc']['value'])
            dry = c * e / 1_000_000;fresh = dry / d
            assert row['dry_matter']['value'] == float(dry) and row['fresh_matter']['value'] == float(fresh)
            assert row['fresh_mass_per_equivalent']['value'] == (float(fresh / n) if n else None)
        for kind, total in mass_summary['totals_by_kind'].items():
            selected = [row for row in mass_rows if row['removal']['kind'] == kind]
            assert total['rows'] == len(selected)
            for key in ('dry_matter', 'fresh_matter'):
                assert total[key]['value'] == float(sum((Decimal.from_float(row[key]['value']) for row in selected), Decimal(0)))
    allocation_parameters = allocation_profile(harvest._mass_parameters(parameter_raw), last_sample=2, last_event=3)
    allocation_raw = harvest._canonical(allocation_parameters)
    allocation_call = lambda **kwargs: harvest.iter_harvest_allocations(service, 'tenant-1', record['result_id'],
                                                        farm, parameter_raw, allocation_raw, **kwargs)
    allocation_summary_call = lambda: harvest.summarize_harvest_allocations(service, 'tenant-1', record['result_id'],
                                                                           farm, parameter_raw, allocation_raw)
    allocation_rows = list(allocation_call())
    assert [row['mass'] for row in allocation_rows] == mass_rows
    assert list(allocation_call(last_sample=1)) + list(allocation_call(first_sample=1)) == allocation_rows
    assert list(allocation_call(sample_page_size=1, event_page_size=1)) == allocation_rows
    allocation_summary = allocation_summary_call()
    assert_allocation_arithmetic(allocation_rows, allocation_summary, allocation_parameters)
    assert allocation_rows[3]['allocations'] == [] and allocation_rows[3]['unassigned']['fraction']['value'] == 1
    assert allocation_rows[2]['allocations'] == [] and allocation_rows[2]['unassigned']['quantities']['fresh_matter']['value'] > 0
    assert allocation_summary['observation_comparisons'][0]['status'] == 'compared_synthetic_fixture'
    for purpose in ('harvest', 'thinning', 'disposal', 'sampling'):
        assert allocation_summary['totals_by_kind_and_purpose']['explicit_fruit_removal'][purpose]['quantities']['fresh_matter']['value'] > 0
    scopes = set(principal['scopes']);tenant = principal['tenant_id']
    try:
        rights.allowed = False
        with pytest.raises(harvest.CropRemovalHold):list(call())
        with pytest.raises(harvest.CropRemovalHold):summary_call()
        with pytest.raises(harvest.CropRemovalHold):allocation_summary_call()
        rights.allowed = True;principal['scopes'].remove('crop_result_read')
        with pytest.raises(PermissionError):list(call())
        with pytest.raises(PermissionError):summary_call()
        with pytest.raises(PermissionError):allocation_summary_call()
        principal['scopes'] = scopes;principal['tenant_id'] = 'foreign'
        with pytest.raises(PermissionError):list(call())
        with pytest.raises(PermissionError):summary_call()
        with pytest.raises(PermissionError):allocation_summary_call()
    finally:
        rights.allowed = True;principal['scopes'] = scopes;principal['tenant_id'] = tenant
    original_page = harvest.current_query.results.CalculationResultReadContext.page;withdrawals = []
    with monkeypatch.context() as patch:
        def withdrawn(self, *args, **kwargs):
            page = original_page(self, *args, **kwargs);rights.allowed = False;withdrawals.append(True);return page
        patch.setattr(harvest.current_query.results.CalculationResultReadContext, 'page', withdrawn)
        for action in (lambda: next(call()), summary_call, lambda: next(allocation_call()), allocation_summary_call):
            try:
                with pytest.raises(harvest.CropRemovalHold):action()
            finally:rights.allowed = True
    assert withdrawals == [True] * 4
    assert len(os.listdir('/proc/self/fd')) == before and inventory() == files_before
    assert counts(service.store.server.binding) == db_before
    with service.store.jobs.connect() as conn:
        assert conn.pgconn.used_password and conn.info.get_parameters()['require_auth'] == 'scram-sha-256'
    save_native('removal-ledger-verified.json', {'scope': 'owned_synthetic_removal_math_only',
        'actual_SCRAM': True, 'rows': rows, 'raw_sample_count': len(expected['samples']),
        'raw_event_count': len(expected['events']), 'original_samples': expected['samples'],
        'original_events': expected['events'], 'whole_split_and_one_row_pages_identical': True,
        'mass_parameter_document': profile, 'mass_parameter_sha256': sha256(parameter_raw).hexdigest(),
        'mass_rows': mass_rows, 'mass_summary': mass_summary, 'mass_split_and_one_row_pages_identical': True,
        'mass_per_row_and_separate_totals_Decimal_checked': True,
        'allocation_parameter_document': allocation_parameters, 'allocation_parameter_sha256': sha256(allocation_raw).hexdigest(),
        'allocation_rows': allocation_rows, 'allocation_summary': allocation_summary,
        'allocation_split_and_one_row_pages_identical': True,
        'allocation_four_quantities_conservation_and_observation_Decimal_checked': True,
        'allocation_nonzero_four_purposes_unassigned_and_leaf_only_verified': True,
        'allocation_current_rights_scope_account_and_after_page_denied': True,
        'initial_boundary_final_and_leaf_stem_only_events_verified': True,
        'current_rights_scope_account_and_after_page_denied': True, 'RHS_calls': 0,
        'FD_before_after': [before, len(os.listdir('/proc/self/fd'))],
        'input_custody_SHA_mode_inode_preserved': True, 'DB_counts_preserved': list(db_before),
        'actual_crop_Runs': 0, 'gates': 'not_assessed'})
