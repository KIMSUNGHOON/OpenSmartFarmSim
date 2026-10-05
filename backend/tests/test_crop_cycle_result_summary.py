"""Actual registered synthetic summary/header agreement; no crop validation."""
from hashlib import sha256
import json
from pathlib import Path
from time import perf_counter

import pytest

from app import crop_cycle_result_store as storage
from app import crop_cycle_server_custody as custody
from app import crop_cycle_input_stream as inputs
from app.thermal_run_store import _canonical
from test_crop_cycle_result_store_farms import DB_KEY, forbid_math
from test_crop_cycle_server_custody_farms import (
    server_setup, OwnInputResolver, KEY, BUDGET, authoring, farm_setup,
    login_database, login_scope)
from test_crop_startup_result_store import shifted
from test_crop_cycle_artifact import PROFILES

pytestmark=pytest.mark.parametrize('login_scope',[{'market_calculation':True,
    'market_source_storage':True,'thermal_scenario_storage':True,
    'break_even_calculation':True,'crop_cycle_result_storage':True}],indirect=True)


@pytest.mark.parametrize('status',['completed','hold'])
def test_registered_summary_keeps_original_header_manifest_and_detached_copy(server_setup,tmp_path,monkeypatch,status):
    server,raw,_,_,_=server_setup
    if status=='hold':
        program=shifted();program['initial_state']['values']['temperature_sum']['value']=0
        anchors=program.pop('output_times');directory=tmp_path/'manifest-hold-inputs'
        packet=inputs.write_input_packet(directory,**program,anchors=anchors,outputs=anchors,
            **PROFILES,program_id='own-summary-manifest-hold')
        body=json.loads(raw);body['input'].update(root_sha256=packet['root_sha256'],program_id='own-summary-manifest-hold')
        body['rights']['input_root_sha256']=packet['root_sha256'];raw=_canonical(body)
        root=tmp_path/'manifest-hold-server';root.mkdir(mode=0o700)
        server=custody.CycleServerCustody(server.binding,root,
            input_resolver=OwnInputResolver(directory,packet['root_sha256']),integrity_key=KEY)
    progress=json.loads(server.advance('tenant-1',raw,budget=BUDGET));assert progress['status']==status
    forbid_math(monkeypatch)
    with server._open('tenant-1',raw,False) as journal:
        expected=journal.context.manifest
        assert _canonical(expected)==_canonical(journal.header['manifest'])
        original_metadata=json.loads(_canonical(journal.writer._summary))
    store=storage.CycleCropResultStore(server,integrity_key=DB_KEY)
    record=store.put('tenant-1',raw);farm=json.loads(raw)['farm']
    tick=perf_counter();summary=store.summary('tenant-1',record['result_id'],farm);elapsed=perf_counter()-tick
    assert 'manifest' in summary
    assert _canonical(summary['manifest'])==_canonical(expected)
    assert set(summary)==set(original_metadata)|{'manifest'}
    assert _canonical({k:v for k,v in summary.items() if k!='manifest'})==_canonical(original_metadata)
    assert summary['status']==status and summary['steps']==progress['steps']
    summary['manifest']['solver']['max_steps']=1
    assert _canonical(store.summary('tenant-1',record['result_id'],farm)['manifest'])==_canonical(expected)
    path=Path('/tmp/ossf-cycle-db-summary-manifest-reference-20261005.json')
    values=json.loads(path.read_bytes()) if path.exists() else {}
    values[status]={'scope':'registered_synthetic_software_only','code_sha256':storage.CODE_SHA256,
        'original_header_context_manifest_equal':True,'original_terminal_metadata_equal':True,
        'returned_copy_detached':True,'summary_rhs_zero':True,'summary_seconds':elapsed,
        'manifest_sha256':sha256(_canonical(expected)).hexdigest()}
    path.write_text(json.dumps(values,indent=2)+'\n')
