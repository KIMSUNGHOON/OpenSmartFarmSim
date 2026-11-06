"""Closed cost HTTP schema over the unchanged lossless batch wire types."""
from typing import Literal

from .economic_batch_wire import _wire
from .economic_cost_query import _CostEnvelope
from .economic_cost_trace import CostTraceResult
from .provenance import Name,Digest


class CostResultWire(_wire(CostTraceResult)):
    trace_version:Literal['economic-cost-line-trace-v1']
    trace_id:Digest
    tenant_id:Name
    code_sha256:Digest
    component_sha256:dict[str,Digest]


class CostArtifactRead(_CostEnvelope):
    artifact_version:Literal['economic-cost-line-calculation-result-v1']
    status:Literal['completed']
    claim_scope:Literal['conditional_user_assumptions_only']
    result:CostResultWire
