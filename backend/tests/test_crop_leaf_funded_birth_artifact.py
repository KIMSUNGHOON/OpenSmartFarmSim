from copy import deepcopy
from hashlib import sha256
from fractions import Fraction
import json
import os

import pytest

from app import crop_leaf_funded_birth_artifact_reader as reader
from app import crop_leaf_funded_birth_artifact_producer as producer
from app.content_access import ContentAccess
from app.crop_morphology_artifact_io import MorphologyArtifactHold
from test_crop_leaf_carbon_stock_artifact import inputs as stock_inputs, profiles

ACCESS = ContentAccess(os.geteuid(), os.getegid())


def encoded(v): return json.dumps(v, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()


def declared_inputs(case=0):
    v = stock_inputs(case, dt=.125, count=4); v['schema_version'] = 'funded-leaf-artifact-input-v1'
    leaf = deepcopy(v['program']['leaves'][0]); leaf.update(leaf_id='new-0', thermal_age={'value': 0., 'unit': 'degC_day'},
        initial_area={'value': .1, 'unit': 'm2'}, initial_carbon={'value': .25, 'unit': 'mg_CH2O/m2_floor'})
    v['births'] = [{'step_index': 2, 'point_inputs': {'schema_version': 'leaf-funded-birth-point-input-v1',
        'input_id': 'birth-one', 'origin': 'synthetic', 'policy': reader.POLICY, 'context_sha256': '1'*64,
        'checkpoint_sha256': '2'*64, 'at_elapsed_seconds_exact': reader.stock._offset(.125, 2),
        'model_floor_area': deepcopy(v['program']['model_floor_area']), 'events': [{'event_id': 'event-0',
        'attachment_internode_id': 'internode-0', 'incoming_temperature': {'value': 22., 'unit': 'degC'}, 'leaf': leaf}]}}]
    return v


def test_closed_plan_parser_preserves_exact_own_inputs_and_private_rights():
    v = declared_inputs(); raw = encoded(v)
    assert reader._inputs(raw) == v
    assert reader._inputs(raw)['rights']['redistribute'] is False


@pytest.mark.parametrize('change', [
    lambda v: v.update(extra=1), lambda v: v.update(births=[]), lambda v: v.update(origin='observed'),
    lambda v: v['rights'].update(display=False), lambda v: v['rights'].update(redistribute=1),
    lambda v: v['births'][0].update(step_index=True), lambda v: v['births'][0].update(step_index=5),
    lambda v: v['births'][0]['point_inputs'].update(policy='unfunded'),
    lambda v: v['births'][0]['point_inputs'].update(context_sha256='invalid'),
    lambda v: v['births'][0]['point_inputs']['at_elapsed_seconds_exact'].update(unit='day'),
    lambda v: v['births'][0]['point_inputs']['model_floor_area'].update(value=99.),
    lambda v: v['births'][0]['point_inputs']['events'][0]['leaf']['initial_carbon'].update(value=0.),
    lambda v: v['births'][0]['point_inputs']['events'][0]['leaf']['initial_carbon'].update(value=True),
    lambda v: v['births'][0]['point_inputs']['events'][0]['leaf']['initial_carbon'].update(unit='mg_CH2O'),
    lambda v: v['births'][0]['point_inputs']['events'][0]['leaf']['thermal_age'].update(value=1.),
    lambda v: v['births'][0]['point_inputs']['events'].append(deepcopy(v['births'][0]['point_inputs']['events'][0]))])
def test_invalid_plan_units_rights_time_and_duplicates_are_rejected(change):
    v = declared_inputs(); change(v)
    with pytest.raises(MorphologyArtifactHold): reader._inputs(encoded(v))


def calculated_inputs(profiles, case=0, *, steps=(0, 2), dt=.125, count=4, new_count=1, base_program=None):
    model = producer.model
    v = stock_inputs(case, dt=dt, count=count); v.update(schema_version='funded-leaf-artifact-input-v1', births=[])
    if base_program is not None: v['program'] = deepcopy(base_program)
    root = model.parent.prepare_context(program=v['program'], step_seconds=dt, step_count=count, **profiles)
    context = None; cp = model.parent.start(root); frames = []
    def save():
        engine = model if context is not None else model.parent
        current = context if context is not None else root
        frames.append({'raw': engine.checkpoint_bytes(current, cp), 'value': cp.value,
                       'program': context.program if context is not None else json.loads(root._program)})
    for step in range(count+1):
        if step:
            engine = model if context is not None else model.parent
            cp = engine.advance_chunk(context if context is not None else root, cp, 1)['checkpoint']
        save()
        for _ in range(steps.count(step)):
            i = len(v['births']); events = []
            for j in range(new_count):
                suffix = str(i) if new_count == 1 else f'{i}-{j}'
                leaf = deepcopy(v['program']['leaves'][0])
                leaf.update(leaf_id=f'funded-new-{suffix}', thermal_age={'value': 0., 'unit': 'degC_day'},
                    initial_area=model.short.old.leaf_area._area_at(Fraction(0), leaf['curve']),
                    initial_carbon={'value': 1., 'unit': 'mg_CH2O/m2_floor'}, carbon_removal={'value': 0., 'unit': 'mg_CH2O/m2_floor/s'})
                events.append({'event_id': f'event-{suffix}', 'attachment_internode_id': f'declared-internode-{suffix}',
                               'incoming_temperature': {'value': 22., 'unit': 'degC'}, 'leaf': leaf})
            point = {'schema_version': 'leaf-funded-birth-point-input-v1', 'input_id': f'funding-{i}', 'origin': 'synthetic',
                'policy': reader.POLICY, 'context_sha256': context.root_sha256 if context is not None else root.root_sha256,
                'checkpoint_sha256': cp.sha256, 'at_elapsed_seconds_exact': reader.stock._offset(dt, step),
                'model_floor_area': deepcopy(v['program']['model_floor_area']), 'events': events}
            raw = frames[-1]['raw']; digest = sha256(raw).hexdigest(); v['births'].append({'step_index': step, 'point_inputs': point})
            if context is None:
                context = model.prepare_context(parent_context=root, raw_parent_checkpoint=raw,
                    expected_parent_sha256=digest, inputs=point)
            else:
                context = model.adopt_births(context=context, raw_checkpoint=raw, expected_sha256=digest, inputs=point)
            cp = model.start(context); save()
    return v, frames


@pytest.mark.parametrize('case', range(6))
def test_original_raw_checkpoints_and_variable_leaf_dtos_match_direct_model(tmp_path, profiles, case):
    from app.crop_morphology_artifact_io import MorphologyBlobStore
    v, original = calculated_inputs(profiles, case)
    raw = encoded(v); directory = tmp_path/'blobs'
    root = producer.produce_funded_leaf_artifact(directory, ACCESS, inputs_raw=raw, **profiles)
    m = reader.read_funded_leaf_manifest(directory, ACCESS, root)
    assert m['source_rights'] == v['rights'] and m['source_rights']['redistribute'] is False
    assert len(m['samples']) == len(original) == 7 and len(m['events']) == 2
    with MorphologyBlobStore(directory, ACCESS) as store:
        assert store.get(m['sources']['inputs']['sha256'], maximum=reader.MAX) == raw
        for i, source in enumerate(original):
            d = m['samples'][i]; frame = reader.read_funded_leaf_frame(directory, ACCESS, root, index=i)
            assert store.get(d['checkpoint_sha256'], maximum=reader.CHECKPOINT_MAX) == source['raw']
            assert frame['sample'] == source['value']['last_confirmed']
            assert frame['leaf_ids'] == [leaf['leaf_id'] for leaf in source['program']['leaves']]
            assert frame['integrated_transfers'] == source['value']['integrated_transfers']
            n = len(frame['leaves']); y = source['value']['last_confirmed']['state']
            for j, leaf in enumerate(frame['leaves']):
                assert [leaf[k]['value'] for k in ('thermal_age', 'area', 'carbon')] == [y[107+j], y[107+n+j], y[107+2*n+j]]
            assert frame['G0_G4'] == 'not_assessed'
    assert producer.produce_funded_leaf_artifact(directory, ACCESS, inputs_raw=raw, **profiles) == root


@pytest.mark.parametrize('steps,dt', [((0,), .125), ((2,), 1/3), ((4,), .125), ((0, 0), 1/3), ((1, 3), .125)])
def test_initial_middle_terminal_same_time_and_fractional_event_frames(tmp_path, profiles, steps, dt):
    v, original = calculated_inputs(profiles, steps=steps, dt=dt)
    directory = tmp_path/'blobs'; root = producer.produce_funded_leaf_artifact(directory, ACCESS, inputs_raw=encoded(v), **profiles)
    m = reader.read_funded_leaf_manifest(directory, ACCESS, root)
    for i, source in enumerate(original):
        frame = reader.read_funded_leaf_frame(directory, ACCESS, root, index=i)
        assert frame['sample'] == source['value']['last_confirmed']
        assert frame['at']['elapsed_seconds_exact'] == reader.stock._offset(dt, source['value']['step_index'])
        if frame['event_sequence']:
            for name in ('segment_integrated_transfers', 'point_totals', 'global_balance_residuals', 'global_balance_budgets'):
                assert frame[name] == source['value'][name]
            for leaf in frame['leaves'][3:]: assert leaf['attachment']['status'] == 'declared_not_bound'
    assert len(m['samples']) == 5+len(steps)
    if steps == (0, 0): assert [d['event_sequence'] for d in m['samples'][:3]] == [0, 1, 2]


@pytest.fixture(scope='module')
def saved(tmp_path_factory, profiles):
    v, frames = calculated_inputs(profiles)
    directory = tmp_path_factory.mktemp('funded-reader')/'blobs'
    root = producer.produce_funded_leaf_artifact(directory, ACCESS, inputs_raw=encoded(v), **profiles)
    return directory, root, v, frames


def bad_last_checkpoint(saved, change):
    from app.crop_morphology_artifact_io import MorphologyBlobStore
    directory, root, _, _ = saved
    with MorphologyBlobStore(directory, ACCESS, write=True) as store:
        m = json.loads(store.get(root, maximum=reader.MAX)); d = m['samples'][-1]
        cp = json.loads(store.get(d['checkpoint_sha256'], maximum=reader.CHECKPOINT_MAX))
        change(cp); raw = encoded(cp); d.update(checkpoint_sha256=store.put(raw, maximum=reader.CHECKPOINT_MAX), checkpoint_bytes=len(raw))
        return store.put(encoded(m), maximum=reader.MAX)


@pytest.mark.parametrize('change', [
    lambda cp: cp.update(extra=1), lambda cp: cp.update(step_index=True), lambda cp: cp.update(event_sequence=1),
    lambda cp: cp.update(phase='root_interval'), lambda cp: cp.update(context_sha256='0'*64),
    lambda cp: cp['last_confirmed']['state'].pop(), lambda cp: cp['last_confirmed']['state'].__setitem__(0, True),
    lambda cp: cp['last_confirmed']['derived']['leaf_carbohydrate'].update(unit='mg_CH2O'),
    lambda cp: cp['point_totals']['growth_respiration'].update(value=0.),
    lambda cp: cp['integrated_transfers']['photosynthesis'].update(unit='mg_CH2O'),
    lambda cp: cp['segment_integrated_transfers']['photosynthesis'].update(value=True),
    lambda cp: cp['global_balance_residuals']['carbohydrate'].update(value=1e99),
    lambda cp: cp['global_balance_budgets']['carbohydrate'].update(value=-1.)])
def test_rehashed_malformed_checkpoint_still_fails_semantic_graph_checks(saved, change):
    root = bad_last_checkpoint(saved, change)
    with pytest.raises(reader.FundedLeafArtifactHold): reader.read_funded_leaf_manifest(saved[0], ACCESS, root)


def test_reader_has_no_growth_point_calls_and_returns_copies(saved, monkeypatch):
    directory, root, _, _ = saved
    def forbidden(*a, **k): raise AssertionError('read cannot calculate growth or point')
    monkeypatch.setattr(producer.model.short, '_evaluate', forbidden)
    monkeypatch.setattr(producer.model.point, '_apply_current', forbidden)
    monkeypatch.setattr(producer.model, 'restore_context', forbidden)
    first = reader.read_funded_leaf_frame(directory, ACCESS, root, index=3)
    original = encoded(first); first['leaves'][0]['area']['value'] = 999.; first['point_totals']['growth_respiration']['value'] = 999.
    assert encoded(reader.read_funded_leaf_frame(directory, ACCESS, root, index=3)) == original


@pytest.mark.parametrize('index', [-1, True, 1.5, 7])
def test_index_bounds(saved, index):
    with pytest.raises(MorphologyArtifactHold): reader.read_funded_leaf_frame(saved[0], ACCESS, saved[1], index=index)


def test_late_file_policy_and_late_code_change_fail_before_return(saved, monkeypatch):
    directory, root, _, _ = saved; original = reader._fence
    def changed(store, m, raws):
        path = directory/m['sources']['inputs']['sha256']; os.chmod(path, 0o644)
        try: return original(store, m, raws)
        finally: os.chmod(path, 0o640)
    monkeypatch.setattr(reader, '_fence', changed)
    with pytest.raises(reader.FundedLeafArtifactHold): reader.read_funded_leaf_frame(directory, ACCESS, root, index=0)
    monkeypatch.setattr(reader, '_fence', original); pins = reader._pins; calls = []
    def changed_pins():
        value = pins(); calls.append(1)
        if len(calls) > 1: value[next(iter(value))] = '0'*64
        return value
    monkeypatch.setattr(reader, '_pins', changed_pins)
    with pytest.raises(reader.FundedLeafArtifactHold): reader.read_funded_leaf_manifest(directory, ACCESS, root)


def test_partial_write_and_domain_hold_publish_no_completed_root(tmp_path, profiles, monkeypatch):
    from app.crop_morphology_artifact_io import MorphologyBlobStore
    v, _ = calculated_inputs(profiles); put = MorphologyBlobStore.put; calls = []
    def fail_put(self, raw, *, maximum):
        calls.append(1)
        if len(calls) == 12: raise OSError('injected partial write')
        return put(self, raw, maximum=maximum)
    monkeypatch.setattr(MorphologyBlobStore, 'put', fail_put)
    with pytest.raises(reader.FundedLeafArtifactHold): producer.produce_funded_leaf_artifact(tmp_path/'partial', ACCESS, inputs_raw=encoded(v), **profiles)
    monkeypatch.setattr(MorphologyBlobStore, 'put', put)
    v['births'][0]['point_inputs']['events'][0]['leaf']['base_temperature']['value'] = 35.
    with pytest.raises(reader.FundedLeafArtifactHold, match='TEMPERATURE_DOMAIN_HOLD'):
        producer.produce_funded_leaf_artifact(tmp_path/'held', ACCESS, inputs_raw=encoded(v), **profiles)
    for directory in (tmp_path/'partial', tmp_path/'held'):
        for path in directory.iterdir():
            try: value = json.loads(path.read_bytes())
            except (ValueError, UnicodeError): continue
            assert not isinstance(value, dict) or value.get('schema_version') != 'funded-leaf-research-artifact-v1'


@pytest.mark.parametrize('which', ['point', 'context_snapshot'])
@pytest.mark.parametrize('change', ['extra', 'source', 'state'])
def test_rehashed_event_sources_cannot_change_original_linked_evidence(saved, which, change):
    from app.crop_morphology_artifact_io import MorphologyBlobStore
    directory, root, _, _ = saved
    with MorphologyBlobStore(directory, ACCESS, write=True) as store:
        m = json.loads(store.get(root, maximum=reader.MAX)); event = m['events'][0]; descriptor = event[which]
        value = json.loads(store.get(descriptor['sha256'], maximum=reader.MAX))
        if change == 'extra': value['extra'] = 1
        elif which == 'point':
            if change == 'source': value['code_sha256'] = '0'*64
            else: value['after_sample']['state'][0] += 1.
            value['calculation_sha256'] = reader._digest({k: v for k, v in value.items() if k != 'calculation_sha256'})
        elif change == 'source': value['manifest']['identity']['point_code_sha256'] = '0'*64
        else:
            value['seed']['anchors'][0]['value'] += 1.
            value['manifest']['seed_sha256'] = reader._digest(value['seed'])
        raw = encoded(value); event[which] = {'sha256': store.put(raw, maximum=reader.MAX), 'bytes': len(raw)}
        if which == 'context_snapshot': event['context_sha256'] = reader._digest(value['manifest'])
        altered = store.put(encoded(m), maximum=reader.MAX)
    with pytest.raises(reader.FundedLeafArtifactHold): reader.read_funded_leaf_manifest(directory, ACCESS, altered)


def test_wrong_declared_point_hash_is_not_filled_by_producer(tmp_path, profiles):
    v, _ = calculated_inputs(profiles); v['births'][0]['point_inputs']['checkpoint_sha256'] = '0'*64
    raw = encoded(v)
    with pytest.raises(reader.FundedLeafArtifactHold, match='HASH_HOLD'):
        producer.produce_funded_leaf_artifact(tmp_path/'blobs', ACCESS, inputs_raw=raw, **profiles)
    assert encoded(v) == raw


def test_same_input_new_directory_has_same_root_and_original_fd_count(tmp_path, profiles):
    v, _ = calculated_inputs(profiles, steps=(2,), dt=1/3)
    before = len(os.listdir('/proc/self/fd'))
    a = producer.produce_funded_leaf_artifact(tmp_path/'a', ACCESS, inputs_raw=encoded(v), **profiles)
    b = producer.produce_funded_leaf_artifact(tmp_path/'b', ACCESS, inputs_raw=encoded(v), **profiles)
    assert a == b
    assert reader.read_funded_leaf_manifest(tmp_path/'a', ACCESS, a) == reader.read_funded_leaf_manifest(tmp_path/'b', ACCESS, b)
    assert len(os.listdir('/proc/self/fd')) == before


@pytest.mark.parametrize('boundary', ['minimum', 'maximum'])
def test_original_one_leaf_and_result_512_leaf_boundary(tmp_path, profiles, boundary):
    p = stock_inputs()['program']; count = 4; new_count = 1
    if boundary == 'minimum':
        share = p['leaves'][0]['initial_area']['value']/sum(leaf['initial_area']['value'] for leaf in p['leaves'])
        p['scenario']['climate_state']['canopy_sensible_energy']['value'] *= share; p['leaves'] = p['leaves'][:1]
    else: new_count = 509; count = 1
    v, frames = calculated_inputs(profiles, steps=(0,), count=count, new_count=new_count, base_program=p)
    directory = tmp_path/'blobs'; root = producer.produce_funded_leaf_artifact(directory, ACCESS, inputs_raw=encoded(v), **profiles)
    frame = reader.read_funded_leaf_frame(directory, ACCESS, root, index=len(frames)-1)
    assert len(frame['leaves']) == (2 if boundary == 'minimum' else 512)
    assert frame['sample'] == frames[-1]['value']['last_confirmed']


def test_recorded_private_rights_cannot_be_revoked_or_promoted_in_graph(saved):
    from app.crop_morphology_artifact_io import MorphologyBlobStore
    directory, root, _, _ = saved
    with MorphologyBlobStore(directory, ACCESS, write=True) as store:
        original = json.loads(store.get(root, maximum=reader.MAX)); m = deepcopy(original)
        m['source_rights']['redistribute'] = True
        promoted = store.put(encoded(m), maximum=reader.MAX)
        m = deepcopy(original); inputs = json.loads(store.get(m['sources']['inputs']['sha256'], maximum=reader.MAX))
        inputs['rights']['display'] = False; m['source_rights'] = inputs['rights']; raw = encoded(inputs)
        m['sources']['inputs'] = {'sha256': store.put(raw, maximum=reader.MAX), 'bytes': len(raw)}
        revoked = store.put(encoded(m), maximum=reader.MAX)
    for altered in (promoted, revoked):
        with pytest.raises(reader.FundedLeafArtifactHold): reader.read_funded_leaf_manifest(directory, ACCESS, altered)
