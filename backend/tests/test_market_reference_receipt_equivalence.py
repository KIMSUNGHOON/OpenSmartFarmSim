"""Differential evidence and counterexamples; no runtime shortcuts enabled."""
from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path

import pytest
from psycopg import sql

from app import market_reference_bundle as bundles, market_reference_receipts as receipts
from app import market_source_store as sources
from app.economic_contracts import OwnedEconomicRecord,EconomicScenario,PriorBatchCostRecord
from app.jobs import canonical_input_bytes
from test_market_current_reference_bundle import (replay_trace,registration,authoring,profiles,
    login_database,original_login_scope,login_scope,query_cleanup,pytestmark)

_spec=importlib.util.spec_from_file_location('receipt_equivalence_evidence',Path(__file__).resolve().parents[2]/'research/market-reference-receipt-equivalence.py')
proof=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(proof)


def save(name,value):
    root=os.environ.get('OSSF_SHARED_MARKET_EVIDENCE')
    if root:
        path=Path(root)/('receipt-equivalence-'+name+'.json')
        with path.open('x') as stream:
            os.fchmod(stream.fileno(),0o400);json.dump(value,stream,sort_keys=True);stream.flush();os.fsync(stream.fileno())


@pytest.fixture
def evidence(replay_trace,login_scope,monkeypatch):
    owner,tenant,trace,principal=replay_trace
    base,policy,_=login_scope
    with base.connect() as conn:
        pin_keys=tuple(dict.fromkeys(args for name,args,_ in trace if name in proof.SCENARIOS))
        pins={key for key in pin_keys if conn.execute(sql.SQL('SELECT 1 FROM {} WHERE tenant_id=%s AND scenario_id=%s AND revision=%s')
            .format(sql.Identifier(policy.schema,'market_candidate_pins')),(tenant,*key)).fetchone()}
        input_keys=tuple(dict.fromkeys(args for name,args,_ in trace if name=='get_economic_input'))
        present={key for key in input_keys if conn.execute(sql.SQL('SELECT 1 FROM {} WHERE tenant_id=%s AND input_id=%s AND revision=%s')
            .format(sql.Identifier(policy.schema,'market_candidate_inputs')),(tenant,*key)).fetchone()}
    plan=proof.trace_plan(trace,present,pins);assert plan is not None and pins
    original=bundles._verify_trace
    def run(consume,selected_plan=plan):
        def primitive(store,selected,slot,lookups):
            bundle=bundles._Bundle(store,selected,slot,store._reference_reader(selected));bundle.token=slot.set(bundle)
            try:
                def visit(reader):consume(reader,lambda:original(store,selected,slot,lookups))
                return receipts.verify_receipts(store,selected,selected_plan['source_keys'],selected_plan['candidate_keys'],selected_plan['pin_keys'],visit)
            finally:bundle.close()
        with monkeypatch.context() as patch:
            patch.setattr(bundles,'_verify_trace',primitive)
            return owner.verify_current_reads(tenant,trace)
    return owner,tenant,trace,principal,plan,pins,run


def test_original_full_trace_and_stable_default_dependency_envelope(evidence):
    owner,_,trace,_,plan,_,run=evidence
    counts={name:sum(n==name for n,_,_ in trace) for name,_,_ in trace}
    assert proof.default_methods(owner)
    def consume(reader,full):
        before=proof.envelope(owner)
        full();full()
        assert proof.envelope(owner)==before
        assert sum(len(keys) for keys in reader.keys)<=128
    assert run(consume) is None
    assert len(plan['pure_indexes'])+len(plan['dynamic_indexes'])==len(trace)
    assert counts['get_economic_input']>0
    save('full-trace',{'logical_reads':len(trace),'counts_by_method':counts,'source_keys':len(plan['source_keys']),'candidate_keys':len(plan['candidate_keys']),'pin_keys':len(plan['pin_keys']),'pure_indexes':len(plan['pure_indexes']),'dynamic_indexes':len(plan['dynamic_indexes']),'original_full_trace_repetitions':2,'values_and_order_preserved':True,'dependency_envelope_stable':True})


