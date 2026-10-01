# Authored Run financial parent selection and recovery

Date: 2026-10-01 (Asia/Seoul). This development session follows actual Codex CLI
`gpt-6.1-sol`/`xhigh`, session `01a0e064-b01b-7a22-8ef8-dd4afe0eb7dc`; selected
invocation metadata is in [the model migration evidence](cli-model-migration-implementation.md).
No recursive product CLI was launched.

## Required dependency and boundary

The current authored Run summary identifies its farm revision and release but
does not expose the exact economic scenario/candidate pinned by that farm.
The [new selection/history contract](../contracts/authored-financial-selection-v1.md)
supplies that necessary server dependency for selecting a saved Run in the web
without manually copying unrelated economic identifiers.

The selection derives the closed economic V3 input from actual current authored
completion and registration, repeats the existing economic parent verifier and
returns the bounded existing thermal summary. The history indexes actual
owned economic/assessment service namespaces, canonical immutable input hashes,
exact parent/farm/release/context pins and linked economic jobs. It pages by
creation time/UUID, marks links as requiring current read, and rechecks current
parent pins before projection. Existing verified money/cash/assessment reads
remain necessary. Reads do not create jobs, compute money or expose private raw
inputs. Current scopes and configured service/store pointers are fenced.

The helper is included in the implementation digest. No table, database role,
dependency or arithmetic formula changes. This server dependency is not the
completed `web-authored-economic-assessment` task.

## Focused verification

- OpenAPI generation, closed public schemas, current scope declarations and
  exact byte checks: **54 passed in 32.50 s**.
- The first real DB test invocation failed at collection because its new module
  lacked the established import path setup when `PYTHONPATH` was unset. The
  test import was corrected; no skip or failed collection counts as acceptance.
- Actual SCRAM selection and four-page recovery passed: each economic job has
  the exact server-selected input; assessment history links the actual economic
  parent; each read leaves the number of jobs unchanged. Initial setup took
  **184.87 s**, with the positive case taking **123.67 s**.
- An initial negative fixture attempted to change only the stored input hash.
  PostgreSQL's `jobs_input_digest_matches` CHECK correctly rejected the setup,
  before a history request could execute. The disposable owner fixture now
  changes bytes and their matching hash together to test semantic corruption;
  it restores both in `finally`. It temporarily disables/re-enables only USER
  triggers in the same test-owner transaction. The digest CHECK and production
  privileges remain unchanged.
- Corrected negative and late-change cases plus the actual standard HTTPS case:
  **3 passed in 804.54 s** on PostgreSQL 16.15/SCRAM. Foreign/non-authored/pending
  jobs, invalid cursors, corrupt pinned scenario, revoked rights, missing
  authority and changes after preparation refused projection. The HTTPS
  response covered exact current selection and owned economic/held-assessment
  history as well as the original admission/hold lifecycle: **10 responses**,
  **six hold categories**, maximum **24.769 s**, unchanged **30-second** limit.
- Final review found that assessment history verified its stored hash and
  semantic fields but did not independently require canonical JSON bytes.
  The reader now checks canonical bytes, and the actual negative fixture adds
  a semantically identical, correctly hashed but noncanonical assessment input.
  The positive and expanded negative actual DB cases **passed in 563.00 s**;
  their calls took **127.17 s** and **62.75 s**. Restoring the canonical input
  restored the successful current history read. This final review change was
  covered by those two DB cases; the ten-response HTTPS timing above was measured
  before this canonical-byte check was added.
- Across OpenAPI (54), actual financial selection (three), expanded standard
  HTTPS (one), and the corrected actual assessment browser (one), **59 distinct
  focused tests passed**. Repeated cases are counted once. OpenAPI regeneration
  exactly matched committed bytes: two added paths and four closed schemas,
  with no changed existing paths/schemas. JavaScript/Python syntax, whitespace
  and changed Markdown local-link checks also passed.

All CLI/reviewer children are synthetic test executables/signatures. The fixture
freezes the initial verified review/candidate once, while current registration,
rights, release, actual parent jobs and the new history checks remain active.

## Hosted follow-up and browser correction

[Run 36800474264](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/36800474264)
on `5bb55afadc9bc552ed46ed302279a9db623a98a6` finished with four successful server
jobs: API **82 passed in 288.72 s**, authored economics **13 in 674.81 s**,
authored assessment **15 in 1058.72 s**, standard authored assessment HTTPS
**1 in 317.10 s** (eight responses, six hold categories, maximum **23.449 s**
under the unchanged 30-second HTTP limit). The browser job had two passes and
one failure, so the whole workflow did not pass.

Its captured assessment-browser failure occurred before CLI processing:
`Network.getResponseBody` could not retrieve the browser response a second time.
The revised harness observes the actual closed POST fields and 202 status,
waits for the application's decoded queued state, reads its displayed job ID,
then independently checks that exact owner's actual DB job is queued assessment.
It retains the subsequent CLI hold, current status/report, reload recovery and
single-POST checks. This avoids an extra protocol body read while preserving
the application and database acceptance checks. No product timeout or envelope
decoder was relaxed.

The corrected real HTTPS/SCRAM/Chromium case **passed in 165.51 s**: one POST,
five HTTPS responses, six hold categories, zero console errors; fake worker
**52.587 s** with the existing 300-second lease. New hosted confirmation remains
pending. The earlier BrokenPipe timing diagnosis remains an inference recorded
in [the previous evidence](authored-calculation-assessment-implementation.md).

## Review and practical limits

Review covered correctness (exact parent inputs, canonical bytes, semantic pins,
stable cursor ordering and late-change refusal), readability (one feature-owned
selection/history helper and closed DTOs), architecture (reuse of actual
completion/registration verifiers and economic authority), security (current
tenant/scopes/rights, parameterized SQL and fixed private-safe errors), and
performance (maximum 50 returned links, bounded lookahead and measured HTTPS).
Assessment rows require a bounded linked-parent lookup; this small software
fixture does not establish latency at production tenant/history volumes.
An index link does not approve an economic receipt/result digest: exact current
money/cash/assessment reads remain mandatory before displaying those results.

Heavy local checks ran sequentially at `nice -n 10`; each test owns disposable
SCRAM database/TLS resources and cleanup completed. The browser protocol correction changes only the
harness, while new read operations retain the existing arithmetic, permissions
and claim boundaries. JavaScript syntax and whitespace checks passed. Changed
Markdown local links were checked. The complete local backend suite, PostgreSQL
18 locally and the new authored financial web flow were not run. The expanded
hosted workflow retains all previous selections and adds the new financial
selection suite; new hosted results remain pending.

## Remaining work

The new web selector, pinned V3 economic admission/result/cash flow, persisted
parent recovery, authored assessment linkage and a complete authored financial
browser flow are still required by the existing task. Actual exact-model product
CLI, independent custody/release and G0/G1/G2/G3a/G3b/G4 evidence remain held.
Fake executable/reviewer fixtures prove software only. No crop growth, harvest,
purchased energy, future margin or ranking is introduced.
