"""Query instrumentation without importing agricultural test fixtures."""
from app import crop_greenhouse_ventilation_input_evidence as inputs
from app import crop_greenhouse_ventilation_execution_query as query
from contextlib import contextmanager
from contextvars import ContextVar
from functools import wraps

_current = ContextVar('synthetic_query_audit', default=None)


def targets():
    c = inputs.continuation
    targets = [(c, 'prepare_context', 'prepare_context'), (c, 'start', 'start'),
        (c, 'restore_checkpoint', 'restore'), (c, 'advance_chunk', 'advance'),
        (inputs.joint, 'evaluate_rhs', 'RHS'), (c.driver.stage, 'integrate', 'step'),
        (c.driver.previous.management, 'apply_management', 'event'),
        (inputs.clock, 'prepare_binding', 'prepare_binding'),
        (c.driver.stage.vent, 'calculate_ventilation', 'ventilation'),
        (query.checkpoints.VentilationExecutionCheckpointStore, 'confirm', 'confirm'),
        (query.custody.VentilationServerCustody, 'advance', 'custody.advance'),
        (query.storage.VentilationResultStore, 'put', 'put'),
        (query.storage.VentilationResultStore, '_put_in_transaction', '_put_in_transaction')]
    targets += [(query.checkpoints.execution.JobStore, name, 'jobs.'+name) for name in
        ('submit', 'claim', 'renew', 'fail', 'cancel', 'ack_cancel', '_event', '_outcome',
         '_insert_publication', '_durable_artifact')]
    return targets


def forbid(patch):
    selected = targets()
    calls = {key: 0 for _, _, key in selected}
    def blocked(key):
        def fail(*args, **kwargs):
            calls[key] += 1
            raise AssertionError('query invoked '+key)
        return fail
    for target, name, key in selected: patch.setattr(target, name, blocked(key))
    return calls


def install(patch):
    for target, name, key in targets():
        original = getattr(target, name)
        def guarded(*args, _original=original, _key=key, **kwargs):
            calls = _current.get()
            if calls is not None:
                calls[_key] += 1
                raise AssertionError('query invoked '+_key)
            return _original(*args, **kwargs)
        patch.setattr(target, name, wraps(original)(guarded))


@contextmanager
def query_calls():
    calls = {key: 0 for _, _, key in targets()}
    token = _current.set(calls)
    try: yield calls
    finally: _current.reset(token)
