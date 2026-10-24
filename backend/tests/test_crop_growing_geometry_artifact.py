from copy import deepcopy
from fractions import Fraction
from hashlib import sha256
import json
import os
from pathlib import Path

import pytest

from app import crop_growing_geometry_continuation as continuation
from app import crop_growing_geometry_artifact_producer as producer
from app import crop_growing_geometry_artifact_reader as reader
from app.content_access import ContentAccess
from app.crop_growth_rates import ReferenceParameters as Growth
from app.crop_fruit_cohorts import ReferenceFruitCohortParameters as Cohort
from app.crop_fruit_transport import ReferenceFruitTransportParameters as Transport
from app.crop_canopy_exchange import ReferenceParameters as Exchange
from app.crop_morphology_artifact_io import MorphologyArtifactHold, MorphologyBlobStore

ROOT = Path(__file__).resolve().parents[2]
CASES = json.loads((ROOT/'fixtures/crop-growing-geometry-climate-reference-v1.json').read_bytes())['cases']
ACCESS = ContentAccess(os.geteuid(), os.getegid())


@pytest.fixture(scope='module')
def profiles():
    return {name: kind((ROOT/'fixtures'/file).read_bytes()) for name, kind, file in (
        ('growth_profile', Growth, 'crop-growth-reference-parameters-v1.json'),
        ('cohort_profile', Cohort, 'crop-fruit-cohort-reference-parameters-v1.json'),
        ('transport_profile', Transport, 'crop-fruit-transport-reference-parameters-v1.json'),
        ('exchange_profile', Exchange, 'crop-canopy-exchange-reference-parameters-v1.json'))}


def inputs(case=0, *, dt=2, count=16):
    p = deepcopy(CASES[case]['program'])
    return {'schema_version': 'growing-geometry-artifact-input-v1', 'input_id': p['input_id'],
        'origin': 'synthetic', 'program': p, 'time_origin_utc': '2026-10-01T00:00:00Z',
        'step_seconds': dt, 'step_count': count,
        'rights': {'declaration_id': 'own-research-fixture', 'revision': 'v1',
            'declared_at_utc': '2026-10-24T07:22:18Z', 'ownership_asserted': True,
            **dict.fromkeys(('access', 'store', 'use', 'transform', 'display'), True), 'redistribute': False}}


def encoded(value): return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()


@pytest.mark.parametrize('case', range(6))
def test_saved_frames_preserve_original_checkpoint_bytes_every_state_and_ledger(tmp_path, profiles, case):
    source = inputs(case); raw = encoded(source); directory = tmp_path/'blobs'
    root = producer.produce_growing_geometry_artifact(directory, ACCESS, inputs_raw=raw, **profiles)
    m = reader.read_growing_geometry_manifest(directory, ACCESS, root)
    assert m['source_rights'] == source['rights'] and m['source_rights']['redistribute'] is False
    assert len(m['samples']) == 17 and m['G0_G4'] == 'not_assessed'
    ctx = continuation.prepare_context(program=source['program'], step_seconds=2, step_count=16, **profiles)
    cp = continuation.start(ctx)
    with MorphologyBlobStore(directory, ACCESS) as store:
        assert store.get(m['sources']['inputs']['sha256'], maximum=reader.MAX) == raw
        assert store.get(m['sources']['request']['sha256'], maximum=reader.MAX) == encoded(source['program'])
        for name, profile in profiles.items():
            assert store.get(m['sources'][name]['sha256'], maximum=reader.MAX) == profile.raw_bytes
        for i in range(17):
            if i: cp = continuation.advance_chunk(ctx, cp, 1)['checkpoint']
            frame = reader.read_growing_geometry_frame(directory, ACCESS, root, index=i)
            saved = cp.value; sample = saved['last_confirmed']; n = 3
            assert store.get(m['samples'][i]['checkpoint_sha256'], maximum=reader.CHECKPOINT_MAX) == continuation.checkpoint_bytes(ctx, cp)
            assert frame['checkpoint_sha256'] == cp.sha256 and frame['sample'] == sample
            assert frame['state_sha256'] == sha256(encoded(sample['state'])).hexdigest()
            assert frame['elapsed_seconds'] == sample['elapsed_seconds']
            assert frame['at']['elapsed_seconds_exact'] == {'numerator': str(i*2), 'denominator': '1', 'unit': 's'}
            assert frame['leaf_ids'] == ctx.manifest['state_layout']['leaf_ids']
            for j, leaf in enumerate(frame['leaves']):
                assert leaf['leaf_id'] == frame['leaf_ids'][j]
                assert leaf['thermal_age'] == {'value': sample['state'][108+j], 'unit': 'degC_day'}
                assert leaf['area'] == {'value': sample['state'][108+n+j], 'unit': 'm2'}
            for key in ('integrated_transfers', 'balance_residuals', 'balance_budgets'):
                assert frame[key] == saved[key]
            assert len(frame['integrated_transfers']) == 21 and len(frame['sample']['state']) == 114
    assert producer.produce_growing_geometry_artifact(directory, ACCESS, inputs_raw=raw, **profiles) == root


