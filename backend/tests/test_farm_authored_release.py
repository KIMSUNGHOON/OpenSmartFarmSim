"""Synthetic reviewer keys prove release packet binding, not independent G1."""

from datetime import datetime, timedelta, timezone
from hashlib import sha256
from pathlib import Path
import sys

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.execution_attestation import ExecutionAttestationStore
from app.execution_verifier import ExecutionVerifier
from app.farm_authored_release import (AuthoredReleaseVerifier,
    AuthoredReleaseHold, DOMAIN, KINDS, REQUIRED_CODE)
from app.farm_authored_review_completion import (AuthoredReviewCompletion,
    AuthoredReviewCompletionVerifier)
from app.jobs import canonical_input_bytes


ROOT = Path(__file__).resolve().parents[2]


def _public(private):
    return private.public_key().public_bytes(serialization.Encoding.Raw,
                                              serialization.PublicFormat.Raw)


def _iso(moment):
    return moment.isoformat(timespec='microseconds').replace('+00:00', 'Z')


def _fixture(tmp_path):
    for name in (*REQUIRED_CODE, 'contracts/thermal-v1.schema.json',
                 'backend/pyproject.toml', 'backend/uv.lock'):
        target = tmp_path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((ROOT / name).read_bytes())
    observer = Ed25519PrivateKey.generate()
    reviewer = Ed25519PrivateKey.generate()
    execution = ExecutionVerifier(
        ExecutionAttestationStore(object(), {'observer': _public(observer)}),
        executable_sha256='1' * 64, environment_sha256='2' * 64)
    completion = object.__new__(AuthoredReviewCompletionVerifier)
    completion.execution_verifier = execution
    proof = AuthoredReviewCompletion(
        tenant_id='tenant-1', review_job_id='11111111-1111-4111-8111-111111111111',
        review_input_sha256='3' * 64, registration_sha256='4' * 64,
        farm_sha256='a' * 64, numeric_input_sha256='b' * 64,
        rights_declaration_sha256='c' * 64, binding_sha256='d' * 64,
        base_snapshot_id='base-snapshot', base_source_sha256='e' * 64,
        decision_context_id='context-id', context_sha256='5' * 64,
        decision_at_utc=_iso(datetime.now(timezone.utc) - timedelta(hours=2)),
        claim_mode='ex_post_replay', decision_time_kind='hypothetical',
        candidate_id='authored-candidate', code_sha256='6' * 64,
        trace_sha256=('7' * 64, '8' * 64), artifact_sha256='9' * 64,
        decision_id='22222222-2222-4222-8222-222222222222',
        capture_id='33333333-3333-4333-8333-333333333333', attempt=1,
        decision_recorded_at_utc=_iso(datetime.now(timezone.utc) - timedelta(hours=1)))
    completion.verify = lambda *args: proof
    artifacts = {f'evidence-{kind}': kind.encode() for kind in KINDS}
    service = AuthoredReleaseVerifier(completion, tmp_path,
        {'reviewer-key': ('separate synthetic reviewer', _public(reviewer))},
        lambda tenant, ref: artifacts.get(ref) if tenant == 'tenant-1' else None)
    return service, proof, reviewer, artifacts, observer


def _signed(service, proof, private):
    request = service.prepare(proof.tenant_id, proof.review_job_id,
                              proof.registration_sha256)
    request_sha = sha256(request).hexdigest()
    reports = {kind: canonical_input_bytes({
        'report_version': 'farm-authored-review-report-v1',
        'request_sha256': request_sha, 'kind': kind, 'verdict': 'pass',
        'method': 'Synthetic independent test inspection.',
        'evidence_refs': [{'id': f'evidence-{kind}',
            'sha256': sha256(kind.encode()).hexdigest()}]}) for kind in KINDS}
    reviewed_at = _iso(datetime.now(timezone.utc) - timedelta(minutes=20))
    evidence = canonical_input_bytes({
        'evidence_version': 'farm-authored-review-evidence-v1',
        'request_sha256': request_sha, 'key_id': 'reviewer-key',
        'reviewer': 'separate synthetic reviewer',
        'reviewed_at_utc': reviewed_at,
        'checks': {kind: sha256(raw).hexdigest() for kind, raw in reports.items()}})
    release = canonical_input_bytes({
        'release_version': 'farm-authored-release-v1',
        'scope': 'synthetic_software_only', 'request_sha256': request_sha,
        'evidence_sha256': sha256(evidence).hexdigest(), 'key_id': 'reviewer-key',
        'reviewer': 'separate synthetic reviewer', 'reviewed_at_utc': reviewed_at,
        'issued_at_utc': _iso(datetime.now(timezone.utc) - timedelta(minutes=10))})
    return release, private.sign(DOMAIN + release), evidence, reports


def test_release_binds_completed_review_code_reports_and_separate_key(tmp_path):
    service, proof, reviewer, artifacts, observer = _fixture(tmp_path)
    packet = _signed(service, proof, reviewer)
    verified = service.verify('tenant-1', proof.review_job_id,
                              proof.registration_sha256, *packet)
    assert verified.release_sha256 == sha256(packet[0]).hexdigest()
    assert verified.request_raw == service.prepare('tenant-1', proof.review_job_id,
                                                   proof.registration_sha256)
    with pytest.raises(AuthoredReleaseHold):
        service.verify('tenant-1', proof.review_job_id, '0' * 64, *packet)
    with pytest.raises(AuthoredReleaseHold):
        service.verify('tenant-1', proof.review_job_id,
                       proof.registration_sha256, packet[0], b'0' * 64,
                       packet[2], packet[3])
    changed_reports = dict(packet[3])
    changed_reports['numeric_recalculation'] += b' '
    with pytest.raises(AuthoredReleaseHold):
        service.verify('tenant-1', proof.review_job_id,
                       proof.registration_sha256, packet[0], packet[1],
                       packet[2], changed_reports)
    artifacts.pop('evidence-runtime_custody')
    with pytest.raises(AuthoredReleaseHold):
        service.verify('tenant-1', proof.review_job_id,
                       proof.registration_sha256, *packet)
    artifacts['evidence-runtime_custody'] = b'runtime_custody'
    path = tmp_path / 'backend/app/farm_authored_review_completion.py'
    path.write_bytes(path.read_bytes() + b'\n# changed deployment code\n')
    with pytest.raises(AuthoredReleaseHold):
        service.verify('tenant-1', proof.review_job_id,
                       proof.registration_sha256, *packet)
    with pytest.raises(AuthoredReleaseHold):
        AuthoredReleaseVerifier(service.completion, tmp_path,
            {'observer': ('same execution signer', _public(observer))},
            lambda *_: b'evidence')
