"""Native page provenance must survive through both stored result hashes."""
from hashlib import sha256
from contextlib import contextmanager
import builtins
import importlib.util
import json
from pathlib import Path
import sys

import pytest
from app import crop_greenhouse_solar_storage as storage
import test_solar_json_load_adapter as previous


def candidate():
    name = 'app._research_solar_json_source_assembly'
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, Path(__file__).resolve().parents[2]/'research/solar-json-source-assembly.py')
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        try:
            spec.loader.exec_module(module)
        except BaseException:
            del sys.modules[name]
            raise
    return sys.modules[name]


profiles = previous.profiles
saved_archive = previous.saved_archive
archive = previous.archive


def test_native_pages_reach_source_and_bound_hash_without_reencoding_for_ownership(archive):
    model = candidate()
    head, expected, seen, size = previous.original_result(archive)
    audit = {}
    with storage._Files(archive) as reader:
        actual = storage._canonical(model.load(reader, head, audit=audit))
        assert actual == expected
        assert reader._seen == seen and reader._referenced_bytes == size
    assert audit['source_pairs'] == head['commit_count'] > 0
    assert audit['cache_hits'] == head['commit_count']
    assert audit['extra_source_encodes_for_ownership'] == 0
    assert audit['disposed'] and audit['raw_bytes_after_close'] == 0
    assert audit['peak_raw_bytes'] <= 1024**2


@pytest.mark.parametrize('field,value', [('version','wrong'),('header_sha256','0'*64),('sequence',True),('sequence',-1),('parent_commit_sha256',None),('parent_commit_sha256',1),('unknown',0),('source_meta',None)])
def test_source_pipeline_preserves_original_commit_errors(archive, monkeypatch, field, value):
    model = candidate()
    with monkeypatch.context() as changed:
        changed.setattr(previous, 'candidate', lambda: model)
        previous.test_real_commit_chain_errors_match_original(archive, field, value)


@pytest.mark.parametrize('change', ['file_bytes','decoder','decoder_body','blob_method','records_method','hash_binding','canonical_binding','load_body'])
def test_source_pipeline_preserves_late_loader_errors(archive, monkeypatch, change):
    model = candidate()
    with monkeypatch.context() as changed:
        changed.setattr(previous, 'candidate', lambda: model)
        previous.test_late_changes_after_chain_validation_preserve_original(archive, monkeypatch, change)


@pytest.mark.parametrize('failure', ['first-event','last-event','interval'])
def test_source_pipeline_preserves_physical_hold(profiles, tmp_path, monkeypatch, failure):
    model = candidate()
    with monkeypatch.context() as changed:
        changed.setattr(previous, 'candidate', lambda: model)
        previous.test_original_physical_hold_preserves_all_confirmed_rows_and_failed_utc(profiles, tmp_path, monkeypatch, failure)


@pytest.mark.parametrize('phase', ['initial', 'late'])
@pytest.mark.parametrize('change', ['point', 'point_body', 'point_alias', 'records_alias', 'dict_alias', 'set_alias'])
def test_foreign_validation_callbacks_cannot_receive_a_reusable_owned_pair(archive, monkeypatch, phase, change):
    model = candidate()
    head, expected, _, _ = previous.original_result(archive)
    results = []
    audits = []
    saved = []
    for selected in ('original', 'candidate'):
        audit = {}
        with monkeypatch.context() as patch:
            original_point = storage.clock._point
            original_records = storage._Files._records
            def point(*args):
                saved.append(args[1])
                return original_point(*args)
            def rejected(*args, **kwargs):
                raise RuntimeError('changed native point body')
            def records(reader, *args):
                values = original_records(reader, *args)
                saved.append(values)
                return values
            def dictionary(*args, **kwargs):
                saved.extend(args)
                return builtins.dict(*args, **kwargs)
            def kind(value):
                return dictionary if builtins.type(value) is builtins.dict else builtins.type(value)
            def aset(*args, **kwargs):
                saved.extend(args)
                return builtins.set(*args, **kwargs)
            def change_now():
                if change == 'point':patch.setattr(storage.clock, '_point', point)
                elif change == 'point_body':patch.setattr(storage.clock.clock_helpers._point, '__code__', rejected.__code__)
                elif change == 'point_alias':patch.setattr(storage.clock.clock_helpers, '_at', rejected)
                elif change == 'records_alias':patch.setattr(storage._Files, '_records', records)
                elif change == 'dict_alias':
                    patch.setattr(storage, 'dict', dictionary, raising=False)
                    patch.setattr(storage, 'type', kind, raising=False)
                else:patch.setattr(storage, 'set', aset, raising=False)
            with storage._Files(archive) as reader:
                call = (lambda: reader._load(head)) if selected == 'original' else (lambda: model.load(reader, head, audit=audit))
                if phase == 'initial':
                    change_now()
                    results.append(previous.outcome(call))
                else:
                    with previous.at_chain_root(change_now) as fired:
                        results.append(previous.outcome(call))
                    assert fired == [True]
        audits.append(audit)
    assert results[0] == results[1]
    if change in ('point_body', 'point_alias'):
        assert results[0][0] == 'error'
    else:
        assert results[0] == ('value', expected)
        assert saved
    assert audits[1]['source_pairs'] == 0
    assert audits[1]['disposed'] and audits[1]['raw_bytes_after_close'] == 0