def test_fractional_grid_preserves_exact_dt_times_index_not_rounded_elapsed(tmp_path, profiles):
    source = inputs(dt=1/3, count=3)
    root = producer.produce_growing_geometry_artifact(tmp_path/'a', ACCESS, inputs_raw=encoded(source), **profiles)
    assert producer.produce_growing_geometry_artifact(tmp_path/'b', ACCESS, inputs_raw=encoded(source), **profiles) == root
    frame = reader.read_growing_geometry_frame(tmp_path/'a', ACCESS, root, index=3)
    exact = Fraction.from_float(1/3)*3
    assert exact < 1 and frame['elapsed_seconds'] == 1.0
    assert frame['at']['elapsed_seconds_exact'] == {'numerator': str(exact.numerator), 'denominator': str(exact.denominator), 'unit': 's'}


@pytest.mark.parametrize('permission', ('ownership_asserted', 'access', 'store', 'use', 'transform', 'display'))
def test_denied_own_rights_reject_before_growth(tmp_path, profiles, permission, monkeypatch):
    source = inputs(count=1); source['rights'][permission] = False
    def forbidden(**kwargs): raise AssertionError('rights must precede growth')
    monkeypatch.setattr(continuation, 'prepare_context', forbidden)
    with pytest.raises(MorphologyArtifactHold):
        producer.produce_growing_geometry_artifact(tmp_path/'denied', ACCESS, inputs_raw=encoded(source), **profiles)


@pytest.fixture(scope='module')
def saved(tmp_path_factory, profiles):
    directory = tmp_path_factory.mktemp('growing-store')/'blobs'
    root = producer.produce_growing_geometry_artifact(directory, ACCESS, inputs_raw=encoded(inputs(count=3)), **profiles)
    return directory, root


def rewrite_root(directory, root, change):
    m = reader.read_growing_geometry_manifest(directory, ACCESS, root); change(m)
    with MorphologyBlobStore(directory, ACCESS, write=True) as store:
        return store.put(encoded(m), maximum=reader.MAX)


@pytest.mark.parametrize('change', [
    lambda m: m.update(extra=1), lambda m: m.update(G0_G4='approved'),
    lambda m: m.update(parameter_scope='measured_cultivar'), lambda m: m.update(status='failed'),
    lambda m: m['source_rights'].update(redistribute=True), lambda m: m.update(time_origin_utc='2026-10-02T00:00:00Z'),
    lambda m: m.update(input_id='different'), lambda m: m.update(context_sha256='0'*64),
    lambda m: m.update(initial_state_sha256='0'*64), lambda m: m.update(terminal_state_sha256='0'*64),
    lambda m: m['code_sha256'].pop(next(iter(m['code_sha256']))),
    lambda m: m['sources']['inputs'].update(bytes=True), lambda m: m['sources'].pop('license_notice'),
    lambda m: m['sources']['exchange_profile'].update(sha256='0'*64),
    lambda m: m['samples'].pop(), lambda m: m['samples'][1].update(index=True),
    lambda m: m['samples'][1].update(previous_checkpoint_sha256=None),
    lambda m: m['samples'][1]['elapsed_seconds_exact'].update(denominator='2'),
    lambda m: m['samples'][1].update(checkpoint_bytes=reader.CHECKPOINT_MAX+1),
    lambda m: m['samples'][1].update(sample_sha256='0'*64),
    lambda m: m['display_policy'].update(geometry_authority='derived_SLA')])
