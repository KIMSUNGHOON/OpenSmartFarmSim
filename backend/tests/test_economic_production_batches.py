"""Self-authored conditional batches; fake repositories are not farm authority."""
from copy import deepcopy
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest

from app.economic_contracts import EconomicScenario
from app.economics import EconomicLedger, canonical_scenario_sha256
from app.economic_production_batches import (
    BatchEconomicScenario, ProductionBatchLedger, FORMULA_VERSION,
)
from test_economics import base, n, T, DECISION, TrustedTestRepository, opening_lot


def batch_record(s, batch_id='batch-1'):
    return dict(batch_id=batch_id, revision='r1', tenant_id=s.tenant_id,
                production_start_at=T(1), origin='user', evidence_level='assumed',
                source_ref='self-authored-batch', assumption_scope='scenario-1:production',
                available_at=DECISION, scope_start=s.period_start, scope_end=s.period_end,
                rights='conditional_g1_use', immutable=True)


class Repository(TrustedTestRepository):
    def __init__(self, s):
        super().__init__(s)
        self.batches = {(p.batch_id, p.revision): batch_record(s, p.batch_id)
                        for p in s.production_batches}

    def get_production_batch(self, batch_id, revision):
        return deepcopy(self.batches.get((batch_id, revision)))


def scenario(harvest=False, **changes):
    overrides = {} if harvest else dict(harvests=(), packouts=(), culls=(), cull_disposals=(),
                                       sales=(), collections=())
    overrides.update(changes)
    d=base(**overrides)
    if not harvest and 'variable_costs' not in changes:
        d['variable_costs'] = d['variable_costs'][:1]
    d.update(schema_version='4', production_batches=({'batch_id':'batch-1','revision':'r1'},))
    return BatchEconomicScenario.model_validate(d)


def run(s=None, repo=None):
    s=scenario() if s is None else s
    return ProductionBatchLedger(repo or Repository(s)).calculate(s)


def test_no_harvest_or_sales_are_created_and_direct_cost_enters_v_once():
    s=scenario();before=s.model_dump();r=run(s)
    assert s.model_dump()==before and not s.harvests and not s.sales
    assert r.ledger.variable_cost==Decimal('20')
    assert r.ledger.harvest_kg==r.ledger.recognized_kg==r.ledger.revenue==0
    assert r.ledger.management_oi==Decimal('-20')
    assert r.ledger.operating_cash==r.ledger.operating_cash_bridge==Decimal('-20')
    assert r.ledger.monthly_cash[0].net==Decimal('-20')
    assert r.ledger.monthly_cash[1].net==0
    b=r.batch_costs[0]
    assert b.batch_id=='batch-1' and b.harvest_event_declared is False
    assert b.variable_incurred==b.cash_paid_in_period==Decimal('20')
    assert b.fixed_incurred==b.remaining_payable_at_period_end==0
    assert r.ledger.closing_inventory=={} and r.ledger.closing_inventory_cost_by_batch=={}
    assert r.ledger.formula_version==FORMULA_VERSION and r.ledger.assessment_status=='hold'
    assert r.G0_G4=='not_assessed' and r.R2=='not_approved'


def test_later_same_period_harvest_preserves_every_legacy_quantity_and_cash():
    s=scenario(harvest=True);r=run(s)
    d=s.model_dump();d.pop('production_batches');d['schema_version']='3'
    old=EconomicScenario.model_validate(d);expected=EconomicLedger(TrustedTestRepository(old)).calculate(old)
    assert r.batch_costs[0].harvest_event_declared
    for name in expected.__dataclass_fields__:
        if name not in ('result_id','formula_version','scenario_sha256'):
            assert getattr(r.ledger,name)==getattr(expected,name),name
    assert r.ledger.result_id!=expected.result_id


