from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from app import crop_cycle_input_evidence as evidence
from app import crop_cycle_input_read_context as candidate
from app import crop_cycle_input_stream as inputs
from app import crop_cycle_stream_execution as engine
from test_crop_cycle_artifact import PROFILES, NOTICE
from test_crop_cycle_input_stream import CASES, write

KEY = b'owned-read-context-test-key-32-bytes!'


def authority():
    return evidence.InputEvidenceAuthority(PROFILES, NOTICE, integrity_key=KEY,
        issuer_id='owned-reader-test', key_id='own-key-v1')


def packet(tmp_path, p=None):
    path=tmp_path/'inputs'; root=write(path,p)['root_sha256']
    for file in path.iterdir():file.chmod(0o400)
    server=authority(); raw=server.issue(path,root)
    return path,root,server,raw


@pytest.mark.parametrize('case',CASES,ids=lambda case:case['case_id'])
def test_all_original_records_clocks_grid_positions_and_cursor_are_preserved(tmp_path,case,monkeypatch):
    path,root,server,raw=packet(tmp_path,deepcopy(case['program']))
    before=len(os.listdir('/proc/self/fd'))
    with inputs.open_input_packet(path,root,**PROFILES) as original:
        old=engine.prepare_context(original,**PROFILES)
        records={kind:[original.record(kind,i) for i in range(old.reader.plan['counts'][kind])] for kind in inputs.KINDS}
        clocks=[original.segment(i) for i in range(old.segment_count)]
        boundaries=[engine._boundary(old,i) for i in range(old.boundary_count)]
        expected_manifest=old.manifest
    monkeypatch.setattr(inputs,'open_input_packet',lambda *a,**k:pytest.fail('full parser called'))
    monkeypatch.setattr(engine,'prepare_context',lambda *a,**k:pytest.fail('full context called'))
    monkeypatch.setattr(engine.short._Evaluator,'rhs',lambda *a,**k:pytest.fail('RHS called'))
    with candidate.open_input_read_context(path,root,raw,authority=server) as context:
        assert type(context) is candidate.InputReadContext
        assert context.manifest==expected_manifest
        assert context.context_record==json.loads(raw)['payload']['context']
        for kind,expected in records.items():assert [context.record(kind,i) for i in range(len(expected))]==expected
        assert [context.segment(i) for i in range(len(clocks))]==clocks
        assert [context.boundary(i) for i in range(len(boundaries))]==boundaries
        cursor=None;observed=[]
        while True:
            page=context.boundary_page(cursor,limit=2);observed.extend(page['boundaries'])
            cursor=context.restore_cursor(context.cursor_bytes(page['cursor']))
            if page['complete']:break
        assert [row['at'] for row in observed]==[row['at'] for row in boundaries]
        returned=context.context_record;returned['seed'][0]+=1.0
        assert returned!=context.context_record
        assert context.identity['math_context_sha256']==context.context_record['context_sha256']
        assert context.identity['read_context_version']==candidate.VERSION
        assert context.rights_or_gate_approval is False
        assert len(context.reader._cache)<=4 and len(context._cache)<=1
        with pytest.raises(engine.CycleStreamExecutionRejected):engine.start(context)
        context.recheck()
    assert len(os.listdir('/proc/self/fd'))==before
    assert context.reader.closed and not context.reader._cache and not context._cache
    with pytest.raises(candidate.InputReadContextHold):context.boundary(0)


@pytest.mark.parametrize('change',['cached-blob','root','replace-directory','writable'])
def test_changes_after_open_or_cache_prevent_read_or_final_recheck(tmp_path,change):
    path,root,server,raw=packet(tmp_path)
    before=len(os.listdir('/proc/self/fd'))
    context=candidate.open_input_read_context(path,root,raw,authority=server)
    context.record('segments',0)
    block=context.reader._root['streams']['segments']['blocks'][0]
    target=path/(block['sha256']+'.json')
    if change=='root':target=path/'root.json'
    if change in ('root','cached-blob'):
        old=target.read_bytes();target.chmod(0o600);target.write_bytes(old+b' ');target.chmod(0o400)
    elif change=='replace-directory':
        path.rename(tmp_path/'old-inputs');path.mkdir(mode=0o700)
        for original in (tmp_path/'old-inputs').iterdir():
            replacement=path/original.name;replacement.write_bytes(original.read_bytes());replacement.chmod(0o400)
    else:target.chmod(0o600)
    with pytest.raises(candidate.InputReadContextHold):
        if change in ('cached-blob','writable'):context.record('segments',0)
        else:context.recheck()
    assert context.reader.closed and len(os.listdir('/proc/self/fd'))==before


def test_wrong_proof_and_failed_construction_leave_no_descriptors(tmp_path):
    path,root,server,raw=packet(tmp_path)
    before=len(os.listdir('/proc/self/fd'))
    with pytest.raises(candidate.InputReadContextHold):
        candidate.open_input_read_context(path,root,raw+b' ',authority=server)
    assert len(os.listdir('/proc/self/fd'))==before


@pytest.mark.parametrize('kind',['index','cursor','source'])
def test_invalid_query_or_changed_read_code_is_a_hold_and_closes_context(tmp_path,kind,monkeypatch):
    path,root,server,raw=packet(tmp_path)
    before=len(os.listdir('/proc/self/fd'))
    context=candidate.open_input_read_context(path,root,raw,authority=server)
    with pytest.raises(candidate.InputReadContextHold):
        if kind=='index':context.boundary(True)
        elif kind=='cursor':context.restore_cursor(b'{}')
        else:
            changed=tmp_path/'changed.py';changed.write_text('owned changed read code')
            monkeypatch.setattr(candidate,'__file__',str(changed));context.recheck()
    assert context.reader.closed and len(os.listdir('/proc/self/fd'))==before


def test_fresh_python_uses_retained_key_and_preserves_bounded_boundary(tmp_path):
    path,root,server,raw=packet(tmp_path)
    keyfile=tmp_path/'private-key';keyfile.write_bytes(KEY);keyfile.chmod(0o400)
    code='''
from pathlib import Path
import json,sys
from app.crop_cycle_input_evidence import InputEvidenceAuthority
from app.crop_cycle_input_read_context import open_input_read_context
from test_crop_cycle_artifact import PROFILES,NOTICE
server=InputEvidenceAuthority(PROFILES,NOTICE,integrity_key=Path(sys.argv[3]).read_bytes(),
 issuer_id='owned-reader-test',key_id='own-key-v1')
with open_input_read_context(sys.argv[1],sys.argv[2],sys.stdin.buffer.read(),authority=server) as context:
 row=context.boundary(1);identity=context.identity;context.recheck()
print(json.dumps({'boundary':row,'identity':identity}))
'''
    env=dict(os.environ,PYTHONPATH=str(Path(__file__).parents[1])+os.pathsep+str(Path(__file__).parent))
    child=subprocess.run([sys.executable,'-c',code,str(path),root,str(keyfile)],input=raw,
        capture_output=True,timeout=30,env=env)
    assert child.returncode==0,child.stderr.decode()
    result=json.loads(child.stdout)
    with candidate.open_input_read_context(path,root,raw,authority=server) as context:
        assert result=={'boundary':context.boundary(1),'identity':context.identity}
