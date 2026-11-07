"""Candidate: real repeat lineage to a closed, source-bound stored artifact."""
from copy import deepcopy
from fractions import Fraction
from hashlib import sha256
import json
import math
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys

import pytest

import test_crop_supply_material_repeat as qa
from test_crop_supply_material_repeat import source, origin
from app import crop_supply_material_repeat_owner as repeat
from app import crop_supply_material_repeat_point as point
from app.content_access import ContentAccess
from app.crop_morphology_artifact_io import MorphologyBlobStore

canonical, q, x = qa.canonical, qa.q, qa.x
ROOT = Path(qa.__file__).resolve().parents[2]


def _api():
    from app import crop_supply_material_repeat_artifact_producer as producer
    from app import crop_supply_material_repeat_artifact_reader as reader
    return producer, reader


def _blob(directory, reference):
    raw = (directory / reference).read_bytes()
    assert sha256(raw).hexdigest() == reference
    return raw, json.loads(raw)


def _ref(raw):
    return {'sha256': sha256(raw).hexdigest(), 'bytes': len(raw)}


def _directories(parent):
    ws = parent['workspace']
    return [ws.repeat_archive_directory, *[p for p, _, _ in qa._source_directories(ws.original_material_workspace)]]


def _inventory(directories):
    return qa._inventory(directories)


@pytest.fixture(scope='module')
def seed_before_repeat(origin, tmp_path_factory):
    path = tmp_path_factory.mktemp('repeat-artifact-real-seed')
    fws, definition, declaration = qa.setup_owner(origin, path, edge=600, end=768)
    pending = qa.forcing.advance(qa.forcing.open_season(origin['source_ref'], definition, fws),
        qa.base.AdvanceRequest(q(768), step_budget=128))
    assert pending.status == 'awaiting_material' and pending.pending['schedule_consumed'] is False, pending.hold
    state = qa.candidate.calculate_threshold_state(pending.handle, pending.pending['page_sha256'], qa.TOLERANCE)
    assert state['status'] == 'candidate_ready', state.get('hold')
    inputs = qa.make_inputs({'workspace': fws, 'definition': definition, 'document': declaration, 'result': pending}, state)
    first_point = qa.point.apply_material_point(pending.handle, pending.pending['page_sha256'], qa.TOLERANCE, inputs=inputs)
    assert first_point['status'] == 'point_ready', first_point.get('hold')
    mws = qa.material.Workspace(fws, path / 'old-material', fws.access)
    adopted = qa.material.adopt_material(pending.handle, pending.pending['page_sha256'], qa.TOLERANCE,
        inputs=inputs, expected_point_sha256=first_point['calculation_sha256'], workspace=mws)
    assert adopted.status == 'adopted', adopted.hold
    next_pending = qa.material.advance(adopted.handle, qa.base.AdvanceRequest(q(768), step_budget=128))
    assert next_pending.status == 'awaiting_material' and next_pending.pending['material_consumed'] is False, next_pending.hold
    assert next_pending.handle.current['numeric']['schedule']['next_sequence'] == 13
    return {'handle': next_pending.handle, 'pending': next_pending.pending['page_sha256'],
            'inputs': inputs, 'first_point': first_point, 'workspace': mws, 'origin': origin}


@pytest.fixture(scope='module')
def first_parent(seed_before_repeat, tmp_path_factory):
    seed = seed_before_repeat; before = seed['handle']; pending = seed['pending']
    info = point.describe_successor_source(before)
    located = point.calculate_successor_candidate(before, pending, qa.TOLERANCE)
    assert located['status'] == 'candidate_ready', located.get('hold')
    inputs = qa._successor_inputs(info, located, pending, before, seed['inputs'], 2)
    receipt = point.apply_successor_material_point(before, pending, qa.TOLERANCE, inputs=inputs)
    assert receipt['status'] == 'point_ready', receipt.get('hold')
    qa._point_accounts(receipt, before, seed['origin']['profiles'])
    ws = repeat.Workspace(seed['workspace'], tmp_path_factory.mktemp('repeat-artifact-first') / 'cas', before._workspace.access)
    adopted = repeat.adopt_successor(before, pending, qa.TOLERANCE, inputs=inputs,
        expected_point_sha256=receipt['calculation_sha256'], workspace=ws)
    assert adopted.status == 'adopted' and type(adopted.handle) is repeat.Handle, adopted.hold
    assert adopted.handle.current['numeric']['schedule']['consumed_sequence'] == 13
    assert [v['phase'] for v in adopted.emitted] == ['material_before', 'material_after']
    assert adopted.handle.current['effective_rights'] == {'use': True, 'display': True, 'redistribute': False}
    return {'handle': adopted.handle, 'workspace': ws, 'receipts': [receipt]}


@pytest.fixture(scope='module')
def complete_parents(seed_before_repeat, tmp_path_factory):
    seed = seed_before_repeat; path = tmp_path_factory.mktemp('repeat-artifact-complete')
    args = (repeat, point, seed['handle'], seed['pending'], seed['inputs'], seed['first_point'], seed['workspace'], seed['origin'])
    full = qa._repeat_path(*args, path / 'full', step_budget=128, cold_splits=False)
    split = qa._repeat_path(*args, path / 'split', step_budget=1, cold_splits=True)
    assert full['handle']._current == split['handle']._current
    assert full['handle']._basis == split['handle']._basis and full['handle']._cursor == split['handle']._cursor
    assert [canonical(v) for v in full['receipts']] == [canonical(v) for v in split['receipts']]
    return full, split


def _publish(parent, directory):
    producer, reader = _api(); access = parent['workspace'].access
    before = _inventory(_directories(parent))
    root = producer.produce_repeat_material_artifact(directory, access, handle=parent['handle'])
    assert type(root) is str and len(root) == 64 and set(root) <= set('0123456789abcdef')
    raw = reader.read_repeat_material_manifest(directory, access, root)
    assert type(raw) is bytes and _ref(raw)['sha256'] == root and raw == (directory / root).read_bytes()
    manifest = json.loads(raw); assert canonical(manifest) == raw
    assert _inventory(_directories(parent)) == before
    return {'directory': directory, 'access': access, 'root': root, 'raw': raw, 'manifest': manifest, 'parent': parent}


@pytest.fixture(scope='module')
def first_artifact(first_parent, tmp_path_factory):
    return _publish(first_parent, tmp_path_factory.mktemp('repeat-artifact-first-output') / 'cas')


@pytest.fixture(scope='module')
def complete_artifacts(complete_parents, tmp_path_factory):
    path = tmp_path_factory.mktemp('repeat-artifact-full-split-output')
    return tuple(_publish(parent, path / kind) for parent, kind in zip(complete_parents, ['full', 'split'], strict=True))


def _history(parent):
    directory = parent['workspace'].repeat_archive_directory
    selected = parent['handle'].cursor_sha256; rows = []; seen = set()
    for _ in range(257):
        assert selected not in seen; seen.add(selected)
        cursor_raw, cursor = _blob(directory, selected)
        current_raw, current = _blob(directory, cursor['current_sha256'])
        basis_raw, basis = _blob(directory, cursor['basis_sha256'])
        if cursor['previous_cursor_sha256'] is None:
            assert current['phase'] == 'source_anchor'
            return (_ref(cursor_raw), _ref(current_raw), _ref(basis_raw)), list(reversed(rows))
        page_raw, page = _blob(directory, cursor['history_page_sha256'])
        _, previous = _blob(directory, cursor['previous_cursor_sha256'])
        before_raw, before = _blob(directory, page['before_current_sha256'])
        before_basis_raw, before_basis = _blob(directory, page['before_basis_sha256'])
        assert page['previous_cursor_sha256'] == cursor['previous_cursor_sha256']
        assert page['before_current_sha256'] == previous['current_sha256']
        assert page['after_current_sha256'] == cursor['current_sha256']
        assert page['after_basis_sha256'] == cursor['basis_sha256']
        rows.append({'cursor_raw': cursor_raw, 'cursor': cursor, 'page_raw': page_raw, 'page': page,
            'before_raw': before_raw, 'before': before, 'before_basis_raw': before_basis_raw, 'before_basis': before_basis,
            'current_raw': current_raw, 'current': current, 'basis_raw': basis_raw, 'basis': basis})
        selected = cursor['previous_cursor_sha256']
    raise AssertionError('actual selected history exceeded the parent bound')


