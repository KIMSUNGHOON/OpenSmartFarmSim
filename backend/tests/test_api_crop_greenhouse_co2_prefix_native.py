"""Actual current read, serialized response and source/witness mutation checks."""
from copy import deepcopy
import json
import os
from pathlib import Path

import pytest

from test_crop_greenhouse_co2_prefix import (
    setup, producer_setup as original_producer_setup, progress_setup, worker_setup, authoring, profiles,
    login_database, original_login_scope, login_scope, query_cleanup,
    model as current, reference, read, selector, advance, writable)

pytestmark=[reference.reference.pytestmark,pytest.mark.usefixtures('query_cleanup')]

@pytest.fixture
def producer_setup(authoring, tmp_path, profiles, request, monkeypatch):
    original=original_producer_setup.__wrapped__
    if getattr(request,'param',None)!='basis-transition':
        return original(authoring,tmp_path,profiles,request,monkeypatch)
    producer=reference.reference.producer
    transition=deepcopy(producer.reference.inputs.producer.reference.BY_ID['weather-multiple'])
    transition['forcing_program'][1]['co2']['basis']='dry'
    packet=producer.reference.inputs.packet
    with monkeypatch.context() as patch:
        patch.setattr(producer.reference.inputs,'packet',lambda directory,profiles,case=None:packet(directory,profiles,transition))
        return original(authoring,tmp_path,profiles,request,monkeypatch)



def save(name,value):
    root=os.environ.get('OSSF_CO2_PREFIX_PROJECTION_EVIDENCE')
    if root:
        with (Path(root)/(name+'.json')).open('x') as f:
            os.fchmod(f.fileno(),0o400);json.dump(value,f,sort_keys=True,indent=2);f.flush();os.fsync(f.fileno())


def test_selected_page_changed_after_serialization_is_held(setup,monkeypatch):
    query,worker,job_id,raw,value=setup
    lease=reference.confirm(worker,job_id);advance(worker,job_id,raw,lease,8)
    reference.readonly(value);record=query.read('tenant-1',job_id)
    pin=selector(json.loads(record.payload_raw));record=query.read('tenant-1',job_id,selector=pin,view='samples')
    _,artifact,_=reference.reference.producer.locations(worker.server,raw)
    head=json.loads((artifact/'HEAD').read_bytes())
    commit=json.loads((artifact/(head['latest_commit_sha256']+'.json')).read_bytes())
    path=artifact/(commit['pages']['samples'][0]['sha256']+'.json')
    original=path.read_bytes();mode=path.stat().st_mode&0o777
    try:
        path.chmod(0o600);path.write_bytes(original+b' ');path.chmod(mode)
        with monkeypatch.context() as patch:
            calls=reference.forbid(patch)
            with pytest.raises(current.Co2PrefixHold):query._after_projection('tenant-1',job_id,record)
            assert not any(calls.values())
    finally:path.chmod(0o600);path.write_bytes(original);path.chmod(mode)
    query._after_projection('tenant-1',job_id,record)
    save('after-serialization-page',{'actual_owned_selected_page_changed_after_original_read':True,
        'rejected_and_original_restored':True,'calls':calls})


from app import api_crop_greenhouse_co2_prefix as public
from test_api_crop_greenhouse_co2_prefix import inspect_private
from test_crop_greenhouse_co2_prefix_concurrent import lightweight_actor


