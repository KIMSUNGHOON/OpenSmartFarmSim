"""Contract tests for an unwired, per-read JSON ownership primitive."""
from contextlib import contextmanager
from dataclasses import FrozenInstanceError
from hashlib import sha256
import asyncio
import importlib.util
import json
from pathlib import Path
import sys
from threading import Thread
import types

import pytest

from app import crop_cycle_artifact as artifact
from app import crop_climate_joint_continuation as climate

_spec = importlib.util.spec_from_file_location(
    'app._research_local_json_ownership',
    Path(__file__).resolve().parents[2] / 'research' / 'solar-local-json-ownership.py')
model = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = model
_spec.loader.exec_module(model)


def metadata():
    return {'version': 'v1', 'binding_sha256': 'binding',
            'scope': 'software_research_only', 'G0_G4': 'not_assessed',
            'source_chunk_sha256': 'chunk', 'before_checkpoint_sha256': 'before',
            'times': {'at': '2026-10-20T00:00:00.123456Z'}}


def commit(sequence=1):
    return {'version': 'test-only', 'header_sha256': 'a'*64, 'sequence': sequence,
            'parent_commit_sha256': None, 'before_checkpoint_sha256': 'b'*64,
            'source_chunk_sha256': 'c'*64, 'result_sha256': 'd'*64,
            'source_meta': {'nested': [sequence]}, 'times_meta': {}, 'pages': []}


def put(directory, value):
    raw = artifact._canonical(value)
    digest = sha256(raw).hexdigest()
    path = directory / (digest + '.json')
    path.write_bytes(raw)
    path.chmod(0o400)
    return digest, raw, path


@contextmanager
def count_calls(function):
    monitor = sys.monitoring
    tool = next(i for i in range(5, -1, -1) if monitor.get_tool(i) is None)
    calls = []
    monitor.use_tool_id(tool, 'json-ownership-contract')
    monitor.register_callback(tool, monitor.events.PY_START, lambda code, offset: calls.append(code))
    monitor.set_local_events(tool, function.__code__, monitor.events.PY_START)
    try:
        yield calls
    finally:
        monitor.set_local_events(tool, function.__code__, 0)
        monitor.register_callback(tool, monitor.events.PY_START, None)
        monitor.free_tool_id(tool)


@pytest.mark.parametrize('source', [
    {'value': 1}, {'문자': '토마토 🌱', 'escape': '\n"\\'},
    {'zero': -0.0, 'float': 0.125, 'int': 10**30, 'bool': True},
])
def test_source_payload_capabilities_preserve_exact_native_hashes(source):
    raw = artifact._canonical({'meta': metadata(), 'source': source})
    with model.OwnedJSONScope(hash_binding=(climate, '_hash')) as scope:
        assert scope.policy.approved
        token = scope.decode(raw)
        source_token = scope.take_field(token, 'source')
        meta_token = scope.take_field(token, 'meta')
        with pytest.raises(model.OwnershipUnavailable):
            scope.materialise(token)
        seal = scope.seal_source(source_token)
        assert seal.sha256 == sha256(climate._canonical(source)).hexdigest()
        with pytest.raises(model.OwnershipUnavailable):
            scope.materialise(source_token)
        result = scope.bind_payload(seal, meta_token)
        assert result.source_sha256 == climate._hash(source)
        assert result.payload_sha256 == climate._hash({**metadata(), 'source': source})
        exposed = scope.materialise(result.source)
        exposed['mutation'] = []
        assert scope.materialise(result.metadata) == metadata()
        for consumed in (seal, meta_token, result.source, result.metadata):
            with pytest.raises(model.OwnershipUnavailable):
                scope.materialise(consumed)
        assert scope.raw_bytes == 0
        assert scope.peak_raw_bytes <= scope.max_raw_bytes
    assert scope.raw_bytes == 0