def test_rehashed_root_cannot_change_closed_scope_sources_time_chain(saved, change):
    directory, root = saved; changed = rewrite_root(directory, root, change)
    with pytest.raises(MorphologyArtifactHold): reader.read_growing_geometry_manifest(directory, ACCESS, changed)


@pytest.mark.parametrize('change', [
    lambda c: c.update(extra=1), lambda c: c.update(version='wrong'), lambda c: c.update(output_cursor=True),
    lambda c: c.update(context_sha256='0'*64), lambda c: c.update(output_prefix_sha256='0'*64),
    lambda c: c['integrated_transfers']['sensible'].update(unit='W/m2_floor'),
    lambda c: c['integrated_transfers']['vapor'].update(value=True),
    lambda c: c['balance_budgets']['vapor'].update(value=-1.0),
    lambda c: c['balance_residuals']['vapor'].update(value=1e20),
    lambda c: c['last_confirmed']['state'].pop(),
    lambda c: c['last_confirmed']['state'].__setitem__(111, 0.0),
    lambda c: c['last_confirmed']['state'].__setitem__(0, 1),
    lambda c: c['last_confirmed']['derived']['leaf_area_index'].update(unit='m2'),
    lambda c: c['last_confirmed'].update(elapsed_seconds=9.0),
    lambda c: c['last_confirmed']['curve_residuals'].pop()])
def test_rehashed_checkpoint_is_still_typed_bounded_and_bound_to_original(saved, change):
    directory, root = saved; m = reader.read_growing_geometry_manifest(directory, ACCESS, root)
    with MorphologyBlobStore(directory, ACCESS, write=True) as store:
        d = m['samples'][1]; cp = json.loads(store.get(d['checkpoint_sha256'], maximum=reader.CHECKPOINT_MAX)); change(cp)
        raw = encoded(cp); d['checkpoint_sha256'] = store.put(raw, maximum=reader.CHECKPOINT_MAX); d['checkpoint_bytes'] = len(raw)
        m['samples'][2]['previous_checkpoint_sha256'] = d['checkpoint_sha256']
        changed = store.put(encoded(m), maximum=reader.MAX)
    with pytest.raises(MorphologyArtifactHold): reader.read_growing_geometry_frame(directory, ACCESS, changed, index=1)


@pytest.mark.parametrize('change', [
    lambda p: p.update(extra=1), lambda p: p.update(origin='measured'), lambda p: p.update(input_id='other'),
    lambda p: p.update(time_origin_utc='2026-02-30T00:00:00Z'), lambda p: p.update(time_origin_utc='2026-10-01T00:00:00.1Z'),
    lambda p: p.update(step_seconds=0), lambda p: p.update(step_seconds=True),
    lambda p: p.update(step_count=True), lambda p: p.update(step_count=512), lambda p: p.update(step_count=4096),
    lambda p: p.update(step_seconds=601), lambda p: p['rights'].pop('redistribute'),
    lambda p: p['rights'].update(redistribute='yes'), lambda p: p['program']['leaves'][0]['initial_area'].update(unit='cm2'),
    lambda p: p['program']['leaves'][1].update(leaf_id=p['program']['leaves'][0]['leaf_id'])])
def test_invalid_wrapper_and_program_rejected_before_growth(tmp_path, profiles, change, monkeypatch):
    p = inputs(count=1); change(p)
    def forbidden(**kwargs): raise AssertionError('invalid wrapper must precede growth')
    monkeypatch.setattr(continuation, 'prepare_context', forbidden)
    with pytest.raises(MorphologyArtifactHold):
        producer.produce_growing_geometry_artifact(tmp_path/'bad', ACCESS, inputs_raw=encoded(p), **profiles)