def _expected_frames(parent):
    anchor, rows = _history(parent)
    receipts = {sha256(canonical(v)).hexdigest(): v for v in parent['receipts']}
    expected = []
    for index, row in enumerate(rows):
        if row['page']['kind'] == 'material_adoption':
            evidence = row['page']['evidence']; receipt = receipts[evidence['point_sha256']]; data = receipt['point_data']
            for side in ['before', 'after']:
                raw, stored = _blob(parent['workspace'].repeat_archive_directory, evidence[side + '_frame_sha256'])
                assert set(stored) == {'phase', 'at', 'point_sha256', 'source_current_sha256', 'state', 'derived'}
                assert stored['point_sha256'] == evidence['point_sha256']
                assert stored['at'] == data['at']
                source = data['before_dense'] if side == 'before' else {'state': data['after_state'], 'derived': data['after_derived']}
                assert stored['state'] == source['state'] and stored['derived'] == source['derived']
                expected.append((index, row, side, receipt, raw, {'at': stored['at'], 'state': stored['state'], 'derived': stored['derived']}))
        else:
            expected.append((index, row, 'after', None, None, row['current']['numeric']['last_confirmed']))
    return anchor, rows, expected


def _assert_frame(frame, expected, frame_index):
    transition_index, row, side, receipt, material_raw, snapshot = expected
    dense = receipt is not None and side == 'before'; numeric = row['current']['numeric']
    phase = 'material_before' if dense else row['current']['phase']
    basis = row['before_basis'] if dense else row['basis']; seed = basis['numeric_basis']['seed']
    binding = frame['binding']
    assert set(frame) == {'schema_version', 'scope', 'G0_G4', 'R2', 'time_kind', 'claim_scope', 'index', 'phase', 'at', 'binding', 'snapshot', 'model_floor_area', 'state_layout', 'leaves', 'internodes', 'accounts'}
    assert set(binding) == {'kind', 'transition_index', 'history_page_sha256', 'transition_cursor_sha256', 'active_basis_sha256', 'context_cursor_sha256', 'checkpoint_cursor_sha256', 'source'}
    assert frame['index'] == frame_index and frame['phase'] == phase and frame['at'] == snapshot['at']
    assert canonical(frame['snapshot']) == canonical(snapshot)
    assert binding['transition_index'] == transition_index
    assert binding['history_page_sha256'] == sha256(row['page_raw']).hexdigest()
    assert binding['transition_cursor_sha256'] == sha256(row['cursor_raw']).hexdigest()
    assert binding['active_basis_sha256'] == sha256(row['before_basis_raw'] if dense else row['basis_raw']).hexdigest()
    assert binding['context_cursor_sha256'] == row['cursor']['previous_cursor_sha256']
    assert binding['checkpoint_cursor_sha256'] == (None if dense else sha256(row['cursor_raw']).hexdigest())
    assert binding['kind'] == ('dense_material_before' if dense else 'adopted_material_after' if receipt else 'confirmed_current')
    if receipt:
        evidence = row['page']['evidence']; source = binding['source']
        assert source['receipt'] == _ref(canonical(receipt))
        assert source['witness']['sha256'] == evidence['point_witness_sha256']
        assert source['material_frame'] == _ref(material_raw)
        if not dense: assert source['current'] == _ref(row['current_raw'])
    else: assert binding['source'] == {'current': _ref(row['current_raw'])}
    assert frame['state_layout'] == seed['state_layout'] and frame['model_floor_area'] == seed['program']['model_floor_area']
    accounts = frame['accounts']
    if dense:
        d = receipt['point_data']; b = d['before_dense']; schedule = deepcopy(d['source_schedule']); schedule['age_exact'] = b['shoot_age_exact']
        expected_accounts = {'event_sequence': b['event_sequence'], 'schedule': schedule, 'global_ledgers': b['pending_global_ledgers'],
            'local_ledgers': b['local_ledgers'], 'point_totals_exact': b['point_totals_exact'],
            'lifetime_transfers_exact': b['pending_lifetime_transfers_exact'], 'transfer_origins': b['transfer_origins']}
    else:
        expected_accounts = {k: numeric[k] for k in ['event_sequence', 'schedule', 'global_ledgers', 'point_totals_exact', 'lifetime_transfers_exact', 'transfer_origins']}
        expected_accounts['local_ledgers'] = numeric['branch_ledgers']
    assert canonical(accounts) == canonical(expected_accounts)
    state = snapshot['state']; n = len(seed['program']['leaves']); m = len(seed['program']['stem_root_compartments'])
    h = len(seed['organs']['internodes']); z = 106 + 3*n + m
    assert len(state) == z + 2*h
    internode_ids = [v['compartment_id'] for v in seed['organs']['internodes']]
    stem_ids = [v['compartment_id'] for v in seed['program']['stem_root_compartments']]
    for kind, name, identifier, unit in [('leaf', 'leaves', 'leaf_id', 'm2'), ('internode', 'internodes', 'compartment_id', 'm')]:
        values = frame[name]; originals = seed['organs'][name]
        assert [v['id'] for v in values] == [v[identifier] for v in originals]
        for i, (value, original) in enumerate(zip(values, originals, strict=True)):
            assert value['source_index'] == i and value['parent_internode_id'] == original.get('parent_internode_id')
            assert value['parent_internode_id'] is None or value['parent_internode_id'] in internode_ids
            offset = 106+n+i if kind == 'leaf' else z+h+i
            carbon = 106+2*n+i if kind == 'leaf' else 106+3*n+stem_ids.index(original[identifier])
            age = 106+i if kind == 'leaf' else z+i
            assert value['geometry'] == {'value': state[offset], 'unit': unit}
            assert value['carbon'] == {'value': state[carbon], 'unit': 'mg_CH2O/m2_floor'}
            assert value['represented_age'] == {'value': state[age], 'unit': 'degC_day'}
            assert value['birth'] == original['baseline'] and value['metadata'] == original
            assert value['geometry_origin'] == seed['geometry_baselines'][name][i]
            birth = original['baseline']; duration = x(frame['at']['elapsed_seconds_exact']) - x(birth['at_elapsed_seconds_exact'])
            air = x(accounts['lifetime_transfers_exact']['indoor_air_temperature_time']) - x(birth['air_temperature_integral_exact'])
            assert value['clock_exact'] == q(x(birth['thermal_age_exact']) + (air-Fraction(birth['base_temperature']['value'])*duration)/86400, 'degC_day')
            assert set(value) == {'id', 'parent_internode_id', 'source_index', 'geometry', 'carbon', 'represented_age', 'clock_exact', 'birth', 'geometry_origin', 'metadata', 'geometry_diagnostics'}
            diagnostics = value['geometry_diagnostics']
            assert set(diagnostics) == {'kind', 'canonical_status', 'potential_exact', 'realized_exact', 'deficit_exact', 'lifetime_potential_exact', 'lifetime_realized_exact', 'lifetime_deficit_exact', 'canonical_gap_exact', 'canonical_potential_difference_exact'}
            if dense:
                assert diagnostics['kind'] == 'dense_stored_transfers' and diagnostics['canonical_status'] == 'not_stored_at_dense_boundary'
                assert diagnostics['canonical_gap_exact'] is diagnostics['canonical_potential_difference_exact'] is None
                for prefix, transfers in [('', b['pending_branch_transfers_exact']), ('lifetime_', b['pending_lifetime_transfers_exact'])]:
                    potential = transfers[f'{kind}_{i}_potential']; realized = transfers[f'{kind}_{i}_realized']
                    assert diagnostics[prefix+'potential_exact'] == potential and diagnostics[prefix+'realized_exact'] == realized
                    assert diagnostics[prefix+'deficit_exact'] == q(x(potential)-x(realized), unit)
            else:
                assert diagnostics['kind'] == 'stored_confirmed' and diagnostics['canonical_status'] == 'stored'
                assert {k:v for k,v in diagnostics.items() if k not in {'kind', 'canonical_status'}} == numeric['geometry_diagnostics'][f'{kind}_{i}']


