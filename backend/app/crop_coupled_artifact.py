"""Bounded calculation artifacts, before tenant/farm rights and DB custody."""
from hashlib import sha256
from math import fsum, isfinite
from pathlib import Path
import platform

from . import crop_plant_cohort_integration as integration
from .thermal_run_store import _canonical, _document, _time


VERSION='crop-coupled-artifact-v1'
MAX_PROGRAM_BYTES=1024*1024
MAX_ARTIFACT_BYTES=16*1024*1024
NOTICE_SHA256='96ce8c1f3d7b5473f473417c2785c63b74148edaddc2b9b6d40a6bbe3b7f4b6a'
ARTIFACT_CODE_SHA256=sha256(Path(__file__).read_bytes()).hexdigest()
PROFILE_TYPES={'growth_profile':integration.plant.ReferenceParameters,
               'cohort_profile':integration.fruit.ReferenceFruitCohortParameters,
               'transport_profile':integration.transport.ReferenceFruitTransportParameters}
PROGRAM_FIELDS={'initial_state','segments','events','output_times','solver'}


class CoupledArtifactHold(ValueError):
    """No calculated or replayable artifact for this request."""


def _need(condition):
    if not condition:raise CoupledArtifactHold('coupled research artifact unavailable')


def _digest(raw):
    return sha256(raw).hexdigest()


def _profiles(profiles,notice_raw):
    _need(all(type(profiles[k]) is cls for k,cls in PROFILE_TYPES.items())
          and type(notice_raw) is bytes and _digest(notice_raw)==NOTICE_SHA256)
    modules={'integrator':integration,'coupled':integration.coupled,'plant':integration.plant,
             'cohorts':integration.fruit,'allocation':integration.allocation,'transport':integration.transport}
    _need(integration.CODE_HASHES=={k:_digest(Path(m.__file__).read_bytes()) for k,m in modules.items()}
          and ARTIFACT_CODE_SHA256==_digest(Path(__file__).read_bytes()))


def _program(raw):
    document=_document(raw,max_size=MAX_PROGRAM_BYTES)
    _need(set(document)==PROGRAM_FIELDS)
    normalized,_,planned=integration._prepare(**document)
    blocks=[normalized['initial_state']]+[s[k] for s in normalized['segments']
        for k in ('forcing','removals','fruit_entry','relative_growth_rate')]
    blocks += [e['removals'] for e in normalized['events']]
    seen={}
    for block in blocks:
        _need(block['origin']=='synthetic'
              and (block['input_id'] not in seen or seen[block['input_id']]==block))
        seen[block['input_id']]=block
    return document,normalized,planned,blocks


def _quantity(q,unit,*,signed=False):
    _need(type(q) is dict and set(q)=={'value','unit'} and q['unit']==unit
          and type(q['value']) in (int,float) and isfinite(q['value'])
          and (signed or q['value']>=0))
    return q['value']


def _state(record):
    _need(type(record) is dict and set(record)==set(integration.PLANT)|set(integration.ARRAY_UNITS))
    vector=[_quantity(record[k],integration.coupled.PLANT_UNITS[k]) for k in integration.PLANT]
    for k,unit in integration.ARRAY_UNITS.items():
        _need(type(record[k]) is list and len(record[k])==50)
        vector.extend(_quantity(q,unit) for q in record[k])
    _need(all(c==0 or n>0 for n,c in zip(vector[5:55],vector[55:105],strict=True)))
    return vector


