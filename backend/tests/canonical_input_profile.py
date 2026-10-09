"""Explicit synthetic serialization diagnostic; no HTTP capacity claim."""

import json
from pathlib import Path
import statistics
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.jobs import canonical_input_bytes
from test_market_scenario import case
from test_market_source_store import record_items


def test_profile_canonical_input_fields_without_changing_bytes():
    source, _ = case()
    documents = [model.model_dump(mode='json') for _, model in record_items(source)]
    expected = [json.dumps(item, sort_keys=True, separators=(',', ':'),
        ensure_ascii=False, allow_nan=False).encode('utf-8') for item in documents]
    samples = []
    for _ in range(3):
        started = time.perf_counter()
        for _ in range(400):
            for item, raw in zip(documents, expected, strict=True):
                assert canonical_input_bytes(item) == raw
        samples.append(time.perf_counter() - started)
    print('canonical_input_profile=' + json.dumps({
        'scope': 'synthetic_field_validation_diagnostic_only',
        'documents': len(documents), 'repeats_per_sample': 400,
        'calls_per_sample': len(documents) * 400, 'samples_seconds': samples,
        'median_seconds': statistics.median(samples)}), flush=True)
