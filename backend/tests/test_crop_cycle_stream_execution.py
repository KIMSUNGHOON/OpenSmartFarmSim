from copy import deepcopy
from dataclasses import replace
from datetime import timedelta
import json
import importlib.util
from pathlib import Path

import pytest

from app import crop_cycle_input_stream as inputs
from app import crop_cycle_stream_execution as engine
from app import crop_plant_startup_integration as original
from app.crop_growth_rates import ReferenceParameters
from app.crop_fruit_cohorts import ReferenceFruitCohortParameters
from app.crop_fruit_transport import ReferenceFruitTransportParameters

ROOT = Path(__file__).resolve().parents[2]
CASES = json.loads((ROOT / 'fixtures/crop-plant-startup-integration-reference-v1.json').read_bytes())['cases']
PROFILES = {
    'growth_profile': ReferenceParameters((ROOT / 'fixtures/crop-growth-reference-parameters-v1.json').read_bytes()),
    'cohort_profile': ReferenceFruitCohortParameters((ROOT / 'fixtures/crop-fruit-cohort-reference-parameters-v1.json').read_bytes()),
    'transport_profile': ReferenceFruitTransportParameters((ROOT / 'fixtures/crop-fruit-transport-reference-parameters-v1.json').read_bytes()),
}


def program(name='empty-entry'):
    return deepcopy(next(c['program'] for c in CASES if c['case_id'] == name))


def packet(path, p, outputs=None):
    p = deepcopy(p)
    anchors = p.pop('output_times')
    receipt = inputs.write_input_packet(path, **p, anchors=anchors,
        outputs=anchors if outputs is None else outputs, **PROFILES, program_id='own-synthetic-test')
    return inputs.open_input_packet(path, receipt['root_sha256'], **PROFILES)


def finish(ctx, quota=7, transitions=13, checkpoint=None):
    cp = checkpoint or engine.start(ctx)
    samples, events, chunks = [], [], []
    while True:
        result = engine.advance_chunk(ctx, cp, {'max_steps': quota, 'max_transitions': transitions})
        assert result['output_start'] == len(samples)
        assert result['event_start'] == len(events)
        samples.extend(result['samples']); events.extend(result['events']); chunks.append(result)
        if result['status'] != 'yielded':
            return {**result, 'samples': samples, 'events': events}, chunks
        cp = engine.restore_checkpoint(ctx, engine.checkpoint_bytes(ctx, result['checkpoint']))


def test_initial_checkpoint_pins_original_seed_clock_grid_and_closed_manifest(tmp_path):
    with packet(tmp_path/'packet', program()) as reader:
        ctx = engine.prepare_context(reader, **PROFILES); cp = engine.start(ctx)
        assert cp['phase'] == 'initial-ready' and cp['y'] == cp['seed']
        assert len(cp['y']) == 121 and all(type(v) is float for v in cp['y'])
        assert cp['boundary_cursor'] == cp['steps'] == cp['sequence'] == 0
        assert engine.restore_checkpoint(ctx, engine.checkpoint_bytes(ctx, cp)) == cp
        assert ctx.planned_steps == reader.plan['planned_steps'] == 120
        assert ctx.boundary_count == reader.plan['boundaries'] == 3
        assert ctx.manifest['input_root_sha256'] == reader.root_sha256
        assert ctx.manifest['physical_code_sha256'] == original.CODE_HASHES
        altered = ctx.manifest; altered['solver']['max_steps'] = 1
        assert ctx.manifest['solver']['max_steps'] == 10000


@pytest.fixture(scope='module')
def originals():
    return {c['case_id']:original.integrate_plant_startup(**c['program'], **PROFILES) for c in CASES}


