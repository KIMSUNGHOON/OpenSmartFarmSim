"""Durable source-bound material adoption and original-grid continuation."""
from copy import deepcopy
from fractions import Fraction
import json

import pytest

from app import crop_supply_material_owner as model
from app import crop_supply_material_point as point
from app import crop_supply_forcing_owner as forcing
from app import crop_supply_season as base
from app.crop_morphology_artifact_io import MorphologyBlobStore
from test_crop_supply_season import source,q,x,canonical
from test_crop_supply_forcing_owner import origin,setup_owner
from test_crop_supply_forcing_threshold import pending,TOLERANCE
from test_crop_supply_forcing_threshold_state import calculated
from test_crop_supply_material_point import point_case


@pytest.fixture(scope='module')
def adopted(pending,point_case,tmp_path_factory):
    inputs,proposal=point_case
    ws=model.Workspace(pending['workspace'],tmp_path_factory.mktemp('material-owner')/'cas',pending['workspace'].access)
    result=model.adopt_material(pending['result'].handle,pending['result'].pending['page_sha256'],TOLERANCE,
        inputs=inputs,expected_point_sha256=proposal['calculation_sha256'],workspace=ws)
    assert result.status=='adopted',result.hold
    return {'workspace':ws,'result':result,'inputs':inputs,'proposal':proposal}


def test_adoption_consumes_exact_source_event_once_and_keeps_all_origins(adopted,pending):
    h=adopted['result'].handle;c=h.current;b=h.basis['numeric_basis'];p=adopted['proposal'];n=c['numeric']
    assert c['phase']=='material_after'and c['at']==p['at']
    assert n['last_confirmed']=={'at':p['at'],'state':p['after_state'],'derived':p['after_derived']}
    assert n['schedule']['consumed_event_id']==p['source_event']['source_event_id']
    assert n['schedule']['consumed_sequence']==p['source_event']['sequence']
    assert n['schedule']['next_sequence']==p['source_event']['sequence']+1
    assert n['schedule']['age_exact']==p['before_dense']['shoot_age_exact']
    assert n['event_sequence']==pending['result'].handle.current['numeric']['event_sequence']+1
    assert b['seed']['birth_bases']==p['after_birth_baselines']
    assert b['seed']['geometry_baselines']==p['after_geometry_baselines']
    assert n['lifetime_transfers_exact']==p['post_point_lifetime_transfers_exact_preview']
    assert n['point_totals_exact']==p['post_point_point_totals_exact_preview']
    assert n['global_ledgers']==p['post_point_global_ledgers_preview']
    assert all(v['value']==0. for v in n['branch_integrated_transfers'].values())
    assert all(x(v['budget_exact'])==x(v['residual_exact'])==0 for v in n['branch_ledgers'].values())
    assert c['effective_rights']['redistribute']is False
    assert n['next_grid_endpoint_exact']==q(528)
    assert x(n['grid_remainder_exact'])+528-x(c['at']['elapsed_seconds_exact'])==8
    assert adopted['result'].progress['proposal_RHS_evaluations']==36


def test_cold_open_does_not_recompute_point_or_past_RHS(adopted,monkeypatch):
    h=adopted['result'].handle
    monkeypatch.setattr(base.stage,'evaluate',lambda *a,**k:pytest.fail('cold RHS'))
    monkeypatch.setattr(point,'apply_material_point',lambda *a,**k:pytest.fail('cold point recomputation'))
    restored=model.open_material(model.CursorRef(h.cursor_sha256),h._definition,adopted['workspace'])
    assert restored.current==h.current and restored.basis==h.basis
    assert restored.cursor_sha256==h.cursor_sha256


