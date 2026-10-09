"""Measure the original farm input helper; no farm authority or crop execution."""
from argparse import ArgumentParser
from datetime import datetime, timezone
from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path
import resource
from time import perf_counter, process_time
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument('--supervision', type=Path, required=True)
    parser.add_argument('--supervision-sha256', required=True)
    parser.add_argument('--cli-context', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('new own observation output required')
    cli = json.loads(args.cli_context.read_bytes())
    assert cli['model'] == 'gpt-6.1-sol' and cli['effort'] == 'xhigh'
    assert cli['recursive_cli_invocations'] == 0
    raw = args.supervision.read_bytes()
    assert sha256(raw).hexdigest() == args.supervision_sha256
    supervision = json.loads(raw)
    pins = supervision['source_sha256']

    def unchanged():
        assert sha256(args.supervision.read_bytes()).hexdigest() == args.supervision_sha256
        assert all(sha256((ROOT / p).read_bytes()).hexdigest() == h for p, h in pins.items())

    unchanged()
    driver = load('own_farm_input_cost_driver', ROOT / 'research/crop-cycle-full-rhs-reference.py')
    reference = load('own_farm_input_cost_profiles', ROOT / 'research/crop-cycle-stream-execution-reference.py')
    profiles = reference.profiles()
    run = args.supervision.parent / 'run'
    spec = driver.read_spec(run, supervision['spec_sha256'], profiles,
                            (ROOT / 'LICENSES/GreenLight-BSD-3-Clause-Clear.txt').read_bytes())
    from app.crop_cycle_farm_binding import CycleFarmBinding
    inputs = driver.inputs
    evaluator = driver.engine.short._Evaluator
    original_rhs = evaluator.rhs
    rhs_calls = 0

    def forbidden_rhs(*args, **kwargs):
        nonlocal rhs_calls
        rhs_calls += 1
        raise AssertionError('input helper measurement must not calculate crop states')

    before = len(os.listdir('/proc/self/fd'))
    evaluator.rhs = forbidden_rhs
    measurements = []
    tick, cpu = perf_counter(), process_time()
    try:
        open_tick, open_cpu = perf_counter(), process_time()
        reader = inputs.open_input_packet(run / 'inputs', spec['input_root_sha256'], **profiles)
        open_cost = {'wall_seconds': perf_counter() - open_tick, 'cpu_seconds': process_time() - open_cpu}
        with reader:
            assert reader.plan == spec['plan']
            root_before = inputs._canonical(reader.manifest)
            request = {'input': {'root_sha256': reader.root_sha256,
                                 'program_id': reader.manifest['program_id']}}
            # This dependency supplies profiles only: no constructor, farm, tenant, rights or DB claim.
            profile_provider = SimpleNamespace(_profiles=lambda: dict(profiles))
            for sequence in range(2):
                started, started_cpu = perf_counter(), process_time()
                value = CycleFarmBinding._input(profile_provider, request, reader)
                measurements.append({'sequence': sequence + 1, 'wall_seconds': perf_counter() - started,
                                     'cpu_seconds': process_time() - started_cpu,
                                     'source': value, 'source_sha256': sha256(inputs._canonical(value)).hexdigest()})
                assert inputs._canonical(reader.manifest) == root_before and reader.plan == spec['plan']
                print(json.dumps({'phase': 'original_farm_input_helper', 'sequence': sequence + 1,
                                  'wall_seconds': measurements[-1]['wall_seconds'], 'rhs_calls': rhs_calls}), flush=True)
        assert measurements[0]['source'] == measurements[1]['source']
    finally:
        evaluator.rhs = original_rhs
    assert rhs_calls == 0 and evaluator.rhs is original_rhs
    after = len(os.listdir('/proc/self/fd'))
    assert before == after
    unchanged()
    source_paths = [Path(__file__), ROOT / 'backend/app/crop_cycle_farm_binding.py',
                    ROOT / 'research/crop-cycle-stream-execution-reference.py']
    result = {
        'evidence_version': 'crop-cycle-farm-input-helper-cost-v1',
        'recorded_at_utc': datetime.now(timezone.utc).isoformat(),
        'scope': 'isolated original _input helper on actual owned synthetic full166 input; not farm authority',
        'actual_cli_context': cli,
        'source_sha256': {str(p.relative_to(ROOT)): sha256(p.read_bytes()).hexdigest() for p in source_paths},
        'frozen_dependency_sha256': pins,
        'supervision_sha256': args.supervision_sha256, 'spec_sha256': supervision['spec_sha256'],
        'input_root_sha256': spec['input_root_sha256'], 'plan': spec['plan'],
        'initial_original_preflight': open_cost, 'helper_measurements': measurements,
        'same_source_and_original_plan': True, 'observed_rhs_calls': rhs_calls,
        'descriptors_before': before, 'descriptors_after': after,
        'wall_seconds': perf_counter() - tick, 'cpu_seconds': process_time() - cpu,
        'effective_nice': os.getpriority(os.PRIO_PROCESS, 0),
        'process_peak_rss_bytes': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024,
        'cache_condition': 'not controlled; initial preflight precedes both helper calls; this packet is used by a live worker',
        'concurrency': 'one independent nice19 read-only probe alongside existing nice15 full166 worker',
        'excluded': ['CycleFarmBinding constructor/_bind/current', 'tenant/registration/current rights/DB',
                     'context preparation', 'artifact/custody/proof', 'HTTPS/3D'],
        'input_or_artifact_modified': False, 'full166_completed_by_this_probe': False,
        'program_tests_run': 0, 'gates': 'not_assessed',
    }
    driver.immutable(args.output, result)
    print(json.dumps({'phase': 'farm_input_helper_cost_complete', 'wall_seconds': result['wall_seconds'],
                      'observed_rhs_calls': rhs_calls, 'descriptors': [before, after]}), flush=True)


if __name__ == '__main__':
    main()
