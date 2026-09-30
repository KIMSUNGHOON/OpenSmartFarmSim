# Codex CLI model migration implementation

Date: 2026-10-01 (Asia/Seoul). User-directed policy change:
`gpt-6-sol`/`xhigh` → **`gpt-6.1-sol`/`xhigh`** for development and product runtime.
This record covers software and policy changes, not agricultural validation,
product execution proof or a G1/G4 release.

## Evidence used

- Current development CLI session `01a0e064-b01b-7a22-8ef8-dd4afe0eb7dc`:
  its latest `turn_context` records `model=gpt-6.1-sol`, `effort=xhigh`.
  Only those selected metadata fields were read; private prompts and credentials
  were not exported. This is the ongoing CLI session, not a new product invocation.
- Local Codex model cache lists `gpt-6.1-sol` with `xhigh` support. The existing
  user configuration also already selects the exact target and effort.
- The [official model page](https://developers.openai.com/api/docs/models/gpt-6.1-sol)
  and [Codex configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference)
  were checked on 2026-10-01. They document the model/effort and trusted project
  defaults. No API endpoint, authentication provider, prompt schema or dependency
  was changed. No public price was adopted as actual CLI account cost.
- [PostgreSQL 18 ALTER TABLE](https://www.postgresql.org/docs/18/sql-altertable.html)
  documents new-row enforcement of CHECK NOT VALID without scanning old rows.

## Changes

The [migration contract](../contracts/cli-model-policy-migration-v1.md) describes
owner cutover and down procedures. `.codex/config.toml` supplies project defaults;
the product worker constructs explicit target argv. Invocation registration,
separate execution issuer and verifier, authored review completion and thermal
publisher now reject the previous model for current execution authority.
The independent thermal review method also selects the new model.

The fresh schema names its exact new-model CHECK. The explicit owner migration
locks the table and replaces only a recognized policy in a transaction, using
NOT VALID to preserve historical rows. Its inverse retains later rows while
restoring the previous write policy. Neither direction rewrites audit bytes.
Unknown names, changed expressions or additional model checks are refused.

AGENTS.md, current authoritative specifications, execution contracts and future
task requirements use the new model. Completed research and actual past CLI
records retain the model that produced them. The immutable thermal parameter
fixture and its historical reviewer assertion are unchanged. White paper v0.2's
exact original LaTeX is preserved as `main_v0.2.tex` and existing PDFs remain
unchanged; current `main.tex` is v0.3 with the target policy. v0.3 PDF is not built.

## Focused verification

One local test process at a time, `nice -n 10`, PostgreSQL 16.15 and Python 3.12:

1. Worker, supervisor, invocation evidence, signed execution, separate issuer,
   immutable thermal fixture, thermal publisher and authored release/store:
   **153 passed in 52.07 s**. These tests use synthetic inputs, fake CLI children
   and test keys. `OSSF_REAL_CLI_SMOKE` was not enabled.
2. Final migration tests and explicit previous-model review-method refusal:
   **8 passed in 2.13 s**. Fresh and upgraded SQL accept the exact target and
   reject old/other/NULL model, wrong/NULL effort, invalid CLI version and
   counterfeit synthetic invocation. Old and target rows compare unchanged
   before/after upgrade/down, repeated calls preserve the policy, an interruption
   after DROP restores the original constraint, and schema drift is rejected.
3. Configuration TOML parses with the exact two expected settings;
   `main_v0.2.tex` byte-compares with the previous committed `main.tex`;
   immutable fixtures and v0.1 source have no diff. `git diff --check` passes.

There are **161 distinct passing focused tests** across the two final selections.
An initial test collection indentation error was corrected before these runs.
The new migration tests are included in the hosted authored API PostgreSQL 18
selection as well as the broad backend suite. Hosted results for this commit
will be recorded after completion; local PostgreSQL 16 is not PostgreSQL 18 proof.

## Remaining holds

No nested Codex CLI was launched from the ongoing development CLI session,
as required by AGENTS.md. Therefore no new-model product three-stage/thermal/
authored smoke, independent release or account-cost measurement is claimed.
The prepared standalone smoke modes now inherit the target worker model and
their assertions require it. Independent product execution, source rights and
G0/G2/G3a/G3b/G4 evidence remain pending. Existing release/code pins must be
reviewed again where the current code or model is part of authority.

## Standalone test import correction

Hosted authored API run [36789791052](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/36789791052)
failed during collection: the new migration test imported `app.db` before
establishing the backend import path. The local `PYTHONPATH=.` setting masked
this test setup error; no PostgreSQL migration had executed in that run.
The test now establishes its backend path like the existing standalone tests.
Rechecking with `env -u PYTHONPATH` and the pytest executable, matching the CI
entry point, gave **7 passed in 1.65 s** on PostgreSQL 16.15. Hosted PostgreSQL
18 verification is still required; this result does not replace it.

Hosted follow-up [36790057723](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/36790057723)
for `2474583` completed successfully on PostgreSQL 18.6: **82 passed in
257.12 s**, including all seven migration cases; the subsequent existing
authored software/browser pair gave **2 passed in 186.06 s**. Web and C0
workflows also passed. The broad backend workflow remains a separate check.
All CLI children in this hosted selection are test executables, not product
model invocation or independent G1 execution authority.
