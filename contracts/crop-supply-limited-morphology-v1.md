# Supply-limited organ extension, research v1

Status: design contract only. The accepted [repeat Context/CP](crop-organ-repeat-v1.md)
does not yet implement this law. [Source review](../research/supply-morphology-primary-equations-20261027.md)
distinguishes published equations from this **new synthetic project policy**. No cultivar
coefficient, dry/fresh-mass conversion, independent farm validation or G0–G4 approval is adopted.

## Law and units

Policy ID: `marginal-construction-extension-v1`. It limits **new extension after the
explicit branch time**, not historical geometry or a permanent mass–geometry allometry.
For an explicitly represented leaf or internode `i`:

```text
F       represented model floor area                       m2_floor
C_i     current structural carbohydrate-equivalent stock    mg_CH2O/m2_floor
g_i     actual allocated new structural inflow              mg_CH2O/m2_floor/s
m_i,r_i maintenance and explicit removal                    mg_CH2O/m2_floor/s
X_i     leaf area A_i / internode length L_i                m2_leaf / m_internode
k_i     marginal construction cost                          mg_CH2O/m2_leaf
                                                           / mg_CH2O/m_internode
a_i     organ thermal age                                   degC_day
P_i     nonnegative potential extension K_i'(a_i) * a_i_dot  X_unit/s
d_i     potential extension construction demand = k_i*P_i/F  mg_CH2O/m2_floor/s
e_i     extension-attributed inflow = min(g_i,d_i)            mg_CH2O/m2_floor/s
b_i     other/unmapped structural inflow = g_i-e_i           mg_CH2O/m2_floor/s
X_i_dot = F*e_i/k_i                                         X_unit/s
C_i_dot = g_i-m_i-r_i                                       mg_CH2O/m2_floor/s
```

Require `F,k_i > 0`, finite inputs and `g_i,P_i >= 0`. Validate the units before
arithmetic. `C` means CH₂O-equivalent mass, not elemental carbon. An absolute organ
quantity uses `F` once; no implicit plant count, planting density or repeated floor factor.
The `k_i` are explicit, versioned **marginal construction assumptions**. They are
not read from prose, inferred from current A/L/C, or supplied by unlicensed data.
No default numerical k, carbon fraction, SLA, density, dry-matter content or stem diameter.

`g_i` comes from the same stage's existing allocation/stock policy, not `C_i_dot`,
photosynthesis, the caller's requested supply or a prior sample. Growth respiration
was already charged on that structural inflow. `e_i/b_i` only classify it; they incur
no additional buffer debit, respiration or refund. `b_i` stays in that organ's existing
stock account, explicitly **unmapped to geometry**. Do not call it diameter growth,
storage reserve, saleable biomass or a measured tissue compartment. A zero potential
rate leaves all g in b; a zero g gives zero extension. Roots retain their existing
stock/sink account and have no invented age, area or length law.

This policy deliberately has no delayed catch-up after the potential window, no
stock-to-size clamp and no maintenance-driven geometric shrinkage. Published source
models make different choices; do not label this a reproduction of any one of them.
Maintained geometry under maintenance is incompatible with claiming `X=F*C/k` or
`C>=k*X/F` at every later time. Record that limitation in every result.

## Genuine source, current clocks and branch

Input authority is the actual accepted `crop_organ_repeat.Context`, its immutable
origin/ordered receipts and an actual own checkpoint, authenticated by a trusted
stored SHA. Preserve the original source pair separately from the current parent
pair. A caller's self-rehashed JSON is insufficient custody. Never manufacture an
older typed Context/CP or use an old public function with a substituted handle.

Bind all current ordered leaf/internode/root IDs, the original selected stem state,
model floor, original parameter/code/profile bytes, exact simulation/development
origins, phase/event sequence/cursor/prefix, current C/A, original D0, schedule,
birth records and air-temperature integral. Derive required clocks inside this
morphology input; do not ship another separate clock DTO prerequisite.

For each actual source baseline `b` and current exact elapsed time `t`:

```text
a_exact(t) = a_b + [I_air(t)-I_air(b)-T_base*(t-t_b)]/86400
```

Use the originally selected initial **internode** clock/age, not its carbon
initialization time. Keep declared and numerical birth bases and their actual parent
receipts distinct. Initial leaf parents that were unbound remain unbound. Roots have
no clock. Keep numerical leaf age and its exact-clock residual/budget; do not replace
the existing state with the diagnostic clock. New internode numerical age channels
start from the checked current exact baselines and evolve in the shared stages.

The new version branches explicitly at a checked current point **before** the
original horizon. The retained final 512-second CP is a read witness, not a source
with more time remaining. Preserve the old state prefix verbatim. Initialize new
length channels from the actual original curve/anchor and current clocks, recording
that this is legacy potential geometry at transition. Existing A/L/C and original D0
are not recalibrated to k, rewound, repaired or retroactively declared carbon-funded.
Existing baseline mass–geometry compatibility stays `not_assessed`; only extension
from the new branch has the new construction ledger.

Keep the original thermal K curves as potential-rate inputs. Once carbon limits
growth, the old `A-K(a)=D0` invariant is no longer a new-law invariant. Retain it as
source history and expose the changed gap. Integrate potential and realized extension
with the same quadrature; `deficit = integral(P)-integral(X_dot)` starts at zero and
is nonnegative within its explicit arithmetic budget. Compare the analytic K change
with integrated potential separately as a quadrature/convergence diagnostic. Never
cover truncation error with an arbitrary ULP tolerance, reset D0, clamp the endpoint
to K, or promise exact canonical-curve bounds from RK4 alone.

## Shared-stage carbon, geometry and climate