def test_remainder_uses_original_grid_and_split_cold_matches(adopted,monkeypatch):
    h=adopted['result'].handle
    full=model.advance(h,base.AdvanceRequest(q(536),step_budget=10))
    assert full.status=='completed',full.hold
    first=model.advance(h,base.AdvanceRequest(q(536),step_budget=1))
    assert first.status=='yielded',first.hold
    assert first.emitted[0]['at']['elapsed_seconds_exact']==q(528)
    with monkeypatch.context()as m:
        m.setattr(base.stage,'evaluate',lambda *a,**k:pytest.fail('cold past RHS'))
        cold=model.open_material(model.CursorRef(first.handle.cursor_sha256),h._definition,adopted['workspace'])
    last=model.advance(cold,base.AdvanceRequest(q(536),step_budget=10))
    assert last.status=='completed',last.hold
    assert last.handle.cursor_sha256==full.handle.cursor_sha256
    assert last.handle.current==full.handle.current
    assert x(full.handle.current['at']['elapsed_seconds_exact'])==536
    assert full.handle.current['numeric']['event_sequence']==h.current['numeric']['event_sequence']


def forged_current(adopted,change):
    h=adopted['result'].handle;current=deepcopy(h.current);change(current)
    cursor=json.loads(h._cursor);page=json.loads((adopted['workspace'].archive_directory/cursor['history_page_sha256']).read_bytes())
    with MorphologyBlobStore(adopted['workspace'].archive_directory,adopted['workspace'].access,write=True)as store:
        cursor['current_sha256']=store.put(canonical(current),maximum=base.PAGE_MAX)
        page['after_current_sha256']=cursor['current_sha256'];cursor['history_page_sha256']=store.put(canonical(page),maximum=base.PAGE_MAX)
        return store.put(canonical(cursor),maximum=base.PAGE_MAX)


@pytest.mark.parametrize('change',['boolean_steps','integer_accumulator','integer_state','integer_derived'])
def test_rehashed_numeric_type_changes_are_not_equal_source_values(adopted,change):
    def alter(c):
        n=c['numeric']
        if change=='boolean_steps':n['branch_steps']=False
        elif change=='integer_accumulator':n['branch_integrated_transfers'][next(iter(n['branch_integrated_transfers']))]['value']=0
        elif change=='integer_derived':
            d=n['last_confirmed']['derived'];name=next(k for k,v in d.items()if v['value']==int(v['value']))
            d[name]['value']=int(d[name]['value'])
        else:
            i=next(i for i,v in enumerate(n['last_confirmed']['state'])if v==int(v))
            n['last_confirmed']['state'][i]=int(n['last_confirmed']['state'][i])
    reference=forged_current(adopted,alter)
    with pytest.raises(ValueError):model.open_material(model.CursorRef(reference),adopted['result'].handle._definition,adopted['workspace'])


def test_remainder_all_states_integrals_and_clock_have_independent_rounding(adopted,monkeypatch):
    from decimal import Decimal,localcontext
    h=adopted['result'].handle;evaluate=base.stage.evaluate;calls=[]
    def count(*a,**k):calls.append(1);return evaluate(*a,**k)
    monkeypatch.setattr(base.stage,'evaluate',count)
    result=model.advance(h,base.AdvanceRequest(q(528)))
    assert result.status=='yielded',result.hold
    assert len(calls)==5 and result.progress['past_intervals_reintegrated']==0
    cursor=json.loads(result.handle._cursor)
    page=json.loads((adopted['workspace'].archive_directory/cursor['history_page_sha256']).read_bytes());trace=page['evidence']
    before=h.current['numeric'];after=result.handle.current['numeric'];duration=Fraction(528)-x(h.current['at']['elapsed_seconds_exact'])
    assert x(trace['step_seconds_exact'])==duration and 0<duration<8
    with localcontext()as ctx:
        ctx.prec=2200;D=Decimal.from_float;dt=Decimal(duration.numerator)/Decimal(duration.denominator)
        for i,value in enumerate(after['last_confirmed']['state']):
            rates=[D(row['rates'][i])for row in trace['stages']]
            expected=float(D(before['last_confirmed']['state'][i])+dt*(rates[0]/6+rates[1]/3+rates[2]/3+rates[3]/6))
            assert value==expected,i
        for name,value in after['branch_integrated_transfers'].items():
            i=next(i for i,row in enumerate(trace['flux_order'])if row['name']==name)
            rates=[D(row['flux'][i])for row in trace['stages']]
            expected=float(dt*(rates[0]/6+rates[1]/3+rates[2]/3+rates[3]/6))
            assert value['value']==expected,name
    for name,row in after['global_ledgers'].items():
        prior=before['global_ledgers'][name];local=after['branch_ledgers'][name]
        assert x(row['residual_exact'])==x(prior['residual_exact'])+x(local['residual_exact']),name
        assert x(row['budget_exact'])==x(prior['budget_exact'])+x(local['budget_exact']),name
        assert abs(x(row['residual_exact']))<=x(row['budget_exact']),name
    air=Fraction(after['branch_integrated_transfers']['indoor_air_temperature_time']['value'])
    age=x(before['schedule']['age_exact'])+(air-Fraction(h.basis['numeric_basis']['shoot_base_temperature'])*duration)/86400
    assert x(after['schedule']['age_exact'])==age
    assert after['schedule']['next_sequence']==before['schedule']['next_sequence']
    assert after['point_totals_exact']==before['point_totals_exact']
    assert after['transfer_origins']==before['transfer_origins']