def test_scheduled_payment_after_end_is_payable_and_does_not_create_current_cash():
    s=scenario();d=s.model_dump();d['period_end']=date(2026,10,31)
    c=d['variable_costs'][0];c['paid_at']=datetime(2026,11,2,tzinfo=timezone.utc)
    s=BatchEconomicScenario.model_validate(d);r=run(s)
    assert r.ledger.variable_cost==Decimal('20')
    assert r.ledger.operating_cash==r.ledger.operating_cash_bridge==0
    assert r.ledger.operating_payable_end==Decimal('20')
    assert r.ledger.future_cash_schedule[0].amount==Decimal('-20')
    assert r.batch_costs[0].cash_paid_in_period==0
    assert r.batch_costs[0].remaining_payable_at_period_end==Decimal('20')


def test_unknown_payment_and_missing_cost_group_remain_unknown_not_zero():
    d=scenario().model_dump();d['variable_costs'][0].update(paid_at=None,payment=None)
    r=run(BatchEconomicScenario.model_validate(d))
    assert r.ledger.operating_cash is None and 'OPERATING_PAYMENT_UNDECLARED' in r.ledger.hold_reasons
    assert r.batch_costs[0].cash_paid_in_period is None
    assert r.batch_costs[0].remaining_payable_at_period_end is None
    r=run(scenario(variable_costs=None))
    assert r.ledger.variable_cost is None and r.batch_costs[0].variable_incurred is None


@pytest.mark.parametrize('change', ['undeclared','duplicate','opening_overlap','cost_before_start','harvest_before_start'])
def test_batch_links_and_production_chronology_fail_closed(change):
    s=scenario(harvest=change=='harvest_before_start');repo=Repository(s)
    if change=='undeclared':
        d=s.model_dump();d['production_batches']=();s=BatchEconomicScenario.model_validate(d);repo=Repository(s)
    elif change=='duplicate':
        d=s.model_dump();d['production_batches']*=2
        with pytest.raises(ValueError):BatchEconomicScenario.model_validate(d)
        return
    elif change=='opening_overlap':
        d=s.model_dump();d['opening_inventory']=(opening_lot(),)
        d['zero_declarations']=tuple(z for z in d['zero_declarations'] if z['group']!='opening_inventory')
        s=BatchEconomicScenario.model_validate(d);repo=Repository(s)
    else:
        repo.batches[('batch-1','r1')]['production_start_at']=T(16)
    with pytest.raises(ValueError):run(s,repo)


@pytest.mark.parametrize('field,value', [
    ('tenant_id','foreign'),('revision','r2'),('batch_id','foreign'),('rights','none'),
    ('immutable',False),('origin','source'),('evidence_level','measured'),
    ('available_at',T(1)),('scope_start',date(2026,10,2)),('scope_end',date(2026,10,31)),
    ('production_start_at',T(1).replace(tzinfo=None)),('extra',True),
])
def test_owned_batch_records_are_revalidated_and_scoped(field,value):
    s=scenario();repo=Repository(s);repo.batches[('batch-1','r1')][field]=value
    with pytest.raises(ValueError):run(s,repo)


def test_missing_batch_authority_and_model_construct_bypass_are_rejected():
    s=scenario();repo=Repository(s);repo.batches.clear()
    with pytest.raises(ValueError):run(s,repo)
    repo=Repository(s);repo.get_production_batch=None
    with pytest.raises(ValueError):run(s,repo)
    with pytest.raises(ValueError):run(s.model_copy(update={'production_batches':({'batch_id':''},)}),Repository(s))


@pytest.mark.parametrize('what',['batch','input','scenario','authentication'])
def test_late_authority_changes_prevent_result_release(what):
    s=scenario();repo=Repository(s)
    class Changing(ProductionBatchLedger):
        def _calculate_verified(self,*args):
            value=super()._calculate_verified(*args)
            if what=='batch':repo.batches[('batch-1','r1')]['source_ref']='changed'
            elif what=='input':repo.records[next(iter(repo.records))]['value']='999'
            elif what=='scenario':repo.scenario_pin['payload_sha256']='0'*64
            else:repo.authenticated=False
            return value
    with pytest.raises(ValueError):Changing(repo).calculate(s)


