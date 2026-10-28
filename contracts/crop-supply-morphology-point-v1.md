# Supply-limited fractional material point, research v1

This additive point follows [the actual candidate](crop-supply-morphology-candidate-v1.md)
and [the seed construction policy](crop-supply-limited-morphology-v1.md).
It is a read-only proposed material transition, not a consumed event or adopted CP.

## Source and declared inputs

`crop_supply_morphology_point.apply_fractional_material_point(context,
raw_checkpoint, expected_sha256=..., time_tolerance_seconds_exact=..., inputs=...)`
requires the genuine supply-limited Context/CP. Closed inputs bind that pair, the
actual recomputed candidate SHA/time, original crop/stem binding, actual first pending
source entity/sequence/threshold and a current pre-point internode parent.
Canonical event/organ IDs derive from the actual source timeline and schedule.
Original history and current inventories must contain neither new event nor organ.
No old-trajectory candidate or manufactured older typed handle is substituted.

The input carries an explicit synthetic construction parameter source/revision,
reviewer and rights, common floor, new internode declaration/initial length/k and
optional new leaf declaration/incoming temperature/k. Units are explicit. The new
leaf starts at the accepted canonical F(0), validated against its declaration;
existing leaves are never initialized again. New internode length is separately
and explicitly declared, bounded and nonnegative. The original emergence curve,
requested initial length and actual shoot base temperature stay traceable. An
explicit seed length is not silently replaced by the historical requested length
or canonical K(0), and no cultivar/allometry validation is implied.

For every new organ, compare exact binary64 declared quantities as fractions:
`C_seed * F >= k * X_seed`. The comparison has arithmetic budget zero. Store exact
required/available/remaining C and seed extension/unmapped classification. This is
a classification of the already funded seed, not another debit/respiration charge.
Incompatibility holds without changing C, k, geometry or the original source.

## Supported zero length and actual material arithmetic

`crop_supply_morphology_birth_stage.py` extends only the supported internode-length
bound to include zero. After normalization of that one guard/error string, its
stage body is identical to the accepted positive-length stage, using the same pinned
helpers/components. Positive-case outputs are identical; actual zero remains zero
in the state and evaluates potential/supply-limited growth without an epsilon.
Negative length and the other original unsupported domains still hold.

The point core uses the pinned cStemG/cLeafG and existing exact funding arithmetic.
Process internode first, then the optional leaf. Charge structural C plus original
growth respiration once, leaving a supported positive buffer. Append the actual
new C/zero-age/geometry coordinates, preserving every existing C/A/L/age and unrelated
plant/cohort/air/vapor value. Leaf capacity and incoming sensible heat use the actual
canonical seed area, common floor, declared incoming temperature and original
reference temperature. The canopy energy state changes once. No stem heat transfer
or second extension cost is invented.

The actual new stage evaluates after each material transition. Each major carbon,
partition, exchange and area-energy component executes once per stage. The candidate
uses1 current+33 new RHS calls; the point adds1 stage for stem only or2 with leaf.
No old biological RHS, old public point/jump, source replay or CP issuance runs.
Only the declared new leaf may initialize, including a pure validation before an
incompatible leaf is rejected; no state is published for a held request.

## Point and unadopted global preview

`crop_supply_morphology_point_books.py` verifies exact point residuals with explicit
arithmetic budgets that retain original before/after operands. It reconstructs the
physical global equations from the genuine root, exact lifetime flows, original and
new birth baselines and original point totals plus this point once. Existing global
residuals/budgets compose with the actual point residuals/budgets. New stocks/ages
and geometry use explicit birth baselines; seed construction stays separate from
continuous geometry transfers. Append only zero continuous flows for new organs.

The result includes the proposed program/state/layout, actual post-point stage,
ordered organs/costs, exact new baselines, seed compatibility, point flows/balances
and an explicitly **unadopted global preview**. All current organ clock fields are
reconciled to the actual point time/air integral/state; historical source lineage
and geometry references remain intact. Root has no invented geometric clock.

This preview is neither a new Context/CP nor a consumed schedule item. Stateless
retry with the same before-source and inputs gives identical bytes. A subsequent
owner-family task must adopt once, then prove cold restore and original-grid
remainder/repeated execution. It must use the new zero-length stage and may not
restore changed geometry through an older invariant/typed checkpoint validator.

## Bounds and failures

Inputs are capped at128KiB and output at2MiB; original context/CP/research limits
remain. Known source/code/profile/access/rights/identity/time/units/seed/funding/
numerical/balance/capacity failures raise `SupplyPointHold` without a partial point.
Unexpected `RuntimeError` propagates. Source/profile/code and the original material/
tolerance inputs are rechecked before return. No DB, network, worker, export or UI
side effect is added. G0–G4 remain not_assessed, with no farm/harvest/margin/ranking claim.

Evidence: [focused report](../research/crop-supply-morphology-point-20261028.md).