def test_retry_is_same_cursor_and_does_not_consume_source_again(adopted,pending):
    h=adopted['result'].handle;directory=adopted['workspace'].archive_directory
    old={p.name:p.read_bytes()for p in directory.iterdir()if p.is_file()}
    result=model.adopt_material(pending['result'].handle,pending['result'].pending['page_sha256'],TOLERANCE,
        inputs=adopted['inputs'],expected_point_sha256=adopted['proposal']['calculation_sha256'],workspace=adopted['workspace'])
    assert result.status=='adopted',result.hold
    assert result.handle.cursor_sha256==h.cursor_sha256 and result.handle.current==h.current
    assert {p.name:p.read_bytes()for p in directory.iterdir()if p.is_file()}==old


@pytest.mark.parametrize('invalid_request',[base.AdvanceRequest(q(527)),base.AdvanceRequest(q(536),step_budget=True),base.AdvanceRequest(q(536),wall_seconds=0)])
def test_invalid_boundaries_or_controls_do_not_evaluate_RHS(adopted,monkeypatch,invalid_request):
    monkeypatch.setattr(base.stage,'evaluate',lambda *a,**k:pytest.fail('invalid request RHS'))
    result=model.advance(adopted['result'].handle,invalid_request)
    assert result.status=='hold'and result.handle.cursor_sha256==adopted['result'].handle.cursor_sha256
    assert result.emitted==[]


def test_rhs_and_byte_yields_keep_the_last_confirmed_state(adopted,monkeypatch):
    h=adopted['result'].handle
    with monkeypatch.context()as m:
        m.setattr(base.stage,'evaluate',lambda *a,**k:pytest.fail('insufficient quota evaluated RHS'))
        result=model.advance(h,base.AdvanceRequest(q(536),rhs_budget=4))
    assert result.status=='yielded'and result.handle.cursor_sha256==h.cursor_sha256
    result=model.advance(h,base.AdvanceRequest(q(536),byte_budget=1))
    assert result.status=='yielded'and result.handle.cursor_sha256==h.cursor_sha256
    assert result.progress['records_emitted']==0 and result.emitted==[]


def test_duplicate_material_and_early_cancel_never_advance(adopted,monkeypatch):
    h=adopted['result'].handle
    monkeypatch.setattr(base.stage,'evaluate',lambda *a,**k:pytest.fail('duplicate or cancelled RHS'))
    a=model.advance(h,base.AdvanceRequest(q(536)),material=adopted['proposal'])
    b=model.advance(h,base.AdvanceRequest(q(536),cancelled=lambda:True))
    assert a.status==b.status=='hold'and a.hold.startswith('MATERIAL_HOLD:')and b.hold.startswith('CANCELLED_HOLD:')
    assert a.handle.cursor_sha256==b.handle.cursor_sha256==h.cursor_sha256


