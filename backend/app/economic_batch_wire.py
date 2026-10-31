"""Closed lossless JSON result schema: Decimal strings and inventory rows."""
from dataclasses import fields,is_dataclass
from decimal import Decimal
import types
from typing import Annotated,Literal,Union,get_args,get_origin,get_type_hints

from pydantic import Field,create_model

from .economic_batch_query import _Envelope
from .economic_production_batches import ProductionBatchResult,FORMULA_VERSION
from .economics import EconomicResult
from .provenance import FrozenContract,Name,Digest

MoneyText=Annotated[str,Field(pattern=r'^-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:E[+-]?[0-9]+)?$')]


class InventoryRow(FrozenContract):
    batch_id:Name
    grade:Name
    channel:Name
    quantity_kg:MoneyText


_MODELS={}
def _wire(annotation):
    if annotation is Decimal:return MoneyText
    if is_dataclass(annotation):
        if annotation in _MODELS:return _MODELS[annotation]
        hints=get_type_hints(annotation);items={f.name:(_wire(hints[f.name]),...)for f in fields(annotation)
            if f.name!='closing_inventory'}
        if annotation is EconomicResult:
            items.update(closing_inventory=(tuple[InventoryRow,...]|None,...),
                formula_version=(Literal[FORMULA_VERSION],...),assessment_status=(Literal['hold'],...),
                result_id=(Digest,...),scenario_sha256=(Digest,...))
        if annotation is ProductionBatchResult:
            items.update(scope=(Literal['conditional_user_assumptions_only'],...),
                G0_G4=(Literal['not_assessed'],...),R2=(Literal['not_approved'],...),
                code_sha256=(Digest,...),component_sha256=(dict[str,Digest],...))
        model=create_model('BatchWire'+annotation.__name__,__base__=FrozenContract,**items)
        _MODELS[annotation]=model;return model
    origin=get_origin(annotation);args=get_args(annotation)
    if origin in(Union,types.UnionType):return Union[tuple(_wire(v)for v in args)]
    if origin is tuple:return tuple[tuple(_wire(v)if v is not Ellipsis else Ellipsis for v in args)]
    if origin is dict:return dict[_wire(args[0]),_wire(args[1])]
    return annotation


BatchResultWire=_wire(ProductionBatchResult)


class BatchArtifactRead(_Envelope):
    artifact_version:Literal['economic-batch-calculation-result-v1']
    status:Literal['completed']
    claim_scope:Literal['conditional_user_assumptions_only']
    result:BatchResultWire