@pytest.mark.parametrize('quota,transitions', [(1,1),(7,13),(10000,10000)])
@pytest.mark.parametrize('case', CASES, ids=lambda c:c['case_id'])
def test_actual_rhs_matches_whole_original_physical_payload(tmp_path, case, quota, transitions, originals):
    p = case['program']; before = deepcopy(p)
    with packet(tmp_path/'packet', p) as reader:
        ctx = engine.prepare_context(reader, **PROFILES)
        actual, chunks = finish(ctx, quota, transitions)
        expected = originals[case['case_id']]
        for field in ('status','scope','samples','events','steps','planned_steps'):
            assert actual[field] == expected[field]
        assert actual['checkpoint']['event_count'] == len(expected['events'])
        assert actual['checkpoint']['boundary_cursor'] == ctx.boundary_count
        assert actual['checkpoint']['sequence'] == expected['steps'] + ctx.boundary_count
        for a,b in zip(chunks,chunks[1:]):
            assert b['checkpoint']['parent_sha256'] == a['checkpoint']['checkpoint_sha256']
        with pytest.raises(engine.CycleStreamExecutionRejected, match='completed'):
            engine.advance_chunk(ctx, actual['checkpoint'], {'max_steps':1,'max_transitions':1})
    assert p == before


def test_pending_forcing_event_output_boundary_commits_once_after_restore(tmp_path):
    p = program('full-removal-reentry')
    with packet(tmp_path/'packet', p) as reader:
        ctx = engine.prepare_context(reader, **PROFILES); cp = engine.start(ctx)
        while cp['at'] != p['events'][1]['at']:
            result = engine.advance_chunk(ctx,cp,{'max_steps':1,'max_transitions':1})
            cp = engine.restore_checkpoint(ctx,engine.checkpoint_bytes(ctx,result['checkpoint']))
        assert cp['phase'] == 'step-end' and cp['active_segment'] == 0
        assert cp['event_count'] == cp['output_cursor'] == 1
        applied = engine.advance_chunk(ctx,cp,{'max_steps':1,'max_transitions':1})
        assert applied['checkpoint']['active_segment'] == 1
        assert applied['checkpoint']['phase'] == 'boundary-committed'
        assert len(applied['samples']) == len(applied['events']) == 1
        assert applied['samples'][0]['state'] == applied['events'][0]['after']
        following = engine.advance_chunk(ctx,applied['checkpoint'],{'max_steps':1,'max_transitions':1})
        assert following['samples'] == following['events'] == []


@pytest.mark.parametrize('kind',['entry','pre-onset','carbon-without-number','underflow','t0-event','event','fractional'])
def test_actual_hold_matches_original_with_confirmed_past_only(tmp_path,kind):
    p = program('full-removal-reentry' if kind in ('t0-event','event') else
                'night-smooth' if kind == 'fractional' else 'empty-entry')
    initial = p['initial_state']['values']
    if kind == 'entry':p['segments'][0]['fruit_entry']['values']['fruit_number_inflow']['value'] = 100
    if kind == 'pre-onset':initial['temperature_sum']['value'] = 0
    if kind == 'carbon-without-number':initial['fruit_carbohydrate'][0]['value'] = 1
    if kind == 'underflow':initial['stem_root']['value'] = 5e-324
    if kind in ('t0-event','event'):p['events'][0 if kind == 't0-event' else 1]['removals']['values']['leaf']['value'] = 1e6
    if kind == 'fractional':
        initial['buffer']['value'] = 1
        p['output_times'] = [p['output_times'][0],p['output_times'][-1]]
        p['solver']['max_step_seconds'] = 3599
    expected = original.integrate_plant_startup(**p, **PROFILES)
    with packet(tmp_path/'packet',p) as reader:
        actual,_ = finish(engine.prepare_context(reader,**PROFILES),1,1)
        for field in ('status','hold','samples','events','steps','planned_steps','last_confirmed'):
            assert actual[field] == expected[field]
        assert actual['checkpoint'] is None