def test_cancel_after_publication_keeps_a_real_cold_recoverable_prefix(adopted,monkeypatch):
    h=adopted['result'].handle;publish=model._publish;cancel={'now':False}
    def stop_after(*a,**k):
        result=publish(*a,**k)
        if result is not None:cancel['now']=True
        return result
    monkeypatch.setattr(model,'_publish',stop_after)
    result=model.advance(h,base.AdvanceRequest(q(536),step_budget=10,cancelled=lambda:cancel['now']))
    assert result.status=='hold'and result.hold.startswith('CANCELLED_HOLD:')
    assert len(result.emitted)==1 and result.handle.cursor_sha256!=h.cursor_sha256
    monkeypatch.setattr(base.stage,'evaluate',lambda *a,**k:pytest.fail('cancel prefix cold RHS'))
    cold=model.open_material(model.CursorRef(result.handle.cursor_sha256),h._definition,adopted['workspace'])
    assert cold.current==result.handle.current


def test_history_write_failure_never_returns_an_unpublished_cursor(adopted,monkeypatch):
    h=adopted['result'].handle;put=MorphologyBlobStore.put
    def fail(self,data,**kwargs):
        v=json.loads(data)
        if v.get('schema_version')=='supply-material-history-page-v1'and v.get('kind')=='interval':raise OSError('own publication fault')
        return put(self,data,**kwargs)
    with monkeypatch.context()as m:
        m.setattr(MorphologyBlobStore,'put',fail)
        held=model.advance(h,base.AdvanceRequest(q(536),step_budget=10))
    assert held.status=='hold'and held.handle.cursor_sha256==h.cursor_sha256 and held.emitted==[]
    retry=model.advance(h,base.AdvanceRequest(q(536),step_budget=10))
    assert retry.status=='completed',retry.hold


def test_mutated_numeric_basis_during_stage_clears_authority(adopted,monkeypatch):
    h=adopted['result'].handle;evaluate=base.stage.evaluate;changed={'now':False}
    def mutate(program,state,organs,costs,profiles):
        result=evaluate(program,state,organs,costs,profiles)
        if not changed['now']:costs['internodes'][0]+=1.;changed['now']=True
        return result
    monkeypatch.setattr(base.stage,'evaluate',mutate)
    result=model.advance(h,base.AdvanceRequest(q(536)))
    assert result.status=='hold'and result.handle is None and result.authority_hold is not None and result.emitted==[]


@pytest.mark.parametrize('change',['alias','fake_source','expected_hash','bad_input'])
def test_adoption_refuses_invalid_source_or_expected_point(adopted,pending,tmp_path,change):
    h=pending['result'].handle;ws=model.Workspace(pending['workspace'],tmp_path/'new-cas',pending['workspace'].access)
    inputs=deepcopy(adopted['inputs']);expected=adopted['proposal']['calculation_sha256']
    if change=='alias':ws=model.Workspace(pending['workspace'],pending['workspace'].archive_directory,ws.access)
    elif change=='fake_source':h={'cursor_sha256':h.cursor_sha256}
    elif change=='expected_hash':expected='0'*64
    else:inputs['rights']['use']=False
    result=model.adopt_material(h,pending['result'].pending['page_sha256'],TOLERANCE,inputs=inputs,expected_point_sha256=expected,workspace=ws)
    assert result.status=='hold'and result.handle is None and result.emitted==[]
    if change!='alias':assert not ws.archive_directory.exists()or not any(p.name for p in ws.archive_directory.iterdir()if len(p.name)==64)


def test_adoption_cancel_before_computation_writes_nothing(adopted,pending,tmp_path,monkeypatch):
    ws=model.Workspace(pending['workspace'],tmp_path/'cancelled-cas',pending['workspace'].access)
    monkeypatch.setattr(point,'apply_material_point',lambda *a,**k:pytest.fail('cancelled adoption recalculated point'))
    result=model.adopt_material(pending['result'].handle,pending['result'].pending['page_sha256'],TOLERANCE,
        inputs=adopted['inputs'],expected_point_sha256=adopted['proposal']['calculation_sha256'],workspace=ws,cancelled=lambda:True)
    assert result.status=='hold'and result.hold.startswith('CANCELLED_HOLD:')and not ws.archive_directory.exists()


