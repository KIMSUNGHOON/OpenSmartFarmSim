"""Pure forcing-interval candidates; source authority and publication belong to callers.

This module neither creates an owner checkpoint nor saves/approves a crop result.
"""
from copy import deepcopy
from fractions import Fraction
from hashlib import sha256
from math import isfinite
from pathlib import Path
import time
from types import SimpleNamespace

from . import crop_supply_season as base

VERSION = 'supply-forcing-interval-research-v1'
CODE_SHA256 = sha256(Path(__file__).read_bytes()).hexdigest()
_COMPONENTS = base.reader._pins()
FLAGS = base.FLAGS
q, x = base.q, base.x
need = base._need
raw, digest = base._raw, base._hash


def _code():
    base._code()
    need(sha256(Path(__file__).read_bytes()).hexdigest() == CODE_SHA256
         and base.reader._pins() == _COMPONENTS, 'CODE_HOLD: unchanged forcing arithmetic required')


def _profiles(basis, profiles):
    classes = {'growth_profile':base.growth.ReferenceParameters,'cohort_profile':base.cohort.ReferenceFruitCohortParameters,
               'transport_profile':base.transport.ReferenceFruitTransportParameters,'exchange_profile':base.exchange.ReferenceParameters}
    need(type(profiles) is dict and set(profiles) == set(classes), 'PROFILE_HOLD: four pinned profiles required')
    for name,cls in classes.items():
        profile = profiles[name]
        need(type(profile) is cls and vars(profile) == vars(cls(profile.raw_bytes))
             and profile.sha256 == basis['profile_sha256'][name], 'PROFILE_HOLD: complete unchanged fixed profile required')


def _view(basis, span):
    base.reader._closed(span, {'input_id','origin','start','end','forcing','fruit_entry'})
    base.reader._id(span['input_id'])
    need(span['origin'] == 'synthetic', 'SCOPE_HOLD: explicit synthetic forcing assumption required')
    program = deepcopy(basis['seed']['program'])
    for block in ('forcing','fruit_entry'):
        original = program['scenario'][block]
        base.reader._closed(span[block], set(original))
        for name,source in original.items():
            value = span[block][name]
            base.reader._closed(value, {'value','unit'})
            need(value['unit'] == source['unit'], 'UNIT_HOLD: original '+name+' unit required')
            need(type(value['value']) is float and isfinite(value['value']), 'INPUT_HOLD: finite binary64 forcing required')
        program['scenario'][block] = deepcopy(span[block])
    return program


def _data(basis, program, profiles):
    seed = basis['seed']
    indices = {v['compartment_id']:i for i,v in enumerate(program['stem_root_compartments'])}
    return {**basis,'program':program,'organs':seed['organs'],'costs':seed['costs'],'profiles':profiles,
            'stem_stock_indices':[indices[row['compartment_id']] for row in seed['organs']['internodes']]}


def _books(s, state, totals, derived, steps, at):
    # Reuse only the existing pure account arithmetic; None grants no old-owner authority.
    return base.books.calculate(None,s.data,state,{'derived':derived},totals,steps,at)


