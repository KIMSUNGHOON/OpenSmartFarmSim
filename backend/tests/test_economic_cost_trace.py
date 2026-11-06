"""Independent item arithmetic for self-authored assumptions; no farm forecast."""
from datetime import datetime,timezone,timedelta
from decimal import Decimal,localcontext,ROUND_FLOOR
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys

import pytest

from app.economic_cost_trace import CostLineLedger,trace_bytes
from app.economic_production_batches import ProductionBatchLedger,BatchEconomicScenario,result_bytes
from test_economic_production_batches import scenario,Repository
from test_economics import n,T
from test_economics_settlement import example as settlement_example


def settled(future=False):
    d=settlement_example();d.update(schema_version='4',production_batches=({'batch_id':'batch-1','revision':'r1'},))
    if future:
        from test_economics import settlement_record
        d['setoffs'][0]['at']=datetime(2026,11,1,tzinfo=timezone.utc)
        d['setoffs'][0]['evidence_sha256']=settlement_record(d,d['setoffs'][0])['raw_sha256']
    return BatchEconomicScenario.model_validate(d)


def run(s=None,repo=None):
    s=scenario()if s is None else s
    return CostLineLedger(repo or Repository(s)).calculate(s)


def test_line_keeps_original_cost_inputs_and_original_v10_result():
    s=scenario();repo=Repository(s);original=ProductionBatchLedger(repo).calculate(s)
    result=run(s,repo);line=result.lines[0]
    assert result.trace_version=='economic-cost-line-trace-v1'
    assert line.category=='variable'and line.cost==s.variable_costs[0]
    assert line.incurred==line.bank_paid_in_period==Decimal('20')
    assert line.remaining_payable_at_period_end==0 and line.payment_status=='declared_bank_payment'
    assert result_bytes(result.base_result)==result_bytes(original)
    assert result.groups[0].incurred==original.ledger.variable_cost
    assert result.ledger_payable_reconciliation=='matched'
    raw=trace_bytes(result);value=json.loads(raw)
    assert value['lines'][0]['incurred']=='20'and value['base_result']==json.loads(result_bytes(original))
    assert value['G0_G4']=='not_assessed'and value['R2']=='not_approved'
    assert value['currency']=='KRW'


def test_mixed_drivers_and_partial_payment_reconcile_batch_and_group():
    d=scenario().model_dump();one=d['variable_costs'][0]
    one['payment']=n('7','partial','KRW')
    second=one|{'id':'electricity','quantity':n('12.5','electricity-q','kWh_e'),
        'unit_cost':n('3.25','electricity-price','KRW/kWh_e'),'payment':n('40.625','electricity-paid','KRW')}
    fixed=one|{'id':'fixed','quantity':n('2','fixed-q','month'),'unit_cost':n('3','fixed-price','KRW/month'),
        'payment':n('6','fixed-paid','KRW')}
    d.update(variable_costs=(one,second),fixed_costs=(fixed,))
    d['zero_declarations']=tuple(z for z in d['zero_declarations']if z['group']!='fixed_costs')
    s=BatchEconomicScenario.model_validate(d);result=run(s)
    with localcontext()as ctx:
        ctx.prec=300;expected=Decimal('12.5')*Decimal('3.25')
    assert [line.incurred for line in result.lines]==[Decimal('20'),expected,Decimal('6')]
    assert result.groups[0].incurred==Decimal('20')+expected
    assert result.base_result.batch_costs[0].remaining_payable_at_period_end==Decimal('13')
    assert sum(line.remaining_payable_at_period_end for line in result.lines)==13


def test_unknown_payment_is_null_and_known_part_is_not_total():
    d=scenario().model_dump();d['variable_costs'][0].update(payment=None,paid_at=None)
    result=run(BatchEconomicScenario.model_validate(d));line=result.lines[0]
    assert line.incurred==20 and line.bank_paid_in_period is None
    assert line.remaining_payable_at_period_end is None and line.payment_status=='undeclared_payment'
    assert result.months[0].known_bank_outflow==0 and result.months[0].bank_outflow is None
    assert result.ledger_payable_reconciliation=='unavailable'


