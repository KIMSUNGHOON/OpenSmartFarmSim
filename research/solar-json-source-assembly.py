"""Rejected assembly prototype; statement observations miss nested graph loans.

Retained for solar-json-observation-boundaries-20261020.md reproduction.
"""
import ast
import builtins
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import importlib.util
from inspect import getattr_static
from pathlib import Path
import sys
import types

ROOT = Path(__file__).resolve().parents[1]
NAME = 'app._research_solar_json_load_adapter'
if NAME not in sys.modules:
    spec = importlib.util.spec_from_file_location(NAME, ROOT/'research/solar-json-load-adapter.py')
    module = importlib.util.module_from_spec(spec)
    sys.modules[NAME] = module
    spec.loader.exec_module(module)
previous = sys.modules[NAME]
core = previous.core
storage = previous.storage
clock = storage.clock.clock_helpers
CLOCK_SHA256 = '946680379e482cbcff63bb6fb60421f9abf41c108fb69667a52f38d22e502b9c'
clock_raw = (ROOT/'backend/app/crop_climate_joint_time.py').read_bytes()
clock_codes = {}

def _collect(code):
    for value in code.co_consts:
        if type(value) is types.CodeType:
            clock_codes[value.co_qualname] = core._code(value)
            _collect(value)
_collect(compile(clock_raw, str(clock.__file__), 'exec', dont_inherit=True))
_clock_functions = tuple(getattr(clock, name) for name in ('_point', '_at', '_stamp', '_need'))
_clock_approved = (sha256(clock_raw).hexdigest() == CLOCK_SHA256 and all(
    type(fn) is types.FunctionType and fn.__globals__ is vars(clock)
    and fn.__module__ == clock.__name__ and fn.__defaults__ is None
    and fn.__kwdefaults__ is None and not fn.__closure__
    and core._code(fn.__code__) == clock_codes.get(fn.__qualname__)
    and fn.__qualname__ == name
    for fn, name in zip(_clock_functions, ('_point', '_at', '_stamp', '_need'), strict=True)))
_clock_stamp = tuple((fn, fn.__code__) for fn in _clock_functions) if _clock_approved else None
_BUILTINS = {name: getattr(builtins, name) for name in ('dict', 'list', 'type', 'set', 'len', 'sum', 'int', 'str', 'range', 'enumerate')}


def _builtins_current():
    return all(vars(storage).get(name, vars(builtins).get(name)) is value
               and vars(builtins).get(name) is value for name, value in _BUILTINS.items())


def _clock_current():
    try:
        if not _clock_approved or storage.clock._point is not _clock_functions[0]:
            return False
        functions = tuple(getattr(clock, name) for name in ('_point', '_at', '_stamp', '_need'))
        return (tuple((fn, fn.__code__) for fn in functions) == _clock_stamp
            and all(fn.__defaults__ is None and fn.__kwdefaults__ is None and not fn.__closure__ for fn in functions)
            and clock.datetime is datetime and clock.timedelta is timedelta and clock.timezone is timezone)
    except (AttributeError, TypeError, ValueError, RecursionError):
        return False


def _source_method():
    tree = ast.parse(previous._SOURCE)
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == '_Files')
    return cls


class _GuardStatements(ast.NodeTransformer):
    def generic_visit(self, node):
        node = super().generic_visit(node)
        for field in ('body', 'orelse'):
            statements = getattr(node, field, None)
            if statements and all(isinstance(v, ast.stmt) for v in statements):
                guarded = []
                for statement in statements:
                    guarded.extend(ast.parse('__scope._guard_assembly()').body)
                    guarded.append(statement)
                setattr(node, field, guarded)
        return node


def _factory(function, arguments):
    factory = ast.parse('def factory(__scope):\n    pass\n').body[0]
    function.args = ast.parse('def x('+arguments+'):\n    pass\n').body[0].args
    function.decorator_list = []
    factory.body = [function, ast.Return(ast.Name(function.name, ast.Load()))]
    module = ast.fix_missing_locations(ast.Module([factory], []))
    compiled = compile(module, 'research-solar-private-assembly', 'exec', dont_inherit=True)
    code = next(x for x in compiled.co_consts if type(x) is types.CodeType)
    return types.FunctionType(code, vars(storage))


