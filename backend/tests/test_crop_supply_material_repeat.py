"""Private baseline: genuine original material current stops at its next event."""
from copy import deepcopy
from fractions import Fraction
from math import ulp
from pathlib import Path
import sys
from hashlib import sha256
import json

from app import crop_supply_material_owner as material
from app import crop_supply_material_point as point
from app import crop_supply_forcing_owner as forcing
from app import crop_supply_forcing_threshold_state as candidate
from app import crop_supply_season as base
from test_crop_supply_season import source, q, x, canonical
from test_crop_supply_forcing_owner import origin, setup_owner
from test_crop_supply_forcing_threshold import TOLERANCE
from test_crop_supply_material_point import make_inputs



def _read_blob(directory, reference):
    raw = (directory / reference).read_bytes()
    assert sha256(raw).hexdigest() == reference
    return json.loads(raw)


def _source_ref(handle, version):
    return {'owner_version': version, 'definition_sha256': handle._definition,
            'cursor_sha256': handle.cursor_sha256, 'current_sha256': sha256(handle._current).hexdigest(),
            'basis_sha256': sha256(handle._basis).hexdigest()}


def _successor_inputs(info, calculation, pending_sha, handle, first_inputs, ordinal):
    value = deepcopy(first_inputs)
    event = info['event']
    value.update(schema_version='supply-material-successor-point-input-v1',
        input_id='own-successor-material-QA-' + str(ordinal),
        policy='explicit-compatible-successor-seed-on-active-forcing-v1',
        source_owner_version=info['source']['owner_version'],
        definition_sha256=info['source']['definition_sha256'], cursor_sha256=handle.cursor_sha256,
        pending_page_sha256=pending_sha, candidate_sha256=calculation['calculation_sha256'],
        initial_binding_sha256=info['initial_binding_sha256'],
        at_elapsed_seconds_exact=deepcopy(calculation['at']['elapsed_seconds_exact']),
        source_event_id=event['source_event_id'], source_threshold_sequence=event['sequence'],
        source_threshold_exact=deepcopy(event['threshold_exact']))
    seed = handle.basis['numeric_basis']['seed']
    parents = [v['compartment_id'] for v in seed['program']['stem_root_compartments'] if v['kind'] == 'internode']
    assert parents
    value['parent_internode_id'] = parents[-1]
    value['internode']['declaration']['compartment_id'] = event['internode_id']
    value['leaf']['declaration']['leaf_id'] = event['leaf_id']
    value['parameter_provenance']['product_id'] = value['input_id']
    # Reuse only the original explicit static declarations; refresh their original hash/units.
    from test_crop_supply_material_point import refresh
    return refresh(value)


def _point_accounts(receipt, before_handle, profiles):
    d = receipt['point_data']; before = d['before_dense']; n0 = before_handle.current['numeric']
    seed = before_handle.basis['numeric_basis']['seed']; p = seed['program']
    n, m = len(p['leaves']), len(p['stem_root_compartments']); nn = n + 1
    a = list(map(Fraction, before['state'][:106 + 3*n + m]))
    b = list(map(Fraction, d['after_state'][:106 + 3*nn + m + 1]))
    flow = {k: x(v) for k, v in d['point_flows_exact'].items()}
    ca = Fraction(before['derived']['air_capacity']['value'])
    latent = Fraction(profiles['exchange_profile'].values['latent_heat'])
    reference = Fraction(d['after_program']['scenario']['parameters']['reference_temperature']['value'])
    carbon = lambda v, count: v[0] + sum(v[3:53]) + sum(v[106 + 2*count:])
    energy = lambda v: v[103] + ca * (v[104] - reference) + latent * v[105]
    stem = Fraction(receipt['inputs']['internode']['declaration']['initial_carbon']['value'])
    leaf = Fraction(receipt['inputs']['leaf']['declaration']['initial_carbon']['value'])
    terms = {
        'buffer': (b[0], -a[0], flow['buffer_debit']),
        'whole_carbohydrate': (carbon(b, nn), -carbon(a, n), flow['growth_respiration']),
        'new_internode': (b[-1], -stem),
        'stem_root_carbon': (sum(b[106 + 3*nn:]), -sum(a[106 + 3*n:]), -stem),
        'capacity': (Fraction(d['after_derived']['canopy_capacity']['value']),
                     -Fraction(before['derived']['canopy_capacity']['value']), -flow['capacity_in']),
        'canopy_sensible': (b[103], -a[103], -flow['sensible_in']),
        'air_sensible': (ca*b[104], -ca*a[104]), 'vapor': (b[105], -a[105]),
        'fruit_number': (sum(b[53:103]), -sum(a[53:103])),
        'reduced_energy': (energy(b), -energy(a), -flow['sensible_in']),
        'new_leaf': (b[106 + 2*nn + n], -leaf),
    }
    assert set(terms) == set(d['point_balances'])
    for name, row in terms.items():
        assert x(d['point_balances'][name]['residual_exact']) == sum(row, Fraction(0)), name
        assert x(d['point_balances'][name]['budget_exact']) == 64 * Fraction(ulp(float(max(map(abs, row))))), name
    mapping = {'carbohydrate': 'whole_carbohydrate', 'number': 'fruit_number',
        'canopy_sensible': 'canopy_sensible', 'air_sensible': 'air_sensible', 'vapor': 'vapor',
        'area_capacity': 'capacity', 'reduced_energy': 'reduced_energy', 'stem_root_carbon': 'stem_root_carbon',
        'leaf_carbon_' + str(n): 'new_leaf', 'stem_root_carbon_' + str(m): 'new_internode'}
    for name, row in d['post_point_global_ledgers_preview'].items():
        prior = before['pending_global_ledgers'].get(name)
        point_row = d['point_balances'].get(mapping.get(name))
        for field in ['residual_exact', 'budget_exact']:
            expected = (x(prior[field]) if prior else 0) + (x(point_row[field]) if point_row else 0)
            assert x(row[field]) == expected, (name, field)
        assert abs(x(row['residual_exact'])) <= x(row['budget_exact']), name
    for name, prior in before['point_totals_exact'].items():
        delta = flow.get(name, stem if name == 'stem_structural_carbon' else leaf if name == 'leaf_structural_carbon' else 0)
        assert x(d['post_point_point_totals_exact_preview'][name]) == x(prior) + delta, name
    for name, prior in before['pending_lifetime_transfers_exact'].items():
        assert d['post_point_lifetime_transfers_exact_preview'][name] == prior, name
    for kind in ['leaf', 'stem_root']:
        assert d['after_birth_baselines'][kind][:-1] == seed['birth_bases'][kind]
    for kind in ['leaves', 'internodes']:
        assert d['after_geometry_baselines'][kind][:-1] == seed['geometry_baselines'][kind]
    actual = base.stage.evaluate(d['after_program'], tuple(d['after_state']), d['after_organs'], d['after_costs'], profiles)
    assert d['after_rates'] == actual['rates'] and d['after_derived'] == actual['derived']
    assert d['source_schedule'] == n0['schedule']
    assert d['source_transfer_origins'] == n0['transfer_origins']
    assert d['point_order'] == ['internode', 'leaf']


