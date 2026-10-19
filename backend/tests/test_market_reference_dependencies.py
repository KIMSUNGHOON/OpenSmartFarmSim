"""Actual registration lifetime and supported default dependency guards."""
import importlib

import pytest

from test_farm_registration_read_scope import (registration,authoring,profiles,
    login_database,original_login_scope,login_scope,query_cleanup,pytestmark)


@pytest.fixture
def loaded(registration):
    farms,args,principal=registration
    with farms.registration_read_scope(*args):
        expected=farms.read_registration(*args)
        witness=farms._registration_read.get()
        yield farms.replay.candidates,witness,principal,expected


def test_default_guard_preserves_actual_full_current_reads_and_closes(loaded):
    owner,witness,_,_=loaded
    model=importlib.import_module('app.market_reference_dependencies')
    with model.scope(owner,witness) as guard:
        assert guard is not None
        guard.check()
        assert owner.verify_current_reads(witness.args[0],tuple(witness.lookups)) is None
        guard.check()
    assert not guard.active and guard.state is guard.binding is guard.token is None
    with pytest.raises(ValueError):guard.check()
    assert model._active.get() is None


def test_close_releases_owner_without_poisoning_registration(loaded):
    from app import market_reference_dependencies as model
    owner,witness,_,_=loaded
    with model.scope(owner,witness) as guard:assert guard is not None
    assert guard.owner is guard.witness is None
    assert not witness.failed
    with model.scope(owner,witness) as second:assert second is not None


@pytest.mark.parametrize('change',['instance_method','validator_plugin','metadata_callback'])
def test_initial_unsupported_profiles_use_actual_original_verifier(loaded,monkeypatch,change):
    from app import market_reference_dependencies as model
    from app.economic_contracts import OwnedEconomicRecord
    from pydantic import AfterValidator
    owner,witness,_,_=loaded;source=owner._source._source;calls=[]
    with monkeypatch.context() as patch:
        if change=='instance_method':
            original=source.get_economic_input
            def wrapper(*args):calls.append(1);return original(*args)
            patch.setattr(source,'get_economic_input',wrapper)
        elif change=='validator_plugin':
            original=OwnedEconomicRecord.__pydantic_validator__
            class Plugin:
                def validate_json(self,*args,**kwargs):calls.append(1);return original.validate_json(*args,**kwargs)
            patch.setattr(OwnedEconomicRecord,'__pydantic_validator__',Plugin())
        else:
            field=OwnedEconomicRecord.model_fields['value']
            patch.setattr(field,'metadata',[*field.metadata,AfterValidator(lambda value:value)])
        with model.scope(owner,witness) as guard:
            assert guard is None
            assert owner.verify_current_reads(witness.args[0],tuple(witness.lookups)) is None
        if change!='metadata_callback':assert calls
    assert model._active.get() is None and not witness.failed


@pytest.mark.parametrize('change',['instance_method','kind_registry','policy','validator','serializer',
    'core_schema','model_config','metadata','decimal','function_code','function_defaults','alias','package_version','guard_code','codec_alias','copy_dispatch'])
def test_late_dependency_changes_poison_current_registration(loaded,monkeypatch,change):
    from app import market_reference_dependencies as model
    from app import market_source_store as source_module,jobs
    from app.economic_contracts import OwnedEconomicRecord,EconomicScenario
    from decimal import localcontext
    from pydantic import AfterValidator
    owner,witness,_,_=loaded;source=owner._source._source;retained=[]
    with pytest.raises(ValueError):
        with model.scope(owner,witness) as guard:
            assert guard is not None;retained.append(guard)
            with monkeypatch.context() as patch,localcontext() as ctx:
                if change=='instance_method':patch.setattr(source,'get_economic_input',lambda *_:None)
                elif change=='kind_registry':patch.setitem(source_module._KINDS,'economic_input',(EconomicScenario,'scenario_id','scenario_revision'))
                elif change=='policy':patch.setattr(source_module,'VERSION','changed')
                elif change=='validator':patch.setattr(OwnedEconomicRecord,'__pydantic_validator__',object())
                elif change=='serializer':patch.setattr(OwnedEconomicRecord,'__pydantic_serializer__',object())
                elif change=='core_schema':patch.setitem(OwnedEconomicRecord.__pydantic_core_schema__,'unsupported_state',True)
                elif change=='model_config':patch.setitem(OwnedEconomicRecord.model_config,'frozen',False)
                elif change=='metadata':
                    field=OwnedEconomicRecord.model_fields['value']
                    patch.setattr(field,'metadata',[*field.metadata,AfterValidator(lambda v:v)])
                elif change=='decimal':ctx.prec+=1
                elif change=='function_code':
                    def replacement(_):return None
                    patch.setattr(jobs._validate_input_fields,'__code__',replacement.__code__)
                elif change=='function_defaults':patch.setattr(model.market_candidate_store._parse,'__defaults__',(16383,))
                elif change=='alias':patch.setattr(source_module,'canonical_input_bytes',lambda _:b'{}')
                elif change=='package_version':patch.setattr(model.pydantic,'__version__','changed')
                elif change=='codec_alias':
                    original=model.json.encoder._make_iterencode
                    def codec(*args,**kwargs):return original(*args,**kwargs)
                    patch.setattr(model.json.encoder,'_make_iterencode',codec)
                elif change=='copy_dispatch':
                    original=model.copy._deepcopy_dispatch[str]
                    def copying(value,memo):return original(value,memo)
                    patch.setitem(model.copy._deepcopy_dispatch,str,copying)
                else:patch.setattr(model,'CODE_SHA256','0'*64)
                with pytest.raises(ValueError):guard.check()
            guard.check()
    assert witness.failed and retained and not retained[0].active
    assert model._active.get() is None


