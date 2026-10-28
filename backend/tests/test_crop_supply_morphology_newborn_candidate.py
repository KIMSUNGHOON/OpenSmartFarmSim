from fractions import Fraction

from test_crop_supply_morphology_newborn_resume import current,profiles,prepared,pending,calculated,adopted,trajectory


def test_actual_newborn_next_candidate_refines_the_current_unadopted_interval(request):
    from app import crop_supply_morphology_newborn_candidate as model
    context=request.getfixturevalue('adopted')[0];path=request.getfixturevalue('trajectory');cp=path['last_confirmed'];raw=model.resume._canonical(cp)
    out=model.calculate_next_event_candidate(context,raw,expected_sha256=model.resume._hash(cp),time_tolerance_seconds_exact={'numerator':'1','denominator':'1000','unit':'s'})
    root=out['numerical_root_interval'];X=model.X
    assert out['source_interval']==path['pending_event']['interval']
    assert X(root['upper_elapsed_seconds_exact'])-X(root['lower_elapsed_seconds_exact'])<=Fraction(1,1000)
    assert X(root['lower_threshold_residual_exact'])<0<=X(root['upper_threshold_residual_exact'])
    assert len(out['dense_candidate']['global_ledgers'])==74
    assert [r['substeps']for r in out['refinements']]==[1,2,4]and all(r['at']==out['at']for r in out['refinements'])
    assert out['source_next_sequence']==cp['schedule']['next_sequence']and out['source_prefix']==cp
    assert out['current_validation_RHS_evaluations']==1 and out['new_RHS_evaluations']==33
    assert out['schedule_consumed']is out['new_organs_created']is False and out['integrator_checkpoint']is None
    assert out['dense_candidate']['point_totals_exact']==cp['point_totals_exact']and out['G0_G4']=='not_assessed'


import pytest


@pytest.fixture(scope='module')
def post_pending(adopted,trajectory):
    from app import crop_supply_morphology_newborn_resume as resume
    context=adopted[0];raw=resume._canonical(trajectory['last_confirmed']);return context,raw,resume._hash(trajectory['last_confirmed']),trajectory['pending_event']


@pytest.fixture(scope='module')
def post_calculated(post_pending):
    from app import crop_supply_morphology_newborn_candidate as model
    ctx,raw,digest,_=post_pending
    return model.calculate_next_event_candidate(ctx,raw,expected_sha256=digest,time_tolerance_seconds_exact={'numerator':'1','denominator':'1000','unit':'s'})


def test_candidate_rejects_a_detached_context():
    from app import crop_supply_morphology_newborn_candidate as model
    with pytest.raises(model.SupplyCandidateHold):
        model.calculate_next_event_candidate(None,b'{}',expected_sha256='0'*64,time_tolerance_seconds_exact={'numerator':'1','denominator':'1000','unit':'s'})


def test_dense_state_all_channels_and_global_accounts_use_actual_stages(post_calculated):
    from app import crop_supply_morphology_newborn_candidate as model
    out=post_calculated;trace=out['source_interval'];cp=out['source_prefix'];rows=trace['stages'];F=Fraction.from_float;X=model.X
    h=X(trace['step_seconds_exact']);duration=X(out['partial_interval_seconds_exact']);theta=duration/h
    weights=(theta-3*theta**2/2+2*theta**3/3,theta**2-2*theta**3/3,theta**2-2*theta**3/3,-theta**2/2+2*theta**3/3)
    for i,value in enumerate(out['dense_candidate']['state']):
        assert value==float(F(cp['last_confirmed']['state'][i])+h*sum((w*F(r['rates'][i])for w,r in zip(weights,rows,strict=True)),Fraction(0)))
    candidate=out['dense_candidate']
    for i,entry in enumerate(trace['flux_order']):
        name=entry['name'];partial=float(h*sum((w*F(r['flux'][i])for w,r in zip(weights,rows,strict=True)),Fraction(0)))
        assert candidate['partial_interval_transfers'][name]=={'value':partial,'unit':entry['unit']}
        assert X(candidate['pending_branch_transfers_exact'][name])==F(cp['branch_integrated_transfers'][name]['value'])+F(partial)
    for name in candidate['global_ledgers']:
        for field in ['residual_exact','budget_exact']:
            assert X(candidate['global_ledgers'][name][field])==X(cp['global_ledgers'][name][field])+X(candidate['local_ledgers'][name][field])
            assert X(candidate['branch_ledgers'][name][field])==X(cp['branch_ledgers'][name][field])+X(candidate['local_ledgers'][name][field])
    assert candidate['point_totals_exact']==cp['point_totals_exact']
    assert all(X(row['deficit_exact'])>=0 and 'canonical_gap_exact'in row and 'canonical_potential_difference_exact'in row for row in candidate['geometry_diagnostics'].values())


