"""Explicit represented area/capacity accounting; crop-area-canopy-energy-v1.md."""
from copy import deepcopy
from hashlib import sha256
import json
from math import isfinite, ulp
from pathlib import Path
import re

from . import crop_canopy_energy_transport as numeric

MODEL_VERSION='explicit-area-canopy-capacity-energy-research-v1'
CODE_SHA256=sha256(Path(__file__).read_bytes()).hexdigest()
NUMERIC_CODE_SHA256=sha256(Path(numeric.__file__).read_bytes()).hexdigest()
UNITS={'leaf_area_index':'m2_leaf/m2_floor','leaf_area_index_rate':'m2_leaf/m2_floor/s',
       'leaf_heat_capacity':'J/m2_leaf/K','capacity_inflow':numeric.CAPACITY_RATE,'capacity_outflow':numeric.CAPACITY_RATE,
       **dict.fromkeys(('canopy_temperature','incoming_capacity_temperature','outgoing_capacity_temperature',
                       'reference_temperature'),'degC'),'nonmaterial_heat':numeric.POWER}


class AreaCanopyEnergyHold(ValueError):
    pass


def _need(condition,reason):
    if not condition:raise AreaCanopyEnergyHold(reason)


def _canonical(value):
    raw=json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
    _need(len(raw)<=128*1024,'CAPACITY_HOLD: bounded area-energy input/output required')
    return raw


def calculate_area_energy(*,inputs):
    try:
        raw=_canonical(inputs);captured=json.loads(raw)
        _need(type(captured)is dict and set(captured)=={'input_id','origin','values'},'INPUT_HOLD: closed area-energy input required')
        _need(type(captured['input_id'])is str and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.:/-]{0,199}',captured['input_id'])
              and captured['origin']=='synthetic','SCOPE_HOLD: bounded explicit synthetic area-energy input required')
        block=captured['values'];_need(type(block)is dict and set(block)==set(UNITS),'INPUT_HOLD: all explicit flux/temperature quantities required')
        v={}
        for name,unit in UNITS.items():
            row=block[name];_need(type(row)is dict and set(row)=={'value','unit'},'INPUT_HOLD: closed quantity required')
            _need(row['unit']==unit,'UNIT_HOLD: '+name)
            _need(type(row['value'])in(int,float),'INPUT_HOLD: numeric quantity required')
            value=float(row['value']);_need(isfinite(value),'NUMERIC_HOLD: finite quantity required');v[name]=value
        _need(v['leaf_area_index']>0 and v['leaf_heat_capacity']>0,'EMPTY_CANOPY_HOLD: positive area and capacity required')
        _need(v['capacity_inflow']>=0 and v['capacity_outflow']>=0,'INPUT_HOLD: nonnegative gross capacity fluxes required')
        tc,tin,tout=(numeric._temperature(v[name])for name in ('canopy_temperature','incoming_capacity_temperature','outgoing_capacity_temperature'))
        ref=v['reference_temperature'];offset=numeric._offset(tc,ref)
        capacity=numeric._multiply(v['leaf_heat_capacity'],v['leaf_area_index'])
        geometric=numeric._multiply(v['leaf_heat_capacity'],v['leaf_area_index_rate'])
        gin,gout=v['capacity_inflow'],v['capacity_outflow'];transport=numeric._sum(gin,-gout)
        capacity_residual=numeric._sum(geometric,-transport)
        capacity_budget=8*ulp(max(abs(geometric),abs(transport)))
        _need(isfinite(capacity_budget)and abs(capacity_residual)<=capacity_budget,
              'CAPACITY_BALANCE_HOLD: explicit net geometry and gross capacity transport differ')
        energy=numeric._multiply(capacity,offset)
        restored=numeric._sum(ref,numeric._divide(energy,capacity))
        _need(abs(numeric._sum(restored,-tc))<=numeric.TEMPERATURE_TOLERANCE,'NUMERIC_HOLD: energy reference roundtrip resolution')
        incoming=numeric._multiply(gin,numeric._offset(tin,ref));outgoing=numeric._multiply(gout,numeric._offset(tout,ref))
        material=numeric._sum(incoming,-outgoing);heat=v['nonmaterial_heat'];total=numeric._sum(heat,material)
        centered=numeric._sum(heat,numeric._multiply(gin,numeric._offset(tin,tc)),
                              -numeric._multiply(gout,numeric._offset(tout,tc)))
        temperature_rate=numeric._divide(centered,capacity)
        temperature_part=numeric._multiply(capacity,temperature_rate);capacity_part=numeric._multiply(offset,geometric)
        chain=numeric._sum(temperature_part,capacity_part);energy_residual=numeric._sum(chain,-total)
        energy_budget=64*ulp(max(map(abs,(temperature_part,capacity_part,incoming,outgoing,heat,total))))
        _need(isfinite(energy_budget)and abs(energy_residual)<=energy_budget,'ENERGY_BALANCE_HOLD: chain rule and energy ledger differ')
        q=numeric._q;normalized={**captured,'values':{name:q(v[name],unit)for name,unit in UNITS.items()}}
        identity={'model_version':MODEL_VERSION,'code_sha256':CODE_SHA256,'numeric_component_sha256':NUMERIC_CODE_SHA256,
                  'policy_id':'explicit-area-gross-capacity-transport-v1','inputs':normalized}
        result={**identity,'input_sha256':sha256(_canonical(identity)).hexdigest(),'raw_input_sha256':sha256(raw).hexdigest(),
            'leaf_area_index':deepcopy(normalized['values']['leaf_area_index']),
            'leaf_area_index_rate':deepcopy(normalized['values']['leaf_area_index_rate']),
            'canopy_capacity':q(capacity,numeric.CAPACITY),'canopy_sensible_energy':q(energy,numeric.ENERGY),
            'capacity_rates':{name:q(value,numeric.CAPACITY_RATE)for name,value in
                [('geometry',geometric),('transport',transport),('incoming',gin),('outgoing',gout)]},
            'energy_flows':{name:q(value,numeric.POWER)for name,value in
                [('incoming',incoming),('outgoing',outgoing),('material',material),('nonmaterial',heat),('total',total)]},
            'canopy_temperature_rate':q(temperature_rate,'K/s'),
            'chain_rule':{name:q(value,numeric.POWER)for name,value in [('temperature_part',temperature_part),('capacity_part',capacity_part),('total',chain)]},
            'balance_residuals':{'capacity_rate':q(capacity_residual,numeric.CAPACITY_RATE),'energy':q(energy_residual,numeric.POWER)},
            'balance_budgets':{'capacity_rate':q(capacity_budget,numeric.CAPACITY_RATE),'energy':q(energy_budget,numeric.POWER)},
            'scope':'software_research_only','claim_scope':'synthetic_area_capacity_bookkeeping_only','G0_G4':'not_assessed'}
        result['calculation_sha256']=sha256(_canonical(result)).hexdigest();_canonical(result)
        return result
    except AreaCanopyEnergyHold:
        raise
    except numeric.CanopyEnergyHold as exc:
        raise AreaCanopyEnergyHold(str(exc))from None
    except(TypeError,ValueError,OverflowError,ZeroDivisionError,RecursionError):
        raise AreaCanopyEnergyHold('INPUT_HOLD: invalid or unrepresentable area-energy input')from None