def test_output_selection_retains_same_grid_and_physical_final_state(tmp_path):
    p = program('positive-tail'); results = []
    for i,outputs in enumerate((None,[p['output_times'][0],p['output_times'][-1]])):
        with packet(tmp_path/str(i),p,outputs) as reader:
            ctx = engine.prepare_context(reader,**PROFILES)
            result,_ = finish(ctx); results.append((ctx,result))
    a,b = results
    assert a[0].manifest['calculation_sha256'] == b[0].manifest['calculation_sha256']
    assert a[0].root_sha256 != b[0].root_sha256
    assert a[1]['checkpoint']['y'] == b[1]['checkpoint']['y']
    assert a[1]['steps'] == b[1]['steps']
    assert a[1]['events'] == b[1]['events']
    assert b[1]['samples'] == [a[1]['samples'][0],a[1]['samples'][-1]]


def test_multiple_grid_pages_keep_global_steps_seed_and_original_boundaries(tmp_path):
    p = program(); start = original._utc(p['segments'][0]['start'])
    end = start + timedelta(seconds=260)
    p['segments'] = [deepcopy(p['segments'][0])]
    p['segments'][0]['end'] = original._stamp(end)
    p['output_times'] = [original._stamp(start+timedelta(seconds=i)) for i in range(261)]
    with packet(tmp_path/'packet',p) as reader:
        ctx = engine.prepare_context(reader,**PROFILES)
        actual,_ = finish(ctx,17,31)
        expected = original.integrate_plant_startup(**p,**PROFILES)
        assert len(ctx.index) == 3
        assert len(ctx._cache['grid'][1]) <= 128
        assert actual['samples'] == expected['samples']
        assert actual['steps'] == 260 and actual['checkpoint']['sequence'] == 521
        assert actual['checkpoint']['seed'] == engine.start(ctx)['seed']


@pytest.mark.parametrize('key,bad',[
    ('version','other'),('root_sha256','0'*64),('calculated_state_id','other'),
    ('steps',True),('steps',999),('event_count',1),('event_cursor',1),
    ('output_cursor',0),('active_segment',1),('boundary_cursor',0),
    ('boundary_cursor',999),('sequence',999),('phase','trial'),('phase',[]),
    ('parent_sha256',None),('output_prefix_sha256',None),('event_prefix_sha256','f'*64),
    ('at','2026-01-01T00:00:07Z'),('at',None),
])
def test_rehashed_checkpoint_global_identity_and_position_tampering_is_rejected(tmp_path,key,bad):
    p = program(); p['solver']['max_step_seconds'] = 5
    with packet(tmp_path/'packet',p) as reader:
        ctx = engine.prepare_context(reader,**PROFILES)
        cp = engine.advance_chunk(ctx,engine.start(ctx),{'max_steps':1,'max_transitions':2})['checkpoint']
        changed = deepcopy(cp); changed[key] = bad; engine._seal(changed)
        with pytest.raises(engine.CycleStreamExecutionRejected):
            engine.restore_checkpoint(ctx,engine._canonical(changed))


@pytest.mark.parametrize('kind',['seed','clock','temperature','ledger','float-type','negative','nonfinite','short','extra','unhashed'])
def test_checkpoint_vector_clock_and_schema_tampering_is_rejected(tmp_path,kind):
    with packet(tmp_path/'packet',program()) as reader:
        ctx = engine.prepare_context(reader,**PROFILES)
        cp = engine.advance_chunk(ctx,engine.start(ctx),{'max_steps':1,'max_transitions':2})['checkpoint']
        changed = deepcopy(cp)
        if kind == 'seed':changed['seed'][0] += 1
        if kind == 'clock':changed['clock']['prefix']['numerator'] = '1'
        if kind == 'temperature':changed['y'][4] += 1
        if kind == 'ledger':changed['y'][0] += 100
        if kind == 'float-type':changed['y'][0] = 1
        if kind == 'negative':changed['y'][0] = -1.0
        if kind == 'nonfinite':changed['y'][0] = float('inf')
        if kind == 'short':changed['y'].pop()
        if kind == 'extra':changed['extra'] = 1
        if kind == 'unhashed':changed['steps'] += 1
        if kind not in ('nonfinite','unhashed'):engine._seal(changed)
        with pytest.raises(engine.CycleStreamExecutionRejected):
            engine.checkpoint_bytes(ctx,changed)


