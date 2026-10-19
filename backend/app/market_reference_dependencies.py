"""Supported default decoding dependencies within an owned registration scope."""
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import fields
from decimal import Decimal,getcontext
from datetime import date,datetime
from hashlib import sha256
from pathlib import Path
import copy
import json
import math
import re
import sys
import types
import tomllib
import typing

import annotated_types
import pydantic
import pydantic_core
from pydantic import AfterValidator,BaseModel,StringConstraints
from pydantic_core import PydanticUndefined,SchemaValidator,SchemaSerializer

from . import (api_market_source,economic_contracts,economics,jobs,market,
               market_candidate_store,market_scenario,market_source_store,provenance)
from .farm_registration_read_scope import RegistrationRead


CODE_SHA256=sha256(Path(__file__).read_bytes()).hexdigest()
_active=ContextVar('market_reference_dependencies',default=None)
_MODULES=(api_market_source,economic_contracts,economics,jobs,market,
          market_candidate_store,market_scenario,market_source_store,provenance)
_SOURCE_READS=('get_economic_scenario','get_economic_scenario_pin','get_economic_input',
    'get_joint_shock','get_joint_shock_pin','get_input_rights','get_settlement_applicability',
    'get_settlement_evidence','get_prior_batch_cost')
_METHODS=((market_source_store.MarketSourceStore,('_read','_read_in_transaction','_read_context',
    '_model','_verified','_checked_job_input','_tenant','tenant_is_authenticated',*_SOURCE_READS)),
    (api_market_source._MarketSources,('__getattr__','tenant_is_authenticated')),
    (market_candidate_store.MarketCandidateStore,('__getattr__','_tenant','_read_context',
    '_checked_input','_input_in_transaction','_candidate','_candidate_in_transaction',
    '_checked_candidate','get_market_candidate','get_economic_scenario','get_economic_scenario_pin','get_economic_input')))
_FUNCTIONS=((market_source_store,('_name',)),(jobs,('canonical_input_bytes','_validate_input_fields')),
    (economic_contracts,('untrusted_data','utc')),(economics,('canonical_scenario_sha256',)),
    (market_scenario,('_json',)),(market_candidate_store,('_canonical','_hash','_pairs','_parse','_check_record_identity')),
    (provenance,('_exact_name',)))
_METADATA=(AfterValidator,StringConstraints,annotated_types.MinLen)
_PATTERN_METHOD=type(re.compile('').match)
_MAX_NODES=200000
_MAX_TEXT=2097152


class DependencyHold(ValueError):
    pass


class _Unsupported(ValueError):
    pass


def _need(value):
    if not value:raise DependencyHold('current reference dependencies unavailable')


def _freeze(value,memo,budget):
    """Closed state representation; no repr, user serialization or object walking."""
    budget[0]+=1
    if budget[0]>_MAX_NODES:raise _Unsupported()
    if value is None or type(value) in (bool,int):return value
    if type(value) in (str,bytes):
        if len(value)>_MAX_TEXT:raise _Unsupported()
        budget[1]+=len(value.encode('utf8')) if type(value) is str else len(value)
        if budget[1]>_MAX_TEXT:raise _Unsupported()
        return value
    if type(value) is float:
        if not math.isfinite(value):raise _Unsupported()
        return ('float',value)
    if value is PydanticUndefined:return ('undefined',)
    if value is Ellipsis:return ('ellipsis',)
    if isinstance(value,(type,types.CodeType)):return ('identity',value)
    identity=id(value)
    if identity in memo:return ('reference',memo[identity][1])
    memo[identity]=(value,len(memo))
    freeze=lambda v:_freeze(v,memo,budget)
    if type(value) is dict:return ('dict',tuple((freeze(k),freeze(v)) for k,v in value.items()))
    if type(value) in (tuple,list):return (type(value),tuple(freeze(v) for v in value))
    if type(value) in (set,frozenset):return (type(value),frozenset(freeze(v) for v in value))
    if type(value) is types.MethodType:
        if not isinstance(value.__self__,type):raise _Unsupported()
        return ('method',value.__self__,freeze(value.__func__))
    if type(value) is types.FunctionType:
        if not (value.__module__ in {m.__name__ for m in _MODULES} or value.__module__.startswith('pydantic.') or value.__module__ in ('copy','json','json.encoder','json.decoder','json.scanner','uuid','contextlib')):
            raise _Unsupported()
        closure=tuple(freeze(cell.cell_contents) for cell in value.__closure__ or ())
        return ('function',value,value.__code__,freeze(value.__defaults__),freeze(value.__kwdefaults__),closure)
    if type(value) in (types.BuiltinFunctionType,types.MethodDescriptorType,types.WrapperDescriptorType):
        return ('builtin',value)
    if isinstance(value,re.Pattern):return ('pattern',value.pattern,value.flags)
    if type(value) is _PATTERN_METHOD and isinstance(value.__self__,re.Pattern):
        return ('pattern_method',freeze(value.__self__),value.__name__)
    if type(value) in _METADATA:
        return (type(value),tuple((f.name,freeze(getattr(value,f.name))) for f in fields(value)))
    origin=typing.get_origin(value)
    if origin is not None:return ('annotation',origin,tuple(freeze(v) for v in typing.get_args(value)))
    raise _Unsupported('unsupported current reference dependency state')