def test_actual_current_views_scope_and_cancel_without_writes(setup,monkeypatch):
    query,worker,job_id,raw,value=setup
    reference.readonly(value);before=reference.persisted_digest(worker.jobs)
    with monkeypatch.context() as patch:
        calls=reference.forbid(patch);none=json.loads(public.read_prefix(query,'tenant-1',job_id))
        assert none['prefix_status']=='none' and none['reference'] is none['summary'] is none['page'] is None
        assert not any(calls.values())
    assert reference.persisted_digest(worker.jobs)==before
    writable(value);lease=reference.confirm(worker,job_id);_,first=advance(worker,job_id,raw,lease,8)
    pin={k:first['checkpoint'][k] for k in public.Selector.model_fields};reference.readonly(value)
    before=reference.persisted_digest(worker.jobs);outputs={}
    with monkeypatch.context() as patch:
        calls=reference.forbid(patch)
        for view in ('summary','samples','events'):
            original=query.read('tenant-1',job_id,selector=pin,view=view)
            out=public.read_prefix(query,'tenant-1',job_id,selector=pin,view=view);decoded=json.loads(out)
            source=json.loads(original.payload_raw);ref=decoded['reference'];outputs[view]=len(out)
            program=query._source_program('tenant-1',job_id,original)
            bases=public.public._basis_map(program,source['manifest'])
            assert ref['selector']==pin and ref['checkpoint']['checkpoint_recorded_at']==source['selection']['checkpoint_recorded_at']
            if view=='samples':
                page=deepcopy(decoded['page'])
                for row in page['records']:
                    assert row.pop('co2_basis')==bases[row['value']['forcing_step_index']]
                assert page==source['page']
            elif view=='events':assert decoded['page']['records']==[public.public._event(r,source['manifest']['identity'],bases) for r in source['page']['records']]
            else:assert decoded['summary']==source['summary']
            inspect_private(decoded)
        for scope in ('metadata','crop_result_read'):
            value[4]['scopes'].remove(scope)
            with pytest.raises(PermissionError):public.read_prefix(query,'tenant-1',job_id)
            value[4]['scopes'].add(scope)
        assert not any(calls.values())
    assert reference.persisted_digest(worker.jobs)==before
    assert worker.jobs.cancel('tenant-1',job_id)
    with monkeypatch.context() as patch:
        calls=reference.forbid(patch);closed=json.loads(public.read_prefix(query,'tenant-1',job_id))
        assert closed['prefix_status']=='closed' and closed['reference'] is None and not any(calls.values())
    save('actual-views',{'actual_scram':True,'original_values_units_UTC_selector':True,'private_fields_absent':True,
        'read_scopes_without_create_execute_write':True,'none_and_cancel_closed':True,'response_bytes':outputs,'calls':calls})


@pytest.mark.parametrize('fault',['rights','review','farm','page','witness','program'])
def test_actual_late_change_during_serialization_is_denied(setup,monkeypatch,fault):
    query,worker,job_id,raw,value=setup
    lease=reference.confirm(worker,job_id);advance(worker,job_id,raw,lease,8)
    reference.readonly(value);before=reference.persisted_digest(worker.jobs)
    pin=selector(read(query,job_id))
    _,artifact,_=reference.reference.producer.locations(worker.server,raw)
    head=json.loads((artifact/'HEAD').read_bytes());commit=json.loads((artifact/(head['latest_commit_sha256']+'.json')).read_bytes())
    path=artifact/(commit['pages']['samples'][0]['sha256']+'.json');source=path.read_bytes();mode=path.stat().st_mode&0o777
    serializer=public._public_bytes;serializations=[];review=value[2][3];review_status=review['status'];farm=worker.server.binding.farms
    program_path=value[2][0]/'source.json';program_original=program_path.read_bytes();program_mode=program_path.stat().st_mode&0o777
    try:
        with monkeypatch.context() as patch:
            calls=reference.forbid(patch)
            if fault=='witness':
                original=query.read
                def no_witness(*a,**kw):
                    record=original(*a,**kw);return current.PrefixRead(record.payload_raw,record.payload_sha256)
                patch.setattr(query,'read',no_witness)
            def serialize(projected):
                wire=serializer(projected);serializations.append(1)
                if len(serializations)==2:
                    if fault=='rights':value[5].allowed=False
                    elif fault=='review':review['status']='revoked'
                    elif fault=='farm':
                        def denied(*a,**kw):raise PermissionError('owned farm provider withdrew access')
                        patch.setattr(farm,'read_registration',denied)
                    elif fault=='page':path.chmod(0o600);path.write_bytes(source+b' ');path.chmod(mode)
                    elif fault=='program':
                        changed=json.loads(program_original);block=changed['forcing_program'][0]['co2']
                        block['basis']='dry' if block['basis']=='wet' else 'wet'
                        program_path.chmod(0o600);program_path.write_bytes(current.storage._canonical(changed));program_path.chmod(program_mode)
                return wire
            patch.setattr(public,'_public_bytes',serialize)
            expected=PermissionError if fault=='farm' else current.Co2PrefixPending if fault=='witness' else public.ProjectionHold
            with pytest.raises(expected):public.read_prefix(query,'tenant-1',job_id,view='samples',selector=pin)
            assert len(serializations)==(0 if fault=='witness' else 2) and not any(calls.values())
    finally:
        value[5].allowed=True;review['status']=review_status
        path.chmod(0o600);path.write_bytes(source);path.chmod(mode)
        if fault=='program':
            program_path.chmod(0o600);program_path.write_bytes(program_original);program_path.chmod(program_mode)
    assert reference.persisted_digest(worker.jobs)==before
    assert json.loads(public.read_prefix(query,'tenant-1',job_id))['prefix_status']=='accepted'
    save('late-'+fault,{'after_final_serialization_change_rejected':fault!='witness','missing_witness_denied_before_source':fault=='witness','fault':fault,'calls':calls,'DB_unchanged':True,'owned_source_restored':True})