def _sample(sample,seed,operations,profile,*,confirmed=False):
    keys={'at','state','cumulative','lai','fruit_carbohydrate_total','carbon_residual',
          'carbon_residual_budget','number_residual','number_residual_budget'}
    _need(type(sample) is dict and set(sample)==keys|({'phase'} if confirmed else set()))
    at=integration._utc(sample['at']);vector=_state(sample['state'])
    cumulative=sample['cumulative']
    _need(type(cumulative) is dict and set(cumulative)==set(integration.FLUX))
    vector.extend(_quantity(cumulative[k],integration.FLUX_UNITS[k]) for k in integration.FLUX)
    _need(_quantity(sample['lai'],'m2_leaf/m2_floor')==profile.values['sla']*vector[1]
          and _quantity(sample['fruit_carbohydrate_total'],integration.plant.MASS_UNIT)==fsum(vector[55:105]))
    carbon,number,cb,nb=integration._ledger(vector,seed,operations,at)
    for key,value,budget,unit in (('carbon',carbon,cb,integration.plant.MASS_UNIT),
        ('number',number,nb,'fruits_equivalent/m2_floor')):
        actual=_quantity(sample[key+'_residual'],unit,signed=True)
        supplied=_quantity(sample[key+'_residual_budget'],unit)
        _need(actual==value and abs(actual)<=supplied<=budget)
    if confirmed:_need(sample['phase'] in ('step-end','boundary','boundary-after-event'))


def _events(journal,program):
    _need(type(journal) is list and len(journal)<=len(program['events']))
    for record,event in zip(journal,program['events']):
        _need(type(record) is dict and set(record)=={'at','input_id','before','after','removed'}
              and record['at']==event['at'] and record['input_id']==event['removals']['input_id'])
        before=_state(record['before']);after=_state(record['after']);expected=list(before)
        values=event['removals']['values'];removed=record['removed']
        _need(type(removed) is dict and set(removed)=={'leaf','stem_root',*integration.ARRAY_UNITS})
        for j,k in enumerate(('leaf','stem_root'),start=1):
            _need(removed[k]==values[k]);expected[j]-=values[k]['value']
        for k,offset in (('fruit_number',5),('fruit_carbohydrate',55)):
            _need(type(removed[k]) is list and len(removed[k])==50)
            for j,q in enumerate(removed[k]):
                amount=_quantity(q,integration.ARRAY_UNITS[k])
                _need(amount==before[offset+j]*values['fruit_fraction'][j]['value'])
                expected[offset+j]-=amount
        _need(after==expected)


def _result(result,program,planned,blocks,profiles):
    _need(type(result) is dict and result.get('status') in ('completed','hold'))
    held=result['status']=='hold'
    keys={'status','scope','manifest','steps','planned_steps','samples','events','result_sha256'}
    _need(set(result)==keys|({'hold','last_confirmed'} if held else set())
          and result['scope']=='software_research_only' and type(result['steps']) is int
          and 0<=result['steps']<=planned and result['planned_steps']==planned
          and result['result_sha256']==integration._hash({k:v for k,v in result.items() if k!='result_sha256'}))
    manifest={'integrator_version':integration.INTEGRATOR_VERSION,
        'rate_model_version':integration.coupled.MODEL_VERSION,
        'profile_sha256':{k:p.sha256 for k,p in profiles.items()},
        'policy_sha256':integration.allocation.POLICY_SHA256,'code_sha256':dict(integration.CODE_HASHES),
        'solver':dict(program['solver']),'time_rule':'UTC_POSIX_whole_seconds_v1',
        'python_version':platform.python_version(),'temperature_sum_method':'analytic_piecewise_constant_fraction_v1',
        'convergence':'not_evaluated_for_this_program','origins':sorted({b['origin'] for b in blocks}),
        'input_ids':[b['input_id'] for b in blocks],'research_assumptions':list(integration.coupled.ASSUMPTIONS)}
    manifest['input_sha256']=integration._hash({'program':program,'manifest':manifest})
    _need(result['manifest']==manifest)
    _events(result['events'],program)
    samples=result['samples'];times=program['output_times']
    _need(type(samples) is list and len(samples)<=len(times)
          and [s['at'] for s in samples]==times[:len(samples)])
    seed=_state(program['initial_state']['values'])+[0.0]*len(integration.FLUX)
    operations=result['steps']+len(result['events'])
    for sample in samples:_sample(sample,seed,operations,profiles['growth_profile'])
    if held:
        hold=result['hold'];_need(type(hold) is dict and set(hold)=={'at','phase','reason'}
            and type(hold['phase']) is str and 0<len(hold['phase'])<=128
            and type(hold['reason']) is str and 0<len(hold['reason'])<=1024)
        at=_time(hold['at']);start=integration._utc(times[0]);end=integration._utc(times[-1])
        _need(start<=at<=end and all(integration._utc(s['at'])<at for s in samples)
              and all(integration._utc(e['at'])<=at for e in result['events']))
        confirmed=result['last_confirmed']
        if confirmed is not None:
            _sample(confirmed,seed,operations,profiles['growth_profile'],confirmed=True)
            _need(start<=integration._utc(confirmed['at'])<=at)
        else:_need(result['steps']==0 and not samples and not result['events'])
    else:_need(result['steps']==planned and len(samples)==len(times)
               and len(result['events'])==len(program['events']))


