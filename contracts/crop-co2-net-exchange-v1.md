# Instantaneous net crop CO₂ exchange v1

Status: software scalar accepted; [evidence](../research/artifacts/crop-co2-net-exchange-20261021.json).
Source decision P02 is in the
[CO₂ review](../research/crop-co2-stomatal-source-policy-20261021.md) and
[register](../research/crop-co2-stomatal-source-register-20261021.json).
This child consumes an already computed rate result; it does not evaluate the
crop a second time or advance state. Numerical development authority remains
[PROJECT_SPEC §5.3](../docs/PROJECT_SPEC.md#53-개발-착수와-결과-게시).

## Input and producer boundary

`crop_co2_net_exchange.calculate_exchange(rates=...)` consumes the current
in-memory research rate dictionary of one supported producer:

| Producer | Respiration fields consumed |
| --- | --- |
| `crop_growth_rates` organ v1 | `growth_respiration`, `maintenance_respiration.{leaf,stem_root,fruit}` |
| `crop_plant_cohort_rates` explicit-entry cohorts | `growth_respiration`, `vegetative_maintenance.{leaf,stem_root}`, `fruit_maintenance` |
| `crop_plant_startup_rates` empty-sink startup used by the current joint RHS | same fields, with the producer's **realized** growth respiration |

All use `photosynthesis`, already including the existing photosynthetic
compensation term. Accept only supported exact model/profile identities,
`scope=software_research_only`, a canonical source input SHA and, for the last
two producers, exact component versions; startup additionally needs the pinned
startup policy. Profile constants remain the existing immutable profiles.
Consumed quantities are closed `{value,unit}` with finite nonnegative Python
int/float and `mg_CH2O/m2_floor/s`. Maintenance mappings have exactly the listed
organs. Unrelated producer fields are not revalidated or used for arithmetic.

This is an internal numerical adapter. Declared identities detect incompatible
results; a dictionary is not an authenticity proof. Later custody/Run publishing
must verify the actual source and current rights. No authority or G0–G4 decision
is created by this function. It can consume the existing joint RHS's actual
startup result without substituting the older organ model or recalculating it.

## Source mass convention and calculation

Pinned GreenLight C9 SHA-256
`272a589edf0bb40d1a91b34e883f8e94b9adf747a576be4620c50296c03d7033`:
`/Model flows/Canopy photosynthesis/Net photosynthesis rate/mcAirCan` and
`/Parameters/mCo2`, `/Parameters/Table 9.1/mCh2o`.
Retain the [BSD notice](../LICENSES/GreenLight-BSD-3-Clause-Clear.txt).

```text
net_CH2O = fsum(photosynthesis, -growth_respiration,
               -maintenance_leaf, -maintenance_stem_root, -maintenance_fruit)
net_crop_CO2_uptake = (44e-3 / 30e-3) * net_CH2O
air_CO2_flux = -net_crop_CO2_uptake
```

The ratio uses mg/umol for both source molar masses. Positive uptake removes
CO₂ from air; a negative sink is a nighttime source. No clipping is applied.
Removal, fruit terminal outflow/harvest, allocation/entry and fruit carbon mass
derivatives are excluded from the gas flux. The startup producer's deferred
allocation must not incur requested fruit respiration a second time. Source
photosynthetic compensation is not subtracted again. The gas converter's
44.01g/mol convention is not silently substituted for C9's44g/mol.

The new version `greenlight-net-crop-co2-exchange-v1` returns normalized consumed
CH₂O terms/net and paired CO₂ uptake/air flux with units, source producer
identity, component-code/profile/input/policy identities, source/model/code and
conversion identities and an input hash bound to those terms. It copies identity
and quantity data; it does not mutate or retain mutable input references.
Invalid identity/shape/unit/domain or overflow/nonfinite arithmetic raises
`Co2NetExchangeHold`; it supplies no invented rates or partial result.

## Acceptance fixed before implementation

1. All existing independent organ/cohort/startup reference cases: source net
   sink from independent high-precision respiration/mole accounting, relative
   tolerance5e-12, absolute5e-14, matching the existing upstream references.
   In addition compare the exact binary input rate terms with Decimal80 and
   the44/30 rational conversion at relative3e-15, absolute0; exact zero is zero.
2. Actual producer calls for nighttime, removal, empty-sink deferral/realized
   respiration and current joint RHS consumption; no repeated crop calculation.
   Assert positive/negative/zero transfers and source mass convention, unchanged
   source inputs/rates and bound identity changes. Reject incompatible producers,
   profiles/components/policy, units and invalid scalar/maintenance fields.
3. Focused tests under unchanged WSL caps; original crop modules/profiles/results,
   both previews and5healthy roots preserved; no DB/browser/deployment or claim
   promotion. Follow with the separate geometry/air mass RHS child.

## Observed acceptance

Final same-source run:52 tests passed in0.30s, including all32 independent
organ/cohort/startup reference cases and consumption of the actual joint stage's
startup result without a second crop calculation. The initial missing-module
run is an absence check, not a numerical counterexample. After the first52-pass
run, the input digest was refined to bind consumed inputs only, excluding the
computed net; the final52-pass run verifies that source. Counts are not added.

Final guard child0/wall0.597468s, peak combined RSS627,859,456bytes, FD4→4;
5healthy roots,2,148originals and frozen previews preserved; owned process/PG/
temp/credential residue0. Existing crop/gas modules and profiles are unchanged.
The exact-model review execution is recorded in the evidence. Dynamic air
inventory/CO₂ feedback, storage/API/3D, whole-product CI and independent farm
validation are not accepted by this scalar result.
