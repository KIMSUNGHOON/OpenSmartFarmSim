"""Run ownership tests beside a real preexisting multiprocessing resource tracker."""
import argparse
import gc
import importlib.util
import json
import os
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[1]


def run(directory, only_original_failure):
    import multiprocessing
    from multiprocessing import resource_tracker
    import pytest

    directory.mkdir(mode=0o700)
    spec = importlib.util.spec_from_file_location('shared_controller_identity',
        ROOT/'research/owned-research-process-scope.py')
    scope = importlib.util.module_from_spec(spec); spec.loader.exec_module(scope)
    semaphore = multiprocessing.get_context('spawn').Semaphore(1)
    tracker = resource_tracker._resource_tracker
    original = scope.identity(tracker._pid)
    deadline = time.monotonic() + 5
    while True:
        status = Path('/proc', str(original.pid), 'status').read_text()
        ignored = int(next(line.split()[1] for line in status.splitlines() if line.startswith('SigIgn:')), 16)
        if ignored & (1 << 14): break
        assert time.monotonic() < deadline; time.sleep(.01)
    command = Path('/proc', str(original.pid), 'cmdline').read_bytes()
    assert b'multiprocessing.resource_tracker' in command and scope.live(original)
    started = {'controller': scope.identity(os.getpid())._asdict(), 'tracker': original._asdict(),
        'tracker_SIGTERM_ignored': True, 'same_Python_pytest_controller': True}
    (directory/'started.private.json').write_text(json.dumps(started)); (directory/'started.private.json').chmod(0o400)
    reports = []
    class Reports:
        def pytest_runtest_logreport(self, report):
            if report.when == 'call': reports.append({'nodeid': report.nodeid, 'outcome': report.outcome})
    options = ['-q', '-p', 'no:cacheprovider', '--tb=short',
        str(ROOT/'backend/tests/test_owned_research_process_scope.py'), '--basetemp', str(directory/'pytest')]
    if only_original_failure: options += ['-k', 'cleanup_preserves_entire_protected_tree_and_stops_only_owned']
    try:
        code = int(pytest.main(options, plugins=[Reports()]))
        preserved = scope.live(original)
    finally:
        del semaphore; gc.collect(); tracker._stop()
    result = {'actual_pytest_exit': code, 'tracker_original_identity_preserved': preserved,
        'tracker_gone_after_owned_stdlib_stop': not scope.live(original), 'reports': reports,
        'same_Python_pytest_controller': True, 'actual_crop_Runs': 0, 'G0_G4': 'not_assessed'}
    (directory/'result.private.json').write_text(json.dumps(result)); (directory/'result.private.json').chmod(0o400)
    assert preserved and result['tracker_gone_after_owned_stdlib_stop']
    return code


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--directory', type=Path, required=True)
    parser.add_argument('--only-original-failure', action='store_true')
    args = parser.parse_args()
    return run(args.directory, args.only_original_failure)


if __name__ == '__main__': raise SystemExit(main())
