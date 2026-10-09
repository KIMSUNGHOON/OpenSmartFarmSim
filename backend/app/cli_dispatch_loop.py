"""Poll one fixed authority endpoint; stop immediately on an unresolved exchange."""

from dataclasses import asdict
import sys
from threading import Event

from .authority_rpc import AuthorityClient, AuthorityDispatchError, _result
from .cli_dispatch import _Arguments, _emit
from .process_stop import process_stop


class AuthorityDispatchLoop:
    def __init__(self, client, *, poll_seconds=1):
        if (type(client) is not AuthorityClient or type(poll_seconds) is not int or
                not 1 <= poll_seconds <= 60):
            raise ValueError('dispatcher loop configuration rejected')
        AuthorityClient(client.socket_path, authority_uid=client.authority_uid,
                        tenant_id=client.tenant_id, wait_seconds=client.wait_seconds)
        self.client, self.poll_seconds = client, poll_seconds
        self._bound = (client, client.socket_path, client.authority_uid,
                       client.tenant_id, client.wait_seconds, poll_seconds)

    def _binding(self):
        client = self.client
        if (type(client) is not AuthorityClient or type(self.poll_seconds) is not int or
                type(client.authority_uid) is not int or type(client.wait_seconds) is not int or
                type(client.tenant_id) is not str or
                (client, client.socket_path, client.authority_uid, client.tenant_id,
                 client.wait_seconds, self.poll_seconds) != self._bound):
            raise AuthorityDispatchError('authority dispatch unresolved')

    def run(self, stop_event, *, emit):
        if not isinstance(stop_event, Event) or not callable(emit):
            raise AuthorityDispatchError('authority dispatch unresolved')
        while not stop_event.is_set():
            self._binding()
            result = self.client.run_once()
            self._binding()
            if result is not None:
                try:
                    public = asdict(result)
                    for name in ('job_id', 'capture_id', 'decision_id'):
                        public[name] = str(public[name]) if public[name] is not None else None
                    _result(public)
                except Exception:
                    raise AuthorityDispatchError('authority dispatch unresolved') from None
                emit({'version': 1, 'event': 'dispatch', 'tenant_id': self.client.tenant_id,
                      'result': public})
                if public['state'] == 'unclosed':
                    raise AuthorityDispatchError('authority dispatch unresolved')
            if not stop_event.is_set():
                stop_event.wait(self.poll_seconds)


def main(argv=None):
    parser = _Arguments(prog='ossf-dispatch-loop', description='Poll one fixed authority endpoint.')
    parser.add_argument('--socket', required=True)
    parser.add_argument('--authority-uid', type=int, required=True)
    parser.add_argument('--tenant', required=True)
    parser.add_argument('--wait-seconds', type=int, default=660)
    parser.add_argument('--poll-seconds', type=int, default=1)
    try:
        args = parser.parse_args(argv)
        client = AuthorityClient(args.socket, authority_uid=args.authority_uid,
                                 tenant_id=args.tenant, wait_seconds=args.wait_seconds)
        loop = AuthorityDispatchLoop(client, poll_seconds=args.poll_seconds)
    except Exception:
        _emit({'version': 1, 'ok': False, 'code': 'dispatcher_loop_configuration_rejected'}, sys.stderr)
        return 2
    try:
        with process_stop() as stop:
            _emit({'version': 1, 'event': 'started'}, sys.stdout)
            try:
                loop.run(stop, emit=lambda value: _emit(value, sys.stdout))
            except Exception:
                _emit({'version': 1, 'ok': False, 'code': 'authority_dispatch_unresolved'}, sys.stderr)
                return 3
            _emit({'version': 1, 'event': 'stopped'}, sys.stdout)
            return 0
    except Exception:
        _emit({'version': 1, 'ok': False, 'code': 'dispatcher_loop_configuration_rejected'}, sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
