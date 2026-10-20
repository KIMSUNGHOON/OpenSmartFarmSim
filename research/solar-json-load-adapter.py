"""Unwired research adapter for the two commit loops in the native Solar load."""
import ast
from hashlib import sha256
import importlib.util
from inspect import getattr_static
from pathlib import Path
import sys
import types

from app import crop_greenhouse_solar_storage as storage

ROOT = Path(__file__).resolve().parents[1]
CORE_PATH = ROOT/'research/solar-local-json-ownership.py'
CORE_SHA256 = '7e90f6df0ba17dc6c00fb61e25608cea3b3c1379bb70e3c057c6a37c2cdf9126'
STORAGE_SHA256 = '065ff9f9706bed285f19b82e67277123947715af285cc6438a77fed3c7e30d6d'
CORE_NAME = 'app._research_local_json_ownership'
if sha256(CORE_PATH.read_bytes()).hexdigest() != CORE_SHA256:
    raise ValueError('research JSON ownership source changed')
if CORE_NAME not in sys.modules:
    spec = importlib.util.spec_from_file_location(CORE_NAME, CORE_PATH)
    core = importlib.util.module_from_spec(spec)
    sys.modules[CORE_NAME] = core
    spec.loader.exec_module(core)
core = sys.modules[CORE_NAME]
_ORIGINAL_LOAD = storage._Files._load
_SOURCE = (ROOT/'backend/app/crop_greenhouse_solar_storage.py').read_bytes()
_SOURCE_APPROVED = sha256(_SOURCE).hexdigest() == STORAGE_SHA256
_CODES = {}

def _collect(code):
    for item in code.co_consts:
        if type(item) is types.CodeType:
            _CODES[item.co_qualname] = core._code(item)
            _collect(item)

_collect(compile(_SOURCE, str(storage.__file__), 'exec', dont_inherit=True))


def _attested(function, name):
    return (_SOURCE_APPROVED and type(function) is types.FunctionType
        and function.__module__ == storage.__name__ and function.__qualname__ == name
        and function.__globals__ is vars(storage) and not function.__closure__
        and function.__defaults__ is None and function.__kwdefaults__ is None
        and core._code(function.__code__) == _CODES.get(name))


class _HeaderCondition(ast.NodeTransformer):
    def visit_Subscript(self, node):
        if isinstance(node.value, ast.Name) and node.value.id == 'commit':
            assert isinstance(node.slice, ast.Constant)
            assert node.slice.value in ('version', 'header_sha256', 'sequence')
            return ast.copy_location(ast.Attribute(ast.Name('commit', ast.Load()), node.slice.value, ast.Load()), node)
        return self.generic_visit(node)

    def visit_Call(self, node):
        if (isinstance(node.func, ast.Name) and node.func.id == 'set'
                and len(node.args) == 1 and isinstance(node.args[0], ast.Name)
                and node.args[0].id == 'commit'):
            return ast.copy_location(ast.Attribute(ast.Name('commit', ast.Load()), 'keys', ast.Load()), node)
        return self.generic_visit(node)

    def visit_Compare(self, node):
        if (isinstance(node.left, ast.Call) and isinstance(node.left.func, ast.Name)
                and node.left.func.id == 'type' and len(node.left.args) == 1
                and isinstance(node.left.args[0], ast.Name) and node.left.args[0].id == 'commit'):
            assert len(node.comparators) == 1 and isinstance(node.comparators[0], ast.Name)
            assert node.comparators[0].id == 'dict'
            node.comparators[0] = ast.Name('__header_type', ast.Load())
        return self.generic_visit(node)


def _build_factory(rewrite=None):
    tree = ast.parse(_SOURCE)
    cls = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == '_Files')
    function = next(node for node in cls.body if isinstance(node, ast.FunctionDef) and node.name == '_load')
    loops = [node for node in function.body if isinstance(node, ast.For)]
    assert len(loops) == 2
    first, second = loops
    expected = "commit, _ = self._blob(digest, LIMITS['metadata_bytes'])"
    assert ast.unparse(first.body[0]) == ast.unparse(second.body[0]) == expected
    validation = first.body[1]
    assert isinstance(validation, ast.Expr) and isinstance(validation.value, ast.Call)
    assert ast.unparse(validation.value.func) == '_need'
    native_validation = _HeaderCondition().visit(ast.parse(ast.unparse(validation)).body[0])
    branch = ast.If(ast.Attribute(ast.Name('__chain_read', ast.Load()), 'retained', ast.Load()),
        [native_validation], [validation])
    first.body[:2] = [*ast.parse("__chain_read = __scope.chain(self, digest, LIMITS['metadata_bytes'])\ncommit = __chain_read.value").body, branch]
    assert ast.unparse(first.body[-1]) == "digest = commit['parent_commit_sha256']"
    first.body[-1] = ast.parse("digest = commit.parent_commit_sha256 if __chain_read.retained else commit['parent_commit_sha256']").body[0]
    second.body[0] = ast.parse("commit = __scope.materialise(__scope.commit(self, digest, LIMITS['metadata_bytes']))").body[0]
    if rewrite is not None:
        rewrite(function)
    factory = ast.parse('def factory(__scope, __header_type):\n    pass\n').body[0]
    factory.body = [function, ast.Return(ast.Name('_load', ast.Load()))]
    module = ast.fix_missing_locations(ast.Module([factory], []))
    code = compile(module, 'research-solar-two-read-adapter', 'exec', dont_inherit=True)
    factory_code = next(value for value in code.co_consts if type(value) is types.CodeType)
    return types.FunctionType(factory_code, vars(storage))


_FACTORY = _build_factory() if _SOURCE_APPROVED else None


def _native_entry(reader):
    try:
        if not any(getattr_static(reader, '_load') is fn for fn in (_ORIGINAL_LOAD, load)):
            return False
        return (_attested(_ORIGINAL_LOAD, '_Files._load')
            and all(_attested(getattr_static(reader, name), '_Files.'+name)
                    for name in ('_load_header', '_records'))
            and _attested(storage._need, '_need'))
    except (AttributeError, TypeError, ValueError):
        return False


def load(self, head, *, audit=None):
    """Return the native complete tuple; audit contains counters, never trees."""
    if audit is not None and type(audit) is not dict:
        raise ValueError('exact research audit dictionary required')
    if not _native_entry(self):
        if audit is not None:
            audit.update(whole_load_fallback=True, cache_hits=0, disposed=True,
                         raw_bytes_after_close=0, peak_raw_bytes=0)
        method = self._load
        if type(method) is types.MethodType and method.__func__ is load:
            return _ORIGINAL_LOAD(self, head)
        return method(head)
    scope = core.OwnedJSONScope(hash_binding=(storage, '_hash'))
    try:
        with scope:
            return _FACTORY(scope, core.ChainHeader)(self, head)
    finally:
        if audit is not None:
            audit.update(whole_load_fallback=False, cache_hits=scope.cache_hits,
                         fallbacks=scope.fallbacks, peak_raw_bytes=scope.peak_raw_bytes,
                         raw_bytes_after_close=scope.raw_bytes, disposed=scope._closed)
