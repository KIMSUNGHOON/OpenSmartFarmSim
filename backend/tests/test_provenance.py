from datetime import datetime, timedelta, timezone
from hashlib import sha256
from pathlib import Path
import sys

import pytest
from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.provenance import (
    ProjectCheck,
    RequestDetail,
    Right,
    SourceRecord,
    SourceScope,
    Variable,
    verify_raw_hash,
)


T0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
T1 = datetime(2026, 1, 2, tzinfo=timezone.utc)
RAW = b"synthetic contract test bytes"


def record(**changes):
    data = dict(
        schema_version="1",
        scope=SourceScope(
            provider="example-provider",
            product_id="hourly-observations",
            product_version="v1",
            source_url="https://example.org/product",
            station_or_grid_id="station-1",
        ),
        revision_id="revision-1",
        request_details=(RequestDetail(name="station", value="station-1"),),
        observed_at=T0,
        published_at=T0,
        available_at=T0,
        retrieved_at=T1,
        valid_from=None,
        valid_to=None,
        variables=(
            Variable(
                name="solar",
                original_unit="MJ/m2",
                time_semantics="interval_total",
                interval_start=T0,
                interval_end=T1,
                provider_qc_status="not_supplied",
                provider_qc_value=None,
            ),
        ),
        project_checks=(
            ProjectCheck(
                variable="solar", name="physical-range", version="v1",
                status="passed", evidence_id="evidence-1", reviewer="reviewer-1",
            ),
        ),
        rights=(
            Right(action="access", status="allowed", evidence_id="terms-1", reviewer="reviewer-1"),
            Right(action="store", status="unknown", evidence_id=None, reviewer=None),
        ),
        raw_sha256=sha256(RAW).hexdigest(),
        synthetic=False,
        synthetic_author=None,
        synthetic_method=None,
        source_reviewer="reviewer-1", source_evidence_id="source-1",
    )
    data.update(changes)
    draft = SourceRecord.model_construct(record_id="placeholder", **data)
    return SourceRecord(record_id=draft.content_id(), **data)


def test_raw_bytes_are_checked_against_immutable_digest():
    source = record()
    assert verify_raw_hash(source, RAW)
    assert not verify_raw_hash(source, RAW + b"changed")
    with pytest.raises(ValidationError):
        source.raw_sha256 = "0" * 64
    with pytest.raises(ValidationError):
        source.variables[0].original_unit = "W/m2"
    with pytest.raises(ValidationError):
        source.scope.product_id = "other"


@pytest.mark.parametrize("digest", ["abc", "G" * 64, "f" * 65])
def test_malformed_digest_is_rejected(digest):
    with pytest.raises(ValidationError):
        record(raw_sha256=digest)


@pytest.mark.parametrize("field", ["observed_at", "published_at", "available_at", "retrieved_at", "valid_from", "valid_to"])
def test_all_record_times_require_utc(field):
    with pytest.raises(ValidationError):
        record(**{field: datetime(2026, 1, 1)})
    with pytest.raises(ValidationError):
        record(**{field: datetime(2026, 1, 1, tzinfo=timezone(timedelta(hours=9)))})


@pytest.mark.parametrize("start,end", [(T1, T0), (T0, T0)])
def test_reversed_or_empty_intervals_are_rejected(start, end):
    with pytest.raises(ValidationError):
        record(valid_from=start, valid_to=end)
    with pytest.raises(ValidationError):
        record(variables=(Variable(name="solar", original_unit="MJ/m2", time_semantics="interval_total", interval_start=start, interval_end=end, provider_qc_status="not_supplied", provider_qc_value=None),))


@pytest.mark.parametrize("field,item", [
    ("variables", lambda r: r.variables[0]),
    ("project_checks", lambda r: r.project_checks[0]),
    ("rights", lambda r: r.rights[0]),
    ("request_details", lambda r: r.request_details[0]),
])
def test_duplicate_named_entries_are_rejected(field, item):
    source = record()
    with pytest.raises(ValidationError):
        record(**{field: (item(source), item(source))})


