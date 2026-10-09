"""Consume the explicitly configured owned collection queue in the foreground."""

import argparse
import importlib
import json
import re
import sys
from threading import Event
from uuid import UUID

from .deterministic_job_discovery import CollectionJobDiscovery
from .jobs import require_reason_code, require_seconds
from .owned_fixture_collection import CollectionService, CollectionWorker, CollectionOutcome
from .process_stop import process_stop


class CollectionLoopHold(ValueError):
    """The configured consumer cannot safely continue."""


class CollectionWorkerLoop:
    def __init__(self, worker, *, poll_seconds=1, page_size=25):
        try:
            require_seconds(poll_seconds, 'poll_seconds', maximum=60)
            require_seconds(page_size, 'page_size', maximum=50)
            if (type(worker) is not CollectionWorker or type(worker.service) is not CollectionService or
                    type(poll_seconds) is not int or
                    type(page_size) is not int or type(worker.lease_seconds) is not int):
                raise ValueError
            require_seconds(worker.lease_seconds, 'lease_seconds')
            worker.service._binding()
            self.worker = worker
            self.poll_seconds, self.page_size = poll_seconds, page_size
            self.discovery = CollectionJobDiscovery(worker.service.jobs, tenant_id=worker.tenant_id)
            self._bound = (worker, worker.service, worker.service._pointers(), worker.tenant_id,
                           worker.lease_seconds, self.discovery, poll_seconds, page_size)
            self._binding()
        except Exception:
            raise CollectionLoopHold('collection_consumer_binding_rejected') from None

    def _binding(self):
        try:
            worker, service, pointers, tenant, lease, discovery, poll, size = self._bound
            if (self.worker is not worker or worker.service is not service or
                    worker.tenant_id != tenant or type(worker.lease_seconds) is not int or
                    worker.lease_seconds != lease or self.discovery is not discovery or
                    type(self.poll_seconds) is not int or self.poll_seconds != poll or
                    type(self.page_size) is not int or self.page_size != size or
                    discovery.jobs is not service.jobs or discovery.tenant_id != tenant):
                raise ValueError
            discovery._binding()
            service._guard(tenant, pointers)
        except Exception:
            raise CollectionLoopHold('collection_consumer_binding_rejected') from None

    @staticmethod
    def _event(result, job):
        try:
            if (type(result) is not CollectionOutcome or type(result.job_id) is not UUID or
                    result.job_id != UUID(job.job_id) or type(result.attempt) is not int or
                    not 1 <= result.attempt <= 3 or
                    result.state not in ('queued', 'succeeded', 'failed', 'hold', 'canceled')):
                raise ValueError
            require_reason_code(result.reason_code)
            return {'version':1, 'event':'attempt', 'job_id':job.job_id,
                    'attempt':result.attempt, 'state':result.state, 'reason_code':result.reason_code}
        except Exception:
            raise CollectionLoopHold('collection_consumer_outcome_rejected') from None

    def run(self, stop_event, *, emit):
        if not isinstance(stop_event, Event) or not callable(emit):
            raise CollectionLoopHold('collection_consumer_binding_rejected')
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
        raise ValueError('collection consumer configuration rejected')


def _emit(value, stream):
    print(json.dumps(value, sort_keys=True, separators=(',', ':'),
        ensure_ascii=True, allow_nan=False), file=stream, flush=True)


def main(argv=None):
    parser = _Arguments(prog='ossf-collection-consume', description='Consume one operator-configured collection queue.')
    parser.add_argument('--factory', required=True)
    try:
        args = parser.parse_args(argv)
    except (Exception, SystemExit) as error:
        if isinstance(error, SystemExit) and error.code == 0:
            return 0
        _emit({'version':1, 'ok':False, 'code':'collection_consumer_startup_rejected'}, sys.stderr)
        return 2
    try:
        with process_stop() as stop:
            try:
                if not re.fullmatch(r'[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*:[A-Za-z_]\w*', args.factory, flags=re.ASCII):
                    raise ValueError
                module, attribute = args.factory.split(':')
                loop = getattr(importlib.import_module(module), attribute)()
                if type(loop) is not CollectionWorkerLoop:
                    raise ValueError
                loop._binding()
            except (Exception, SystemExit):
                _emit({'version':1, 'ok':False, 'code':'collection_consumer_startup_rejected'}, sys.stderr)
                return 2
            try:
                _emit({'version':1, 'event':'started'}, sys.stdout)
                loop.run(stop, emit=lambda value:_emit(value, sys.stdout))
                _emit({'version':1, 'event':'stopped'}, sys.stdout)
                return 0
            except Exception:
                _emit({'version':1, 'ok':False, 'code':'collection_consumer_execution_unresolved'}, sys.stderr)
                return 3
    except Exception:
        _emit({'version':1, 'ok':False, 'code':'collection_consumer_startup_rejected'}, sys.stderr)
        return 2


if __name__ == '__main__':
    from app.collection_consume import main as entry_main
    raise SystemExit(entry_main())
