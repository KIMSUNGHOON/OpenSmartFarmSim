"""Stored model cohort stocks and continuous counters; no crop equations."""
from copy import deepcopy
from fractions import Fraction
from hashlib import sha256
from pathlib import Path

from . import crop_supply_material_artifact_reader as reader
from .crop_morphology_artifact_io import MorphologyArtifactHold,MorphologyBlobStore,_need

VERSION='supply-material-quantity-window-v1'
CODE_SHA256=sha256(Path(__file__).read_bytes()).hexdigest()
MAX_RESPONSE_BYTES=2*1024**2
MASS,NUMBER='mg_CH2O/m2_floor','fruits_equivalent/m2_floor'
COUNTERS={'terminal_carbon':MASS,'terminal_number':NUMBER,
    **dict.fromkeys(('sensible','latent','incoming_heat','outgoing_heat','canopy_external','air_external'),'J/m2_floor'),
    **dict.fromkeys(('vapor','external_vapor'),'kg_water/m2_floor')}
q,x=reader.q,reader.x


class MaterialQuantityHold(ValueError):
    """The source-bound stored quantity window cannot be returned."""


def _code_fence():
    _need(sha256(Path(__file__).read_bytes()).hexdigest()==CODE_SHA256,'CODE_HOLD: unchanged loaded material quantity projection required')


def _frame(frame):
    layout=frame['state_layout']['original']
    _need(layout['plant']==['buffer','temperature_filtered_24h','temperature_sum']
        and layout['cohort_arrays']==['fruit_carbohydrate','fruit_number']
        and layout['units']['cohort_arrays']=={'fruit_carbohydrate':MASS,'fruit_number':NUMBER},
        'LAYOUT_HOLD: original50-cohort order and units required')
    state=frame['snapshot']['state'];carbon,number=state[3:53],state[53:103]
    _need(len(carbon)==len(number)==50,'STATE_HOLD: original50-cohort stocks required')
    for c,n in zip(carbon,number,strict=True):
        reader.legacy.projection.nonnegative(c);reader.legacy.projection.nonnegative(n)
        _need(c==0 or n>0,'STATE_HOLD: positive cohort carbon requires represented fruit number')
    cumulative={}
    for name,unit in COUNTERS.items():
        value=frame['lifetime_transfers_exact'][name];v=x(value,unit)
        if name in ('terminal_carbon','terminal_number'):_need(v>=0,'QUANTITY_HOLD: nonnegative original terminal counter required')
        cumulative[name]=deepcopy(value)
    reference={**reader.frame_descriptor(frame),'state_sha256':reader.digest(state),'state_kind':frame['state_kind']}
    return {'reference':reference,'at':deepcopy(frame['at']),'phase':frame['phase'],
        'fruit_carbohydrate':{'values':list(carbon),'unit':MASS},'fruit_number':{'values':list(number),'unit':NUMBER},
        'carbohydrate_stock_exact':q(sum(map(Fraction,carbon),Fraction(0)),MASS),
        'number_stock_exact':q(sum(map(Fraction,number),Fraction(0)),NUMBER),'cumulative_exact':cumulative}