def _interval_accounts(before_handle, after_handle, profiles):
    before, after = before_handle.current['numeric'], after_handle.current['numeric']
    seed = before_handle.basis['numeric_basis']['seed']; p = seed['program']
    n, m, h = len(p['leaves']), len(p['stem_root_compartments']), len(seed['organs']['internodes'])
    a, b = [list(map(Fraction, v['last_confirmed']['state'])) for v in [before, after]]
    t = {k: x(after['lifetime_transfers_exact'][k]) - x(before['lifetime_transfers_exact'][k]) for k in before['lifetime_transfers_exact']}
    ca = Fraction(before['last_confirmed']['derived']['air_capacity']['value'])
    latent = Fraction(profiles['exchange_profile'].values['latent_heat'])
    carbon = lambda y: y[0] + sum(y[3:53]) + sum(y[106 + 2*n:106 + 3*n + m])
    rows = {
        'carbohydrate': carbon(b)-carbon(a)-t['photosynthesis']+sum(t[k] for k in ['growth_respiration','maintenance_leaf','maintenance_stem','maintenance_fruit','removal_leaf','removal_stem','terminal_carbon']),
        'number': sum(b[53:103])-sum(a[53:103])-t['entry_number']+t['terminal_number'],
        'canopy_sensible': b[103]-a[103]-t['canopy_external']+t['sensible']+t['latent']-t['incoming_heat']+t['outgoing_heat'],
        'air_sensible': ca*(b[104]-a[104])-t['air_external']-t['sensible'],
        'vapor': b[105]-a[105]-t['vapor']-t['external_vapor'],
        'area_capacity': Fraction(after['last_confirmed']['derived']['canopy_capacity']['value'])-Fraction(before['last_confirmed']['derived']['canopy_capacity']['value'])-t['capacity_in']+t['capacity_out'],
        'reduced_energy': b[103]-a[103]+ca*(b[104]-a[104])+latent*(b[105]-a[105])-t['canopy_external']-t['air_external']-latent*t['external_vapor']-t['incoming_heat']+t['outgoing_heat'],
    }
    elapsed = x(after['at']['elapsed_seconds_exact']) - x(before['at']['elapsed_seconds_exact'])
    assert elapsed > 0
    for i, leaf in enumerate(p['leaves']):
        rows['leaf_age_' + str(i)] = b[106+i]-a[106+i]-(t['indoor_air_temperature_time']-Fraction(leaf['base_temperature']['value'])*elapsed)/86400
    for kind, offset, count in [('leaf', 106+2*n, n), ('stem_root', 106+3*n, m)]:
        for i in range(count):
            k = kind + '_' + str(i)
            rows[kind + '_carbon_' + str(i)] = b[offset+i]-a[offset+i]-t[k+'_inflow']+t[k+'_maintenance']+t[k+'_removal']
    rows['stem_root_carbon'] = sum(b[106+3*n:106+3*n+m])-sum(a[106+3*n:106+3*n+m])-sum(t['stem_root_'+str(i)+'_inflow'] for i in range(m))+sum(t['stem_root_'+str(i)+'_maintenance']+t['stem_root_'+str(i)+'_removal'] for i in range(m))
    size = 106+3*n+m
    indices = {v['compartment_id']: i for i, v in enumerate(p['stem_root_compartments'])}
    for kind, organs, offset, unit in [('leaf', seed['organs']['leaves'], 106+n, 'leaves'), ('internode', seed['organs']['internodes'], size+h, 'internodes')]:
        for i, organ in enumerate(organs):
            k = kind + '_' + str(i)
            stock = 'leaf_' + str(i) if kind == 'leaf' else 'stem_root_' + str(indices[organ['compartment_id']])
            rows[k+'_geometry'] = b[offset+i]-a[offset+i]-t[k+'_realized']
            rows[k+'_partition'] = t[k+'_extension']+t[k+'_unmapped']-t[stock+'_inflow']
            rows[k+'_construction'] = t[k+'_extension']-Fraction(seed['costs'][unit][i])*t[k+'_realized']/Fraction(p['model_floor_area']['value'])
            if kind == 'internode':
                rows[k+'_age'] = b[size+i]-a[size+i]-(t['indoor_air_temperature_time']-Fraction(organ['baseline']['base_temperature']['value'])*elapsed)/86400
    assert set(rows) == set(before['global_ledgers']) == set(after['global_ledgers'])
    for name, residual in rows.items():
        assert residual == x(after['global_ledgers'][name]['residual_exact'])-x(before['global_ledgers'][name]['residual_exact']), name
        assert abs(x(after['global_ledgers'][name]['residual_exact'])) <= x(after['global_ledgers'][name]['budget_exact']), name
    assert after['point_totals_exact'] == before['point_totals_exact']
    assert after['transfer_origins'] == before['transfer_origins']
    shoot_base = Fraction(before_handle.basis['numeric_basis']['shoot_base_temperature'])
    assert x(after['schedule']['age_exact']) == x(before['schedule']['age_exact'])+(t['indoor_air_temperature_time']-shoot_base*elapsed)/86400
    assert after['schedule']['consumed_sequence'] == before['schedule']['consumed_sequence']


def _positive_new_growth(receipt, after_handle):
    d = receipt['point_data']; p = d['after_program']; organs = d['after_organs']
    n, m, h = len(p['leaves']), len(p['stem_root_compartments']), len(organs['internodes'])
    size = 106+3*n+m; event = d['source_event']
    leaf = next(i for i, v in enumerate(p['leaves']) if v['leaf_id'] == event['leaf_id'])
    node = next(i for i, v in enumerate(organs['internodes']) if v['compartment_id'] == event['internode_id'])
    compartment = next(i for i, v in enumerate(p['stem_root_compartments']) if v['compartment_id'] == event['internode_id'])
    a = d['after_state']; b = after_handle.current['numeric']['last_confirmed']['state']
    assert b[106+n+leaf] > a[106+n+leaf], 'new leaf area did not grow beyond its seed'
    assert b[size+h+node] > a[size+h+node], 'new internode length did not grow beyond its seed'
    assert b[106+2*n+leaf] > a[106+2*n+leaf], 'new leaf structural stock did not grow'
    assert b[106+3*n+compartment] > a[106+3*n+compartment], 'new internode structural stock did not grow'


def _cold_without_generation(model, point_model, handle, workspace):
    entries = (
        (base.stage.evaluate, (None, None, None, None, None), {}),
        (point.apply_material_point, (None, None, None), {'inputs': None}),
        (candidate.calculate_threshold_state, (None, None, None), {}),
        (point_model.calculate_successor_candidate, (None, None, None), {}),
        (point_model.apply_successor_material_point, (None, None, None), {'inputs': None}),
        (model.adopt_successor, (None, None, None),
         {'inputs': None, 'expected_point_sha256': None, 'workspace': None}),
    )
    blocked = {function.__code__ for function, _, _ in entries}
    assert len(blocked) == 6
    monitoring = sys.monitoring
    event = monitoring.events.PY_START
    previous_profile, previous_trace = sys.getprofile(), sys.gettrace()
    tools_before = tuple((monitoring.get_tool(i), monitoring.get_events(i)) for i in range(6))
    tool = next(i for i in (3, 4) if monitoring.get_tool(i) is None)
    name = 'OpenSmartFarmSim-cold-six-entry-check'
    monitoring.use_tool_id(tool, name)
    previous_global = monitoring.get_events(tool)
    previous_local = {code: monitoring.get_local_events(tool, code) for code in blocked}
    previous_callback = None
    installed = False
    calls, controls = [], []
    phase, expected = 'control', None

    class EntrySeen(BaseException):
        pass

    def observe(code, offset):
        assert code in blocked
        if phase == 'control':
            assert code is expected
            controls.append(code)
            raise EntrySeen()
        calls.append(code.co_name)
        raise AssertionError('cold open entered forbidden numerical producer: ' + code.co_name)

    def positive_controls():
        nonlocal expected
        for function, args, kwargs in entries:
            expected = function.__code__
            count = len(controls)
            try:
                function(*args, **kwargs)
            except EntrySeen:
                pass
            else:
                raise AssertionError('entry observer did not stop the positive control')
            assert len(controls) == count + 1 and controls[-1] is expected

    try:
        assert previous_global == 0 and all(mask == 0 for mask in previous_local.values())
        previous_callback = monitoring.register_callback(tool, event, observe)
        installed = True
        assert previous_callback is None, 'unused monitoring slot has a stale callback'
        for code in blocked:
            monitoring.set_local_events(tool, code, event)
        positive_controls()
        phase = 'cold'
        cold = model.open_material(model.CursorRef(handle.cursor_sha256), handle._definition, workspace)
        phase = 'control'
        positive_controls()
        assert len(controls) == 12 and calls == []
        assert monitoring.get_tool(tool) == name and monitoring.get_events(tool) == 0
        assert all(monitoring.get_local_events(tool, code) == event for code in blocked)
    finally:
        for code, mask in previous_local.items():
            monitoring.set_local_events(tool, code, mask)
        monitoring.set_events(tool, previous_global)
        if installed:
            assert monitoring.register_callback(tool, event, previous_callback) is observe
        monitoring.free_tool_id(tool)
        assert tuple((monitoring.get_tool(i), monitoring.get_events(i)) for i in range(6)) == tools_before
        assert sys.getprofile() is previous_profile and sys.gettrace() is previous_trace
    # The unchanged old source may algebraically rederive its saved point using saved stage values.
    assert cold._current == handle._current and cold._basis == handle._basis and cold._cursor == handle._cursor
    return cold


def _advance_to_pending(model, point_model, handle, workspace, *, end, step_budget, cold_splits):
    emitted = []
    for _ in range(64):
        result = model.advance(handle, base.AdvanceRequest(q(end), step_budget=step_budget))
        assert result.status in {'yielded', 'awaiting_material'}, result.hold
        emitted.extend(result.emitted)
        assert result.progress['past_confirmed_intervals_reintegrated'] == 0
        if result.status == 'awaiting_material':
            return result, emitted
        assert result.handle.cursor_sha256 != handle.cursor_sha256, 'bounded request made no progress'
        handle = _cold_without_generation(model, point_model, result.handle, workspace) if cold_splits else result.handle
    raise AssertionError('bounded repeated continuation did not reach its next actual pending event')


def _repeat_history(handle, workspace):
    cursor_sha = handle.cursor_sha256; pages = []
    for _ in range(257):
        cursor = _read_blob(workspace.repeat_archive_directory, cursor_sha)
        if cursor['previous_cursor_sha256'] is None:
            return cursor, _read_blob(workspace.repeat_archive_directory, cursor['current_sha256']), pages
        page = _read_blob(workspace.repeat_archive_directory, cursor['history_page_sha256'])
        assert set(page) == {'schema_version','kind','definition_sha256','previous_cursor_sha256',
            'before_current_sha256','after_current_sha256','before_basis_sha256','after_basis_sha256','evidence'}
        assert page['schema_version'] == 'supply-material-repeat-history-page-v1'
        assert page['after_current_sha256'] == cursor['current_sha256']
        assert page['after_basis_sha256'] == cursor['basis_sha256']
        assert page['previous_cursor_sha256'] == cursor['previous_cursor_sha256']
        pages.append(page);cursor_sha = cursor['previous_cursor_sha256']
    raise AssertionError('repeat history exceeded original bounded transition plan')


