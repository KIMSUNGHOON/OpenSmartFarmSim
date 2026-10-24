"""Authoritative leaf stocks; crop-leaf-carbon-stock-rhs-v1.md."""
from copy import deepcopy
from fractions import Fraction
from hashlib import sha256
import json
from math import fsum,isfinite,ulp
from pathlib import Path
from sys import modules

from . import crop_leaf_partition_climate_rhs as source

part=source.partition
MODEL_VERSION='individual-leaf-carbon-stock-joint-rhs-research-v1'
POLICY_ID='leaf-stocks-uniform-maintenance-explicit-removal-v1'
POLICY={'id':POLICY_ID,'stock':'mg_CH2O/m2_floor_each_same_footprint','aggregate':'once_rounded_exact_sum_only',
    'maintenance':'original_total_proportional_to_current_stock','removal':'explicit_each_leaf',
    'growth_partition_policy':part.POLICY_ID,'zero_stock':'reject_outward_final_derivative_no_clipping'}
POLICY_SHA256=sha256(json.dumps(POLICY,sort_keys=True,separators=(',',':')).encode()).hexdigest()
MAX_BYTES=512*1024
CODE_SHA256=sha256(Path(__file__).read_bytes()).hexdigest()
COMPONENT_CODE_SHA256={**source.COMPONENT_CODE_SHA256,source.__name__:sha256(Path(source.__file__).read_bytes()).hexdigest()}


class LeafCarbonStockHold(ValueError):
    pass


def _need(condition,reason):
    if not condition:raise LeafCarbonStockHold(reason)


def _canonical(v):
    raw=json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
    _need(len(raw)<=MAX_BYTES,'CAPACITY_HOLD: 512KiB individual stock input/output required');return raw


def _sum(values):return part._normal(float(sum((Fraction.from_float(v)for v in values),Fraction(0))))


def _fence():
    expected={**COMPONENT_CODE_SHA256,__name__:CODE_SHA256}
    _need(all(sha256(Path(modules[name].__file__).read_bytes()).hexdigest()==h for name,h in expected.items()),
        'CODE_HOLD: original stock and joint sources required')