def test_default_codec_matches_isolated_reference():
    assert model.json_reference_profile() in model._APPROVED_JSON_PROFILES
    assert model.native_json_current()
    with model.OwnedJSONScope() as scope:
        assert scope.policy.approved


def test_receipts_cannot_be_forged_transferred_or_reused():
    with model.OwnedJSONScope() as first, model.OwnedJSONScope() as second:
        value = first.decode(b'{"v":[]}')
        forged = model.OwnedValue(value._owner, value._slot, value._key)
        for scope, token in ((second, value), (first, forged)):
            with pytest.raises(model.OwnershipUnavailable):
                scope.materialise(token)
        assert first.materialise(value) == {'v': []}
    with pytest.raises(model.OwnershipUnavailable):
        first.decode(b'{}')
    first.close()


@pytest.mark.parametrize('budget', [True, False, 0, -1, 1.0, model.MAX_RAW_BYTES+1])
def test_invalid_aggregate_budgets_rejected(budget):
    with pytest.raises(model.OwnershipUnavailable):
        model.OwnedJSONScope(max_raw_bytes=budget)


@pytest.mark.parametrize('binding', [False, (), [], (artifact,), (artifact, '_json'), (object(), '_hash')])
def test_invalid_hash_binding_rejected(binding):
    with pytest.raises(model.OwnershipUnavailable):
        model.OwnedJSONScope(hash_binding=binding)


def test_small_budget_falls_back_without_losing_value_or_exceeding_cap():
    with model.OwnedJSONScope(max_raw_bytes=2) as scope:
        token = scope.decode(b'{"v":1}')
        assert not scope.owns(token)
        assert scope.seal_source(token) is None
        assert scope.materialise(token) == {'v': 1}
        assert scope.peak_raw_bytes == 0
    raw = artifact._canonical({'meta': metadata(), 'source': {'v': 1}})
    with model.OwnedJSONScope(max_raw_bytes=2*len(raw)+8) as scope:
        root = scope.decode(raw)
        source = scope.take_field(root, 'source')
        meta = scope.take_field(root, 'meta')
        seal = scope.seal_source(source)
        assert seal is not None
        assert scope.bind_payload(seal, meta) is None
        assert scope.materialise(meta) == metadata()
        assert scope.peak_raw_bytes <= scope.max_raw_bytes


def test_exception_disposes_all_private_buffers():
    scope = model.OwnedJSONScope()
    with pytest.raises(RuntimeError, match='owned failure'):
        with scope:
            scope.decode(b'{"v":[1,2]}')
            raise RuntimeError('owned failure')
    assert scope.raw_bytes == 0
    assert not scope._slots and not scope._groups and not scope._cache


def test_cross_thread_and_async_task_owners_rejected():
    with model.OwnedJSONScope() as scope:
        errors = []
        def foreign():
            try:
                scope.decode(b'{}')
            except model.OwnershipUnavailable as exc:
                errors.append(str(exc))
        thread = Thread(target=foreign)
        thread.start(); thread.join()
        assert errors == ['local JSON owner unavailable']
    async def run():
        with model.OwnedJSONScope() as owner:
            async def child():
                with pytest.raises(model.OwnershipUnavailable):
                    owner.decode(b'{}')
            await asyncio.create_task(child())
            assert owner.materialise(owner.decode(b'{}')) == {}
    asyncio.run(run())


def test_chain_hides_mutable_values_and_commit_redecodes_only_after_transfer(tmp_path):
    digest, raw, _ = put(tmp_path, commit())
    with artifact._Files(tmp_path) as reader, model.OwnedJSONScope() as scope:
        with count_calls(artifact._json) as calls:
            chain = scope.chain(reader, digest, len(raw))
            assert chain.retained and len(calls) == 1
            assert chain.value.sequence == 1
            assert chain.value.keys == frozenset(commit())
            assert not hasattr(chain.value, 'source_meta')
            with pytest.raises(FrozenInstanceError):
                chain.value.sequence = 2
            token = scope.commit(reader, digest, len(raw))
            assert len(calls) == 1 and scope.cache_hits == 1
            exposed = scope.materialise(token)
            exposed['source_meta']['nested'].append(9)
            next_value = scope.materialise(scope.commit(reader, digest, len(raw)))
            assert len(calls) == 2 and scope.cache_hits == 1
            assert next_value == commit()
        assert reader._seen == {digest}
        assert reader._referenced_bytes == 8192+len(raw)
        assert scope.raw_bytes == 0