def _repeat_path(model, point_model, old_handle, pending_sha, first_inputs, first_point, original_workspace,
                 origin, repeat_directory, *, step_budget, cold_splits):
    workspace = model.Workspace(original_workspace, repeat_directory, original_workspace.access)
    handle = old_handle; expected_sequence = old_handle.current['numeric']['schedule']['next_sequence']
    receipts = []; adoptions = []; emissions = []; growth = []
    for ordinal in [2, 3]:
        old_family = ordinal == 2
        family = 'supply-material-owner-research-v1' if old_family else 'supply-material-repeat-owner-research-v1'
        info = point_model.describe_successor_source(handle)
        assert info['schema_version'] == 'supply-material-successor-source-v1'
        assert info['source'] == _source_ref(handle, family)
        assert info['event']['sequence'] == expected_sequence
        located = point_model.calculate_successor_candidate(handle, pending_sha, TOLERANCE)
        assert located['status'] == 'candidate_ready', located.get('hold')
        assert located['source'] == info['source']
        assert located['checkpoint_issued'] is located['history_committed'] is located['material_consumed'] is False
        inputs = _successor_inputs(info, located, pending_sha, handle, first_inputs, ordinal)
        receipt = point_model.apply_successor_material_point(handle, pending_sha, TOLERANCE, inputs=inputs)
        assert receipt['status'] == 'point_ready', receipt.get('hold')
        assert receipt['candidate_sha256'] == located['calculation_sha256']
        assert receipt['source'] == info['source'] and receipt['inputs'] == inputs
        assert receipt['calculation_sha256'] == sha256(canonical({k:v for k,v in receipt.items() if k != 'calculation_sha256'})).hexdigest()
        assert receipt['checkpoint_issued'] is receipt['history_committed'] is receipt['material_consumed'] is False
        assert receipt['elapsed_seconds_advanced'] == q(0) and receipt['schedule_adoption'] == 'not_performed'
        _point_accounts(receipt, handle, origin['profiles'])
        adopted = model.adopt_successor(handle, pending_sha, TOLERANCE, inputs=inputs,
            expected_point_sha256=receipt['calculation_sha256'], workspace=workspace)
        assert adopted.status == 'adopted', adopted.hold
        after = adopted.handle; data = receipt['point_data']; numeric = after.current['numeric']
        assert type(after) is model.Handle and type(after) is not material.Handle
        assert len(adopted.emitted) == 2
        assert [v['phase'] for v in adopted.emitted] == ['material_before','material_after']
        assert all(v['at'] == data['at'] for v in adopted.emitted)
        assert after.current['at'] == data['at'] == receipt['candidate']['at']
        assert after.current['at']['elapsed_seconds_exact'] == located['root_certificate']['root']['upper_elapsed_seconds_exact']
        assert after.current['at']['time_origin_utc'] == old_handle.current['at']['time_origin_utc']
        assert numeric['last_confirmed']['state'] == data['after_state']
        assert numeric['schedule']['consumed_sequence'] == expected_sequence
        assert numeric['schedule']['consumed_event_id'] == data['source_event']['source_event_id']
        assert numeric['schedule']['age_exact'] == data['before_dense']['shoot_age_exact']
        assert numeric['event_sequence'] == handle.current['numeric']['event_sequence'] + 1
        assert numeric['schedule']['next_sequence'] == expected_sequence + 1
        assert x(numeric['schedule']['next_threshold_exact']) == x(data['source_event']['threshold_exact']) + x(info['timeline']['phyllochron_exact'])
        assert numeric['point_totals_exact'] == data['post_point_point_totals_exact_preview']
        assert numeric['global_ledgers'] == data['post_point_global_ledgers_preview']
        assert numeric['lifetime_transfers_exact'] == data['post_point_lifetime_transfers_exact_preview']
        seed = after.basis['numeric_basis']['seed']
        assert seed['program'] == data['after_program'] and seed['organs'] == data['after_organs']
        assert seed['birth_bases'] == data['after_birth_baselines'] and seed['geometry_baselines'] == data['after_geometry_baselines']
        assert after.current['lifetime']['material_adoptions'] == ordinal
        assert after.current['effective_rights']['redistribute'] is False
        root_cursor, root_current, pages = _repeat_history(after, workspace)
        page = pages[0]; assert page['kind'] == 'material_adoption'
        assert page['evidence']['source_owner_version'] == family
        assert page['evidence']['point_sha256'] == sha256(canonical(receipt)).hexdigest()
        assert page['evidence']['before_frame_sha256'] == sha256(canonical(adopted.emitted[0])).hexdigest()
        assert page['evidence']['after_frame_sha256'] == sha256(canonical(adopted.emitted[1])).hexdigest()
        assert root_current['phase'] == 'source_anchor'
        assert root_current['output_cursor'] == old_handle.current['output_cursor']
        assert root_current['output_prefix_sha256'] == old_handle.current['output_prefix_sha256']
        root_numeric = {k:v for k,v in root_current['numeric'].items() if k not in {'schema_version','code_sha256'}}
        old_numeric = {k:v for k,v in old_handle.current['numeric'].items() if k not in {'schema_version','code_sha256'}}
        assert root_numeric == old_numeric
        assert after.current['lifetime']['repeat_transitions'] == len(pages)
        assert after.current['lifetime']['positive_segments'] > root_current['lifetime']['positive_segments']
        represented_RHS = sum(receipt['work'][k] for k in ['interval_replay_RHS_evaluations','dense_state_RHS_evaluations','point_stage_RHS_evaluations'])
        prior_lifetime = root_current['lifetime'] if old_family else handle.current['lifetime']
        assert after.current['lifetime']['committed_RHS_evaluations'] == prior_lifetime['committed_RHS_evaluations'] + represented_RHS
        assert after.current['lifetime']['repeat_transitions'] == prior_lifetime['repeat_transitions'] + 1
        assert after.current['lifetime']['frames'] == prior_lifetime['frames'] + 2
        assert after.current['lifetime']['positive_segments'] == prior_lifetime['positive_segments'] + 1
        stale = model.adopt_successor(after, pending_sha, TOLERANCE, inputs=inputs,
            expected_point_sha256=receipt['calculation_sha256'], workspace=workspace)
        assert stale.status == 'hold'
        if stale.handle is not None:
            assert stale.handle.cursor_sha256 == after.cursor_sha256
        assert stale.emitted == []
        after = _cold_without_generation(model, point_model, after, workspace)
        if ordinal == 2:
            continuation, frames = _advance_to_pending(model, point_model, after, workspace,
                end=768, step_budget=step_budget, cold_splits=cold_splits)
            grown = continuation.handle; pending_sha = continuation.pending['page_sha256']
            assert continuation.pending['material_consumed'] is False
            page_raw = _read_blob(workspace.repeat_archive_directory, pending_sha)
            assert set(page_raw) == {'schema_version','definition_sha256','previous_cursor_sha256','interval','schedule','material_consumed'}
            assert page_raw['schema_version'] == 'supply-material-repeat-pending-page-v1'
            assert page_raw['previous_cursor_sha256'] == grown.cursor_sha256 and page_raw['material_consumed'] is False
            assert grown.current['numeric']['schedule']['next_sequence'] == expected_sequence + 1
        else:
            horizon = after.current['numeric']['next_grid_endpoint_exact']
            continuation = model.advance(after, base.AdvanceRequest(horizon, step_budget=step_budget))
            assert continuation.status in {'yielded','completed'} and continuation.pending is None, continuation.hold
            grown = continuation.handle; frames = continuation.emitted
            assert grown.current['at']['elapsed_seconds_exact'] == horizon
            assert x(horizon) <= 768 and x(horizon) % 8 == 0
        _interval_accounts(after, grown, origin['profiles'])
        _positive_new_growth(receipt, grown)
        receipts.append(receipt); adoptions.append(adopted); emissions.extend(adopted.emitted); emissions.extend(frames)
        growth.append({'source_sequence': expected_sequence, 'at_seed': data['at'], 'at_grown': grown.current['at']})
        handle = _cold_without_generation(model, point_model, grown, workspace)
        expected_sequence += 1
    assert len({v['point_data']['source_event']['source_event_id'] for v in receipts}) == 2
    assert any(v['phase'] == 'forcing_after' for v in emissions)
    root_cursor, root_current, pages = _repeat_history(handle, workspace)
    assert {v['kind'] for v in pages} == {'material_adoption','interval','forcing_switch'}
    assert handle.current['lifetime']['material_adoptions'] == 3
    assert handle.current['lifetime']['forcing_switches'] > root_current['lifetime']['forcing_switches']
    return {'handle':handle,'workspace':workspace,'receipts':receipts,'adoptions':adoptions,'growth':growth,'emissions':emissions}


