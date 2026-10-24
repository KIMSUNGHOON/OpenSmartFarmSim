"""Bounded instantaneous removal; growing-geometry-leaf-removal-point-v1.md."""
from copy import deepcopy
from fractions import Fraction
from hashlib import sha256
import json
from math import isfinite, ulp
from pathlib import Path
from sys import float_info

from . import crop_growing_geometry_continuation as resume
from .crop_rational_morphology_clock import _seconds, RationalMorphologyClockHold

VERSION='growing-geometry-leaf-removal-point-research-v1'
CODE_SHA256=sha256(Path(__file__).read_bytes()).hexdigest()
FIELDS={'schema_version','input_id','origin','context_sha256','checkpoint_sha256',
    'at_elapsed_seconds_exact','mass_basis','events'}
numeric=resume.short.numeric


class LeafRemovalPointHold(ValueError):
    pass


def _need(condition,reason):
    if not condition:raise LeafRemovalPointHold(reason)


def _canonical(value):
    raw=json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
    _need(len(raw)<=2*1024**2,'CAPACITY_HOLD: 2MiB point input/output required')
    return raw


def _closed(value,keys):
    _need(type(value)is dict and set(value)==set(keys),'INPUT_HOLD: closed point fields required')


def _identifier(value):resume.short.leaf_area._identifier(value)


def _quantity(value,unit,positive=False):
    _closed(value,{'value','unit'});_need(value['unit']==unit,'UNIT_HOLD: '+unit+' required')
    _need(type(value['value'])in(int,float),'INPUT_HOLD: explicit number required')
    v=float(value['value']);_need(isfinite(v)and(v==0 or abs(v)>=float_info.min),'NUMERIC_HOLD: normal finite quantity required')
    _need(not positive or v>0,'INPUT_HOLD: positive quantity required');return v


def _per_floor(values,floor):
    exact=sum((Fraction.from_float(v)for v in values),Fraction(0))/Fraction.from_float(floor)
    value=float(exact)
    _need(isfinite(value)and(exact==0 or abs(value)>=float_info.min),'NUMERIC_HOLD: floor quantity unrepresentable')
    return value


def _balance(terms,unit):
    residual=numeric._sum(*terms);budget=64*ulp(max(map(abs,terms)))
    _need(isfinite(budget)and abs(residual)<=budget,'BALANCE_HOLD: declared point '+unit)
    return {'residual':numeric._q(residual,unit),'budget':numeric._q(budget,unit)}


