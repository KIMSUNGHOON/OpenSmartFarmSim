"""Fresh Python typed pages over the preserved owned verified-result fixtures."""
from argparse import ArgumentParser
from bisect import bisect_left
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
from app import crop_cycle_calculation_result_read_context as query

spec = importlib.util.spec_from_file_location('owned_proof_reference', ROOT/'research/crop-cycle-calculation-result-evidence-reference.py')
proof_reference = importlib.util.module_from_spec(spec); spec.loader.exec_module(proof_reference)
evidence, inputs = query.evidence, query.inputs
SOURCE = Path(__file__).resolve()


def canonical(value):return inputs._canonical(value)
def digest(value):return sha256(canonical(value)).hexdigest()
def save(path, value):proof_reference.save(path, canonical(value))


def child(request_path, output):
    request = json.loads(Path(request_path).read_bytes()); fixture = Path(request['fixture'])
    base = fixture/request['case']; raw_request = json.loads((base/'request.json').read_bytes())
    server = proof_reference.authority(fixture); expected = request['expected']
    args = (Path(raw_request['artifact_directory']), raw_request['artifact_sha256'],
        Path(raw_request['input_directory']), raw_request['input_root_sha256'],
        Path(raw_request['input_proof']).read_bytes(), Path(raw_request['result_proof']).read_bytes())
    assert sha256(args[-1]).hexdigest() == expected['proof_sha256']
    calls = {'input_parser':0,'old_context':0,'calculation_context':0,'artifact_reader':0,
        'prefix_QC':0,'delta_QC':0,'advance':0,'rhs':0}
    def forbidden(label):
        def fail(*a, **k):
            calls[label] += 1; raise AssertionError('read constructed calculation/parser/QC/RHS')
        return fail
    for owner, name, label in ((inputs,'open_input_packet','input_parser'),
            (evidence.calculation.legacy,'prepare_context','old_context'),
            (evidence.calculation,'open_calculation_context','calculation_context'),
            (evidence.artifact,'open_artifact','artifact_reader'),
            (evidence.artifact._Files,'_load_prefix','prefix_QC'),(evidence.artifact,'_validate_delta','delta_QC'),
            (evidence.calculation,'advance_chunk','advance'),(evidence.calculation.short._Evaluator,'rhs','rhs')):
        setattr(owner, name, forbidden(label))
    before = len(os.listdir('/proc/self/fd')); started = perf_counter(); pages, all_rows = [], {}
    tick = perf_counter(); reader = query.open_calculation_result_read_context(*args, authority=server)
    open_seconds = perf_counter()-tick
    def page(kind, start=0, limit=None, **kwargs):
        tick = perf_counter(); result = reader.page(kind, start, limit, **kwargs)
        size = len(canonical(result)); assert size <= kwargs.get('max_bytes',query.MAX_PAGE_BYTES)
        pages.append({'kind':kind,'start':start,'next':result['next'],'count':len(result['records']),
            'bytes':size,'wall_seconds':perf_counter()-tick})
        return result
    with reader:
        summary, context, identity = reader.summary, reader.context_record, reader.identity
        original = expected['fresh_python']
        assert digest(summary) == original['summary_sha256'] and digest(context) == original['context_sha256']
        assert reader.manifest == summary['manifest'] and reader.rights_or_gate_approval is False
        assert identity['read_context_version'] == query.VERSION and identity['read_code_sha256'] == query.CODE_SHA256
        assert identity['read_dependency_sha256'] == query.DEPENDENCY_SHA256
        assert {key:identity[key] for key in original['identity']} == original['identity']
        validation = context['manifest']['input_validation']
        assert validation['validated_context_sha256'] == original['original_validated_context_sha256']
        assert context['context_sha256'] == original['calculation_context_sha256']
        assert validation['evidence_sha256'] == sha256(args[4]).hexdigest()
        if summary['status'] == 'completed':assert len(summary['checkpoint']['y']) == len(summary['checkpoint']['seed']) == 121
        else:assert summary['checkpoint'] is None and summary['last_confirmed'] is not None
        for kind in ('samples','events'):
            rows, offset = [], 0
            while True:
                value = page(kind, offset, 7 if kind == 'samples' else 2)
                rows.extend(value['records']); offset = value['next']
                if offset == value['total']:break
            actual = {'count':len(rows),'rows_sha256':digest(rows),'utc_sha256':digest([row['at'] for row in rows])}
            assert actual == original['rows'][kind]; all_rows[kind] = rows
            empty = page(kind, offset, 1)
            assert empty == {'kind':kind,'start':offset,'next':offset,'total':offset,'records':[]}
            full = page(kind, 0)
            assert full['records'] == rows[:64 if kind == 'samples' else 8]
        rows = all_rows['samples']; selected = sorted({0,len(rows)//2,len(rows)-1})
        times = [row['at'] for row in rows]
        for event in all_rows['events']:
            at = bisect_left(times,event['at'])
            selected = sorted(set(selected)|{i for i in (at-1,at,at+1) if 0 <= i < len(rows)})
        for at in selected:assert page('samples',at,1)['records'] == rows[at:at+1]
        first_two = page('samples',0,2)
        first = {**first_two,'next':1,'records':first_two['records'][:1]}; cap = len(canonical(first))
        short = page('samples',0,2,max_bytes=cap)
        assert short == first and len(canonical(short)) == cap
        assert page('samples',short['next'],1)['records'] == first_two['records'][1:]
        with query.open_calculation_result_read_context(*args,authority=server) as too_small:
            try:too_small.page('samples',0,2,max_bytes=cap-1)
            except query.CalculationResultReadContextHold:pass
            else:raise AssertionError('one original row exceeded byte budget without hold')
            assert too_small.closed and not too_small._cache
        copied = page('samples',0,1); copied['records'][0]['at'] = 'changed-copy'
        assert page('samples',0,1)['records'] == rows[:1]
        reader.recheck(); cache_count = len(reader._cache)
        assert cache_count <= 2
    assert reader.closed and not reader._cache and len(os.listdir('/proc/self/fd')) == before
    assert not any(calls.values())
    result = {'pid':os.getpid(),'nice':os.getpriority(os.PRIO_PROCESS,0),'case':request['case'],
        'status':summary['status'],'counts':summary['counts'],'summary_sha256':digest(summary),
        'context_record_sha256':digest(context),'identity':identity,'open_wall_seconds':open_seconds,
        'wall_seconds':perf_counter()-started,'pages':pages,'all_rows_equal_prior_original_reference':True,
        'selected_sample_indices':selected,'byte_short_exact_cap':cap,'too_small_closed':True,
        'checkpoint_121_values_preserved':summary['status']=='completed','hold_confirmed_past_preserved':summary['status']=='hold',
        'forbidden_calls':calls,'cache_kinds_max_observed':cache_count,'closed_empty_cache':True,
        'fd_before':before,'fd_after':len(os.listdir('/proc/self/fd')),
        'peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024}
    save(output,result)


def main(output, fixture, archive, native_cli_proof):
    fixture, archive = Path(fixture), Path(archive); archive.mkdir(mode=0o700)
    prior_path = ROOT/'research/artifacts/crop-cycle-calculation-result-evidence-reference-20261007.json'
    prior = json.loads(prior_path.read_bytes()); preserved = dict(prior['preserved_original_source_sha256'])
    for name, value in prior['source_sha256'].items():
        if name.endswith('.py'):preserved[name] = value
    def preserve():
        assert all(sha256((ROOT/name).read_bytes()).hexdigest() == value for name,value in preserved.items())
    preserve(); results = []; before = len(os.listdir('/proc/self/fd')); started = perf_counter()
    for expected in prior['measurements']:
        label = expected['case']; request_path, response_path = archive/(label+'.request.json'),archive/(label+'.response.json')
        save(request_path,{'fixture':str(fixture),'case':label,'expected':expected})
        command = [sys.executable,str(SOURCE),'--child','--request',str(request_path),'--output',str(response_path)]
        process = subprocess.run(command,capture_output=True,timeout=120)
        save(archive/(label+'.command.json'),{'argv':command,'actual_exit_code':process.returncode})
        proof_reference.save(archive/(label+'.log'),process.stdout+process.stderr)
        assert process.returncode == 0,process.stderr.decode()
        result = json.loads(response_path.read_bytes()); assert not Path('/proc',str(result['pid'])).exists()
        result.update(actual_exit_code=process.returncode,pid_gone=True)
        results.append(result)
        print(json.dumps({'case':label,'status':result['status'],'counts':result['counts'],
            'wall_seconds':result['wall_seconds'],'maximum_page_bytes':max(page['bytes'] for page in result['pages'])}),flush=True)
    preserve(); assert len(os.listdir('/proc/self/fd')) == before
    names = ['backend/app/crop_cycle_calculation_result_read_context.py',
        'backend/tests/test_crop_cycle_calculation_result_read_context.py',
        'research/crop-cycle-calculation-result-read-context-reference.py',
        'contracts/crop-cycle-calculation-result-read-context-v1.md']
    record = {'version':'crop-cycle-calculation-result-read-context-reference-v1','scope':'owned_synthetic_software_only',
        'native_cli':json.loads(Path(native_cli_proof).read_bytes()),'prior_original_reference_sha256':sha256(prior_path.read_bytes()).hexdigest(),
        'source_sha256':{name:sha256((ROOT/name).read_bytes()).hexdigest() for name in names},
        'preserved_source_count':len(preserved),'preserved_source_sha256':preserved,'fresh_python':results,
        'fd_before':before,'fd_after':len(os.listdir('/proc/self/fd')),'wall_seconds':perf_counter()-started,
        'peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,'rights_or_gate_approval':False,
        'actual_new_RHS_runs':0,'reused_preserved_owned_proofs_without_relabeling':True,
        'gate_decisions':{name:'not_assessed' for name in ('G0','G1','G2','G3a','G3b','G4')},
        'external_dependencies':{'adopted_cultivar_inputs':0,'independent_domestic_validation_datasets':0,'actual_crop_runs':0},
        'not_run':['farm_DB_current_query','HTTP','WebGL','whole166_new_proof','whole_backend','hosted_CI','independent_agricultural_validation']}
    save(output,record)


if __name__ == '__main__':
    parser = ArgumentParser(); parser.add_argument('--output',required=True); parser.add_argument('--fixture')
    parser.add_argument('--archive'); parser.add_argument('--native-cli-proof'); parser.add_argument('--child',action='store_true'); parser.add_argument('--request')
    args = parser.parse_args()
    if args.child:child(args.request,args.output)
    else:main(args.output,args.fixture,args.archive,args.native_cli_proof)