def test_refinements_compare_same_full_state_and_actual_differences(post_calculated):
    from app import crop_supply_morphology_newborn_candidate as model
    rows=post_calculated['refinements'];X=model.X;F=Fraction.from_float
    assert len(post_calculated['state_coordinates'])==len(post_calculated['state_differences'])==146
    for i,row in enumerate(post_calculated['state_differences']):
        assert X(row['one_to_two_exact'])==abs(F(rows[0]['state'][i])-F(rows[1]['state'][i]))
        assert X(row['two_to_four_exact'])==abs(F(rows[1]['state'][i])-F(rows[2]['state'][i]))
    for i in [103,104,105]:assert X(post_calculated['state_differences'][i]['two_to_four_exact'])<X(post_calculated['state_differences'][i]['one_to_two_exact'])


@pytest.mark.parametrize('value',[
    {'numerator':'0','denominator':'1','unit':'s'},
    {'numerator':'-1','denominator':'1','unit':'s'},
    {'numerator':'9','denominator':'1','unit':'s'},
    {'numerator':'2','denominator':'2000','unit':'s'},
    {'numerator':'1','denominator':'1','unit':'m'},
    {'numerator':True,'denominator':'1','unit':'s'},
    {'numerator':'1','denominator':'0','unit':'s'},
    {'numerator':'1','denominator':'1','unit':'s','extra':1},
    {'numerator':'1'*129,'denominator':'1','unit':'s'},
])
def test_invalid_tolerance_cannot_run_current_or_new_rhs(post_pending,monkeypatch,value):
    from app import crop_supply_morphology_newborn_candidate as model
    def forbidden(*args,**kw):raise AssertionError('invalid tolerance cannot run RHS')
    monkeypatch.setattr(model.resume.owner.point.core.stage,'evaluate',forbidden)
    ctx,raw,digest,_=post_pending
    with pytest.raises(model.SupplyCandidateHold):model.calculate_next_event_candidate(ctx,raw,expected_sha256=digest,time_tolerance_seconds_exact=value)


@pytest.mark.parametrize('field',['state','flow','schedule','prefix','version'])
def test_self_rehashed_altered_checkpoint_cannot_authorize_a_candidate(post_pending,field):
    from copy import deepcopy
    from hashlib import sha256
    from app import crop_supply_morphology_newborn_candidate as model
    ctx,raw,_,_=post_pending;p=deepcopy(model.resume._parse(raw,sha256(raw).hexdigest(),model.resume.MAX_CP))
    if field=='state':p['last_confirmed']['state'][0]+=1.
    elif field=='flow':p['branch_integrated_transfers']['photosynthesis']['value']+=1.
    elif field=='schedule':p['schedule']['next_sequence']+=1
    elif field=='prefix':p['output_prefix_sha256']='0'*64
    else:p['version']='other'
    changed=model.resume._canonical(p)
    with pytest.raises(model.SupplyCandidateHold):model.calculate_next_event_candidate(ctx,changed,expected_sha256=sha256(changed).hexdigest(),time_tolerance_seconds_exact={'numerator':'1','denominator':'1000','unit':'s'})


def test_nonbracketing_current_interval_does_not_search_a_later_event(adopted):
    from app import crop_supply_morphology_newborn_candidate as model
    prepared=adopted[0];cp=model.resume.start(prepared);raw=model.resume.checkpoint_bytes(prepared,cp)
    with pytest.raises(model.SupplyCandidateHold,match='THRESHOLD_HOLD'):
        model.calculate_next_event_candidate(prepared,raw,expected_sha256=cp.sha256,time_tolerance_seconds_exact={'numerator':'1','denominator':'1000','unit':'s'})
    assert model.resume.checkpoint_bytes(prepared,cp)==raw


