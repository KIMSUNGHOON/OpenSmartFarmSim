"""Stable job vocabulary and validation shared by submission and workers."""

from hashlib import sha256
import json
import re


ACTIVE_BY_STAGE = {
    "research": "researching",
    "collection": "collecting",
    "collection_review": "reviewing",
    "simulation": "simulating",
    "assessment": "assessing",
}
DETERMINISTIC_STAGES = frozenset({"collection", "simulation"})
AI_STAGES = frozenset(ACTIVE_BY_STAGE) - DETERMINISTIC_STAGES
ACTIVE_STATES = frozenset(ACTIVE_BY_STAGE.values())
TERMINAL_STATES = frozenset({"succeeded", "hold", "failed", "canceled"})
FAILURE_KINDS = frozenset({"transient", "hold", "fatal"})
MAX_INPUT_BYTES = 64 * 1024
PUBLIC_MANIFEST_V1_CALLER_FIELDS = frozenset({"schema_version"})
_BLOCKED_INPUT_KEYS = frozenset({
    "secret", "clientsecret", "password", "passwd", "credential", "credentials",
    "apikey", "accesskey", "privatekey", "token", "accesstoken", "refreshtoken",
    "authtoken", "authorization", "cookie", "sessioncookie",
    "raw", "rawdata", "rawsource", "rawpayload", "rawrecord", "rawrecords",
    "sourcedata", "sourcetext", "sourcecontent", "sourcepayload", "sourcebody",
    "providerresponse", "documenttext", "documentcontent", "responsebody", "httpbody",
})
_BLOCKED_INPUT_KEY_MARKERS = re.compile(
    "password|secret|credential|apikey|accesskey|privatekey|accesstoken|"
    "refreshtoken|authtoken|bearertoken|authorization|cookie|rawdata|"
    "rawsource|rawpayload|rawrecord|rawcontent"
)


def _validate_input_fields(value: object) -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            if not isinstance(key, str):
                raise ValueError("input field names must be strings")
            if key == "raw_sha256" and type(nested) is str and re.fullmatch(r"[0-9a-f]{64}", nested):
                continue
            normalized = re.sub(r"[^a-z0-9]", "", key.casefold())
            if (normalized in _BLOCKED_INPUT_KEYS or normalized.startswith("raw")
                or _BLOCKED_INPUT_KEY_MARKERS.search(normalized)):
                raise ValueError("input field is not allowed")
            _validate_input_fields(nested)
    elif isinstance(value, list):
        for nested in value:
            _validate_input_fields(nested)
    elif value is not None and type(value) not in (str, int, float, bool):
        raise ValueError("input must contain JSON values")


def canonical_input_bytes(value: object) -> bytes:
    """Serialize a bounded JSON object into canonical UTF-8 bytes."""
    if not isinstance(value, dict):
        raise ValueError("input must be a JSON object")
    try:
        _validate_input_fields(value)
        encoded = json.dumps(value, sort_keys=True, separators=(",", ":"),
                             ensure_ascii=False, allow_nan=False).encode("utf-8")
    except (TypeError, OverflowError, RecursionError, UnicodeError) as error:
        raise ValueError("input must be valid JSON") from error
    if len(encoded) > MAX_INPUT_BYTES:
        raise ValueError(f"input exceeds {MAX_INPUT_BYTES} UTF-8 bytes")
    return encoded


def canonical_input_sha256(value: object) -> str:
    """Hash a JSON input with stable key ordering and no non-JSON numbers."""
    return sha256(canonical_input_bytes(value)).hexdigest()


def require_public_manifest_v1(manifest: object) -> None:
    if (type(manifest) is not dict or
        len(manifest) != 1 or
        manifest.keys() != PUBLIC_MANIFEST_V1_CALLER_FIELDS or
        type(manifest["schema_version"]) is not str or
        manifest["schema_version"] != "1"):
        raise ValueError("public manifest v1 accepts only schema_version '1'")


def require_name(value: str, label: str) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > 200:
        raise ValueError(f"{label} must be nonempty and at most 200 characters")
    return value


def require_digest(value: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value):
        raise ValueError("SHA-256 must be lowercase hexadecimal")
    return value


def require_seconds(value: int, label: str, minimum: int = 1, maximum: int = 86400) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not minimum <= value <= maximum:
        raise ValueError(f"{label} must be an integer from {minimum} to {maximum}")
    return value


def require_reason_code(value: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[a-z][a-z0-9_]{0,63}", value):
        raise ValueError("reason code must be a short machine-readable name")
    return value
