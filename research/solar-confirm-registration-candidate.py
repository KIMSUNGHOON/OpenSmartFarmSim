"""Unadopted confirm-local registration lifetime experiment; no product imports."""
import ast
from contextlib import contextmanager
import inspect
from pathlib import Path
import textwrap

from app import crop_greenhouse_solar_execution_checkpoint as checkpoints
from app import farm_registration_read_scope as registration

custody = checkpoints.custody


@contextmanager
def _confirm_scope(store, tenant, value):
    # The original first-current guard still runs in the original method body.
    store._guard(tenant)
    farms = store.admission.binding.farms
    ref = value['request']['farm']
    with farms.registration_read_scope(tenant, ref['scenario_id'], ref['scenario_revision'],
                                      ref['registration_sha256']):
        yield


def _registration_lifetime(server, lifetime, tenant, ref, join):
    farms = server.binding.farms
    if not join:
        return lifetime.enter_context(farms.registration_read_scope(tenant,
            ref['scenario_id'], ref['scenario_revision'], ref['registration_sha256']))
    owner = farms._registration_read.get()
    custody._need(type(owner) is registration.RegistrationRead and owner.owner is farms
        and owner.args == (tenant, ref['scenario_id'], ref['scenario_revision'], ref['registration_sha256'])
        and owner.active and not owner.failed and not owner.loading
        and owner.slot is farms._registration_read and owner.execution == registration._execution())
    owner._guard()


def _clone(method, module, edit):
    tree = ast.parse(textwrap.dedent(inspect.getsource(method)))
    assert len(tree.body) == 1 and isinstance(tree.body[0], ast.FunctionDef)
    edit(tree.body[0])
    ast.fix_missing_locations(tree)
    local = {}
    exec(compile(tree, str(Path(__file__)), 'exec'), module.__dict__, local)
    return local[tree.body[0].name]


def _edit_confirm(node):
    outer = node.body[0]
    assert isinstance(outer, ast.Try)
    connection = next(s for s in outer.body if isinstance(s, ast.With))
    assert isinstance(connection.body[2], ast.Expr)
    assert ast.unparse(connection.body[2].value.func) == 'self._current'
    scope = ast.With(items=[ast.withitem(context_expr=ast.parse(
        '_research_confirm_registration_scope(self, tenant, value)', mode='eval').body)],
        body=connection.body[2:])
    connection.body = connection.body[:2] + [scope]


def _edit_session(node):
    scope = next(s for s in node.body if isinstance(s, ast.With))
    call = scope.items[0].context_expr
    assert ast.unparse(call.func) == 'self.server._open'
    call.keywords.append(ast.keyword(arg='_join_registration_scope', value=ast.Constant(True)))


def _edit_open(node):
    node.args.kwonlyargs.append(ast.arg(arg='_join_registration_scope'))
    node.args.kw_defaults.append(ast.Constant(False))
    node.body.insert(2, ast.parse('_need(type(_join_registration_scope) is bool and '
        '(not _join_registration_scope or write is False))').body[0])
    replaced = []
    for item in ast.walk(node):
        if not isinstance(item, ast.Expr) or not isinstance(item.value, ast.Call):
            continue
        if ast.unparse(item.value.func) == 'lifetime.enter_context':
            item.value = ast.parse('_research_registration_lifetime(self, lifetime, '
                'tenant, ref, _join_registration_scope)', mode='eval').body
            replaced.append(True)
    assert len(replaced) == 1


def install(patch):
    """Apply only inside the explicit research test's monkeypatch context."""
    confirm = _clone(checkpoints.SolarExecutionCheckpointStore.confirm, checkpoints, _edit_confirm)
    session = _clone(checkpoints.SolarExecutionCheckpointStore._session, checkpoints, _edit_session)
    opened = _clone(custody.SolarServerCustody._open, custody, _edit_open)
    patch.setattr(checkpoints, '_research_confirm_registration_scope', _confirm_scope, raising=False)
    patch.setattr(custody, '_research_registration_lifetime', _registration_lifetime, raising=False)
    patch.setattr(checkpoints.SolarExecutionCheckpointStore, 'confirm', confirm)
    patch.setattr(checkpoints.SolarExecutionCheckpointStore, '_session', session)
    patch.setattr(custody.SolarServerCustody, '_open', opened)