def test_forcing_edge_after_material_keeps_new_stocks_and_same_grid(origin,tmp_path):
    from test_crop_supply_material_point import make_inputs
    from app import crop_supply_forcing_threshold_state as candidate
    (tmp_path/'forcing').mkdir()
    ws,definition,d=setup_owner(origin,tmp_path/'forcing',edge=528,end=536)
    first=forcing.open_season(origin['source_ref'],definition,ws)
    held=forcing.advance(first,base.AdvanceRequest(q(536),step_budget=10))
    state=candidate.calculate_threshold_state(held.handle,held.pending['page_sha256'],TOLERANCE)
    data={'workspace':ws,'definition':definition,'document':d,'result':held}
    inputs=make_inputs(data,state)
    proposal=point.apply_material_point(held.handle,held.pending['page_sha256'],TOLERANCE,inputs=inputs)
    new_ws=model.Workspace(ws,tmp_path/'material-cas',ws.access)
    adopted=model.adopt_material(held.handle,held.pending['page_sha256'],TOLERANCE,inputs=inputs,
        expected_point_sha256=proposal['calculation_sha256'],workspace=new_ws)
    assert adopted.status=='adopted',adopted.hold
    step=model.advance(adopted.handle,base.AdvanceRequest(q(536),step_budget=1))
    assert [r['phase']for r in step.emitted]==['forcing_before','forcing_after']
    assert all(r['at']['elapsed_seconds_exact']==q(528)for r in step.emitted)
    cursors=[json.loads((new_ws.archive_directory/r['cursor_sha256']).read_bytes())for r in step.emitted]
    states=[json.loads((new_ws.archive_directory/c['current_sha256']).read_bytes())for c in cursors]
    a,b=[v['numeric']for v in states]
    assert a['last_confirmed']['state']==b['last_confirmed']['state']and a['global_ledgers']==b['global_ledgers']
    assert a['point_totals_exact']==b['point_totals_exact']==adopted.handle.current['numeric']['point_totals_exact']
    last=model.advance(step.handle,base.AdvanceRequest(q(536),step_budget=10))
    full=model.advance(adopted.handle,base.AdvanceRequest(q(536),step_budget=10))
    assert last.status==full.status=='completed'and last.handle.cursor_sha256==full.handle.cursor_sha256


def test_rehashed_global_budget_cannot_replace_the_accepted_point_budget(adopted):
    def change(c):
        row=c['numeric']['global_ledgers']['carbohydrate']
        row['budget_exact']=q(x(row['budget_exact'])+1,row['budget_exact']['unit'])
    reference=forged_current(adopted,change)
    with pytest.raises(ValueError):model.open_material(model.CursorRef(reference),adopted['result'].handle._definition,adopted['workspace'])


def test_rehashed_interval_stage_is_checked_without_past_RHS(adopted,monkeypatch):
    h=adopted['result'].handle;first=model.advance(h,base.AdvanceRequest(q(528)))
    cursor=json.loads(first.handle._cursor);directory=adopted['workspace'].archive_directory
    page=json.loads((directory/cursor['history_page_sha256']).read_bytes())
    page['evidence']['stages'][1]['state'][104]+=1.
    with MorphologyBlobStore(directory,adopted['workspace'].access,write=True)as store:
        cursor['history_page_sha256']=store.put(canonical(page),maximum=base.PAGE_MAX)
        sha=store.put(canonical(cursor),maximum=base.PAGE_MAX)
    monkeypatch.setattr(base.stage,'evaluate',lambda *a,**k:pytest.fail('forged history ran past RHS'))
    with pytest.raises(ValueError):model.open_material(model.CursorRef(sha),h._definition,adopted['workspace'])