@pytest.mark.parametrize('change', ['bytes', 'limit', 'missing', 'symlink'])
def test_cached_commit_still_reads_current_file_and_limit(tmp_path, change):
    digest, raw, path = put(tmp_path, commit())
    with artifact._Files(tmp_path) as reader, model.OwnedJSONScope() as scope:
        scope.chain(reader, digest, len(raw))
        if change == 'bytes':
            path.chmod(0o600); path.write_bytes(raw.replace(b'test-only', b'evil-only'))
        if change in ('missing', 'symlink'):
            path.unlink()
        if change == 'symlink':
            other = tmp_path / 'target'
            other.write_bytes(raw); path.symlink_to(other)
        limit = len(raw)-1 if change == 'limit' else len(raw)
        with pytest.raises(artifact.CycleArtifactRejected) as original:
            reader._blob(digest, limit)
        with pytest.raises(type(original.value)) as candidate:
            scope.commit(reader, digest, limit)
        assert str(candidate.value) == str(original.value)
        assert scope.cache_hits == 0
    assert scope.raw_bytes == 0


def test_cached_commit_keeps_reference_budget_errors(tmp_path):
    digest, raw, _ = put(tmp_path, commit())
    with artifact._Files(tmp_path) as reader, model.OwnedJSONScope() as scope:
        scope.chain(reader, digest, len(raw))
        reader._seen.clear()
        reader._referenced_bytes = artifact.LIMITS['directory_bytes']
        with pytest.raises(artifact.CycleArtifactRejected, match='referenced artifact budget'):
            scope.commit(reader, digest, len(raw))
        assert scope.cache_hits == 0 and scope.raw_bytes == 0


def test_aggregate_budget_evicts_old_chain_and_never_crosses_reader(tmp_path):
    one, raw1, _ = put(tmp_path, commit(1))
    two, raw2, _ = put(tmp_path, commit(2))
    with artifact._Files(tmp_path) as reader, model.OwnedJSONScope(max_raw_bytes=max(len(raw1), len(raw2))) as scope:
        assert scope.chain(reader, one, len(raw1)).retained
        assert scope.chain(reader, two, len(raw2)).retained
        assert list(scope._cache) == [two]
        with artifact._Files(tmp_path) as other:
            with pytest.raises(model.OwnershipUnavailable, match='reader changed'):
                scope.commit(other, two, len(raw2))
        assert scope.materialise(scope.commit(reader, one, len(raw1))) == commit(1)
        assert scope.cache_hits == 0
        assert scope.peak_raw_bytes <= scope.max_raw_bytes
    assert scope.raw_bytes == 0


