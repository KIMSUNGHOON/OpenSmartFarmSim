# Bound supply-limited organ RHS, research v1

Implements the one-stage portion of the [design contract](crop-supply-limited-morphology-v1.md).
The design's historical status and original source pins stay immutable. Evidence is
[recorded separately](../research/crop-supply-morphology-rhs-20261028.md).

`crop_supply_morphology_rhs.evaluate_bound_rhs(context, raw_checkpoint,
expected_sha256=..., inputs=...)` accepts a genuine `crop_organ_repeat.Context`
and its actual checkpoint bytes/trusted SHA before the original horizon. It authenticates
the original/current source pairs, complete ordered inventory, birth/clock/parent bases,
current A/C/D0, rights and pinned reference objects. No older typed handle is fabricated.

The closed `inputs` schema is `supply-morphology-stage-input-v1` with `input_id`,
`origin='synthetic'`, `policy='marginal-construction-extension-v1'`,
`parameter_revision`, `parameter_source='own_declared_synthetic_assumptions'`,
`reviewer`, the original explicit synthetic rights declaration structure,
`context_sha256`, `checkpoint_sha256`, original `model_floor_area`, and ordered
`leaves`/`internodes`. Each row contains the actual `leaf_id`/`compartment_id` and
an explicit positive `construction_cost`, respectively `mg_CH2O/m2_leaf` or
`mg_CH2O/m_internode`. There are no numerical defaults or real cultivar coefficients.
Input/output bounds are 128 KiB/2 MiB; the incoming CP retains its original 512-KiB bound.

The result preserves the original state prefix and appends internode numerical ages
and legacy potential lengths initialized from their actual selected/birth baselines.
Its `organs` record preserves exact clocks/roundoff, original anchors, actual parents,
distinct material/threshold sequences and unbound initial leaf parents. Roots have no
new geometric clock. Historical geometry–carbon compatibility remains `not_assessed`.

`stage` contains actual allocated stock flows/maintenance, potential/realized leaf
and internode rates, extension/unmapped construction accounts, adjusted carbon rates,
same-state capacity/exchange/climate rates and instantaneous balance residuals/budgets.
Underlying carbon→partition→construction→capacity/climate kernels execute once per
new stage. The incoming CP's one old current-RHS validation and branch length-point
evaluations are separately reported. This function performs no time integration,
material jump, initialization, DB/network/CLI/file write or event adoption.

Zero-supply organs retain zero extension even if potential is positive. Positive
supplies can be supply- or demand-limited; unmapped inflow does not incur another
buffer debit or growth respiration and does not imply thickness/reserve/harvest.
Supported domain and explicit holds follow the design contract, including zero
vegetative removal/capacity outflow. Current/late source, code, profile and parameter
changes prevent a result; unexpected RuntimeError propagates. Returned data is copied.

All results remain `software_research_only`, `G0_G4=not_assessed`, no production,
economic forecast or recommendation. A result is not an integrator CP and advances
zero elapsed seconds. Shared RK4/resume, new-law repeated births and immutable
same-state realistic 3D are the following separately accepted implementation stages.