def _selected_source_bytes(parent):
    from app import crop_supply_material_artifact_reader as old_reader
    ws = parent['workspace']; mws = ws.original_material_workspace
    fws = mws.forcing_workspace; bws = fws.source_workspace
    directories = {'original': bws.source_directory, 'base': bws.archive_directory,
                   'forcing': fws.archive_directory, 'material': mws.archive_directory,
                   'repeat': ws.repeat_archive_directory}
    groups = {kind: {} for kind in directories}
    def obj(reference, kind):
        raw, value = _blob(directories[kind], reference)
        assert canonical(value) == raw
        groups[kind][reference] = raw
        return value
    definition = obj(parent['handle']._definition, 'repeat'); selected = definition['source']
    md = obj(selected['definition_sha256'], 'material')
    fd = obj(md['source']['definition_sha256'], 'forcing')
    bd = obj(fd['source']['definition_sha256'], 'base')
    with MorphologyBlobStore(bws.source_directory, ws.access) as store:
        original, _, originals = old_reader.legacy._load(store, bd['source']['artifact_sha256'])
    groups['original'] = {h: value[0] for h, value in originals.items()}
    legacy_source = {'original_root': _ref(groups['original'][bd['source']['artifact_sha256']]),
        'source_frame_index': bd['source']['frame_index'], 'base': fd['source'], 'forcing': md['source'],
        'material': {k: selected[k] for k in ['definition_sha256', 'cursor_sha256']}}
    old_reader._graph({'source': legacy_source, 'code_sha256': old_reader._pins(),
                       'effective_rights': parent['handle'].current['effective_rights']}, obj, original)
    anchor, rows = _history(parent)
    for reference in anchor: obj(reference['sha256'], 'repeat')
    for row in rows:
        for name in ['cursor_raw', 'page_raw', 'before_raw', 'before_basis_raw', 'current_raw', 'basis_raw']:
            raw = row[name]; groups['repeat'][sha256(raw).hexdigest()] = raw
        if row['page']['kind'] == 'material_adoption':
            evidence = row['page']['evidence']
            witness = obj(evidence['point_witness_sha256'], 'repeat')
            for name in ['before_frame_sha256', 'after_frame_sha256']: obj(evidence[name], 'repeat')
            pending_group = 'material' if witness['source']['owner_version'] == qa.material.VERSION else 'repeat'
            obj(witness['pending_page_sha256'], pending_group)
            for record in row['basis']['origin_records'].values():
                expected_raw = canonical(record); actual = obj(sha256(expected_raw).hexdigest(), 'repeat')
                assert canonical(actual) == expected_raw
    return groups, legacy_source, original


def _assert_manifest(packet):
    parent = packet['parent']; manifest = packet['manifest']; directory = packet['directory']
    assert set(manifest) == {'schema_version', 'scope', 'G0_G4', 'R2', 'time_kind', 'claim_scope', 'code_sha256', 'source',
        'blob_groups', 'transitions', 'frames', 'effective_rights', 'window', 'terminal', 'notice'}
    assert manifest['schema_version'] == 'supply-material-repeat-artifact-v1'
    assert manifest['scope'] == 'software_research_only' and manifest['G0_G4'] == 'not_assessed' and manifest['R2'] == 'not_approved'
    assert manifest['effective_rights'] == {'use': True, 'display': True, 'redistribute': False}
    from app import crop_supply_material_artifact_reader as old_reader
    paths = set(old_reader.SOURCE_PATHS) | {'backend/app/crop_supply_material_repeat_point.py',
        'backend/app/crop_supply_material_repeat_owner.py', 'backend/app/crop_supply_material_repeat_proof.py',
        'backend/app/job_store.py', 'backend/app/crop_supply_material_repeat_artifact_producer.py',
        'backend/app/crop_supply_material_repeat_artifact_reader.py'}
    assert manifest['code_sha256'] == {name: sha256((ROOT/name).read_bytes()).hexdigest() for name in paths}
    selected, legacy_source, original = _selected_source_bytes(parent)
    for kind, expected_blobs in selected.items():
        assert manifest['blob_groups'][kind] == sorted([_ref(v) for v in expected_blobs.values()], key=lambda v:v['sha256'])
        assert all((directory/h).read_bytes() == raw for h, raw in expected_blobs.items())
    source = manifest['source']
    assert source['owner_version'] == repeat.VERSION and source['definition'] == _ref((parent['workspace'].repeat_archive_directory/parent['handle']._definition).read_bytes())
    assert source['original_root'] == legacy_source['original_root'] and source['original_frame_index'] == legacy_source['source_frame_index']
    for kind in ['base', 'forcing', 'material']:
        assert source[kind] == {name: _ref(selected[kind][legacy_source[kind][name+'_sha256']]) for name in ['definition', 'cursor']}
    assert manifest['notice'] == original['root_inputs']['license_notice']
    assert manifest['source']['final'] == {'cursor': _ref(parent['handle']._cursor), 'current': _ref(parent['handle']._current), 'basis': _ref(parent['handle']._basis)}
    anchor, rows, expected = _expected_frames(parent)
    assert manifest['source']['anchor'] == dict(zip(['cursor', 'current', 'basis'], anchor, strict=True))
    assert len(manifest['transitions']) == len(rows) and len(manifest['frames']) == len(expected)
    assert set(manifest['blob_groups']) == {'original', 'base', 'forcing', 'material', 'repeat', 'points', 'frames'}
    sizes = {}
    for group in manifest['blob_groups'].values():
        assert group == sorted(group, key=lambda v: v['sha256']) and len({v['sha256'] for v in group}) == len(group)
        for reference in group:
            raw = (directory / reference['sha256']).read_bytes(); assert _ref(raw) == reference
            sizes[reference['sha256']] = len(raw)
    assert sum(sizes.values()) + len(packet['raw']) <= 64*1024**2
    assert len(sizes) + 1 <= 4096
    assert sum(v['state_scalars'] for v in manifest['frames']) <= 32768
    assert {v['sha256'] for v in manifest['blob_groups']['points']} == {sha256(canonical(v)).hexdigest() for v in parent['receipts']}
    for receipt in parent['receipts']:
        h = sha256(canonical(receipt)).hexdigest(); assert (directory / h).read_bytes() == canonical(receipt)
    frame_index = 0
    for index, row in enumerate(rows):
        transition = manifest['transitions'][index]
        assert transition['index'] == index and transition['kind'] == row['page']['kind']
        assert transition['previous_cursor_sha256'] == row['cursor']['previous_cursor_sha256']
        for field, source in [('cursor', 'cursor_raw'), ('history_page', 'page_raw'), ('before_current', 'before_raw'),
                              ('after_current', 'current_raw'), ('before_basis', 'before_basis_raw'), ('after_basis', 'basis_raw')]:
            assert transition[field] == _ref(row[source])
        width = 2 if row['page']['kind'] == 'material_adoption' else 1
        assert transition['frame_indices'] == list(range(frame_index, frame_index+width))
        if width == 2:
            receipt = next(v for v in parent['receipts'] if sha256(canonical(v)).hexdigest() == row['page']['evidence']['point_sha256'])
            evidence = transition['point']; assert evidence['receipt'] == _ref(canonical(receipt))
            assert evidence['witness']['sha256'] == row['page']['evidence']['point_witness_sha256']
            assert evidence['witness']['sha256'] != evidence['receipt']['sha256'] != receipt['calculation_sha256']
            assert evidence['calculation_sha256'] == receipt['calculation_sha256']
            assert evidence['candidate_calculation_sha256'] == receipt['candidate']['calculation_sha256']
        frame_index += width
    assert len(expected) == frame_index
    return expected


def test_genuine_second_adoption_roundtrips_before_any_artifact_API_is_available(first_parent, tmp_path):
    assert type(first_parent['handle']) is repeat.Handle
    assert first_parent['handle'].current['numeric']['schedule']['consumed_sequence'] == 13
    packet = _publish(first_parent, tmp_path / 'first-artifact')
    expected = _assert_manifest(packet); _, reader = _api()
    assert [v['phase'] for v in packet['manifest']['frames']] == ['material_before', 'material_after']
    for index, source in enumerate(expected):
        raw = reader.read_repeat_material_frame(packet['directory'], packet['access'], packet['root'], index=index)
        assert raw == (packet['directory'] / packet['manifest']['frames'][index]['frame']['sha256']).read_bytes()
        _assert_frame(json.loads(raw), source, index)


def test_complete_full_split_roots_and_all_actual_per_basis_frames_are_identical(complete_artifacts):
    full, split = complete_artifacts; _, reader = _api()
    assert full['root'] == split['root'] and full['raw'] == split['raw']
    expected = _assert_manifest(full); assert len(full['parent']['receipts']) == 2
    assert {row['page']['kind'] for _, row, *_ in expected} == {'material_adoption', 'interval', 'forcing_switch'}
    frames = []
    for index, source in enumerate(expected):
        a = reader.read_repeat_material_frame(full['directory'], full['access'], full['root'], index=index)
        b = reader.read_repeat_material_frame(split['directory'], split['access'], split['root'], index=index)
        assert a == b and _ref(a) == full['manifest']['frames'][index]['frame']
        frame = json.loads(a); _assert_frame(frame, source, index); frames.append(frame)
    material = [f for f in frames if f['phase'] in {'material_before', 'material_after'}]
    assert len(material) == 2*len(full['parent']['receipts'])
    assert len({f['binding']['active_basis_sha256'] for f in material}) == 3
    assert len({len(f['snapshot']['state']) for f in material}) == 3
    for before, after in zip(material[::2], material[1::2], strict=True):
        assert before['at'] == after['at'] and before['binding']['checkpoint_cursor_sha256'] is None
    pairs = [(a,b) for a,b in zip(frames, frames[1:]) if a['phase'] == 'forcing_before' and b['phase'] == 'forcing_after']
    assert pairs
    for before, after in pairs:
        assert before['at'] == after['at'] and before['binding']['active_basis_sha256'] == after['binding']['active_basis_sha256']
        assert before['snapshot']['state'] == after['snapshot']['state'] and before['accounts'] == after['accounts']
        assert [v['geometry'] for v in before['leaves']+before['internodes']] == [v['geometry'] for v in after['leaves']+after['internodes']]