def evaluate_rhs(*,scenario,leaf_stocks,growth_profile,cohort_profile,transport_profile,exchange_profile):
    try:
        _fence();part._closed(leaf_stocks,{'input_id','origin','policy','model_floor_area','leaf_ids','leaves'})
        _need(type(leaf_stocks['leaf_ids'])is list and type(leaf_stocks['leaves'])is list,'INPUT_HOLD: explicit stock lists required')
        raw=_canonical({'scenario':scenario,'leaf_stocks':leaf_stocks});captured=json.loads(raw);s=captured['scenario'];l=captured['leaf_stocks']
        _need(type(s)is dict,'INPUT_HOLD: declared scenario required')
        part._closed(s['plant_state'],set(source.source.carbon.original.PLANT_UNITS)-{'leaf'})
        part._closed(s['removals'],set(source.source.carbon.original.REMOVAL_UNITS)-{'leaf'})
        _need(l['input_id']==s.get('input_id')and l['origin']=='synthetic'and l['policy']==POLICY_ID,
            'SCOPE_HOLD: one explicit synthetic stock stage required');part._id(l['input_id'])
        floor=part._number(l['model_floor_area'],'m2_floor')
        _need(floor>0 and part._q(floor,'m2_floor')==s['geometry']['model_floor_area'],'BASIS_HOLD: same positive model footprint required')
        ids=l['leaf_ids'];_need(1<=len(ids)<=512,'CAPACITY_HOLD: 1..512 original stock IDs required')
        for identifier in ids:part._id(identifier)
        _need(len(set(ids))==len(ids),'INPUT_HOLD: unique original stock IDs required')
        rows=[]
        for row in l['leaves']:
            part._closed(row,{'leaf_id','carbon','sink_weight','removal'});part._id(row['leaf_id'])
            rows.append({'leaf_id':row['leaf_id'],**{k:part._q(part._number(row[k],unit),unit)for k,unit in(
                ('carbon',part.source.MASS_UNIT),('sink_weight','1'),('removal',part.source.RATE_UNIT))}})
        _need([x['leaf_id']for x in rows]==ids,'STATE_MISMATCH_HOLD: complete ordered stock IDs required')
        carbon=[x['carbon']['value']for x in rows];exact=sum(map(Fraction.from_float,carbon),Fraction(0));total_C=_sum(carbon)
        _need(total_C>0,'STATE_HOLD: positive aggregate leaf carbon required');total_R=_sum(x['removal']['value']for x in rows)
        assembled=deepcopy(s);assembled['plant_state']['leaf']=part._q(total_C,part.source.MASS_UNIT);assembled['removals']['leaf']=part._q(total_R)
        stage=source.evaluate_rhs(scenario=assembled,leaf_stage={'input_id':l['input_id'],'origin':'synthetic','policy':part.POLICY_ID,
            'leaf_ids':ids,'sinks':[{k:deepcopy(x[k])for k in('leaf_id','sink_weight')}for x in rows]},
            growth_profile=growth_profile,cohort_profile=cohort_profile,transport_profile=transport_profile,exchange_profile=exchange_profile)
        _need(stage['code_sha256']==COMPONENT_CODE_SHA256[source.__name__]
            and stage['calculation_sha256']==sha256(source._canonical({k:v for k,v in stage.items()if k!='calculation_sha256'})).hexdigest(),
            'SOURCE_HOLD: original stock-assembled stage result and hash required')
        crop=stage['source_joint']['crop'];M=crop['vegetative_maintenance']['leaf']['value'];_need(M>0,'NUMERIC_HOLD: positive aggregate maintenance lost')
        rates=[]
        for row,c,inflow in zip(rows,carbon,stage['leaf_partition']['allocation'],strict=True):
            _need(row['leaf_id']==inflow['leaf_id'],'SOURCE_HOLD: original allocation order required')
            maintenance=part._normal(float(Fraction.from_float(M)*Fraction.from_float(c)/exact))
            _need(c==0 or maintenance>0,'NUMERIC_HOLD: positive individual maintenance lost')
            derivative=part._normal(fsum((inflow['carbohydrate_inflow']['value'],-maintenance,-row['removal']['value'])))
            _need(c!=0 or derivative>=0,'DEPLETED_STATE_HOLD: outward derivative at zero individual stock')
            rates.append({'leaf_id':row['leaf_id'],'inflow':deepcopy(inflow['carbohydrate_inflow']),'maintenance':part._q(maintenance),
                'removal':deepcopy(row['removal']),'derivative':part._q(derivative)})
        totals={name:_sum(x[name]['value']for x in rates)for name in('inflow','maintenance','removal','derivative')}
        plant=deepcopy(stage['derivatives']['plant']);plant['leaf']=part._q(totals['derivative'])
        targets={'inflow':stage['adjusted_carbon']['allocation']['leaf']['value'],'maintenance':M,'removal':total_R,
            'derivative':stage['derivatives']['plant']['leaf']['value']}
        aggregation={k:fsum((totals[k],-targets[k]))for k in totals}
        scale=max(1.,*map(abs,targets.values()),*(abs(x[k]['value'])for x in rates for k in totals))
        roundoff=64*(len(rows)+8)*ulp(scale)
        _need(isfinite(roundoff)and all(abs(v)<=roundoff for v in aggregation.values()),'BALANCE_HOLD: unresolved individual aggregation')
        terms=[*(plant[k]['value']for k in('buffer','leaf','stem_root')),
            *(x['value']for x in stage['derivatives']['cohorts']['fruit_carbohydrate']),stage['adjusted_carbon']['growth_respiration']['value'],
            totals['maintenance'],crop['vegetative_maintenance']['stem_root']['value'],crop['fruit_maintenance']['value'],
            totals['removal'],crop['removals']['stem_root']['value'],crop['cohorts']['terminal_outflow']['fruit_carbohydrate']['value'],-crop['photosynthesis']['value']]
        residuals={'carbohydrate':fsum(terms),'leaf_compartment':fsum((totals['derivative'],totals['maintenance'],totals['removal'],-totals['inflow']))}
        budgets={'carbohydrate':fsum((stage['balance_budgets']['carbohydrate']['value'],roundoff,64*ulp(max(1.,*map(abs,terms))))),
            'leaf_compartment':roundoff}
        _need(all(isfinite(v)for v in(*residuals.values(),*budgets.values()))and all(abs(v)<=budgets[k]for k,v in residuals.items()),
            'BALANCE_HOLD: unresolved individual/whole carbon ledger')
        normalized=deepcopy(stage['inputs']['scenario']);normalized['plant_state'].pop('leaf');normalized['removals'].pop('leaf')
        identity={'model_version':MODEL_VERSION,'code_sha256':CODE_SHA256,'component_code_sha256':dict(COMPONENT_CODE_SHA256),
            'profile_sha256':dict(stage['profile_sha256']),'policy_id':POLICY_ID,'policy_sha256':POLICY_SHA256,
            'inputs':{'scenario':normalized,'leaf_stocks':{**l,'model_floor_area':part._q(floor,'m2_floor'),'leaves':deepcopy(rows)}},
            'source_stage_calculation_sha256':stage['calculation_sha256']}
        result={**identity,'raw_input_sha256':sha256(raw).hexdigest(),'input_sha256':sha256(_canonical(identity)).hexdigest(),
            'scope':'software_research_only','claim_scope':'synthetic_individual_leaf_carbon_rhs_only','G0_G4':'not_assessed',
            'time_coordinate':'derivatives_per_second_no_time_advance','aggregate_leaf_derivative_use':'derived_diagnostic_not_independent_state',
            'source_stage':deepcopy(stage),'leaf_rates':rates,'leaf_totals':{'carbon':part._q(total_C,part.source.MASS_UNIT),**{k:part._q(v)for k,v in totals.items()}},
            'derivatives':{'plant':plant,'cohorts':deepcopy(stage['derivatives']['cohorts']),'climate':deepcopy(stage['derivatives']['climate'])},
            'aggregation_residuals':{k:part._q(v)for k,v in aggregation.items()},'aggregation_budgets':{k:part._q(roundoff)for k in aggregation},
            'balance_residuals':{**deepcopy(stage['balance_residuals']),**{k:part._q(v)for k,v in residuals.items()}},
            'balance_budgets':{**deepcopy(stage['balance_budgets']),**{k:part._q(v)for k,v in budgets.items()}}}
        result['calculation_sha256']=sha256(_canonical(result)).hexdigest();_canonical(result);_fence();return result
    except LeafCarbonStockHold:raise
    except(source.LeafPartitionClimateHold,part.LeafCarbonPartitionHold)as exc:raise LeafCarbonStockHold(str(exc))from None
    except(ValueError,TypeError,KeyError,AttributeError,OSError,OverflowError,RecursionError,ZeroDivisionError):
        raise LeafCarbonStockHold('INPUT_HOLD: invalid or unrepresentable individual leaf stock stage')from None
