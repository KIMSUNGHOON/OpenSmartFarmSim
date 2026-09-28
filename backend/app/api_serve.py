"""Foreground entrypoint for an operator-assembled HTTPS API."""

import argparse
import importlib
import json
import re
import sys

from .https_service import HttpsApiService


class _Arguments(argparse.ArgumentParser):
    def error(self, _message):
        raise ValueError("API arguments rejected")


def _error(code):
    print(json.dumps({"version": 1, "ok": False, "code": code},
                     sort_keys=True, separators=(",", ":")), file=sys.stderr, flush=True)


def main(argv=None):
    parser = _Arguments(prog="ossf-api", description="Serve an operator-assembled HTTPS API.")
    parser.add_argument("--factory", required=True)
    try:
        args = parser.parse_args(argv)
        if not re.fullmatch(r"[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*:[A-Za-z_]\w*", args.factory, flags=re.ASCII):
            raise ValueError()
    except Exception:
        _error("api_startup_rejected")
        return 2
    try:
        module, attribute = args.factory.split(":")
        service = getattr(importlib.import_module(module), attribute)()
        if type(service) is not HttpsApiService:
            raise TypeError()
    except (Exception, SystemExit):
        _error("api_startup_rejected")
        return 2
    try:
        service.serve()
    except (Exception, SystemExit):
        _error("api_service_failed")
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