def _put(directory, value):
    raw = canonical(value); digest = sha256(raw).hexdigest(); path = directory / digest
    path.write_bytes(raw); path.chmod(0o640)
    return _ref(raw)


def _changed_frame(packet, path, change):
    directory = shutil.copytree(packet['directory'], path); manifest = deepcopy(packet['manifest'])
    index = 1 if change == 'confirmed_null' else 0
    descriptor = manifest['frames'][index]; old = descriptor['frame']['sha256']; frame = json.loads((directory / old).read_bytes())
    if change == 'basis': frame['binding']['active_basis_sha256'] = manifest['frames'][1]['active_basis_sha256']; descriptor['active_basis_sha256'] = frame['binding']['active_basis_sha256']
    elif change == 'context_as_checkpoint': frame['binding']['checkpoint_cursor_sha256'] = frame['binding']['context_cursor_sha256']
    elif change == 'dense_zero': frame['leaves'][0]['geometry_diagnostics']['canonical_gap_exact'] = q(0, 'm2')
    elif change == 'confirmed_null': frame['leaves'][0]['geometry_diagnostics']['canonical_gap_exact'] = None
    elif change == 'extra': frame['unregistered_source'] = {'approved': True}
    elif change == 'diagnostic_tag': frame['leaves'][0]['geometry_diagnostics']['kind'] = 'stored_confirmed'
    elif change == 'unit': frame['leaves'][0]['geometry']['unit'] = 'm'
    elif change == 'coordinate':
        leaf = frame['leaves'][0]; n = len(frame['leaves']); offset = 106+n
        value = math.nextafter(frame['snapshot']['state'][offset], math.inf)
        frame['snapshot']['state'][offset] = value; leaf['geometry']['value'] = value
    elif change == 'dimension': frame['snapshot']['state'].pop(); descriptor['state_scalars'] -= 1
    elif change == 'parent':
        row = frame['leaves'][0]; alternatives = [v['id'] for v in frame['internodes'] if v['id'] != row['parent_internode_id']]
        assert alternatives; row['parent_internode_id'] = alternatives[-1]
    else: raise AssertionError(change)
    new = _put(directory, frame); descriptor['frame'] = new
    manifest['blob_groups']['frames'] = sorted([new if v['sha256'] == old else v for v in manifest['blob_groups']['frames']], key=lambda v:v['sha256'])
    return directory, _put(directory, manifest)['sha256'], index


@pytest.mark.parametrize('change', ['basis', 'context_as_checkpoint', 'dense_zero', 'confirmed_null', 'extra', 'diagnostic_tag', 'unit', 'coordinate', 'dimension', 'parent'])
def test_rehashed_frame_cannot_change_its_actual_source(first_artifact, tmp_path, change):
    _, reader = _api(); p = first_artifact
    assert reader.read_repeat_material_manifest(p['directory'], p['access'], p['root']) == p['raw']
    directory, root, index = _changed_frame(p, tmp_path / 'changed', change)
    with pytest.raises(reader.RepeatArtifactHold): reader.read_repeat_material_frame(directory, p['access'], root, index=index)


@pytest.mark.parametrize('change', ['rights', 'use_false', 'display_false', 'code', 'extra', 'source', 'order', 'duplicate_group'])
def test_rehashed_root_cannot_override_closed_provenance(first_artifact, tmp_path, change):
    _, reader = _api(); p = first_artifact
    assert reader.read_repeat_material_manifest(p['directory'], p['access'], p['root']) == p['raw']
    directory = shutil.copytree(p['directory'], tmp_path / 'changed'); manifest = deepcopy(p['manifest'])
    if change == 'rights': manifest['effective_rights']['redistribute'] = True
    elif change == 'use_false': manifest['effective_rights']['use'] = False
    elif change == 'display_false': manifest['effective_rights']['display'] = False
    elif change == 'code': manifest['code_sha256']['backend/app/crop_supply_material_repeat_artifact_reader.py'] = '0'*64
    elif change == 'extra': manifest['unregistered_source'] = {'approval': True}
    elif change == 'source': manifest['source']['final']['basis'] = manifest['source']['anchor']['basis']
    elif change == 'order': manifest['transitions'][0]['frame_indices'].reverse()
    elif change == 'duplicate_group': manifest['blob_groups']['repeat'].append(deepcopy(manifest['blob_groups']['repeat'][0]))
    changed = _put(directory, manifest)['sha256']
    with pytest.raises(reader.RepeatArtifactHold): reader.read_repeat_material_manifest(directory, p['access'], changed)


def test_rehashed_retained_witness_observation_cannot_reuse_an_unverified_public_receipt(first_artifact, tmp_path):
    _, reader = _api(); packet = first_artifact
    assert reader.read_repeat_material_manifest(packet['directory'], packet['access'], packet['root']) == packet['raw']
    directory = shutil.copytree(packet['directory'], tmp_path/'changed-witness'); manifest = deepcopy(packet['manifest'])
    transition = manifest['transitions'][0]; evidence = transition['point']; old_witness = evidence['witness']['sha256']
    witness = json.loads((directory/old_witness).read_bytes())
    item = next(value for value in witness['dense_derived'].values() if type(value.get('value')) is float)
    item['value'] = math.nextafter(item['value'], math.inf)
    new_witness = _put(directory, witness); evidence['witness'] = new_witness
    old_page = transition['history_page']['sha256']; page = json.loads((directory/old_page).read_bytes())
    page['evidence']['point_witness_sha256'] = new_witness['sha256']; transition['history_page'] = _put(directory, page)
    old_cursor = transition['cursor']['sha256']; cursor = json.loads((directory/old_cursor).read_bytes())
    cursor['history_page_sha256'] = transition['history_page']['sha256']; transition['cursor'] = _put(directory, cursor)
    manifest['source']['final']['cursor'] = transition['cursor']
    replacements = {old_witness:new_witness, old_page:transition['history_page'], old_cursor:transition['cursor']}
    manifest['blob_groups']['repeat'] = sorted([replacements.get(v['sha256'],v) for v in manifest['blob_groups']['repeat']],key=lambda v:v['sha256'])
    frame_replacements = {}
    for descriptor in manifest['frames']:
        old_frame = descriptor['frame']['sha256']; frame = json.loads((directory/old_frame).read_bytes())
        frame['binding']['history_page_sha256'] = transition['history_page']['sha256']
        frame['binding']['transition_cursor_sha256'] = transition['cursor']['sha256']
        frame['binding']['source']['witness'] = new_witness
        if frame['binding']['checkpoint_cursor_sha256'] is not None: frame['binding']['checkpoint_cursor_sha256'] = transition['cursor']['sha256']
        descriptor['frame'] = _put(directory, frame); frame_replacements[old_frame] = descriptor['frame']
    manifest['blob_groups']['frames'] = sorted([frame_replacements.get(v['sha256'],v) for v in manifest['blob_groups']['frames']],key=lambda v:v['sha256'])
    changed_root = _put(directory, manifest)['sha256']
    with pytest.raises(reader.RepeatArtifactHold): reader.read_repeat_material_manifest(directory, packet['access'], changed_root)
    assert reader.read_repeat_material_manifest(packet['directory'], packet['access'], packet['root']) == packet['raw']


def test_full_physical_byte_budget_rejects_before_a_new_publication(first_parent, tmp_path):
    producer, reader = _api(); directory = tmp_path/'byte-full'; directory.mkdir(mode=0o750); directory.chmod(0o750)
    block = bytes(65536)
    for index in range(4):
        temporary = directory/'temporary-owned-prefill'; hasher = sha256()
        with temporary.open('xb') as output:
            first = bytes([index+1])+block[1:]; output.write(first); hasher.update(first)
            for _ in range(255): output.write(block); hasher.update(block)
        temporary.chmod(0o640); temporary.rename(directory/hasher.hexdigest())
    assert sum(p.stat().st_size for p in directory.iterdir()) == 64*1024**2
    before = _inventory([directory]); sources = _inventory(_directories(first_parent))
    with pytest.raises(reader.RepeatArtifactHold, match=r'^CAPACITY_HOLD:'): producer.produce_repeat_material_artifact(directory, first_parent['workspace'].access, handle=first_parent['handle'])
    assert _inventory([directory]) == before and _inventory(_directories(first_parent)) == sources


