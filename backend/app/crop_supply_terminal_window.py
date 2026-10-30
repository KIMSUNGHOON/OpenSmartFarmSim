"""Recorded C/N and terminal differences; supply-terminal-window-v1.md."""
from copy import deepcopy
from fractions import Fraction
from hashlib import sha256
import json
from pathlib import Path

from . import crop_supply_morphology_artifact_reader as reader
from .crop_morphology_artifact_io import MorphologyBlobStore, _need

VERSION = 'supply-terminal-window-v1'
CODE_SHA256 = sha256(Path(__file__).read_bytes()).hexdigest()
MASS, NUMBER = 'mg_CH2O/m2_floor', 'fruits_equivalent/m2_floor'
q, x = reader.projection.q, reader.projection.x


class SupplyTerminalHold(ValueError):
    """No source-bound projection is returned for this request."""


def _code_fence():
    _need(sha256(Path(__file__).read_bytes()).hexdigest() == CODE_SHA256,
          'CODE_HOLD: unchanged loaded terminal projection required')


def _lifetimes(manifest, raws):
    checkpoints, material = {}, {}
    previous_context = previous_cp = None
    pins = {name:manifest['code_sha256'][name] for name in reader.MODEL_SOURCE_PATHS}
    for segment in manifest['segments']:
        context = json.loads(raws[segment['context']['sha256']][0])
        if previous_context is not None:
            receipt = reader._transition(previous_context, context, previous_cp, pins)
            material[reader._digest(receipt)] = receipt['before_candidate']['dense_candidate']['pending_lifetime_transfers_exact']
        for descriptor in segment['checkpoints']:
            previous_cp = json.loads(raws[descriptor['sha256']][0])
            checkpoints[descriptor['sha256']] = previous_cp['lifetime_transfers_exact']
        previous_context = context
    return checkpoints, material


def _stock_frame(frame, lifetime):
    layout = frame['state_layout']['original']
    _need(layout['plant'] == ['buffer','temperature_filtered_24h','temperature_sum']
          and layout['cohort_arrays'] == ['fruit_carbohydrate','fruit_number']
          and layout['units']['cohort_arrays'] == {'fruit_carbohydrate':MASS,'fruit_number':NUMBER},
          'LAYOUT_HOLD: original50-cohort coordinate order and units required')
    state = frame['snapshot']['state']
    carbon, number = state[3:53], state[53:103]
    _need(len(carbon) == len(number) == 50
          and all(c >= 0 and n >= 0 and (c == 0 or n > 0) for c,n in zip(carbon,number,strict=True)),
          'STATE_HOLD: nonnegative original cohort stocks required')
    for name, unit in [('terminal_carbon',MASS),('terminal_number',NUMBER)]:
        _need(x(lifetime[name],unit) >= 0, 'QUANTITY_HOLD: nonnegative original terminal counter required')
    reference = {name:deepcopy(frame[name]) for name in (
        'index','context_sha256','checkpoint_sha256','receipt_sha256',
        'event_sequence','output_cursor','output_prefix_sha256')}
    reference['frame_sha256'] = reader._digest(frame)
    return {'reference':reference,'at':deepcopy(frame['at']),'phase':frame['phase'],
            'state_sha256':reader._digest(state),
            'fruit_carbohydrate':{'values':list(carbon),'unit':MASS},
            'fruit_number':{'values':list(number),'unit':NUMBER},
            'carbohydrate_stock_exact':q(sum(map(Fraction,carbon),Fraction(0)),MASS),
            'number_stock_exact':q(sum(map(Fraction,number),Fraction(0)),NUMBER),
            'terminal_carbohydrate_exact':deepcopy(lifetime['terminal_carbon']),
            'terminal_number_exact':deepcopy(lifetime['terminal_number'])}


