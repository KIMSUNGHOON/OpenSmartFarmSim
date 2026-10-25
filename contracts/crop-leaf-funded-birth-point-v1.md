# 명시한 새 잎의 구조 탄소 조달점 — synthetic research v1

Status: synthetic point accepted — [74focused/297related and36independent points](../research/crop-leaf-funded-birth-point-20261026.md). The current fixed-list
[Ci/a/A continuation](crop-leaf-carbon-stock-continuation-v1.md) remains unchanged.
[Source and decision](../research/crop-leaf-funded-births-design-20261026.md).

This operator represents **declared new structural growth from buffer**. It is not
a physiological law for organ emergence. Revealing biomass already paid for in a
hidden organ pool would require a different transfer and must not use this debit.
No area→mass/SLA inversion, default seed mass, inferred cultivar or new coefficient.

`apply_births(context, raw_checkpoint, expected_sha256, inputs)` accepts a prepared
current-stock context and externally trusted canonical CP bytes/hash. The closed
input specifies schema, input ID, synthetic origin, explicit policy, original
context/CP hashes, reduced exact elapsed seconds, original floor, and 1..512 events.
Each event specifies event ID, attachment internode ID, incoming temperature and
a complete current-stock leaf declaration. New IDs are unique and absent from the
old list; resulting list ≤512. Age must explicitly be zero; requested positive A
must match the existing normalized logistic F(0), tolerance1e-12 relative/0 absolute.
F(0) is **positive**, not zero. Positive initial Ci is independently declared in
mg_CH2O/m2_floor. Explicit sink/removal/base temperature/curve remain mandatory.
Attachment is a declared identity only; actual stem/source binding remains pending.

For same-floor B=Σnew Ci and original pinned cLeafG: Rg=cLeafG·B,
buffer_after=buffer_before−B−Rg>0. Existing Ci and all fruit/stem stocks remain
unchanged. Whole represented C changes by −Rg. No continuous allocation is
refunded: this is an additional explicitly declared point allocation, not a second
charge for an upstream continuous increment. Reject an unrepresentable/lost debit.

For each new leaf ΔK_i=k_leaf·A_i/floor and E_i=ΔK_i·(T_in_i−T_ref), using the
existing explicit k_leaf/T_ref. U_after=U_before+ΣE_i; K_after=K_before+ΣΔK_i.
The same after-state RHS derives canopy temperature. Incoming T is supplied,
never defaulted to canopy T. This is the existing reduced sensible-heat model;
chemical heat, organ water/solute inventories and a complete first law are absent.

Restore validates only current CP once; after-state RHS once. Do not prepare the
old geometry again, replay old steps, infer old A from age, or reset old D0.
Preserve original first107 scalars except buffer/U104, then concatenate old+new
age/A/C blocks. Old initial-gap receipts are preserved; new gaps use birth F(0).
Exact time, old transfers/prefix/CP and original program/seed/code/profile identity
remain in result. No elapsed step advances. End fences check current source pins.

Return immutable-before copies, explicit normalized after-program/state/layout,
same-time after sample/rates, input/calculation hashes, leaf receipts, point flows
and independently checkable C/buffer/new-stock/capacity/U balances. Bound input/output
2MiB. Closed quantities exclude bool/nonfinite/subnormal values. Fail atomically
with a typed hold; no result, CP mutation, DB/CLI/network/file writes. Scope is
software_research_only; G0_G4=not_assessed.

This first slice does **not** issue a resumable changed-topology checkpoint.
Following slice must adopt a versioned new context/point history, preserve global
clock/prefix/old D0 and continuous plus point ledgers, then integrate/save/replay.
Cross-history event replay prevention, original stem/emergence evidence, empty
canopy initialization, simultaneous removal, supply-limited area feedback and
actual cultivar measurements/rights remain parent requirements.

Acceptance: app-free Decimal checks for same-floor carbon debit/respiration and
capacity/energy, original6 cases/initial and continued CP, fractional exact time,
single/simultaneous births and 512-leaf boundary; zero/negative/duplicate/wrong
units/policy/floor/time/hashes/curve/temperature/budget rejection; current eval
counts and no reprepare/past advance; old A/Ci/D0/fruit/air/prefix bytes preserved;
source/profile fences, bounded output, copy isolation and WSL/protected-root proof.
