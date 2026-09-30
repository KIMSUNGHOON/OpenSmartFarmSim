# Authored farm review HTTP admission record

Date: 2026-09-30. Scope: queue a currently valid registered farm version for
the existing `collection_review` decision stage. This is software evidence,
not an executed CLI decision, independent release or accepted Run.

The new closed `FarmAuthoredReviewRequest` carries only scenario identity,
registration SHA-256 and idempotency key. The API checks the current Bearer
principal and exact review scopes, then delegates to the existing service in
a threadpool. The service rereads rights/sources, recalculates both complete
thermal candidate traces and repeats the verification before the immutable
intent is committed. `ApiRuntime` constructs the exact review service from
its owned farm authoring service; a detached service is rejected by the API.

Focused local checks:

```text
uv run --locked --group dev python -m app.api_openapi --write
uv run --locked --group dev pytest -q tests/test_api_openapi.py tests/test_api_runtime.py tests/test_api_authored_runtime.py tests/test_api_farm_authoring.py
76 passed, 13 skipped in 24.75s
```

The OpenAPI check caught an initial symbol collision between authored review
scopes and existing collection review scopes. That collision was fixed and
the entire documented route scope table passed on rerun. The 13 skipped cases
require a disposable PostgreSQL SCRAM database absent locally. The new
database test covers scope/owner denial, transport rejection, queued
admission, exact retry, conflict and current-evidence hold. On exact head
`cc181cb`, [authored API run 36660968888](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/36660968888)
passed **51 tests** against disposable PostgreSQL, including this test.
No product Codex CLI execution,
independent reviewer release, authored simulation worker call or G1 proof is
claimed.
