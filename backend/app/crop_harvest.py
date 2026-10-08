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


def _allocation_fraction(record):
    _need(type(record) is dict and set(record) == {'value', 'unit'} and record['unit'] == '1')
    value = record['value']
    _need(type(value) is str and re.fullmatch(r'(?:0(?:\.\d{1,18})?|1(?:\.0{1,18})?)', value))
    result = Fraction(value)
    _need(0 < result <= 1)
    return result


def _rational_quantity(value, unit):
    rounded = -_float_quantity(-value) if value < 0 else _float_quantity(value)
    return {'value': rounded, 'unit': unit,
            'exact': {'numerator': str(value.numerator), 'denominator': str(value.denominator)}}


def _portion(mass, fraction):
    amounts = {'carbohydrate': mass['removal']['carbohydrate'], 'number': mass['removal']['number'],
               'dry_matter': mass['dry_matter'], 'fresh_matter': mass['fresh_matter']}
    units = {'carbohydrate': MASS_UNIT, 'number': NUMBER_UNIT,
             'dry_matter': 'kg_DM/m2_floor', 'fresh_matter': 'kg_FW/m2_floor'}
    return {key: _rational_quantity(Fraction(_amount(amount, units[key])) * fraction, units[key])
            for key, amount in amounts.items()}


def _allocation_parameters(raw, parameters):
    try:
        _need(type(raw) is bytes and 0 < len(raw) <= 262144)
        profile = current_query.inputs._json(raw);mass, mass_sha = parameters
        _need(type(profile) is dict and _canonical(profile) == raw and set(profile) == {
            'version', 'allocation_id', 'revision', 'origin', 'evidence_level', 'evidence_id',
            'available_at', 'source', 'population', 'mass_parameter_sha256', 'policy', 'rules', 'observations'})
        _need(profile['version'] == 'crop-harvest-allocation-v1' and profile['origin'] == 'synthetic'
              and profile['evidence_level'] == 'assumed' and profile['policy'] == 'proportional_original_population'
              and profile['source'] == mass['source'] and profile['population'] == mass['population']
              and profile['mass_parameter_sha256'] == mass_sha)
        def identifier(value):
            _need(type(value) is str and 0 < len(value) <= 128 and value.isprintable())
        for key in ('allocation_id', 'revision', 'evidence_id'):identifier(profile[key])
        _at(profile['available_at']);rules = profile['rules'];observations = profile['observations']
        _need(type(rules) is list and len(rules) <= 256 and type(observations) is list and len(observations) <= 64)
        by_id = {};edges = {};events = {}
        for rule in rules:
            _need(type(rule) is dict and set(rule) == {'assignment_id', 'selector', 'purpose', 'fraction'})
            identifier(rule['assignment_id']);_need(rule['assignment_id'] not in by_id)
            _need(rule['purpose'] in ('harvest', 'thinning', 'disposal', 'sampling'))
            weight = _allocation_fraction(rule['fraction']);selector = rule['selector']
            _need(type(selector) is dict)
            if selector['kind'] == 'model_terminal_outflow':
                _need(set(selector) == {'kind', 'first_sample', 'last_sample'})
                a, b = selector['first_sample'], selector['last_sample']
                _need(type(a) is int and type(b) is int and 0 <= a < b)
                edges[a] = edges.get(a, Fraction(0)) + weight
                edges[b] = edges.get(b, Fraction(0)) - weight
            else:
                _need(set(selector) == {'kind', 'event'} and selector['kind'] == 'explicit_fruit_removal')
                index = selector['event'];_need(type(index) is int and index >= 0)
                events[index] = events.get(index, Fraction(0)) + weight
                _need(events[index] <= 1)
            by_id[rule['assignment_id']] = rule
        running = Fraction(0)
        for edge in sorted(edges):
            running += edges[edge];_need(0 <= running <= 1)
        _need(running == 0)
        seen = set();linked = set()
        for observation in observations:
            _need(type(observation) is dict and set(observation) == {'observation_id', 'origin', 'evidence_level',
                'evidence_id', 'available_at', 'start_at', 'end_at', 'assignment_ids', 'fresh_matter'})
            for key in ('observation_id', 'evidence_id'):identifier(observation[key])
            _need(observation['observation_id'] not in seen and observation['origin'] == 'synthetic'
                  and observation['evidence_level'] == 'assumed')
            _at(observation['available_at']);_need(_at(observation['start_at']) <= _at(observation['end_at']))
            ids = observation['assignment_ids']
            _need(type(ids) is list and 1 <= len(ids) <= 256)
            for name in ids:
                identifier(name)
                _need(name in by_id and name not in linked and by_id[name]['purpose'] == 'harvest')
                linked.add(name)
            _amount(observation['fresh_matter'], 'kg_FW/m2_floor');seen.add(observation['observation_id'])
        return profile, sha256(raw).hexdigest()
    except Exception:
        raise CropRemovalHold('crop harvest allocation parameters unavailable') from None