def apply_removals(*,context,raw_checkpoint,expected_sha256,inputs):
    try:
        _closed(inputs,FIELDS);raw=_canonical(inputs);v=json.loads(raw);_identifier(v['input_id'])
        _need(v['schema_version']=='growing-geometry-leaf-removal-point-input-v1'and v['origin']=='synthetic',
            'SCOPE_HOLD: explicit synthetic point required')
        cp=resume.restore_checkpoint(context,raw_checkpoint,expected_sha256=expected_sha256)
        _need(v['context_sha256']==context.root_sha256 and v['checkpoint_sha256']==cp.sha256,
            'HASH_HOLD: original point context/checkpoint required')
        p,seed,m=resume._context(context);saved=cp.value;y=saved['last_confirmed']['state'];n=len(p['leaves'])
        at=Fraction.from_float(m['numerical']['step_seconds'])*saved['step_index']
        _need(_seconds(v['at_elapsed_seconds_exact'])==at,'TIME_HOLD: original exact elapsed coordinate required')
        _need(p['scenario']['removals']['leaf']['value']==0 and p['capacity_outflow']['value']==0,
            'DUPLICATE_REMOVAL_HOLD: current continuous leaf/capacity outflow needs attribution')
        basis=v['mass_basis'];_closed(basis,{'origin','evidence_level','evidence_id','model_floor_area','leaves'})
        _need(basis['origin']=='synthetic'and basis['evidence_level']=='assumed','SCOPE_HOLD: declared assumed current mass distribution required')
        _identifier(basis['evidence_id']);floor=_quantity(basis['model_floor_area'],'m2_floor',True)
        _need(floor==p['model_floor_area']['value'],'BASIS_HOLD: original footprint required')
        records=basis['leaves'];_need(type(records)is list and len(records)==n,'MASS_HOLD: complete current leaf distribution required')
        masses={};positions={leaf['leaf_id']:i for i,leaf in enumerate(p['leaves'])}
        for leaf,record in zip(p['leaves'],records,strict=True):
            _closed(record,{'leaf_id','carbohydrate'})
            _need(record['leaf_id']==leaf['leaf_id'],'MASS_HOLD: original complete leaf order required')
            masses[leaf['leaf_id']]=_quantity(record['carbohydrate'],'mg_CH2O',True)
        _need(_per_floor(masses.values(),floor)==y[1],'MASS_HOLD: declared current masses differ from stock')
        events=v['events'];_need(type(events)is list and 1<=len(events)<=512,'EVENT_HOLD: nonempty bounded batch required')
        _need(len(events)<n,'EMPTY_CANOPY_HOLD: positive remaining canopy required')
        k=p['scenario']['parameters']['leaf_heat_capacity']['value'];ref=p['scenario']['parameters']['reference_temperature']['value']
        tc=saved['last_confirmed']['derived']['canopy_temperature']['value'];removed=set();event_ids=set();checks=[]
        for event in events:
            _closed(event,{'event_id','leaf_id','carbohydrate','capacity','sensible_energy','outgoing_temperature'})
            _identifier(event['event_id']);_identifier(event['leaf_id']);leaf_id=event['leaf_id']
            _need(leaf_id in positions and leaf_id not in removed and event['event_id']not in event_ids,
                'EVENT_HOLD: missing or repeated leaf/event')
            mass=_quantity(event['carbohydrate'],'mg_CH2O',True)
            _need(mass==masses[leaf_id],'MASS_HOLD: removal differs from current leaf distribution')
            cap=_quantity(event['capacity'],numeric.CAPACITY,True);energy=_quantity(event['sensible_energy'],numeric.ENERGY)
            outgoing=_quantity(event['outgoing_temperature'],'degC')
            _need(outgoing==tc,'TEMPERATURE_HOLD: explicitly well-mixed outgoing temperature required')
            expected_cap=numeric._multiply(k,numeric._divide(y[108+n+positions[leaf_id]],floor))
            expected_energy=numeric._multiply(cap,numeric._sum(outgoing,-ref))
            checks.append({'event_id':event['event_id'],'capacity':_balance((cap,-expected_cap),numeric.CAPACITY),
                'energy':_balance((energy,-expected_energy),numeric.ENERGY)})
            removed.add(leaf_id);event_ids.add(event['event_id'])
        active=[i for i,leaf in enumerate(p['leaves'])if leaf['leaf_id']not in removed]
        carbon_out=_per_floor((masses[e['leaf_id']]for e in events),floor)
        capacity_out=numeric._sum(*(e['capacity']['value']for e in events))
        energy_out=numeric._sum(*(e['sensible_energy']['value']for e in events))
        stock=numeric._sum(y[1],-carbon_out);energy=numeric._sum(y[105],-energy_out)
        _need(stock>0,'DEPLETED_STATE_HOLD: positive remaining leaf stock required')
        lai=numeric._divide(numeric._sum(*(y[108+n+i]for i in active)),floor)
        capacity=numeric._multiply(k,lai);new_tc=numeric._sum(ref,numeric._divide(energy,capacity))
        numeric._temperature(new_tc)
        _need(abs(numeric._sum(new_tc,-tc))<=numeric.TEMPERATURE_TOLERANCE,'TEMPERATURE_HOLD: unresolved instantaneous temperature')
        remaining_carbon=_per_floor((masses[p['leaves'][i]['leaf_id']]for i in active),floor)
        old_cap=saved['last_confirmed']['derived']['canopy_capacity']['value']
        balances={'carbon':_balance((stock,-y[1],carbon_out),numeric.MASS),
            'remaining_mass':_balance((stock,-remaining_carbon),numeric.MASS),
            'capacity':_balance((capacity,-old_cap,capacity_out),numeric.CAPACITY),
            'sensible_energy':_balance((energy,-y[105],energy_out),numeric.ENERGY)}
        after=[*y[:108],*(y[108+i]for i in active),*(y[108+n+i]for i in active)];after[1]=stock;after[105]=energy
        q=numeric._q
        result={'model_version':VERSION,'code_sha256':CODE_SHA256,'input_sha256':sha256(raw).hexdigest(),
            'context_sha256':context.root_sha256,'checkpoint_sha256':cp.sha256,'parent_identity':deepcopy(m['identity']),
            'original_program_sha256':m['program_sha256'],'original_seed_sha256':m['seed_sha256'],
            'inputs':v,'at_elapsed_seconds_exact':deepcopy(v['at_elapsed_seconds_exact']),
            'time_coordinate':'same_elapsed_instant_no_UTC_no_advance','before':deepcopy(saved['last_confirmed']),
            'after':{'state':after,'leaf_ids':[p['leaves'][i]['leaf_id']for i in active],
                'leaf_area_index':q(lai,'m2_leaf/m2_floor'),'capacity':q(capacity,numeric.CAPACITY),
                'canopy_temperature':q(new_tc,'degC'),'original_leaf_indices':active},
            'removed_last_states':[{'leaf_id':e['leaf_id'],'thermal_age':q(y[108+positions[e['leaf_id']]],'degC_day'),
                'area':q(y[108+n+positions[e['leaf_id']]],'m2')}for e in events],
            'original_curve_invariant':deepcopy(seed['evaluation']['curve_residuals']),
            'original_initial_area_receipts':deepcopy(seed['initial_area_receipts']),
            'original_interval_transfers':deepcopy(saved['integrated_transfers']),
            'point_outflows':{'carbohydrate':q(carbon_out,numeric.MASS),'capacity':q(capacity_out,numeric.CAPACITY),
                'sensible_energy':q(energy_out,numeric.ENERGY)},'event_balances':checks,'balances':balances,
            'continuation_checkpoint':False,'scope':'software_research_only',
            'claim_scope':'synthetic_independent_area_leaf_removal_point_only','G0_G4':'not_assessed'}
        result['calculation_sha256']=sha256(_canonical(result)).hexdigest();_canonical(result);return result
    except LeafRemovalPointHold:raise
    except(ValueError,TypeError,KeyError,AttributeError,OverflowError,ZeroDivisionError,RecursionError)as error:
        known=(resume.ContinuationRejected,resume.short.GrowingGeometryHold,numeric.CanopyEnergyHold,
            resume.short.leaf_area.LeafAreaHold,RationalMorphologyClockHold)
        raise LeafRemovalPointHold(str(error)if isinstance(error,known)else'INPUT_HOLD: invalid removal point')from None