def test_KST_boundary_and_period_after_payment_remain_original_events():
    d=scenario().model_dump();d['variable_costs'][0]['paid_at']=datetime(2026,10,31,15,tzinfo=timezone.utc)
    result=run(BatchEconomicScenario.model_validate(d))
    assert [m.bank_outflow for m in result.months]==[0,Decimal('20')]
    d['variable_costs'][0]['paid_at']=datetime(2026,12,1,tzinfo=timezone.utc)
    result=run(BatchEconomicScenario.model_validate(d));line=result.lines[0]
    assert line.bank_paid_in_period==0 and line.bank_paid_after_period==20
    assert line.remaining_payable_at_period_end==20


@pytest.mark.parametrize('future',[False,True])
def test_sale_setoff_is_not_bank_payment_and_future_schedule_is_preserved(future):
    s=settled(future);result=run(s);line=next(v for v in result.lines if v.cost.id=='fee')
    assert line.setoff==s.setoffs[0]and line.payment_status=='declared_setoff'
    assert line.incurred==60 and line.bank_paid_in_period==line.bank_paid_after_period==0
    assert line.setoff_in_period==(0 if future else 60)
    assert line.remaining_payable_at_period_end==(60 if future else 0)
    assert result.months[0].bank_outflow==70 and result.months[0].ledger_net==770
    assert result.groups[0].incurred==130 and result.groups[0].bank_paid_in_period==70
    assert result.ledger_payable_reconciliation=='matched'


@pytest.mark.parametrize('which',['variable','fixed'])
def test_missing_group_differs_from_declared_zero(which):
    d=scenario().model_dump();d[which+'_costs']=None
    d['zero_declarations']=tuple(v for v in d['zero_declarations']if v['group']!=which+'_costs')
    result=run(BatchEconomicScenario.model_validate(d))
    group=next(v for v in result.groups if v.category==which)
    assert not group.declared and group.incurred is None
    assert all(v.bank_outflow is None for v in result.months)
    declared=run();assert declared.groups[1].declared and declared.groups[1].incurred==0


@pytest.mark.parametrize('which',['variable_costs','fixed_costs','setoffs'])
def test_empty_group_without_owned_zero_evidence_remains_unknown(which):
    d=scenario().model_dump();d[which]=()
    d['zero_declarations']=tuple(v for v in d['zero_declarations']if v['group']!=which)
    s=BatchEconomicScenario.model_validate(d);result=run(s)
    if which=='setoffs':assert not result.setoffs_declared
    else:
        group=next(v for v in result.groups if v.category==which.removesuffix('_costs'))
        assert not group.declared and group.incurred is None
        assert all(v.bank_outflow is None for v in result.months)


def test_multiple_batches_and_period_fixed_cost_keep_distinct_scopes():
    d=scenario().model_dump();cost=d['variable_costs'][0]
    other=cost|{'id':'other-production','batch_id':'batch-2','quantity':n(2,'other-q'),
        'unit_cost':n(3,'other-price','KRW/kg'),'payment':n(4,'other-payment','KRW')}
    rent=cost|{'id':'rent','purpose':'period','batch_id':None,'quantity':n(1,'rent-q','month'),
        'unit_cost':n(10,'rent-price','KRW/month'),'payment':n(10,'rent-payment','KRW')}
    d.update(variable_costs=(cost,other),fixed_costs=(rent,),production_batches=(
        {'batch_id':'batch-1','revision':'r1'},{'batch_id':'batch-2','revision':'r1'}))
    d['zero_declarations']=tuple(v for v in d['zero_declarations']if v['group']!='fixed_costs')
    result=run(BatchEconomicScenario.model_validate(d))
    assert [(v.batch_id,v.variable_incurred,v.fixed_incurred,v.remaining_payable_at_period_end)
        for v in result.base_result.batch_costs]==[('batch-1',20,0,0),('batch-2',6,0,2)]
    assert [v.incurred for v in result.groups]==[26,10]and result.groups[0].remaining_payable_at_period_end==2
    assert result.months[0].known_bank_outflow==34