@pytest.mark.parametrize('change',['nested','copied','thread','task','copied_close','early_close','exception'])
def test_execution_lifetime_cannot_escape_or_reenter(loaded,change):
    from app import market_reference_dependencies as model
    from contextvars import copy_context
    from concurrent.futures import ThreadPoolExecutor
    import asyncio
    owner,witness,_,_=loaded;retained=[]
    with pytest.raises((ValueError,RuntimeError)):
        with model.scope(owner,witness) as guard:
            assert guard is not None;retained.append(guard)
            if change=='exception':raise RuntimeError('owned interruption')
            if change=='early_close':guard.close();return
            with pytest.raises(ValueError):
                if change=='nested':
                    with model.scope(owner,witness):pass
                elif change=='copied':copy_context().run(guard.check)
                elif change=='copied_close':copy_context().run(guard.close)
                elif change=='task':
                    async def copied():guard.check()
                    asyncio.run(copied())
                else:
                    context=copy_context()
                    with ThreadPoolExecutor(max_workers=1) as pool:pool.submit(context.run,guard.check).result(timeout=10)
            guard.check()
    assert retained and not retained[0].active and model._active.get() is None


def test_wrong_registration_owner_is_rejected(loaded):
    from app import market_reference_dependencies as model
    owner,witness,_,_=loaded
    with pytest.raises(ValueError):
        with model.scope(object(),witness):pass
    assert model._active.get() is None


def test_guard_does_not_replace_current_role_audit(loaded,login_scope):
    from app import market_reference_dependencies as model
    from psycopg import sql
    owner,witness,_,_=loaded;base,policy,_=login_scope
    with pytest.raises(ValueError):
        with model.scope(owner,witness) as guard:
            assert guard is not None
            with base.connect() as conn:
                conn.execute(sql.SQL('GRANT UPDATE ON {} TO {}').format(sql.Identifier(policy.schema,'market_source_records'),sql.Identifier(policy.roles['authority'])))
            guard.check()
            owner.verify_current_reads(witness.args[0],tuple(witness.lookups))


def test_HTTP_principal_provider_expiry_remains_current(registration,monkeypatch):
    from app import market_reference_dependencies as model,http_identity as identity
    from datetime import datetime,timedelta,timezone
    farms,args,principal=registration;owner=farms.replay.candidates
    clock=[datetime(2026,10,1,tzinfo=timezone.utc)]
    grant=identity.BearerGrant('a'*64,args[0],frozenset(principal['scopes']),clock[0],clock[0]+timedelta(seconds=1))
    registry=identity.BearerRegistry((grant,),clock=lambda:clock[0])
    token=identity._PRINCIPAL.set(identity._RequestIdentity(grant,registry))
    try:
        with monkeypatch.context() as patch:
            patch.setattr(farms.replay.jobs,'principal_provider',identity.current_principal)
            for instance in (owner,owner._source,owner._source._source,owner._source._holds,owner._source._holds._context_store):
                patch.setattr(instance,'_principal_provider',identity.current_principal)
            with farms.registration_read_scope(*args):
                farms.read_registration(*args);witness=farms._registration_read.get()
                with pytest.raises((ValueError,PermissionError)):
                    with model.scope(owner,witness) as guard:
                        assert guard is not None
                        clock[0]+=timedelta(seconds=2)
                        guard.check()
                assert witness.failed
    finally:identity._PRINCIPAL.reset(token)


