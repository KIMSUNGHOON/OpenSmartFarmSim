"""Select a protected server contract by durable stage and input version."""

from hashlib import sha256
from types import MappingProxyType

from .cli_contracts import DecisionContract, ProposalHold, STAGES, _id, _json


class CliContractRouter(DecisionContract):
    VERSION = 'cli-contract-router-v1'

    def __init__(self, routes):
        if (type(routes) is not dict or not 1 <= len(routes) <= 16 or any(
                type(key) is not tuple or len(key) != 2 or
                type(key[0]) is not str or key[0] not in STAGES or not _id(key[1]) or
                not isinstance(contract, DecisionContract) or isinstance(contract, CliContractRouter)
                for key, contract in routes.items()) or
                {key[0] for key in routes} != STAGES):
            raise ValueError('CLI contract routes rejected')
        self._routes = MappingProxyType(dict(routes))

    def _select(self, job):
        raw = job.get('input_bytes')
        if type(raw) is not bytes:
            raise ProposalHold('input_unavailable')
        if sha256(raw).hexdigest() != job.get('input_sha256'):
            raise ProposalHold('input_hash_mismatch')
        value = _json(raw)
        stage = job.get('stage')
        if (type(value) is not dict or type(stage) is not str or stage not in STAGES or
                type(value.get('input_version')) is not str):
            raise ProposalHold('invalid_stage_input')
        contract = self._routes.get((stage, value['input_version']))
        if contract is None:
            raise ProposalHold('decision_contract_unregistered')
        return contract

    def binding_fields(self, job):
        return self._select(job).binding_fields(job)

    def input_context(self, job):
        return self._select(job).input_context(job)

    def plan(self, job, final_output):
        return self._select(job).plan(job, final_output)

    def __call__(self, job, final_output, proposed_artifact):
        try:
            contract = self._select(job)
        except ProposalHold as exc:
            return {'passed':False, 'version':self.VERSION, 'code':exc.code, 'disposition':None}
        return contract(job, final_output, proposed_artifact)