def test_all_seven_default_source_families_and_both_pins_are_stable(evidence,login_scope):
    owner,tenant,_,_,_,_,run=evidence
    base,policy,_=login_scope;source=owner._source._source
    from test_economics import base as economic_base,opening_lot,TrustedTestRepository
    prior=TrustedTestRepository(EconomicScenario.model_validate(economic_base(opening_inventory=(opening_lot(),))))
    for raw in prior.prior_costs.values():
        model=PriorBatchCostRecord.model_validate(raw);job=base.submit(tenant,'simulation',model.model_dump(mode='json'),'proof-prior-cost')
        source.adopt_job(tenant,'prior_batch_cost',str(job['job_id']))
    with base.connect() as conn:
        rows=conn.execute(sql.SQL('SELECT kind,record_id,revision,payload_raw FROM {} WHERE tenant_id=%s ORDER BY kind,record_id,revision')
            .format(sql.Identifier(policy.schema,'market_source_records')),(tenant,)).fetchall()
    assert {row['kind'] for row in rows}==set(sources._KINDS)
    methods={kind:name for name,kind in proof.SOURCE_KINDS.items() if not name.endswith('_pin')}
    expected=[];keys=[]
    for row in rows:
        model,identity,revision=source._model(row['kind'],tenant,row['payload_raw'])
        assert (identity,revision)==(row['record_id'],row['revision'])
        args=(identity,) if row['kind']=='prior_batch_cost' else (identity,revision)
        expected.append((methods[row['kind']],args,bundles.fingerprint(model.model_dump(mode='python'))))
        keys.append((row['kind'],identity,revision))
    plan={'source_keys':tuple(keys),'candidate_keys':(),'pin_keys':()}
    def consume(reader,_):
        before=proof.envelope(owner)
        for _ in range(2):
            for name,args,digest in expected:assert bundles.fingerprint(getattr(source,name)(*args))==digest
        scenario=next(row for row in rows if row['kind']=='economic_scenario')
        shock=next(row for row in rows if row['kind']=='joint_shock')
        assert source.get_economic_scenario_pin(scenario['record_id'],scenario['revision'])['immutable'] is True
        assert source.get_joint_shock_pin(shock['record_id'],shock['revision'])['immutable'] is True
        assert proof.envelope(owner)==before
    assert run(consume,plan) is None
    save('seven-families',{'families':sorted(sources._KINDS),'source_records':len(rows),'default_return_comparisons':2*len(expected),'source_pin_paths':2,'raw_receipts_stable':True})


@pytest.mark.parametrize('change',['instance_method','kind_registry','validator','serializer','decimal','policy'])
def test_equal_receipts_do_not_prove_unchanged_decoder_or_settings(evidence,monkeypatch,change):
    owner,tenant,trace,_,_,_,run=evidence
    source=owner._source._source
    def consume(reader,full):
        before=proof.envelope(owner)
        from decimal import localcontext
        with monkeypatch.context() as patch,localcontext() as ctx:
            if change=='instance_method':
                def denied(*_a,**_k):raise ValueError('research replacement decoder')
                patch.setattr(source,'get_economic_input',denied)
            elif change=='kind_registry':patch.setitem(sources._KINDS,'economic_input',(EconomicScenario,'scenario_id','scenario_revision'))
            elif change=='validator':
                class Denied:
                    def validate_json(self,*_a,**_kw):raise ValueError('research validator drift')
                patch.setattr(OwnedEconomicRecord,'__pydantic_validator__',Denied())
            elif change=='policy':patch.setattr(sources,'VERSION','research-policy-drift')
            elif change=='serializer':
                class Denied:
                    def to_python(self,*_a,**_kw):raise ValueError('research serializer drift')
                patch.setattr(OwnedEconomicRecord,'__pydantic_serializer__',Denied())
            else:ctx.prec+=1
            assert proof.envelope(owner)!=before
            if change=='decimal':full()
            else:
                with pytest.raises(ValueError):full()
        assert proof.envelope(owner)==before
    # Identical raw SQL receipts still pass. A runtime dependency guard is required.
    assert run(consume) is None



