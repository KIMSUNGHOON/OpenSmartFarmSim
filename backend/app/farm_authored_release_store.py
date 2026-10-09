"""Immutable tenant-scoped custody for externally signed authored release packets."""

from datetime import timezone
from hashlib import sha256
import json

from psycopg import sql

from .farm_authored_release import (AuthoredReleaseVerifier, KINDS,
    VerifiedAuthoredRelease)


class AuthoredReleaseStoreHold(ValueError):
    pass


class AuthoredReleaseConflict(AuthoredReleaseStoreHold):
    pass


def install_authored_release_schema(conn, schema):
    """Owner-run additive install after the durable job table."""
    namespace = sql.Identifier(schema)
    conn.execute(sql.SQL("""
        CREATE TABLE {}.authored_release_packets (
            tenant_id text NOT NULL CHECK (length(tenant_id) BETWEEN 1 AND 200),
            review_job_id uuid NOT NULL,
            registration_sha256 char(64) NOT NULL,
            request_raw bytea NOT NULL CHECK (octet_length(request_raw) BETWEEN 1 AND 65536),
            request_sha256 char(64) NOT NULL,
            release_raw bytea NOT NULL CHECK (octet_length(release_raw) BETWEEN 1 AND 65536),
            release_sha256 char(64) NOT NULL,
            signature bytea NOT NULL CHECK (octet_length(signature) = 64),
            evidence_raw bytea NOT NULL CHECK (octet_length(evidence_raw) BETWEEN 1 AND 65536),
            evidence_sha256 char(64) NOT NULL,
            source_report_raw bytea NOT NULL CHECK (octet_length(source_report_raw) BETWEEN 1 AND 65536),
            source_report_sha256 char(64) NOT NULL,
            numeric_report_raw bytea NOT NULL CHECK (octet_length(numeric_report_raw) BETWEEN 1 AND 65536),
            numeric_report_sha256 char(64) NOT NULL,
            runtime_report_raw bytea NOT NULL CHECK (octet_length(runtime_report_raw) BETWEEN 1 AND 65536),
            runtime_report_sha256 char(64) NOT NULL,
            reviewer text NOT NULL CHECK (length(reviewer) BETWEEN 1 AND 200),
            issued_at_utc timestamptz NOT NULL,
            recorded_at timestamptz NOT NULL DEFAULT clock_timestamp(),
            PRIMARY KEY (tenant_id, review_job_id),
            FOREIGN KEY (tenant_id, review_job_id)
                REFERENCES {}.jobs (tenant_id, job_id),
            CHECK ((registration_sha256 = convert_from(request_raw, 'UTF8')::jsonb#>>
                '{{completion,registration_sha256}}') IS TRUE),
            CHECK ((review_job_id::text = convert_from(request_raw, 'UTF8')::jsonb#>>
                '{{completion,review_job_id}}') IS TRUE),
            CHECK ((tenant_id = convert_from(request_raw, 'UTF8')::jsonb#>>
                '{{completion,tenant_id}}') IS TRUE),
            CHECK ((convert_from(request_raw, 'UTF8')::jsonb->>'request_version' =
                'farm-authored-release-request-v1') IS TRUE),
            CHECK (request_sha256 = encode(sha256(request_raw), 'hex')),
            CHECK (release_sha256 = encode(sha256(release_raw), 'hex')),
            CHECK (evidence_sha256 = encode(sha256(evidence_raw), 'hex')),
            CHECK (source_report_sha256 = encode(sha256(source_report_raw), 'hex')),
            CHECK (numeric_report_sha256 = encode(sha256(numeric_report_raw), 'hex')),
            CHECK (runtime_report_sha256 = encode(sha256(runtime_report_raw), 'hex')),
            CHECK ((request_sha256 = convert_from(release_raw, 'UTF8')::jsonb->>'request_sha256') IS TRUE),
            CHECK ((evidence_sha256 = convert_from(release_raw, 'UTF8')::jsonb->>'evidence_sha256') IS TRUE),
            CHECK ((reviewer = convert_from(release_raw, 'UTF8')::jsonb->>'reviewer') IS TRUE),
            CHECK ((convert_from(release_raw, 'UTF8')::jsonb->>'release_version' =
                'farm-authored-release-v1') IS TRUE),
            CHECK ((issued_at_utc = (convert_from(release_raw, 'UTF8')::jsonb->>'issued_at_utc')::timestamptz) IS TRUE),
            CHECK (recorded_at >= issued_at_utc),
            CHECK ((source_report_sha256 = convert_from(evidence_raw, 'UTF8')::jsonb#>>
                '{{checks,source_rights_qc}}') IS TRUE),
            CHECK ((numeric_report_sha256 = convert_from(evidence_raw, 'UTF8')::jsonb#>>
                '{{checks,numeric_recalculation}}') IS TRUE),
            CHECK ((runtime_report_sha256 = convert_from(evidence_raw, 'UTF8')::jsonb#>>
                '{{checks,runtime_custody}}') IS TRUE),
            CHECK ((convert_from(evidence_raw, 'UTF8')::jsonb->>'evidence_version' =
                'farm-authored-review-evidence-v1') IS TRUE)
        )
    """).format(namespace, namespace))
    conn.execute(sql.SQL("""
        CREATE FUNCTION {}.reject_authored_release_change()
        RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN RAISE EXCEPTION 'authored release packet is immutable'; END $$
    """).format(namespace))
    conn.execute(sql.SQL("""
        CREATE TRIGGER authored_release_immutable BEFORE UPDATE OR DELETE
        ON {}.authored_release_packets FOR EACH ROW
        EXECUTE FUNCTION {}.reject_authored_release_change()
    """).format(namespace, namespace))