@pytest.mark.parametrize('action',['heartbeat','cancel'])
def test_independent_change_after_serialization(setup,tmp_path,monkeypatch,action):
    query,worker,job_id,raw,value=setup
    lease=reference.confirm(worker,job_id);advance(worker,job_id,raw,lease,8)
    reference.readonly(value);original=read(query,job_id);pin=selector(original)
    serializer=public._public_bytes;serialized=[];observed=[]
    with lightweight_actor(worker,job_id,tmp_path,action) as change:
        def serialize(projected):
            wire=serializer(projected);serialized.append(wire)
            if len(serialized)==2:observed.append(change())
            return wire
        with monkeypatch.context() as patch:
            calls=reference.forbid(patch);patch.setattr(public,'_public_bytes',serialize)
            if action=='cancel':
                with pytest.raises(current.Co2PrefixPending):public.read_prefix(query,'tenant-1',job_id,selector=pin,view='samples')
            else:
                out=json.loads(public.read_prefix(query,'tenant-1',job_id,selector=pin,view='samples'))
                assert out['reference']['selector']==pin and out['reference']['checkpoint']['checkpoint_recorded_at']==original['selection']['checkpoint_recorded_at']
            assert len(observed)==1 and len(serialized)==2 and not any(calls.values())
    save('serialized-'+action,{'actor':observed[0],'product_query_calls':calls,'current_change_handled_after_final_serialization':True,
        'actor_SQL_is_intentional_test_control':True})