def test_current_dependency_checks_do_not_query_DB(loaded,monkeypatch):
    from app import market_reference_dependencies as model
    import psycopg
    owner,witness,_,_=loaded
    def forbidden(*_a,**_kw):pytest.fail('pure dependency guard queried DB')
    with monkeypatch.context() as patch:
        patch.setattr(psycopg.Connection,'execute',forbidden)
        with model.scope(owner,witness) as guard:
            assert guard is not None
            guard.check()


def test_unsupported_startup_state_retains_original_path(loaded,monkeypatch):
    from app import market_reference_dependencies as model
    owner,witness,_,_=loaded
    with monkeypatch.context() as patch:
        patch.setattr(model,'_BOOTSTRAP',None)
        with model.scope(owner,witness) as guard:
            assert guard is None
            assert owner.verify_current_reads(witness.args[0],tuple(witness.lookups)) is None
    assert not witness.failed


@pytest.mark.parametrize('package',['pydantic','pydantic_core'])
def test_installed_versions_must_match_repository_lock(login_scope,monkeypatch,package):
    from app import market_reference_dependencies as model
    selected=getattr(model,package)
    with monkeypatch.context() as patch:
        patch.setattr(selected,'__version__','unlocked-version')
        with pytest.raises(ValueError):model._snapshot()


def test_cancellation_poisons_current_registration_and_clears_context(loaded):
    from app import market_reference_dependencies as model
    import asyncio
    owner,witness,_,_=loaded
    with pytest.raises(asyncio.CancelledError):
        with model.scope(owner,witness) as guard:
            assert guard is not None
            raise asyncio.CancelledError()
    assert witness.failed and not guard.active and guard.owner is guard.witness is None
    assert model._active.get() is None


def test_dependency_guard_and_raw_receipts_compose_around_original_trace(registration,login_scope,monkeypatch):
    from app import market_reference_dependencies as model,market_reference_bundle as bundles,market_reference_receipts as receipts
    from test_market_reference_receipt_equivalence import proof
    from psycopg import sql
    import json,os
    from pathlib import Path
    farms,args,_=registration;owner=farms.replay.candidates;base,policy,_=login_scope
    original=bundles._verify_trace;selected=[None];runs=[]
    def instrumented(store,tenant,slot,trace):
        if selected[0] is None:return original(store,tenant,slot,trace)
        plan=selected[0];bundle=bundles._Bundle(store,tenant,slot,store._reference_reader(tenant));bundle.token=slot.set(bundle)
        try:
            def consume(_reader):
                guard=model._active.get();assert guard is not None
                guard.check();original(store,tenant,slot,trace);guard.check();runs.append(len(trace))
            return receipts.verify_receipts(store,tenant,plan['source_keys'],plan['candidate_keys'],plan['pin_keys'],consume)
        finally:bundle.close()
    monkeypatch.setattr(bundles,'_verify_trace',instrumented)
    with farms.registration_read_scope(*args):
        expected=farms.read_registration(*args);witness=farms._registration_read.get();trace=tuple(witness.lookups)
        with base.connect() as conn:
            pins={key for key in dict.fromkeys(a for n,a,_ in trace if n in proof.SCENARIOS) if conn.execute(sql.SQL('SELECT 1 FROM {} WHERE tenant_id=%s AND scenario_id=%s AND revision=%s').format(sql.Identifier(policy.schema,'market_candidate_pins')),(args[0],*key)).fetchone()}
            candidates={key for key in dict.fromkeys(a for n,a,_ in trace if n=='get_economic_input') if conn.execute(sql.SQL('SELECT 1 FROM {} WHERE tenant_id=%s AND input_id=%s AND revision=%s').format(sql.Identifier(policy.schema,'market_candidate_inputs')),(args[0],*key)).fetchone()}
        selected[0]=proof.trace_plan(trace,candidates,pins);assert selected[0] is not None
        with model.scope(owner,witness) as guard:
            assert guard is not None
            assert farms.read_registration(*args)==expected
            assert farms.read_registration(*args)==expected
    assert runs==[len(trace),len(trace)] and model._active.get() is None
    root=os.environ.get('OSSF_SHARED_MARKET_EVIDENCE')
    if root:
        result={'full_trace_repetitions':len(runs),'logical_reads_per_trace':len(trace),
            'source_keys':len(selected[0]['source_keys']),'candidate_keys':len(selected[0]['candidate_keys']),
            'pin_keys':len(selected[0]['pin_keys']),'all_original_getters_executed':True,
            'raw_receipts_and_guard_accepted':True,'registration_values_preserved':True,'models':len(model._models())}
        with (Path(root)/'reference-dependency-composition.json').open('x') as f:
            os.fchmod(f.fileno(),0o400);json.dump(result,f,sort_keys=True);f.flush();os.fsync(f.fileno())