def test_actual_candidate_uses_one_new_current_and_thirty_three_new_rhs_without_old_biology(post_pending,post_calculated,monkeypatch):
    from app import crop_supply_morphology_newborn_candidate as model
    ctx,raw,digest,_=post_pending;calls=[];run=model.resume.owner.point.core.stage.evaluate
    def counted(*args,**kw):calls.append(1);return run(*args,**kw)
    def forbidden(*args,**kw):raise AssertionError('no old trajectory, initialization, point or CP issuance')
    for owner,name in [(model.source.stock.short,'_evaluate'),(model.source,'advance_chunk'),(model.source,'restore_checkpoint'),(model.source,'adopt_first'),(model.source,'adopt_successor'),(model.source.stock.short.old.leaf_area,'initialize_leaf_area'),(model.resume.owner,'prepare_context'),(model.resume.owner,'restore_checkpoint'),(model.resume.owner.point,'apply_fractional_material_point'),(model.resume.owner.point.core.arithmetic,'_fund'),(model.resume.owner.point.core.arithmetic,'_new_leaf'),(model.resume.resume,'_rhs'),(model.resume,'start'),(model.resume,'restore_checkpoint'),(model.resume,'advance_chunk'),(model.resume,'_seal')]:monkeypatch.setattr(owner,name,forbidden)
    monkeypatch.setattr(model.resume.owner.point.core.stage,'evaluate',counted)
    out=model.calculate_next_event_candidate(ctx,raw,expected_sha256=digest,time_tolerance_seconds_exact={'numerator':'1','denominator':'1000','unit':'s'})
    assert len(calls)==34 and out==post_calculated and model.resume._canonical(out['source_prefix'])==raw


@pytest.mark.parametrize('failure',['k2_domain','dense_domain','late_profile','runtime'])
def test_failed_stage_and_late_profile_never_return_a_partial_candidate(post_pending,monkeypatch,failure):
    from app import crop_supply_morphology_newborn_candidate as model
    ctx,raw,digest,_=post_pending;run=model.resume.owner.point.core.stage.evaluate;calls=[];profile=ctx._origin._source._source._root._profiles[0];original=profile.filtered_temperature_bounds
    def changed(*args,**kw):
        calls.append(1)
        if len(calls)==2 and failure=='runtime':raise RuntimeError('unexpected candidate stage')
        if (len(calls)==2 and failure=='k2_domain')or(len(calls)==6 and failure=='dense_domain'):raise ValueError('DOMAIN_HOLD: deliberately unsupported new state')
        out=run(*args,**kw)
        if len(calls)==34 and failure=='late_profile':object.__setattr__(profile,'filtered_temperature_bounds',(1.,2.))
        return out
    monkeypatch.setattr(model.resume.owner.point.core.stage,'evaluate',changed)
    try:
        with pytest.raises(RuntimeError if failure=='runtime'else model.SupplyCandidateHold):
            model.calculate_next_event_candidate(ctx,raw,expected_sha256=digest,time_tolerance_seconds_exact={'numerator':'1','denominator':'1000','unit':'s'})
    finally:object.__setattr__(profile,'filtered_temperature_bounds',original)


def test_unresolved_tight_root_is_bounded_without_clamping_or_snapping(post_pending):
    from app import crop_supply_morphology_newborn_candidate as model
    ctx,raw,digest,_=post_pending
    with pytest.raises(model.SupplyCandidateHold,match='PRECISION_HOLD'):
        model.calculate_next_event_candidate(ctx,raw,expected_sha256=digest,time_tolerance_seconds_exact={'numerator':'1','denominator':str(2**150),'unit':'s'})