@pytest.mark.parametrize('bad',['duplicate','missing_record','different_value','different_owner','late_available','scope'])
def test_existing_numeric_owner_revision_and_scope_checks_still_apply(bad):
    s=scenario();repo=Repository(s)
    if bad=='duplicate':
        d=s.model_dump();other=d['variable_costs'][0]|{'quantity':n(1,'duplicate-q'),
            'unit_cost':n(1,'duplicate-rate','KRW/kg'),'payment':n(1,'duplicate-paid','KRW')}
        d['variable_costs']=(*d['variable_costs'],other);s=BatchEconomicScenario.model_validate(d);repo=Repository(s)
    else:
        key=(s.variable_costs[0].quantity.input_id,'r1');record=repo.records[key]
        if bad=='missing_record':repo.records.pop(key)
        elif bad=='different_value':record['value']='999'
        elif bad=='different_owner':record['tenant_id']='other'
        elif bad=='late_available':record['available_at']=datetime(2026,12,1,tzinfo=timezone.utc)
        else:record['scope_end']=s.period_start
    with pytest.raises(ValueError):run(s,repo)


@pytest.mark.parametrize('part',['input','batch','auth','repository'])
def test_late_change_blocks_trace_return(monkeypatch,part):
    import app.economic_cost_trace as mod
    s=scenario();repo=Repository(s);kernel=CostLineLedger(repo);actual=mod._line
    def changed(*args):
        line=actual(*args)
        if part=='input':repo.records[(s.variable_costs[0].quantity.input_id,'r1')]['value']='999'
        elif part=='batch':repo.batches[('batch-1','r1')]['source_ref']='different-current-record'
        elif part=='auth':repo.authenticated=False
        else:kernel._repository=Repository(s)
        return line
    monkeypatch.setattr(mod,'_line',changed)
    with pytest.raises(ValueError):kernel.calculate(s)


def test_final_auth_revoke_inside_last_context_is_checked(monkeypatch):
    s=scenario();repo=Repository(s);actual=repo.get_production_batch;calls=[]
    def revoke(*args):
        result=actual(*args);calls.append(1)
        if len(calls)==4:repo.authenticated=False
        return result
    monkeypatch.setattr(repo,'get_production_batch',revoke)
    with pytest.raises(ValueError,match='current tenant'):run(s,repo)


def test_code_fence_and_independent_input_output_bounds(monkeypatch,tmp_path):
    import app.economic_cost_trace as mod
    raw=Path(mod.__file__).read_bytes();local=tmp_path/'loaded.py';local.write_bytes(raw)
    monkeypatch.setattr(mod,'__file__',str(local));actual=mod._line
    def changed(*args):
        result=actual(*args);local.write_bytes(raw+b'\n');return result
    with monkeypatch.context()as patch:
        patch.setattr(mod,'_line',changed)
        with pytest.raises(ValueError,match='CODE_HOLD'):run()
    local.write_bytes(raw);result=run();encoded=trace_bytes(result)
    with monkeypatch.context()as patch:
        patch.setattr(mod,'MAX_BYTES',len(encoded)-1)
        with pytest.raises(ValueError,match='CAPACITY_HOLD'):run()
    s=scenario()
    from app.economic_production_batches import _raw
    with monkeypatch.context()as patch:
        patch.setattr(mod,'MAX_BYTES',len(_raw(s))-1)
        patch.setattr(ProductionBatchLedger,'calculate',lambda *_:pytest.fail('input limit before math'))
        with pytest.raises(ValueError,match='CAPACITY_HOLD'):run(s)


def test_component_fence_reconciliation_and_return_copies(monkeypatch):
    import app.economic_cost_trace as mod
    s=scenario();repo=Repository(s);first=run(s,repo);raw=trace_bytes(first)
    first.component_sha256.clear();first.base_result.component_sha256.clear()
    assert trace_bytes(run(s,repo))==raw
    actual=mod._line
    monkeypatch.setattr(mod,'_line',lambda *args:replace(actual(*args),incurred=Decimal('999')))
    with pytest.raises(ValueError,match='differs'):run(s,repo)