def _records_factory():
    fn = next(n for n in _source_method().body if isinstance(n, ast.FunctionDef) and n.name == '_records')
    loop = next(n for n in fn.body if isinstance(n, ast.For))
    expected = "rows, _ = self._blob(d['sha256'], LIMITS['page_bytes'])"
    position = next(i for i, n in enumerate(loop.body) if ast.unparse(n) == expected)
    loop.body[position] = ast.parse("rows = __scope._page(self, d['sha256'], LIMITS['page_bytes'])").body[0]
    fn = _GuardStatements().visit(fn)
    return _factory(fn, 'self, kind, descriptors, manifest, program')


class _AssemblyCalls(ast.NodeTransformer):
    def visit_Call(self, node):
        node = self.generic_visit(node)
        if (isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name)
                and node.func.value.id == 'self' and node.func.attr == '_records'):
            node.func.value = ast.Name('__scope', ast.Load())
            node.args.insert(0, ast.Name('self', ast.Load()))
        elif isinstance(node.func, ast.Name) and node.func.id == '_hash' and len(node.args) == 1:
            arg = node.args[0]
            if isinstance(arg, ast.Name) and arg.id in ('source', 'payload'):
                node.func = ast.Attribute(ast.Name('__scope', ast.Load()), '_'+arg.id+'_hash', ast.Load())
                if arg.id == 'source': node.args.extend([ast.Name('times', ast.Load())])
        return node


def _prepare_factory():
    fn = next(n for n in _source_method().body if isinstance(n, ast.FunctionDef) and n.name == '_load')
    loop = [n for n in fn.body if isinstance(n, ast.For)][1]
    end = next(i for i, n in enumerate(loop.body) if 'HASH_HOLD: exact bound result/context/scope' in ast.unparse(n))
    fn.name = 'prepare_commit'
    fn.body = loop.body[1:end+1] + ast.parse('return source, times').body
    fn = _GuardStatements().visit(_AssemblyCalls().visit(fn))
    return _factory(fn, 'self, commit, digest, cp, h, context, manifest, program, index, counts')


_RECORDS = _records_factory()
_PREPARE = _prepare_factory()


def _rewrite_load(fn):
    loop = [n for n in fn.body if isinstance(n, ast.For)][1]
    end = next(i for i, n in enumerate(loop.body) if 'HASH_HOLD: exact bound result/context/scope' in ast.unparse(n))
    loop.body[:end+1] = ast.parse("__commit_token = __scope.commit(self, digest, LIMITS['metadata_bytes'])\nsource, times = __scope.process_commit(self, __commit_token, digest, cp, h, context, manifest, program, index, counts)").body


_LOAD = previous._build_factory(_rewrite_load)


