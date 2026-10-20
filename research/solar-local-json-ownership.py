"""Research candidate: linear JSON ownership for one artifact read operation.

This module is not wired into a worker. Native approval is an isolated-reference
fingerprint; an unsupported codec uses the original artifact decoder.
"""
from __future__ import annotations

import builtins
from dataclasses import dataclass
from hashlib import sha256
import json
import os
from pathlib import Path
import sys
from threading import get_ident
import types

MAX_RAW_BYTES = 1024 * 1024
_APPROVED_JSON_PROFILES = frozenset((
    '3905591a468ecd740179f8bb52231ec95a4f34296ee7bd4fb3f0fbd916f343a2',
    'b4840046d7f0bee639353d6f44225c8d77c0293bc6c9ad0a2d0f0777bcbb8f3a',
))
_JSON_MODULES = (json, json.encoder, json.decoder, json.scanner)
_IGNORE = frozenset(('_default_encoder', '_default_decoder'))


class OwnershipUnavailable(ValueError):
    """A receipt has no current owner, codec, or resource capacity."""


def _code(value):
    if type(value) is types.CodeType:
        return (value.co_code.hex(), tuple(_code(x) for x in value.co_consts),
                value.co_names, value.co_varnames, value.co_argcount,
                value.co_posonlyargcount, value.co_kwonlyargcount, value.co_flags,
                value.co_freevars, value.co_cellvars, value.co_exceptiontable.hex())
    if type(value) is tuple:
        return tuple(_code(x) for x in value)
    if type(value) is frozenset:
        return ('frozenset', tuple(sorted((_code(x) for x in value), key=repr)))
    return value


def _semantic(value, seen):
    kind = type(value)
    if value is None or kind in (bool, int, str, bytes):
        return value
    if kind is float:
        return ('float', float.hex(value))
    if kind in (tuple, list):
        return (kind.__name__, tuple(_semantic(x, seen) for x in value))
    if kind is dict:
        return ('dict', tuple((k, _semantic(v, seen)) for k, v in sorted(value.items())))
    if isinstance(value, int):
        return ('integer_type', kind.__module__, kind.__qualname__, int.__int__(value))
    if kind is types.ModuleType:
        return ('module', value.__name__)
    if kind is types.CodeType:
        return ('code', _code(value))
    if kind is types.FunctionType:
        label = ('function', value.__module__, value.__qualname__)
        if id(value) in seen:
            return ('reference', label)
        seen.add(id(value))
        owner = sys.modules.get(value.__module__)
        used = tuple((n, ('unused_default_instance', n) if n in _IGNORE else
                      _semantic(value.__globals__.get(n, value.__builtins__.get(n)), seen))
                     for n in value.__code__.co_names)
        return (label, _code(value.__code__), _semantic(value.__defaults__, seen),
                _semantic(value.__kwdefaults__, seen),
                tuple(_semantic(c.cell_contents, seen) for c in value.__closure__ or ()),
                owner is not None and value.__globals__ is vars(owner), used)
    if kind is type:
        label = ('class', value.__module__, value.__qualname__, value.__flags__ & 768)
        if not value.__module__.startswith('json'):
            return label
        if id(value) in seen:
            return ('reference', label)
        seen.add(id(value))
        fields = tuple((n, _semantic(v, seen)) for n, v in sorted(vars(value).items())
                       if n not in ('__dict__', '__weakref__', '__doc__'))
        return (label, tuple((v.__module__, v.__qualname__) for v in value.__bases__), fields)
    if (kind in (types.BuiltinFunctionType, types.BuiltinMethodType)
            or (kind.__module__ == 'builtins' and kind.__name__ == 'builtin_method'
                and kind.__flags__ & 256)):
        return ('builtin', value.__module__, value.__qualname__,
                _semantic(value.__self__, seen) if value.__self__ is not None else None)
    if kind in (types.MethodDescriptorType, types.WrapperDescriptorType):
        return ('descriptor', value.__qualname__, _semantic(value.__objclass__, seen))
    if kind is classmethod or kind is staticmethod:
        return (kind.__name__, _semantic(value.__func__, seen))
    if kind.__module__ == 're' and kind.__name__ == 'Pattern' and kind.__flags__ & 256:
        return ('regex', value.pattern, value.flags)
    raise OwnershipUnavailable('unsupported JSON reference state: '+kind.__module__+'.'+kind.__qualname__)


