"""Consume an explicitly configured deterministic queue in the foreground."""

import argparse
import importlib
import json
import os
import re
import select
import signal
import sys
from threading import Event
import time
from uuid import UUID

from .break_even_calculation_worker import BreakEvenCalculationWorker, BreakEvenCalculationOutcome
from .break_even_verification_worker import BreakEvenVerificationWorker, BreakEvenVerificationOutcome
from .deterministic_job_discovery import DeterministicJobDiscovery
from .economic_calculation_worker import EconomicCalculationWorker, EconomicCalculationOutcome
from .jobs import require_reason_code, require_seconds


WORKERS = {
    EconomicCalculationWorker: (frozenset({'economic-calculation-input-v1',
        'economic-calculation-input-v2', 'economic-calculation-input-v3'}), EconomicCalculationOutcome),
    BreakEvenCalculationWorker: (frozenset({'break-even-calculation-input-v1'}), BreakEvenCalculationOutcome),
    BreakEvenVerificationWorker: (frozenset({'break-even-verification-input-v1'}), BreakEvenVerificationOutcome),
}


class LoopHold(ValueError):
    """The consumer cannot safely continue its configured execution."""


class DeterministicWorkerLoop:
    def __init__(self, worker, *, input_versions, poll_seconds=1, page_size=25):
        try:
            require_seconds(poll_seconds, 'poll_seconds', maximum=60)
            require_seconds(page_size, 'page_size', maximum=50)
            if (type(poll_seconds) is not int or type(page_size) is not int or
                    type(worker) not in WORKERS or type(input_versions) is not frozenset or
                    not input_versions or not input_versions <= WORKERS[type(worker)][0]):
                raise ValueError
            self.worker = worker
            self.poll_seconds, self.page_size = poll_seconds, page_size
            self.discovery = DeterministicJobDiscovery(worker.jobs, tenant_id=worker.tenant_id,
                                                       input_versions=input_versions)
            self._bound = (worker, self.discovery, poll_seconds, page_size)
            self._binding()
        except Exception:
            raise LoopHold('deterministic_binding_rejected') from None

    def _binding(self):
        try:
            worker, discovery, poll, size = self._bound
            if (self.worker is not worker or self.discovery is not discovery or
                    self.poll_seconds != poll or self.page_size != size or
                    worker.jobs is not discovery.jobs or worker.tenant_id != discovery.tenant_id):
                raise ValueError
            discovery._binding()
            if type(worker) is EconomicCalculationWorker:
                if (('economic-calculation-input-v2' in discovery.input_versions and
                        worker.farm_scenario_service is None) or
                        ('economic-calculation-input-v3' in discovery.input_versions and
                         (worker.farm_scenario_service is None or worker.authored_run_store is None))):
                    raise ValueError
            if type(worker) is BreakEvenVerificationWorker:
                worker._guard(worker.service.authority.plans._pointers(), worker.service._digests())
            else:
                worker._binding()
        except Exception:
            raise LoopHold('deterministic_binding_rejected') from None

    def _event(self, result, job):
        try:
            if (type(result) is not WORKERS[type(self.worker)][1] or result.job_id != UUID(job.job_id) or
                    type(result.attempt) is not int or not 1 <= result.attempt <= 3 or
                    result.state not in ('queued', 'succeeded', 'failed', 'hold', 'canceled')):
                raise ValueError
            require_reason_code(result.reason_code)
            return {'version': 1, 'event': 'attempt', 'job_id': job.job_id,
                    'attempt': result.attempt, 'state': result.state, 'reason_code': result.reason_code}
        except Exception:
            raise LoopHold('deterministic_outcome_rejected') from None

    def run(self, stop_event, *, emit):
        if not isinstance(stop_event, Event) or not callable(emit):
            raise LoopHold('deterministic_binding_rejected')
        cursor = None
        while not stop_event.is_set():
            self._binding()
            page = self.discovery.page(cursor=cursor, limit=self.page_size)
            for job in page.jobs:
                if stop_event.is_set():
                    break
                self._binding()
                result = self.worker.run_once(job.job_id)
                if result is not None:
                    emit(self._event(result, job))
            cursor = page.next_cursor
            if not stop_event.is_set():
                stop_event.wait(self.poll_seconds)


class _Arguments(argparse.ArgumentParser):
    def error(self, _message):
        raise ValueError('deterministic configuration rejected')


class _SignalStop(Event):
    """Main-thread stop flag with a nonblocking signal wakeup pipe."""

    def __init__(self):
        super().__init__()
        self.requested = False
        self.reader, self.writer = os.pipe2(os.O_NONBLOCK | os.O_CLOEXEC)

    def set(self):
        self.requested = True

    def is_set(self):
        return self.requested

    def wait(self, seconds):
        deadline = time.monotonic() + seconds
        while not self.requested:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            if select.select([self.reader], [], [], remaining)[0]:
                os.read(self.reader, 4096)
        return self.requested

    def close(self):
        os.close(self.reader)
        os.close(self.writer)


def _emit(value, stream):
    print(json.dumps(value, sort_keys=True, separators=(',', ':'),
        ensure_ascii=True, allow_nan=False), file=stream, flush=True)


def main(argv=None):
    parser = _Arguments(prog='ossf-deterministic', description='Consume one operator-configured deterministic queue.')
    parser.add_argument('--factory', required=True)
    try:
        args = parser.parse_args(argv)
    except (Exception, SystemExit) as error:
        if isinstance(error, SystemExit) and error.code == 0:
            return 0
        _emit({'version': 1, 'ok': False, 'code': 'deterministic_startup_rejected'}, sys.stderr)
        return 2
    stop, wakeup = None, None
    handlers = {}
    try:
        try:
            if not re.fullmatch(r'[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*:[A-Za-z_]\w*', args.factory, flags=re.ASCII):
                raise ValueError
            stop = _SignalStop()
            wakeup = signal.set_wakeup_fd(stop.writer, warn_on_full_buffer=False)
            for sig in (signal.SIGTERM, signal.SIGINT):
                handlers[sig] = signal.signal(sig, lambda *_: stop.set())
            module, attribute = args.factory.split(':')
            loop = getattr(importlib.import_module(module), attribute)()
            if type(loop) is not DeterministicWorkerLoop:
                raise ValueError
            loop._binding()
        except (Exception, SystemExit):
            _emit({'version': 1, 'ok': False, 'code': 'deterministic_startup_rejected'}, sys.stderr)
            return 2
        try:
            _emit({'version': 1, 'event': 'started'}, sys.stdout)
            loop.run(stop, emit=lambda value: _emit(value, sys.stdout))
            _emit({'version': 1, 'event': 'stopped'}, sys.stdout)
            return 0
        except Exception:
            _emit({'version': 1, 'ok': False, 'code': 'deterministic_execution_unresolved'}, sys.stderr)
            return 3
    finally:
        for sig, handler in handlers.items():
            signal.signal(sig, handler)
        if wakeup is not None:
            signal.set_wakeup_fd(wakeup)
        if stop is not None:
            stop.close()


if __name__ == '__main__':
    # Operator factories import this public class from the canonical module.
    from app.deterministic_work import main as entry_main
    raise SystemExit(entry_main())
