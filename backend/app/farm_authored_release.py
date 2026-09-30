"""Verify a separate reviewer's signed release of authored farm input evidence."""

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import re

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from .farm_authored_review_completion import (AuthoredReviewCompletion,
    AuthoredReviewCompletionVerifier)
from .jobs import canonical_input_bytes


DOMAIN = b'ossf-farm-authored-release-v1\0'
HEX = re.compile(r'[0-9a-f]{64}\Z')
KEY_ID = re.compile(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,63}\Z')
KINDS = ('source_rights_qc', 'numeric_recalculation', 'runtime_custody')
REQUIRED_CODE = frozenset({
    'backend/app/farm_authored_release.py',
    'backend/app/farm_authored_release_store.py',
    'backend/app/farm_authored_run.py',
    'backend/app/farm_authored_run_store.py',
    'backend/app/farm_authored_simulation.py',
    'backend/app/farm_authored_review_completion.py',
    'backend/app/farm_authored_review.py',
    'backend/app/farm_authoring_storage.py',
    'backend/app/authored_thermal_candidate.py',
    'backend/app/farm_input_compiler.py',
    'backend/app/farm_inputs.py',
    'backend/app/thermal.py',
    'backend/app/thermal_units.py',
    'backend/app/execution_verifier.py',
    'backend/app/execution_attestation.py',
})


class AuthoredReleaseHold(ValueError):
    pass


def _need(condition):
    if not condition:
        raise AuthoredReleaseHold('independent authored release unavailable')


def _pairs(items):
    value = {}
    for key, item in items:
        _need(key not in value)
        value[key] = item
    return value


