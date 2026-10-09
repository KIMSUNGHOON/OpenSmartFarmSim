"""Immutable source metadata and raw-byte integrity contract."""

from datetime import datetime, timedelta
from hashlib import sha256
import json
import re
from typing import Annotated, Literal, Self
from urllib.parse import unquote, urlsplit

from pydantic import AfterValidator, BaseModel, ConfigDict, StringConstraints, field_validator, model_validator


def _exact_name(value: str) -> str:
    if not value or value != value.strip() or any(ord(char) < 32 for char in value):
        raise ValueError("identifier must be nonempty and have no surrounding whitespace or controls")
    return value


Name = Annotated[str, AfterValidator(_exact_name)]
Digest = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]
TimeSemantics = Literal["instant", "mean", "interval_total", "unknown"]
RightAction = Literal["access", "store", "transform", "display", "redistribute"]


class FrozenContract(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", strict=True, hide_input_in_errors=True)


def _utc(value: datetime | None) -> datetime | None:
    if value is not None and value.utcoffset() != timedelta(0):
        raise ValueError("time must be UTC-aware")
    return value


class SourceScope(FrozenContract):
    provider: Name
    product_id: Name
    product_version: Name
    source_url: str
    station_or_grid_id: Name | None

    @field_validator("source_url")
    @classmethod
    def safe_source_url(cls, value: str) -> str:
        if any(char.isspace() or ord(char) < 32 for char in value) or "?" in value or "#" in value:
            raise ValueError("source URL must have no query, fragment, or credentials")
        parts = urlsplit(value)
        if parts.scheme not in ("http", "https") or not parts.hostname or "@" in parts.netloc:
            raise ValueError("source URL must be an HTTP(S) URL without credentials")
        _ = parts.port
        path = unquote(parts.path).lower()
        if (any(char.isspace() or ord(char) < 32 for char in path) or
                "?" in path or "#" in path or re.search(r"%[0-9a-f]{2}", path)):
            raise ValueError("source URL path must not contain encoded delimiters or controls")
        if re.search(r"(?:^|/)(?:api[-_]?key|access[-_]?key|token|secret|password|credential|authorization|auth|signature|bearer)(?:[/:=]|$)", path) or re.search(r"(?:^|/)(?:sk-|ghp_|xox[baprs]-)[^/]+", path):
            raise ValueError("source URL path may contain credentials")
        return value


class RequestDetail(FrozenContract):
    name: Name
    value: str

    @field_validator("name")
    @classmethod
    def no_secret_parameter(cls, value: str) -> str:
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]*", value):
            raise ValueError("request detail name must be a simple parameter name")
        compact = re.sub(r"[^a-z0-9]", "", value.lower())
        if any(word in compact for word in ("apikey", "accesskey", "token", "secret", "password", "credential", "signature", "authorization", "auth", "cookie")):
            raise ValueError("credential-bearing request detail name is not permitted")
        return value

    @field_validator("value")
    @classmethod
    def no_obvious_secret_value(cls, value: str) -> str:
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}", value):
            raise ValueError("request detail value must be a short canonical scalar")
        if re.search(r"(?:^|[._:-])(?:bearer|token|secret|password|apikey|api_key|credential|auth)(?:$|[._:-])", value, re.I) or re.match(r"(?:sk-|ghp_|xox[baprs]-)", value, re.I):
            raise ValueError("credential-like request detail value is not permitted")
        return value


class Variable(FrozenContract):
    name: Name
    original_unit: Name | None
    time_semantics: TimeSemantics
    interval_start: datetime | None = None
    interval_end: datetime | None = None
    provider_qc_status: Literal["passed", "failed", "unknown", "not_supplied"]
    provider_qc_value: Name | None

    @field_validator("interval_start", "interval_end")
    @classmethod
    def utc_interval(cls, value: datetime | None) -> datetime | None:
        return _utc(value)

    @model_validator(mode="after")
    def coherent_variable(self) -> Self:
        if (self.interval_start is None) != (self.interval_end is None):
            raise ValueError("both interval bounds must be supplied together")
        if self.interval_start is not None and self.interval_start >= self.interval_end:
            raise ValueError("interval end must follow start")
        if self.time_semantics == "instant" and self.interval_start is not None:
            raise ValueError("instant value cannot have an interval")
        if self.provider_qc_status == "not_supplied" and self.provider_qc_value is not None:
            raise ValueError("not-supplied provider QC cannot have a raw value")
        if self.provider_qc_status != "not_supplied" and self.provider_qc_value is None:
            raise ValueError("supplied provider QC needs its raw value")
        return self


class ProjectCheck(FrozenContract):
    variable: Name
    name: Name
    version: Name
    status: Literal["passed", "failed", "unknown"]
    evidence_id: Name | None
    reviewer: Name | None


class Right(FrozenContract):
    action: RightAction
    status: Literal["allowed", "denied", "unknown"]
    evidence_id: Name | None
    reviewer: Name | None


class SourceRecord(FrozenContract):
    schema_version: Literal["1"]
    record_id: Name
    scope: SourceScope
    revision_id: Name
    request_details: tuple[RequestDetail, ...]
    observed_at: datetime | None
    published_at: datetime | None
    available_at: datetime | None
    retrieved_at: datetime
    valid_from: datetime | None
    valid_to: datetime | None
    variables: tuple[Variable, ...]
    project_checks: tuple[ProjectCheck, ...]
    rights: tuple[Right, ...]
    raw_sha256: Digest
    synthetic: bool
    synthetic_author: Name | None
    synthetic_method: Name | None
    source_reviewer: Name | None
    source_evidence_id: Name | None

    @field_validator("observed_at", "published_at", "available_at", "retrieved_at", "valid_from", "valid_to")
    @classmethod
    def utc_record_time(cls, value: datetime | None) -> datetime | None:
        return _utc(value)

    @model_validator(mode="after")
    def coherent_record(self) -> Self:
        for keys in (
            [v.name for v in self.variables],
            [(c.variable, c.name) for c in self.project_checks],
            [r.action for r in self.rights],
            [d.name for d in self.request_details],
        ):
            if len(keys) != len(set(keys)):
                raise ValueError("duplicate source metadata entry")
        if (self.valid_from is None) != (self.valid_to is None):
            raise ValueError("both validity bounds must be supplied together")
        if self.valid_from is not None and self.valid_from >= self.valid_to:
            raise ValueError("validity end must follow start")
        for time in (self.observed_at, self.published_at, self.available_at):
            if time is not None and time > self.retrieved_at:
                raise ValueError("observation, publication, and availability cannot follow retrieval")
        if self.published_at is not None and self.available_at is not None and self.available_at < self.published_at:
            raise ValueError("availability cannot precede publication")
        if self.synthetic and (self.synthetic_author is None or self.synthetic_method is None):
            raise ValueError("synthetic source needs author and generation method")
        if not self.synthetic and (self.synthetic_author is not None or self.synthetic_method is not None):
            raise ValueError("real source cannot have synthetic generation metadata")
        if self.record_id != self.content_id():
            raise ValueError("record ID must bind canonical metadata and raw digest")
        return self

    def content_id(self) -> str:
        metadata = self.model_dump(mode="json", exclude={"record_id"})
        canonical = json.dumps(metadata, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        return sha256(canonical.encode("utf-8")).hexdigest()


def verify_raw_hash(record: SourceRecord, raw_bytes: bytes) -> bool:
    """Compare the stored digest with the exact, unmodified response bytes."""
    return sha256(raw_bytes).hexdigest() == record.raw_sha256