def _models():
    result=set();seen=set()
    def visit(value):
        if id(value) in seen:return
        seen.add(id(value))
        if len(seen)>_MAX_NODES:raise _Unsupported()
        if isinstance(value,type) and issubclass(value,BaseModel):
            result.add(value);visit(value.__pydantic_core_schema__)
        elif type(value) is dict:
            for child in value.values():visit(child)
        elif type(value) in (list,tuple):
            for child in value:visit(child)
    for model,_,_ in market_source_store._KINDS.values():visit(model)
    for model in (economic_contracts.OwnedScenarioPin,market_scenario.JointShockPin,market_scenario.MarketScenarioRequest):visit(model)
    return tuple(sorted(result,key=lambda cls:(cls.__module__,cls.__qualname__)))


def _library_state(freeze):
    modules=(json,json.encoder,json.decoder,json.scanner,copy)
    functions=tuple((m.__name__,name,freeze(value)) for m in modules for name,value in vars(m).items()
        if type(value) is types.FunctionType and value.__module__==m.__name__)
    aliases=tuple((m.__name__,name,id(value)) for m in modules for name,value in vars(m).items() if callable(value))
    classes=tuple((cls,tuple((name,id(value)) for name,value in vars(cls).items()),
        tuple(freeze(value) for value in vars(cls).values() if type(value) is types.FunctionType))
        for cls in (json.JSONEncoder,json.JSONDecoder))
    copied=(str,bytes,int,float,bool,type(None),list,tuple,dict,date,datetime,Decimal,
        market_source_store.UUID,pydantic_core.TzInfo)
    dispatch=tuple((kind,freeze(copy._deepcopy_dispatch.get(kind)),freeze(copy.dispatch_table.get(kind))) for kind in copied)
    policies=freeze((json.encoder.ESCAPE,json.encoder.ESCAPE_ASCII,json.encoder.ESCAPE_DCT,
        json.decoder.WHITESPACE,json.decoder.WHITESPACE_STR,json.decoder.STRINGCHUNK,json.decoder.BACKSLASH))
    constants=tuple((name,value.hex()) for name,value in json.decoder._CONSTANTS.items())
    code=tuple((m.__name__,sha256(Path(m.__file__).read_bytes()).digest()) for m in modules)
    return functions,aliases,classes,dispatch,policies,constants,code


def _snapshot():
    lock_raw=(Path(__file__).resolve().parents[1]/'uv.lock').read_bytes()
    locked={p['name']:p['version'] for p in tomllib.loads(lock_raw.decode('utf8'))['package']
        if p['name'] in ('pydantic','pydantic-core')}
    if (sys.version_info[:2]!=(3,12) or locked!={'pydantic':pydantic.__version__,'pydantic-core':pydantic_core.__version__}):
        raise _Unsupported('unlocked current reference dependency version')
    memo={};budget=[0,0];freeze=lambda v:_freeze(v,memo,budget)
    models=[]
    for cls in _models():
        if (type(cls.__pydantic_validator__) is not SchemaValidator
                or type(cls.__pydantic_serializer__) is not SchemaSerializer):raise _Unsupported()
        info=tuple((name,id(field),field.annotation,field.default,field.default_factory,field.alias,
            field.validation_alias,field.serialization_alias,field.metadata) for name,field in cls.model_fields.items())
        models.append((cls,cls.__pydantic_validator__,cls.__pydantic_serializer__,
            tuple((name,id(value)) for name,value in vars(cls).items()),
            freeze(cls.__pydantic_core_schema__),freeze(cls.model_config),freeze(info),
            freeze(cls.model_validate_json),freeze(cls.model_dump)))
    policies=(market_source_store.VERSION,market_source_store.MAX_INPUT_BYTES,jobs.MAX_INPUT_BYTES,
        jobs._BLOCKED_INPUT_KEYS,jobs._BLOCKED_INPUT_KEY_MARKERS,api_market_source._SOURCE_METHODS,
        market_candidate_store._RECORD_KEYS,market_candidate_store._DIGEST,economic_contracts._DECIMAL,
        market_source_store._KINDS)
    aliases=tuple((m.__name__,name,id(value)) for m in _MODULES for name,value in vars(m).items()
        if isinstance(value,(type,types.BuiltinFunctionType,types.FunctionType)))
    functions=tuple((m.__name__,name,freeze(getattr(m,name))) for m,names in _FUNCTIONS for name in names)
    methods=tuple((cls,name,freeze(getattr(cls,name))) for cls,names in _METHODS for name in names)
    libraries=tuple(freeze(f) for f in (json.loads,json.dumps,copy.deepcopy,
        market_source_store.UUID.__str__,json.JSONEncoder.encode,json.JSONEncoder.iterencode,
        json.JSONDecoder.decode,json.JSONDecoder.raw_decode))
    ctx=getcontext()
    decimal=(ctx.prec,ctx.rounding,ctx.Emin,ctx.Emax,ctx.capitals,ctx.clamp,
        tuple(sorted((signal.__name__,enabled) for signal,enabled in ctx.traps.items())))
    code=tuple((m.__name__,sha256(Path(m.__file__).read_bytes()).digest()) for m in _MODULES)
    lock=sha256(lock_raw).digest()
    return (tuple(models),freeze(policies),aliases,functions,methods,libraries,_library_state(freeze),decimal,code,lock,
        sys.version,pydantic.__version__,pydantic_core.__version__,
        tuple((name,id(value)) for name,value in vars(BaseModel).items()),
        _MAX_NODES,_MAX_TEXT)


