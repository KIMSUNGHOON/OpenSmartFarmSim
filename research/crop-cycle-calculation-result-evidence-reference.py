"""Owned verified-result proof issuance and fresh Python checks, without a farm claim."""
from argparse import ArgumentParser
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path
import resource
import subprocess
import sys
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'backend'))
from app import crop_cycle_calculation_result_evidence as evidence

spec = importlib.util.spec_from_file_location('owned_stream_reference', ROOT/'research/crop-cycle-stream-execution-reference.py')
reference = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reference)
engine, artifact, inputs, files = evidence.calculation, evidence.artifact, evidence.inputs, evidence.files
NOTICE = (ROOT/'LICENSES/GreenLight-BSD-3-Clause-Clear.txt').read_bytes()
SOURCE = Path(__file__).resolve()


def canonical(value):
    return inputs._canonical(value)


def digest(value):
    return sha256(canonical(value)).hexdigest()


def save(path, raw):
    with Path(path).open('xb') as handle:
        os.chmod(path, 0o400)
        handle.write(raw); handle.flush(); os.fsync(handle.fileno())


def authority(archive):
    archive = Path(archive)
    source = evidence.input_evidence.InputEvidenceAuthority(reference.profiles(), NOTICE,
        integrity_key=(archive/'input.key').read_bytes(), issuer_id='owned-verified-result-input', key_id='input-v1')
    return evidence.CalculationResultEvidenceAuthority(source,
        integrity_key=(archive/'result.key').read_bytes(), issuer_id='owned-verified-result-proof', key_id='result-v1')


def program(held):
    value = reference.long_program()
    start = engine.physical._utc(value['segments'][0]['start'])
    value['segments'] = value['segments'][:60]
    value['output_times'] = [engine.physical._stamp(start+timedelta(seconds=i*300)) for i in range(61)]
    events = deepcopy(value['events'])
    value['events'] = [events[0], events[1], events[-1]]
    for event, seconds in zip(value['events'], (0, 600, 18000)):
        event['at'] = engine.physical._stamp(start+timedelta(seconds=seconds))
    value['solver']['max_step_seconds'] = 10
    if held:
        value['events'][-1]['removals']['values']['leaf']['value'] = 1e9
    return value


def row_evidence(checked, directory):
    fd = files.job_store._open_directory_nofollow(Path(directory))
    rows = {}
    try:
        files._secure(fd, directory=True)
        for kind, pages in checked.index.items():
            values = []
            for page in pages:
                raw = files._read(fd, page['sha256']+'.json', artifact.LIMITS['page_bytes'])
                current = inputs._json(raw)
                assert sha256(raw).hexdigest() == page['sha256'] and canonical(current) == raw
                assert len(current) == page['count'] and page['start'] == len(values)
                assert current[0]['at'] == page['first_at'] and current[-1]['at'] == page['last_at']
                values.extend(current)
            assert len(values) == checked.summary['counts'][kind]
            rows[kind] = {'count':len(values), 'rows_sha256':digest(values),
                'utc_sha256':digest([value['at'] for value in values])}
    finally:
        os.close(fd)
    return rows