def _allocation_scope(profile, original):
    _need(profile['source'] == _source(original))
    packet = current_query.inputs._json(original['record']['payload_raw'])
    samples, events = packet['artifact']['sample_count'], packet['artifact']['event_count']
    _need(type(samples) is int and samples > 0 and type(events) is int and events >= 0)
    for rule in profile['rules']:
        selector = rule['selector']
        _need(selector['last_sample'] < samples if selector['kind'] == 'model_terminal_outflow'
              else selector['event'] < events)


def _allocation_row(mass, parameters):
    profile, allocation_sha = parameters;removal = mass['removal']
    _need(mass['schema_version'] == 'crop-removal-mass-v1' and mass['code_sha256'] == CODE_SHA256
          and mass['dependency_sha256'] == DEPENDENCY_SHA256 and removal['source'] == profile['source']
          and mass['parameter_sha256'] == profile['mass_parameter_sha256']
          and mass['claim_scope'] == 'synthetic_removal_mass_math_only' and mass['rights_or_gate_approval'] is False)
    allocations = [];assigned = Fraction(0)
    for rule in profile['rules']:
        selector = rule['selector']
        if selector['kind'] != removal['kind']:continue
        applies = (selector['first_sample'] <= removal['position']['samples'][0] < selector['last_sample']
                   if selector['kind'] == 'model_terminal_outflow' else selector['event'] == removal['position']['event'])
        if applies:
            weight = _allocation_fraction(rule['fraction']);assigned += weight
            allocations.append({'assignment_id': rule['assignment_id'], 'purpose': rule['purpose'],
                                'fraction': deepcopy(rule['fraction']), 'quantities': _portion(mass, weight)})
    _need(assigned <= 1)
    identity = {'version': 'crop-harvest-allocation-result-v1', 'code_sha256': CODE_SHA256,
                'dependency_sha256': dict(DEPENDENCY_SHA256), 'mass_row_sha256': sha256(_canonical(mass)).hexdigest(),
                'allocation_sha256': allocation_sha}
    declaration = {key: deepcopy(value) for key, value in profile.items() if key not in ('rules', 'observations')}
    return {**identity, 'schema_version': identity['version'],
            'row_id': identity['version'] + ':' + sha256(_canonical(identity)).hexdigest(),
            'claim_scope': 'synthetic_harvest_allocation_math_only', 'rights_or_gate_approval': False,
            'mass': deepcopy(mass), 'allocation_parameters': declaration, 'allocations': allocations,
            'unassigned': {'fraction': _rational_quantity(1 - assigned, '1'),
                           'quantities': _portion(mass, 1 - assigned)},
            'rounding': 'nearest_float64_with_exact_rational_portions_of_stored_mass_row'}


def _read_allocations(read, parameter_raw, allocation_raw, **window):
    mass = _mass_parameters(parameter_raw);parameters = _allocation_parameters(allocation_raw, mass)
    original = read();_allocation_scope(parameters[0], original)
    for row in _read_mass(read, parameter_raw, **window):
        _pins()
        yield _allocation_row(row, parameters)
    _pins()
    _same(read(), original)


def iter_harvest_allocations(query, tenant, result_id, farm_ref, parameter_raw, allocation_raw, *,
                             first_sample=0, last_sample=None, sample_page_size=64, event_page_size=8):
    try:
        _pins()
        _need(type(query) is current_query.CalculationCurrentCycleQuery)
        yield from _read_allocations(lambda **kwargs: query.read(tenant, result_id, farm_ref, **kwargs),
            parameter_raw, allocation_raw, first_sample=first_sample, last_sample=last_sample,
            sample_page_size=sample_page_size, event_page_size=event_page_size)
    except PermissionError:
        raise
    except Exception:
        raise CropRemovalHold('crop harvest allocation unavailable') from None