Use an acyclic new-version RHS with the accepted pure component kernels:

1. Current A and common F determine LAI, canopy heat capacity and canopy temperature
   from the actual sensible-energy state. Current states/forcing determine carbon
   uptake, potential allocation, original growth respiration and maintenance.
2. Existing leaf/stem/root sink and stock policies give actual g/m/r, retaining
   their existing zero-sink refunds once. Apply the extension law and classify e/b.
3. Actual A_dot determines LAI_dot and capacity inflow. Evaluate exchange, capacity
   transport and the energy/vapor derivatives with those same state and area values.

Current carbon allocation does not depend on LAI_dot in the inspected kernels.
The existing top-level joint RHS computes climate before returning its allocation,
so **do not** call it with a guessed potential A_dot and patch its climate later.
Compose the underlying kernels in this order, with new truthful receipts/code pins.
Evaluate each actual component once per new numerical stage; no hidden second RHS,
fixed-point guess or counterfeit old result hash. Old modules stay byte-for-byte.
The one old current-RHS check required to authenticate the incoming CP is counted
separately from the new stage; neither is past integration or initialization.

For the first supported continuous domain, require positive total leaf area/heat
capacity and positive aggregate stocks accepted by the existing kernels, nonnegative
individual stocks, zero vegetative organ removals and zero declared capacity outflow.
Use the original k_heat, reference/incoming temperature and latent heat:

```text
LAI = sum(A_i)/F
capacity = k_heat*LAI
capacity_in = k_heat*sum(A_i_dot)/F ; capacity_out = 0
material_heat = capacity_in*(T_in-T_ref)
```

Retain canopy/air sensible heat, vapor/water boundary and reduced-energy balances.
Area-driven capacity is the existing reduced-model convention; unmapped b is not
new measured heat capacity. Sensitivity/biological adequacy remains unvalidated.
Do not infer irrigation, purchased energy or system water consumption from vapor
exchange alone. Carbon and point/global books remain independent of shape labels.

Any unsupported removal, empty canopy/re-entry, negative intermediate stock,
outward derivative at depleted stock, invalid signed thermal domain, lost positive
quantity or original bound violation holds at the last confirmed prefix. No epsilon
area, negative clamp, automatic death/shrinkage, maintenance suppression or new
external-input fabrication. These excluded physiological/management cases need
separate reviewed laws; they are not silently supported by this v1.

## Subsequent integration and births

The first implementation exposes an actual bound **one-stage RHS**, not a renderer
transform. A genuine new Context/CP family then carries the extended state, same
original grid/horizon, exact remainder, shared-stage RK4 and continuous construction,
potential/realized/deficit and original C/energy/water ledgers. Whole/split/cold restore
must give identical final bytes. Source restore never reruns past RHS/material/leaf
initialization; current-stage validation is separately measured.

New births after the branch must satisfy, before any mutation:
`C_seed*F >= k_i*X_seed` using explicit seed dimensions (positive leaf area,
nonnegative internode length) and declared seed C,
with a documented rounding budget and scope. The existing seed debit and its original
growth respiration are charged **once**, not again as extension. Retain exact birth
time/air/age/actual parent, seed cost/remaining unmapped C and point capacity/sensible
heat receipt. A tiny legacy QA seed is not automatically compatible with any new k.
Incompatibility holds; do not increase seed C, shrink F(0), fund from nowhere or fit
k to make a fixture pass. Pre-branch receipts stay immutable and historically scoped.

Automatic threshold detection/material adoption requires new-law stage brackets and
candidate/point/global ledgers, not candidates generated by the old trajectory.
No output may skip a due event or consume it twice. The initial RHS slice may stop
before a threshold; the subsequent event slice must implement repeated adoption
before claiming a complete new-law trajectory through events.

## Acceptance and visible output

Next task: `supply-morphology-bound-shared-stage-rhs`. It is complete only when actual
current repeat inputs (including original, declared and numerical births) bind to a
new stage with all of the following evidence:

- Independently computed zero/supply-limited/demand-limited/boundary cases, area and
  length units/floor scaling, zero potential, no root shape, e+b=g and C/respiration
  conservation. Values are own QA inputs, not crop coefficients.
- The same original state and valid changed carbon availability produce the
  corresponding actual A_dot/L_dot through allocation, not through a caller override.
  LAI_dot, capacity/material heat and the resulting actual climate derivatives use
  those rates. Count each component and the separate incoming-CP validation.
- Exact source/current ID, clock, A/C/D0, parent, raw/profile/code/trusted hash and
  current/late rights checks; input immutability and deterministic retry. Reject
  missing/unlicensed/wrong-unit/wrong-scope parameters, guessed ancestry, altered
  baselines, unsupported removals/empty/depleted domains, rehash and size/cap failures.
- A separate producer/consumer process and arithmetic reader, no DB/API/CLI/network
  or file mutation in calculation; accepted sources/old stored results/UI and bounded
  WSL ownership are preserved. Report old-validation and new-stage calls separately.

Further ordered tasks are coupled RK4/restore, new-law repeated funded events, then
immutable result/reader and same-state realistic 3D. The latter must show actual
saved A/L/C/age/ID/time/phase and e/b/deficit in mesh/table/graphs, preserve parent
attachments and navigation/reload, and identify decorative width/pose/fruit. No
wall-clock growth animation or interpolation as a calculated state. Keep rights
withdrawal/partial results and original views working. Final visual R2 and product
farm/worker integration remain separate acceptance items.

All outputs stay `software_research_only`, policy/version/parameter/source hashes
explicit, `G0_G4=not_assessed`, no harvest/profit/ranking. Independent local measurements
and rights-cleared cultivar/allometry data run in parallel with synthetic development.
