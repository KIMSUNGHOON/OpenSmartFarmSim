"""Forensic probes: passing cases reproduce the rejected prototype's failures.

Run explicitly with pytest; these are not production adoption checks.
"""
from pathlib import Path
from hashlib import sha256
import builtins,json,os,sys,types

R=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(R/'backend/tests')]
import test_solar_json_source_assembly as source
import test_solar_json_load_adapter as previous
import pytest

archive=source.archive
saved_archive=source.saved_archive
model=source.candidate()
storage=model.storage


def save_proof(name,value,fallback_directory):
    directory=Path(os.environ.get('OSSF_SOLAR_EXECUTION_QUERY_EVIDENCE',fallback_directory))
    directory.mkdir(mode=0o700,parents=True,exist_ok=True)
    with (directory/name).open('x') as target:
        os.fchmod(target.fileno(),0o400)
        json.dump(value,target,indent=2)
        target.write('\n')


@pytest.mark.parametrize('mutate',[False,True])
def test_nested_builtin_borrow_between_statement_observations(archive,monkeypatch,mutate,tmp_path):
    head,expected,_,_=previous.original_result(archive)
    results=[]
    for selected in ('original','candidate'):
        captured=[];installed=[];restored=[];audit={}
        record_code=(storage._Files._records.__code__ if selected=='original' else
            next(v for v in model._RECORDS.__code__.co_consts
                 if type(v) is types.CodeType and v.co_name=='_records'))
        monitor=sys.monitoring
        slot=next(i for i in range(5,-1,-1) if monitor.get_tool(i) is None)
        with monkeypatch.context() as patch:
            def aset(value):
                captured.append(value)
                patch.setattr(storage,'set',builtins.set)
                restored.append(True)
                return builtins.set(value)
            def returned(code,offset,callable,arg0):
                if (callable is builtins.type and builtins.type(arg0) is builtins.dict
                        and builtins.set(arg0)=={'value','time'} and not installed):
                    installed.append(True)
                    patch.setattr(storage,'set',aset,raising=False)
            def after_source():
                assert installed==restored==[True] and len(captured)==1
                if mutate:captured[0]['value']['step_index']+=1
            monitor.use_tool_id(slot,'nested-native-borrow-review')
            try:
                monitor.register_callback(slot,monitor.events.C_RETURN,returned)
                monitor.set_local_events(slot,record_code,monitor.events.CALL)
                with storage._Files(archive) as reader, source.before_first_source_hash_check(after_source) as checked:
                    call=(lambda:reader._load(head)) if selected=='original' else (lambda:model.load(reader,head,audit=audit))
                    outcome=previous.outcome(call)
                    assert checked==[True]
            finally:
                monitor.set_local_events(slot,record_code,0)
                monitor.register_callback(slot,monitor.events.C_RETURN,None)
                monitor.free_tool_id(slot)
        assert installed==restored==[True] and len(captured)==1
        if outcome[0]=='value':
            assert outcome[1]==expected
            outcome=('value',sha256(outcome[1]).hexdigest(),len(outcome[1]))
        results.append({'mode':selected,'outcome':outcome,'captured_rows':len(captured),
                        'binding_restored':True,'audit':audit})
    if mutate:
        assert results[0]['outcome'][0]==results[1]['outcome'][0]=='error'
        assert results[0]['outcome']!=results[1]['outcome']
    else:
        assert results[0]['outcome']==results[1]['outcome']
        assert results[1]['audit']['source_pairs']==head['commit_count']
    assert results[1]['audit']['disposed'] and results[1]['audit']['raw_bytes_after_close']==0
    proof={'scope':'software-only observation counterexample; current candidate is not adopted',
           'mutated_after_source_hash':mutate,'results':results,
           'statement_guards_unchanged':True,'methods_changed_only_storage_set_in_one_expression':True,
           'graph_capture_through_actual_callback_argument':True,'graph_access_through_stack':False,
           'timing_trial':False,'product_calls':0,'normal64_accepted':False,'actual_farm_Runs':0,'G0_G4':'not_assessed'}
    save_proof('nested-mutation.json' if mutate else 'nested-observe.json',proof,tmp_path/'evidence')


def test_internal_scanner_factory_can_restore_before_outer_approval(tmp_path,monkeypatch):
    core=model.core;legacy=storage.files
    value={'version':'test-only','header_sha256':'a'*64,'sequence':1,
           'parent_commit_sha256':None,'before_checkpoint_sha256':'b'*64,
           'source_chunk_sha256':'c'*64,'result_sha256':'d'*64,
           'source_meta':{'nested':[1]},'times_meta':{},'pages':[]}
    raw=legacy._canonical(value);digest=sha256(raw).hexdigest()
    path=tmp_path/(digest+'.json');path.write_bytes(raw);path.chmod(0o400)
    monitor=sys.monitoring;slot=next(i for i in range(5,-1,-1) if monitor.get_tool(i) is None)
    code=json.JSONDecoder.__init__.__code__;captured=[];installed=[]
    native=json.scanner.make_scanner
    with monkeypatch.context() as patch:
        def factory(context):
            scanner=native(context)
            def scan(text,index):
                result=scanner(text,index)
                captured.append(result[0])
                patch.setattr(json.scanner,'make_scanner',native)
                return result
            return scan
        def entered(called,offset):
            if not installed:
                installed.append(True)
                patch.setattr(json.scanner,'make_scanner',factory)
        monitor.use_tool_id(slot,'internal-scanner-loan-review')
        try:
            monitor.register_callback(slot,monitor.events.PY_START,entered)
            monitor.set_local_events(slot,code,monitor.events.PY_START)
            with legacy._Files(tmp_path) as reader,core.OwnedJSONScope() as scope:
                assert scope.policy.approved
                chain=scope.chain(reader,digest,len(raw))
                assert chain.retained and installed==[True] and len(captured)==1
                assert json.scanner.make_scanner is native and core.native_json_current()
                captured[0]['source_meta']['nested'][0]=9
                actual=scope.materialise(scope.commit(reader,digest,len(raw)))
                expected,_=reader._blob(digest,len(raw))
                assert expected==value and actual!=expected
                assert actual['source_meta']['nested']==[9] and expected['source_meta']['nested']==[1]
                assert scope.cache_hits==1 and path.read_bytes()==raw
                proof={'scope':'synthetic JSON software counterexample; no product cache',
                       'native_approval_before_and_after':True,'factory_restored':True,
                       'capture_through_actual_scanner_return':True,'graph_access_through_stack':False,
                       'unchanged_blob_SHA256':digest,'fresh_original_value_SHA256':sha256(legacy._canonical(expected)).hexdigest(),
                       'cached_value_SHA256':sha256(legacy._canonical(actual)).hexdigest(),
                       'cached_value_differs_from_fresh_read':True,'cache_hits':scope.cache_hits,
                       'raw_bytes_budget_peak':scope.peak_raw_bytes,'timing_trial':False,
                       'product_calls':0,'normal64_accepted':False,'actual_farm_Runs':0,'G0_G4':'not_assessed'}
        finally:
            monitor.set_local_events(slot,code,0)
            monitor.register_callback(slot,monitor.events.PY_START,None)
            monitor.free_tool_id(slot)
    assert scope.raw_bytes==0 and scope._closed
    proof['disposed']=True
    save_proof('internal-scanner.json',proof,tmp_path/'evidence')