@pytest.mark.parametrize('confirmed',[False,True],ids=['private','confirmed'])
def test_new_original_rows_after_serialization_preserve_selected_public_page(setup,tmp_path,monkeypatch,confirmed):
    query,worker,job_id,raw,value=setup
    lease=reference.confirm(worker,job_id);_,first=advance(worker,job_id,raw,lease,2)
    pin={k:first['checkpoint'][k] for k in public.Selector.model_fields}
    _,artifact,_=reference.reference.producer.locations(worker.server,raw);path=artifact/'HEAD';old=path.read_bytes()
    progress=worker.server.advance('tenant-1',raw,budget=8);tail=json.loads(progress);new=path.read_bytes();mode=path.stat().st_mode&0o777
    assert all(tail['counts'][k]>first['checkpoint']['counts'][k] for k in ('samples','events'))
    with worker.server._open('tenant-1',raw,False) as (session,_):
        checkpoint,_=worker.checkpoints._snapshot(session,progress,2,lease['input_sha256'])
    try:
        path.chmod(0o600);path.write_bytes(old);path.chmod(mode);reference.readonly(value)
        expected=json.loads(public.read_prefix(query,'tenant-1',job_id,selector=pin,view='samples'))
        serializer=public._public_bytes;serialized=[];observed=[]
        with lightweight_actor(worker,job_id,tmp_path,'publish-original',head_path=str(path),head_raw=new.decode(),head_mode=mode,
                checkpoint=checkpoint if confirmed else None,event_kind=current.checkpoints.EVENT_KIND) as change:
            def serialize(projected):
                wire=serializer(projected);serialized.append(1)
                if len(serialized)==2:observed.append(change())
                return wire
            with monkeypatch.context() as patch:
                calls=reference.forbid(patch);patch.setattr(public,'_public_bytes',serialize)
                actual=json.loads(public.read_prefix(query,'tenant-1',job_id,selector=pin,view='samples'))
                expected['observed_at']=actual['observed_at'];assert actual==expected
                assert len(observed)==1 and len(serialized)==2 and not any(calls.values())
        save('serialized-append-'+str(confirmed),{'actor':observed[0],'same_original_public_page_UTC_first_time':True,
            'original_and_tail_counts':[first['checkpoint']['counts'],tail['counts']],'product_query_calls':calls,
            'actor_publishes_precomputed_original_not_new_numerics':True})
    finally:path.chmod(0o600);path.write_bytes(new);path.chmod(mode)


@pytest.mark.parametrize('producer_setup',['normal','hold'],indirect=True)
def test_actual_terminal_closed_keeps_existing_result(setup,monkeypatch):
    query,worker,job_id,raw,value=setup
    worker.server.advance('tenant-1',raw,budget=128);outcome=worker.run_once(job_id)
    assert outcome.state in ('succeeded','hold') and outcome.result_id
    reference.readonly(value);before=reference.persisted_digest(worker.jobs)
    with monkeypatch.context() as patch:
        calls=reference.forbid(patch);wire=public.read_prefix(query,'tenant-1',job_id);out=json.loads(wire)
        assert out['prefix_status']=='closed' and out['job']['state']==outcome.state
        assert out['reference'] is out['summary'] is out['page'] is None
        assert json.loads(query.query.read('tenant-1',job_id))['result']['result_id']==outcome.result_id
        assert not any(calls.values())
    assert reference.persisted_digest(worker.jobs)==before
    save('terminal-'+outcome.state,{'actual_scram':True,'closed_without_numeric_frames':True,'existing_result_link':True,'calls':calls,'DB_unchanged':True})


def test_actual_ready_without_invented_time_or_rows(setup,monkeypatch):
    query,worker,job_id,raw,value=setup;lease=reference.confirm(worker,job_id)
    with monkeypatch.context() as patch:
        def stop(*a,**kw):raise RuntimeError('owned stop after signed initialization')
        patch.setattr(current.custody.continuation,'advance_chunk',stop)
        with pytest.raises(current.custody.Co2CustodyHold):worker.server.advance('tenant-1',raw,budget=1)
    cp=worker.checkpoints.confirm('tenant-1',job_id,attempt=lease['attempt'],lease_token=lease['lease_token'])
    pin={k:cp['checkpoint'][k] for k in public.Selector.model_fields}
    reference.readonly(value);before=reference.persisted_digest(worker.jobs)
    with monkeypatch.context() as patch:
        calls=reference.forbid(patch);out=json.loads(public.read_prefix(query,'tenant-1',job_id))
        assert out['reference']['checkpoint']['status']=='ready' and out['reference']['checkpoint']['computed_through_utc'] is None
        assert out['summary']=={'counts':{'samples':0,'events':0},'last_sample_utc':None,'last_event_utc':None}
        for view in ('samples','events'):
            page=json.loads(public.read_prefix(query,'tenant-1',job_id,selector=pin,view=view))['page']
            assert page['total']==0 and page['records']==[] and page['next_offset'] is None
        assert not any(calls.values())
    assert reference.persisted_digest(worker.jobs)==before
    save('actual-ready',{'actual_scram':True,'no_invented_numeric_frames_or_times':True,'calls':calls,'DB_unchanged':True})


