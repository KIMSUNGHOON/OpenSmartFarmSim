"""Same-stage carbon adjustments; crop-leaf-partition-climate-rhs-v1.md."""
from copy import deepcopy
from hashlib import sha256
import json
from math import fsum,isfinite,ulp
from pathlib import Path

from . import crop_explicit_lai_climate_rhs as source
from . import crop_leaf_carbon_partition as partition

MODEL_VERSION='leaf-partition-crop-climate-stage-research-v1'
MAX_BYTES=256*1024
CODE_SHA256=sha256(Path(__file__).read_bytes()).hexdigest()
COMPONENT_CODE_SHA256={**source.COMPONENT_CODE_SHA256,
    **{m.__name__:sha256(Path(m.__file__).read_bytes()).hexdigest()for m in(source,partition)}}


class LeafPartitionClimateHold(ValueError):
    pass


def _need(condition,reason):
    if not condition:raise LeafPartitionClimateHold(reason)


def _canonical(v):
    raw=json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
    _need(len(raw)<=MAX_BYTES,'CAPACITY_HOLD: 256KiB joint partition input/output required');return raw


def _fence():
    modules={**{name:__import__(name,fromlist=[''])for name in COMPONENT_CODE_SHA256},__name__:__import__(__name__,fromlist=[''])}
    expected={**COMPONENT_CODE_SHA256,__name__:CODE_SHA256}
    _need(all(sha256(Path(m.__file__).read_bytes()).hexdigest()==expected[name]for name,m in modules.items()),
        'CODE_HOLD: original joint/partition sources required')