@pytest.mark.parametrize('phase', ['initial', 'late'])
@pytest.mark.parametrize('slot', ['parser', 'parser_body', 'reader_method', 'hash', 'pristine_wrong_slot'])
def test_changed_helpers_use_actual_original_fallback(tmp_path, monkeypatch, phase, slot):
    digest, raw, _ = put(tmp_path, commit())
    with artifact._Files(tmp_path) as reader:
        scope = model.OwnedJSONScope() if phase == 'late' else None
        if scope:
            scope.chain(reader, digest, len(raw))
        def rejected(*args):
            raise RuntimeError('changed helper executed')
        with monkeypatch.context() as changed:
            if slot == 'parser':
                changed.setattr(artifact, '_json', rejected)
            elif slot == 'parser_body':
                changed.setattr(artifact._json, '__code__', rejected.__code__)
            elif slot == 'reader_method':
                changed.setattr(artifact._Files, '_blob', rejected)
            elif slot == 'hash':
                changed.setattr(artifact, '_hash', rejected)
            else:
                changed.setattr(artifact, '_json', artifact._canonical)
            scope = scope or model.OwnedJSONScope()
            try:
                assert not scope.policy.current()
                if slot in ('parser', 'parser_body', 'reader_method'):
                    with pytest.raises(RuntimeError, match='changed helper executed'):
                        scope.commit(reader, digest, len(raw))
                elif slot == 'pristine_wrong_slot':
                    with pytest.raises(TypeError) as original:
                        reader._blob(digest, len(raw))
                    with pytest.raises(TypeError) as candidate:
                        scope.commit(reader, digest, len(raw))
                    assert str(candidate.value) == str(original.value)
                else:
                    with count_calls(artifact._json) as calls:
                        result = scope.materialise(scope.commit(reader, digest, len(raw)))
                    original, _ = reader._blob(digest, len(raw))
                    assert result == original
                    assert len(calls) == 1
                assert scope.cache_hits == 0 and scope.fallbacks == 1
            finally:
                scope.close()


def test_preimport_foreign_codec_is_never_learned_as_native(monkeypatch):
    name = 'app._unapproved_json_ownership_test'
    spec = importlib.util.spec_from_file_location(name, model.__file__)
    alternate = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, name, alternate)
    original = json.loads
    def foreign(*args, **kwargs):
        return original(*args, **kwargs)
    with monkeypatch.context() as changed:
        changed.setattr(json, 'loads', foreign)
        spec.loader.exec_module(alternate)
        assert not alternate._JSON_APPROVED
    with alternate.OwnedJSONScope() as scope:
        token = scope.decode(b'{"v":1}')
        assert not scope.owns(token)
        assert scope.materialise(token) == {'v': 1}


@pytest.mark.parametrize('change', ['recursion', 'int_limit', 'decoder_body'])
def test_late_codec_and_runtime_limits_disable_transfer(tmp_path, monkeypatch, change):
    digest, raw, _ = put(tmp_path, commit())
    with artifact._Files(tmp_path) as reader, model.OwnedJSONScope() as scope:
        scope.chain(reader, digest, len(raw))
        old_recursion = sys.getrecursionlimit()
        old_int = sys.get_int_max_str_digits()
        try:
            with monkeypatch.context() as changed:
                if change == 'recursion':
                    sys.setrecursionlimit(old_recursion+1)
                elif change == 'int_limit':
                    sys.set_int_max_str_digits(old_int+1 if old_int else 4301)
                else:
                    def rejected(*args, **kwargs):
                        raise RuntimeError('decoder changed')
                    changed.setattr(json.JSONDecoder.__init__, '__code__', rejected.__code__)
                assert not scope.policy.current()
                if change == 'decoder_body':
                    with pytest.raises(RuntimeError, match='decoder changed'):
                        scope.commit(reader, digest, len(raw))
                else:
                    assert scope.materialise(scope.commit(reader, digest, len(raw))) == commit()
                assert scope.cache_hits == 0 and scope.fallbacks == 1
        finally:
            sys.setrecursionlimit(old_recursion)
            sys.set_int_max_str_digits(old_int)


@pytest.mark.parametrize('raw', [b'{"v":1,"v":2}', b'{"v":NaN}', b'\xff', b'{"v": 1}', b'[]\n',
                               b'"\\u12 x"', '{"v":1١}'.encode(), '{"v":1.١}'.encode()])
def test_invalid_or_noncanonical_json_preserves_original_rejection(raw):
    def original():
        value = artifact._json(raw)
        artifact._need(artifact._canonical(value) == raw, 'ARTIFACT_HOLD: canonical blob required')
    with pytest.raises(artifact.CycleArtifactRejected) as expected:
        original()
    with model.OwnedJSONScope() as scope:
        with pytest.raises(type(expected.value)) as actual:
            scope.decode(raw)
        assert str(actual.value) == str(expected.value)
        assert scope.raw_bytes == 0