@pytest.mark.parametrize('index', [True, -1, 512, '0'])
def test_invalid_index_does_not_select_a_different_frame(first_artifact, index):
    _, reader = _api(); p = first_artifact
    with pytest.raises(reader.RepeatArtifactHold): reader.read_repeat_material_frame(p['directory'], p['access'], p['root'], index=index)


def test_missing_notice_is_held_without_source_recovery(first_artifact, tmp_path):
    _, reader = _api(); p = first_artifact
    assert reader.read_repeat_material_manifest(p['directory'], p['access'], p['root']) == p['raw']
    directory = shutil.copytree(p['directory'], tmp_path / 'missing')
    (directory / p['manifest']['notice']['sha256']).unlink()
    with pytest.raises(reader.RepeatArtifactHold): reader.read_repeat_material_manifest(directory, p['access'], p['root'])


@pytest.mark.parametrize('kind', ['dto', 'same', 'descendant', 'ancestor', 'symlink'])
def test_invalid_handle_or_output_cannot_modify_any_source(first_parent, tmp_path, kind):
    producer, reader = _api(); ws = first_parent['workspace']; parent = ws.repeat_archive_directory
    before = _inventory(_directories(first_parent)); output = tmp_path / 'output'; handle = first_parent['handle']
    if kind == 'dto': handle = handle.current
    elif kind == 'same': output = parent
    elif kind == 'descendant': output = parent / 'bad-output'
    elif kind == 'ancestor': output = parent.parent
    elif kind == 'symlink': output.symlink_to(parent, target_is_directory=True)
    with pytest.raises(reader.RepeatArtifactHold): producer.produce_repeat_material_artifact(output, ws.access, handle=handle)
    assert _inventory(_directories(first_parent)) == before


def test_full_output_file_budget_rejects_before_a_new_publication(first_parent, tmp_path):
    producer, reader = _api(); directory = tmp_path / 'full'; directory.mkdir(mode=0o750); directory.chmod(0o750)
    for index in range(4096): _put(directory, {'test_owned_orphan': index})
    before = _inventory([directory]); sources = _inventory(_directories(first_parent))
    with pytest.raises(reader.RepeatArtifactHold, match=r'^CAPACITY_HOLD:'): producer.produce_repeat_material_artifact(directory, first_parent['workspace'].access, handle=first_parent['handle'])
    assert _inventory([directory]) == before and _inventory(_directories(first_parent)) == sources


@pytest.mark.parametrize('fault', ['output_mode', 'validation_property'])
def test_late_publication_failure_closes_real_store_without_rejected_dispatch(first_parent, tmp_path, fault):
    producer, reader = _api(); directory = tmp_path / 'late-output'; before = _inventory(_directories(first_parent))
    prior = ContentAccess.__dict__['validate']; rejected = []; stores = []; injected = []
    fd_before = qa._fd_count()
    def getter(self):
        rejected.append(True)
        return prior.__get__(self, type(self))
    def observe(frame, event, value):
        if event != 'return' or injected: return
        store = frame.f_locals['self']; fd = store.__dict__.get('_fd')
        if fd is None or not directory.exists(): return
        a, b = os.fstat(fd), directory.stat(follow_symlinks=False)
        if (a.st_dev, a.st_ino) != (b.st_dev, b.st_ino): return
        stores.append(store); injected.append(value)
        if fault == 'output_mode': directory.chmod(0o777)
        else: ContentAccess.validate = property(getter)
    try:
        with qa._watch(observe, {MorphologyBlobStore.put.__code__}):
            with pytest.raises(reader.RepeatArtifactHold):
                producer.produce_repeat_material_artifact(directory, first_parent['workspace'].access, handle=first_parent['handle'])
        assert injected and all(store.__dict__.get('_fd') is None for store in stores)
        assert qa._fd_count() == fd_before and rejected == []
    finally:
        ContentAccess.validate = prior
        if directory.exists(): directory.chmod(0o750)
    assert _inventory(_directories(first_parent)) == before
    assert injected[0] in {p.name for p in directory.iterdir()}
    assert all(p.name == sha256(p.read_bytes()).hexdigest() for p in directory.iterdir())
    # The one already written immutable blob is an allowed orphan, not a completed artifact result.


COLD_READER = r"""
import json,os,stat,sys
from hashlib import sha256
from pathlib import Path
R=Path(sys.argv[1]);directory=Path(sys.argv[2]);root=sys.argv[3];indices=json.loads(sys.argv[4])
sys.path[:0]=[str(R/'backend'),str(R/'backend/tests')];sys.dont_write_bytecode=True
import test_crop_supply_material_repeat as qa
from app.job_store import JobStore
from app.crop_morphology_artifact_io import MorphologyBlobStore
from app.content_access import ContentAccess
from app import crop_supply_material_repeat_owner as owner
from app import crop_supply_material_repeat_point as point
from app import crop_leaf_area as leaf_curve
from app import crop_internode_length as length_curve

def metadata(path):
 i=path.stat(follow_symlinks=False);return(i.st_dev,i.st_ino,i.st_mode,i.st_uid,i.st_gid,i.st_nlink,i.st_mtime_ns,i.st_ctime_ns)
dir_before=metadata(directory)
def inventory():
 return {p.name:(p.stat().st_mode,p.stat().st_uid,p.stat().st_gid,p.stat().st_nlink,p.stat().st_size,p.stat().st_mtime_ns,p.stat().st_ctime_ns,sha256(p.read_bytes()).hexdigest())for p in directory.iterdir()}
before=inventory();fd_before=len(os.listdir('/proc/self/fd'));entered=[];controls=[];phase='control';expected=None
entries=[(qa.base.stage.evaluate,(None,)*5,{}),(qa.point.apply_material_point,(None,)*3,{'inputs':None}),
 (qa.candidate.calculate_threshold_state,(None,)*3,{}),(point.calculate_successor_candidate,(None,)*3,{}),
 (point.apply_successor_material_point,(None,)*3,{'inputs':None}),
 (owner.adopt_successor,(None,)*3,{'inputs':None,'expected_point_sha256':None,'workspace':None}),
 (MorphologyBlobStore.put,(None,b''),{'maximum':1}),(JobStore.connect,(None,),{}),
 (JobStore._durable_content,(None,b'','0'*64),{}),
 (leaf_curve._area_at,(None,None),{}),(leaf_curve.calculate_leaf_area_point,(),{'inputs':None}),
 (length_curve._length_at_thermal_age,(None,None),{}),(length_curve.calculate_internode_length_point,(),{'inputs':None})]
codes={f.__code__ for f,_,_ in entries};assert len(codes)==len(entries)
class Seen(BaseException):pass
def observe(frame,event,value):
 if event!='call':return
 if phase=='control':
  assert frame.f_code is expected;controls.append(frame.f_code);raise Seen()
 entered.append(frame.f_code.co_name);raise AssertionError('stored reader entered numerical/publication/DB boundary')
def positive_controls():
 global expected
 for function,args,kwargs in entries:
  expected=function.__code__;n=len(controls)
  try:function(*args,**kwargs)
  except Seen:pass
  else:raise AssertionError('entry control ran original body')
  assert len(controls)==n+1
mutations=[]
def audit(event,args):
 if event in {'socket.connect','socket.__new__','socket.getaddrinfo','subprocess.Popen','os.system','os.posix_spawn','os.exec'}:
  mutations.append(event);raise AssertionError(event)
 if event=='open':
  mode=args[1];flags=args[2]
  if (isinstance(mode,str)and any(x in mode for x in 'wax+'))or(isinstance(flags,int)and flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND)):
   mutations.append(event);raise AssertionError('file write')
 if event=='os.mkdir':
  value=Path(os.fsdecode(args[0]));fd=args[2]
  if not value.is_absolute():value=(Path.cwd()if fd in(None,-1)else Path(os.readlink('/proc/self/fd/'+str(fd))))/value
  info=value.stat(follow_symlinks=False)
  assert value==directory and stat.S_ISDIR(info.st_mode)and not value.is_symlink()and(info.st_dev,info.st_ino)==dir_before[:2]
  return
 if event in {'os.remove','os.rename','os.rmdir','os.chmod','os.chown','os.utime','os.link','os.symlink','os.truncate'}:
  mutations.append(event);raise AssertionError(event)
assert 'app.crop_supply_material_repeat_artifact_reader' not in sys.modules
sys.addaudithook(audit)
with qa._watch(observe,codes):
 positive_controls();phase='read'
 from app import crop_supply_material_repeat_artifact_reader as reader
 access=ContentAccess(os.getuid(),os.getgid());manifest=reader.read_repeat_material_manifest(directory,access,root)
 raws=[reader.read_repeat_material_frame(directory,access,root,index=i)for i in indices]
 phase='control';positive_controls()
assert entered==[]and mutations==[]and len(controls)==2*len(entries)
assert inventory()==before and metadata(directory)==dir_before and len(os.listdir('/proc/self/fd'))==fd_before
print(json.dumps({'root':sha256(manifest).hexdigest(),'frames':[sha256(v).hexdigest()for v in raws],
 'forbidden_entries':entered,'mutations':mutations,'controls':len(controls),'fd_before':fd_before,'fd_after':len(os.listdir('/proc/self/fd'))}))
"""