def _interval(left,right):
    _need(left['at']['time_origin_utc']==right['at']['time_origin_utc'],'TIME_HOLD: same original model time origin required')
    a,b=left['reference'],right['reference']
    _need(type(a['index'])is int and type(b['index'])is int and b['index']==a['index']+1,
        'ORDER_HOLD: adjacent original frame indices required')
    duration=x(right['at']['elapsed_seconds_exact'],'s')-x(left['at']['elapsed_seconds_exact'],'s')
    _need(duration>=0,'TIME_HOLD: ordered original exact model time required')
    flows={name:q(x(right['cumulative_exact'][name],unit)-x(left['cumulative_exact'][name],unit),unit)for name,unit in COUNTERS.items()}
    for name in ('terminal_carbon','terminal_number'):_need(x(flows[name],COUNTERS[name])>=0,'ORDER_HOLD: nondecreasing original terminal counter required')
    if duration==0:
        _need(left['phase']=='material_before'and right['phase']=='material_after'
            and type(a['event_sequence'])is int and type(b['event_sequence'])is int and b['event_sequence']==a['event_sequence']+1,
            'BOUNDARY_HOLD: actual once-consumed equal-time material boundary required')
        _need(all(x(v,COUNTERS[k])==0 for k,v in flows.items())
            and all(left[k]==right[k]for k in ('fruit_carbohydrate','fruit_number')),
            'BOUNDARY_HOLD: continuous counters and fruit stocks must not jump at this material point')
    return {'from_frame':deepcopy(a),'to_frame':deepcopy(b),'start_at':deepcopy(left['at']),'end_at':deepcopy(right['at']),
        'elapsed_seconds_exact':q(duration,'s'),'kind':'zero_duration_material_boundary'if duration==0 else'stored_model_interval',
        'flows_exact':flows}


def read_material_quantity_window(directory,access,root_sha256,*,first_frame=0,last_frame=None):
    """Read a trusted stored root; quantities are not harvest or purchase meters."""
    try:
        _code_fence()
        _need(type(first_frame)is int and 0<=first_frame<512
            and(last_frame is None or type(last_frame)is int and first_frame<=last_frame<512),
            'WINDOW_HOLD: bounded inclusive original indices required')
        reader.legacy._hash(root_sha256)
        with MorphologyBlobStore(directory,access)as store:
            manifest,original,raws=reader._load(store,root_sha256)
            rights=reader._rights(manifest['effective_rights']);_need(rights['display'],'RIGHTS_HOLD: current embedded display permission required')
            last=len(original)-1 if last_frame is None else last_frame
            _need(first_frame<=last<len(original),'WINDOW_HOLD: existing stored frame required')
            basis=original[0]['model_floor_area']
            _need(all(f['model_floor_area']==basis for f in original),'BASIS_HOLD: unchanged original floor basis required')
            frames=[_frame(f)for f in original[first_frame:last+1]]
            intervals=[_interval(a,b)for a,b in zip(frames,frames[1:])]
            totals={}
            for name,unit in COUNTERS.items():
                delta=x(frames[-1]['cumulative_exact'][name],unit)-x(frames[0]['cumulative_exact'][name],unit)
                _need(sum((x(row['flows_exact'][name],unit)for row in intervals),Fraction(0))==delta,
                    'BALANCE_HOLD: exact selected endpoint telescoping required')
                totals[name]=q(delta,unit)
            result={'schema_version':VERSION,'scope':'software_research_only','claim_scope':'stored_synthetic_material_quantities_only',
                'time_kind':manifest['time_kind'],'G0_G4':manifest['G0_G4'],'R2':manifest['R2'],'projection_code_sha256':CODE_SHA256,
                'source':{'artifact_sha256':root_sha256,**{k:deepcopy(manifest[k])for k in ('code_sha256','effective_rights','source','window','terminal')}},
                'model_floor_area':deepcopy(basis),'counter_units':deepcopy(COUNTERS),
                'window':{'first_frame':first_frame,'last_frame':last,'start_at':deepcopy(frames[0]['at']),'end_at':deepcopy(frames[-1]['at'])},
                'frames':frames,'intervals':intervals,'totals_exact':totals}
            _need(len(reader.raw(result))<=MAX_RESPONSE_BYTES,'CAPACITY_HOLD: bounded material quantity response required')
            reader._fence(store,manifest,raws);_code_fence();return deepcopy(result)
    except MaterialQuantityHold:raise
    except MorphologyArtifactHold as error:raise MaterialQuantityHold(str(error))from None
    except(OSError,ValueError,TypeError,KeyError,OverflowError,ZeroDivisionError,RecursionError):
        raise MaterialQuantityHold('QUANTITY_HOLD: invalid or unavailable original material quantities')from None