def test_caller_decimal_context_does_not_change_trace_identity_or_serialization():
    expected=sha256(trace_bytes(run())).hexdigest()
    with localcontext()as ctx:
        ctx.prec=2;ctx.rounding=ROUND_FLOOR;ctx.Emax=2;ctx.Emin=-2;ctx.capitals=0
        actual=sha256(trace_bytes(run())).hexdigest()
    assert actual==expected


def test_independent_high_precision_oracle_and_fresh_process(tmp_path):
    d=scenario().model_dump();d['variable_costs'][0].update(
        quantity=n('9'*60,'large-q'),unit_cost=n('8'*60,'large-price','KRW/kg'),payment=n(0,'large-paid','KRW'))
    boundary=scenario().model_dump();boundary['variable_costs'][0]['paid_at']=datetime(2026,10,31,15,tzinfo=timezone.utc)
    future=scenario().model_dump();future['variable_costs'][0]['paid_at']=datetime(2026,12,1,tzinfo=timezone.utc)
    cases=[scenario(),BatchEconomicScenario.model_validate(d),settled(),settled(True),
        BatchEconomicScenario.model_validate(boundary),BatchEconomicScenario.model_validate(future)]
    expected=[];oracle_count=0
    for s in cases:
        with localcontext()as ctx:
            ctx.prec=300
            amounts=[Decimal(c.quantity.value)*Decimal(c.unit_cost.value)for group in
                (s.variable_costs,s.fixed_costs)for c in group or ()]
            with localcontext()as small:
                small.prec=3;small.Emax=2;small.Emin=-2;small.rounding=ROUND_FLOOR;small.capitals=0
                result=run(s)
            assert [line.incurred for line in result.lines]==amounts;oracle_count+=len(amounts)
            for name,group in [('variable',s.variable_costs),('fixed',s.fixed_costs)]:
                expected_sum=sum((Decimal(c.quantity.value)*Decimal(c.unit_cost.value)for c in group or ()),Decimal(0))
                assert next(v.incurred for v in result.groups if v.category==name)==expected_sum
            zone=timezone(timedelta(hours=9))
            for month in result.months:
                bank=sum((Decimal(c.payment.value)for group in(s.variable_costs,s.fixed_costs)for c in group or ()
                    if c.payment is not None and s.period_start<=c.paid_at.astimezone(zone).date()<=s.period_end and
                    c.paid_at.astimezone(zone).strftime('%Y-%m')==month.month),Decimal(0))
                receipts=sum((Decimal(c.amount.value)for c in s.collections or ()if
                    c.at.astimezone(zone).strftime('%Y-%m')==month.month),Decimal(0))
                assert month.bank_outflow==month.known_bank_outflow==bank
                assert month.ledger_net==receipts-bank
        expected.append(sha256(trace_bytes(result)).hexdigest())
    source=tmp_path/'self-authored-cases.private.json';source.write_text(json.dumps([s.model_dump(mode='json')for s in cases]))
    output=tmp_path/'cold-trace-results.private.json'
    child=subprocess.run([sys.executable,'-B',str(Path(__file__).with_name('economic_cost_trace_cold.py')),
        str(source),str(output)],capture_output=True,timeout=30)
    assert child.returncode==0 and child.stdout==child.stderr==b''
    found=json.loads(output.read_bytes());assert found['trace_sha256']==expected
    assert found['cases']==6 and found['same_final_code']
    receipt={'cases':6,'independent_Decimal_precision':300,'oracle_cost_lines':oracle_count,
        'source_trace_sha256':expected,'actual_fresh_Python_process':True,'production_DB_or_HTTP':False,
        'G0_G4':'not_assessed','R2':'not_approved'}
    (tmp_path/'cost-trace-oracle-receipt.private.json').write_text(json.dumps(receipt,indent=2))
