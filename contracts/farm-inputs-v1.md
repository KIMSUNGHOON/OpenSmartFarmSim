# Farm inputs v1

Status: compiler specification, 2026-09-30. Module `farm-inputs` in the
[capability map](../CAPABILITIES-farm-authoring.md). This is the provider for
authored farm versions, not an extension of the existing selection-only
[farm replay request](farm-replay-scenario-v1.md).

## Objective and boundary

Create a closed, immutable, one-zone user-assumption document containing the
facility, initial conditions, heater, time-specific forcing, cultivation and
expected harvest/sale/collection windows, objective, capital/liquidity limits,
and exact economic candidate pin. Values must change numerical inputs. The
first provider compiles against the original hash-checked owned two-hour
weather and registered thermal law. It never replaces the pinned fixture,
accepts new law coefficients, invents crop outputs or publishes a Run.

The current crop entries express user intent with unavailable profiles. Their
area/calendar constrains land occupancy and economic batch dates; it does not
generate evaporation, growth or yield. Canopy evaporation is a separate explicit
quantity. Efficiency/meter evidence is unavailable in v1, so purchased energy
and its coupling to costs stay unavailable. A missing value is not zero.

## Input contract

`FarmInputs` (`farm-inputs-v1`) has a versioned scenario id, actual research job
UUID, thermal snapshot and DecisionContext ids, decision time, unavailable
MarketContext, `historical-thermal-replay` goal, evaluation dates in Asia/Seoul,
and an economic scenario/revision/hash/candidate pin. These references require
actual server resolution in the storage/execution modules; syntax is not
authorization or custody proof.

Every numeric assumption carries a decimal string, explicit unit, input id,
revision, source reference, UTC `available_at`, `origin=user` and
`evidence_level=assumed`. Availability cannot exceed decision time. Strings,
lists, identifiers and bytes are bounded; extras, floating point input,
invalid signs/units and bypassed Pydantic instances are rejected. Numeric input
ids/revisions must resolve to one identical record throughout the document.
Arithmetic for area and money uses Decimal with an explicit sufficient local
precision. Thermal conversion to binary64 is deterministic and rejects
nonfinite/underflow values.

- Facility: zone/type, owned/leased/unknown tenure, new-facility versus existing
  facility crop-change decision basis and user provenance; separate floor and cultivable area, indoor volume,
  effective heat capacity, dry air mass, envelope conductance and absorbed
  solar fraction. No inferred conductance, heat capacity or measured dimensions.
- Initial state: Kelvin temperature and kg_v/kg_da humidity ratio.
- Heater: delivered W_th capacity, Kelvin setpoint and explicit sourced
  availability; registered indirect sensible control. No COP default.
- Forcing: exactly one entry for each original weather interval, with UTC
  bounds and explicit ventilation kg_da/s, canopy kg_v/s and signed ground W.
- Cultivation: bounded crop/batch ids, user species/variety intent, occupied
  area, occupancy start/end and release time after cleanup/rest; expected
  harvest/sale/collection windows and explicit user provenance. All profiles
  remain unavailable. Sweep simultaneous reservations through release time;
  their sum cannot exceed cultivable area. Adjacent half-open reservations
  may reuse the area. Empty cultivation is allowed for a thermal-only plan.
- Objective: conditional operating profit, conditional operating margin or
  minimum cash. Constraints explicitly include nullable capex ceiling and
  minimum cash (KRW); omission is rejected and null remains unknown.

## Provider interfaces and structure

`backend/app/farm_inputs.py`: models, canonical serialization and economic
scope validation. `backend/app/farm_input_compiler.py`: pure compilation with
original manifest/weather/parameter bytes and explicit review time. Both
revalidate untrusted values at their public boundary.

`canonical_farm_inputs(value)` returns bytes (bounded by the existing job
input limit), so corrections necessarily produce a new content hash.
`validate_economic_scope(farm, economic, authenticated_tenant)` verifies the
exact economic payload pin, tenant, decision, market/evaluation calendar and
crop batch/window/channel connections. It is a scope check, not economic
rights, conservation, settlement, gate or authentication authority; those
remain with the existing server services. Opening inventory may have a batch
with no current planting; new harvests may not. Collections must match their
referenced sale's expected collection window. No event dates are shifted.

`compile_farm_inputs(farm, manifest_bytes, weather_bytes, parameter_bytes,
review_at_utc=...)` returns immutable canonical farm and numerical bytes with
their hashes. It verifies the exact original snapshot hash and source times,
retains original law/constants and weather, and converts authored values into
the existing `euler_step` parameter/state/heater/forcing records. Derived
outdoor humidity and solar gain retain rule versions and actual input ids.
It checks initial state and 60-second stability, but does not claim full-run
convergence/residual acceptance. New artifacts have `unpublished_candidate`
status and explicit missing review/release evidence. They cannot pass the
existing pinned publisher or become an accepted thermal-v1 trace.

Style: frozen closed Pydantic contracts; small pure functions; no new package,
database, public HTTP endpoint or permission in this module. Example:

```python
farm = FarmInputs.model_validate(untrusted_data(value))
raw = canonical_input_bytes(farm.model_dump(mode='json'))
```

## Verification and acceptance

From `backend/`:

```bash
uv run --locked --group dev pytest -q tests/test_farm_inputs.py tests/test_farm_input_compiler.py tests/test_thermal.py tests/test_economics.py
```

1. Accept a fully explicit owned synthetic plan; reject wrong units, signs,
   missing/duplicate records, late inputs, date/area violations and forged
   constructed models. Reordering JSON keys preserves the digest; corrections
   change it. Preserve exact decimal area sums beyond the default context.
2. Reject different economic pins, tenants, calendars, decisions/contexts,
   unlinked harvest batches and sale/collection dates outside declared windows.
3. Compile actual kernel records; changing facility/control/forcing changes
   `euler_step` results under the existing code, with unchanged weather/law.
   Reject original source/snapshot tampering, forcing gaps, unstable steps and
   invalid initial humidity. Retain user provenance and candidate/hold status.

Persistence, current authorization/rights, source custody, new snapshot release,
full simulation/replay, API and browser authoring are the next modules. Full
farm authoring and G1 are not accepted by these provider tests alone.
