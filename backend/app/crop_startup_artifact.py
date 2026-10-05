"""Immutable startup calculation bytes, before farm rights and DB custody."""
from datetime import timedelta
from hashlib import sha256
from math import fsum
from pathlib import Path
import platform

from . import crop_plant_startup_integration as integration
from . import crop_coupled_artifact as legacy_artifact
from . import thermal_run_store as json_store

VERSION = 'crop-startup-artifact-v1'
MAX_PROGRAM_BYTES = legacy_artifact.MAX_PROGRAM_BYTES
MAX_ARTIFACT_BYTES = legacy_artifact.MAX_ARTIFACT_BYTES
NOTICE_SHA256 = legacy_artifact.NOTICE_SHA256
ARTIFACT_CODE_SHA256 = sha256(Path(__file__).read_bytes()).hexdigest()
DEPENDENCIES = {'legacy_artifact':legacy_artifact, 'canonical_json':json_store}
ARTIFACT_DEPENDENCY_SHA256 = {k:sha256(Path(m.__file__).read_bytes()).hexdigest()
                            for k,m in DEPENDENCIES.items()}
PROFILE_TYPES = legacy_artifact.PROFILE_TYPES
_canonical, _document, _time = json_store._canonical, json_store._document, json_store._time
_program, _quantity, _state, _events = (
    legacy_artifact._program, legacy_artifact._quantity, legacy_artifact._state, legacy_artifact._events)


class StartupArtifactHold(ValueError):
    """No calculated or replayable startup artifact for this request."""


def _need(condition):
    if not condition:raise StartupArtifactHold('startup research artifact unavailable')


def _digest(raw):
    return sha256(raw).hexdigest()


def _profiles(profiles,notice_raw):
    _need(all(type(profiles[k]) is cls for k,cls in PROFILE_TYPES.items())
          and type(notice_raw) is bytes and _digest(notice_raw)==NOTICE_SHA256)
    modules = {'integrator':integration,'coupled':integration.coupled,'startup':integration.startup,
               'plant':integration.plant,'cohorts':integration.fruit,'allocation':integration.allocation,
               'transport':integration.transport,'legacy_helpers':integration.legacy,
               'original_rates':integration.legacy.coupled}
    _need(integration.CODE_HASHES=={k:_digest(Path(m.__file__).read_bytes()) for k,m in modules.items()}
          and ARTIFACT_CODE_SHA256==_digest(Path(__file__).read_bytes())
          and ARTIFACT_DEPENDENCY_SHA256=={k:_digest(Path(m.__file__).read_bytes()) for k,m in DEPENDENCIES.items()})


def _schedule(program):
    boundaries = set(map(integration._utc,program['output_times']))
    boundaries.update(integration._utc(s['end']) for s in program['segments'])
    boundaries.update(integration._utc(e['at']) for e in program['events'])
    ordered = sorted(boundaries);steps_at = {ordered[0]:0};steps = 0
    h = program['solver']['max_step_seconds']
    for begin,end in zip(ordered,ordered[1:]):
        while begin<end:
            begin += timedelta(seconds=min(h,int((end-begin).total_seconds())))
            steps += 1;steps_at[begin] = steps
    return steps_at,boundaries


def _sample(sample,seed,operations,profile,*,confirmed=False):
    keys = {'at','state','cumulative','startup_diagnostics','lai','fruit_carbohydrate_total',
            'carbon_residual','carbon_residual_budget','number_residual','number_residual_budget'}
    _need(type(sample) is dict and set(sample)==keys|({'phase'} if confirmed else set()))
    at = integration._utc(sample['at']);vector = _state(sample['state'])
    cumulative = sample['cumulative']
    _need(type(cumulative) is dict and set(cumulative)==set(integration.FLUX))
    vector.extend(_quantity(cumulative[k],integration.FLUX_UNITS[k]) for k in integration.FLUX)
    _need(_quantity(sample['lai'],'m2_leaf/m2_floor')==profile.values['sla']*vector[1]
          and _quantity(sample['fruit_carbohydrate_total'],integration.plant.MASS_UNIT)==fsum(vector[55:105]))
    carbon,number,cb,nb,expected = integration._ledger(vector,seed,operations,at,profile.values['cFruitG'])
    for key,value,budget,unit in (('carbon',carbon,cb,integration.plant.MASS_UNIT),
                               ('number',number,nb,'fruits_equivalent/m2_floor')):
        actual = _quantity(sample[key+'_residual'],unit,signed=True)
        supplied = _quantity(sample[key+'_residual_budget'],unit)
        _need(actual==value and abs(actual)<=supplied<=budget)
    diagnostics = sample['startup_diagnostics']
    _need(type(diagnostics) is dict and set(diagnostics)==set(expected))
    for key in ('requested','growth_respiration'):
        residual,budget = key+'_residual',key+'_budget'
        actual = _quantity(diagnostics[residual],integration.plant.MASS_UNIT,signed=True)
        supplied = _quantity(diagnostics[budget],integration.plant.MASS_UNIT)
        _need(actual==expected[residual]['value'] and abs(actual)<=supplied<=expected[budget]['value'])


