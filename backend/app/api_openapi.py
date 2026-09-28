"""Export/check implemented route schemas without operational dependencies or reads."""

import argparse
import json
from pathlib import Path
import sys

from .api import create_app
from .http_identity import current_principal


CONTRACT_PATH = Path(__file__).resolve().parents[2]/"contracts"/"openapi-v1.json"


class _SchemaOnlyStores:
    def _refuse(self, *_args):
        raise RuntimeError("schema-only store cannot serve requests")
    get_job = get_public_report = get_run = get_snapshot = get_economic_result = _refuse


def contract_document():
    stores = _SchemaOnlyStores()
    return create_app(stores, stores, stores, stores, principal_provider=current_principal).openapi()


def contract_bytes():
    return (json.dumps(contract_document(), sort_keys=True, indent=2, ensure_ascii=False,
                       allow_nan=False)+"\n").encode("utf-8")


def main(argv=None):
    parser = argparse.ArgumentParser(prog="ossf-openapi")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true")
    group.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    try:
        raw = contract_bytes()
        if args.write:
            CONTRACT_PATH.write_bytes(raw)
        elif CONTRACT_PATH.read_bytes() != raw:
            raise ValueError()
    except Exception:
        print('{"ok":false,"code":"openapi_contract_unavailable_or_changed"}', file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
