"""Fruit-only C/N removal from verified stored results, before mass conversion."""
from copy import deepcopy
from datetime import datetime
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
    source = {'result_id': original['record']['result_id'], 'payload_sha256': original['record']['payload_sha256'],
              'input_root_sha256': packet['input_root_sha256'], 'artifact_sha256': packet['artifact']['sha256'],
              'math_manifest_sha256': sha256(_canonical(terminal['manifest'])).hexdigest(),
              'source_status': terminal['status']}
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