def _event_prefix(sample,journal):
    carbon = number = 0.0
    for event in journal:
        if event['at']>sample['at']:break
        removed = event['removed']
        carbon = fsum((carbon,removed['leaf']['value'],removed['stem_root']['value'],
                       *(q['value'] for q in removed['fruit_carbohydrate'])))
        number = fsum((number,*(q['value'] for q in removed['fruit_number'])))
        if event['at']==sample['at']:_need(sample['state']==event['after'])
    _need(sample['cumulative']['event_carbohydrate']['value']==carbon
          and sample['cumulative']['event_number']['value']==number)


def _manifest(program,blocks,profiles):
    manifest = {'program_version':integration.PROGRAM_VERSION,'integrator_version':integration.INTEGRATOR_VERSION,
        'rate_model_version':integration.coupled.MODEL_VERSION,
        'profile_sha256':{k:p.sha256 for k,p in profiles.items()},'policy_sha256':integration.startup.POLICY_SHA256,
        'allocation_policy_sha256':integration.allocation.POLICY_SHA256,'code_sha256':dict(integration.CODE_HASHES),
        'solver':dict(program['solver']),'time_rule':'UTC_POSIX_whole_seconds_v1',
        'python_version':platform.python_version(),'temperature_sum_method':'analytic_piecewise_constant_fraction_v1',
        'convergence':'not_evaluated_for_this_program','origins':sorted({b['origin'] for b in blocks}),
        'input_ids':[b['input_id'] for b in blocks],'research_assumptions':list(integration.legacy.coupled.ASSUMPTIONS),
        'startup_transition':'zero_or_positive_tail_research_only_not_validated_sink_capacity',
        'startup_balance_rule':'64-ulp-per-operation-without-absolute-floor-v1'}
    manifest['input_sha256'] = integration._hash({'program':program,'manifest':manifest})
    return manifest


def _result(result,program,planned,blocks,profiles):
    _need(type(result) is dict and result.get('status') in ('completed','hold'))
    held = result['status']=='hold'
    keys = {'status','scope','manifest','steps','planned_steps','samples','events','result_sha256'}
    _need(set(result)==keys|({'hold','last_confirmed'} if held else set())
          and result['scope']=='software_research_only' and type(result['steps']) is int
          and 0<=result['steps']<=planned and type(result['planned_steps']) is int and result['planned_steps']==planned
          and result['result_sha256']==integration._hash({k:v for k,v in result.items() if k!='result_sha256'})
          and result['manifest']==_manifest(program,blocks,profiles))
    _events(result['events'],program)
    journal = result['events'];samples = result['samples'];times = program['output_times']
    _need(type(samples) is list and len(samples)<=len(times)
          and all(type(s) is dict for s in samples) and [s['at'] for s in samples]==times[:len(samples)])
    steps_at,boundaries = _schedule(program)
    seed = _state(program['initial_state']['values'])+[0.0]*len(integration.FLUX)
    event_times = [integration._utc(e['at']) for e in journal]
    profile = profiles['growth_profile']
    for sample in samples:
        at = integration._utc(sample['at'])
        _need(steps_at[at]<=result['steps'])
        operations = steps_at[at]+sum(t<=at for t in event_times)
        _sample(sample,seed,operations,profile);_event_prefix(sample,journal)
    if not held:
        _need(result['steps']==planned and len(samples)==len(times) and len(journal)==len(program['events']))
        return
    hold = result['hold']
    _need(type(hold) is dict and set(hold)=={'at','phase','reason'}
          and type(hold['phase']) is str and 0<len(hold['phase'])<=128
          and type(hold['reason']) is str and 0<len(hold['reason'])<=1024)
    at = _time(hold['at']);start = integration._utc(times[0]);end = integration._utc(times[-1])
    _need(hold['at']==integration._stamp(at) and start<=at<=end
          and all(integration._utc(s['at'])<at for s in samples) and all(t<=at for t in event_times))
    confirmed = result['last_confirmed']
    if confirmed is None:
        _need(result['steps']==0 and not samples and not journal)
        return
    _need(type(confirmed) is dict)
    confirmed_at = integration._utc(confirmed['at'])
    _need(confirmed_at in steps_at and steps_at[confirmed_at]==result['steps'] and start<=confirmed_at<=at
          and all(integration._utc(s['at'])<=confirmed_at for s in samples)
          and all(t<=confirmed_at for t in event_times))
    phase = confirmed['phase'];approved_here = confirmed_at in event_times
    _need((phase=='step-end' and result['steps']>0 and not approved_here)
          or (phase=='boundary-after-event' and approved_here)
          or (phase=='boundary' and confirmed_at in boundaries
              and not any(e['at']==confirmed['at'] for e in program['events'])))
    _sample(confirmed,seed,result['steps']+len(journal),profile,confirmed=True)
    # A failed boundary event leaves a confirmed step before that event.
    _event_prefix(confirmed,journal)
    if samples and samples[-1]['at']==confirmed['at']:
        _need({k:v for k,v in confirmed.items() if k!='phase'}==samples[-1])