@pytest.mark.parametrize('when',['current','last_stage'])
def test_new_candidate_code_is_fenced_before_and_after_calculation(post_pending,monkeypatch,when):
    from app import crop_supply_morphology_newborn_candidate as model
    ctx,raw,digest,_=post_pending;run=model.resume.owner.point.core.stage.evaluate;calls=[]
    if when=='current':monkeypatch.setattr(model,'CODE_SHA256','0'*64)
    else:
        def changed(*args,**kw):
            out=run(*args,**kw);calls.append(1)
            if len(calls)==34:monkeypatch.setattr(model,'CODE_SHA256','0'*64)
            return out
        monkeypatch.setattr(model.resume.owner.point.core.stage,'evaluate',changed)
    with pytest.raises(model.SupplyCandidateHold,match='CODE_HOLD'):
        model.calculate_next_event_candidate(ctx,raw,expected_sha256=digest,time_tolerance_seconds_exact={'numerator':'1','denominator':'1000','unit':'s'})


@pytest.mark.parametrize('when',['current','last_stage'])
def test_actual_source_access_loss_never_returns_a_candidate(post_pending,monkeypatch,when):
    from pathlib import Path
    from stat import S_IMODE
    from app import crop_supply_morphology_newborn_candidate as model
    ctx,raw,digest,_=post_pending;directory=Path(ctx._origin._source._source._directories[0]);mode=S_IMODE(directory.stat().st_mode);run=model.resume.owner.point.core.stage.evaluate;calls=[]
    def changed(*args,**kw):
        out=run(*args,**kw);calls.append(1)
        if len(calls)==34:directory.chmod(0)
        return out
    try:
        if when=='current':directory.chmod(0)
        else:monkeypatch.setattr(model.resume.owner.point.core.stage,'evaluate',changed)
        with pytest.raises(model.SupplyCandidateHold):
            model.calculate_next_event_candidate(ctx,raw,expected_sha256=digest,time_tolerance_seconds_exact={'numerator':'1','denominator':'1000','unit':'s'})
    finally:directory.chmod(mode)


@pytest.mark.parametrize('kind',['oversized','wrong_sha'])
def test_raw_checkpoint_bounds_and_trusted_hash_hold_before_rhs(post_pending,monkeypatch,kind):
    from hashlib import sha256
    from app import crop_supply_morphology_newborn_candidate as model
    ctx,raw,digest,_=post_pending
    def forbidden(*args,**kw):raise AssertionError('untrusted input cannot run RHS')
    monkeypatch.setattr(model.resume.owner.point.core.stage,'evaluate',forbidden)
    if kind=='oversized':raw=b' '*(model.resume.MAX_CP+1);digest=sha256(raw).hexdigest()
    else:digest='0'*64
    with pytest.raises(model.SupplyCandidateHold,match='HASH_HOLD'):
        model.calculate_next_event_candidate(ctx,raw,expected_sha256=digest,time_tolerance_seconds_exact={'numerator':'1','denominator':'1000','unit':'s'})


def test_output_capacity_failure_does_not_emit_or_change_the_source_checkpoint(post_pending,monkeypatch):
    from app import crop_supply_morphology_newborn_candidate as model
    ctx,raw,digest,_=post_pending
    monkeypatch.setattr(model,'MAX_BYTES',1)
    with pytest.raises(model.SupplyCandidateHold,match='CAPACITY_HOLD'):
        model.calculate_next_event_candidate(ctx,raw,expected_sha256=digest,time_tolerance_seconds_exact={'numerator':'1','denominator':'1000','unit':'s'})
    assert model.resume._canonical(model.resume._parse(raw,digest,model.resume.MAX_CP))==raw


def test_caller_tolerance_changed_during_calculation_cannot_relabel_root_accuracy(post_pending,monkeypatch):
    from app import crop_supply_morphology_newborn_candidate as model
    ctx,raw,digest,_=post_pending;run=model.resume.owner.point.core.stage.evaluate;calls=[];tolerance={'numerator':'1','denominator':'1000','unit':'s'}
    def changed(*args,**kw):
        out=run(*args,**kw);calls.append(1)
        if len(calls)==34:tolerance['denominator']='1000000'
        return out
    monkeypatch.setattr(model.resume.owner.point.core.stage,'evaluate',changed)
    with pytest.raises(model.SupplyCandidateHold,match='SOURCE_HOLD'):
        model.calculate_next_event_candidate(ctx,raw,expected_sha256=digest,time_tolerance_seconds_exact=tolerance)