def test_large_cost_is_exact_and_overflow_still_holds():
    d=scenario().model_dump();c=d['variable_costs'][0];c.update(paid_at=None,payment=None)
    c['quantity']=n('123456789012345678901234567890123456789','big-q','kWh_e')
    c['unit_cost']=n('987654321098765432109876543210987654321','big-p','KRW/kWh_e')
    r=run(BatchEconomicScenario.model_validate(d))
    expected=Decimal(str(int(c['quantity']['value'])*int(c['unit_cost']['value'])))
    assert r.ledger.variable_cost==r.batch_costs[0].variable_incurred==expected
    c['quantity']['value']=c['unit_cost']['value']='9'*64
    d['variable_costs']=(c,{**deepcopy(c),'id':'second',
        'quantity':n('9'*64,'second-q','kWh_e'),'unit_cost':n('9'*64,'second-p','KRW/kWh_e')})
    with pytest.raises(ValueError,match='128'):run(BatchEconomicScenario.model_validate(d))


def test_old_version_and_undeclared_zero_costs_do_not_silently_upgrade():
    with pytest.raises(ValueError):BatchEconomicScenario.model_validate(base())
    s=scenario(variable_costs=());d=s.model_dump()
    d['zero_declarations']=tuple(z for z in d['zero_declarations'] if z['group']!='variable_costs')
    r=run(BatchEconomicScenario.model_validate(d))
    assert r.ledger.variable_cost is None and r.batch_costs[0].variable_incurred is None


def test_mixed_batches_and_common_costs_are_not_redistributed_or_double_counted():
    d=scenario(harvest=True).model_dump()
    d['production_batches']+=({'batch_id':'growing','revision':'r1'},)
    d['variable_costs']+=({'id':'growing-cost','purpose':'production','batch_id':'growing','sale_id':None,
        'incurred_at':T(19),'quantity':n('0.3','growing-q','kWh_e'),
        'unit_cost':n('0.2','growing-price','KRW/kWh_e'),
        'paid_at':T(21),'payment':n('0.06','growing-payment','KRW')},
        {'id':'common','purpose':'period','batch_id':None,'sale_id':None,
        'incurred_at':T(19),'quantity':n('2','common-q','L'),'unit_cost':n('3','common-p','KRW/L'),
        'paid_at':T(22),'payment':n('6','common-payment','KRW')})
    r=run(BatchEconomicScenario.model_validate(d));b={b.batch_id:b for b in r.batch_costs}
    assert r.ledger.variable_cost==Decimal('31.06')
    assert b['batch-1'].variable_incurred==20 and b['growing'].variable_incurred==Decimal('0.06')
    assert r.ledger.closing_inventory_cost_by_batch=={'batch-1':Decimal('7.50')}
    assert 'growing' not in r.ledger.closing_inventory_cost_by_batch
    assert r.ledger.harvest_kg==10 and r.ledger.operating_cash==Decimal('468.94')


def test_fixed_production_cost_stays_fixed_and_partial_payment_keeps_payable():
    d=scenario().model_dump();c=deepcopy(d['variable_costs'][0]);c.update(id='fixed',
        quantity=n('3','fixed-q','month'),unit_cost=n('2','fixed-p','KRW/month'),
        payment=n('1','fixed-payment','KRW'))
    d['fixed_costs']=(c,);d['zero_declarations']=tuple(z for z in d['zero_declarations']if z['group']!='fixed_costs')
    r=run(BatchEconomicScenario.model_validate(d));b=r.batch_costs[0]
    assert (r.ledger.variable_cost,r.ledger.fixed_cost)==(20,6)
    assert b.variable_incurred==20 and b.fixed_incurred==6
    assert b.cash_paid_in_period==21 and b.remaining_payable_at_period_end==5
    assert r.ledger.operating_payable_end==5 and r.ledger.operating_cash==Decimal('-21')


