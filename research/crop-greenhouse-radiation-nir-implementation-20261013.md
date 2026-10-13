# Virtual solar NIR calculation acceptance — 2026-10-13

Accepted the [pure instantaneous boundary](../contracts/crop-greenhouse-radiation-nir-v1.md),
[implementation](../backend/app/crop_greenhouse_radiation_nir.py) and
[machine evidence](artifacts/crop-greenhouse-radiation-nir-implementation-20261013.json).
This is source virtual cover→canopy→floor optics, not an actual cover/floor
thermal model or whole-greenhouse solar closure. Actual farm Runs0/G0–G4
`not_assessed`; no time advance, stored production result, UI or deployment.

## Research and calculation

Native parent CLI `gpt-6.1-sol`/`xhigh` context at2026-10-13T10:13:48.709Z,
raw SHA `ae32f11e0bb6473981cc29b16ed3c199d2883f47f90b4ff4c4cfa74ded46636a`,
and the independently proven exact-model [child audit](crop-nir-independent-source-audit-20261013.md)
record source ordering, denominators, rights and model limits. No recursive
CLI was run. The [new source register](crop-nir-source-register-20261013.json)
records URL/product/revision/retrieval/QC/units/rights/reviewer; publication,
observation and available-at are unknown. No farm data were adopted.

All optical coefficients/solar fractions are explicit inputs without defaults.
Positive, algebraically equivalent absorptance and denominator expressions
avoid loss of tiny nonzero canopy absorption through subtraction. The separate
Decimal80 oracle evaluates original ordered source formulas and a distinct
expanded two-stream cavity solution; they agree within1e-70. The oracle receives
exact binary64 inputs, separating arithmetic error from input quantization.
Final virtual transmission is floor absorption. Actual cover transmission,
actual cover heat and source direct-air heat have separate meanings and receive
no credit here; construction energy is explicitly unallocated.

## Passed checks

- Original21229:0 generated15 cases/315 reference scalars under the guard.
- Original22323:0: **95 new tests**,0.22s pytest/0.911s guard.
- Original85854:0: **233 focused tests,0 skipped**,0.56s pytest/1.196s guard,
 including unchanged PAR and ventilation consumers.
- **315 independent optical/denominator/energy values** at relative2e-13,
 exact analytic zeros and all four passivity/energy residual budgets.
- Dark/zero leaf/extinction, lossless canopy, fully reflective cover/floor,
 transparent cover, black canopy/floor, construction interception, sparse1e-16
 and dense LAI, near-perfect reflecting layers. Sparse absorption remains
 positive even when binary64 exp rounds transmission to1.
- Scaling, immutable inputs/replay/new identity, source/notice custody,
 closed schema/units/numeric types/fractions; singular trapped lossless cavity
 holds even in darkness; input/product/attenuation underflow/overflow holds.
 No epsilon denominator, clipped absorption or fallback was introduced.

The focused guard preserved **all five required roots and descendants**,
both frozen UI source/asset sets,2,148 original entries, HTTP5173, FD4→4 and
owned processes/PG/passfiles0. Peak136,171,520bytes/PID and849,936,384bytes
combined; existing512MiB/PID/combined1GiB limits and nominal0.25s sampling.
No edits occurred during guards; frozen sources/profiles/old calculations stay
unchanged. Full CI, browser and full database repetition were not run for this
additive pure calculation. The existing ventilation scene continues unchanged.

Next: current-state PAR/NIR/ventilation composition with explicit **non-solar**
canopy heat and a new identity, then every RK trial/independent trajectories,
new immutable context/checkpoint/store/API/same UTC3D. Actual optical/local
farm/future economic data and corresponding publication gates remain external
dependencies; total product completion has no substantiated date.