def json_reference_profile():
    """A portable semantic fingerprint; no object addresses or input data."""
    seen = set()
    roots = tuple((module.__name__, tuple((n, _semantic(v, seen))
                  for n, v in sorted(vars(module).items())
                  if not n.startswith('__') and n not in _IGNORE)) for module in _JSON_MODULES)
    state = (sys.implementation.name, tuple(sys.version_info[:2]), roots)
    return sha256(repr(state).encode()).hexdigest()


def _live_stamp():
    if (json.encoder is not _JSON_MODULES[1] or json.decoder is not _JSON_MODULES[2]
            or json.scanner is not _JSON_MODULES[3]):
        return None
    parts = []; functions = []; mutable = set()
    def container(v):
        if type(v) in (dict, list) and id(v) not in mutable:
            mutable.add(id(v))
            items = tuple(sorted(v.items())) if type(v) is dict else tuple(enumerate(v))
            parts.append((id(v), tuple((k, id(x)) for k, x in items)))
            for _, x in items:
                container(x)
    for module in _JSON_MODULES:
        fields = tuple((n, v) for n, v in sorted(vars(module).items())
                       if not n.startswith('__') and n not in _IGNORE)
        parts.append((id(module), tuple((n, id(v)) for n, v in fields)))
        for _, value in fields:
            container(value)
            if type(value) is types.FunctionType:
                functions.append(value)
            elif type(value) is type and value.__module__.startswith('json'):
                attributes = tuple(sorted(vars(value).items()))
                parts.append((id(value), tuple((n, id(v)) for n, v in attributes)))
                functions.extend(v for _, v in attributes if type(v) is types.FunctionType)
    names = set()
    for fn in functions:
        parts.append((id(fn), id(fn.__code__), id(fn.__defaults__), id(fn.__kwdefaults__),
                      tuple(id(c.cell_contents) for c in fn.__closure__ or ())))
        container(fn.__kwdefaults__)
        for value in fn.__defaults__ or ():
            container(value)
        names.update(fn.__code__.co_names)
    parts.append(tuple((n, id(vars(builtins).get(n))) for n in sorted(names)))
    parts.append((id(sys.getrecursionlimit), sys.getrecursionlimit(),
                  id(sys.get_int_max_str_digits), sys.get_int_max_str_digits()))
    return tuple(parts)