@pytest.mark.parametrize('raw',[b'{}',b'{"x":1,"x":2}',b'{"x":NaN}',b'\xff',
    '{"x":1}'.encode('utf-16'),b' '*65537,'{}',b'[]'])
def test_checkpoint_utf8_closed_json_and_size_rejection(tmp_path,raw):
    with packet(tmp_path/'packet',program()) as reader:
        with pytest.raises(engine.CycleStreamExecutionRejected):
            engine.restore_checkpoint(engine.prepare_context(reader,**PROFILES),raw)


@pytest.mark.parametrize('budget',[{},None,{'max_steps':True,'max_transitions':1},
    {'max_steps':0,'max_transitions':1},{'max_steps':10001,'max_transitions':1},
    {'max_steps':1,'max_transitions':0},{'max_steps':1,'max_transitions':1.0},
    {'max_steps':1,'max_transitions':1,'extra':1}])
def test_invalid_chunk_budget_never_starts_rhs(tmp_path,budget,monkeypatch):
    with packet(tmp_path/'packet',program()) as reader:
        ctx = engine.prepare_context(reader,**PROFILES); cp = engine.start(ctx)
        def unexpected(*args):raise AssertionError('RHS must not start')
        monkeypatch.setattr(engine.short._Evaluator,'rhs',unexpected)
        with pytest.raises(engine.CycleStreamExecutionRejected,match='RESOURCE_HOLD'):
            engine.advance_chunk(ctx,cp,budget)


@pytest.mark.parametrize('pin',['new-code','continuation-code','physical-code','policy','python','profile','input-root','input-calculation'])
def test_changed_execution_pins_reject_before_any_rhs(tmp_path,pin,monkeypatch):
    with packet(tmp_path/'packet',program()) as reader:
        ctx = engine.prepare_context(reader,**PROFILES); cp = engine.start(ctx)
        if pin == 'new-code':monkeypatch.setattr(engine,'CODE_SHA256','0'*64)
        if pin == 'continuation-code':monkeypatch.setattr(engine.short,'CODE_SHA256','0'*64)
        if pin == 'physical-code':monkeypatch.setattr(original,'CODE_HASHES',{})
        if pin == 'policy':monkeypatch.setattr(original.startup,'POLICY_SHA256','0'*64)
        if pin == 'python':monkeypatch.setattr(engine.platform,'python_version',lambda:'0.0.0')
        if pin == 'profile':
            manifest = ctx.manifest; manifest['profile_sha256']['growth_profile'] = '0'*64
            ctx = replace(ctx,_manifest=engine._canonical(manifest),root_sha256=engine._hash(manifest))
        if pin == 'input-root':reader.root_sha256 = '0'*64
        if pin == 'input-calculation':reader.calculation_sha256 = '0'*64
        def unexpected(*args):raise AssertionError('RHS must not start')
        monkeypatch.setattr(engine.short._Evaluator,'rhs',unexpected)
        with pytest.raises(engine.CycleStreamExecutionRejected,match='CONTEXT_HOLD'):
            engine.advance_chunk(ctx,cp,{'max_steps':1,'max_transitions':1})


def test_wrong_profiles_reader_and_closed_reader_are_typed_rejections(tmp_path):
    with pytest.raises(engine.CycleStreamExecutionRejected):engine.prepare_context({},**PROFILES)
    with packet(tmp_path/'packet',program()) as reader:
        for key in PROFILES:
            changed = {**PROFILES,key:{}}
            with pytest.raises(engine.CycleStreamExecutionRejected,match='PROFILE_HOLD'):
                engine.prepare_context(reader,**changed)
        ctx = engine.prepare_context(reader,**PROFILES); cp = engine.start(ctx)
        with pytest.raises(engine.CycleStreamExecutionRejected):engine.start({})
    with pytest.raises(engine.CycleStreamExecutionRejected,match='closed'):
        engine.advance_chunk(ctx,cp,{'max_steps':1,'max_transitions':1})