def test_actual_second_and_third_material_adoptions_grow_with_original_accounts(origin, tmp_path):
    # These are explicit software-fixture boundaries, not observed root times.
    edge, end = 600, 768
    forcing_workspace, definition, declaration = setup_owner(origin, tmp_path, edge=edge, end=end)
    start = forcing.open_season(origin['source_ref'], definition, forcing_workspace)
    first_pending = forcing.advance(start, base.AdvanceRequest(q(end), step_budget=128))
    assert first_pending.status == 'awaiting_material', first_pending.hold
    assert first_pending.pending['schedule_consumed'] is False
    first_pending_raw = (forcing_workspace.archive_directory / first_pending.pending['page_sha256']).read_bytes()
    first_page = json.loads(first_pending_raw)
    assert set(first_page) == {'schema_version', 'definition_sha256', 'previous_cursor_sha256', 'result', 'reason'}
    assert first_page['schema_version'] == 'supply-forcing-pending-page-v1'
    assert first_page['result']['material_consumed'] is False
    first_sequence = first_pending.handle.current['numeric']['schedule']['next_sequence']
    threshold_state = candidate.calculate_threshold_state(
        first_pending.handle, first_pending.pending['page_sha256'], TOLERANCE)
    assert threshold_state['status'] == 'candidate_ready', threshold_state.get('hold')
    input_document = make_inputs({'workspace': forcing_workspace, 'definition': definition,
                                 'document': declaration, 'result': first_pending}, threshold_state)
    point_result = point.apply_material_point(
        first_pending.handle, first_pending.pending['page_sha256'], TOLERANCE, inputs=input_document)
    assert point_result['status'] == 'point_ready', point_result.get('hold')
    material_workspace = material.Workspace(forcing_workspace, tmp_path / 'material-cas', forcing_workspace.access)
    adopted = material.adopt_material(first_pending.handle, first_pending.pending['page_sha256'], TOLERANCE,
        inputs=input_document, expected_point_sha256=point_result['calculation_sha256'], workspace=material_workspace)
    assert adopted.status == 'adopted', adopted.hold
    assert type(adopted.handle) is material.Handle and adopted.handle._token is material._TOKEN
    first_current_raw = adopted.handle._current
    first_schedule = adopted.handle.current['numeric']['schedule']
    assert first_schedule['consumed_sequence'] == first_sequence
    assert first_schedule['next_sequence'] == first_sequence + 1

    next_pending = material.advance(adopted.handle, base.AdvanceRequest(q(end), step_budget=128))
    assert next_pending.status == 'awaiting_material', next_pending.hold
    assert next_pending.pending['material_consumed'] is False
    handle = next_pending.handle
    assert type(handle) is material.Handle and handle._token is material._TOKEN
    assert adopted.handle._current == first_current_raw
    pending_raw = (material_workspace.archive_directory / next_pending.pending['page_sha256']).read_bytes()
    assert sha256(pending_raw).hexdigest() == next_pending.pending['page_sha256']
    page = json.loads(pending_raw)
    assert set(page) == {'schema_version', 'definition_sha256', 'previous_cursor_sha256',
                         'interval', 'schedule', 'material_consumed'}
    assert page['schema_version'] == 'supply-material-pending-page-v1'
    assert page['definition_sha256'] == handle._definition
    assert page['previous_cursor_sha256'] == handle.cursor_sha256
    assert page['material_consumed'] is False
    current = handle.current
    schedule = current['numeric']['schedule']
    assert schedule['consumed_sequence'] == first_sequence
    assert schedule['consumed_event_id'] == first_schedule['consumed_event_id']
    assert schedule['next_sequence'] == first_sequence + 1
    assert schedule['next_threshold_exact'] == first_schedule['next_threshold_exact']
    assert page['schedule']['next_sequence'] == schedule['next_sequence']
    assert page['schedule']['next_threshold_exact'] == schedule['next_threshold_exact']
    assert x(schedule['age_exact']) < x(schedule['next_threshold_exact'])
    assert x(page['schedule']['age_exact']) >= x(schedule['next_threshold_exact'])
    assert page['interval']['left_elapsed_seconds_exact'] == current['at']['elapsed_seconds_exact']
    assert x(page['interval']['right_elapsed_seconds_exact']) > x(current['at']['elapsed_seconds_exact'])
    assert page['interval']['stages'][0]['state'] == current['numeric']['last_confirmed']['state']
    assert current['numeric']['last_confirmed']['at'] == current['at']
    assert current['numeric']['event_sequence'] == adopted.handle.current['numeric']['event_sequence']
    assert next_pending.progress['past_intervals_reintegrated'] == 0
    assert current['effective_rights']['redistribute'] is False
    cursor = json.loads(handle._cursor)
    assert cursor['current_sha256'] == sha256(handle._current).hexdigest()
    cold = material.open_material(material.CursorRef(handle.cursor_sha256), handle._definition, material_workspace)
    assert cold._current == handle._current and cold._basis == handle._basis and cold._cursor == handle._cursor

    exports = {
        'baseline-first-forcing-pending-v1.private.json': first_pending_raw,
        'baseline-first-point-input-v1.private.json': canonical(input_document),
        'baseline-first-point-result-v1.private.json': canonical(point_result),
        'baseline-first-material-current-v1.private.json': first_current_raw,
        'baseline-second-material-pending-v1.private.json': pending_raw,
        'baseline-confirmed-current-v1.private.json': handle._current,
        'baseline-confirmed-basis-v1.private.json': handle._basis,
        'baseline-confirmed-cursor-v1.private.json': handle._cursor,
        'baseline-material-definition-v1.private.json': (material_workspace.archive_directory / handle._definition).read_bytes(),
        'baseline-forcing-definition-v1.private.json': (forcing_workspace.archive_directory / definition).read_bytes(),
    }
    for name, raw in exports.items():
        (tmp_path / name).write_bytes(raw)
    proof = {
        'schema_version': 'private-original-material-second-pending-baseline-v1',
        'fixture': {'declared_forcing_edge_seconds': edge, 'declared_end_seconds': end,
                    'edge_is_observed_root_time': False, 'old_end536_fixture_modified': False},
        'source_cursor_sha256': origin['source_ref'].cursor_sha256,
        'forcing_definition_sha256': definition,
        'first_material_definition_sha256': handle._definition,
        'first_material_cursor_sha256': adopted.handle.cursor_sha256,
        'confirmed_cursor_sha256': handle.cursor_sha256,
        'actual_sequences': {'first_branch_consumed': first_sequence,
                            'second_branch_pending': schedule['next_sequence'],
                            'third_branch_if_later_consumed': schedule['next_sequence'] + 1},
        'first_material_at': adopted.handle.current['at'],
        'confirmed_at': current['at'],
        'unconfirmed_interval_right': page['interval']['right_elapsed_seconds_exact'],
        'current_schedule': schedule, 'pending_schedule': page['schedule'],
        'pending_page_sha256': next_pending.pending['page_sha256'],
        'material_consumed': False,
        'confirmed_current_is_pending_interval_left_and_not_its_endpoint': True,
        'cold_current_basis_cursor_bytes_equal': True,
        'first_point_calculation_sha256': point_result['calculation_sha256'],
        'original_operator_progress': {'first_adoption': adopted.progress, 'second_pending': next_pending.progress},
        'exports': {name: {'sha256': sha256(raw).hexdigest(), 'bytes': len(raw)} for name, raw in exports.items()},
        'new_repeat_API_used': False, 'second_or_third_adoption_claimed': False,
        'db_used': False, 'scope': 'self-authored synthetic software baseline only',
        'G0_G4': 'not_assessed', 'R2': 'not_approved', 'whole_goal_complete': False,
    }
    (tmp_path / 'baseline-proof-v1.private.json').write_bytes(canonical(proof))

    # The complete real old-owner baseline above must succeed BEFORE missing-feature admission.
    from app import crop_supply_material_repeat_point as repeat_point
    from app import crop_supply_material_repeat_owner as repeat_owner
    from app import crop_supply_material_repeat_proof as repeat_proof
    assert Path(repeat_proof.__file__).is_file()
    full = _repeat_path(repeat_owner, repeat_point, handle, next_pending.pending['page_sha256'],
        input_document, point_result, material_workspace, origin, tmp_path / 'repeat-full',
        step_budget=128, cold_splits=False)
    split = _repeat_path(repeat_owner, repeat_point, handle, next_pending.pending['page_sha256'],
        input_document, point_result, material_workspace, origin, tmp_path / 'repeat-split',
        step_budget=1, cold_splits=True)
    assert full['handle']._definition == split['handle']._definition
    assert full['handle'].cursor_sha256 == split['handle'].cursor_sha256
    assert full['handle']._current == split['handle']._current
    assert full['handle']._basis == split['handle']._basis
    assert full['handle']._cursor == split['handle']._cursor
    assert [v['calculation_sha256'] for v in full['receipts']] == [v['calculation_sha256'] for v in split['receipts']]
    assert full['growth'] == split['growth']
    final = full['handle']
    repeat_exports = {
        'repeat-final-current-v1.private.json': final._current,
        'repeat-final-basis-v1.private.json': final._basis,
        'repeat-final-cursor-v1.private.json': final._cursor,
        'repeat-definition-v1.private.json': (full['workspace'].repeat_archive_directory / final._definition).read_bytes(),
    }
    for ordinal, receipt in enumerate(full['receipts'], 2):
        repeat_exports['repeat-point-' + str(ordinal) + '-v1.private.json'] = canonical(receipt)
    for name, raw in repeat_exports.items():
        (tmp_path / name).write_bytes(raw)
    (tmp_path / 'repeat-growth-proof-v1.private.json').write_bytes(canonical({
        'schema_version':'private-repeat-material-functional-proof-v1',
        'source_baseline_cursor_sha256':handle.cursor_sha256,
        'actual_source_sequences':[v['point_data']['source_event']['sequence'] for v in full['receipts']],
        'source_event_ids':[v['point_data']['source_event']['source_event_id'] for v in full['receipts']],
        'final_cursor_sha256':final.cursor_sha256,'final_at':final.current['at'],
        'final_lifetime':final.current['lifetime'],'growth':full['growth'],
        'full_split_current_basis_cursor_and_point_bytes_equal':True,
        'cold_inprocess_stage_RHS_and_public_generation_calls':0,
        'original_saved_stage_algebraic_verification_permitted':True,
        'independent_cold_subprocess_proof_claimed':False,
        'independent_point_and_interval_accounts_checked':True,
        'exports':{name:{'sha256':sha256(raw).hexdigest(),'bytes':len(raw)} for name,raw in repeat_exports.items()},
        'G0_G4':'not_assessed','R2':'not_approved','whole_goal_complete':False,
    }))