@pytest.mark.parametrize('raw', [b'{}', b'\xff', b'{"x":NaN}', b'{"x":1e999}', b'{"x":1,"x":1}', b' '*(2*1024**2+1)])
def test_invalid_raw_bytes_rejected(tmp_path, profiles, raw):
    with pytest.raises(MorphologyArtifactHold):
        producer.produce_growing_geometry_artifact(tmp_path/'bad', ACCESS, inputs_raw=raw, **profiles)


@pytest.mark.parametrize('index', [-1, 4, True, None, '0', 1.5])
def test_invalid_frame_index(saved, index):
    with pytest.raises(MorphologyArtifactHold): reader.read_growing_geometry_frame(*saved[:1], ACCESS, saved[1], index=index)


def test_query_uses_only_stored_states_and_detached_copies(saved, monkeypatch):
    directory, root = saved
    def forbidden(*args, **kwargs): raise AssertionError('query must not compute or write')
    for name in ('prepare_context', 'start', 'advance_chunk', 'restore_checkpoint', '_context'):
        monkeypatch.setattr(continuation, name, forbidden)
    monkeypatch.setattr(MorphologyBlobStore, 'put', forbidden)
    old = reader.read_growing_geometry_frame(directory, ACCESS, root, index=3)
    changed = deepcopy(old); changed['leaves'][0]['area']['value'] = 0; changed['source_rights']['display'] = False
    assert reader.read_growing_geometry_frame(directory, ACCESS, root, index=3) == old
    m = reader.read_growing_geometry_manifest(directory, ACCESS, root); m['samples'].clear()
    assert len(reader.read_growing_geometry_manifest(directory, ACCESS, root)['samples']) == 4


def test_current_and_late_file_policy_are_rechecked(saved, monkeypatch):
    directory, root = saved; m = reader.read_growing_geometry_manifest(directory, ACCESS, root)
    digest = m['sources']['inputs']['sha256']; path = directory/digest
    before = len(os.listdir('/proc/self/fd')); path.chmod(0o600)
    try:
        with pytest.raises(MorphologyArtifactHold): reader.read_growing_geometry_frame(directory, ACCESS, root, index=0)
    finally: path.chmod(0o640)
    original = MorphologyBlobStore.get; calls = []
    def late(self, key, **kwargs):
        raw = original(self, key, **kwargs)
        if key == digest:
            calls.append(key)
            if len(calls) == 1: path.chmod(0o600)
        return raw
    monkeypatch.setattr(MorphologyBlobStore, 'get', late)
    try:
        with pytest.raises(MorphologyArtifactHold): reader.read_growing_geometry_frame(directory, ACCESS, root, index=0)
        assert len(calls) == 1
    finally: path.chmod(0o640)
    assert len(os.listdir('/proc/self/fd')) == before


def test_late_code_change_and_partial_write_return_no_completed_root(tmp_path, profiles, monkeypatch):
    original = MorphologyBlobStore.put; roots = []
    def fail(self, raw, **kwargs):
        parsed = json.loads(raw) if raw.startswith(b'{') else {}
        if parsed.get('schema_version') == 'growing-geometry-research-artifact-v1': roots.append(raw)
        if parsed.get('version') == 'growing-geometry-companion-checkpoint-v1' and parsed['step_index'] == 1:
            raise OSError('injected partial writer failure')
        return original(self, raw, **kwargs)
    monkeypatch.setattr(MorphologyBlobStore, 'put', fail)
    with pytest.raises(MorphologyArtifactHold):
        producer.produce_growing_geometry_artifact(tmp_path/'partial', ACCESS, inputs_raw=encoded(inputs(count=2)), **profiles)
    assert roots == []
    monkeypatch.setattr(MorphologyBlobStore, 'put', original)
    pins = reader._pins; calls = []
    def changed():
        calls.append(1); value = pins()
        if len(calls) >= 6: value[next(iter(value))] = '0'*64
        return value
    monkeypatch.setattr(reader, '_pins', changed)
    with pytest.raises(MorphologyArtifactHold):
        producer.produce_growing_geometry_artifact(tmp_path/'late-code', ACCESS, inputs_raw=encoded(inputs(count=2)), **profiles)
    assert len(calls) >= 6


