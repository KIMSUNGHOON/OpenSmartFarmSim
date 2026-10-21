"""Closed Co2 execution progress responses; no routes or operational startup."""
from hashlib import sha256
from pathlib import Path as FilePath
from typing import Annotated,Literal
from pydantic import Field,create_model,model_validator
from . import api_contracts as jobs_public
from . import api_crop_replay as public
from .api_crop_greenhouse_co2_replay import FalseApproval
from .crop_result_store import READ_SCOPES

VERSION = 'joint-co2-solar-execution-query-v1'
INPUT_VERSION = 'joint-co2-solar-execution-input-v1'
SOURCE_VERSION = 'joint-co2-solar-input-source-v1'
RIGHTS_VERSION = 'joint-co2-solar-input-rights-v1'
MAX_RESPONSE_BYTES = 16 * 1024
MAX_CHECKPOINT_EVENTS = 4099
CODE_SHA256 = sha256(FilePath(__file__).read_bytes()).hexdigest()
PROGRESS_SCOPES = ('metadata',) + READ_SCOPES
Counter = Annotated[int, Field(strict=True, ge=0, le=2**63 - 1)]


def _need(value):
    if not value: raise ValueError('co2 execution response unavailable')


class Co2ExecutionCounts(public._Public):
    samples: Counter
    events: Counter


class Co2ExecutionCheckpoint(public._Public):
    head_sha256: public.Digest
    proof_sha256: public.Digest
    artifact_sha256: public.Digest | None
    status: Literal['ready', 'yielded', 'completed', 'hold']
    steps: Counter
    planned_steps: Annotated[int, Field(strict=True, ge=1, le=2**63 - 1)]
    provenance_sha256: public.Digest
    rights_or_gate_approval: FalseApproval
    counts: Co2ExecutionCounts
    computed_through_utc: public.UtcStamp | None
    checkpoint_recorded_at: public.UtcStamp
    publication_sequence: Annotated[int, Field(strict=True, ge=1, le=MAX_CHECKPOINT_EVENTS)]


Co2ExecutionResultFarm = create_model('Co2ExecutionResultFarm', __base__=public._Public,
    **{k: (public.Digest if k == 'registration_sha256' else public.Name, ...)
       for k in ('scenario_id', 'scenario_revision', 'registration_sha256', 'crop_id', 'batch_id', 'zone_id')})


class Co2ExecutionResult(public._Public):
    result_id: Annotated[str, Field(strict=True, pattern=r'^joint-co2-solar-result-v1:[a-f0-9]{64}$')]
    farm: Co2ExecutionResultFarm
    status: Literal['completed', 'hold']
    provenance_sha256: public.Digest
    rights_or_gate_approval: FalseApproval


class Co2ExecutionRead(public._Public):
    version: Literal['joint-co2-solar-execution-query-v1']
    scope: Literal['synthetic_joint_co2_solar_math_only']
    G0_G4: Literal['not_assessed']
    rights_or_gate_approval: FalseApproval
    job: jobs_public.JobStatus
    cancel_requested: Annotated[bool, Field(strict=True)]
    observed_at: public.UtcStamp
    checkpoint_status: Literal['none', 'current', 'unavailable']
    checkpoint: Co2ExecutionCheckpoint | None
    result: Co2ExecutionResult | None

    @model_validator(mode='after')
    def consistent_progress(self):
        _need((self.checkpoint_status == 'current') == (self.checkpoint is not None))
        if self.checkpoint is not None:
            c = self.checkpoint
            _need(c.steps <= c.planned_steps
                and (c.artifact_sha256 is not None) == (c.status in ('completed', 'hold'))
                and (c.computed_through_utc is None) == (c.status == 'ready'))
            if c.status == 'completed': _need(c.steps == c.planned_steps)
        if self.result is not None:
            _need(self.checkpoint is not None and self.checkpoint.status == self.result.status
                and self.job.state == ('succeeded' if self.result.status == 'completed' else 'hold')
                and self.result.provenance_sha256 == self.checkpoint.provenance_sha256)
        return self
