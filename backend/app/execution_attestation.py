"""Signed CLI completion evidence; deployment owns the observer and private key."""

from datetime import datetime, timedelta
from hashlib import sha256
import json
import re
from typing import Literal
from uuid import UUID

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from pydantic import BaseModel, ConfigDict, Field, StrictInt, field_validator, model_validator
from psycopg import sql


DOMAIN = b"ossf-cli-execution-attestation-v1\0"
HEX = re.compile(r"[0-9a-f]{64}\Z")
KEY_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,63}\Z")
USAGE_KEYS = frozenset({"input_tokens", "output_tokens", "total_tokens",
                        "cached_input_tokens", "cache_write_input_tokens",
                        "reasoning_output_tokens"})


def _pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            raise ValueError("duplicate attestation JSON key")
        result[key] = value
    return result


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


class ExecutionAttestation(BaseModel):
    """A supervisor observation, never a caller-provided gate decision."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    record_version: Literal["cli-execution-attestation-v1"]
    key_id: str = Field(min_length=1, max_length=64)
    tenant_id: str = Field(min_length=1, max_length=200)
    job_id: UUID
    attempt: StrictInt = Field(ge=1)
    attempt_id: UUID
    nonce: UUID
    input_sha256: str
    prompt_sha256: str
    schema_sha256: str
    cli_version: str
    executable_sha256: str
    argv: list[str] = Field(min_length=1, max_length=32)
    environment_sha256: str
    launch_id: UUID
    capture_id: UUID
    jsonl_sha256: str
    final_output_sha256: str
    process_id: StrictInt = Field(gt=0)
    process_start_token: str = Field(min_length=1, max_length=128)
    started_at_utc: datetime
    ended_at_utc: datetime
    signed_at_utc: datetime
    exit_code: Literal[0]
    termination_reason: Literal["completed"]
    usage: dict[str, StrictInt]

    @field_validator("key_id")
    @classmethod
    def valid_key_id(cls, value):
        if not KEY_ID.fullmatch(value):
            raise ValueError("invalid attestation key ID")
        return value

    @field_validator("input_sha256", "prompt_sha256", "schema_sha256",
                     "executable_sha256", "environment_sha256",
                     "jsonl_sha256", "final_output_sha256")
    @classmethod
    def valid_digest(cls, value):
        if not HEX.fullmatch(value):
            raise ValueError("invalid attestation digest")
        return value

    @field_validator("cli_version")
    @classmethod
    def valid_cli_version(cls, value):
        if not re.fullmatch(r"codex-cli [0-9]+\.[0-9]+\.[0-9]+", value):
            raise ValueError("invalid attested CLI version")
        return value

    @field_validator("argv")
    @classmethod
    def valid_argv(cls, value):
        if any(type(arg) is not str or not arg or len(arg) > 1000 for arg in value):
            raise ValueError("invalid attested argv")
        return value

    @field_validator("usage")
    @classmethod
    def valid_usage(cls, value):
        if (not {"input_tokens", "output_tokens"} <= set(value) or
                not set(value) <= USAGE_KEYS or
                any(type(count) is not int or count < 0 for count in value.values())):
            raise ValueError("invalid attested usage")
        return value

    @model_validator(mode="after")
    def valid_times(self):
        times = (self.started_at_utc, self.ended_at_utc, self.signed_at_utc)
        if (any(value.utcoffset() != timedelta(0) for value in times) or
                not times[0] <= times[1] <= times[2] or self.nonce.version != 4):
            raise ValueError("invalid attestation chronology or nonce")
        return self


def encode_attestation(value: ExecutionAttestation) -> bytes:
    if not isinstance(value, ExecutionAttestation):
        raise ValueError("attestation model required")
    raw = _canonical(value.model_dump(mode="json"))
    if len(raw) > 16384:
        raise ValueError("attestation too large")
    if _canonical(ExecutionAttestation.model_validate_json(raw).model_dump(mode="json")) != raw:
        raise ValueError("attestation normalized differently")
    return raw


def decode_attestation(raw: bytes) -> ExecutionAttestation:
    if type(raw) is not bytes or not 1 <= len(raw) <= 16384:
        raise ValueError("attestation bytes invalid")
    value = json.loads(raw.decode("utf-8"), object_pairs_hook=_pairs,
                       parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
    if type(value) is not dict or _canonical(value) != raw:
        raise ValueError("attestation is not canonical JSON")
    for name in ("started_at_utc", "ended_at_utc", "signed_at_utc"):
        if type(value.get(name)) is not str or not value[name].endswith("Z"):
            raise ValueError("attestation timestamp is not UTC Z")
    record = ExecutionAttestation.model_validate_json(raw)
    if encode_attestation(record) != raw:
        raise ValueError("attestation normalized differently")
    return record


def verify_signature(raw: bytes, signature: bytes, public_keys: dict[str, bytes]):
    record = decode_attestation(raw)
    key = public_keys.get(record.key_id)
    if type(key) is not bytes or len(key) != 32 or type(signature) is not bytes or len(signature) != 64:
        raise ValueError("attestation key or signature unavailable")
    try:
        Ed25519PublicKey.from_public_bytes(key).verify(signature, DOMAIN + raw)
    except InvalidSignature as exc:
        raise ValueError("attestation signature invalid") from exc
    return record


def install_execution_attestation_schema(conn, schema):
    """Owner-only installation after the durable job schema."""
    namespace = sql.Identifier(schema)
    conn.execute(sql.SQL("""
        CREATE TABLE {}.execution_attestations (
            tenant_id text NOT NULL, job_id uuid NOT NULL, attempt integer NOT NULL,
            attempt_id uuid NOT NULL, nonce uuid NOT NULL UNIQUE,
            capture_id uuid NOT NULL, key_id text NOT NULL,
            raw bytea NOT NULL CHECK (octet_length(raw) BETWEEN 1 AND 16384),
            raw_sha256 char(64) NOT NULL CHECK (raw_sha256 = encode(sha256(raw), 'hex')),
            signature bytea NOT NULL CHECK (octet_length(signature) = 64),
            stored_at timestamptz NOT NULL DEFAULT clock_timestamp(),
            PRIMARY KEY (tenant_id, job_id, attempt),
            FOREIGN KEY (tenant_id, job_id, attempt, attempt_id)
                REFERENCES {}.job_attempts (tenant_id, job_id, attempt, attempt_id),
            CHECK ((convert_from(raw, 'UTF8')::jsonb->>'tenant_id' = tenant_id) IS TRUE),
            CHECK ((convert_from(raw, 'UTF8')::jsonb->>'job_id' = job_id::text) IS TRUE),
            CHECK ((convert_from(raw, 'UTF8')::jsonb->>'attempt' = attempt::text) IS TRUE),
            CHECK ((convert_from(raw, 'UTF8')::jsonb->>'attempt_id' = attempt_id::text) IS TRUE),
            CHECK ((convert_from(raw, 'UTF8')::jsonb->>'nonce' = nonce::text) IS TRUE),
            CHECK ((convert_from(raw, 'UTF8')::jsonb->>'capture_id' = capture_id::text) IS TRUE),
            CHECK ((convert_from(raw, 'UTF8')::jsonb->>'key_id' = key_id) IS TRUE)
        )
    """).format(namespace, namespace))
    conn.execute(sql.SQL("""
        CREATE FUNCTION {}.reject_execution_attestation_change()
        RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN RAISE EXCEPTION 'execution attestation is immutable'; END $$
    """).format(namespace))
    conn.execute(sql.SQL("""
        CREATE TRIGGER execution_attestation_immutable BEFORE UPDATE OR DELETE
        ON {}.execution_attestations FOR EACH ROW
        EXECUTE FUNCTION {}.reject_execution_attestation_change()
    """).format(namespace, namespace))


class ExecutionAttestationStore:
    """Software candidate; DB roles and signer process are deployment evidence."""

    def __init__(self, job_store, public_keys: dict[str, bytes]):
        if not public_keys or any(type(key) is not str or type(value) is not bytes or
                                  len(value) != 32 for key, value in public_keys.items()):
            raise ValueError("trusted attestation public keys required")
        self.job_store = job_store
        self.public_keys = dict(public_keys)

    def _table(self):
        return self.job_store._table("execution_attestations")

    def put(self, raw: bytes, signature: bytes):
        record = verify_signature(raw, signature, self.public_keys)
        with self.job_store.connect() as conn:
            conn.execute(sql.SQL("""
                INSERT INTO {} (tenant_id, job_id, attempt, attempt_id,
                    nonce, capture_id, key_id, raw, raw_sha256, signature)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING
            """).format(self._table()),
                (record.tenant_id, record.job_id, record.attempt, record.attempt_id,
                 record.nonce, record.capture_id, record.key_id, raw,
                 sha256(raw).hexdigest(), signature))
            row = conn.execute(sql.SQL("""
                SELECT * FROM {} WHERE tenant_id=%s AND job_id=%s AND attempt=%s
            """).format(self._table()),
                (record.tenant_id, record.job_id, record.attempt)).fetchone()
            if row is None or row["raw"] != raw or row["signature"] != signature:
                raise ValueError("attestation immutable pin conflict")
        return record

    def get(self, tenant, job_id, attempt):
        with self.job_store.connect() as conn:
            row = conn.execute(sql.SQL("""
                SELECT * FROM {} WHERE tenant_id=%s AND job_id=%s AND attempt=%s
            """).format(self._table()), (tenant, job_id, attempt)).fetchone()
        if row is None:
            return None
        if sha256(row["raw"]).hexdigest() != row["raw_sha256"]:
            raise ValueError("attestation stored digest differs")
        record = verify_signature(row["raw"], row["signature"], self.public_keys)
        if (record.tenant_id, record.job_id, record.attempt, record.attempt_id,
            record.nonce, record.capture_id, record.key_id) != (
                row["tenant_id"], row["job_id"], row["attempt"], row["attempt_id"],
                row["nonce"], row["capture_id"], row["key_id"]):
            raise ValueError("attestation stored identity differs")
        return record
