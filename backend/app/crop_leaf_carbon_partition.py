"""Conditional budget partition; crop-leaf-carbon-partition-v1.md. No stock advance."""
from fractions import Fraction
from hashlib import sha256
import json
from math import fsum,isfinite,ulp
from pathlib import Path
import re
from sys import float_info

from . import crop_growth_rates as source

MODEL_VERSION='leaf-carbon-budget-partition-research-v1'
POLICY_ID='explicit-relative-leaf-sinks-and-empty-deferral-v1'
POLICY={'id':POLICY_ID,'weights':'declared_relative_priorities_not_mass_demand_caps',
    'empty':'defer_requested_leaf_growth_and_its_growth_respiration',
    'source_debit_basis':'requested_structural_leaf_growth_plus_profile_cLeafG_cost','stock_advance':False}
MAX=128*1024
CODE_SHA256=sha256(Path(__file__).read_bytes()).hexdigest()
SOURCE_SHA256=sha256(Path(source.__file__).read_bytes()).hexdigest()
POLICY_SHA256=sha256(json.dumps(POLICY,sort_keys=True,separators=(',',':')).encode()).hexdigest()


class LeafCarbonPartitionHold(ValueError):
    pass


def _need(condition,reason):
    if not condition:raise LeafCarbonPartitionHold(reason)


def _canonical(v):
    raw=json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
    _need(len(raw)<=MAX,'CAPACITY_HOLD: 128KiB partition input/output required');return raw


def _closed(v,keys):_need(type(v)is dict and set(v)==set(keys),'INPUT_HOLD: closed partition fields required')


def _normal(v):
    _need(isfinite(v)and(v==0 or abs(v)>=float_info.min),'NUMERIC_HOLD: finite normal value or zero required');return v


def _number(v,unit):
    _closed(v,{'value','unit'});_need(v['unit']==unit,'UNIT_HOLD: original quantity unit required')
    _need(type(v['value'])in(int,float),'INPUT_HOLD: explicit numeric quantity required')
    x=_normal(float(v['value']));_need(x>=0,'INPUT_HOLD: nonnegative partition quantity required');return x


def _id(v):_need(type(v)is str and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.:/-]{0,199}',v),'INPUT_HOLD: bounded ASCII identity required')


def _q(v,unit=source.RATE_UNIT):return {'value':v,'unit':unit}


def _fence():
    _need(sha256(Path(__file__).read_bytes()).hexdigest()==CODE_SHA256
        and sha256(Path(source.__file__).read_bytes()).hexdigest()==SOURCE_SHA256,'CODE_HOLD: partition source changed')