def calculate_startup_artifact(program_raw,*,growth_profile,cohort_profile,transport_profile,notice_raw):
    """Compute bounded synthetic inputs into new immutable bytes outside requests."""
    profiles = {'growth_profile':growth_profile,'cohort_profile':cohort_profile,'transport_profile':transport_profile}
    try:
        _profiles(profiles,notice_raw);document,_,_,_ = _program(program_raw)
        result = integration.integrate_plant_startup(**document,**profiles)
        packet = {'schema_version':VERSION,'claim_scope':'synthetic_crop_math_only',
            'program_raw_utf8':program_raw.decode(),'program_sha256':_digest(program_raw),
            'profile_raw_utf8':{k:p.raw_bytes.decode() for k,p in profiles.items()},'notice_raw_utf8':notice_raw.decode(),
            'artifact_code_sha256':ARTIFACT_CODE_SHA256,'artifact_dependency_sha256':dict(ARTIFACT_DEPENDENCY_SHA256),
            'result':result}
        packet['artifact_id'] = VERSION+':'+_digest(_canonical(packet));raw = _canonical(packet)
        read_startup_artifact(raw,expected_sha256=_digest(raw),**profiles,notice_raw=notice_raw)
        return raw
    except StartupArtifactHold:raise
    except (ValueError,TypeError,KeyError,OverflowError,OSError,RecursionError,integration._EvaluationHold):
        raise StartupArtifactHold('startup research artifact unavailable') from None


def read_startup_artifact(raw,*,expected_sha256,growth_profile,cohort_profile,transport_profile,notice_raw):
    """Validate trusted bytes and ledgers without replaying the crop integrator."""
    profiles = {'growth_profile':growth_profile,'cohort_profile':cohort_profile,'transport_profile':transport_profile}
    try:
        _need(type(raw) is bytes and 0<len(raw)<=MAX_ARTIFACT_BYTES and type(expected_sha256) is str
              and expected_sha256==_digest(raw))
        _profiles(profiles,notice_raw);packet = _document(raw,max_size=MAX_ARTIFACT_BYTES)
        _need(set(packet)=={'schema_version','claim_scope','program_raw_utf8','program_sha256','profile_raw_utf8',
                           'notice_raw_utf8','artifact_code_sha256','artifact_dependency_sha256','result','artifact_id'}
              and packet['schema_version']==VERSION and packet['claim_scope']=='synthetic_crop_math_only'
              and packet['artifact_code_sha256']==ARTIFACT_CODE_SHA256
              and packet['artifact_dependency_sha256']==ARTIFACT_DEPENDENCY_SHA256
              and packet['profile_raw_utf8']=={k:p.raw_bytes.decode() for k,p in profiles.items()}
              and packet['notice_raw_utf8']==notice_raw.decode()
              and packet['artifact_id']==VERSION+':'+_digest(_canonical({k:v for k,v in packet.items() if k!='artifact_id'}))
              and type(packet['program_raw_utf8']) is str)
        program_raw = packet['program_raw_utf8'].encode();_need(packet['program_sha256']==_digest(program_raw))
        _,normalized,planned,blocks = _program(program_raw)
        _result(packet['result'],normalized,planned,blocks,profiles)
        return packet
    except StartupArtifactHold:raise
    except (ValueError,TypeError,KeyError,OverflowError,OSError,RecursionError,integration._EvaluationHold):
        raise StartupArtifactHold('startup research artifact unavailable') from None