def advance_interval(*, basis, current, profiles, span, end, cancelled=None, wall_seconds=60):
    """Calculate one declared interval no farther than the next original grid edge.

    Inputs must already have source/rights admission by the caller. Returned
    candidates remain unpublished and must not be cast into a v1 owner handle.
    """
    started = time.monotonic()
    _code()
    snapshot = raw({'basis':basis,'current':current,'span':span,'end':end})
    _profiles(basis,profiles)
    program = _view(basis,span)
    need(type(wall_seconds) is int and 1 <= wall_seconds <= 60
         and (cancelled is None or callable(cancelled)), 'BUDGET_HOLD: bounded local controls required')
    need(type(current) is dict and all(current[k] == v for k,v in FLAGS.items()), 'SCOPE_HOLD: research current state required')
    schema = current['schema_version']
    need(schema in ('supply-season-current-v1','supply-forcing-interval-state-v1'), 'STATE_HOLD: supported numerical state required')
    if schema == 'supply-forcing-interval-state-v1':
        need(current['code_sha256'] == CODE_SHA256 and current['model_version'] == VERSION,
             'CODE_HOLD: original forcing candidate version required')
    seed = basis['seed']
    base.reader._closed(current['at'], {'time_origin_utc','elapsed_seconds_exact'})
    base.reader._closed(current['last_confirmed'], {'at','state','derived'})
    at, right = x(current['at']['elapsed_seconds_exact'],'s'), x(end,'s')
    begin, stop = x(span['start'],'s'), x(span['end'],'s')
    grid = Fraction(seed['original_numerical']['step_seconds'])
    need(grid > 0, 'TIME_HOLD: positive original grid step required')
    next_grid = (at//grid+1)*grid
    need(begin <= at < right <= stop and right <= next_grid,
         'TIME_HOLD: covered positive interval within next original grid endpoint required')
    need(current['last_confirmed']['at'] == current['at']
         and current['at']['time_origin_utc'] == seed['initial_sample']['at']['time_origin_utc'],
         'TIME_HOLD: unchanged exact origin/snapshot time required')
    need(type(current['grid_index']) is int and current['grid_index'] == at//grid,
         'TIME_HOLD: unchanged actual original grid position required')
    if schema == 'supply-forcing-interval-state-v1':
        need(current['grid_remainder_exact'] == q(at-(at//grid)*grid,'s')
             and current['next_grid_endpoint_exact'] == q(next_grid,'s'),
             'TIME_HOLD: actual fractional grid remainder required')
    else:
        need(at%grid == 0 and current['phase'] == 'original_grid_endpoint',
             'TIME_HOLD: a v1 input must be an actual original-grid endpoint')
    need(type(current['branch_steps']) is int and current['branch_steps'] >= 0,
         'STATE_HOLD: actual branch operation count required')
    state = base._vector(current['last_confirmed']['state'],len(seed['initial_sample']['state']))
    units = base.books.flux_units(program,seed['organs'])
    base.reader._closed(current['branch_integrated_transfers'],set(units))
    totals = []
    for name,unit in units.items():
        value = current['branch_integrated_transfers'][name]
        base.reader._closed(value, {'value','unit'})
        need(value['unit'] == unit and type(value['value']) is float and isfinite(value['value']),
             'UNIT_HOLD: complete finite original flux accumulators required')
        totals.append(value['value'])
    data = _data(basis,program,profiles)
    s = SimpleNamespace(data=data,basis=basis,profiles=profiles,units=units,dt=right-at)
    need(base._clock(s,tuple(totals),at) == current['schedule']
         and x(current['schedule']['age_exact'],'degC_day') < x(current['schedule']['next_threshold_exact'],'degC_day'),
         'CLOCK_HOLD: original accumulated clock before pending threshold required')
    local, global_books, _, lifetime = _books(s,state,tuple(totals),current['last_confirmed']['derived'],current['branch_steps'],at)
    need(local == current['branch_ledgers'] and global_books == current['global_ledgers']
         and {k:q(v,units[k]) for k,v in lifetime.items()} == current['lifetime_transfers_exact']
         and current['event_sequence'] == seed['event_sequence']
         and current['point_totals_exact'] == seed['point_totals_exact']
         and current['transfer_origins'] == seed['transfer_origins'], 'BALANCE_HOLD: unchanged actual input accounts and origins required')
    active = digest({k:span[k] for k in ('forcing','fruit_entry')})
    previous = current.get('active_input_sha256',digest({k:seed['program']['scenario'][k] for k in ('forcing','fruit_entry')}))
    need(active == previous or at == begin, 'ORDER_HOLD: changed forcing must start at the declared edge')
    controls = base.AdvanceRequest(end,wall_seconds=wall_seconds,cancelled=cancelled)
    progress = {'stage':'current_validation','current_validation_RHS_evaluations':0,'new_RHS_evaluations':0}
    first = base._rhs(s,state,controls,progress,started,'current_validation')
    if active == previous:
        need(first['derived'] == current['last_confirmed']['derived'], 'STATE_HOLD: unchanged-input current RHS required')
    transition = {'at':deepcopy(current['at']),'changed':active != previous,'previous_input_sha256':previous,
                  'active_input_sha256':active,'before_state_sha256':digest(list(state)),'after_state_sha256':digest(list(state)),
                  'before_derived':deepcopy(current['last_confirmed']['derived']),'after_derived':deepcopy(first['derived']),
                  'point_transfers_added':False}
    end_state, cumulative, evaluated, trace, schedule = base._step(s,current,first,controls,progress,started)
    base._interrupt(controls,progress,started)
    _code()
    need(snapshot == raw({'basis':basis,'current':current,'span':span,'end':end}), 'SOURCE_HOLD: immutable interval inputs required')
    common = {**FLAGS,'schema_version':'supply-forcing-interval-candidate-v1','model_version':VERSION,
              'code_sha256':CODE_SHA256,'arithmetic_code_sha256':base.CODE_SHA256,'component_code_sha256':dict(_COMPONENTS),
              'input_sha256':sha256(snapshot).hexdigest(),'span_sha256':digest(span),'forcing_transition':transition,
              'interval':trace,'progress':deepcopy(progress),'checkpoint_issued':False,'history_committed':False,'material_consumed':False}
    if x(schedule['age_exact'],'degC_day') >= x(schedule['next_threshold_exact'],'degC_day'):
        result = {**common,'status':'awaiting_material','current':None,'pending':{'left_at':q(at,'s'),'right_at':q(right,'s'),
                  'left_age_exact':current['schedule']['age_exact'],'right_age_exact':schedule['age_exact'],
                  'threshold_exact':schedule['next_threshold_exact'],'schedule_consumed':False,
                  'forcing_material_order_resolved':False,'candidate_or_checkpoint_issued':False}}
    else:
        steps = current['branch_steps']+1
        local, global_books, diagnostics, lifetime = _books(s,end_state,cumulative,evaluated['derived'],steps,right)
        position = int(right//grid)
        advanced = {**FLAGS,'schema_version':'supply-forcing-interval-state-v1','model_version':VERSION,'code_sha256':CODE_SHA256,
                    **{k:deepcopy(current[k]) for k in base.NUMERIC_FIELDS if k not in ('output_cursor','output_prefix_sha256')},
                    'at':{'time_origin_utc':current['at']['time_origin_utc'],'elapsed_seconds_exact':q(right,'s')},
                    'branch_steps':steps,'grid_index':position,'grid_remainder_exact':q(right-position*grid,'s'),
                    'next_grid_endpoint_exact':q((position+1)*grid,'s'),'active_input_sha256':active,
                    'phase':'original_grid_endpoint' if right%grid == 0 else 'forcing_interval_endpoint',
                    'schedule':schedule,'branch_integrated_transfers':{k:{'value':v,'unit':unit} for (k,unit),v in zip(units.items(),cumulative,strict=True)},
                    'lifetime_transfers_exact':{k:q(v,units[k]) for k,v in lifetime.items()},
                    'branch_ledgers':local,'global_ledgers':global_books,'geometry_diagnostics':diagnostics}
        advanced['last_confirmed'] = {'at':deepcopy(advanced['at']),'state':list(end_state),'derived':deepcopy(evaluated['derived'])}
        raw(advanced,base.CURRENT_MAX)
        result = {**common,'status':'interval_ready','current':advanced,'pending':None}
    raw(result)
    return result