def test_deeper_second_call_redecodes_instead_of_assuming_recursion_capacity(tmp_path):
    digest, raw, _ = put(tmp_path, commit())
    with artifact._Files(tmp_path) as reader, model.OwnedJSONScope() as scope:
        scope.chain(reader, digest, len(raw))
        def nested():
            return scope.commit(reader, digest, len(raw))
        with count_calls(artifact._json) as calls:
            token = nested()
        assert len(calls) == 1 and scope.cache_hits == 0
        assert scope.materialise(token) == commit()


def test_closed_reader_cannot_supply_a_cached_value(tmp_path):
    digest, raw, _ = put(tmp_path, commit())
    reader = artifact._Files(tmp_path)
    with model.OwnedJSONScope() as scope:
        try:
            scope.chain(reader, digest, len(raw))
        finally:
            reader.close()
        with pytest.raises(model.OwnershipUnavailable, match='closed'):
            scope.commit(reader, digest, len(raw))
        assert scope.cache_hits == 0


def test_metadata_shape_and_seal_capacity_preserve_owned_inputs():
    with model.OwnedJSONScope() as scope:
        source = scope.decode(b'{"v":1}')
        seal = scope.seal_source(source)
        meta = scope.decode(b'{"extra":1}')
        with pytest.raises(model.OwnershipUnavailable, match='closed bound payload'):
            scope.bind_payload(seal, meta)
        assert scope.materialise(meta) == {'extra': 1}
    with model.OwnedJSONScope(max_raw_bytes=7) as scope:
        source = scope.decode(b'{"v":1}')
        assert scope.seal_source(source) is None
        assert scope.materialise(source) == {'v': 1}
        assert scope.raw_bytes == 0


def test_profile_does_not_depend_on_unreachable_default_codec_instances(monkeypatch):
    with monkeypatch.context() as changed:
        changed.setattr(json, '_default_encoder', object())
        changed.setattr(json, '_default_decoder', object())
        assert model.native_json_current()
        with model.OwnedJSONScope() as scope:
            assert scope.materialise(scope.decode(b'{"v":1}')) == {'v': 1}


def test_source_reserves_encoding_capacity_before_allocating_another_large_buffer():
    raw = artifact._canonical({'v': 'x'*550000})
    with model.OwnedJSONScope() as scope:
        with count_calls(artifact._canonical) as calls:
            token = scope.decode(raw)
            assert len(calls) == 1
            assert scope.seal_source(token) is None
            assert len(calls) == 1
        assert len(scope.materialise(token)['v']) == 550000
        assert scope.peak_raw_bytes <= model.MAX_RAW_BYTES
        assert scope.raw_bytes == 0


def test_native_read_reserves_capacity_for_fresh_bytes_alongside_retained_bytes(tmp_path):
    digest, raw, _ = put(tmp_path, commit())
    with artifact._Files(tmp_path) as reader, model.OwnedJSONScope(max_raw_bytes=2*len(raw)-1) as scope:
        assert scope.chain(reader, digest, len(raw)).retained
        assert scope.materialise(scope.commit(reader, digest, len(raw))) == commit()
        assert scope.cache_hits == 0
        assert scope.peak_raw_bytes <= scope.max_raw_bytes


def test_oversized_read_uses_original_limit_and_cannot_offer_owned_values(tmp_path):
    digest, raw, _ = put(tmp_path, commit())
    with artifact._Files(tmp_path) as reader, model.OwnedJSONScope(max_raw_bytes=len(raw)) as scope:
        assert not scope.chain(reader, digest, len(raw)+1).retained
        token = scope.commit(reader, digest, len(raw)+1)
        assert not scope.owns(token)
        assert scope.materialise(token) == commit()
        assert scope.raw_bytes == 0 and scope.fallbacks == 2
