"""Pure exact source-plus-partial accounts; no context or checkpoint authority."""
from copy import deepcopy
from fractions import Fraction
from hashlib import sha256
from pathlib import Path

from . import crop_supply_forcing_interval as kernel
from . import crop_supply_morphology_candidate_books as legacy

base=kernel.base
q,x,need=base.q,base.x,base._need
CODE_SHA256=sha256(Path(__file__).read_bytes()).hexdigest()


def packet(math,current,state,partial,derived,at,steps):
    d=math.data;seed=d['seed'];units=math.units;p=d['program'];size=seed['state_layout']['original_prefix_length']
    numeric_view={**d,'initial':{'organs':seed['organs'],'state_layout':seed['state_layout']}}
    a,b=tuple(map(Fraction,current['last_confirmed']['state'])),tuple(map(Fraction,state))
    transfers={k:Fraction(v)for k,v in zip(units,partial,strict=True)}
    duration=at-x(current['at']['elapsed_seconds_exact'],'s')
    rows={**legacy._physical(numeric_view,a[:size],b[:size],transfers,current['last_confirmed']['derived'],derived,duration),
          **legacy._geometry(numeric_view,a,b,transfers,duration)}
    need(set(rows)==set(current['branch_ledgers'])==set(current['global_ledgers']),
         'BALANCE_HOLD: complete source and partial account inventory required')
    local={k:legacy.resume.books._row(terms,start,end,unit,steps)for k,(terms,start,end,unit)in rows.items()}
    composed={}
    for label in ('branch','global'):
        result={}
        for name,value in local.items():
            prior=current[label+'_ledgers'][name];unit=value['residual_exact']['unit']
            residual=x(prior['residual_exact'],unit)+x(value['residual_exact'],unit)
            budget=x(prior['budget_exact'],unit)+x(value['budget_exact'],unit)
            need(abs(residual)<=budget,'BALANCE_HOLD: exact source plus partial '+label+' '+name)
            result[name]={'residual_exact':q(residual,unit),'budget_exact':q(budget,unit)}
        composed['pending_'+label+'_ledgers']=result
    branch={k:Fraction(current['branch_integrated_transfers'][k]['value'])+v for k,v in transfers.items()}
    lifetime={k:x(current['lifetime_transfers_exact'][k],units[k])+v for k,v in transfers.items()}
    age=x(current['schedule']['age_exact'],'degC_day')+(transfers['indoor_air_temperature_time']-
        Fraction(math.basis['shoot_base_temperature'])*duration)/86400
    threshold=x(current['schedule']['next_threshold_exact'],'degC_day');grid=Fraction(seed['original_numerical']['step_seconds'])
    return {'at':{'time_origin_utc':current['at']['time_origin_utc'],'elapsed_seconds_exact':q(at,'s')},
            'state':list(state),'derived':deepcopy(derived),'partial_steps':steps,
            'partial_interval_transfers':{k:{'value':v,'unit':unit}for(k,unit),v in zip(units.items(),partial,strict=True)},
            'pending_branch_transfers_exact':{k:q(v,units[k])for k,v in branch.items()},
            'pending_lifetime_transfers_exact':{k:q(v,units[k])for k,v in lifetime.items()},
            'local_ledgers':local,**composed,'point_totals_exact':deepcopy(current['point_totals_exact']),
            'transfer_origins':deepcopy(current['transfer_origins']),'event_sequence':current['event_sequence'],
            'shoot_age_exact':q(age,'degC_day'),'shoot_threshold_residual_exact':q(age-threshold,'degC_day'),
            'represented_threshold_status':'crossed'if age>=threshold else'not_crossed',
            'grid_index':int(at//grid),'grid_remainder_exact':q(at-(at//grid)*grid,'s'),
            'next_grid_endpoint_exact':q((at//grid+1)*grid,'s'),'schedule_consumed':False}