def test_exact_kst_month_boundary_and_later_period_do_not_recharge_old_cost():
    d=scenario().model_dump();c=d['variable_costs'][0]
    c['paid_at']=datetime(2026,10,31,15,tzinfo=timezone.utc)
    r=run(BatchEconomicScenario.model_validate(d))
    assert [m.net for m in r.ledger.monthly_cash]==[0,Decimal('-20')]
    d['period_start']=date(2026,11,1)
    s=BatchEconomicScenario.model_validate(d);repo=Repository(s)
    with pytest.raises(ValueError,match='outside'):run(s,repo)
    c['incurred_at']=datetime(2026,10,31,15,tzinfo=timezone.utc)
    s=BatchEconomicScenario.model_validate(d);repo=Repository(s)
    repo.batches[('batch-1','r1')]['production_start_at']=T(1)
    assert run(s,repo).ledger.variable_cost==20


@pytest.mark.parametrize('bad',[1,'true'])
def test_immutable_flag_is_a_real_boolean(bad):
    s=scenario();repo=Repository(s);repo.batches[('batch-1','r1')]['immutable']=bad
    with pytest.raises(ValueError):run(s,repo)


def test_batch_record_version_participates_in_result_identity_and_output_copies():
    s=scenario();repo=Repository(s);first=run(s,repo);second=run(s,repo)
    assert first==second
    first.component_sha256.clear()
    assert run(s,repo)==second
    repo.batches[('batch-1','r1')]['source_ref']='different-owned-source'
    changed=run(s,repo)
    assert changed.ledger.scenario_sha256==second.ledger.scenario_sha256
    assert changed.ledger.result_id!=second.ledger.result_id
    assert changed.ledger.variable_cost==second.ledger.variable_cost


def test_source_change_at_release_and_independent_input_output_caps(monkeypatch,tmp_path):
    import app.economic_production_batches as mod
    from pathlib import Path
    original=Path(mod.__file__).read_bytes();local=tmp_path/'loaded.py';local.write_bytes(original)
    monkeypatch.setattr(mod,'__file__',str(local))
    class Changed(ProductionBatchLedger):
        def _calculate_verified(self,*args):
            r=super()._calculate_verified(*args);local.write_bytes(original+b'\n');return r
    s=scenario()
    with pytest.raises(ValueError,match='CODE_HOLD'):Changed(Repository(s)).calculate(s)
    local.write_bytes(original)
    monkeypatch.setattr(mod,'MAX_BYTES',1)
    with pytest.raises(ValueError,match='CAPACITY_HOLD'):run(s)
    monkeypatch.setattr(mod,'MAX_BYTES',2*1024**2)
    def huge(_):return b'x'*(2*1024**2+1)
    monkeypatch.setattr(mod,'result_bytes',huge)
    with pytest.raises(ValueError,match='CAPACITY_HOLD'):run(s)


def test_owned_record_and_512_batch_limits_are_independent_of_request_cap():
    s=scenario();repo=Repository(s)
    repo.batches[('batch-1','r1')]['source_ref']='x'*(2*1024**2)
    with pytest.raises(ValueError,match='bounded owned production records'):run(s,repo)
    d=s.model_dump();d['production_batches']+=tuple({'batch_id':f'other-{i}','revision':'r1'}for i in range(511))
    s=BatchEconomicScenario.model_validate(d)
    assert len(run(s).batch_costs)==512
    d['production_batches']+=({'batch_id':'overflow','revision':'r1'},)
    with pytest.raises(ValueError):BatchEconomicScenario.model_validate(d)


def test_same_batch_rejects_old_period_production_expense_without_inventing_harvest():
    d=scenario().model_dump();d['variable_costs'][0]['incurred_at']=datetime(2026,9,30,14,59,59,tzinfo=timezone.utc)
    s=BatchEconomicScenario.model_validate(d);repo=Repository(s)
    repo.batches[('batch-1','r1')]['production_start_at']=datetime(2026,9,1,tzinfo=timezone.utc)
    with pytest.raises(ValueError,match='outside'):run(s,repo)