def calculate_coupled_artifact(program_raw,*,growth_profile,cohort_profile,transport_profile,notice_raw):
    """Compute from canonical synthetic inputs; call outside request handlers."""
    profiles={'growth_profile':growth_profile,'cohort_profile':cohort_profile,'transport_profile':transport_profile}
    try:
        _profiles(profiles,notice_raw);document,_,_,_=_program(program_raw)
        result=integration.integrate_plant_cohorts(**document,**profiles)
        packet={'schema_version':VERSION,'claim_scope':'synthetic_crop_math_only',
                'program_raw_utf8':program_raw.decode(),'program_sha256':_digest(program_raw),
                'profile_raw_utf8':{k:p.raw_bytes.decode() for k,p in profiles.items()},
                'notice_raw_utf8':notice_raw.decode(),'artifact_code_sha256':ARTIFACT_CODE_SHA256,'result':result}
        packet['artifact_id']=VERSION+':'+_digest(_canonical(packet));raw=_canonical(packet)
        read_coupled_artifact(raw,expected_sha256=_digest(raw),**profiles,notice_raw=notice_raw)
        return raw
    except CoupledArtifactHold:raise
    except (ValueError,TypeError,KeyError,OverflowError,OSError,RecursionError,integration._EvaluationHold):
        raise CoupledArtifactHold('coupled research artifact unavailable') from None


def read_coupled_artifact(raw,*,expected_sha256,growth_profile,cohort_profile,transport_profile,notice_raw):
    """Check bounded bytes against a trusted digest without rerunning integration."""
    profiles={'growth_profile':growth_profile,'cohort_profile':cohort_profile,'transport_profile':transport_profile}
    try:
        _need(type(raw) is bytes and 0<len(raw)<=MAX_ARTIFACT_BYTES and type(expected_sha256) is str
              and expected_sha256==_digest(raw))
        _profiles(profiles,notice_raw);packet=_document(raw,max_size=MAX_ARTIFACT_BYTES)
        _need(set(packet)=={'schema_version','claim_scope','program_raw_utf8','program_sha256',
                           'profile_raw_utf8','notice_raw_utf8','artifact_code_sha256','result','artifact_id'}
              and packet['schema_version']==VERSION and packet['claim_scope']=='synthetic_crop_math_only'
              and packet['artifact_code_sha256']==ARTIFACT_CODE_SHA256
              and packet['profile_raw_utf8']=={k:p.raw_bytes.decode() for k,p in profiles.items()}
              and packet['notice_raw_utf8']==notice_raw.decode()
              and packet['artifact_id']==VERSION+':'+_digest(_canonical({k:v for k,v in packet.items() if k!='artifact_id'}))
              and type(packet['program_raw_utf8']) is str)
        program_raw=packet['program_raw_utf8'].encode();_need(packet['program_sha256']==_digest(program_raw))
        _,normalized,planned,blocks=_program(program_raw)
        _result(packet['result'],normalized,planned,blocks,profiles)
        return packet
    except CoupledArtifactHold:raise
    except (ValueError,TypeError,KeyError,OverflowError,OSError,RecursionError,integration._EvaluationHold):
        raise CoupledArtifactHold('coupled research artifact unavailable') from None
