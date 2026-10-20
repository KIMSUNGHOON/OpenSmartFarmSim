"""Research rejection evidence; these checks do not install a product parser."""
import importlib.util
from pathlib import Path

import pytest

from app import crop_cycle_input_stream as stream

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    'fresh_pairs_candidate', ROOT / 'research/solar-fresh-input-json-pairs.py')
candidate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(candidate)


def outcome(parser, raw):
    try:
        value = parser(raw)
        return ('value', stream._canonical(value))
    except Exception as exc:
        def signature(error):
            if error is None:
                return None
            return (type(error).__name__, str(error), signature(error.__cause__))
        return ('error', signature(exc))


@pytest.mark.parametrize('raw', [
    b'{}', b'[]', b'null', b'true', b'123456789012345678901234567890',
    b'{"b":2,"a":1}', b'{"a":[{},[1,2],{"b":null}]}',
    b'{"a":-0.0,"b":5e-324,"c":1.7976931348623157e308}',
    '{"지역":"서울","작물":"방울토마토"}'.encode(),
    b'{"a":"\\u0061","b":"\\ud83c\\udf45"}',
    b'{"a":1,"a":2}', b'{"x":{"a":1,"a":2}}',
    b'{"a":1,"\\u0061":2}', b'{"a":1,"b":2,"a":3}',
    b'{"a":NaN}', b'{"a":Infinity}', b'{"a":-Infinity}',
    b'{"a":1e9999}', b'{"a":}', b'{"a":1} {}', b'\xff',
    b'"\\uXXXX"', b'\xef\xbb\xbf{}', b'[' * 1100 + b']' * 1100,
], ids=lambda raw: repr(raw[:45]))
def test_standard_inputs_preserve_values_or_original_error_chain(raw):
    assert outcome(candidate.build_candidate(stream), raw) == outcome(stream._json, raw)


def test_fresh_decoder_calls_values_and_key_order(monkeypatch):
    original_loads = stream.json.loads
    calls = []

    def loads(raw, **kwargs):
        calls.append((raw, tuple(kwargs)))
        return original_loads(raw, **kwargs)

    monkeypatch.setattr(stream.json, 'loads', loads)
    parser = candidate.build_candidate(stream)
    raw = b'{"z":[{"value":1}],"a":2}'
    original = stream._json(raw)
    first = parser(raw)
    first['z'][0]['value'] = 999
    second = parser(raw)
    assert original == second and first != second
    assert list(second) == ['z', 'a']
    assert len(calls) == 3
    assert all(keys == ('object_pairs_hook', 'parse_constant') for _, keys in calls)


def test_mapping_protocol_counterexample_rejects_candidate(monkeypatch):
    class PairsWithMapping(list):
        def keys(self):
            return ['a', 'b']

        def __getitem__(self, key):
            return 999 if isinstance(key, str) else super().__getitem__(key)

    def loads(raw, **kwargs):
        return kwargs['object_pairs_hook'](PairsWithMapping([('a', 1), ('b', 2)]))

    monkeypatch.setattr(stream.json, 'loads', loads)
    parser = candidate.build_candidate(stream)
    assert stream._json(b'{}') == {'a': 1, 'b': 2}
    assert parser(b'{}') == {'a': 999, 'b': 999}


def test_iterator_protocol_counterexample_rejects_candidate(monkeypatch):
    def loads(raw, **kwargs):
        return kwargs['object_pairs_hook'](iter([('a', 1)]))

    monkeypatch.setattr(stream.json, 'loads', loads)
    assert stream._json(b'{}') == {'a': 1}
    with pytest.raises(TypeError, match='has no len'):
        candidate.build_candidate(stream)(b'{}')


def test_key_callback_counterexample_rejects_candidate(monkeypatch):
    class Key(str):
        def __hash__(self):
            self.calls += 1
            if self.calls == 2:
                raise RuntimeError('second key hash')
            return str.__hash__(self)

    def loads(raw, **kwargs):
        key = Key('a')
        key.calls = 0
        return kwargs['object_pairs_hook']([(key, 1)])

    monkeypatch.setattr(stream.json, 'loads', loads)
    with pytest.raises(RuntimeError, match='second key hash'):
        stream._json(b'{}')
    assert candidate.build_candidate(stream)(b'{}') == {'a': 1}
