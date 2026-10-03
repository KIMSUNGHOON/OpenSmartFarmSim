# Farm selection to thermal execution: implementation evidence

Date: 2026-09-29. Internal software candidate; no whole G1 or farm claim.
Contract: [farm thermal execution v1](../contracts/farm-thermal-execution-v1.md).

## Development context and implementation

The active Codex CLI turn context at `2026-09-29T13:02:11.276Z` records
model `gpt-6-sol`, effort `xhigh`, thread
`01a0e064-b01b-7a22-8ef8-dd4afe0eb7dc`. This session supplied the reviewable
development judgment. No recursive CLI, provider data adoption or actual model
invocation was performed for this increment.

- FarmReplayScenarioService exposes an internal verified selection read over
  the same immutable row and current references as its public metadata read.
- Closed thermal input v3 requires the farm ID, revision and full input hash;
  the HTTP request also retains the existing model/profile/key fields. V1/v2
  inputs and V2 admission remain supported. Mixed or incomplete shapes fail.
- The dedicated binder checks the exact service/store assembly, current scopes,
  stored thermal/economic pins and actual completed owned research, collection
  and review lineage. It checks root/collection publication bytes and manifests,
  root attempt/decision/input/artifact hashes and collection attempt/input/record
  hashes. Another root with the same snapshot and canonical research hash fails.
- Admission checks binding before publisher validation and again at commit.
  The existing owned review verifier's extra admission scopes are explicitly
  declared and checked. Completion reads use the farm read scopes.
- The existing publisher still verifies capture, decision, source/QC, independently
  observed execution and release. The worker rechecks the binding before
  calculation, against the verified packet, and before/after Run insertion.
- Receipt v3 adds the three farm identity fields and canonical server binding
  hash. Job discovery reconstructs the input and verifies the publication,
  actual Run and current selection before returning the existing public DTO.
- ApiRuntime supplies its actual farm service to admission and discovery. No
  table, grant, dependency, physical formula, tariff or monetary calculation was
  added. CODE_FILES includes the binder; OpenAPI is regenerated from the routes.

## Checks and observed failures

Local PostgreSQL 16.15 uses the existing isolated real SCRAM login fixture with
market calculation, source storage, thermal scenario and break-even profiles.
The CLI executable, source metadata and context/release/execution authorities
are controlled synthetic test fixtures. These cannot establish an actual model
decision, independent review/release, source G0 or full G1/G4.

- Initial V3 input shape: 1 passed in 0.32s. The HTTP request test first failed
  at import because RUN_REQUEST did not exist; implementation then passed both
  closed/discriminated input tests.
- The first joined fixture failed in 26.42s because its helper treated an actual
  ResearchScope as a dictionary. The helper was corrected to use its fields.
- The next completion attempt failed at admission in 58.52s. Direct diagnostic
  admission reproduced the server hold in 74.89s: the binder expected a review
  job field in the publisher's smaller admission context. Admission now passes
  its already-fixed review job alongside that context; the worker/read path
  still requires the full report identity. No publisher check was removed.
- The corrected owned-lineage/completion, different-root rejection and late Run
  authority rollback run passed 3 in 309.96s. Extra admission scopes and the
  admission rollback check were then added for final verification.
- Existing runtime, V1 atomic completion, V2 HTTP scenario execution and late
  admission rollback checks passed 37 in 57.66s before the final V3-only scope
  declaration. Legacy behavior remains unchanged.
- The first TLS helper failed in 48.20s at grant construction: it copied more
  than the supported 20 scopes from the fixture operator. It now grants only
  the scopes needed by submission or read; the limit was not raised.
- Actual ApiRuntime + HTTPS/Bearer/SCRAM passed in 123.32s before, and in
  **128.06s after**, explicit V3 admission scope declaration. It verifies 401,
  reader POST 403, new admission, same-key retry, actual worker completion,
  reader Run discovery and foreign tenant 404. The server is shut down and
  joined in `finally`. Final timings were 0.004/0.005s for denied calls,
  22.126s POST, 21.542s retry, 7.152s completion read, 0.051s foreign read;
  the existing 30s client timeout was retained. This is no capacity/SLA proof.
- Regenerated OpenAPI and the two input tests passed **41 in 19.22s** after the
  explicit scope declaration. The earlier snapshot mismatch was corrected by
  regeneration rather than weakening the snapshot test.

Final owned admission/completion, different-root rejection, admission-event and
late Run authority rollback, plus legacy V1/V2 verification passed **5 in
332.49s** after the explicit scopes and additional rollback assertions. The
missing farm service holds without a job/Run fallback, each additional admission
scope is denied with 403, and rollback leaves no job/event or Run/publication.
Together these terminal runs verify **82 unique passing cases**; this is not a
claim that the earlier failed runs were green or that the full backend suite was
run locally. Frontend tests and Docker app launch were not rerun for this
backend-only increment. Diff whitespace and **335 local documentation links**
passed. Against the previous committed OpenAPI, only POST /v1/runs and GET
/v1/jobs/{job_id}/run change; public response components remain identical.

## Review and remaining work

Review covered canonical versions, actual parent lineage, current authority,
transaction rollback, publication/input/receipt identity, exact runtime service
bindings, bounded artifact/request reads and fixed public errors. The binder is
an internal verification module; domain inputs are not added to public outputs.

The registered economic selection is revalidated as a current reference; this
does not run or physically couple its money calculation. Economic V2 inputs and
receipts, paired assessment, whole farm/settlement authoring, heat-to-purchased
energy/cost evidence, browser/3D and actual CLI with independent capture/release
custody remain future work. G0/G2/G3a/G3b/G4 and the existing checklist stay
unaccepted. No crop growth, harvest, purchased energy, future margin or ranking
was demonstrated by these tests.
