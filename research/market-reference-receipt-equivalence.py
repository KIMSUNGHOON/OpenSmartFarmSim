"""Research-only dependency inventory; never a runtime authorization/seal."""
from decimal import getcontext
from hashlib import sha256
from pathlib import Path
import inspect
import sys

import pydantic
import pydantic_core
from pydantic import BaseModel
from app import (api_market_source, economic_contracts, economics, jobs, market,
                 market_candidate_store, market_scenario, market_source_store, provenance)

MODULES=(api_market_source,economic_contracts,economics,jobs,market,
         market_candidate_store,market_scenario,market_source_store,provenance)
SOURCE_KINDS={
    'get_economic_scenario':'economic_scenario','get_economic_scenario_pin':'economic_scenario',
    'get_economic_input':'economic_input','get_joint_shock':'joint_shock',
    'get_joint_shock_pin':'joint_shock','get_input_rights':'input_rights',
    'get_settlement_applicability':'settlement_applicability',
    'get_settlement_evidence':'settlement_evidence','get_prior_batch_cost':'prior_batch_cost'}
DYNAMIC=frozenset({'tenant_is_authenticated','get_market_candidate','get_market_hold_report','get_decision_context'})
SCENARIOS=frozenset({'get_market_candidate','get_economic_scenario','get_economic_scenario_pin'})
METHODS=(
 (market_source_store.MarketSourceStore,('_read','_read_in_transaction','_read_context','_model',
    '_verified','_checked_job_input','_tenant','tenant_is_authenticated',*SOURCE_KINDS)),
 (api_market_source._MarketSources,('__getattr__','tenant_is_authenticated')),
 (market_candidate_store.MarketCandidateStore,('__getattr__','_tenant','_read_context','_checked_input',
    '_input_in_transaction','_candidate','_candidate_in_transaction','_checked_candidate',
    'get_market_candidate','get_economic_scenario','get_economic_scenario_pin','get_economic_input')))


def _function(value):
    function=getattr(value,'__func__',value)
    return (id(function),getattr(function,'__code__',None),repr(getattr(function,'__defaults__',None)),
            repr(getattr(function,'__kwdefaults__',None)))


DEFAULT_METHODS=tuple((cls,name,_function(getattr(cls,name))) for cls,names in METHODS for name in names)


def default_methods(owner):
    if type(owner) is not market_candidate_store.MarketCandidateStore:return False
    view=owner._source
    if type(view) is not api_market_source._MarketSources or type(view._source) is not market_source_store.MarketSourceStore:return False
    instances={type(owner):owner,type(view):view,type(view._source):view._source}
    return all(_function(getattr(cls,name))==expected
        and _function(getattr(instances[cls],name))==expected for cls,name,expected in DEFAULT_METHODS)


def _models():
    found=set();seen=set();functions=[]
    def visit(value):
        if id(value) in seen:return
        seen.add(id(value))
        if isinstance(value,type) and issubclass(value,BaseModel):
            found.add(value);visit(value.__pydantic_core_schema__)
        elif isinstance(value,dict):
            for item in value.values():visit(item)
        elif isinstance(value,(tuple,list)):
            for item in value:visit(item)
        elif inspect.isfunction(value) or inspect.ismethod(value):functions.append(_function(value))
    for model,_,_ in market_source_store._KINDS.values():visit(model)
    for model in (economic_contracts.OwnedScenarioPin,market_scenario.JointShockPin,market_scenario.MarketScenarioRequest):visit(model)
    return tuple(sorted(found,key=lambda cls:(cls.__module__,cls.__qualname__))),tuple(functions)


def envelope(owner):
    """In-process differential evidence, NOT a production dependency guard.

    Identity/repr observations are deliberately non-portable. Principal outputs,
    DB rows, rights decisions and permission results are never cached here.
    """
    models,validators=_models();ctx=getcontext()
    aliases=tuple((module.__name__,name,_function(value)) for module in MODULES
        for name,value in vars(module).items() if inspect.isfunction(value))
    model_state=tuple((cls.__module__,cls.__qualname__,id(cls),id(cls.__pydantic_validator__),
        id(cls.__pydantic_serializer__),repr(cls.__pydantic_core_schema__),repr(cls.model_config),
        tuple((name,repr(field)) for name,field in cls.model_fields.items()),
        _function(cls.model_validate_json),_function(cls.model_dump)) for cls in models)
    policies=(market_source_store.VERSION,market_source_store.MAX_INPUT_BYTES,
        jobs.MAX_INPUT_BYTES,tuple(sorted(jobs._BLOCKED_INPUT_KEYS)),
        (jobs._BLOCKED_INPUT_KEY_MARKERS.pattern,jobs._BLOCKED_INPUT_KEY_MARKERS.flags),
        tuple(sorted(api_market_source._SOURCE_METHODS)),
        tuple(sorted(market_candidate_store._RECORD_KEYS)),
        (market_candidate_store._DIGEST.pattern,market_candidate_store._DIGEST.flags),
        (economic_contracts._DECIMAL.pattern,economic_contracts._DECIMAL.flags),
        owner._source._source.runtime_identity[0].roles['authority'])
    callable_globals=tuple((module.__name__,name,id(value)) for module in MODULES
        for name,value in vars(module).items() if callable(value) and not inspect.isfunction(value))
    library_functions=tuple(_function(value) for value in (
        market_candidate_store.json.loads,market_candidate_store.json.dumps,
        market_candidate_store.deepcopy,market_candidate_store.sha256,market_source_store.UUID))
    return (policies,callable_globals,library_functions,
        tuple((module.__name__,sha256(Path(module.__file__).read_bytes()).hexdigest()) for module in MODULES),
        tuple((cls,name,_function(getattr(cls,name))) for cls,names in METHODS for name in names),
        tuple((kind,model,identity,revision) for kind,(model,identity,revision) in market_source_store._KINDS.items()),
        aliases,model_state,validators,
        (ctx.prec,ctx.rounding,ctx.Emin,ctx.Emax,ctx.capitals,ctx.clamp,
         tuple(sorted((s.__name__,v) for s,v in ctx.traps.items()))),
        sys.version,pydantic.__version__,pydantic_core.__version__,default_methods(owner))


def trace_plan(trace, candidate_present, pin_present):
    """Closed test planner; presence must be independently rechecked in runtime."""
    sources=[];candidates=[];pins=[];dynamic=[];pure=[]
    for index,(name,args,_) in enumerate(trace):
        if name not in SOURCE_KINDS and name not in DYNAMIC:return None
        if name in SCENARIOS and args not in pins:pins.append(args)
        if name=='get_economic_input' and args not in candidates:candidates.append(args)
        if name in DYNAMIC or (name in SCENARIOS and args in pin_present):
            dynamic.append(index);continue
        pure.append(index)
        if name=='get_economic_input' and args in candidate_present:continue
        key=(SOURCE_KINDS[name],*args,*(('single',) if name=='get_prior_batch_cost' else ()))
        if key not in sources:sources.append(key)
    if len(sources)+len(candidates)+len(pins)>128:return None
    return {'source_keys':tuple(sources),'candidate_keys':tuple(candidates),'pin_keys':tuple(pins),
            'dynamic_indexes':tuple(dynamic),'pure_indexes':tuple(pure)}