def test_unknown_fields_and_secret_bearing_request_details_are_rejected():
    with pytest.raises(ValidationError):
        record(unreviewed=True)
    with pytest.raises(ValidationError):
        RequestDetail(name="api_key", value="secret")
    with pytest.raises(ValidationError):
        SourceScope(provider="p", product_id="id", product_version="v", source_url="https://example.org/data?token=secret", station_or_grid_id="s")


def test_source_url_and_request_values_preserve_exact_non_secret_input():
    scope = SourceScope(provider="p", product_id="id", product_version="v", source_url="https://example.org", station_or_grid_id="s")
    assert scope.source_url == "https://example.org"
    assert RequestDetail(name="station", value="001").value == "001"
    with pytest.raises(ValidationError):
        SourceScope(provider="p", product_id=" id ", product_version="v", source_url="https://example.org", station_or_grid_id="s")


def test_provider_qc_raw_value_is_distinct_from_project_result():
    with pytest.raises(ValidationError):
        Variable(name="solar", original_unit="MJ/m2", time_semantics="instant", provider_qc_status="not_supplied", provider_qc_value="0")
    with pytest.raises(ValidationError):
        Variable(name="solar", original_unit="MJ/m2", time_semantics="instant", provider_qc_status="passed", provider_qc_value=None)
    with pytest.raises(ValidationError):
        ProjectCheck(variable="solar", name="physical-range", version="v1", status="not_supplied", evidence_id="evidence-1", reviewer="reviewer-1")


def test_synthetic_inputs_identify_author_and_generation_method():
    with pytest.raises(ValidationError):
        record(synthetic=True)
    assert record(synthetic=True, synthetic_author="test-author", synthetic_method="handwritten bytes").synthetic


def test_nested_times_and_event_order_are_validated():
    with pytest.raises(ValidationError):
        Variable(name="solar", original_unit="MJ/m2", time_semantics="interval_total", interval_start=datetime(2026, 1, 1), interval_end=T1, provider_qc_status="not_supplied", provider_qc_value=None)
    with pytest.raises(ValidationError):
        record(observed_at=datetime(2026, 1, 3, tzinfo=timezone.utc))
    with pytest.raises(ValidationError):
        record(published_at=T1, available_at=T0)


@pytest.mark.parametrize("name,value", [
    ("apikey", "credential-text"), ("X-API-Key", "anything"),
    ("Authorization", "anything"), ("station", "Bearer credential-text"),
    ("station", "token:credential"), ("station", "sk-secret-example"),
    ("station", ""), ("station", " 001 "),
])
def test_request_detail_rejects_obvious_secret_forms_and_noncanonical_values(name, value):
    with pytest.raises(ValidationError):
        RequestDetail(name=name, value=value)


@pytest.mark.parametrize("url", [
    "https://example.org/data/token/credential",
    "https://example.org/data/api_key/credential",
    "https://example.org/data/%74oken/credential",
    "https://example.org/data/sk-secret-example",
    "https://example.org/data/token=credential",
    "https://example.org/data/apiKey:credential",
    "https://example.org/data/%3Ftoken=credential",
    "https://example.org/data/%23secret=credential",
    "https://example.org/data#fragment",
    "https://example.org/data?station=1",
])
def test_source_url_excludes_secret_paths_queries_and_fragments(url):
    with pytest.raises(ValidationError):
        SourceScope(provider="p", product_id="id", product_version="v", source_url=url, station_or_grid_id="s")


def test_content_id_binds_manifest_and_raw_digest():
    original = record()
    assert original.content_id() == original.record_id
    with pytest.raises(ValidationError):
        SourceRecord(**(original.model_dump() | {"raw_sha256": "0" * 64}))
    with pytest.raises(ValidationError):
        SourceRecord(**(original.model_dump() | {"revision_id": "new-revision"}))
    assert record(revision_id="new-revision").record_id != original.record_id
    assert record(raw_sha256="0" * 64).record_id != original.record_id
