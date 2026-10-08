"""Fruit-only C/N removal from verified stored results, before mass conversion."""
from copy import deepcopy
from datetime import datetime
from fractions import Fraction
from hashlib import sha256
from math import fsum, isfinite
from pathlib import Path
import re

from . import crop_cycle_calculation_current_query as current_query
from . import thermal_run_store as json_store

_canonical = json_store._canonical

VERSION = 'crop-removal-ledger-v1'
CODE_SHA256 = sha256(Path(__file__).read_bytes()).hexdigest()
MASS_UNIT = 'mg_CH2O/m2_floor'
NUMBER_UNIT = 'fruits_equivalent/m2_floor'
_MODULES = {'current_query': current_query, 'canonical_json': json_store}
DEPENDENCY_SHA256 = {name: sha256(Path(module.__file__).read_bytes()).hexdigest()
                     for name, module in _MODULES.items()}
_DECLARATIONS = (VERSION, CODE_SHA256, MASS_UNIT, NUMBER_UNIT, _canonical(DEPENDENCY_SHA256))


class CropRemovalHold(ValueError):
    """No removal ledger for an invalid or unavailable original result."""


def _need(condition):
    if not condition:
        raise CropRemovalHold('crop removal ledger unavailable')


def _pins():
    _need((VERSION, CODE_SHA256, MASS_UNIT, NUMBER_UNIT, _canonical(DEPENDENCY_SHA256)) == _DECLARATIONS
          and sha256(Path(__file__).read_bytes()).hexdigest() == CODE_SHA256
          and {name: sha256(Path(module.__file__).read_bytes()).hexdigest()
               for name, module in _MODULES.items()} == DEPENDENCY_SHA256)


