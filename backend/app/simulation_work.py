"""Foreground execution of one job from an operator-controlled authority factory."""

import argparse
from dataclasses import asdict
import importlib
import json
import re
import sys
from uuid import UUID

from .thermal_simulation_worker import ThermalSimulationWorker


class _Arguments(argparse.ArgumentParser):
    def error(self, _message):
        raise ValueError('simulation configuration rejected')


def _emit(value, stream):
    print(json.dumps(value, sort_keys=True, separators=(',', ':'),
        ensure_ascii=True, allow_nan=False), file=stream, flush=True)


def main(argv=None):
    parser = _Arguments(prog='ossf-simulation', description='Execute one operator-configured thermal job.')
    parser.add_argument('--factory', required=True)
    parser.add_argument('--job-id', required=True)
    try:
        args = parser.parse_args(argv)
        if (not re.fullmatch(r'[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*:[A-Za-z_]\w*', args.factory, flags=re.ASCII)
                or str(UUID(args.job_id)) != args.job_id):
            raise ValueError()
        module, attribute = args.factory.split(':')
        worker = getattr(importlib.import_module(module), attribute)()
        if type(worker) is not ThermalSimulationWorker:
            raise TypeError()
    except (Exception, SystemExit):
        _emit({'version': 1, 'ok': False, 'code': 'simulation_startup_rejected'}, sys.stderr)
        return 2
    try:
        result = worker.run_once(args.job_id)
        if result is not None and result.state == 'unclosed':
            raise ValueError()
    except Exception:
        _emit({'version': 1, 'ok': False, 'code': 'simulation_execution_unresolved'}, sys.stderr)
        return 3
    public = asdict(result) if result is not None else None
    if public is not None:
        public['job_id'] = str(public['job_id'])
    _emit({'version': 1, 'ok': True, 'result': public}, sys.stdout)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