def child(archive, request_path, output):
    started = perf_counter(); before = len(os.listdir('/proc/self/fd'))
    request = json.loads(Path(request_path).read_bytes()); server = authority(archive)
    args = (Path(request['artifact_directory']), request['artifact_sha256'],
        Path(request['input_directory']), request['input_root_sha256'],
        Path(request['input_proof']).read_bytes(), Path(request['result_proof']).read_bytes())
    calls = {'input_parser':0, 'old_context':0, 'calculation_context':0,
        'artifact_reader':0, 'terminal_prefix_QC':0, 'terminal_delta_QC':0, 'advance':0, 'rhs':0}
    def forbidden(name):
        def fail(*a, **k):
            calls[name] += 1
            raise AssertionError('forbidden calculation or original QC during fresh verification')
        return fail
    for owner, name, label in ((inputs,'open_input_packet','input_parser'),
            (engine.legacy,'prepare_context','old_context'), (engine,'open_calculation_context','calculation_context'),
            (artifact,'open_artifact','artifact_reader'), (artifact._Files,'_load_prefix','terminal_prefix_QC'),
            (artifact,'_validate_delta','terminal_delta_QC'), (engine,'advance_chunk','advance'),
            (engine.short._Evaluator,'rhs','rhs')):
        setattr(owner, name, forbidden(label))
    tick = perf_counter(); checked = server.verify(*args); verify_seconds = perf_counter()-tick
    summary, context = checked.summary, checked.context
    validation = context['manifest']['input_validation']
    assert validation['validated_context_sha256'] != context['context_sha256']
    assert validation['evidence_sha256'] == sha256(args[4]).hexdigest()
    assert checked.rights_or_gate_approval is False
    tick = perf_counter(); rows = row_evidence(checked, args[0]); read_seconds = perf_counter()-tick
    assert not any(calls.values()) and len(os.listdir('/proc/self/fd')) == before
    cp = summary['checkpoint']
    result = {'pid':os.getpid(), 'verify_wall_seconds':verify_seconds, 'raw_rows_wall_seconds':read_seconds,
        'summary_sha256':digest(summary), 'index_sha256':digest(checked.index), 'context_sha256':digest(context),
        'identity':checked.identity, 'rows':rows, 'status':summary['status'],
        'checkpoint_sha256':None if cp is None else cp['checkpoint_sha256'],
        'checkpoint_vector_count':None if cp is None else len(cp['y']),
        'original_validated_context_sha256':validation['validated_context_sha256'],
        'calculation_context_sha256':context['context_sha256'], 'forbidden_calls':calls,
        'fd_before':before, 'fd_after':len(os.listdir('/proc/self/fd')),
        'wall_seconds':perf_counter()-started, 'peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024}
    save(output, canonical(result))


def main(output, archive, native_cli_proof):
    archive = Path(archive); archive.mkdir(mode=0o700)
    save(archive/'input.key', os.urandom(32)); save(archive/'result.key', os.urandom(32))
    old = json.loads((ROOT/'research/artifacts/crop-cycle-full-rhs-durable-completed-reference-20261007.json').read_bytes())
    preserved = old['source_sha256']
    assert len(preserved) == 55
    def preserve():
        assert all(sha256((ROOT/name).read_bytes()).hexdigest() == expected for name, expected in preserved.items())
    preserve(); server = authority(archive); measurements = []
    fd_before = len(os.listdir('/proc/self/fd')); started = perf_counter()
    for held in (False, True):
        label = 'confirmed-past-hold' if held else 'completed'; base = archive/label; base.mkdir(mode=0o700)
        input_path, artifact_path = base/'inputs', base/'artifact'; value = program(held)
        tick = perf_counter(); receipt = reference.write_packet(input_path, value, reference.profiles())
        for path in input_path.iterdir():path.chmod(0o400)
        input_raw = server.input_authority.issue(input_path, receipt['root_sha256'])
        input_seconds = perf_counter()-tick; save(base/'input-proof.json', input_raw)
        tick = perf_counter()
        with engine.open_calculation_context(input_path, receipt['root_sha256'], input_raw,
                authority=server.input_authority) as context:
            with artifact.create_writer(artifact_path, context, notice_raw=NOTICE) as writer:
                while writer.advance({'max_steps':997, 'max_transitions':128})['status'] == 'yielded':pass
                result = writer.finalize()
            with artifact.open_artifact(artifact_path, result['artifact_sha256'], context, notice_raw=NOTICE) as reader:
                expected = reader.summary; expected_index = deepcopy(reader._index); expected_rows = {}
                for kind in ('samples','events'):
                    rows, offset = [], 0
                    while True:
                        page = reader.page(kind, offset, 64 if kind == 'samples' else 8)
                        rows.extend(page['records']); offset = page['next']
                        if offset == page['total']:break
                    expected_rows[kind] = {'count':len(rows), 'rows_sha256':digest(rows),
                        'utc_sha256':digest([row['at'] for row in rows])}
        assert context.reader.closed and not context.reader._cache and not context._cache
        calculation_seconds = perf_counter()-tick
        args = (artifact_path, result['artifact_sha256'], input_path, receipt['root_sha256'], input_raw)
        original, actual_qc, rhs = artifact.open_artifact, [], engine.short._Evaluator.rhs
        def checked(*a, **k):
            actual_qc.append('original-whole-artifact-QC'); return original(*a, **k)
        def forbidden_rhs(*a, **k):raise AssertionError('proof issuance ran RHS')
        artifact.open_artifact = checked; engine.short._Evaluator.rhs = forbidden_rhs
        try:
            tick = perf_counter(); raw = server.issue(*args); issue_seconds = perf_counter()-tick
        finally:
            artifact.open_artifact = original; engine.short._Evaluator.rhs = rhs
        assert actual_qc == ['original-whole-artifact-QC']; save(base/'result-proof.json', raw)
        request = {'artifact_directory':str(artifact_path), 'artifact_sha256':result['artifact_sha256'],
            'input_directory':str(input_path), 'input_root_sha256':receipt['root_sha256'],
            'input_proof':str(base/'input-proof.json'), 'result_proof':str(base/'result-proof.json')}
        save(base/'request.json', canonical(request))
        command = [sys.executable, str(SOURCE), '--child', '--archive', str(archive),
            '--request', str(base/'request.json'), '--output', str(base/'child-output.json')]
        process = subprocess.run(command, capture_output=True, timeout=120)
        save(base/'child-command.json', canonical({'argv':command, 'actual_exit_code':process.returncode}))
        save(base/'child.log', process.stdout+process.stderr)
        assert process.returncode == 0, process.stderr.decode()
        fresh = json.loads((base/'child-output.json').read_bytes())
        assert not Path('/proc', str(fresh['pid'])).exists()
        assert fresh['summary_sha256'] == digest(expected) and fresh['index_sha256'] == digest(expected_index)
        assert fresh['rows'] == expected_rows
        assert expected['status'] == ('hold' if held else 'completed')
        if held:assert expected['checkpoint'] is None and expected['last_confirmed'] is not None
        else:assert fresh['checkpoint_vector_count'] == 121 and expected['steps'] == expected['planned_steps'] == 1800
        measurements.append({'case':label, 'steps':expected['steps'], 'planned_steps':expected['planned_steps'],
            'counts':expected['counts'], 'commit_count':expected['commit_count'], 'input_wall_seconds':input_seconds,
            'calculation_and_original_read_wall_seconds':calculation_seconds, 'proof_issue_wall_seconds':issue_seconds,
            'proof_bytes':len(raw), 'proof_sha256':sha256(raw).hexdigest(),
            'whole_artifact_QC_calls_at_issue':len(actual_qc), 'fresh_python_exit_code':process.returncode,
            'fresh_python_pid_gone':True, 'closed_context_and_empty_caches':True, 'fresh_python':fresh})
        print(label, json.dumps({'steps':expected['steps'], 'counts':expected['counts'],
            'issue_seconds':issue_seconds, 'fresh_verify_seconds':fresh['verify_wall_seconds']}), flush=True)
    preserve(); assert len(os.listdir('/proc/self/fd')) == fd_before
    source_paths = ['backend/app/crop_cycle_calculation_result_evidence.py',
        'backend/tests/test_crop_cycle_calculation_result_evidence.py',
        'research/crop-cycle-calculation-result-evidence-reference.py', 'contracts/crop-cycle-calculation-query-v1.md']
    result = {'version':'crop-cycle-calculation-result-evidence-reference-v1', 'scope':'owned_synthetic_software_only',
        'recorded_at_utc':datetime.now(timezone.utc).isoformat(), 'native_cli':json.loads(Path(native_cli_proof).read_bytes()),
        'source_sha256':{name:sha256((ROOT/name).read_bytes()).hexdigest() for name in source_paths},
        'preserved_original_source_count':55, 'preserved_original_source_sha256':preserved,
        'measurements':measurements, 'fd_before':fd_before, 'fd_after':len(os.listdir('/proc/self/fd')),
        'wall_seconds':perf_counter()-started, 'peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
        'rights_or_gate_approval':False, 'gate_decisions':{name:'not_assessed' for name in ('G0','G1','G2','G3a','G3b','G4')},
        'external_dependencies':{'adopted_cultivar_inputs':0,'independent_domestic_validation_datasets':0,'actual_crop_runs':0},
        'not_run':['typed_result_read_context','farm_DB_binding','HTTP','WebGL','whole_166_day_new_proof',
            'independent_agricultural_validation','whole_backend_suite','hosted_CI']}
    save(output, canonical(result)+b'\n')


if __name__ == '__main__':
    parser = ArgumentParser(); parser.add_argument('--output', required=True); parser.add_argument('--archive', required=True)
    parser.add_argument('--native-cli-proof'); parser.add_argument('--child', action='store_true'); parser.add_argument('--request')
    args = parser.parse_args()
    if args.child:child(args.archive, args.request, args.output)
    else:main(args.output, args.archive, args.native_cli_proof)