def test_domain_hold_never_publishes_completion(tmp_path, profiles):
    p = inputs(dt=8, count=4); p['program']['scenario']['forcing']['canopy_external_heat']['value'] = 1e7
    with pytest.raises(MorphologyArtifactHold, match='CALCULATION_HOLD'):
        producer.produce_growing_geometry_artifact(tmp_path/'hold', ACCESS, inputs_raw=encoded(p), **profiles)
    for file in (tmp_path/'hold').iterdir():
        if file.read_bytes().startswith(b'{'):
            assert json.loads(file.read_bytes()).get('schema_version') != 'growing-geometry-research-artifact-v1'


@pytest.mark.parametrize('source,change', [
    ('inputs', lambda p: p['rights'].update(display=False)),
    ('request', lambda p: p['leaves'][0]['initial_area'].update(unit='cm2')),
    ('program', lambda p: p['leaves'][0]['thermal_age'].update(value=1.0)),
    ('seed', lambda p: p['initial_area_receipts'][0].update(leaf_id='other')),
    ('context', lambda p: p['identity'].update(engine_version='other')),
    ('context', lambda p: p['state_layout']['units']['leaf_blocks'].update(area='cm2'))])
def test_changed_source_even_with_new_blob_and_root_digest_is_rejected(saved, source, change):
    directory, root = saved; m = reader.read_growing_geometry_manifest(directory, ACCESS, root)
    with MorphologyBlobStore(directory, ACCESS, write=True) as store:
        value = json.loads(store.get(m['sources'][source]['sha256'], maximum=reader.MAX)); change(value); raw = encoded(value)
        m['sources'][source] = {'sha256': store.put(raw, maximum=reader.MAX), 'bytes': len(raw)}
        changed = store.put(encoded(m), maximum=reader.MAX)
    with pytest.raises(MorphologyArtifactHold): reader.read_growing_geometry_manifest(directory, ACCESS, changed)


def test_current_source_raw_corruption_is_not_returned(saved):
    directory, root = saved; m = reader.read_growing_geometry_manifest(directory, ACCESS, root)
    file = directory/m['sources']['growth_profile']['sha256']; raw = file.read_bytes()
    try:
        file.write_bytes(raw+b' ')
        with pytest.raises(MorphologyArtifactHold): reader.read_growing_geometry_manifest(directory, ACCESS, root)
    finally: file.write_bytes(raw)


def test_requested_area_receipt_is_preserved_but_current_area_uses_original_canonical_value(tmp_path, profiles):
    p = inputs(count=1); leaf = p['program']['leaves'][0]
    leaf['initial_area']['value'] *= 1+5e-13
    requested = deepcopy(leaf['initial_area'])
    root = producer.produce_growing_geometry_artifact(tmp_path/'a', ACCESS, inputs_raw=encoded(p), **profiles)
    frame = reader.read_growing_geometry_frame(tmp_path/'a', ACCESS, root, index=0)
    assert frame['leaves'][0]['initial_area_receipt']['requested_area'] == requested
    assert frame['leaves'][0]['area']['value'] != requested['value']
    assert frame['leaves'][0]['area'] == frame['leaves'][0]['initial_area_receipt']['canonical_area']


def test_maximum_leaf_count_preserves_order_and_vector_bounds(tmp_path, profiles):
    p = inputs(count=1); leaf = p['program']['leaves'][0]
    p['program']['leaves'] = [{**deepcopy(leaf), 'leaf_id': f'stored-leaf-{i}'} for i in range(512)]
    p['program']['model_floor_area']['value'] = 512*.25/1.33
    root = producer.produce_growing_geometry_artifact(tmp_path/'a', ACCESS, inputs_raw=encoded(p), **profiles)
    frame = reader.read_growing_geometry_frame(tmp_path/'a', ACCESS, root, index=1)
    assert frame['leaf_ids'] == [f'stored-leaf-{i}' for i in range(512)]
    assert len(frame['sample']['state']) == 1132 and len(frame['leaves']) == 512