# Fixed source-session regressions share only their genuine immutable source fixture.
from contextlib import contextmanager
import os
import stat
import pytest
from app import crop_supply_material_owner as original
from app import crop_supply_material_point as old_point
from app import crop_supply_forcing_threshold_state as old_candidate
from app import crop_supply_material_repeat_point as repeat_point_model
from app.content_access import ContentAccess
from app.crop_morphology_artifact_io import MorphologyBlobStore, MorphologyArtifactHold
from app.job_store import JobStore



@pytest.fixture(scope='module')
def real_repeat_fault_case(origin, tmp_path_factory):
    from app import crop_supply_material_repeat_point as point
    from app import crop_supply_material_repeat_owner as owner
    directory = tmp_path_factory.mktemp('real-repeat-review-faults')
    fws, definition, declaration = setup_owner(origin, directory, edge=600, end=768)
    pending = forcing.advance(forcing.open_season(origin['source_ref'], definition, fws),
        base.AdvanceRequest(q(768), step_budget=128))
    assert pending.status == 'awaiting_material', pending.hold
    state = old_candidate.calculate_threshold_state(pending.handle, pending.pending['page_sha256'], TOLERANCE)
    assert state['status'] == 'candidate_ready', state.get('hold')
    inputs = make_inputs({'workspace':fws,'definition':definition,'document':declaration,'result':pending}, state)
    receipt = old_point.apply_material_point(pending.handle, pending.pending['page_sha256'], TOLERANCE, inputs=inputs)
    assert receipt['status'] == 'point_ready', receipt.get('hold')
    mws = original.Workspace(fws, directory / 'original-material', fws.access)
    adopted = original.adopt_material(pending.handle, pending.pending['page_sha256'], TOLERANCE,
        inputs=inputs, expected_point_sha256=receipt['calculation_sha256'], workspace=mws)
    assert adopted.status == 'adopted', adopted.hold
    pending = original.advance(adopted.handle, base.AdvanceRequest(q(768), step_budget=128))
    assert pending.status == 'awaiting_material' and pending.pending['material_consumed'] is False, pending.hold
    before = pending.handle
    assert type(before) is original.Handle and before.current['numeric']['schedule']['next_sequence'] == 13
    info = point.describe_successor_source(before)
    assert info['source'] == _source_ref(before, 'supply-material-owner-research-v1')
    candidate = point.calculate_successor_candidate(before, pending.pending['page_sha256'], TOLERANCE)
    assert candidate['status'] == 'candidate_ready', candidate.get('hold')
    next_inputs = _successor_inputs(info, candidate, pending.pending['page_sha256'], before, inputs, 2)
    next_point = point.apply_successor_material_point(before, pending.pending['page_sha256'], TOLERANCE, inputs=next_inputs)
    assert next_point['status'] == 'point_ready', next_point.get('hold')
    workspace = owner.Workspace(mws, directory / 'repeat', mws.access)
    result = owner.adopt_successor(before, pending.pending['page_sha256'], TOLERANCE, inputs=next_inputs,
        expected_point_sha256=next_point['calculation_sha256'], workspace=workspace)
    assert result.status == 'adopted', result.hold
    assert type(result.handle) is owner.Handle
    assert result.handle.current['numeric']['schedule']['consumed_sequence'] == 13
    return {'owner':owner,'point':point,'after':result.handle,'old_source':before,
            'pending_sha':pending.pending['page_sha256'],'workspace':workspace,'original_workspace':mws}



def _fd_count():
    return len(os.listdir('/proc/self/fd'))



@contextmanager
def _watch(observe, codes):
    monitoring = sys.monitoring
    start, returned = monitoring.events.PY_START, monitoring.events.PY_RETURN
    mask = start | returned
    profile_before, trace_before = sys.getprofile(), sys.gettrace()
    tools_before = tuple((monitoring.get_tool(i), monitoring.get_events(i)) for i in range(6))
    tool = next(i for i in (3, 4) if monitoring.get_tool(i) is None)
    previous_local, previous_callbacks = {}, {}
    monitoring.use_tool_id(tool, 'OpenSmartFarmSim-cold-saved-algebra')
    previous_global = monitoring.get_events(tool)

    def arm(code):
        if code not in previous_local:
            previous_local[code] = monitoring.get_local_events(tool, code)
            assert previous_local[code] == 0, 'unused cold observer slot has stale local events'
            monitoring.set_local_events(tool, code, mask)

    def started(code, offset):
        frame = sys._getframe(1)
        assert frame.f_code is code, 'PY_START must expose the genuine callee frame'
        observe(frame, 'call', None)

    def finished(code, offset, value):
        frame = sys._getframe(1)
        assert frame.f_code is code, 'PY_RETURN must expose the genuine callee frame'
        observe(frame, 'return', value)

    try:
        assert previous_global == 0, 'unused cold observer slot has stale global events'
        for event, callback in ((start, started), (returned, finished)):
            prior = monitoring.register_callback(tool, event, callback)
            previous_callbacks[event] = (prior, callback)
            assert prior is None, 'unused cold observer slot has stale callback'
        for code in codes:
            arm(code)
        try:
            yield arm
        except BaseException as error:
            # PY_UNWIND is not local in 3.12. Preserve selected failed frames from
            # the real propagating exception, without enabling global events.
            traceback = error.__traceback__
            while traceback is not None:
                frame = traceback.tb_frame
                if frame.f_code in previous_local:
                    observe(frame, 'unwind', error)
                traceback = traceback.tb_next
            raise
    finally:
        for code, prior in previous_local.items():
            monitoring.set_local_events(tool, code, prior)
        monitoring.set_events(tool, previous_global)
        restored_callbacks = []
        for event, (prior, callback) in previous_callbacks.items():
            restored_callbacks.append(monitoring.register_callback(tool, event, prior) is callback)
        monitoring.free_tool_id(tool)
        assert all(restored_callbacks), 'production replaced cold observer callbacks'
        assert all(monitoring.get_local_events(tool, code) == prior for code, prior in previous_local.items())
        assert tuple((monitoring.get_tool(i), monitoring.get_events(i)) for i in range(6)) == tools_before
        assert sys.getprofile() is profile_before and sys.gettrace() is trace_before



def _owned_directory(tmp_path):
    access = ContentAccess(os.geteuid(), os.getegid())
    directory = tmp_path / 'owned'
    directory.mkdir(mode=0o750)
    directory.chmod(0o750)
    fd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        access.require_writer()
        access.validate(fd, directory=True)
    finally:
        os.close(fd)
    return directory, access



def _release(store):
    # Test-owned emergency cleanup, independent of any rejected Python close hook.
    if store is not None and store.__dict__.get('_fd') is not None:
        os.close(store.__dict__['_fd'])
        store.__dict__['_fd'] = None



def _store_state(store, directory, access, write):
    assert type(store) is MorphologyBlobStore
    assert set(store.__dict__) == {'_fd', '_access', '_write', '_jobs'}
    assert store._access is access and store._write is write
    assert type(store._jobs) is JobStore
    assert store._jobs.artifact_root == directory and store._jobs.content_access is access
    assert store._jobs.schema == 'morphology_research'
    assert type(store._fd) is int
    held = os.fstat(store._fd); named = directory.stat(follow_symlinks=False)
    assert stat.S_ISDIR(held.st_mode) and stat.S_IMODE(held.st_mode) == 0o750
    assert held.st_uid == access.owner_uid and held.st_gid == access.reader_gid
    assert (held.st_dev, held.st_ino) == (named.st_dev, named.st_ino)
    access.validate(store._fd, directory=True)
    store._guard()
    return {'directory': str(directory), 'write': write, 'fd': store._fd,
            'device': held.st_dev, 'inode': held.st_ino, 'mode': stat.S_IMODE(held.st_mode)}



def _source_directories(workspace):
    f = workspace.forcing_workspace; b = f.source_workspace
    return [(workspace.archive_directory, workspace.access, True),
            (f.archive_directory, f.access, True),
            (b.archive_directory, b.access, True),
            (b.source_directory, b.access, False)]



def _inventory(directories):
    result = {}
    for directory in directories:
        entries = {}
        for path in directory.iterdir():
            info = path.stat(follow_symlinks=False)
            assert stat.S_ISREG(info.st_mode)
            entries[path.name] = (info.st_dev, info.st_ino, info.st_mode, info.st_uid,
                info.st_gid, info.st_nlink, info.st_size, info.st_mtime_ns, info.st_ctime_ns,
                sha256(path.read_bytes()).hexdigest())
        result[str(directory)] = entries
    return result



def _source_value(s):
    fields = ('definition', 'source_current', 'point', 'math_basis', 'origins', 'basis',
              'spans', 'grid', 'stop', 'rights', 'basis_raw')
    return {'fields': {name: deepcopy(getattr(s, name)) for name in fields},
            'profiles': {name: (type(profile).__module__, type(profile).__qualname__,
                profile.sha256, dict(profile.values)) for name, profile in s.profiles.items()}}



