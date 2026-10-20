"""Mutation equivalence against the retained, pre-optimization state oracles."""
import builtins
import importlib.util
import json
import sys

import pytest

from app import crop_cycle_artifact as artifact
from app import crop_climate_joint_continuation as climate
from test_local_json_ownership import model, count_calls


def test_current_checks_do_not_rebuild_identity_stamps():
    with model.OwnedJSONScope(hash_binding=(climate, '_hash')) as scope:
        assert scope.policy.approved
        with count_calls(model._live_stamp) as json_calls, count_calls(scope.policy.stamp) as legacy_calls:
            for _ in range(3):
                assert scope.policy.current()
        assert not json_calls and not legacy_calls


def test_watched_builtin_is_checked_before_new_comparison_uses_it(monkeypatch):
    calls = []
    def foreign_len(value):
        calls.append(value)
        raise RuntimeError('foreign builtin invoked')
    with monkeypatch.context() as altered:
        altered.setattr(builtins, 'len', foreign_len)
        observed = model.native_json_current()
    assert observed is False and not calls


@pytest.mark.parametrize('change', [
    'module_alias', 'module_value', 'module_extra', 'module_missing', 'same_size_module',
    'same_size_module_sentinel',
    'class_value', 'class_extra', 'class_missing', 'same_size_class',
    'function_code', 'defaults', 'kwdefaults', 'mutable_value', 'mutable_extra',
    'mutable_missing', 'same_size_mutable', 'builtin', 'recursion_getter', 'int_getter',
    'recursion_value', 'int_value', 'ignored_default', 'ignored_dunder',
])
def test_native_guard_matches_original_oracle_before_during_after_mutation(monkeypatch, change):
    baseline = model._JSON_STAMP
    assert model._live_stamp() == baseline and model.native_json_current()
    recursion, digits = sys.getrecursionlimit(), sys.get_int_max_str_digits()
    try:
        with monkeypatch.context() as altered:
            if change == 'module_alias':
                altered.setattr(json, 'encoder', object())
            elif change == 'module_value':
                altered.setattr(json.encoder, 'INFINITY', object())
            elif change in ('module_extra', 'same_size_module', 'same_size_module_sentinel'):
                if change.startswith('same_size_'):
                    altered.delattr(json.encoder, 'INFINITY')
                value = model._MISSING if change.endswith('_sentinel') else None
                altered.setattr(json.encoder, 'research_extra', value, raising=False)
            elif change == 'module_missing':
                altered.delattr(json.encoder, 'INFINITY')
            elif change == 'class_value':
                altered.setattr(json.JSONEncoder, '__doc__', 'changed')
            elif change in ('class_extra', 'same_size_class'):
                if change == 'same_size_class':
                    altered.delattr(json.JSONEncoder, 'encode')
                altered.setattr(json.JSONEncoder, 'research_extra', None, raising=False)
            elif change == 'class_missing':
                altered.delattr(json.JSONEncoder, 'encode')
            elif change == 'function_code':
                altered.setattr(json.dumps, '__code__', (lambda *a, **k: None).__code__)
            elif change == 'defaults':
                altered.setattr(json.encoder.py_encode_basestring_ascii, '__defaults__', ())
            elif change == 'kwdefaults':
                altered.setattr(json.dumps, '__kwdefaults__', {})
            elif change == 'mutable_value':
                altered.setitem(json.encoder.ESCAPE_DCT, '\n', 'changed')
            elif change in ('mutable_extra', 'same_size_mutable'):
                if change == 'same_size_mutable':
                    altered.delitem(json.encoder.ESCAPE_DCT, '\n')
                altered.setitem(json.encoder.ESCAPE_DCT, 'research_extra', None)
            elif change == 'mutable_missing':
                altered.delitem(json.encoder.ESCAPE_DCT, '\n')
            elif change == 'builtin':
                # A late builtin shadow must be seen without invoking it.
                altered.setattr(builtins, 'ValueError', RuntimeError)
            elif change == 'recursion_getter':
                altered.setattr(sys, 'getrecursionlimit', lambda: recursion)
            elif change == 'int_getter':
                altered.setattr(sys, 'get_int_max_str_digits', lambda: digits)
            elif change == 'recursion_value':
                sys.setrecursionlimit(recursion + 1)
            elif change == 'int_value':
                sys.set_int_max_str_digits(digits + 1 if digits else 4301)
            elif change == 'ignored_default':
                altered.setattr(json, '_default_encoder', object())
            else:
                altered.setattr(json, '__research_ignored', object(), raising=False)
            expected = model._live_stamp() == baseline
            assert model.native_json_current() is expected
            assert expected is change.startswith('ignored_')
    finally:
        sys.setrecursionlimit(recursion)
        sys.set_int_max_str_digits(digits)
    assert model._live_stamp() == baseline and model.native_json_current()


@pytest.mark.parametrize('change', [
    'slot', 'code', 'defaults', 'kwdefaults', 'global', 'builtin_fallback',
    'nested_code_global', 'canonical_slot', 'hash_slot', 'input_alias', 'files_alias',
])
def test_helper_guard_matches_original_oracle_after_approved_capture(monkeypatch, change):
    with model.OwnedJSONScope(hash_binding=(climate, '_hash')) as scope:
        policy = scope.policy
        assert policy.approved and policy.current()
        with monkeypatch.context() as altered:
            if change == 'slot':
                altered.setattr(artifact, '_json', artifact._canonical)
            elif change == 'code':
                altered.setattr(artifact._json, '__code__', artifact._canonical.__code__)
            elif change == 'defaults':
                altered.setattr(artifact._json, '__defaults__', ())
            elif change == 'kwdefaults':
                altered.setattr(artifact._json, '__kwdefaults__', {})
            elif change == 'global':
                altered.setattr(climate, 'json', object())
            elif change == 'builtin_fallback':
                altered.setattr(artifact.inputs, 'len', object(), raising=False)
            elif change == 'nested_code_global':
                assert '_need' not in artifact.inputs._json.__code__.co_names
                altered.setattr(artifact.inputs, '_need', object())
            elif change == 'canonical_slot':
                altered.setattr(artifact, '_canonical', climate._canonical)
            elif change == 'hash_slot':
                altered.setattr(climate, '_hash', artifact._hash)
            elif change == 'input_alias':
                altered.setattr(artifact, 'inputs', object())
            else:
                altered.setattr(artifact, '_Files', object())
            assert policy.stamp() != policy.baseline
            assert not policy.current()
        assert policy.stamp() == policy.baseline and policy.current()