def _default_instances(owner):
    if type(owner) is not market_candidate_store.MarketCandidateStore:return False
    view=owner._source
    if type(view) is not api_market_source._MarketSources or type(view._source) is not market_source_store.MarketSourceStore:return False
    instances={type(owner):owner,type(view):view,type(view._source):view._source}
    return all(getattr(getattr(instances[cls],name),'__func__',getattr(instances[cls],name))
        is getattr(getattr(cls,name),'__func__',getattr(cls,name)) for cls,names in _METHODS for name in names)


class _Dependencies:
    def __init__(self,owner,witness,state):
        self.owner,self.witness,self.state=owner,witness,state
        self.binding=owner._shared_profile()
        _need(self.binding is not None)
        self.authority=owner.runtime_identity[0].roles['authority']
        self.slot=_active;self.token=None;self.active=True;self.failed=False
        self.functions=(_snapshot,_freeze,_models,_default_instances,_library_state)

    def check(self):
        try:
            _need(self.active and not self.failed and self.slot is _active and self.slot.get() is self
                and self.token is not None and self.functions==(_snapshot,_freeze,_models,_default_instances,_library_state))
            self.slot.reset(self.token);self.token=self.slot.set(self)
            self.witness._guard()
            _need(self.witness.repository is self.owner and self.witness.value is not None
                and self.owner._shared_profile(self.binding[:2]) is not None
                and self.owner.runtime_identity[0].roles['authority']==self.authority
                and self.owner._tenant('market_candidate_read')==self.witness.args[0]
                and _default_instances(self.owner) and _snapshot()==self.state
                and sha256(Path(__file__).read_bytes()).hexdigest()==CODE_SHA256)
        except Exception:
            self.failed=True
            if self.witness is not None:self.witness.failed=True
            raise

    def close(self):
        self.active=False
        self.state=self.binding=self.functions=None
        try:
            if self.token is not None:
                self.slot.reset(self.token);self.token=None
        except Exception:
            self.failed=True
            if self.witness is not None:self.witness.failed=True
            raise
        finally:self.owner=self.witness=None


@contextmanager
def scope(owner,witness):
    """Yield an owned guard or None for an initially unsupported decoding profile."""
    existing=_active.get()
    if existing is not None:
        existing.failed=True;existing.witness.failed=True
        raise DependencyHold('nested current reference dependencies unavailable')
    _need(type(witness) is RegistrationRead and witness.repository is owner
        and witness.active and witness.value is not None and not witness.loading)
    witness._guard()
    try:
        supported=_BOOTSTRAP is not None and _default_instances(owner) and _snapshot()==_BOOTSTRAP
    except (ValueError,TypeError,AttributeError,OSError,RecursionError):supported=False
    if not supported:
        yield None
        return
    guard=_Dependencies(owner,witness,_BOOTSTRAP);guard.token=_active.set(guard)
    try:
        guard.check();yield guard;guard.check()
    except BaseException:
        guard.failed=True;witness.failed=True
        raise
    finally:guard.close()


try:_BOOTSTRAP=_snapshot()
except (ValueError,TypeError,AttributeError,OSError,RecursionError):_BOOTSTRAP=None