class _JSONReferences:
    """Retain approved objects; inspect all original mutable slots on each call."""
    def __init__(self):
        self.modules = []
        self.classes = []
        self.functions = []
        self.containers = []
        parts = []
        seen = set()
        def container(value):
            if type(value) in (dict, list) and id(value) not in seen:
                seen.add(id(value))
                entries = tuple(sorted(value.items())) if type(value) is dict else tuple(enumerate(value))
                self.containers.append((value, entries))
                parts.append((id(value), tuple((k, id(v)) for k, v in entries)))
                for _, item in entries:
                    container(item)
        functions = []
        for module in _JSON_MODULES:
            fields = {n: v for n, v in sorted(vars(module).items())
                      if not n.startswith('__') and n not in _IGNORE}
            self.modules.append((vars(module), {n: (v,) for n, v in fields.items()}))
            parts.append((id(module), tuple((n, id(v)) for n, v in fields.items())))
            for value in fields.values():
                container(value)
                if type(value) is types.FunctionType:
                    functions.append(value)
                elif type(value) is type and value.__module__.startswith('json'):
                    attributes = tuple(sorted(vars(value).items()))
                    self.classes.append((value, attributes))
                    parts.append((id(value), tuple((n, id(v)) for n, v in attributes)))
                    functions.extend(v for _, v in attributes if type(v) is types.FunctionType)
        names = set()
        for fn in functions:
            self.functions.append((fn, fn.__code__, fn.__defaults__, fn.__kwdefaults__,
                                   tuple(c.cell_contents for c in fn.__closure__ or ())))
            _, code, defaults, kwdefaults, closure = self.functions[-1]
            parts.append((id(fn), id(code), id(defaults), id(kwdefaults), tuple(id(v) for v in closure)))
            container(fn.__kwdefaults__)
            for value in fn.__defaults__ or ():
                container(value)
            names.update(fn.__code__.co_names)
        self.builtins = tuple((n, vars(builtins).get(n)) for n in sorted(names))
        self.limits = (sys.getrecursionlimit, sys.getrecursionlimit(),
                       sys.get_int_max_str_digits, sys.get_int_max_str_digits())
        parts.append(tuple((n, id(v)) for n, v in self.builtins))
        recursion, recursion_value, digits, digits_value = self.limits
        parts.append((id(recursion), recursion_value, id(digits), digits_value))
        self.stamp = tuple(parts)

    def current(self):
        table = vars(builtins)
        for name, value in self.builtins:
            if table.get(name) is not value:
                return False
        if (json.encoder is not _JSON_MODULES[1] or json.decoder is not _JSON_MODULES[2]
                or json.scanner is not _JSON_MODULES[3]):
            return False
        for table, expected in self.modules:
            count = 0
            for name, value in table.items():
                if type(name) is not str:
                    return _live_stamp() == self.stamp
                entry = expected.get(name)
                if entry is not None:
                    if entry[0] is not value:
                        return False
                    count += 1
                elif not name.startswith('__') and name not in _IGNORE:
                    return False
            if count != len(expected):
                return False
        for cls, entries in self.classes:
            table = vars(cls)
            if len(table) != len(entries):
                return False
            for name, value in entries:
                if table.get(name, _MISSING) is not value:
                    return False
        for fn, code, defaults, kwdefaults, closure in self.functions:
            if (fn.__code__ is not code or fn.__defaults__ is not defaults
                    or fn.__kwdefaults__ is not kwdefaults):
                return False
            cells = fn.__closure__ or ()
            if len(cells) != len(closure):
                return False
            for index, value in enumerate(closure):
                if cells[index].cell_contents is not value:
                    return False
        for value, entries in self.containers:
            if len(value) != len(entries):
                return False
            if type(value) is dict:
                for key, item in entries:
                    if value.get(key, _MISSING) is not item:
                        return False
            else:
                for index, item in entries:
                    if value[index] is not item:
                        return False
        recursion, recursion_value, digits, digits_value = self.limits
        return (sys.getrecursionlimit is recursion and sys.get_int_max_str_digits is digits
                and recursion() == recursion_value and digits() == digits_value)


_MISSING = object()
try:
    _JSON_APPROVED = json_reference_profile() in _APPROVED_JSON_PROFILES
    _JSON_STAMP = _live_stamp() if _JSON_APPROVED else None
    _JSON_REFERENCES = _JSONReferences() if _JSON_APPROVED else None
    if _JSON_APPROVED and _JSON_REFERENCES.stamp != _JSON_STAMP:
        raise OwnershipUnavailable('JSON reference changed during approval')
except (OwnershipUnavailable, AttributeError, TypeError, ValueError, RecursionError):
    _JSON_APPROVED = False
    _JSON_STAMP = None
    _JSON_REFERENCES = None


def native_json_current():
    if not _JSON_APPROVED:
        return False
    try:
        return _JSON_REFERENCES.current()
    except (AttributeError, TypeError, ValueError, RecursionError):
        return False