def _interval(left, right):
    _need(left['at']['time_origin_utc'] == right['at']['time_origin_utc'],
          'TIME_HOLD: same original origin required')
    duration = x(right['at']['elapsed_seconds_exact'],'s')-x(left['at']['elapsed_seconds_exact'],'s')
    carbon = x(right['terminal_carbohydrate_exact'],MASS)-x(left['terminal_carbohydrate_exact'],MASS)
    number = x(right['terminal_number_exact'],NUMBER)-x(left['terminal_number_exact'],NUMBER)
    _need(duration >= 0 and carbon >= 0 and number >= 0,
          'ORDER_HOLD: ordered time and terminal counters required')
    if duration == 0:
        _need(carbon == number == 0
              and left['phase'] == 'fractional_before_compatible_material_point'
              and right['phase'] == 'fractional_after_compatible_material_point',
              'BOUNDARY_HOLD: unchanged terminal quantities at actual material point required')
    return {'from_frame':deepcopy(left['reference']),'to_frame':deepcopy(right['reference']),
            'start_at':deepcopy(left['at']),'end_at':deepcopy(right['at']),
            'kind':'zero_duration_material_boundary' if duration == 0 else 'model_terminal_outflow',
            'carbohydrate_exact':q(carbon,MASS),'number_exact':q(number,NUMBER)}


def read_supply_terminal_window(directory, access, root_sha256, *, first_frame=0, last_frame=None):
    """Read an inclusive original-index window; never calculate fresh crop states."""
    try:
        _code_fence()
        _need(type(first_frame) is int and 0 <= first_frame < 512
              and (last_frame is None or type(last_frame) is int and first_frame <= last_frame < 512),
              'WINDOW_HOLD: bounded inclusive original indices required')
        reader._hash(root_sha256)
        with MorphologyBlobStore(directory, access) as store:
            manifest, original, raws = reader._load(store,root_sha256)
            last = len(original)-1 if last_frame is None else last_frame
            _need(first_frame <= last < len(original), 'WINDOW_HOLD: existing stored frame required')
            basis = original[0]['model_floor_area']
            _need(all(f['model_floor_area'] == basis for f in original),
                  'BASIS_HOLD: unchanged original floor basis required')
            checkpoints, material = _lifetimes(manifest,raws)
            frames = []
            for frame in original[first_frame:last+1]:
                lifetime = (checkpoints[frame['checkpoint_sha256']] if frame['checkpoint_sha256'] is not None
                            else material[frame['receipt_sha256']])
                frames.append(_stock_frame(frame,lifetime))
            intervals = [_interval(a,b) for a,b in zip(frames,frames[1:])]
            totals = {}
            for name, field, unit in [('terminal_carbohydrate_exact','carbohydrate_exact',MASS),
                                       ('terminal_number_exact','number_exact',NUMBER)]:
                delta = x(frames[-1][name],unit)-x(frames[0][name],unit)
                _need(sum((x(row[field],unit) for row in intervals),Fraction(0)) == delta,
                      'BALANCE_HOLD: exact original endpoint telescoping required')
                totals[name] = q(delta,unit)
            result = {'schema_version':VERSION,'code_sha256':CODE_SHA256,'scope':'software_research_only',
                'claim_scope':'synthetic_terminal_quantities_only','G0_G4':manifest['G0_G4'],'R2':manifest['R2'],
                'source':{'artifact_sha256':root_sha256,'model_code_sha256':deepcopy(manifest['code_sha256']),
                          'root_inputs':deepcopy(manifest['root_inputs']),'source_rights':deepcopy(manifest['source_rights']),
                          'redistribution_authorized':manifest['redistribution_authorized'],
                          'model_floor_area':deepcopy(basis),'terminal':deepcopy(manifest['terminal'])},
                'window':{'first_frame':first_frame,'last_frame':last,'start_at':deepcopy(frames[0]['at']),
                          'end_at':deepcopy(frames[-1]['at'])},'frames':frames,'intervals':intervals,'totals':totals}
            _need(len(reader._canonical(result)) <= reader.MAX, 'CAPACITY_HOLD: original2MiB response cap required')
            reader._fence(store,manifest,raws)
            _code_fence()
            return result
    except (OSError,ValueError,TypeError,KeyError,AttributeError,OverflowError,ZeroDivisionError,RecursionError):
        raise SupplyTerminalHold('SUPPLY_TERMINAL_HOLD: original source/window unavailable') from None