def _admission_observer(expected):
    opened = []; forbidden = []
    init = repeat_point_model._open_store_v2
    prohibited = {MorphologyBlobStore.__init__.__code__: 'legacy_constructor',
        MorphologyBlobStore.__enter__.__code__: 'legacy_enter',
        MorphologyBlobStore.__exit__.__code__: 'legacy_exit',
        MorphologyBlobStore.put.__code__: 'CAS_put', base.stage.evaluate.__code__: 'live_RHS',
        base._session.__wrapped__.__code__: 'legacy_base_session',
        forcing._session.__wrapped__.__code__: 'legacy_forcing_session',
        original._session.__wrapped__.__code__: 'legacy_material_session',
        JobStore.connect.__code__: 'SQL_connection'}
    def observe(frame, event, value):
        if event == 'call' and frame.f_code in prohibited:
            forbidden.append(prohibited[frame.f_code])
            raise AssertionError('forbidden source-session-v2 dispatch: ' + forbidden[-1])
        if event == 'return' and frame.f_code is init.__code__ and type(value) is MorphologyBlobStore:
            index = len(opened)
            assert index < len(expected), 'unexpected extra real source store'
            opened.append((value, _store_state(value, *expected[index])))
    return observe, tuple(prohibited) + (init.__code__,), opened, forbidden



@pytest.mark.parametrize('write', [False, True])
def test_fixed_initializer_returns_real_owned_store_after_actual_preconditions(tmp_path, write):
    directory, access = _owned_directory(tmp_path)
    before = _fd_count(); store = None; old_calls = []
    # The meaningful baseline RED happens here, after real rights/path/fd checks.
    initializer = repeat_point_model._open_store_v2
    blocked = {MorphologyBlobStore.__init__.__code__, MorphologyBlobStore.__enter__.__code__,
               MorphologyBlobStore.__exit__.__code__}
    def observe(frame, event, value):
        if event == 'call' and frame.f_code in blocked:
            old_calls.append(frame.f_code.co_name)
            raise AssertionError('new initializer dispatched legacy constructor/context')
    try:
        with _watch(observe, blocked):
            store = initializer(directory, access, write=write, meter=repeat_point_model._Meter())
        actual = _store_state(store, directory, access, write)
        assert not old_calls
        assert actual['fd'] is not None
    finally:
        _release(store)
    assert _fd_count() == before
    assert list(directory.iterdir()) == []



@pytest.mark.parametrize('fault', ['relative', 'parent_component', 'symlink', 'owner', 'mode', 'write_type'])
def test_fixed_initializer_rejects_actual_invalid_storage_without_fd_leak(tmp_path, fault):
    directory, access = _owned_directory(tmp_path)
    target = directory; supplied_access = access; write = False
    if fault == 'relative':
        target = Path('relative-source-store')
    elif fault == 'parent_component':
        target = directory / '..' / directory.name
    elif fault == 'symlink':
        target = tmp_path / 'link'; target.symlink_to(directory, target_is_directory=True)
    elif fault == 'owner':
        supplied_access = ContentAccess(access.owner_uid + 1, access.reader_gid)
    elif fault == 'mode':
        directory.chmod(0o700)
    elif fault == 'write_type':
        write = 1
    before = _fd_count(); entries = list(directory.iterdir())
    with pytest.raises(MorphologyArtifactHold):
        repeat_point_model._open_store_v2(target, supplied_access, write=write, meter=repeat_point_model._Meter())
    assert _fd_count() == before
    assert list(directory.iterdir()) == entries



def test_fixed_initializer_enforces_actual_exclusive_writer_lock(tmp_path):
    directory, access = _owned_directory(tmp_path)
    before = _fd_count(); first = second = None
    try:
        first = repeat_point_model._open_store_v2(directory, access, write=True, meter=repeat_point_model._Meter())
        _store_state(first, directory, access, True)
        held_count = _fd_count()
        with pytest.raises(MorphologyArtifactHold):
            second = repeat_point_model._open_store_v2(directory, access, write=True, meter=repeat_point_model._Meter())
        assert _fd_count() == held_count
        _store_state(first, directory, access, True)
    finally:
        _release(second); _release(first)
    assert _fd_count() == before



@pytest.mark.parametrize('mutation', ['function', 'property', 'code'])
def test_partial_initializer_fd_is_closed_without_rejected_close_dispatch(tmp_path, mutation):
    directory, access = _owned_directory(tmp_path)
    initializer = repeat_point_model._open_store_v2
    original_close = MorphologyBlobStore.close; original_code = original_close.__code__
    calls = []; acquired = []; changed = []
    marker = '_repeat_close_codeswap_calls_v1'; sentinel = object()
    globals_map = original_close.__globals__; prior_marker = globals_map.get(marker, sentinel)
    def rejected_close(store):
        calls.append(store.__dict__.get('_fd'))
        return original_close(store)
    def rejected_getter(store):
        calls.append(store.__dict__.get('_fd'))
        return original_close.__get__(store, type(store))
    def rejected_code(store):
        _repeat_close_codeswap_calls_v1.append(store.__dict__.get('_fd'))
        if store.__dict__.get('_fd') is not None:
            os.close(store.__dict__['_fd'])
            store.__dict__['_fd'] = None
    def observe(frame, event, value):
        if event == 'return' and frame.f_code is JobStore._content_directory.__code__ and not changed:
            caller = frame.f_back
            if caller is not None and caller.f_code is initializer.__code__ and type(value) is int:
                assert stat.S_ISDIR(os.fstat(value).st_mode)
                acquired.append(value); changed.append(mutation)
                if mutation == 'function':
                    MorphologyBlobStore.close = rejected_close
                elif mutation == 'property':
                    MorphologyBlobStore.close = property(rejected_getter)
                else:
                    assert original_code.co_freevars == rejected_code.__code__.co_freevars == ()
                    globals_map[marker] = calls
                    original_close.__code__ = rejected_code.__code__
    before = _fd_count()
    try:
        with pytest.raises(MorphologyArtifactHold) as held:
            with _watch(observe, [JobStore._content_directory.__code__]):
                initializer(directory, access, write=True, meter=repeat_point_model._Meter())
        assert 'CODE_HOLD:' in str(held.value)
    finally:
        original_close.__code__ = original_code
        MorphologyBlobStore.close = original_close
        if prior_marker is sentinel:
            globals_map.pop(marker, None)
        else:
            globals_map[marker] = prior_marker
    assert changed == [mutation] and len(acquired) == 1, 'must mutate only after genuine FD acquisition'
    for fd in acquired:
        with pytest.raises(OSError):
            os.fstat(fd)
    assert _fd_count() == before
    assert calls == [], 'rejected Python close hook/code was executed in partial initializer cleanup'



@pytest.mark.parametrize('mutation', ['function', 'property'])
def test_source_archive_exception_closes_real_fd_without_rejected_hook(tmp_path, mutation):
    directory, access = _owned_directory(tmp_path)
    original_close = MorphologyBlobStore.close; calls = []; store = None
    error = RuntimeError('explicit-test-original-body-error'); before = _fd_count()
    production_closed = None; production_fd_count = None
    def rejected_close(value):
        calls.append(value._fd)
        return original_close(value)
    def rejected_getter(value):
        calls.append(value._fd)
        return original_close.__get__(value, type(value))
    try:
        with pytest.raises(RuntimeError) as caught:
            with repeat_point_model._source_archive_v2(directory, access, write=True, meter=repeat_point_model._Meter()) as store:
                _store_state(store, directory, access, True)
                MorphologyBlobStore.close = rejected_close if mutation == 'function' else property(rejected_getter)
                raise error
        assert caught.value is error
    finally:
        MorphologyBlobStore.close = original_close
        production_closed = store is not None and store.__dict__.get('_fd') is None
        production_fd_count = _fd_count()
        _release(store)
    assert production_closed is True, 'production cleanup must close FD before test emergency cleanup'
    assert production_fd_count == before
    assert store is not None and store._fd is None
    assert _fd_count() == before
    assert calls == []



def test_actual_old_560_public_source_new_admission_is_byte_equivalent_without_generation(real_repeat_fault_case, tmp_path):
    c = real_repeat_fault_case; source = c['old_source']; workspace = c['original_workspace']
    cold = original.open_material(original.CursorRef(source.cursor_sha256), source._definition, workspace)
    assert cold._current == source._current and cold._basis == source._basis and cold._cursor == source._cursor
    assert source.current['at']['elapsed_seconds_exact'] == q(560)
    with original._session(source._definition, workspace) as old_session:
        old_cursor, old_current = original._restore(old_session, source.cursor_sha256)
        original._check(old_session)
        expected_value = _source_value(old_session)
    expected = _source_directories(workspace)
    before = _fd_count(); inventory = _inventory([d for d,a,w in expected])
    observe, codes, opened, forbidden = _admission_observer(expected)
    with _watch(observe, codes):
        with repeat_point_model._material_source_session_v2(source._definition, workspace, repeat_point_model._Meter()) as actual:
            cursor, current = original._restore(actual, source.cursor_sha256)
            original._check(actual)
            assert repeat_point_model.raw(cursor, base.CURRENT_MAX) == source._cursor
            assert repeat_point_model.raw(current, base.CURRENT_MAX) == source._current
            assert actual.basis_raw == source._basis
            assert _source_value(actual) == expected_value
    assert len(opened) == 4 and not forbidden
    assert all(store._fd is None for store,state in opened)
    assert _fd_count() == before
    assert _inventory([d for d,a,w in expected]) == inventory
    (tmp_path/'source-session-v2-old560-equivalence.private.json').write_bytes(canonical({
        'source_cursor_sha256': source.cursor_sha256,
        'current_sha256': sha256(source._current).hexdigest(), 'basis_sha256': sha256(source._basis).hexdigest(),
        'actual_new_initializer_stores': [state for store,state in opened], 'legacy_constructor_sessions_executed':False,
        'live_RHS_CAS_SQL_dispatches':forbidden,'raw3_and_profile_origin_rights_equal':True,
        'source_files_unchanged':True,'FD_before_after':[before,_fd_count()],
        'G0_G4':'not_assessed','R2':'not_approved'}))



