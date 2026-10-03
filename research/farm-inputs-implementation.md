# Explicit farm input compiler implementation

Date: 2026-09-30 KST. Status: tested provider candidate for `farm-inputs` in the
[capability map](../CAPABILITIES-farm-authoring.md), following the
[provider contract](../contracts/farm-inputs-v1.md). Full farm authoring, actual
product CLI, independent G1 and production acceptance remain open.

## Development evidence and implementation

The existing development Codex CLI session's turn metadata at
`2026-09-29T16:28:30.232Z` records `gpt-6-sol` with effort `xhigh` in
`rollout-2026-09-27T10-04-50-01a0e064-b01b-7a22-8ef8-dd4afe0eb7dc.jsonl`.
No nested CLI, agricultural research, crop coefficients or external tariff
selection was performed in this increment. The original owned fixture and
registered law remain pinned. This development record is not runtime AI evidence.

`farm_inputs.py` validates explicit facility/control/state/forcing quantities,
user provenance and availability, tenure and decision basis, cultivated area,
cleanup/rest release dates, expected crop event windows, objective, nullable
capital/liquidity limits and exact economic payload references. Money remains
decimal strings; area reservations use an isolated Decimal context. Duplicate
input ids/revisions cannot represent different records. Canonical farm bytes
are bounded by the existing job input policy; bypassed model objects are
revalidated. The economic scope helper checks actual payload hash, tenant,
decision, contexts, evaluation dates and batch/grade/channel/event windows.
Existing stock does not require inventing a current planting.

`farm_input_compiler.py` consumes those explicit values and the original
hash-checked source bytes to build immutable canonical kernel inputs. Facility,
heater, initial state and forcing values reach the existing numerical code.
Original weather and law/constants remain unchanged, while authored quantities
carry the full user evidence and farm content hash/pointer. Derived forcing
records reference the actual authored area/fraction inputs. Initial saturation,
coverage, original snapshot and 60-second stability checks reject invalid plans.

The artifact is `unpublished_candidate`; it carries its base snapshot/source
pins, compiler/engine/unit versions, review cutoff and missing authored review
and snapshot release evidence. It has no accepted Run id, crop prediction or
purchased-energy result. The current pinned fixture/publisher input path rejects
the authored artifact. No source adoption, rights approval, storage grant,
runtime wiring, public HTTP endpoint or existing calculation path changed.

## Verification

The first focused run failed collection with two absent implementation modules
(`2 errors in 0.15s`). After implementation, 14 cases failed because the test
fixture converted the existing `1e-05` float to exponent notation, which the
new decimal-string contract correctly rejects. The fixture now renders its
existing value as fixed decimal text; the contract was kept strict. The focused
24 initial cases then passed in 0.39s.

The final expanded checks recorded **173 passed in 1.89s** across the new provider and
existing thermal/economic suites. The new provider contributes 38 cases:

- Closed inputs, units/signs, explicit missing/null constraints, unavailable
  efficiency/profile evidence, UTC/knowledge time, duplicate ids/crops and
  revalidation of forged Pydantic instances.
- Exact area capacity including a `10^-30` excess, adjacent reservations and
  cleanup/rest occupancy; results do not inherit the caller's Decimal context.
- Exact economic pins/tenant/decision/period, legal but incompatible crop event
  windows, half-open boundaries, grade/channel constraints, unlinked new
  harvest/sale batches and existing opening inventory.
- Actual thermal output changes for floor area, conductance, heat capacity,
  dry air mass, volume, absorbed solar fraction, initial temperature, heater
  capacity and evaporation. All 120 original points match the existing kernel
  exactly, including thermal/vapor residuals, on two deterministic passes.
- Source/snapshot tampering, forcing gap, unstable parameters and initial
  saturation reject; the old pinned input path cannot publish the candidate.

An explicit standalone compiler test exposed an import-path collection error
(`No module named app`, 0.12s). Its own path setup now follows neighboring
tests; standalone execution passed **14 in 0.37s**. This correction is limited
to the test harness.

Changed-document validation found 212 local links and no missing file targets;
the task list retains 19 accepted and 20 pending entries. `git diff --check`
passed. These checks do not inspect external link availability or acceptance.

No browser, PostgreSQL integration, full local backend suite, product CLI,
authored snapshot release or G0/G2/G3/G4 test was run for this provider. Existing
source/worker/3D evidence remains historical; this increment does not turn it
into acceptance of the new path.

## Next dependency

Implement `farm-authoring-storage`: current authenticated ownership/scopes,
actual research/context/economic candidate resolution, assumption rights,
atomic immutable version/custody registration and the authored source/snapshot
review/release boundary. Then bind actual execution and Assessment to those
versions, before exposing the complete farm/economic authoring flow in the web.
The existing whole-farm, API and G1 task checkboxes remain open.