def _parse(raw, limit=65536):
    _need(type(raw) is bytes and 1 <= len(raw) <= limit)
    value = json.loads(raw.decode('utf-8'), object_pairs_hook=_pairs,
        parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
    _need(type(value) is dict and canonical_input_bytes(value) == raw)
    return value


def _time(value):
    _need(type(value) is str and value.endswith('Z'))
    moment = datetime.fromisoformat(value[:-1] + '+00:00')
    _need(moment.utcoffset().total_seconds() == 0 and
          moment.isoformat(timespec='microseconds').replace('+00:00', 'Z') == value)
    return moment


def _digest(raw):
    return sha256(raw).hexdigest()


def _runtime_manifest(root):
    root = Path(root).resolve()
    paths = tuple(sorted((*((root / 'backend/app').glob('*.py')),
                          *((root / 'contracts').glob('*.schema.json')))))
    code = {}
    for path in paths:
        _need(path.is_file() and not path.is_symlink())
        code[path.relative_to(root).as_posix()] = _digest(path.read_bytes())
    _need(REQUIRED_CODE <= set(code) and
          any(name.startswith('contracts/') for name in code))
    environment = {}
    for name in ('backend/pyproject.toml', 'backend/uv.lock'):
        path = root / name
        _need(path.is_file() and not path.is_symlink())
        environment[name] = _digest(path.read_bytes())
    return code, environment


@dataclass(frozen=True)
class VerifiedAuthoredRelease:
    request_raw: bytes
    release_raw: bytes
    signature: bytes
    evidence_raw: bytes
    reports: tuple[bytes, bytes, bytes]
    reviewer: str
    issued_at_utc: str

    @property
    def release_sha256(self):
        return _digest(self.release_raw)


class AuthoredReleaseVerifier:
    """Verify external release bytes; this service never signs or publishes a Run."""

    def __init__(self, completion, root, trusted_reviewers, evidence_resolver):
        if type(completion) is not AuthoredReviewCompletionVerifier:
            raise AuthoredReleaseHold('completed review authority required')
        execution_keys = completion.execution_verifier.store.public_keys
        if (type(trusted_reviewers) is not dict or not trusted_reviewers or
                any(type(key_id) is not str or not KEY_ID.fullmatch(key_id) or
                    type(pair) is not tuple or len(pair) != 2 or
                    type(pair[0]) is not str or not 1 <= len(pair[0]) <= 200 or
                    pair[0] == 'OpenSmartFarmSim fixture authors' or
                    type(pair[1]) is not bytes or len(pair[1]) != 32 or
                    key_id in execution_keys or pair[1] in execution_keys.values()
                    for key_id, pair in trusted_reviewers.items()) or
                not callable(evidence_resolver)):
            raise AuthoredReleaseHold('separate reviewer authority required')
        self.completion = completion
        self.root = Path(root)
        self.trusted_reviewers = dict(trusted_reviewers)
        self.evidence_resolver = evidence_resolver

    def prepare(self, tenant, review_job_id, expected_registration_sha256):
        proof = self.completion.verify(tenant, review_job_id,
                                       expected_registration_sha256)
        _need(type(proof) is AuthoredReviewCompletion and
              proof.tenant_id == tenant and
              proof.review_job_id == str(review_job_id) and
              proof.registration_sha256 == expected_registration_sha256 and
              proof.claim_mode == 'ex_post_replay')
        code, environment = _runtime_manifest(self.root)
        value = {'request_version': 'farm-authored-release-request-v1',
            'scope': 'synthetic_software_only',
            'completion': {**proof.__dict__,
                'trace_sha256': list(proof.trace_sha256),
                'proof_sha256': proof.proof_sha256},
            'runtime_code_files': code,
            'runtime_environment_files': environment,
            'cli_executable_sha256':
                self.completion.execution_verifier.executable_sha256,
            'cli_environment_sha256':
                self.completion.execution_verifier.environment_sha256,
            'pending_holds': ['authored_input_review', 'authored_snapshot_release']}
        return canonical_input_bytes(value)

    def verify(self, tenant, review_job_id, expected_registration_sha256,
               release_raw, signature, evidence_raw, report_raws):
        try:
            request_raw = self.prepare(tenant, review_job_id,
                                       expected_registration_sha256)
            request = _parse(request_raw)
            release = _parse(release_raw)
            evidence = _parse(evidence_raw)
            _need(set(release) == {'release_version', 'scope', 'request_sha256',
                'evidence_sha256', 'key_id', 'reviewer', 'reviewed_at_utc',
                'issued_at_utc'} and
                release['release_version'] == 'farm-authored-release-v1' and
                release['scope'] == request['scope'] and
                release['request_sha256'] == _digest(request_raw) and
                release['evidence_sha256'] == _digest(evidence_raw) and
                release['key_id'] in self.trusted_reviewers and
                release['reviewer'] == self.trusted_reviewers[release['key_id']][0] and
                type(signature) is bytes and len(signature) == 64)
            Ed25519PublicKey.from_public_bytes(
                self.trusted_reviewers[release['key_id']][1]).verify(
                    signature, DOMAIN + release_raw)
            reviewed_at = _time(release['reviewed_at_utc'])
            issued_at = _time(release['issued_at_utc'])
            _need(_time(request['completion']['decision_recorded_at_utc']) <=
                  reviewed_at <= issued_at <= datetime.now(timezone.utc))
            _need(set(evidence) == {'evidence_version', 'request_sha256',
                'key_id', 'reviewer', 'reviewed_at_utc', 'checks'} and
                evidence['evidence_version'] == 'farm-authored-review-evidence-v1' and
                all(evidence[key] == release[key] for key in
                    ('request_sha256', 'key_id', 'reviewer', 'reviewed_at_utc')) and
                type(evidence['checks']) is dict and
                set(evidence['checks']) == set(KINDS) and
                type(report_raws) is dict and set(report_raws) == set(KINDS))
            ordered = []
            for kind in KINDS:
                raw = report_raws[kind]
                report = _parse(raw)
                _need(type(evidence['checks'][kind]) is str and
                      HEX.fullmatch(evidence['checks'][kind]) and
                      evidence['checks'][kind] == _digest(raw) and
                      set(report) == {'report_version', 'request_sha256',
                          'kind', 'verdict', 'method', 'evidence_refs'} and
                      report['report_version'] == 'farm-authored-review-report-v1' and
                      report['request_sha256'] == _digest(request_raw) and
                      report['kind'] == kind and report['verdict'] == 'pass' and
                      type(report['method']) is str and 1 <= len(report['method']) <= 200 and
                      type(report['evidence_refs']) is list and
                      1 <= len(report['evidence_refs']) <= 32 and
                      all(type(ref) is dict and set(ref) == {'id', 'sha256'} and
                          type(ref['id']) is str and 1 <= len(ref['id']) <= 200 and
                          type(ref['sha256']) is str and HEX.fullmatch(ref['sha256'])
                          for ref in report['evidence_refs']))
                for ref in report['evidence_refs']:
                    artifact = self.evidence_resolver(tenant, ref['id'])
                    _need(type(artifact) is bytes and 1 <= len(artifact) <= 1048576 and
                          _digest(artifact) == ref['sha256'])
                ordered.append(raw)
            _need(request_raw == self.prepare(tenant, review_job_id,
                                              expected_registration_sha256))
            return VerifiedAuthoredRelease(request_raw, release_raw, signature,
                evidence_raw, tuple(ordered), release['reviewer'],
                release['issued_at_utc'])
        except Exception:
            raise AuthoredReleaseHold('independent authored release unavailable') from None