@pytest.mark.parametrize('phase', ['material_before', 'material_after', 'original_grid_endpoint', 'forcing_before', 'forcing_after'])
def test_fresh_stored_reader_preserves_each_actual_phase_without_generation_or_writes(complete_artifacts, phase):
    packet = complete_artifacts[0]
    selected = [v for v in packet['manifest']['frames'] if v['phase'] == phase]
    assert selected
    before = _inventory([packet['directory'], *_directories(packet['parent'])])
    child = subprocess.run([sys.executable, '-B', '-c', COLD_READER, str(ROOT), str(packet['directory']), packet['root'],
        json.dumps([v['index'] for v in selected])], capture_output=True, text=True, timeout=540,
        env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})
    assert child.returncode == 0, child.stderr[-4000:]
    result = json.loads(child.stdout)
    assert result['root'] == packet['root'] and result['frames'] == [v['frame']['sha256'] for v in selected]
    assert result['forbidden_entries'] == result['mutations'] == [] and result['controls'] == 26
    assert result['fd_before'] == result['fd_after']
    assert _inventory([packet['directory'], *_directories(packet['parent'])]) == before


# Proposed additional transport-boundary regressions; original tests above stay exact.
from dataclasses import replace as _boundary_replace
import time as _boundary_time


def _boundary_writer_state(access):
    return id(access), tuple(vars(access).items())


def _boundary_valid_drift(access):
    writer = ContentAccess.__dict__['require_writer']
    alternatives = {os.getegid(), *os.getgroups()} - {access.reader_gid}
    if alternatives:
        access.__dict__['reader_gid'] = min(alternatives)
        kind = 'other_actual_reader_group'
    else:
        access.__dict__['require_writer'] = writer.__get__(access, ContentAccess)
        kind = 'same_original_bound_writer_added_to_instance_state'
    assert writer(access) is None
    return kind


@pytest.fixture
def _boundary_replica(first_parent, tmp_path):
    producer, reader = _api()
    ws = first_parent['workspace']; old = ws.original_material_workspace
    forcing = old.forcing_workspace; base = forcing.source_workspace
    parent_before = _inventory(_directories(first_parent))
    owned = tmp_path / 'owned-source-replica'; owned.mkdir(mode=0o700)
    base_copy = _boundary_replace(base, source_directory=owned / 'original', archive_directory=owned / 'base')
    forcing_copy = _boundary_replace(forcing, source_workspace=base_copy, archive_directory=owned / 'forcing')
    old_copy = _boundary_replace(old, forcing_workspace=forcing_copy, archive_directory=owned / 'material')
    ws_copy = _boundary_replace(ws, original_material_workspace=old_copy, repeat_archive_directory=owned / 'repeat')
    pairs = ((base.source_directory, base_copy.source_directory),
             (base.archive_directory, base_copy.archive_directory),
             (forcing.archive_directory, forcing_copy.archive_directory),
             (old.archive_directory, old_copy.archive_directory),
             (ws.repeat_archive_directory, ws_copy.repeat_archive_directory))
    setup_meter = point._Meter()
    for original, copied in pairs:
        with reader._store(copied, ws.access, write=True, meter=setup_meter) as store:
            for path in sorted(Path(original).iterdir()):
                data = path.read_bytes()
                assert len(path.name) == 64 and sha256(data).hexdigest() == path.name
                assert store.put(data, maximum=16 * 1024**2) == path.name
    handle = repeat.open_material(repeat.CursorRef(first_parent['handle'].cursor_sha256),
        definition_sha256=first_parent['handle']._definition, workspace=ws_copy)
    assert type(handle) is repeat.Handle and handle._token is repeat._TOKEN
    assert (handle._current, handle._basis, handle._cursor) == (first_parent['handle']._current,
        first_parent['handle']._basis, first_parent['handle']._cursor)
    assert handle.current['numeric']['schedule']['consumed_sequence'] == 13
    assert handle.current['effective_rights'] == {'use': True, 'display': True, 'redistribute': False}
    assert _inventory(_directories(first_parent)) == parent_before
    return handle, ws_copy, parent_before


def test_boundary_real_parent_exit_deadline_prevents_bundle_and_every_put(first_parent, tmp_path):
    producer, reader = _api(); directory = tmp_path / 'parent-exit-expired'
    before = _inventory(_directories(first_parent)); fd_before = qa._fd_count()
    held = repeat._held.__wrapped__.__code__
    observed = {'exit': [], 'bundle': [], 'publish': [], 'puts': [], 'stores': []}
    def observe(frame, event, value):
        code = frame.f_code
        if code is point._open_store_v2.__code__ and event == 'return':
            assert type(value) is MorphologyBlobStore
            observed['stores'].append(value)
        elif code is producer._Bundle.__new__.__code__ and event == 'call': observed['bundle'].append(True)
        elif code is producer._publish.__code__ and event == 'call': observed['publish'].append(True)
        elif code is MorphologyBlobStore.put.__code__ and event == 'call': observed['puts'].append(True)
        elif code is held and event == 'return' and not observed['exit']:
            meter = frame.f_locals['meter']
            assert type(meter) is point._Meter and meter.deadline - meter.started == 60.0
            assert len(observed['stores']) == 5
            assert all(store.__dict__['_fd'] is not None for store in observed['stores'])
            remaining = meter.deadline - _boundary_time.monotonic()
            assert remaining > 0.0, 'parent reached its normal-exit trigger before its real deadline'
            observed['exit'].append((meter.started, meter.deadline, remaining))
            _boundary_time.sleep(remaining + 0.025)
    codes = {held, point._open_store_v2.__code__, producer._Bundle.__new__.__code__,
             producer._publish.__code__, MorphologyBlobStore.put.__code__}
    with qa._watch(observe, codes):
        with pytest.raises(reader.RepeatArtifactHold, match=r'^WALL_HOLD:'):
            producer.produce_repeat_material_artifact(directory, first_parent['workspace'].access,
                handle=first_parent['handle'])
    assert len(observed['exit']) == 1 and observed['bundle'] == observed['publish'] == observed['puts'] == []
    assert len(observed['stores']) == 5 and all(store.__dict__['_fd'] is None for store in observed['stores'])
    assert qa._fd_count() == fd_before and not directory.exists()
    assert _inventory(_directories(first_parent)) == before


@pytest.mark.parametrize('phase', ['after_validation', 'after_transfer'])
def test_boundary_separate_output_policy_cannot_rebaseline_or_change_before_return(first_parent, tmp_path, phase):
    producer, reader = _api(); directory = tmp_path / ('output-policy-' + phase)
    source_access = first_parent['workspace'].access
    output_access = ContentAccess(source_access.owner_uid, source_access.reader_gid)
    assert output_access is not source_access
    original_vars = dict(vars(output_access)); original_state = _boundary_writer_state(output_access)
    before = _inventory(_directories(first_parent)); fd_before = qa._fd_count()
    observed = {'changed': [], 'puts': [], 'root': []}
    code = producer._validate.__code__ if phase == 'after_validation' else producer._publish.__code__
    def observe(frame, event, value):
        if frame.f_code is MorphologyBlobStore.put.__code__ and event == 'return': observed['puts'].append(value)
        if frame.f_code is code and event == 'return' and not observed['changed']:
            if phase == 'after_validation':
                assert type(value) is producer._Bundle
            else:
                assert type(value) is str and len(value) == 64
                observed['root'].append(value)
            observed['changed'].append(_boundary_valid_drift(output_access))
            assert _boundary_writer_state(output_access) != original_state
    try:
        with qa._watch(observe, {code, MorphologyBlobStore.put.__code__}):
            with pytest.raises(reader.RepeatArtifactHold, match=r'^STORAGE_HOLD: API-entry output policy changed'):
                producer.produce_repeat_material_artifact(directory, output_access, handle=first_parent['handle'])
        assert len(observed['changed']) == 1 and qa._fd_count() == fd_before
        if phase == 'after_validation':
            assert observed['puts'] == observed['root'] == [] and not directory.exists()
        else:
            assert len(observed['root']) == 1 and observed['puts'] and observed['puts'][-1] == observed['root'][0]
            assert observed['root'][0] in {path.name for path in directory.iterdir()}
            assert all(path.name == sha256(path.read_bytes()).hexdigest() for path in directory.iterdir())
    finally:
        vars(output_access).clear(); vars(output_access).update(original_vars)
    assert _inventory(_directories(first_parent)) == before


