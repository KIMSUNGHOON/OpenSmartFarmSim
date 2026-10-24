"""Explicit geometry with retained carbon equations; crop-explicit-lai-carbon-cohorts-v1.md."""
from hashlib import sha256
import json
from math import exp, expm1, fsum, hypot, isfinite, log, sqrt, ulp
from pathlib import Path
import re

from . import crop_growth_rates as source
from . import crop_explicit_lai_photosynthesis as optical
from . import crop_fruit_cohorts as fruit
from . import crop_fruit_startup as startup
from . import crop_plant_cohort_rates as original
from . import crop_fruit_transport as transport

MODEL_VERSION = 'explicit-lai-startup-carbon-cohort-rates-research-v1'
CODE_SHA256 = sha256(Path(__file__).read_bytes()).hexdigest()
COMPONENT_CODE_SHA256 = {m.__name__: sha256(Path(m.__file__).read_bytes()).hexdigest()
                        for m in (source, optical, fruit, startup, original, transport)}
BLOCKS = ('state', 'cohort_state', 'forcing', 'removals', 'fruit_entry', 'geometry')


class ExplicitLaiCarbonHold(ValueError):
    pass


def _need(condition, reason):
    if not condition:
        raise ExplicitLaiCarbonHold(reason)


def _canonical(value):
    raw = json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()
    _need(len(raw) <= 128*1024, 'CAPACITY_HOLD: bounded explicit-LAI carbon stage required')
    return raw


def _q(value, unit=source.RATE_UNIT):
    return {'value': value, 'unit': unit}


def _non_optical(s, f, p):
    filtered = s['temperature_filtered_24h']; temperature = f['canopy_temperature']
    buffer_factor = source._sigmoid(p['buffer_empty_slope']*(s['buffer']-p['cBufMin']))
    instant = source._sigmoid(p['instant_low_slope']*(temperature-p['tCanMin']))*source._sigmoid(
        -p['instant_high_slope']*(temperature-p['tCanMax']))
    averaged = source._sigmoid(p['filtered_low_slope']*(filtered-p['tCan24Min']))*source._sigmoid(
        -p['filtered_high_slope']*(filtered-p['tCan24Max']))
    x = s['temperature_sum']/p['tEndSum']; smoothing = sqrt(p['development_smoothing_squared'])
    development = 0.5*(1+(2*x-1)/(hypot(x,smoothing)+hypot(x-1,smoothing)))
    common = buffer_factor*averaged*(p['allocation_temperature_slope']*filtered+p['allocation_temperature_intercept'])
    allocation = {'fruit': common*instant*development*p['rgFruit'],
                  'leaf': common*p['rgLeaf'], 'stem_root': common*p['rgStem']}
    factor = -expm1(-p['cRgr']*p['rgr'])*exp(log(p['q10m'])*(filtered-p['maintenance_temperature_reference_c'])/
                                         p['q10_temperature_interval_c'])
    maintenance = {organ: factor*s[organ]*p[key] for organ,key in (('leaf','cLeafM'),('stem_root','cStemM'))}
    _need(all(isfinite(v) and v >= 0 for v in (*allocation.values(),*maintenance.values())),
          'NUMERIC_HOLD: invalid non-optical flux')
    return allocation, maintenance


