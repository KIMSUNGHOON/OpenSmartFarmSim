"""One authority RPC request, with no database/CLI credential or automatic retry."""

import argparse
from dataclasses import asdict
import json
import sys

from .authority_rpc import AuthorityClient, AuthorityDispatchError


class _Arguments(argparse.ArgumentParser):
    def error(self, _message):
        # Native parser errors can echo an accidentally supplied credential argument.
        raise ValueError("dispatcher configuration rejected")


def _emit(value, stream):
    print(json.dumps(value, sort_keys=True, separators=(",", ":"),
                     ensure_ascii=True, allow_nan=False), file=stream, flush=True)


def main(argv=None):
    parser = _Arguments(prog="ossf-dispatch", description="Request one scoped authority dispatch.")
    parser.add_argument("--socket", required=True)
    parser.add_argument("--authority-uid", type=int, required=True)
    parser.add_argument("--tenant", required=True)
    parser.add_argument("--wait-seconds", type=int, default=660)
    try:
        args = parser.parse_args(argv)
        client = AuthorityClient(args.socket, authority_uid=args.authority_uid,
                                 tenant_id=args.tenant, wait_seconds=args.wait_seconds)
    except ValueError:
        _emit({"version": 1, "ok": False, "code": "dispatcher_configuration_rejected"}, sys.stderr)
        return 2
    try:
        result = client.run_once()
    except AuthorityDispatchError:
        _emit({"version": 1, "ok": False, "code": "authority_dispatch_unresolved"}, sys.stderr)
        return 3
    public = asdict(result) if result is not None else None
    if public is not None:
        for key in ("job_id", "capture_id", "decision_id"):
            public[key] = str(public[key]) if public[key] is not None else None
    _emit({"version": 1, "ok": True, "tenant_id": args.tenant, "result": public}, sys.stdout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