def test_closed_planner_rejects_unknown_and_keeps_derived_candidate_reads(evidence):
    _,_,trace,_,plan,pins,_=evidence
    assert proof.trace_plan((*trace,('unknown_callback',('x',),b'x'*32)),set(),pins) is None
    assert all(index in plan['dynamic_indexes'] for index,(name,args,_) in enumerate(trace)
        if name in proof.DYNAMIC or (name in proof.SCENARIOS and args in pins))
    assert all(index not in plan['pure_indexes'] for index in plan['dynamic_indexes'])


def test_candidate_priority_omits_unused_source_dependency(evidence,login_scope,monkeypatch):
    owner,tenant,trace,_,_,pins,run=evidence
    base,policy,_=login_scope
    key=next(args for name,args,_ in trace if name=='get_economic_input')
    with base.connect() as conn:
        raw=conn.execute(sql.SQL('SELECT payload_raw FROM {} WHERE tenant_id=%s AND kind=\'economic_input\' AND record_id=%s AND revision=%s')
            .format(sql.Identifier(policy.schema,'market_source_records')),(tenant,*key)).fetchone()['payload_raw']
        conn.execute(sql.SQL('INSERT INTO {}(tenant_id,input_id,revision,payload_raw,payload_sha256) VALUES(%s,%s,%s,%s,%s)')
            .format(sql.Identifier(policy.schema,'market_candidate_inputs')),(tenant,*key,raw,sha256(raw).hexdigest()))
    selected=tuple(item for item in trace if item[0]=='get_economic_input' and item[1]==key)
    plan=proof.trace_plan(selected,{key},set())
    assert plan['source_keys']==() and plan['candidate_keys']==(key,)
    source=owner._source._source;calls=[];read=source._read_in_transaction
    def observed(*args,**kwargs):calls.append(1);return read(*args,**kwargs)
    monkeypatch.setattr(source,'_read_in_transaction',observed)
    def consume(reader,_):
        expected=OwnedEconomicRecord.model_validate_json(raw).model_dump(mode='python')
        assert owner.get_economic_input(*key)==expected
        with base.connect() as conn:
            target=sql.Identifier(policy.schema,'market_source_records')
            conn.execute(sql.SQL('ALTER TABLE {} DISABLE TRIGGER USER').format(target))
            conn.execute(sql.SQL('UPDATE {} SET payload_raw=%s,payload_sha256=%s WHERE tenant_id=%s AND kind=\'economic_input\' AND record_id=%s AND revision=%s')
                .format(target),(b'{}',sha256(b'{}').hexdigest(),tenant,*key))
        assert owner.get_economic_input(*key)==expected and calls==[]
    assert run(consume,plan) is None
    save('candidate-priority',{'unused_source_keys':0,'source_getter_calls':0,'before_after_candidate_values_equal':True,'unused_source_changed':True})