def calculate_plant_rates(*, state, cohort_state, forcing, removals, fruit_entry, geometry,
                          growth_profile, cohort_profile, transport_profile):
    try:
        supplied = dict(state=state,cohort_state=cohort_state,forcing=forcing,removals=removals,
                        fruit_entry=fruit_entry,geometry=geometry)
        raw = _canonical(supplied); captured = json.loads(raw)
        _need(type(growth_profile) is source.ReferenceParameters
              and type(cohort_profile) is fruit.ReferenceFruitCohortParameters
              and type(transport_profile) is transport.ReferenceFruitTransportParameters,
              'PROFILE_HOLD: three pinned reference profiles required')
        for pkey,ckey in (('cFruitG','fruit_growth_respiration'),('cFruitM','fruit_maintenance'),
                ('cRgr','cRgr'),('q10m','Q10'),('maintenance_temperature_reference_c','maintenance_temperature_reference_c'),
                ('q10_temperature_interval_c','q10_temperature_interval_c'),('seconds_per_day','seconds_per_day')):
            _need(growth_profile.values[pkey] == cohort_profile.values[ckey], 'PROFILE_HOLD: incompatible shared coefficients')
        for block in captured.values():
            _need(type(block) is dict and set(block) == {'input_id','origin','values'}, 'INPUT_HOLD: closed stage block required')
            _need(type(block['input_id']) is str and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.:/-]{0,199}',block['input_id'])
                  and block['origin'] == 'synthetic', 'SCOPE_HOLD: bounded explicitly synthetic stage required')
        s,ns = source._block(captured['state'], original.PLANT_UNITS)
        f,nf = source._block(captured['forcing'], source.FORCING_UNITS)
        r,nr = source._block(captured['removals'], original.REMOVAL_UNITS)
        e,ne = source._block(captured['fruit_entry'], original.ENTRY_UNITS)
        g,ng = source._block(captured['geometry'], {'leaf_area_index':'m2_leaf/m2_floor'})
        c,nc = fruit._block(captured['cohort_state'], fruit.SCALAR_UNITS, fruit.ARRAY_UNITS)
        _need(all(s[k] == c[k] for k in fruit.SCALAR_UNITS), 'STATE_MISMATCH_HOLD: shared temperature states differ')
        low,high = growth_profile.filtered_temperature_bounds
        _need(low <= s['temperature_filtered_24h'] <= high, 'INPUT_HOLD: original filtered temperature domain required')
        _need(g['leaf_area_index'] == 0 or s['leaf'] > 0, 'STATE_HOLD: positive geometry without represented leaf carbon unsupported')
        normalized = dict(state=ns,cohort_state=nc,forcing=nf,removals=nr,fruit_entry=ne,geometry=ng)
        demand = fruit.calculate_demand_rates(state=nc,profile=cohort_profile)
        photo = optical.calculate_photosynthesis(inputs={'input_id':nf['input_id'],'origin':'synthetic','values':{
            **nf['values'],'buffer':ns['values']['buffer'],'leaf_area_index':ng['values']['leaf_area_index']}},profile=growth_profile)
        requested,maintenance = _non_optical(s,f,growth_profile.values)
        retained = startup.calculate_startup_rates(state={**ne,'values':{**ne['values'],
            'fruit_carbohydrate_inflow':_q(requested['fruit']), 'fruit_potential_demand':demand['weighted_demand']}},profile=cohort_profile)
        cohorts = fruit.calculate_cohort_rates(state=nc,inflow={**ne,'values':{**ne['values'],
            'fruit_carbohydrate_inflow':retained['effective_carbohydrate_inflow']}},profile=cohort_profile,transport_profile=transport_profile)
        _need(cohorts['allocation'] == retained['carbohydrate_inflow'] and
              cohorts['fruit_growth_respiration'] == retained['realized_growth_respiration'],
              'BALANCE_HOLD: realized allocation or respiration differ')
        p = growth_profile.values
        requested_growth = fsum(p[key]*requested[organ] for organ,key in (('fruit','cFruitG'),('leaf','cLeafG'),('stem_root','cStemG')))
        buffer_base = fsum((photo['photosynthesis']['value'],-requested_growth,*(-v for v in requested.values())))
        derivatives = {'buffer':_q(fsum((buffer_base,retained['buffer_derivative_adjustment']['value']))),
            **{k:_q(fsum((requested[k],-maintenance[k],-r[k]))) for k in ('leaf','stem_root')},
            'temperature_filtered_24h':_q((f['canopy_temperature']-s['temperature_filtered_24h'])/p['seconds_per_day'],'degC/s'),
            'temperature_sum':_q(f['canopy_temperature']/p['seconds_per_day'],'degC_day/s')}
        _need(all(isfinite(q['value']) for q in derivatives.values()), 'NUMERIC_HOLD: nonfinite plant derivative')
        _need(all(s[k] != 0 or derivatives[k]['value'] >= 0 for k in ('buffer','leaf','stem_root')),
              'DEPLETED_STATE_HOLD: outward final derivative at zero storage')
        growth = fsum((startup._product(p['cLeafG'],requested['leaf']),startup._product(p['cStemG'],requested['stem_root']),
                       retained['realized_growth_respiration']['value']))
        fruit_maintenance = fsum(q['value'] for q in cohorts['maintenance']); total_fruit = fsum(c['fruit_carbohydrate'])
        terms = [*(derivatives[k]['value'] for k in ('buffer','leaf','stem_root')),
            *(q['value'] for q in cohorts['derivatives']['fruit_carbohydrate']),growth,*maintenance.values(),fruit_maintenance,
            *r.values(),cohorts['terminal_outflow']['fruit_carbohydrate']['value'],-photo['photosynthesis']['value']]
        residual = fsum(terms)
        budget = fsum((cohorts['balance_budget']['carbohydrate']['value'],retained['balance_budget']['whole_plant']['value'],
                       64*ulp(max(1.0,*map(abs,terms)))))
        _need(all(isfinite(v) for v in (*terms,total_fruit,residual,budget)) and abs(residual) <= budget,
              'BALANCE_HOLD: unresolved explicit-LAI whole carbon ledger')
        profiles = {name:profile.sha256 for name,profile in (('growth',growth_profile),('cohort',cohort_profile),('transport',transport_profile))}
        identity = {'model_version':MODEL_VERSION,'code_sha256':CODE_SHA256,'component_code_sha256':dict(COMPONENT_CODE_SHA256),
            'profile_sha256':profiles,'policy_sha256':startup.POLICY_SHA256,'inputs':normalized,
            'component_input_sha256':{'optical':photo['input_sha256'],'cohorts':cohorts['input_sha256'],'startup':retained['input_sha256']}}
        result = {**identity,'input_sha256':sha256(_canonical(identity)).hexdigest(),'raw_input_sha256':sha256(raw).hexdigest(),
            'scope':'software_research_only','claim_scope':'synthetic_explicit_lai_carbon_cohort_math_only','G0_G4':'not_assessed',
            'research_assumptions':list(original.ASSUMPTIONS),'optical':photo,'photosynthesis':photo['photosynthesis'],'lai':photo['lai'],
            'derivatives':derivatives,'cohorts':cohorts,'fruit_startup':retained,'growth_respiration':_q(growth),
            'requested_allocation':{k:_q(v) for k,v in requested.items()},
            'allocation':{**{k:_q(v) for k,v in requested.items()},'fruit':retained['effective_carbohydrate_inflow']},
            'vegetative_maintenance':{k:_q(v) for k,v in maintenance.items()},'removals':nr['values'],
            'fruit_carbohydrate_total':_q(total_fruit,source.MASS_UNIT),'fruit_maintenance':_q(fruit_maintenance),
            'balance_residual':{'carbohydrate':_q(residual),'number':cohorts['balance_residual']['number']},
            'balance_budget':{'carbohydrate':_q(budget),'number':cohorts['balance_budget']['number']}}
        _canonical(result)
        return result
    except ExplicitLaiCarbonHold:
        raise
    except (source.CropRateHold,optical.ExplicitLaiPhotosynthesisHold,fruit.FruitCohortHold,startup.FruitStartupHold) as exc:
        raise ExplicitLaiCarbonHold(str(exc)) from None
    except (ValueError,TypeError,OverflowError,RecursionError,ZeroDivisionError):
        raise ExplicitLaiCarbonHold('INPUT_HOLD: invalid or unrepresentable explicit-LAI carbon stage') from None