def test_source_hash_rejection_occurs_before_any_bound_payload_hash(archive, monkeypatch):
    model = candidate()
    head, _, _, _ = previous.original_result(archive)
    tip_path = archive/(head['latest_commit_sha256']+'.json')
    commit = json.loads(tip_path.read_bytes())
    commit['source_chunk_sha256'] = '0'*64
    raw = storage._canonical(commit)
    digest = sha256(raw).hexdigest()
    (archive/(digest+'.json')).write_bytes(raw)
    head['latest_commit_sha256'] = digest
    results = []
    for selected in ('original','candidate'):
        with monkeypatch.context() as patch:
            payload_calls = []
            original = model.AssemblyScope._payload_hash
            def payload(scope, value):
                payload_calls.append(True)
                return original(scope, value)
            patch.setattr(model.AssemblyScope, '_payload_hash', payload)
            with storage._Files(archive) as reader:
                call = (lambda: reader._load(head)) if selected == 'original' else (lambda: model.load(reader, head))
                results.append(previous.outcome(call))
            # Earlier valid commits have payload hashes; the bad tip does not.
            if selected == 'candidate':assert len(payload_calls) == head['commit_count']-1
    assert results[0] == results[1] and results[0][0] == 'error'


def test_small_extra_raw_budget_preserves_original_result_through_hash_fallback(archive, monkeypatch):
    model = candidate()
    head, expected, _, _ = previous.original_result(archive)
    constructor = model.AssemblyScope.__init__
    def small(scope):
        constructor(scope)
        scope.max_raw_bytes = 1024
    audit = {}
    with monkeypatch.context() as patch:
        patch.setattr(model.AssemblyScope, '__init__', small)
        with storage._Files(archive) as reader:
            assert storage._canonical(model.load(reader, head, audit=audit)) == expected
    assert audit['source_pairs'] == 0 and audit['fallback_pairs'] == head['commit_count']
    assert audit['peak_raw_bytes'] <= 1024
    assert audit['disposed'] and audit['raw_bytes_after_close'] == 0


def test_source_loader_can_be_installed_without_losing_opaque_pair_path(archive, monkeypatch):
    model = candidate()
    with monkeypatch.context() as patch:
        patch.setattr(previous, 'candidate', lambda: model)
        previous.test_installed_reader_method_preserves_native_dispatch(archive, monkeypatch)


@pytest.mark.parametrize('slot', ['_load','_load_header','_records','_need','records_body','pristine_wrong_slot'])
def test_source_loader_keeps_initial_actual_method_fallback(archive, monkeypatch, slot):
    model = candidate()
    with monkeypatch.context() as patch:
        patch.setattr(previous, 'candidate', lambda: model)
        previous.test_initial_foreign_method_uses_actual_original_path(archive, monkeypatch, slot)


def test_point_callback_restoring_itself_does_not_reapprove_escaped_first_source(archive, monkeypatch):
    model = candidate()
    head, expected, _, _ = previous.original_result(archive)
    audit = {}
    saved = []
    native = storage.clock._point
    with monkeypatch.context() as patch:
        def transient(*args):
            saved.append(args[1])
            patch.setattr(storage.clock, '_point', native)
            return native(*args)
        patch.setattr(storage.clock, '_point', transient)
        with storage._Files(archive) as reader:
            assert storage._canonical(model.load(reader, head, audit=audit)) == expected
    assert len(saved) == 1
    assert audit['source_pairs'] < head['commit_count']
    assert audit['fallback_pairs'] >= 1
    assert audit['disposed'] and audit['raw_bytes_after_close'] == 0


@contextmanager
def before_first_source_hash_check(action):
    monitoring = sys.monitoring
    slot = next(i for i in range(5, -1, -1) if monitoring.get_tool(i) is None)
    code = storage._need.__code__
    fired = []
    def entered(called, offset):
        frame = sys._getframe(1)
        if not fired and frame.f_locals['reason'] == 'HASH_HOLD: exact original chunk':
            fired.append(True)
            action()
    monitoring.use_tool_id(slot, 'source-before-bound-codec-change')
    monitoring.register_callback(slot, monitoring.events.PY_START, entered)
    monitoring.set_local_events(slot, code, monitoring.events.PY_START)
    try:
        yield fired
    finally:
        monitoring.set_local_events(slot, code, 0)
        monitoring.register_callback(slot, monitoring.events.PY_START, None)
        monitoring.free_tool_id(slot)


def test_codec_changed_between_hashes_uses_actual_mutating_payload_encoder(archive, monkeypatch):
    model = candidate()
    head, _, _, _ = previous.original_result(archive)
    outcomes = []
    for selected in ('original','candidate'):
        audit = {}
        payloads = []
        native = json.dumps
        with monkeypatch.context() as patch:
            def encoder(value, *args, **kwargs):
                if builtins.type(value) is builtins.dict and 'source' in value:
                    payloads.append(True)
                    value['source']['steps'] += 1
                return native(value, *args, **kwargs)
            def change():
                patch.setattr(json, 'dumps', encoder)
            with storage._Files(archive) as reader, before_first_source_hash_check(change) as fired:
                call = (lambda: reader._load(head)) if selected == 'original' else (lambda: model.load(reader, head, audit=audit))
                outcomes.append(previous.outcome(call))
                assert fired == [True] and payloads == [True]
            if selected == 'candidate':
                assert audit['source_pairs'] == 0 and audit['fallback_pairs'] == 1
                assert audit['disposed'] and audit['raw_bytes_after_close'] == 0
    assert outcomes[0] == outcomes[1] and outcomes[0][0] == 'error'