@pytest.mark.parametrize('producer_setup',['dense'],indirect=True)
def test_actual_dense_64_plus_one_public_pages(setup,monkeypatch):
    query,worker,job_id,raw,value=setup;c=current.custody.continuation;ctx=value[2][2]._context
    expected=c.advance_chunk(ctx,c.start(ctx),128)
    lease=reference.confirm(worker,job_id);advance(worker,job_id,raw,lease,64);_,last=advance(worker,job_id,raw,lease,1)
    pin={k:last['checkpoint'][k] for k in public.Selector.model_fields};reference.readonly(value);before=reference.persisted_digest(worker.jobs)
    rows=[];sizes=[]
    with monkeypatch.context() as patch:
        calls=reference.forbid(patch)
        for start in (0,64):
            raw_response=public.read_prefix(query,'tenant-1',job_id,selector=pin,view='samples',start=start)
            page=json.loads(raw_response)['page'];rows.extend(page['records']);sizes.append(len(raw_response))
            assert len(page['records'])==(64 if start==0 else 1) and page['next_offset']==(64 if start==0 else None)
        assert current.execution._same([r['value'] for r in rows],expected['samples'])
        assert [r['time']['at'] for r in rows]==[current.custody.clock.at_index(value[2][2],r['step_index']) for r in expected['samples']]
        assert not any(calls.values())
    assert reference.persisted_digest(worker.jobs)==before
    save('actual-dense',{'actual_scram':True,'original_rows':65,'page_counts':[64,1],'original_values_units_UTC':True,
        'response_bytes':sizes,'calls':calls,'DB_unchanged':True})


@pytest.mark.parametrize('producer_setup',['basis-transition'],indirect=True)
def test_actual_source_program_basis_and_same_UTC_event_boundary(setup,monkeypatch):
    query,worker,job_id,raw,value=setup
    lease=reference.confirm(worker,job_id);progress,accepted=advance(worker,job_id,raw,lease,9)
    assert progress['steps']==8
    pin={k:accepted['checkpoint'][k] for k in public.Selector.model_fields}
    reference.readonly(value);before=reference.persisted_digest(worker.jobs)
    with monkeypatch.context() as patch:
        calls=reference.forbid(patch)
        source=query.read('tenant-1',job_id,selector=pin,view='samples')
        program=query._source_program('tenant-1',job_id,source)
        assert program==value[2][2]._context.program
        samples=json.loads(public.read_prefix(query,'tenant-1',job_id,selector=pin,view='samples'))['page']['records']
        events=json.loads(public.read_prefix(query,'tenant-1',job_id,selector=pin,view='events'))['page']['records']
        bases={row['step_index']:row['co2']['basis'] for row in program['forcing_program']}
        assert {row['co2_basis'] for row in samples}=={'wet','dry'}
        for row in samples+events:
            assert row['co2_basis']==bases[row['value']['forcing_step_index']]
        event=next(row for row in events if row['value']['step_index']==8)
        sample=next(row for row in samples if row['value']['step_index']==8)
        assert event['time']==sample['time'] and event['co2_basis']==sample['co2_basis']=='wet'
        assert event['value']['forcing_step_index']==sample['value']['forcing_step_index']==8
        assert next(row for row in samples if row['value']['step_index']==4)['co2_basis']=='dry'
        preserved=deepcopy(samples)
        for row in preserved:row.pop('co2_basis')
        assert preserved==json.loads(source.payload_raw)['page']['records']
        assert not any(calls.values())
    assert reference.persisted_digest(worker.jobs)==before
    save('actual-basis',{'actual_scram':True,'actual32s_input_variant':True,'steps':8,
        'selected_program_equals_original_context':True,'original_values_units_UTC_preserved':True,
        'same_UTC_new_forcing_before_event_and_output':True,
        'source_program_not_reconstructed_from_public_payload':True,'calls':calls,'DB_unchanged':True})