def _at(value):
    _need(type(value) is str and re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z', value))
    try:
        return datetime.fromisoformat(value[:-1] + '+00:00')
    except ValueError:
        raise CropRemovalHold('crop removal ledger unavailable') from None


def _amount(record, unit):
    try:
        _need(type(record) is dict and set(record) == {'value', 'unit'} and record['unit'] == unit)
        _need(type(record['value']) in (int, float))
        value = float(record['value'])
        _need(isfinite(value) and value >= 0)
        return value
    except (OverflowError, TypeError):
        raise CropRemovalHold('crop removal ledger unavailable') from None


def _row(source, kind, position, start, end, carbon, number, cohorts=None):
    _need(all(isfinite(value) and value >= 0 for value in (carbon, number)))
    identity = {'version': VERSION, 'code_sha256': CODE_SHA256,
                'dependency_sha256': DEPENDENCY_SHA256, 'source': source,
                'kind': kind, 'position': position}
    return {'schema_version': VERSION, 'code_sha256': CODE_SHA256,
            'dependency_sha256': dict(DEPENDENCY_SHA256),
            'claim_scope': 'research_removal_math_only', 'rights_or_gate_approval': False,
            'row_id': VERSION + ':' + sha256(_canonical(identity)).hexdigest(),
            'source': deepcopy(source), 'kind': kind, 'position': deepcopy(position),
            'start_at': start, 'end_at': end,
            'carbohydrate': {'value': carbon, 'unit': MASS_UNIT},
            'number': {'value': number, 'unit': NUMBER_UNIT}, 'cohorts': deepcopy(cohorts)}


def _terminal_row(source, previous, current):
    try:
        left, before = previous
        right, after = current
        _need(type(left) is int and left >= 0 and type(right) is int and right == left + 1)
        _need(_at(before['at']) < _at(after['at']))
        amounts = []
        for name, unit in (('terminal_carbohydrate', MASS_UNIT), ('terminal_number', NUMBER_UNIT)):
            amounts.append(_amount(after['cumulative'][name], unit) - _amount(before['cumulative'][name], unit))
        position = {'samples': [left, right],
                    'sample_sha256': [sha256(_canonical(value)).hexdigest() for value in (before, after)]}
        return _row(source, 'model_terminal_outflow', position, before['at'], after['at'], *amounts)
    except (KeyError, TypeError, ValueError, OverflowError):
        raise CropRemovalHold('crop removal ledger unavailable') from None


def _event_row(source, indexed):
    try:
        index, event = indexed
        _need(type(index) is int and index >= 0)
        _at(event['at'])
        _need(type(event['input_id']) is str and bool(event['input_id']))
        removed = event['removed']
        _need(type(removed) is dict and set(removed) == {'leaf', 'stem_root', 'fruit_carbohydrate', 'fruit_number'})
        for name in ('leaf', 'stem_root'):
            _amount(removed[name], MASS_UNIT)
        amounts = []
        for name, unit in (('fruit_carbohydrate', MASS_UNIT), ('fruit_number', NUMBER_UNIT)):
            vector = removed[name]
            _need(type(vector) is list and len(vector) == 50)
            amounts.append(fsum(_amount(value, unit) for value in vector))
        position = {'event': index, 'input_id': event['input_id'], 'event_sha256': sha256(_canonical(event)).hexdigest()}
        cohorts = {name: removed[name] for name in ('fruit_carbohydrate', 'fruit_number')}
        return _row(source, 'explicit_fruit_removal', position, event['at'], event['at'], *amounts, cohorts)
    except (KeyError, TypeError, ValueError, OverflowError):
        raise CropRemovalHold('crop removal ledger unavailable') from None


def _same(value, original):
    _need(type(value) is dict and value['record'] == original['record']
          and value['identity'] == original['identity'] and value['terminal'] == original['terminal'])


def _source(original):
    packet = current_query.inputs._json(original['record']['payload_raw'])
    return {'result_id': original['record']['result_id'], 'payload_sha256': original['record']['payload_sha256'],
            'input_root_sha256': packet['input_root_sha256'], 'artifact_sha256': packet['artifact']['sha256'],
            'math_manifest_sha256': sha256(_canonical(original['terminal']['manifest'])).hexdigest(),
            'source_status': original['terminal']['status']}


def _pages(read, original, kind, total, start, stop, limit):
    position, previous = start, None
    while position < stop:
        _pins()
        size = min(limit, stop - position)
        value = read(kind=kind, start=position, limit=size)
        _same(value, original)
        page = value['page']
        _need(type(page) is dict and set(page) == {'kind', 'start', 'next', 'total', 'records'})
        rows = page['records']
        _need(page['kind'] == kind and type(rows) is list and 1 <= len(rows) <= size
              and all(type(page[key]) is int for key in ('start', 'next', 'total'))
              and page['start'] == position and page['next'] == position + len(rows) and page['total'] == total)
        for offset, row in enumerate(rows):
            at = _at(row['at'])
            _need(previous is None or previous < at)
            previous = at
            yield position + offset, row
        position = page['next']


def _read_ledger(read, *, first_sample=0, last_sample=None, sample_page_size=64, event_page_size=8):
    original = read()
    _need(type(original) is dict)
    packet = current_query.inputs._json(original['record']['payload_raw'])
    terminal = original['terminal']
    _need(terminal['status'] in ('completed', 'hold') and packet['claim_scope'] == 'synthetic_crop_math_only')
    counts = {kind: packet['artifact'][name] for kind, name in (('samples', 'sample_count'), ('events', 'event_count'))}
    _need(all(type(value) is int and value >= 0 for value in counts.values()))
    last_sample = counts['samples'] - 1 if last_sample is None else last_sample
    _need(type(first_sample) is int and type(last_sample) is int
          and 0 <= first_sample <= last_sample < counts['samples'])
    _need(type(sample_page_size) is int and 1 <= sample_page_size <= 64
          and type(event_page_size) is int and 1 <= event_page_size <= 8)
    source = _source(original)
    samples = _pages(read, original, 'samples', counts['samples'], first_sample, last_sample + 1, sample_page_size)
    events = _pages(read, original, 'events', counts['events'], 0, counts['events'], event_page_size)
    previous = next(samples)
    start = _at(previous[1]['at'])
    for name, unit in (('terminal_carbohydrate', MASS_UNIT), ('terminal_number', NUMBER_UNIT)):
        value = _amount(previous[1]['cumulative'][name], unit)
        _need(first_sample != 0 or value == 0)
    event = next(events, None)
    while event is not None and (_at(event[1]['at']) < start or (first_sample > 0 and _at(event[1]['at']) == start)):
        event = next(events, None)
    if first_sample == 0 and event is not None and _at(event[1]['at']) == start:
        yield _event_row(source, event)
        event = next(events, None)
    for selected in samples:
        end = _at(selected[1]['at'])
        while event is not None and _at(event[1]['at']) < end:
            yield _event_row(source, event)
            event = next(events, None)
        yield _terminal_row(source, previous, selected)
        if event is not None and _at(event[1]['at']) == end:
            yield _event_row(source, event)
            event = next(events, None)
        previous = selected
    _pins()
    _same(read(), original)


def iter_removal_ledger(query, tenant, result_id, farm_ref, *, first_sample=0, last_sample=None,
                        sample_page_size=64, event_page_size=8):
    try:
        _pins()
        _need(type(query) is current_query.CalculationCurrentCycleQuery)
        yield from _read_ledger(lambda **kwargs: query.read(tenant, result_id, farm_ref, **kwargs),
                                first_sample=first_sample, last_sample=last_sample,
                                sample_page_size=sample_page_size, event_page_size=event_page_size)
    except PermissionError:
        raise
    except Exception:
        raise CropRemovalHold('crop removal ledger unavailable') from None


def _float_quantity(value):
    try:
        result = float(value)
        _need(isfinite(result) and result >= 0 and (value == 0 or result > 0))
        return result
    except OverflowError:
        raise CropRemovalHold('crop removal mass unavailable') from None


def _mass_values(carbohydrate, number, eta, dmc):
    carbon = _amount(carbohydrate, MASS_UNIT)
    count = _amount(number, NUMBER_UNIT)
    factor = _amount(eta, 'mg_DM/mg_CH2O')
    fraction = _amount(dmc, 'kg_DM/kg_FW')
    _need(factor > 0 and 0 < fraction <= 1)
    dry = Fraction(carbon) * Fraction(factor) / 1_000_000
    fresh = dry / Fraction(fraction)
    return {'dry_matter': {'value': _float_quantity(dry), 'unit': 'kg_DM/m2_floor'},
            'fresh_matter': {'value': _float_quantity(fresh), 'unit': 'kg_FW/m2_floor'},
            'fresh_mass_per_equivalent': {'value': _float_quantity(fresh / Fraction(count)) if count else None,
                                          'unit': 'kg_FW/fruit_equivalent'}}


def _mass_parameters(raw):
    try:
        _need(type(raw) is bytes and 0 < len(raw) <= 262144)
        profile = current_query.inputs._json(raw)
        _need(type(profile) is dict and _canonical(profile) == raw and set(profile) == {
            'version', 'parameter_id', 'revision', 'origin', 'evidence_level', 'evidence_id',
            'available_at', 'source', 'population', 'policy', 'segments'})
        _need(profile['version'] == 'crop-removal-mass-parameters-v1'
              and profile['origin'] == 'synthetic' and profile['evidence_level'] == 'assumed'
              and profile['policy'] == 'constant_per_original_interval')
        def identifier(value):
            _need(type(value) is str and 0 < len(value) <= 128 and value.isprintable())
        for key in ('parameter_id', 'revision', 'evidence_id'):identifier(profile[key])
        _at(profile['available_at'])
        source = profile['source']
        _need(type(source) is dict and set(source) == {'result_id', 'payload_sha256',
            'input_root_sha256', 'artifact_sha256', 'math_manifest_sha256', 'source_status'})
        identifier(source['result_id'])
        _need(source['source_status'] in ('completed', 'hold'))
        for key in ('payload_sha256', 'input_root_sha256', 'artifact_sha256', 'math_manifest_sha256'):
            _need(type(source[key]) is str and re.fullmatch('[0-9a-f]{64}', source[key]))
        population = profile['population']
        _need(type(population) is dict and set(population) == {'population_id', 'scope', 'basis', 'basis_evidence_id'}
              and population['scope'] == 'all_model_fruit_cohorts' and population['basis'] == 'm2_floor')
        identifier(population['population_id']);identifier(population['basis_evidence_id'])
        segments = profile['segments'];previous = None;seen = set()
        _need(type(segments) is list and 1 <= len(segments) <= 256)
        for segment in segments:
            _need(type(segment) is dict and set(segment) == {'segment_id', 'start_at', 'end_at', 'eta', 'dmc'})
            identifier(segment['segment_id'])
            _need(segment['segment_id'] not in seen and _at(segment['start_at']) < _at(segment['end_at']))
            _need(previous is None or previous == segment['start_at'])
            _mass_values({'value': 0, 'unit': MASS_UNIT}, {'value': 0, 'unit': NUMBER_UNIT},
                         segment['eta'], segment['dmc'])
            seen.add(segment['segment_id']);previous = segment['end_at']
        return profile, sha256(raw).hexdigest()
    except Exception:
        raise CropRemovalHold('crop removal mass parameters unavailable') from None


def _mass_row(removal, parameters):
    profile, parameter_sha256 = parameters
    _need(removal['source'] == profile['source'] and removal['schema_version'] == VERSION
          and removal['code_sha256'] == CODE_SHA256 and removal['dependency_sha256'] == DEPENDENCY_SHA256
          and removal['claim_scope'] == 'research_removal_math_only' and removal['rights_or_gate_approval'] is False)
    start, end = removal['start_at'], removal['end_at']
    _need(_at(start) <= _at(end))
    segments = profile['segments'];matched = []
    for i, segment in enumerate(segments):
        if removal['kind'] == 'model_terminal_outflow':
            applies = segment['start_at'] <= start < end <= segment['end_at']
        else:
            _need(removal['kind'] == 'explicit_fruit_removal' and start == end)
            applies = segment['start_at'] <= start < segment['end_at'] or (i == len(segments)-1 and start == segment['end_at'])
        if applies:matched.append(segment)
    _need(len(matched) == 1)
    segment = matched[0]
    values = _mass_values(removal['carbohydrate'], removal['number'], segment['eta'], segment['dmc'])
    identity = {'version': 'crop-removal-mass-v1', 'code_sha256': CODE_SHA256,
                'dependency_sha256': DEPENDENCY_SHA256, 'removal_sha256': sha256(_canonical(removal)).hexdigest(),
                'parameter_sha256': parameter_sha256, 'segment_id': segment['segment_id']}
    declaration = {key: profile[key] for key in ('version', 'parameter_id', 'revision', 'origin',
        'evidence_level', 'evidence_id', 'available_at', 'population', 'policy')}
    declaration.update(sha256=parameter_sha256, segment=segment,
                       rounding='nearest_float64_from_exact_input_floats_per_row')
    return {**identity, 'schema_version': 'crop-removal-mass-v1',
            'row_id': 'crop-removal-mass-v1:' + sha256(_canonical(identity)).hexdigest(),
            'claim_scope': 'synthetic_removal_mass_math_only', 'rights_or_gate_approval': False,
            'removal': deepcopy(removal), 'parameters': deepcopy(declaration), **values}


def _read_mass(read, parameter_raw, **window):
    parameters = _mass_parameters(parameter_raw)
    original = read()
    _need(_source(original) == parameters[0]['source'])
    for removal in _read_ledger(read, **window):
        _pins()
        yield _mass_row(removal, parameters)
    _pins()
    _same(read(), original)


def iter_removal_mass(query, tenant, result_id, farm_ref, parameter_raw, *, first_sample=0, last_sample=None,
                      sample_page_size=64, event_page_size=8):
    try:
        _pins()
        _need(type(query) is current_query.CalculationCurrentCycleQuery)
        yield from _read_mass(lambda **kwargs: query.read(tenant, result_id, farm_ref, **kwargs), parameter_raw,
                              first_sample=first_sample, last_sample=last_sample,
                              sample_page_size=sample_page_size, event_page_size=event_page_size)
    except PermissionError:
        raise
    except Exception:
        raise CropRemovalHold('crop removal mass unavailable') from None


def _mass_totals(rows, parameters):
    groups = {kind: {'rows': 0, 'sums': [Fraction(0) for _ in range(4)]}
              for kind in ('model_terminal_outflow', 'explicit_fruit_removal')}
    units = (MASS_UNIT, NUMBER_UNIT, 'kg_DM/m2_floor', 'kg_FW/m2_floor')
    profile, parameter_sha256 = parameters;chain = sha256();count = 0
    for row in rows:
        _need(row['parameter_sha256'] == parameter_sha256 and row['removal']['source'] == profile['source'])
        group = groups[row['removal']['kind']];group['rows'] += 1;count += 1
        amounts = (row['removal']['carbohydrate'], row['removal']['number'], row['dry_matter'], row['fresh_matter'])
        for i, (amount, unit) in enumerate(zip(amounts, units, strict=True)):
            group['sums'][i] += Fraction(_amount(amount, unit))
        chain.update(_canonical(row));chain.update(b'\n')
    totals = {}
    for kind, group in groups.items():
        totals[kind] = {'rows': group['rows'], **{key: {'value': _float_quantity(value), 'unit': unit}
            for key, value, unit in zip(('carbohydrate', 'number', 'dry_matter', 'fresh_matter'), group['sums'], units, strict=True)}}
    return {'schema_version': 'crop-removal-mass-summary-v1', 'code_sha256': CODE_SHA256,
            'claim_scope': 'synthetic_removal_mass_math_only', 'rights_or_gate_approval': False,
            'source': deepcopy(profile['source']), 'parameter_sha256': parameter_sha256,
            'row_count': count, 'row_chain_sha256': chain.hexdigest(), 'totals_by_kind': totals,
            'rounding': 'nearest_float64_of_exact_sum_of_rounded_rows'}


def summarize_removal_mass(query, tenant, result_id, farm_ref, parameter_raw, **window):
    return _mass_totals(iter_removal_mass(query, tenant, result_id, farm_ref, parameter_raw, **window),
                        _mass_parameters(parameter_raw))