@pytest.mark.parametrize('exc',[KeyboardInterrupt,RuntimeError])
def test_cancel_or_external_exception_is_not_a_numeric_hold(tmp_path,monkeypatch,exc):
    with packet(tmp_path/'packet',program()) as reader:
        ctx = engine.prepare_context(reader,**PROFILES); cp = engine.start(ctx)
        def interrupted(*args):raise exc('external stop')
        monkeypatch.setattr(engine.short._Evaluator,'rhs',interrupted)
        with pytest.raises(exc):engine.advance_chunk(ctx,cp,{'max_steps':1,'max_transitions':1})
        assert cp == engine.start(ctx)


def test_odd_step_and_boundary_remainders_use_original_trial_times(tmp_path,monkeypatch):
    p = program('positive-tail'); p['solver']['max_step_seconds'] = 7
    with packet(tmp_path/'packet',p) as reader:
        ctx = engine.prepare_context(reader,**PROFILES); times = []
        rhs = engine.short._Evaluator.rhs
        def observed(self,vector,time,active,phase):
            if phase.startswith('rk4-'):times.append((phase,time))
            return rhs(self,vector,time,active,phase)
        monkeypatch.setattr(engine.short._Evaluator,'rhs',observed)
        actual,_ = finish(ctx,2,3)
        boundaries = sorted({original._utc(t) for t in p['output_times']}
                            | {original._utc(s['end']) for s in p['segments']}
                            | {original._utc(e['at']) for e in p['events']})
        expected = []
        for a,b in zip(boundaries,boundaries[1:]):
            at = a
            while at < b:
                h = min(7,int((b-at).total_seconds()))
                for phase,t in zip(('rk4-k1','rk4-k2','rk4-k3','rk4-k4'),
                                  (at,at+timedelta(seconds=h/2),at+timedelta(seconds=h/2),at+timedelta(seconds=h)),strict=True):
                    expected.append((phase,t))
                at += timedelta(seconds=h)
        assert times == expected and actual['steps'] == len(expected)//4


def test_changed_unread_block_propagates_input_hash_rejection(tmp_path):
    p = program(); first = deepcopy(p['segments'][0]); start = original._utc(first['start'])
    p['segments'] = []
    for i in range(129):
        row = deepcopy(first)
        row['start'] = original._stamp(start+timedelta(seconds=i))
        row['end'] = original._stamp(start+timedelta(seconds=i+1))
        p['segments'].append(row)
    p['output_times'] = [p['segments'][0]['start'],p['segments'][-1]['end']]
    with packet(tmp_path/'packet',p) as reader:
        ctx = engine.prepare_context(reader,**PROFILES); cp = engine.start(ctx)
        block = reader.manifest['streams']['segments']['blocks'][1]
        (tmp_path/'packet'/(block['sha256']+'.json')).write_bytes(b'[]')
        with pytest.raises(inputs.CycleInputRejected,match='HASH_HOLD'):
            finish(ctx,10000,10000,cp)


def test_independent_long_reference_control_flow_preserves_normalized_event_json_and_prefixes(tmp_path):
    path = ROOT/'research/crop-cycle-stream-execution-reference.py'
    spec = importlib.util.spec_from_file_location('cycle_stream_reference',path)
    reference = importlib.util.module_from_spec(spec);spec.loader.exec_module(reference)
    p = program('full-removal-reentry'); before = deepcopy(p)
    expected,final = reference.independent_control_flow(p,PROFILES)
    legacy = original.integrate_plant_startup(**p,**PROFILES)
    with packet(tmp_path/'packet',p) as reader:
        actual,_ = finish(engine.prepare_context(reader,**PROFILES),7,13)
        for field in ('status','scope','samples','events','steps','planned_steps'):
            assert engine._canonical(actual[field]) == engine._canonical(expected[field]) == engine._canonical(legacy[field])
        for field in final:
            assert engine._canonical(actual['checkpoint'][field]) == engine._canonical(final[field])
    assert p == before