def test_manifest_dependency_outside_trace_can_change_with_equal_explicit_receipts(evidence,login_scope):
    owner,tenant,trace,_,plan,pins,run=evidence
    base,policy,_=login_scope
    pin=next(iter(pins));extra=('proof-manifest-extra','r1')
    assert extra not in plan['candidate_keys']
    tables={name:sql.Identifier(policy.schema,name) for name in ('market_candidate_inputs','market_candidate_pins','market_source_records')}
    with base.connect() as conn:
        row=conn.execute(sql.SQL('SELECT payload_raw FROM {} WHERE tenant_id=%s AND kind=\'economic_input\' LIMIT 1').format(tables['market_source_records']),(tenant,)).fetchone()
        data=json.loads(row['payload_raw']);data.update(input_id=extra[0],revision=extra[1]);raw=canonical_input_bytes(data)
        conn.execute(sql.SQL('INSERT INTO {}(tenant_id,input_id,revision,payload_raw,payload_sha256) VALUES(%s,%s,%s,%s,%s)').format(tables['market_candidate_inputs']),(tenant,*extra,raw,sha256(raw).hexdigest()))
        pinrow=conn.execute(sql.SQL('SELECT inputs_manifest_raw FROM {} WHERE tenant_id=%s AND scenario_id=%s AND revision=%s').format(tables['market_candidate_pins']),(tenant,*pin)).fetchone()
        manifest=json.loads(pinrow['inputs_manifest_raw']);manifest.append({'input_id':extra[0],'revision':extra[1],'sha256':sha256(raw).hexdigest()});manifest.sort(key=lambda v:(v['input_id'],v['revision']))
        encoded=json.dumps(manifest,sort_keys=True,separators=(',',':')).encode()
        conn.execute(sql.SQL('ALTER TABLE {} DISABLE TRIGGER USER').format(tables['market_candidate_pins']))
        conn.execute(sql.SQL('UPDATE {} SET inputs_manifest_raw=%s,inputs_manifest_sha256=%s WHERE tenant_id=%s AND scenario_id=%s AND revision=%s').format(tables['market_candidate_pins']),(encoded,sha256(encoded).hexdigest(),tenant,*pin))
    original=owner.get_market_candidate(*pin);assert original is not None
    def consume(reader,full):
        before=proof.envelope(owner);full()
        with base.connect() as conn:
            conn.execute(sql.SQL('ALTER TABLE {} DISABLE TRIGGER USER').format(tables['market_candidate_inputs']))
            data['value']='987654';changed=canonical_input_bytes(data)
            conn.execute(sql.SQL('UPDATE {} SET payload_raw=%s,payload_sha256=%s WHERE tenant_id=%s AND input_id=%s AND revision=%s').format(tables['market_candidate_inputs']),(changed,sha256(changed).hexdigest(),tenant,*extra))
        with pytest.raises(ValueError):owner.get_market_candidate(*pin)
        assert proof.envelope(owner)==before
    # Receipts for only explicit trace keys agree; original dynamic validation fails.
    assert run(consume) is None
    save('manifest-negative-control',{'explicit_receipts_stable':True,'dependency_envelope_stable':True,'unrecorded_manifest_input_changed':True,'actual_candidate_validation_denied':True,'derived_getters_must_remain_dynamic':True})


def test_live_bearer_expiry_is_not_a_raw_data_or_pure_envelope_property(evidence,monkeypatch):
    from datetime import datetime,timedelta,timezone
    from app import http_identity as identity
    owner,tenant,_,principal,_,_,run=evidence
    clock=[datetime(2026,10,1,tzinfo=timezone.utc)]
    grant=identity.BearerGrant('a'*64,tenant,frozenset(principal['scopes']),clock[0],clock[0]+timedelta(seconds=1))
    registry=identity.BearerRegistry((grant,),clock=lambda:clock[0])
    token=identity._PRINCIPAL.set(identity._RequestIdentity(grant,registry))
    try:
        with monkeypatch.context() as patch:
            for instance in (owner,owner._source,owner._source._source,owner._source._holds,owner._source._holds._context_store):
                patch.setattr(instance,'_principal_provider',identity.current_principal)
            def consume(reader,full):
                before=proof.envelope(owner);assert owner.tenant_is_authenticated(tenant)
                clock[0]+=timedelta(seconds=2)
                assert identity.current_principal() is None and not owner.tenant_is_authenticated(tenant)
                assert proof.envelope(owner)==before
                with pytest.raises(ValueError):full()
            with pytest.raises(ValueError):run(consume)
    finally:identity._PRINCIPAL.reset(token)
    save('bearer-expiry',{'pure_dependency_envelope_stable':True,'current_principal_expired':True,'actual_current_verifier_denied':True,'permission_cache_permitted':False})