def test_late_caller_input_change_before_adoption_writes_nothing(adopted,pending,tmp_path,monkeypatch):
    inputs=deepcopy(adopted['inputs']);apply=point.apply_material_point
    def mutate(*a,**k):
        out=apply(*a,**k);inputs['reviewer']='changed-after-calculation';return out
    monkeypatch.setattr(point,'apply_material_point',mutate)
    ws=model.Workspace(pending['workspace'],tmp_path/'late-input-cas',pending['workspace'].access)
    result=model.adopt_material(pending['result'].handle,pending['result'].pending['page_sha256'],TOLERANCE,
        inputs=inputs,expected_point_sha256=adopted['proposal']['calculation_sha256'],workspace=ws)
    assert result.status=='hold'and result.handle is None and result.hold.startswith('SOURCE_HOLD:')
    assert not ws.archive_directory.exists()


def test_late_copied_original_profile_change_clears_confirmed_authority(adopted,tmp_path,monkeypatch):
    from shutil import copytree
    original=adopted['workspace'];f=original.forcing_workspace;b=f.source_workspace
    new_base=base.Workspace(copytree(b.source_directory,tmp_path/'source'),copytree(b.archive_directory,tmp_path/'base-cas'),b.access)
    new_forcing=forcing.Workspace(new_base,copytree(f.archive_directory,tmp_path/'forcing-cas'),f.access)
    ws=model.Workspace(new_forcing,copytree(original.archive_directory,tmp_path/'material-cas'),original.access)
    h=model.open_material(model.CursorRef(adopted['result'].handle.cursor_sha256),adopted['result'].handle._definition,ws)
    name=h.basis['numeric_basis']['profile_sha256']['growth_profile'];path=new_base.source_directory/name;before=(b.source_directory/name).read_bytes()
    evaluate=base.stage.evaluate;changed={'now':False}
    def mutate(*a,**k):
        out=evaluate(*a,**k)
        if not changed['now']:
            v=json.loads(path.read_bytes());v['parameters']['cStemG']['value']+=1.;path.chmod(0o600);path.write_bytes(canonical(v));changed['now']=True
        return out
    monkeypatch.setattr(base.stage,'evaluate',mutate)
    result=model.advance(h,base.AdvanceRequest(q(536)))
    assert result.status=='hold'and result.handle is None and result.authority_hold is not None and result.emitted==[]
    assert(b.source_directory/name).read_bytes()==before


def test_completed_request_is_idempotent_without_RHS_or_new_writes(adopted,monkeypatch):
    h=adopted['result'].handle;last=model.advance(h,base.AdvanceRequest(q(536),step_budget=10))
    assert last.status=='completed',last.hold
    monkeypatch.setattr(base.stage,'evaluate',lambda *a,**k:pytest.fail('completed request RHS'))
    monkeypatch.setattr(MorphologyBlobStore,'put',lambda *a,**k:pytest.fail('completed request wrote CAS'))
    result=model.advance(last.handle,base.AdvanceRequest(q(536),step_budget=10))
    assert result.status=='completed'and result.handle.cursor_sha256==last.handle.cursor_sha256 and result.emitted==[]


@pytest.mark.parametrize('change',['root_claim','derived_unit','progress_count'])
def test_saved_point_metadata_cannot_promote_scope_or_change_units(adopted,monkeypatch,change):
    h=adopted['result'].handle
    monkeypatch.setattr(base.stage,'evaluate',lambda *a,**k:pytest.fail('saved proof evaluated past RHS'))
    with model._session(h._definition,adopted['workspace'])as s:
        value=deepcopy(s.point);definition=deepcopy(s.definition)
        if change=='root_claim':value['root_certificate']['claim_scope']='validated_physical_emergence'
        elif change=='derived_unit':
            value['after_derived']['air_capacity']['unit']='wrong-unit'
            value['after_stage']['derived']['air_capacity']['unit']='wrong-unit'
        else:value['progress']['candidate_RHS_evaluations']=0
        value['calculation_sha256']=base._hash({k:v for k,v in value.items()if k!='calculation_sha256'})
        definition['expected_point_sha256']=value['calculation_sha256'];definition['point_sha256']=base._hash(value)
        with pytest.raises(ValueError):model.proof.verify(s.parent,s.source_current,point._source(s.parent,s.source_current),definition,value)