class AssemblyScope(core.OwnedJSONScope):
    def __init__(self):
        super().__init__(hash_binding=(storage, '_hash'))
        self._bounds = {}
        self._assembling = False
        self._source_owned = False
        self._bound = 0
        self._source_token = None
        self._seal = None
        self.source_pairs = 0
        self.page_reads = 0
        self.fallback_pairs = 0

    def _new(self, value, groups=(), *, owned=True, seal=None, bound=None):
        token = super()._new(value, groups, owned=owned, seal=seal)
        self._bounds[token._slot] = (sum(len(self._groups[g]) for g in self._get(token)[2]) if bound is None else bound)
        return token

    def _drop(self, token):
        row = super()._drop(token)
        self._bounds.pop(token._slot, None)
        return row

    def _encoding_bound(self, token):
        self._get(token)
        return self._bounds[token._slot]

    def close(self):
        super().close()
        self._bounds.clear()

    def chain(self, reader, digest, limit):
        if not _builtins_current():
            self._bind_reader(reader)
            self.fallbacks += 1
            value, size = reader._blob(digest, limit)
            return core.ChainRead(value, size, False)
        return super().chain(reader, digest, limit)

    def _guard_assembly(self):
        self._check()
        if not self._assembling:
            raise core.OwnershipUnavailable('no private source assembly')
        self._source_owned = self._source_owned and self._ready() and _builtins_current() and _clock_current()

    def _page(self, reader, digest, limit):
        self._guard_assembly()
        native = self._reader_native(reader)
        # The original reader owns its existing bounded IO/canonical temporaries.
        # No raw page bytes are retained or duplicated by this scope.
        value, size = reader._blob(digest, limit)
        self.page_reads += 1
        self._guard_assembly()
        self._source_owned = self._source_owned and native and self._reader_native(reader)
        if type(size) is int and 0 <= size <= limit:
            self._bound += size
        else:
            self._source_owned = False
        return value

    def _records(self, reader, *args):
        self._guard_assembly()
        method = getattr_static(reader, '_records')
        if previous._attested(method, '_Files._records'):
            return _RECORDS(self)(reader, *args)
        self._source_owned = False
        return reader._records(*args)

    def _source_hash(self, source, times):
        self._guard_assembly()
        if self._source_owned and type(source) is dict and type(times) is dict:
            self._source_token = self._new(source, owned=True, bound=self._bound)
            self._seal = self.seal_source(self._source_token)
            if self._seal is not None:
                return self._seal.sha256
        self._source_owned = False
        return storage._hash(source)

    def _discard_source(self):
        for token in (self._seal, self._source_token):
            if token is not None and token._slot in self._slots:
                self._drop(token)
        self._seal = self._source_token = None

    def _payload_hash(self, payload):
        self._guard_assembly()
        if self._seal is not None and self._source_owned:
            metadata = {k: v for k, v in payload.items() if k != 'source'}
            if all(type(v) is str for k, v in metadata.items() if k != 'times'):
                bound = self._bound + 512 + 12*sum(len(v) for k, v in metadata.items() if k != 'times')
                token = self._new(metadata, owned=True, bound=bound)
                result = self.bind_payload(self._seal, token)
                if result is not None:
                    self.materialise(result.source)
                    self.materialise(result.metadata)
                    self._seal = self._source_token = None
                    self.source_pairs += 1
                    return result.payload_sha256
                self._drop(token)
        self._discard_source()
        self.fallback_pairs += 1
        return storage._hash(payload)

    def process_commit(self, reader, token, digest, cp, h, context, manifest, program, index, counts):
        row = self._get(token)
        self._assembling = True
        self._source_owned = row[3] and type(row[1]) is dict
        self._bound = self._encoding_bound(token) + 64
        if self._source_owned:
            self._source_owned = all(type(row[1].get(k)) is dict for k in ('source_meta', 'times_meta'))
        try:
            return _PREPARE(self)(reader, row[1], digest, cp, h, context, manifest, program, index, counts)
        finally:
            self._discard_source()
            self._drop(token)
            self._assembling = False


def load(self, head, *, audit=None):
    if audit is not None and type(audit) is not dict:
        raise ValueError('exact research audit dictionary required')
    method = getattr_static(self, '_load')
    eligible = (any(method is fn for fn in (previous._ORIGINAL_LOAD, load)) and _builtins_current()
        and previous._attested(previous._ORIGINAL_LOAD, '_Files._load')
        and all(previous._attested(getattr_static(self, name), '_Files.'+name) for name in ('_load_header', '_records'))
        and previous._attested(storage._need, '_need'))
    if not eligible:
        if audit is not None:
            audit.update(whole_load_fallback=True, source_pairs=0, fallback_pairs=0, cache_hits=0,
                         peak_raw_bytes=0, disposed=True, raw_bytes_after_close=0, extra_source_encodes_for_ownership=0)
        method = self._load
        if type(method) is types.MethodType and method.__func__ is load:
            return previous._ORIGINAL_LOAD(self, head)
        return method(head)
    scope = AssemblyScope()
    try:
        with scope:
            return _LOAD(scope, core.ChainHeader)(self, head)
    finally:
        if audit is not None:
            audit.update(whole_load_fallback=False, source_pairs=scope.source_pairs,
                         fallback_pairs=scope.fallback_pairs, page_reads=scope.page_reads,
                         cache_hits=scope.cache_hits, fallbacks=scope.fallbacks,
                         peak_raw_bytes=scope.peak_raw_bytes, disposed=scope._closed,
                         raw_bytes_after_close=scope.raw_bytes, extra_source_encodes_for_ownership=0)