@pytest.mark.parametrize('change', ['list_item', 'list_append', 'dict_item', 'dict_key',
                                    'kwdefault', 'closure', 'empty_cell'])
def test_recursive_mutable_and_closure_capture_matches_stamp_without_approving_codec(monkeypatch, change):
    nested = {'items': [object()], 'map': {'key': object()}}
    captured = object()
    def make_function():
        cell = captured
        def function(value=nested, *, option=nested):
            return value, option, cell
        return function
    function = make_function()
    with monkeypatch.context() as altered:
        # This synthetic graph exercises the oracle's recursive watches. It is
        # never approved by the public native codec predicate.
        altered.setattr(json, 'research_function', function, raising=False)
        baseline = model._live_stamp()
        references = model._JSONReferences()
        assert references.current() and not model.native_json_current()
        if change == 'list_item':
            nested['items'][0] = object()
        elif change == 'list_append':
            nested['items'].append(object())
        elif change == 'dict_item':
            nested['map']['key'] = object()
        elif change == 'dict_key':
            nested['map']['other'] = nested['map'].pop('key')
        elif change == 'kwdefault':
            function.__kwdefaults__['option'] = object()
        elif change == 'closure':
            function.__closure__[0].cell_contents = object()
        else:
            del function.__closure__[0].cell_contents
        if change == 'empty_cell':
            with pytest.raises(ValueError):
                model._live_stamp()
            with pytest.raises(ValueError):
                references.current()
        else:
            assert model._live_stamp() != baseline
            assert not references.current()
    assert model.native_json_current()


def test_json_reference_capture_cannot_learn_change_after_initial_stamp(monkeypatch):
    name = 'app._json_reference_snapshot_test'
    spec = importlib.util.spec_from_file_location(name, model.__file__)
    alternate = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, name, alternate)
    monitor = sys.monitoring
    slot = next(i for i in range(5, -1, -1) if monitor.get_tool(i) is None)
    hits = []
    with monkeypatch.context() as altered:
        def entered(code, offset):
            if code.co_qualname == '_JSONReferences.__init__' and not hits:
                hits.append(True)
                altered.setattr(json, 'dumps', lambda *a, **k: None)
        monitor.use_tool_id(slot, 'json-reference-snapshot-mutation')
        try:
            monitor.register_callback(slot, monitor.events.PY_START, entered)
            monitor.set_events(slot, monitor.events.PY_START)
            spec.loader.exec_module(alternate)
        finally:
            monitor.set_events(slot, 0)
            monitor.register_callback(slot, monitor.events.PY_START, None)
            monitor.free_tool_id(slot)
        assert hits == [True]
        assert not alternate._JSON_APPROVED and not alternate.native_json_current()
    assert not alternate.native_json_current() and model.native_json_current()


def test_helper_reference_capture_cannot_learn_change_after_initial_stamp(monkeypatch):
    original = model._LegacyPolicy.stamp
    hits = []
    with monkeypatch.context() as altered:
        def stamp(policy):
            result = original(policy)
            if not hits:
                hits.append(True)
                altered.setattr(artifact, '_json', lambda raw: raw)
            return result
        altered.setattr(model._LegacyPolicy, 'stamp', stamp)
        with model.OwnedJSONScope() as scope:
            assert hits == [True]
            assert not scope.policy.approved and not scope.policy.current()


@pytest.mark.parametrize('kind', ['object', 'str_subclass'])
def test_unusual_module_key_preserves_original_stamp_rejection(monkeypatch, kind):
    class Key:
        def __hash__(self):
            return hash('INFINITY')
        def __eq__(self, other):
            return other == 'INFINITY'
        def startswith(self, prefix):
            return 'INFINITY'.startswith(prefix)
        def __lt__(self, other):
            raise TypeError('foreign key ordering')
    class StringKey(str):
        def __lt__(self, other):
            raise TypeError('foreign key ordering')
    key = Key() if kind == 'object' else StringKey('INFINITY')
    table = vars(json.encoder)
    original = table['INFINITY']
    with monkeypatch.context() as altered:
        altered.delitem(table, 'INFINITY')
        altered.setitem(table, key, original)
        with pytest.raises(TypeError):
            model._live_stamp()
        assert not model.native_json_current()
        with model.OwnedJSONScope() as scope:
            token = scope.decode(b'{"v":1}')
            assert not scope.policy.approved and not scope.owns(token)
            assert scope.materialise(token) == {'v': 1}
    assert model.native_json_current()


def test_helper_global_lookup_preserves_missing_none_and_sentinel(monkeypatch):
    with model.OwnedJSONScope() as scope:
        policy = scope.policy
        assert policy.approved and policy.current()
        for value, expected in ((builtins.len, True), (None, False), (model._MISSING, False)):
            with monkeypatch.context() as altered:
                altered.setattr(artifact.inputs, 'len', value, raising=False)
                assert (policy.stamp() == policy.baseline) is expected
                assert policy.current() is expected
        assert policy.current()