def evaluate_rhs(*,scenario,leaf_stage,growth_profile,cohort_profile,transport_profile,exchange_profile):
    try:
        _fence();partition._closed(leaf_stage,{'input_id','origin','policy','leaf_ids','sinks'})
        _need(type(leaf_stage['leaf_ids'])is list and type(leaf_stage['sinks'])is list,'INPUT_HOLD: declared stage lists required')
        raw=_canonical({'scenario':scenario,'leaf_stage':leaf_stage});captured=json.loads(raw);s=captured['scenario'];l=captured['leaf_stage']
        _need(type(s)is dict and l['input_id']==s.get('input_id')and l['origin']=='synthetic'
            and l['policy']==partition.POLICY_ID,'SCOPE_HOLD: one explicit synthetic stage/policy required')
        partition._id(l['input_id']);ids=l['leaf_ids'];rows=l['sinks']
        _need(1<=len(ids)<=512,'CAPACITY_HOLD: 1..512 original stage leaf IDs required')
        for identifier in ids:partition._id(identifier)
        _need(len(set(ids))==len(ids),'INPUT_HOLD: unique original stage IDs required')
        normalized=[]
        for row in rows:
            partition._closed(row,{'leaf_id','sink_weight'});partition._id(row['leaf_id'])
            normalized.append({'leaf_id':row['leaf_id'],'sink_weight':partition._q(partition._number(row['sink_weight'],'1'),'1')})
        _need([x['leaf_id']for x in normalized]==ids,'STATE_MISMATCH_HOLD: complete original ordered sink IDs required')
        l={**l,'sinks':normalized}
        original=source.evaluate_rhs(scenario=s,growth_profile=growth_profile,cohort_profile=cohort_profile,
            transport_profile=transport_profile,exchange_profile=exchange_profile)
        _need(original['code_sha256']==COMPONENT_CODE_SHA256[source.__name__]
            and original['raw_input_sha256']==sha256(source._canonical(s)).hexdigest()
            and original['calculation_sha256']==sha256(source._canonical({k:v for k,v in original.items()if k!='calculation_sha256'})).hexdigest(),
            'SOURCE_HOLD: original same-stage result and hash required')
        crop=original['crop'];allocated=partition.calculate_partition(inputs={'input_id':l['input_id'],'origin':'synthetic',
            'policy':l['policy'],'requested_leaf_growth':crop['allocation']['leaf'],'leaves':normalized},growth_profile=growth_profile)
        _need(allocated['code_sha256']==COMPONENT_CODE_SHA256[partition.__name__]
            and allocated['inputs']['requested_leaf_growth']==crop['allocation']['leaf']and allocated['inputs']['leaves']==normalized
            and allocated['profile_sha256']==original['profile_sha256']['growth']
            and allocated['calculation_sha256']==sha256(partition._canonical({k:v for k,v in allocated.items()if k!='calculation_sha256'})).hexdigest(),
            'SOURCE_HOLD: original allocation result and hash required')
        adjustments=allocated['derivative_adjustments'];plant=deepcopy(original['derivatives']['plant']);q=partition._q
        for name in('buffer','leaf'):plant[name]=q(fsum((plant[name]['value'],adjustments[name]['value'])))
        growth=fsum((crop['growth_respiration']['value'],adjustments['growth_respiration']['value']))
        _need(isfinite(growth)and growth>=0 and all(isfinite(v['value'])for v in plant.values()),
            'NUMERIC_HOLD: invalid adjusted carbon derivative or growth cost')
        cohorts=original['derivatives']['cohorts'];terms=[*(plant[k]['value']for k in('buffer','leaf','stem_root')),
            *(v['value']for v in cohorts['fruit_carbohydrate']),growth,
            *(v['value']for v in crop['vegetative_maintenance'].values()),crop['fruit_maintenance']['value'],
            *(v['value']for v in crop['removals'].values()),crop['cohorts']['terminal_outflow']['fruit_carbohydrate']['value'],
            -crop['photosynthesis']['value']]
        leaf_terms=[plant['leaf']['value'],crop['vegetative_maintenance']['leaf']['value'],crop['removals']['leaf']['value'],
            *(-v['carbohydrate_inflow']['value']for v in allocated['allocation'])]
        residuals={'carbohydrate':fsum(terms),'leaf_compartment':fsum(leaf_terms)}
        budgets={'carbohydrate':fsum((original['balance_budgets']['carbohydrate']['value'],
            allocated['balance_budgets']['whole_leaf_budget']['value'],64*ulp(max(1.,*map(abs,terms))))),
            'leaf_compartment':fsum((allocated['balance_budgets']['allocation']['value'],64*ulp(max(1.,*map(abs,leaf_terms)))))}
        _need(all(isfinite(x)for x in(*residuals.values(),*budgets.values()))and all(abs(v)<=budgets[k]for k,v in residuals.items()),
            'BALANCE_HOLD: unresolved adjusted carbon or leaf ledger')
        balances={**deepcopy(original['balance_residuals']),**{k:q(v)for k,v in residuals.items()}}
        bounds={**deepcopy(original['balance_budgets']),**{k:q(v)for k,v in budgets.items()}}
        identity={'model_version':MODEL_VERSION,'code_sha256':CODE_SHA256,'component_code_sha256':dict(COMPONENT_CODE_SHA256),
            'profile_sha256':dict(original['profile_sha256']),'policy_id':partition.POLICY_ID,'policy_sha256':partition.POLICY_SHA256,
            'inputs':{'scenario':deepcopy(original['scenario']),'leaf_stage':deepcopy(l)},
            'source_joint_calculation_sha256':original['calculation_sha256'],'partition_calculation_sha256':allocated['calculation_sha256']}
        result={**identity,'raw_input_sha256':sha256(raw).hexdigest(),'input_sha256':sha256(_canonical(identity)).hexdigest(),
            'scope':'software_research_only','claim_scope':'synthetic_leaf_partition_joint_rhs_only','G0_G4':'not_assessed',
            'time_coordinate':'derivatives_per_second_no_time_advance','source_joint':deepcopy(original),'leaf_partition':deepcopy(allocated),
            'adjusted_carbon':{'requested_allocation':deepcopy(crop['requested_allocation']),
                'allocation':{**deepcopy(crop['allocation']),'leaf':deepcopy(allocated['effective_leaf_growth'])},
                'growth_respiration':q(growth),'derivatives':deepcopy(plant)},
            'derivatives':{'plant':plant,'cohorts':deepcopy(cohorts),'climate':deepcopy(original['derivatives']['climate'])},
            'balance_residuals':balances,'balance_budgets':bounds}
        result['calculation_sha256']=sha256(_canonical(result)).hexdigest();_canonical(result);_fence();return result
    except LeafPartitionClimateHold:raise
    except(source.ExplicitLaiClimateHold,partition.LeafCarbonPartitionHold)as exc:raise LeafPartitionClimateHold(str(exc))from None
    except(ValueError,TypeError,OverflowError,KeyError,AttributeError,OSError,RecursionError,ZeroDivisionError):
        raise LeafPartitionClimateHold('INPUT_HOLD: invalid or unrepresentable partition joint stage')from None
