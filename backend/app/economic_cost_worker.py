"""One leased conditional cost trace over the shared atomic batch worker."""
from dataclasses import dataclass
from uuid import UUID

from .economic_batch_worker import EconomicBatchWorker,_BATCH_CODE_FILES
from .economic_cost_calculation import EconomicCostCalculationInput,EconomicCostCalculationService
from .economic_cost_trace import CostLineLedger,trace_bytes

ARTIFACT_VERSION='economic-cost-line-calculation-result-v1'


@dataclass(frozen=True)
class CostCalculationOutcome:
    job_id: UUID
    attempt: int
    state: str
    reason_code: str
    trace_id: str|None=None


class EconomicCostWorker(EconomicBatchWorker):
    _input_version='economic-cost-line-calculation-input-v1'
    _input_type=EconomicCostCalculationInput
    _service_type=EconomicCostCalculationService
    _ledger_type=CostLineLedger
    _artifact_version=ARTIFACT_VERSION
    _outcome_type=CostCalculationOutcome
    _reason_prefix='economic_cost'
    _code_files=_BATCH_CODE_FILES+('economic_cost_worker.py','economic_cost_calculation.py','economic_cost_trace.py')

    def _reference(self,value):
        return value.base_input

    def _encode(self,result):
        return trace_bytes(result)

    def _result_id(self,result):
        return result.trace_id
