"""Bind conditional money calculations to a currently verified authored Run."""

from hashlib import sha256
from uuid import UUID

from .api_authored_thermal import AUTHORED_READ_SCOPES, read_authored_job_completion
from .farm_authored_run_store import AuthoredRunStore
from .farm_authoring_storage import FarmAuthoringService
from .jobs import canonical_input_bytes


AUTHORED_ECONOMIC_SCOPES = AUTHORED_READ_SCOPES


class AuthoredEconomicHold(ValueError):
    pass


def authored_economic_pointers(runs, jobs, results, farm):
    try:
        if (type(runs) is not AuthoredRunStore or runs.jobs is not jobs or
                type(runs.preparer.authoring) is not FarmAuthoringService or
                runs.preparer.authoring.replay is not farm or farm.jobs is not jobs or
                farm.candidates is not results._candidates or
                farm.thermal.runs is not results._candidates._source._holds._context_store):
            raise ValueError()
        runs.preparer._binding()
        author = runs.preparer.authoring
        release = runs.preparer.release_store
        completion = release.verifier.completion
        if (completion.jobs is not jobs or
                completion.runs is not farm.thermal.runs or
                completion.review.authoring is not author):
            raise ValueError()
        return (runs, runs.preparer, author, author._pointers(), release,
            release.verifier, completion, completion.review,
            completion.execution_verifier, runs.gate_key)
    except Exception:
        raise AuthoredEconomicHold('authored economic authority unavailable') from None


def authored_economic_completion(runs, jobs, results, farm, tenant, value):
    pointers = authored_economic_pointers(runs, jobs, results, farm)
    author = runs.preparer.authoring

    def guard():
        if not all(jobs._has_scope(tenant, scope) for scope in AUTHORED_ECONOMIC_SCOPES):
            raise PermissionError('authored economic access denied')
        if authored_economic_pointers(runs, jobs, results, farm) != pointers:
            raise AuthoredEconomicHold('authored economic authority changed')
        author._guard(tenant, pointers[3], AUTHORED_ECONOMIC_SCOPES)

    guard()
    try:
        completion = read_authored_job_completion(jobs, runs, tenant, UUID(value.thermal_job_id))
        if completion is None:
            raise ValueError()
        thermal = completion.value
        if (thermal['scenario_id'], thermal['scenario_revision'], thermal['registration_sha256']) != (
                value.authored_scenario_id, value.authored_scenario_revision, value.registration_sha256):
            raise ValueError()
        registered = author.read_registration(tenant, value.authored_scenario_id,
            value.authored_scenario_revision, value.registration_sha256)
        selected = registered['farm'].economic
        if (value.scenario_id, value.scenario_revision, value.scenario_sha256, value.candidate_id) != (
                selected.scenario_id, selected.revision, selected.sha256, selected.candidate_id):
            raise ValueError()
        report = completion.stored['report']
        context = registered['binding']
        if any(report[key] != context[key] for key in ('decision_context_id', 'context_sha256')):
            raise ValueError()
        binding = {
            'authored_scenario_id': value.authored_scenario_id,
            'authored_scenario_revision': value.authored_scenario_revision,
            'registration_sha256': value.registration_sha256,
            'authored_bindings_sha256': sha256(canonical_input_bytes(context)).hexdigest(),
            'numeric_input_sha256': sha256(registered['numeric_input_bytes']).hexdigest(),
            'release_sha256': report['release_sha256'],
            'thermal_job_id': value.thermal_job_id,
            'thermal_input_sha256': completion.input_sha256,
            'thermal_receipt_sha256': sha256(canonical_input_bytes(completion.receipt)).hexdigest(),
            'thermal_report_sha256': sha256(completion.stored['report_raw']).hexdigest(),
            'thermal_run_id': completion.summary['run_id'],
        }
        return binding, completion
    except PermissionError:
        raise
    except Exception:
        raise AuthoredEconomicHold('authored economic selection or completion unavailable') from None
    finally:
        guard()