def test_actual_repeat_owner_integration_uses_five_real_new_initializer_stores(real_repeat_fault_case, tmp_path):
    c = real_repeat_fault_case; owner = c['owner']; after = c['after']; workspace = c['workspace']
    expected = [(workspace.repeat_archive_directory, workspace.access, True),
                *_source_directories(c['original_workspace'])]
    before = _fd_count(); inventory = _inventory([d for d,a,w in expected])
    observe, codes, opened, forbidden = _admission_observer(expected)
    meter = repeat_point_model._Meter()
    with _watch(observe, codes):
        with owner._session(after._definition, workspace, meter) as actual:
            cursor, current = owner._restore(actual, after.cursor_sha256, meter)
            assert repeat_point_model.raw(cursor, base.CURRENT_MAX) == after._cursor
            assert repeat_point_model.raw(current, base.CURRENT_MAX) == after._current
            assert repeat_point_model.raw(actual.basis) == after._basis
    assert len(opened) == 5 and not forbidden
    assert all(store._fd is None for store,state in opened)
    assert _fd_count() == before
    assert _inventory([d for d,a,w in expected]) == inventory
    (tmp_path/'source-session-v2-five-store-integration.private.json').write_bytes(canonical({
        'cursor_sha256':after.cursor_sha256,'actual_new_initializer_stores':[state for store,state in opened],
        'legacy_constructor_sessions_executed':False,'live_RHS_CAS_SQL_dispatches':forbidden,
        'raw3_equal':True,'source_files_unchanged':True,'FD_before_after':[before,_fd_count()],
        'G0_G4':'not_assessed','R2':'not_approved'}))



def test_cancel_after_real_published_handle_preserves_cold_recoverable_prefix(real_repeat_fault_case, tmp_path):
    c = real_repeat_fault_case; owner = c['owner']; before = c['after']
    captured = []; stop = {'now':False}; previous = sys.getprofile(); rhs = []
    handle_code, rhs_code = owner._handle.__code__, base.stage.evaluate.__code__
    def observe(frame, event, arg):
        if event == 'call' and frame.f_code is rhs_code:
            rhs.append(1)
        if event == 'return' and frame.f_code is handle_code and type(arg) is owner.Handle:
            if arg.cursor_sha256 != before.cursor_sha256:
                captured.append(arg)
                stop['now'] = True
        if previous is not None:
            previous(frame,event,arg)
    original_fd_count = _fd_count()
    sys.setprofile(observe)
    try:
        target = q(x(before.current['numeric']['next_grid_endpoint_exact']) + 8)
        result = owner.advance(before, base.AdvanceRequest(target, step_budget=2, cancelled=lambda:stop['now']))
    finally:
        sys.setprofile(previous)
    assert stop['now'] and len(captured) == 1, 'must cancel after an actual newly published original Handle return'
    assert result.status == 'hold' and 'CANCELLED_HOLD' in result.hold
    published = captured[0]
    assert published.current['at']['elapsed_seconds_exact'] == before.current['numeric']['next_grid_endpoint_exact']
    assert published.current['numeric']['point_totals_exact'] == before.current['numeric']['point_totals_exact']
    assert published.current['numeric']['event_sequence'] == before.current['numeric']['event_sequence']
    assert _fd_count() == original_fd_count
    # Genuine fixed-source admission/cold verification succeeds before judging the returned prefix.
    cold = owner.open_material(owner.CursorRef(published.cursor_sha256), published._definition, c['workspace'])
    assert cold._current == published._current and cold._basis == published._basis and cold._cursor == published._cursor
    original_cold = original.open_material(original.CursorRef(c['old_source'].cursor_sha256),
        c['old_source']._definition, c['original_workspace'])
    assert original_cold._current == c['old_source']._current
    cursor = json.loads(published._cursor)
    assert sha256(published._cursor).hexdigest() == published.cursor_sha256
    assert cursor['current_sha256'] == sha256(published._current).hexdigest()
    assert (c['workspace'].repeat_archive_directory / published.cursor_sha256).read_bytes() == published._cursor
    for name,raw in [('cancel-prefix-current.private.json',published._current),
                     ('cancel-prefix-basis.private.json',published._basis),('cancel-prefix-cursor.private.json',published._cursor)]:
        (tmp_path/name).write_bytes(raw)
    (tmp_path/'cancel-prefix-observed.private.json').write_bytes(canonical({
        'published_cursor_sha256':published.cursor_sha256,'published_at':published.current['at'],
        'actual_RHS_observed':len(rhs),'status':result.status,'hold':result.hold,
        'returned_handle_sha256':None if result.handle is None else result.handle.cursor_sha256,
        'returned_emitted':result.emitted,'authority_hold':result.authority_hold,
        'genuine_published_prefix_and_original_source_cold_validated':True,
        'FD_before_after':[original_fd_count,_fd_count()],'G0_G4':'not_assessed','R2':'not_approved'}))
    assert result.handle is not None, 'valid fully published prefix was discarded after cancellation'
    assert result.handle.cursor_sha256 == published.cursor_sha256
    assert result.handle._current == published._current and result.handle._basis == published._basis
    assert result.authority_hold is None
    assert len(result.emitted) == 1 and result.emitted[0]['cursor_sha256'] == published.cursor_sha256
    assert result.emitted[0]['at'] == published.current['at']



def test_interrupted_new_root_reports_actual_completed_bisections(real_repeat_fault_case, tmp_path):
    c = real_repeat_fault_case; point = c['point']; stop = {'now':False}; observed = {'completed':None,'RHS':0}
    previous = sys.getprofile(); isolate_code = point.locator._isolate.__code__
    root_code, fence_code = point._root.__code__, point._Meter.fence.__code__
    def profile(frame,event,arg):
        if event == 'call' and frame.f_code is base.stage.evaluate.__code__:
            observed['RHS'] += 1
        if event == 'call' and frame.f_code is fence_code:
            isolate = frame.f_back
            if isolate is not None and isolate.f_code is isolate_code:
                root = isolate.f_back
                # Ignore mandatory old-source saved-stage algebraic isolation.
                if root is not None and root.f_code is root_code:
                    completed = isolate.f_locals['progress']['bisections']
                    if completed >= 3 and not stop['now']:
                        observed['completed'] = completed
                        stop['now'] = True
        if previous is not None:
            previous(frame,event,arg)
    sys.setprofile(profile)
    try:
        result = point.calculate_successor_candidate(c['old_source'], c['pending_sha'], TOLERANCE,
            cancelled=lambda:stop['now'])
    finally:
        sys.setprofile(previous)
    assert stop['now'] and observed['completed'] is not None, 'must reach actual new-root isolation after genuine pending replay'
    assert observed['completed'] >= 3
    assert result['status'] == 'hold' and 'CANCELLED_HOLD' in result['hold']
    assert observed['RHS'] == result['progress']['actual_RHS_evaluations'] == 5
    assert result['checkpoint_issued'] is result['history_committed'] is result['material_consumed'] is False
    source = c['old_source']
    cold = original.open_material(original.CursorRef(source.cursor_sha256), source._definition, c['original_workspace'])
    assert cold._current == source._current and cold._basis == source._basis and cold._cursor == source._cursor
    (tmp_path/'interrupted-root-observed.private.json').write_bytes(canonical({
        'actual_new_root_bisections_completed':observed['completed'],
        'reported_root_bisections':result['progress']['root_bisections'],
        'observed_RHS':observed['RHS'],'progress':result['progress'],
        'status':result['status'],'hold':result['hold'],'original_source_cold_bytes_preserved':True,
        'G0_G4':'not_assessed','R2':'not_approved'}))
    assert result['progress']['root_bisections'] == observed['completed'], 'completed original bisections were reported as zero on interruption'



def _expected_source_stores(workspace):
    f = workspace.forcing_workspace; b = f.source_workspace
    return [(workspace.archive_directory, workspace.access, True),
            (f.archive_directory, f.access, True),
            (b.archive_directory, b.access, True),
            (b.source_directory, b.access, False)]



def _assert_actual_source_store(store, expected):
    directory, access, writer = expected
    assert type(store) is MorphologyBlobStore
    assert set(store.__dict__) == {'_fd', '_access', '_write', '_jobs'}
    assert store._access is access and store._write is writer
    assert type(store._jobs) is JobStore and store._jobs.artifact_root == directory
    assert store._jobs.content_access is access
    held = os.fstat(store._fd); named = directory.stat(follow_symlinks=False)
    assert stat.S_ISDIR(held.st_mode) and stat.S_IMODE(held.st_mode) == 0o750
    assert held.st_uid == access.owner_uid and held.st_gid == access.reader_gid
    assert (held.st_dev, held.st_ino) == (named.st_dev, named.st_ino)