@pytest.mark.parametrize('fault', ['bytes', 'directory'])
def test_boundary_real_source_change_after_validation_blocks_renewal_before_put(first_parent, _boundary_replica, tmp_path, fault):
    producer, reader = _api(); handle, workspace, original_inventory = _boundary_replica
    directory = tmp_path / ('source-renewal-' + fault); fd_before = qa._fd_count()
    changed = []; puts = []; old_data = None; damaged = None; moved = None
    def observe(frame, event, value):
        nonlocal old_data, damaged, moved
        if frame.f_code is MorphologyBlobStore.put.__code__ and event == 'call': puts.append(True)
        if frame.f_code is producer._validate.__code__ and event == 'return' and not changed:
            assert type(value) is producer._Bundle and value.handle_state[2:] == (handle._current, handle._basis, handle._cursor)
            if fault == 'bytes':
                source = next(row for row in value.sources if row[0] == 'repeat')
                reference, expected, metadata = source[5][0]
                damaged = Path(source[1]) / reference; old_data = damaged.read_bytes()
                assert old_data == expected and sha256(old_data).hexdigest() == reference
                damaged.write_bytes(old_data + b' ')
            else:
                damaged = workspace.repeat_archive_directory
                moved = damaged.with_name('repeat-preserved-before-renewal')
                damaged.rename(moved)
                damaged.mkdir(mode=0o750)
                policy_fd = os.open(damaged, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
                try:
                    workspace.access.prepare_new(policy_fd, directory=True)
                finally:
                    os.close(policy_fd)
                assert damaged.stat().st_ino != moved.stat().st_ino
            changed.append(True)
    try:
        with qa._watch(observe, {producer._validate.__code__, MorphologyBlobStore.put.__code__}):
            reason = (r'^STORAGE_HOLD: renewed source metadata differs$' if fault == 'bytes' else
                      r'^CONTEXT_HOLD: source Handle or workspace changed during transfer$')
            with pytest.raises(reader.RepeatArtifactHold, match=reason):
                producer.produce_repeat_material_artifact(directory, workspace.access, handle=handle)
        assert changed == [True] and puts == [] and not directory.exists()
        assert qa._fd_count() == fd_before
    finally:
        if fault == 'bytes' and damaged is not None and old_data is not None:
            damaged.write_bytes(old_data)
        elif fault == 'directory' and moved is not None:
            damaged.rmdir(); moved.rename(damaged)
    recovered = repeat.open_material(repeat.CursorRef(handle.cursor_sha256),
        definition_sha256=handle._definition, workspace=workspace)
    assert type(recovered) is repeat.Handle
    assert (recovered._current, recovered._basis, recovered._cursor) == (handle._current, handle._basis, handle._cursor)
    assert _inventory(_directories(first_parent)) == original_inventory


def test_boundary_actual_deadline_expiry_after_all_transfer_cleanup_suppresses_root(first_parent, tmp_path):
    producer, reader = _api(); handle = first_parent['handle']; access = first_parent['workspace'].access
    directory = producer._target(tmp_path / 'expired-after-cleanup', handle._workspace)
    before = _inventory(_directories(first_parent)); fd_before = qa._fd_count()
    bundle = producer._validate(handle, _boundary_time.monotonic() + 600.0)
    assert type(bundle) is producer._Bundle and bundle.handle_state[2:] == (handle._current, handle._basis, handle._cursor)
    assert qa._fd_count() == fd_before
    # A stricter real remaining envelope tests the same private transfer predicates without waiting600s.
    deadline = _boundary_time.monotonic() + 180.0
    assert deadline <= bundle.deadline
    observed = {'stores': [], 'expired_after_cleanup': []}
    closed = reader._store.__wrapped__.__code__
    def observe(frame, event, value):
        if frame.f_code is point._open_store_v2.__code__ and event == 'return':
            assert type(value) is MorphologyBlobStore
            observed['stores'].append(value)
        elif frame.f_code is closed and event == 'return' and len(observed['stores']) == 6:
            if all(store.__dict__['_fd'] is None for store in observed['stores']) and not observed['expired_after_cleanup']:
                assert (directory / bundle.root).is_file()
                remaining = deadline - _boundary_time.monotonic()
                assert remaining > 0.0, 'all real FDs closed before the injected deadline crossing'
                observed['expired_after_cleanup'].append(remaining)
                _boundary_time.sleep(remaining + 0.025)
    with qa._watch(observe, {point._open_store_v2.__code__, closed}):
        with pytest.raises(reader.RepeatArtifactHold, match=r'^WALL_HOLD: whole artifact deadline exhausted'):
            producer._publish(directory, access, handle, bundle, deadline, _boundary_writer_state(access))
    assert len(observed['expired_after_cleanup']) == 1 and len(observed['stores']) == 6
    assert all(store.__dict__['_fd'] is None for store in observed['stores']) and qa._fd_count() == fd_before
    assert (directory / bundle.root).is_file()
    assert all(path.name == sha256(path.read_bytes()).hexdigest() for path in directory.iterdir())
    assert _inventory(_directories(first_parent)) == before


def _stored_adapter_increment(quantity):
    value = Fraction(int(quantity['numerator']), int(quantity['denominator'])) + 1
    return {'numerator': str(value.numerator), 'denominator': str(value.denominator),
            'unit': quantity['unit']}


def _stored_adapter_changed_artifact(packet, directory, case):
    directory = shutil.copytree(packet['directory'], directory)
    manifest = deepcopy(packet['manifest'])
    assert len(manifest['transitions']) == 1 and len(manifest['frames']) == 2
    transition = manifest['transitions'][0]
    assert transition['kind'] == 'material_adoption'
    old_current = transition['after_current']['sha256']
    old_page = transition['history_page']['sha256']
    old_cursor = transition['cursor']['sha256']
    old_point = transition['point']['receipt']['sha256']
    old_witness = transition['point']['witness']['sha256']
    current_raw, current = _blob(directory, old_current)
    _, page = _blob(directory, old_page)
    _, cursor = _blob(directory, old_cursor)
    point_raw, receipt = _blob(directory, old_point)
    _, witness = _blob(directory, old_witness)
    claims = {'original_current': deepcopy(current), 'original_current_raw': current_raw,
              'original_point': deepcopy(receipt), 'original_point_raw': point_raw}
    replacements = {}
    if case in {'transfer', 'clock'}:
        if case == 'transfer':
            key = next(k for k in sorted(current['numeric']['geometry_diagnostics'])
                       if k.startswith('leaf_'))
            diagnostic = current['numeric']['geometry_diagnostics'][key]
            for name in ('potential_exact', 'deficit_exact'):
                diagnostic[name] = _stored_adapter_increment(diagnostic[name])
            assert x(diagnostic['deficit_exact']) == (
                x(diagnostic['potential_exact']) - x(diagnostic['realized_exact']))
            claims['key'] = key
        else:
            current['numeric']['schedule']['age_exact'] = _stored_adapter_increment(
                current['numeric']['schedule']['age_exact'])
        new_current = _put(directory, current)
        claims['current'] = current
        page['after_current_sha256'] = new_current['sha256']
        cursor['current_sha256'] = new_current['sha256']
        transition['after_current'] = new_current
        manifest['source']['final']['current'] = new_current
        replacements[old_current] = new_current
    else:
        assert receipt['point_data']['leaf_receipts']
        if case == 'funding':
            balance = receipt['point_data']['point_balances']['buffer']
            balance['residual_exact'] = _stored_adapter_increment(balance['residual_exact'])
        else:
            assert case == 'initialization'
            initialization = receipt['point_data']['leaf_receipts'][0]['initialization']
            state = initialization['state']
            state['age_exact'] = _stored_adapter_increment(state['age_exact'])
            state['anchor']['age_exact'] = deepcopy(state['age_exact'])
            identity = {'model_version': initialization['model_version'], 'operation': 'initialize',
                        'input_id': state['leaf_id'], 'state': state}
            initialization['input_sha256'] = sha256(canonical(identity)).hexdigest()
        receipt['calculation_sha256'] = sha256(canonical(
            {k: v for k, v in receipt.items() if k != 'calculation_sha256'})).hexdigest()
        new_point = _put(directory, receipt)
        witness['public_calculation_sha256'] = receipt['calculation_sha256']
        witness['public_point_sha256'] = new_point['sha256']
        new_witness = _put(directory, witness)
        claims['point'] = receipt
        claims['witness'] = witness
        page['evidence']['point_sha256'] = new_point['sha256']
        page['evidence']['point_witness_sha256'] = new_witness['sha256']
        transition['point'].update(receipt=new_point, witness=new_witness,
                                   calculation_sha256=receipt['calculation_sha256'])
        manifest['blob_groups']['points'] = sorted(
            [new_point if v['sha256'] == old_point else v
             for v in manifest['blob_groups']['points']], key=lambda v: v['sha256'])
        replacements[old_witness] = new_witness
    new_page = _put(directory, page)
    cursor['history_page_sha256'] = new_page['sha256']
    new_cursor = _put(directory, cursor)
    transition.update(history_page=new_page, cursor=new_cursor)
    manifest['source']['final']['cursor'] = new_cursor
    replacements.update({old_page: new_page, old_cursor: new_cursor})
    manifest['blob_groups']['repeat'] = sorted(
        [replacements.get(v['sha256'], v) for v in manifest['blob_groups']['repeat']],
        key=lambda v: v['sha256'])
    # The required semantic rejection precedes downstream frame reconstruction.
    # The exact cause and genuine helper observations below cannot pass on a later link mismatch.
    return directory, _put(directory, manifest)['sha256'], claims


@pytest.mark.parametrize('case', ['transfer', 'clock', 'funding', 'initialization'])
def test_stored_adapter_rejects_rehashed_independent_observation(first_artifact, tmp_path, case):
    _, reader = _api()
    packet = first_artifact
    originals = [packet['directory'], *_directories(packet['parent'])]
    original_inventory = _inventory(originals)
    fd_before = qa._fd_count()
    assert reader.read_repeat_material_manifest(
        packet['directory'], packet['access'], packet['root']) == packet['raw']
    directory, root, claim = _stored_adapter_changed_artifact(
        packet, tmp_path / ('changed-' + case), case)
    copied_inventory = _inventory([directory])
    if case in {'funding', 'initialization'}:
        assert canonical(reader.proof.pack_point_witness(claim['point'])) == canonical(claim['witness'])
    reasons = {
        'transfer': 'PROOF_HOLD: independently recomputed transfer diagnostics differ',
        'clock': 'HISTORY_HOLD: exact after basis/current/cursor required',
        'funding': 'PROOF_HOLD: full public point, inner calculation or work identity differs',
        'initialization': 'PROOF_HOLD: complete saved initialization envelope differs'}
    events = {'target_entries': 0, 'numeric': [], 'adoption': [], 'point': [], 'books': [], 'unwind': []}
    six = ('potential_exact', 'realized_exact', 'deficit_exact', 'lifetime_potential_exact',
           'lifetime_realized_exact', 'lifetime_deficit_exact')
    point_books = reader.point.old.point_books.calculate
    if case == 'transfer':
        codes = {reader._stored_books.__code__}
    elif case == 'clock':
        codes = {reader._stored_repeat_numeric.__code__, reader._stored_repeat_adoption.__code__}
    elif case == 'funding':
        codes = {reader._stored_point_saved.__code__, point_books.__code__}
    else:
        codes = {reader._stored_leaf.__code__}

    def same_point(value):
        return (type(value) is dict and
                value.get('calculation_sha256') == claim['original_point']['calculation_sha256'])

    def observe(frame, event, value):
        local = frame.f_locals
        if case == 'transfer' and frame.f_code is reader._stored_books.__code__:
            if local.get('observed') != claim['current']['numeric']['geometry_diagnostics']:
                return
            if event == 'call':
                events['target_entries'] += 1
            elif event == 'unwind':
                key = claim['key']
                events['unwind'].append({'reason': str(value), 'key': local.get('key'),
                    'saved': canonical(local['saved']),
                    'rebuilt': canonical({k: local['diagnostics'][key][k] for k in six})})
        elif case == 'clock':
            if frame.f_code is reader._stored_repeat_adoption.__code__ and same_point(local.get('receipt')):
                if event == 'call':
                    events['target_entries'] += 1
                elif event == 'return':
                    events['adoption'].append(canonical(value[1]))
            elif frame.f_code is reader._stored_repeat_numeric.__code__ and event == 'return':
                parent = frame.f_back
                if (parent is not None and parent.f_code is reader._stored_repeat_adoption.__code__
                        and same_point(parent.f_locals.get('receipt'))):
                    events['numeric'].append(canonical(value['schedule']))
        elif case == 'funding':
            if frame.f_code is reader._stored_point_saved.__code__:
                if (local.get('source') != claim['original_point']['source'] or
                        local.get('pending') != claim['original_point']['pending_page_sha256']):
                    return
                if event == 'call':
                    events['target_entries'] += 1
                elif event == 'return':
                    events['point'].append(canonical(value))
            elif frame.f_code is point_books.__code__ and event == 'return':
                parent = frame.f_back
                if (parent is not None and parent.f_code is reader._stored_point_data.__code__ and
                        parent.f_locals['candidate']['calculation_sha256'] ==
                        claim['original_point']['candidate']['calculation_sha256']):
                    events['books'].append(canonical(value['point_balances']['buffer']))
        elif case == 'initialization' and frame.f_code is reader._stored_leaf.__code__:
            saved = claim['point']['point_data']['leaf_receipts'][0]['initialization']
            if (local.get('saved') != saved or
                    local.get('leaf') != claim['original_point']['inputs']['leaf']['declaration']):
                return
            if event == 'call':
                events['target_entries'] += 1
            elif event == 'unwind':
                events['unwind'].append({'reason': str(value), 'rebuilt': canonical(local['receipt'])})

    # Keep raises outside the observer so real selected traceback frames reach _watch.
    with pytest.raises(reader.RepeatArtifactHold) as held:
        with qa._watch(observe, codes):
            reader.read_repeat_material_manifest(directory, packet['access'], root)
    assert str(held.value) == reasons[case]
    assert events['target_entries'] == 1
    if case == 'transfer':
        key = claim['key']
        assert len(events['unwind']) == 1 and events['unwind'][0]['key'] == key
        assert events['unwind'][0]['reason'] == reasons[case]
        assert events['unwind'][0]['saved'] == canonical(claim['current']['numeric']['geometry_diagnostics'][key])
        original = claim['original_current']['numeric']['geometry_diagnostics'][key]
        assert events['unwind'][0]['rebuilt'] == canonical({k: original[k] for k in six})
        assert events['unwind'][0]['saved'] != canonical(original)
    elif case == 'clock':
        expected = claim['original_current']['numeric']['schedule']
        assert events['numeric'] == [canonical(expected)]
        assert events['adoption'] == [claim['original_current_raw']]
        assert canonical(claim['current']['numeric']['schedule']) != canonical(expected)
    elif case == 'funding':
        expected = claim['original_point']['point_data']['point_balances']['buffer']
        assert events['books'] == [canonical(expected)]
        assert events['point'] == [claim['original_point_raw']]
        assert canonical(claim['point']['point_data']['point_balances']['buffer']) != canonical(expected)
    else:
        original = claim['original_point']['point_data']['leaf_receipts'][0]['initialization']
        assert events['unwind'] == [{'reason': reasons[case], 'rebuilt': canonical(original)}]
        assert canonical(claim['point']['point_data']['leaf_receipts'][0]['initialization']) != canonical(original)
    assert _inventory([directory]) == copied_inventory
    assert _inventory(originals) == original_inventory and qa._fd_count() == fd_before
    assert reader.read_repeat_material_manifest(
        packet['directory'], packet['access'], packet['root']) == packet['raw']
    assert _inventory(originals) == original_inventory and qa._fd_count() == fd_before
    observation = {'schema_version': 'stored-adapter-negative-observation-v1', 'case': case,
        'reason': str(held.value), 'original_root': packet['root'], 'changed_root': root,
        'target_entries': events['target_entries'],
        'returned_numeric': len(events['numeric']), 'returned_adoption': len(events['adoption']),
        'returned_point': len(events['point']), 'returned_point_books': len(events['books']),
        'real_selected_unwinds': len(events['unwind']), 'original_recovery_equal': True,
        'FD_before_after': [fd_before, qa._fd_count()],
        'owned_copy_and_original_inventory_unchanged': True,
        'curve_equation_or_normalizer_representability_claimed': False}
    output = tmp_path / 'stored-adapter-negative-observation-v1.private.json'
    with output.open('xb') as stream:
        stream.write(canonical(observation))
        stream.flush()
        os.fsync(stream.fileno())
    output.chmod(0o400)
