"""Foreground authority entrypoint for an operator-controlled application factory."""

import argparse
import importlib
import json
import re
import sys

from .authority_rpc import AuthorityServer


class _Arguments(argparse.ArgumentParser):
    def error(self, _message):
        raise ValueError("authority configuration rejected")


def _error(code):
    print(json.dumps({"version": 1, "ok": False, "code": code},
                     sort_keys=True, separators=(",", ":")), file=sys.stderr, flush=True)


def main(argv=None):
    parser = _Arguments(prog="ossf-authority", description="Serve an operator-configured CLI authority.")
    parser.add_argument("--factory", required=True)
    parser.add_argument("--max-sessions", type=int)
    try:
        args = parser.parse_args(argv)
        if (not re.fullmatch(r"[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*:[A-Za-z_]\w*", args.factory,
                             flags=re.ASCII) or
                (args.max_sessions is not None and args.max_sessions < 1)):
            raise ValueError("invalid authority configuration")
        module, attribute = args.factory.split(":")
        server = getattr(importlib.import_module(module), attribute)()
        if type(server) is not AuthorityServer:
            raise TypeError("configured authority required")
    except Exception:
        _error("authority_startup_rejected")
        return 2
    try:
        server.serve(max_sessions=args.max_sessions)
    except Exception:
        _error("authority_service_failed")
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