class AuthoredReleaseStore:
    """Store verified packets; current rights and runtime bytes still gate reads."""

    def __init__(self, verifier):
        if type(verifier) is not AuthoredReleaseVerifier or not hasattr(
                verifier.completion, 'jobs'):
            raise AuthoredReleaseStoreHold('release authority unavailable')
        self.verifier = verifier
        self.jobs = verifier.completion.jobs

    def _table(self):
        return self.jobs._table('authored_release_packets')

    def _scope(self, tenant, kind):
        if not self.jobs._has_scope(tenant, kind):
            raise AuthoredReleaseStoreHold('authored release access unavailable')

    @staticmethod
    def _same(row, verified, registration_sha256):
        raws = (verified.request_raw, verified.release_raw,
                verified.evidence_raw, *verified.reports)
        names = ('request', 'release', 'evidence', 'source_report',
                 'numeric_report', 'runtime_report')
        return (row['registration_sha256'] == registration_sha256 and
                row['reviewer'] == verified.reviewer and
                row['recorded_at'] >= row['issued_at_utc'] and
                row['issued_at_utc'].astimezone(timezone.utc).isoformat(
                    timespec='microseconds').replace(
                    '+00:00', 'Z') == verified.issued_at_utc and
                row['signature'] == verified.signature and
                all(row[name + '_raw'] == raw and
                    row[name + '_sha256'] == sha256(raw).hexdigest()
                    for name, raw in zip(names, raws, strict=True)))

    def put(self, tenant, review_job_id, registration_sha256,
            release_raw, signature, evidence_raw, report_raws):
        self._scope(tenant, 'authored_release_write')
        verified = self.verifier.verify(tenant, review_job_id, registration_sha256,
                                        release_raw, signature, evidence_raw, report_raws)
        raws = (verified.request_raw, verified.release_raw,
                verified.evidence_raw, *verified.reports)
        try:
            with self.jobs.connect() as conn:
                job = conn.execute(sql.SQL("""
                    SELECT stage, state, input_sha256 FROM {} WHERE tenant_id=%s AND job_id=%s
                """).format(self.jobs._table('jobs')), (tenant, review_job_id)).fetchone()
                if (job is None or job['stage'] != 'collection_review' or
                        job['state'] != 'succeeded' or
                        job['input_sha256'] != json.loads(verified.request_raw)
                            ['completion']['review_input_sha256']):
                    raise AuthoredReleaseStoreHold('completed review job unavailable')
                conn.execute(sql.SQL("""
                    INSERT INTO {} (tenant_id, review_job_id, registration_sha256,
                        request_raw, request_sha256, release_raw, release_sha256, signature,
                        evidence_raw, evidence_sha256, source_report_raw, source_report_sha256,
                        numeric_report_raw, numeric_report_sha256,
                        runtime_report_raw, runtime_report_sha256, reviewer, issued_at_utc)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    ON CONFLICT DO NOTHING
                """).format(self._table()),
                    (tenant, review_job_id, registration_sha256,
                     raws[0], sha256(raws[0]).hexdigest(),
                     raws[1], sha256(raws[1]).hexdigest(), verified.signature,
                     raws[2], sha256(raws[2]).hexdigest(),
                     raws[3], sha256(raws[3]).hexdigest(),
                     raws[4], sha256(raws[4]).hexdigest(),
                     raws[5], sha256(raws[5]).hexdigest(),
                     verified.reviewer, verified.issued_at_utc))
                row = conn.execute(sql.SQL("""
                    SELECT * FROM {} WHERE tenant_id=%s AND review_job_id=%s
                """).format(self._table()), (tenant, review_job_id)).fetchone()
                if row is None or not self._same(row, verified, registration_sha256):
                    raise AuthoredReleaseConflict('conflicting authored release bytes')
            return verified
        except AuthoredReleaseStoreHold:
            raise
        except Exception:
            raise AuthoredReleaseStoreHold('authored release storage unavailable') from None

    def get(self, tenant, review_job_id, registration_sha256):
        self._scope(tenant, 'authored_release_read')
        try:
            with self.jobs.connect() as conn:
                row = conn.execute(sql.SQL("""
                    SELECT * FROM {} WHERE tenant_id=%s AND review_job_id=%s
                """).format(self._table()), (tenant, review_job_id)).fetchone()
            if row is None or row['registration_sha256'] != registration_sha256:
                return None
            reports = dict(zip(KINDS, (row['source_report_raw'],
                row['numeric_report_raw'], row['runtime_report_raw']), strict=True))
            verified = self.verifier.verify(tenant, review_job_id, registration_sha256,
                row['release_raw'], row['signature'], row['evidence_raw'], reports)
            if not self._same(row, verified, registration_sha256):
                raise AuthoredReleaseStoreHold('stored authored release differs')
            return verified
        except AuthoredReleaseStoreHold:
            raise
        except Exception:
            raise AuthoredReleaseStoreHold('authored release read unavailable') from None