_APP_FILES = {
    'crop_cycle_artifact.py': '10bcf863ba40338f2efa7242d78c2cccd3020fbdca061951da6b7b1c5a7c51f7',
    'crop_cycle_input_stream.py': '83eecd4c282f5572cbd244edd633b7b9b40ba1c879fe5cfb9de102da182d2d53',
    'crop_cycle_continuation.py': '478f152a2395a451d9add64acf37e23ddc32a15273b14d0419869c1634596899',
    'crop_climate_joint_continuation.py': 'a3b1bb37b506ecad5961ffa1c5ce200282c6265365ce6e0d59787dd69333520a',
}
_APP_DIRECTORY = Path(__file__).resolve().parents[1] / 'backend' / 'app'
_COMPILED = {}
_COMMIT_FIELDS = frozenset(('version', 'header_sha256', 'sequence', 'parent_commit_sha256',
    'before_checkpoint_sha256', 'source_chunk_sha256', 'result_sha256', 'source_meta', 'times_meta', 'pages'))
_META_FIELDS = frozenset(('version', 'binding_sha256', 'scope', 'G0_G4',
    'source_chunk_sha256', 'before_checkpoint_sha256', 'times'))


def _attested(fn, expected_name, expected_module=None):
    if (type(fn) is not types.FunctionType or fn.__defaults__ is not None
            or fn.__kwdefaults__ is not None or fn.__closure__
            or fn.__qualname__ != expected_name
            or (expected_module is not None and fn.__module__ != expected_module)):
        return False
    path = Path(fn.__globals__.get('__file__', ''))
    if path.parent != _APP_DIRECTORY or path.name not in _APP_FILES:
        return False
    raw = path.read_bytes(); digest = sha256(raw).hexdigest()
    if digest != _APP_FILES[path.name]:
        return False
    if digest not in _COMPILED:
        codes = {}
        def collect(code):
            for item in code.co_consts:
                if type(item) is types.CodeType:
                    codes[item.co_qualname] = _code(item); collect(item)
        collect(compile(raw, str(path), 'exec', dont_inherit=True))
        _COMPILED[digest] = codes
    owner = sys.modules.get(fn.__module__)
    return (owner is not None and fn.__globals__ is vars(owner)
            and _code(fn.__code__) == _COMPILED[digest].get(fn.__qualname__))