def _allocation_totals(rows, parameters):
    profile, allocation_sha = parameters
    units = {'carbohydrate': MASS_UNIT, 'number': NUMBER_UNIT,
             'dry_matter': 'kg_DM/m2_floor', 'fresh_matter': 'kg_FW/m2_floor'}
    kinds = ('model_terminal_outflow', 'explicit_fruit_removal')
    purposes = ('harvest', 'thinning', 'disposal', 'sampling', 'unassigned')
    groups = {kind: {purpose: {'rows': 0, 'sums': {key: Fraction(0) for key in units}}
                     for purpose in purposes} for kind in kinds}
    progress = {rule['assignment_id']: {'rows': 0, 'fresh': Fraction(0), 'start': None, 'end': None}
                for rule in profile['rules']}
    def exact(quantity):
        return Fraction(int(quantity['exact']['numerator']), int(quantity['exact']['denominator']))
    chain = sha256();count = 0
    for row in rows:
        _need(row['allocation_sha256'] == allocation_sha and row['mass']['removal']['source'] == profile['source'])
        removal = row['mass']['removal'];kind = removal['kind'];count += 1
        for part in row['allocations'] + [{'purpose': 'unassigned', **row['unassigned']}]:
            group = groups[kind][part['purpose']];group['rows'] += 1
            for key in units:group['sums'][key] += exact(part['quantities'][key])
            if part['purpose'] != 'unassigned':
                state = progress[part['assignment_id']];state['rows'] += 1
                state['fresh'] += exact(part['quantities']['fresh_matter'])
                state['start'] = min(state['start'] or removal['start_at'], removal['start_at'])
                state['end'] = max(state['end'] or removal['end_at'], removal['end_at'])
        chain.update(_canonical(row));chain.update(b'\n')
    totals = {kind: {purpose: {'rows': group['rows'], 'quantities': {
        key: _rational_quantity(value, units[key]) for key, value in group['sums'].items()}}
        for purpose, group in by_purpose.items()} for kind, by_purpose in groups.items()}
    by_id = {rule['assignment_id']: rule for rule in profile['rules']};comparisons = []
    for observation in profile['observations']:
        states = [progress[name] for name in observation['assignment_ids']]
        def expected(name):
            selector = by_id[name]['selector']
            return selector['last_sample'] - selector['first_sample'] if selector['kind'] == kinds[0] else 1
        complete = all(state['rows'] == expected(name) for name, state in zip(observation['assignment_ids'], states, strict=True))
        model = difference = None
        if complete:
            _need(all(observation['start_at'] <= state['start'] <= state['end'] <= observation['end_at'] for state in states))
            value = sum((state['fresh'] for state in states), Fraction(0))
            model = _rational_quantity(value, 'kg_FW/m2_floor')
            difference = _rational_quantity(Fraction(_amount(observation['fresh_matter'], 'kg_FW/m2_floor')) - value, 'kg_FW/m2_floor')
        comparisons.append({'observation': deepcopy(observation),
            'status': 'compared_synthetic_fixture' if complete else 'incomplete_selected_window',
            'modeled_fresh_matter': model, 'observed_minus_modeled': difference})
    return {'schema_version': 'crop-harvest-allocation-summary-v1', 'code_sha256': CODE_SHA256,
        'claim_scope': 'synthetic_harvest_allocation_math_only', 'rights_or_gate_approval': False,
        'source': deepcopy(profile['source']), 'allocation_sha256': allocation_sha,
        'allocation_parameters': deepcopy(profile), 'row_count': count, 'row_chain_sha256': chain.hexdigest(),
        'totals_by_kind_and_purpose': totals, 'observation_comparisons': comparisons,
        'rounding': 'nearest_float64_with_exact_rational_sum_of_portions'}


def summarize_harvest_allocations(query, tenant, result_id, farm_ref, parameter_raw, allocation_raw, **window):
    parameters = _allocation_parameters(allocation_raw, _mass_parameters(parameter_raw))
    return _allocation_totals(iter_harvest_allocations(query, tenant, result_id, farm_ref,
                                                      parameter_raw, allocation_raw, **window), parameters)