def calculate_partition(*,inputs,growth_profile):
    try:
        _fence();_need(type(growth_profile)is source.ReferenceParameters,'PROFILE_HOLD: pinned growth profile required')
        _need(growth_profile.sha256==source.PROFILE_SHA256==sha256(growth_profile.raw_bytes).hexdigest(),
            'PROFILE_HOLD: original pinned profile bytes required')
        c=growth_profile.values['cLeafG'];_need(c==float(json.loads(growth_profile.raw_bytes)['parameters']['cLeafG']['value'])and c>0,
            'PROFILE_HOLD: original leaf growth cost required')
        _closed(inputs,{'input_id','origin','policy','requested_leaf_growth','leaves'})
        _need(type(inputs['leaves'])is list,'INPUT_HOLD: declared leaf list required')
        raw=_canonical(inputs);v=json.loads(raw);_id(v['input_id'])
        _need(v['origin']=='synthetic'and v['policy']==POLICY_ID,'SCOPE_HOLD: explicit synthetic partition policy required')
        g=_number(v['requested_leaf_growth'],source.RATE_UNIT);rows=v['leaves']
        _need(1<=len(rows)<=512,'CAPACITY_HOLD: 1..512 declared leaves required')
        ids=[];weights=[]
        for row in rows:
            _closed(row,{'leaf_id','sink_weight'});_id(row['leaf_id']);ids.append(row['leaf_id']);weights.append(_number(row['sink_weight'],'1'))
        _need(len(set(ids))==len(ids),'INPUT_HOLD: unique original leaf IDs required')
        total=_normal(fsum(weights));denominator=sum(map(Fraction.from_float,weights),Fraction(0))
        flows=[]
        for w in weights:
            flow=float(Fraction.from_float(g)*Fraction.from_float(w)/denominator)if denominator else 0.
            _normal(flow);_need(not(g>0 and w>0)or flow>0,'NUMERIC_HOLD: positive leaf inflow lost');flows.append(flow)
        effective=g if denominator else 0.;deferred=g-effective
        requested_resp=_normal(c*g);realized_resp=_normal(c*effective);avoided_resp=_normal(c*deferred)
        _need(g==0 or requested_resp>0,'NUMERIC_HOLD: positive growth cost lost')
        refund=_normal(fsum((deferred,avoided_resp)));adjustments={'buffer':refund,'leaf':-deferred if deferred else 0.,
            'growth_respiration':-avoided_resp if avoided_resp else 0.}
        residuals={'allocation':fsum((*flows,-effective)),'request':fsum((effective,deferred,-g)),
            'respiration':fsum((realized_resp,avoided_resp,-requested_resp)),
            'refund':fsum((refund,-deferred,-avoided_resp)),'adjustments':fsum(adjustments.values()),
            'whole_leaf_budget':fsum((-g,-requested_resp,refund,*flows,realized_resp))}
        scale=max(g,requested_resp,refund,realized_resp,*flows)
        budget=64*(len(rows)+8)*ulp(scale)if scale else 0.
        _need(isfinite(budget)and all(isfinite(x)and abs(x)<=budget for x in residuals.values()),'BALANCE_HOLD: partition budget unresolved')
        normalized={'input_id':v['input_id'],'origin':v['origin'],'policy':POLICY_ID,'requested_leaf_growth':_q(g),
            'leaves':[{'leaf_id':i,'sink_weight':_q(w,'1')}for i,w in zip(ids,weights,strict=True)]}
        result={'model_version':MODEL_VERSION,'code_sha256':CODE_SHA256,'source_code_sha256':SOURCE_SHA256,
            'profile_sha256':growth_profile.sha256,'policy_id':POLICY_ID,'policy_sha256':POLICY_SHA256,'inputs':normalized,
            'raw_input_sha256':sha256(raw).hexdigest(),'input_sha256':sha256(_canonical(normalized)).hexdigest(),
            'scope':'software_research_only','claim_scope':'synthetic_leaf_carbon_partition_math_only','G0_G4':'not_assessed',
            'requested_leaf_growth':_q(g),'effective_leaf_growth':_q(effective),'deferred_leaf_growth':_q(deferred),
            'sink_weight_sum':_q(total,'1'),'growth_respiration_coefficient':_q(c,'1'),
            'allocation':[{'leaf_id':i,'carbohydrate_inflow':_q(f)}for i,f in zip(ids,flows,strict=True)],
            'growth_respiration':{k:_q(x)for k,x in (('requested',requested_resp),('realized',realized_resp),('avoided',avoided_resp))},
            'derivative_adjustments':{k:_q(x)for k,x in adjustments.items()},
            'balance_residuals':{k:_q(x)for k,x in residuals.items()},'balance_budgets':{k:_q(budget)for k in residuals}}
        result['calculation_sha256']=sha256(_canonical(result)).hexdigest();_canonical(result);_fence();return result
    except LeafCarbonPartitionHold:raise
    except(OverflowError,ValueError,TypeError,KeyError,AttributeError,OSError,RecursionError,ZeroDivisionError):
        raise LeafCarbonPartitionHold('INPUT_HOLD: invalid or unrepresentable leaf partition')from None