class _LegacyPolicy:
    def __init__(self, legacy, hash_binding):
        self.legacy = legacy
        self.inputs = legacy.inputs
        self.files = legacy._Files
        self.hash_owner, self.hash_name = hash_binding
        hash_function = getattr(self.hash_owner, self.hash_name, None)
        self.hash_function = hash_function
        self.canonical = hash_function.__globals__.get('_canonical') if type(hash_function) is types.FunctionType else None
        self.paths = ((legacy, '_blob'), (legacy, '_json'), (legacy, '_read'), (legacy, '_need'),
            (self.inputs, '_json'), (self.inputs, '_need'), (self.inputs, '_read'), (self.inputs, '_digest'),
            (self.files, '_blob'), (self.hash_owner, self.hash_name))
        slots = [(getattr(owner, name, None), name,
                  None if owner is self.hash_owner and name == self.hash_name else owner.__name__)
                 for owner, name in self.paths if owner is not self.files]
        slots.append((self.files._blob, '_Files._blob', legacy.__name__))
        slots.extend(((legacy._canonical, '_canonical', None),
                      (self.canonical, '_canonical', None)))
        self.approved = (native_json_current()
            and all(_attested(fn, name, module) for fn, name, module in slots)
            and Path(self.canonical.__code__.co_filename).name in (
                'crop_cycle_continuation.py', 'crop_climate_joint_continuation.py')
            and self.canonical.__module__ == hash_function.__module__
            and legacy._canonical.__globals__.get('json') is json
            and self.canonical.__globals__.get('json') is json
            and self.inputs.json is json and legacy.sha256 is sha256
            and hash_function.__globals__.get('sha256') is sha256)
        self.baseline = self.stamp() if self.approved else None
        self.references = []
        if self.approved:
            functions = [getattr(owner, name, None) for owner, name in self.paths]
            functions.extend((legacy._canonical, self.hash_function, self.canonical))
            def names(code):
                found = set(code.co_names)
                for item in code.co_consts:
                    if type(item) is types.CodeType:
                        found.update(names(item))
                return found
            for fn in functions:
                bindings = tuple((n, fn.__globals__.get(n, fn.__builtins__.get(n)))
                                 for n in sorted(names(fn.__code__)))
                self.references.append((fn, fn.__code__, fn.__defaults__, fn.__kwdefaults__, bindings))
            self.aliases = (legacy.inputs, legacy._Files, self.inputs.json, legacy.sha256)
            captured = tuple((id(fn), id(code), id(defaults), id(kwdefaults),
                              tuple((n, id(v)) for n, v in bindings))
                             for fn, code, defaults, kwdefaults, bindings in self.references)
            self.approved = captured + (tuple(id(v) for v in self.aliases),) == self.baseline

    def stamp(self):
        functions = [getattr(owner, name, None) for owner, name in self.paths]
        functions.extend((self.legacy._canonical, self.hash_function, self.canonical))
        result = []
        def names(code):
            found = set(code.co_names)
            for value in code.co_consts:
                if type(value) is types.CodeType:
                    found.update(names(value))
            return found
        for fn in functions:
            if type(fn) is not types.FunctionType:
                return None
            result.append((id(fn), id(fn.__code__), id(fn.__defaults__), id(fn.__kwdefaults__),
                tuple((n, id(fn.__globals__.get(n, fn.__builtins__.get(n)))) for n in sorted(names(fn.__code__)))))
        result.append((id(self.legacy.inputs), id(self.legacy._Files), id(self.inputs.json), id(self.legacy.sha256)))
        return tuple(result)

    def current(self):
        try:
            if not self.approved or not native_json_current():
                return False
            for index, (owner, name) in enumerate(self.paths):
                if getattr(owner, name, None) is not self.references[index][0]:
                    return False
            if (self.legacy._canonical is not self.references[-3][0]
                    or self.hash_function is not self.references[-2][0]
                    or self.canonical is not self.references[-1][0]):
                return False
            for fn, code, defaults, kwdefaults, bindings in self.references:
                if (fn.__code__ is not code or fn.__defaults__ is not defaults
                        or fn.__kwdefaults__ is not kwdefaults):
                    return False
                namespace, fallback = fn.__globals__, fn.__builtins__
                for name, value in bindings:
                    actual = namespace.get(name, _MISSING)
                    if actual is _MISSING and name not in namespace:
                        actual = fallback.get(name)
                    if actual is not value:
                        return False
            return (self.legacy.inputs is self.aliases[0] and self.legacy._Files is self.aliases[1]
                    and self.inputs.json is self.aliases[2] and self.legacy.sha256 is self.aliases[3])
        except (AttributeError, TypeError, ValueError, RecursionError):
            return False


@dataclass(frozen=True, slots=True)
class OwnedValue:
    _owner: object
    _slot: int
    _key: object


@dataclass(frozen=True, slots=True)
class SourceSeal:
    _owner: object
    _slot: int
    _key: object
    sha256: str


@dataclass(frozen=True, slots=True)
class PayloadHashes:
    source_sha256: str
    payload_sha256: str
    source: OwnedValue
    metadata: OwnedValue


@dataclass(frozen=True, slots=True)
class ChainHeader:
    keys: frozenset
    version: str
    header_sha256: str
    sequence: int
    parent_commit_sha256: str | None


@dataclass(frozen=True, slots=True)
class ChainRead:
    value: object
    size: int
    retained: bool