def test_rejected_late_close_is_never_dispatched_while_genuine_source_unwinds_new_source_session_v2(real_repeat_fault_case, tmp_path):
    c = real_repeat_fault_case; source = c['old_source']; old_current = source._current
    original_close, actual_initializer = MorphologyBlobStore.close, c['point']._open_store_v2
    legacy_init_code = MorphologyBlobStore.__init__.__code__; legacy_init_calls = []
    expected_stores = _expected_source_stores(c['original_workspace'])
    close_calls = []; stores = []; changed = {'now':False}; rhs = []
    previous = sys.getprofile(); initial_fd_count = _fd_count()
    def rejected_close(store):
        close_calls.append({'fd_before':store._fd})
        return original_close(store)
    def observe(frame,event,arg):
        if event == 'call' and frame.f_code is legacy_init_code:
            legacy_init_calls.append(1)
        if event == 'return' and frame.f_code is actual_initializer.__code__:
            store = arg
            if type(store) is MorphologyBlobStore and store._fd is not None:
                _assert_actual_source_store(store, expected_stores[len(stores)])
                stores.append((store,store._fd))
        if event == 'call' and frame.f_code is base.stage.evaluate.__code__:
            rhs.append(1)
        if event == 'return' and frame.f_code is base.stage.evaluate.__code__ and not changed['now']:
            changed['now'] = True
            MorphologyBlobStore.close = rejected_close
        if previous is not None:
            previous(frame,event,arg)
    sys.setprofile(observe)
    try:
        result = c['point'].calculate_successor_candidate(source, c['pending_sha'], TOLERANCE)
    finally:
        MorphologyBlobStore.close = original_close
        sys.setprofile(previous)
    assert changed['now'] and rhs and stores, 'fault must follow real RHS with genuine held source stores'
    assert len(stores) == 4 and not legacy_init_calls, 'observe four actual new-initializer source stores, no simulated legacy constructor'
    assert result['status'] == 'hold' and 'CODE_HOLD' in result['hold']
    assert result['checkpoint_issued'] is result['history_committed'] is result['material_consumed'] is False
    assert 'calculation_sha256' not in result
    assert source._current == old_current
    assert all(store._fd is None for store,fd in stores)
    assert _fd_count() == initial_fd_count
    cold = original.open_material(original.CursorRef(source.cursor_sha256), source._definition, c['original_workspace'])
    assert cold._current == old_current and cold._basis == source._basis and cold._cursor == source._cursor
    (tmp_path/'new-source-v2-rejected-close-observed.private.json').write_bytes(canonical({
        'changed_after_actual_RHS':True,'actual_RHS_calls':len(rhs),'rejected_close_invocations':close_calls,
        'new_initializer_source_store_count':len(stores),'legacy_initializer_calls':len(legacy_init_calls),
        'actual_initializer_module_sha256':sha256(Path(c['point'].__file__).read_bytes()).hexdigest(),'all_held_stores_closed':True,
        'original_source_cold_bytes_preserved':True,'FD_before_after':[initial_fd_count,_fd_count()],
        'status':result['status'],'hold':result['hold'],'G0_G4':'not_assessed','R2':'not_approved'}))
    assert close_calls == [], 'rejected close callback was invoked during source cleanup'



def test_rejected_late_close_property_getter_is_never_dispatched_while_genuine_source_unwinds_new_source_session_v2(real_repeat_fault_case, tmp_path):
    c = real_repeat_fault_case; source = c['old_source']; old_current = source._current
    original_close, actual_initializer = MorphologyBlobStore.close, c['point']._open_store_v2
    legacy_init_code = MorphologyBlobStore.__init__.__code__; legacy_init_calls = []
    expected_stores = _expected_source_stores(c['original_workspace'])
    close_calls = []; stores = []; changed = {'now':False}; rhs = []
    previous = sys.getprofile(); initial_fd_count = _fd_count()
    def rejected_close(store):
        close_calls.append({'fd_before':store._fd})
        return original_close.__get__(store, type(store))
    def observe(frame,event,arg):
        if event == 'call' and frame.f_code is legacy_init_code:
            legacy_init_calls.append(1)
        if event == 'return' and frame.f_code is actual_initializer.__code__:
            store = arg
            if type(store) is MorphologyBlobStore and store._fd is not None:
                _assert_actual_source_store(store, expected_stores[len(stores)])
                stores.append((store,store._fd))
        if event == 'call' and frame.f_code is base.stage.evaluate.__code__:
            rhs.append(1)
        if event == 'return' and frame.f_code is base.stage.evaluate.__code__ and not changed['now']:
            changed['now'] = True
            MorphologyBlobStore.close = property(rejected_close)
        if previous is not None:
            previous(frame,event,arg)
    sys.setprofile(observe)
    try:
        result = c['point'].calculate_successor_candidate(source, c['pending_sha'], TOLERANCE)
    finally:
        MorphologyBlobStore.close = original_close
        sys.setprofile(previous)
    assert changed['now'] and rhs and stores, 'fault must follow real RHS with genuine held source stores'
    assert len(stores) == 4 and not legacy_init_calls, 'observe four actual new-initializer source stores, no simulated legacy constructor'
    assert result['status'] == 'hold' and 'CODE_HOLD' in result['hold']
    assert result['checkpoint_issued'] is result['history_committed'] is result['material_consumed'] is False
    assert 'calculation_sha256' not in result
    assert source._current == old_current
    assert all(store._fd is None for store,fd in stores)
    assert _fd_count() == initial_fd_count
    cold = original.open_material(original.CursorRef(source.cursor_sha256), source._definition, c['original_workspace'])
    assert cold._current == old_current and cold._basis == source._basis and cold._cursor == source._cursor
    (tmp_path/'new-source-v2-rejected-close-property-observed.private.json').write_bytes(canonical({
        'changed_after_actual_RHS':True,'actual_RHS_calls':len(rhs),'rejected_close_property_getter_invocations':close_calls,
        'new_initializer_source_store_count':len(stores),'legacy_initializer_calls':len(legacy_init_calls),
        'actual_initializer_module_sha256':sha256(Path(c['point'].__file__).read_bytes()).hexdigest(),'all_held_stores_closed':True,
        'original_source_cold_bytes_preserved':True,'FD_before_after':[initial_fd_count,_fd_count()],
        'status':result['status'],'hold':result['hold'],'G0_G4':'not_assessed','R2':'not_approved'}))
    assert len(close_calls) == 0, 'rejected close property getter was invoked during source cleanup'



def test_rejected_late_close_code_swap_is_never_dispatched_while_genuine_source_unwinds_new_source_session_v2(real_repeat_fault_case, tmp_path):
    c = real_repeat_fault_case; source = c['old_source']; old_current = source._current
    original_close, actual_initializer = MorphologyBlobStore.close, c['point']._open_store_v2
    legacy_init_code = MorphologyBlobStore.__init__.__code__; legacy_init_calls = []
    expected_stores = _expected_source_stores(c['original_workspace'])
    close_calls = []; stores = []; changed = {'now':False}; rhs = []
    original_code = original_close.__code__
    marker = '_repeat_close_codeswap_calls_v1'
    original_globals = original_close.__globals__
    sentinel = object(); prior_marker = original_globals.get(marker, sentinel)
    assert original_code.co_freevars == ()
    original_globals[marker] = close_calls
    previous = sys.getprofile(); initial_fd_count = _fd_count()
    def rejected_close(store):
        _repeat_close_codeswap_calls_v1.append({'fd_before':store._fd})
        if store._fd is not None:
            os.close(store._fd)
            store._fd = None
    def observe(frame,event,arg):
        if event == 'call' and frame.f_code is legacy_init_code:
            legacy_init_calls.append(1)
        if event == 'return' and frame.f_code is actual_initializer.__code__:
            store = arg
            if type(store) is MorphologyBlobStore and store._fd is not None:
                _assert_actual_source_store(store, expected_stores[len(stores)])
                stores.append((store,store._fd))
        if event == 'call' and frame.f_code is base.stage.evaluate.__code__:
            rhs.append(1)
        if event == 'return' and frame.f_code is base.stage.evaluate.__code__ and not changed['now']:
            changed['now'] = True
            assert rejected_close.__code__.co_freevars == ()
            original_close.__code__ = rejected_close.__code__
        if previous is not None:
            previous(frame,event,arg)
    sys.setprofile(observe)
    try:
        result = c['point'].calculate_successor_candidate(source, c['pending_sha'], TOLERANCE)
    finally:
        original_close.__code__ = original_code
        if prior_marker is sentinel:
            original_globals.pop(marker, None)
        else:
            original_globals[marker] = prior_marker
        sys.setprofile(previous)
    assert changed['now'] and rhs and stores, 'fault must follow real RHS with genuine held source stores'
    assert len(stores) == 4 and not legacy_init_calls, 'observe four actual new-initializer source stores, no simulated legacy constructor'
    assert result['status'] == 'hold' and 'CODE_HOLD' in result['hold']
    assert result['checkpoint_issued'] is result['history_committed'] is result['material_consumed'] is False
    assert 'calculation_sha256' not in result
    assert source._current == old_current
    assert all(store._fd is None for store,fd in stores)
    assert _fd_count() == initial_fd_count
    cold = original.open_material(original.CursorRef(source.cursor_sha256), source._definition, c['original_workspace'])
    assert cold._current == old_current and cold._basis == source._basis and cold._cursor == source._cursor
    (tmp_path/'new-source-v2-rejected-close-code-swap-observed.private.json').write_bytes(canonical({
        'changed_after_actual_RHS':True,'actual_RHS_calls':len(rhs),'rejected_close_code_invocations':close_calls,
        'new_initializer_source_store_count':len(stores),'legacy_initializer_calls':len(legacy_init_calls),
        'actual_initializer_module_sha256':sha256(Path(c['point'].__file__).read_bytes()).hexdigest(),'all_held_stores_closed':True,
        'original_source_cold_bytes_preserved':True,'FD_before_after':[initial_fd_count,_fd_count()],
        'status':result['status'],'hold':result['hold'],'G0_G4':'not_assessed','R2':'not_approved'}))
    assert close_calls == [], 'rejected close function code was invoked during source cleanup'