class OwnedJSONScope:
    """Opaque trees and a shared raw-byte budget, owned by one call/thread/task.

    A chain read exposes immutable header fields. A matching commit read must
    re-read/hash the file before it can transfer the retained tree once. Trees
    exposed by materialise() are consumed and can no longer supply a seal.
    """
    def __init__(self, *, max_raw_bytes=MAX_RAW_BYTES, hash_binding=None):
        from app import crop_cycle_artifact as legacy
        if type(max_raw_bytes) is not int or not 0 < max_raw_bytes <= MAX_RAW_BYTES:
            raise OwnershipUnavailable('invalid local JSON budget')
        if hash_binding is None:
            hash_binding = (legacy, '_hash')
        if (type(hash_binding) is not tuple or len(hash_binding) != 2
                or type(hash_binding[0]) is not types.ModuleType
                or type(hash_binding[1]) is not str or hash_binding[1] != '_hash'):
            raise OwnershipUnavailable('invalid local JSON hash binding')
        self.legacy = legacy
        self.policy = _LegacyPolicy(legacy, hash_binding)
        self.max_raw_bytes = max_raw_bytes
        self._pid, self._thread, self._task = os.getpid(), get_ident(), self._current_task()
        self._closed = False; self._tainted = False; self._key = object(); self._reserved = 0
        self._slots = {}; self._groups = {}; self._refs = {}; self._cache = {}
        self._next = 0; self._next_group = 0; self._reader = None; self._directory = None
        self.raw_bytes = 0; self.peak_raw_bytes = 0; self.cache_hits = 0; self.fallbacks = 0

    @staticmethod
    def _current_task():
        import asyncio
        try:
            return asyncio.current_task()
        except RuntimeError:
            return None

    def _check(self):
        if (self._closed or os.getpid() != self._pid or get_ident() != self._thread
                or self._current_task() is not self._task):
            raise OwnershipUnavailable('local JSON owner unavailable')

    def _ready(self):
        self._check()
        return not self._tainted and self.policy.current()

    @staticmethod
    def _depth():
        frame = sys._getframe()
        depth = 0
        while frame is not None:
            depth += 1
            frame = frame.f_back
        return depth

    def __enter__(self):
        self._check(); return self

    def __exit__(self, *args):
        self.close()

    def close(self):
        if not self._closed:
            self._check()
        self._slots.clear(); self._cache.clear(); self._groups.clear(); self._refs.clear()
        self.raw_bytes = 0; self._reserved = 0; self._reader = None; self._closed = True

    def _get(self, token):
        self._check()
        if (type(token) not in (OwnedValue, SourceSeal) or token._owner is not self
                or token._key is not self._key):
            raise OwnershipUnavailable('foreign JSON receipt')
        row = self._slots.get(token._slot)
        if row is None or row[0] is not token:
            raise OwnershipUnavailable('consumed JSON receipt')
        return row

    def _new(self, value, groups=(), *, owned=True, seal=None):
        self._check()
        self._next += 1
        cls = OwnedValue if seal is None else SourceSeal
        token = cls(self, self._next, self._key) if seal is None else cls(self, self._next, self._key, seal)
        groups = frozenset(groups)
        for group in groups:
            self._refs[group] = self._refs.get(group, 0) + 1
        self._slots[token._slot] = (token, value, groups, owned)
        return token

    def _drop(self, token):
        row = self._get(token); del self._slots[token._slot]
        for group in row[2]:
            self._refs[group] -= 1
            if not self._refs[group]:
                del self._refs[group]
                self.raw_bytes -= len(self._groups.pop(group))
        return row

    def _room(self, amount):
        while self.raw_bytes + amount > self.max_raw_bytes and self._cache:
            digest = next(iter(self._cache)); entry = self._cache.pop(digest)
            self._drop(entry[0])
        return self.raw_bytes + amount <= self.max_raw_bytes

    def _allocate(self, raw):
        if not self._room(len(raw)):
            return None
        self._next_group += 1; group = self._next_group
        self._groups[group] = raw; self._refs[group] = 0
        self.raw_bytes += len(raw); self.peak_raw_bytes = max(self.peak_raw_bytes, self.raw_bytes)
        return group

    def _reserve(self, amount):
        if not self._room(amount):
            return False
        self._reserved += amount; self.raw_bytes += amount
        self.peak_raw_bytes = max(self.peak_raw_bytes, self.raw_bytes)
        return True

    def _unreserve(self, amount):
        if not self._closed:
            self.raw_bytes -= amount; self._reserved -= amount

    def _decode(self, raw):
        before = self._ready()
        value = self.legacy._json(raw)
        self.legacy._need(self.legacy._canonical(value) == raw, 'ARTIFACT_HOLD: canonical blob required')
        after = self._ready()
        if before and not after:
            self._tainted = True
        return value, before and after

    def decode(self, raw):
        self._check()
        if type(raw) is not bytes:
            raise OwnershipUnavailable('exact JSON bytes required')
        value, owned = self._decode(raw)
        group = self._allocate(raw) if owned else None
        return self._new(value, () if group is None else (group,), owned=owned and group is not None)

    def owns(self, token):
        row = self._get(token)
        return row[3] and self._ready()

    def materialise(self, token):
        return self._drop(token)[1]

    def take_field(self, token, name):
        row = self._get(token)
        if not row[3] or not self._ready() or type(row[1]) is not dict or type(name) is not str:
            raise OwnershipUnavailable('native object ownership required')
        value = row[1].pop(name)
        child = self._new(value, row[2])
        if not row[1]:
            self._drop(token)
        return child

    def _encoding_bound(self, token):
        return sum(len(self._groups[group]) for group in self._get(token)[2])

    def seal_source(self, token):
        row = self._get(token)
        if not row[3] or not self._ready():
            return None
        reserved = self._encoding_bound(token)
        if not self._reserve(reserved):
            return None
        try:
            try:
                raw = self.policy.canonical(row[1])
            except RecursionError:
                return None
            if len(raw) > reserved:
                raise OwnershipUnavailable('source exceeded its owned encoding')
        finally:
            self._unreserve(reserved)
        if not self._ready():
            self._tainted = True; return None
        group = self._allocate(raw)
        if group is None:
            return None
        value, groups = row[1], row[2]
        sealed = self._new((value, raw, groups), (*groups, group), seal=sha256(raw).hexdigest())
        self._drop(token)
        return sealed

    def bind_payload(self, source, metadata):
        left = self._get(source); right = self._get(metadata)
        if (type(source) is not SourceSeal or type(metadata) is not OwnedValue
                or not right[3] or not self._ready()):
            return None
        if type(right[1]) is not dict or set(right[1]) != _META_FIELDS:
            raise OwnershipUnavailable('closed bound payload metadata required')
        value, raw, source_groups = left[1]
        before = {k: v for k, v in right[1].items() if k < 'source'}
        after = {k: v for k, v in right[1].items() if k > 'source'}
        reserved = self._encoding_bound(metadata) + 16
        if not self._reserve(reserved):
            return None
        try:
            try:
                prefix = self.policy.canonical(before)[:-1] + b',"source":'
                suffix = b',' + self.policy.canonical(after)[1:]
            except RecursionError:
                return None
            if len(prefix) + len(suffix) > reserved:
                raise OwnershipUnavailable('bound metadata exceeded its owned encoding')
            if not self._ready():
                self._tainted = True; return None
            digest = sha256(); digest.update(prefix); digest.update(raw); digest.update(suffix)
            new_source = self._new(value, source_groups)
            new_metadata = self._new(right[1], right[2])
            self._drop(source); self._drop(metadata)
            return PayloadHashes(source.sha256, digest.hexdigest(), new_source, new_metadata)
        finally:
            self._unreserve(reserved)

    def _bind_reader(self, reader):
        self._check()
        fd = reader._fd
        if type(fd) is not int:
            raise OwnershipUnavailable('artifact reader is closed')
        info = os.fstat(fd); identity = (fd, info.st_dev, info.st_ino)
        if self._reader is None:
            self._reader = reader; self._directory = identity
        if self._reader is not reader or self._directory != identity:
            raise OwnershipUnavailable('artifact reader changed')

    def _reader_native(self, reader):
        method = reader._blob
        return (self._ready() and type(method) is types.MethodType
            and method.__func__ is self.policy.files._blob
            and type(reader._seen) is set and type(reader._referenced_bytes) is int)

    def _account(self, reader, digest, size):
        if digest not in reader._seen:
            reader._seen.add(digest); reader._referenced_bytes += size
            self.legacy._need(reader._referenced_bytes <= self.legacy.LIMITS['directory_bytes']
                and len(reader._seen) <= self.legacy.LIMITS['files'],
                'RESOURCE_HOLD: referenced artifact budget exceeded')

    def _raw(self, reader, digest, limit):
        self.legacy._need(self.legacy.inputs._digest(digest), 'ARTIFACT_HOLD: blob SHA required')
        raw = self.legacy._read(reader._fd, digest + '.json', limit)
        self.legacy._need(self.legacy.sha256(raw).hexdigest() == digest, 'HASH_HOLD: artifact blob mismatch')
        return raw

    def chain(self, reader, digest, limit):
        self._bind_reader(reader)
        native = (self._reader_native(reader) and type(limit) is int
                  and 0 < limit <= self.max_raw_bytes and self._reserve(limit))
        if not native:
            self.fallbacks += 1; value, size = reader._blob(digest, limit)
            self._check()
            return ChainRead(value, size, False)
        depth = self._depth()
        try:
            raw = self._raw(reader, digest, limit)
        finally:
            self._unreserve(limit)
        value, owned = self._decode(raw)
        self._account(reader, digest, len(raw))
        valid = (owned and type(value) is dict and set(value) == _COMMIT_FIELDS
            and type(value['version']) is str and type(value['header_sha256']) is str
            and type(value['sequence']) is int
            and (value['parent_commit_sha256'] is None or type(value['parent_commit_sha256']) is str))
        group = self._allocate(raw) if valid and digest not in self._cache else None
        if group is None:
            return ChainRead(value, len(raw), False)
        token = self._new(value, (group,)); self._cache[digest] = (token, raw, depth)
        view = ChainHeader(frozenset(value), value['version'], value['header_sha256'],
            value['sequence'], value['parent_commit_sha256'])
        return ChainRead(view, len(raw), True)

    def commit(self, reader, digest, limit):
        self._bind_reader(reader)
        native = (self._reader_native(reader) and type(limit) is int
                  and 0 < limit <= self.max_raw_bytes and self._reserve(limit))
        if not native:
            self.fallbacks += 1; value, _ = reader._blob(digest, limit)
            return self._new(value, owned=False)
        try:
            raw = self._raw(reader, digest, limit)
        finally:
            self._unreserve(limit)
        entry = self._cache.pop(digest, None)
        if entry is not None:
            token, previous, decoded_depth = entry
            if (previous == raw and self._depth() <= decoded_depth
                    and self._reader_native(reader)):
                try:
                    self._account(reader, digest, len(raw))
                except BaseException:
                    if not self._closed and token._slot in self._slots:
                        self._drop(token)
                    raise
                self.cache_hits += 1
                return token
            self._drop(token)
        value, owned = self._decode(raw); self._account(reader, digest, len(raw))
        group = self._allocate(raw) if owned else None
        return self._new(value, () if group is None else (group,), owned=owned and group is not None)


if __name__ == '__main__' and sys.argv[1:] == ['--reference']:
    print(json_reference_profile())
