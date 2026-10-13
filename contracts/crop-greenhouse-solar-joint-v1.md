# Current-state PAR, virtual NIR and ventilation — v1

`evaluate_rhs(scenario=..., solar=..., ventilation=..., four profiles)` creates
`current-state-solar-ventilation-joint-rhs-research-v1`, without advancing time.
The previous [PAR adapter](crop-greenhouse-radiation-par-joint-v1.md), pure
[NIR](crop-greenhouse-radiation-nir-v1.md), ventilation, core profiles and saved
models remain immutable. This contract accepts no old total-canopy-heat,
non-PAR-only heat, supplied incident photons, or supplied LAI.

Scenario has the closed core joint blocks, with forcing `canopy_non_solar_heat`
in W/m2_floor replacing the PAR adapter's `canopy_non_par_heat`. It explicitly
excludes this boundary's solar PAR/NIR. Other forcing is the explicit complement
to ventilation air sensible/vapor; labels alone cannot prove those meanings,
so future server admission must bind component definitions/evidence.

`solar` has input_id/origin/values. Its exact quantity union is the PAR solar
input excluding LAI, plus NIR inputs excluding LAI and duplicate global radiation/
construction fraction. One shared outdoor global-radiation coordinate and
construction fraction apply; spectral PAR+NIR fractions must sum to1 in binary64.
This is an explicit two-band research assumption, not inferred spectrum data.
Units/domains are those of the two pure boundaries. No actual NIR transmission
or new optical defaults. `ventilation` has the existing closed outdoor forcing;
all three origins must match.

Derive LAI from pinned SLA×positive current leaf. Evaluate NIR once; evaluate
ventilation once from current air/vapor; add its sensible/vapor contribution
once to other air forcing. Pass explicit non-solar heat+absorbed NIR as the
PAR adapter's non-PAR complement. That adapter evaluates PAR and core RHS once,
preserving its incident-photon coordinate and same current temperature/capacity.
The actual combined heat uses these recorded sequential sums; no extra RHS,
temperature substitution, floor/cover/reflection/construction-to-air heat credit
or duplicated crop interception is introduced.

Return normalized original scenario/solar/outdoor input, PAR/NIR/ventilation and
original joint result, explicit non-solar/PAR/NIR/combined heat, component code/
policy/source/notice/input/calculation hashes. Verify same trial LAI and one
shared construction/global coordinate. No RK/UTC/context/checkpoint/store/API/3D.
`software_research_only`, `synthetic_current_state_solar_ventilation_rhs_only`,
`G0_G4=not_assessed`. Source virtual NIR optics and unallocated cover/floor/air
paths prevent a whole-greenhouse heat-closure claim even with the two-band sum.

Acceptance: independent Decimal80 PAR/NIR and outdoor air equations compose the
existing app-free whole-joint oracle for day/dark/reverse-air/signed-other-heat/
changed-leaf cases; all117 scalars/case within relative5e-12/absolute5e-14 and
seven core balances. Actual one-call capture/current state/once-only composition,
no double interception or unallocated heat credit, dark same-state behavior,
immutable inputs/replay/new identity and closed mixed-origin/schema/unit/spectral/
profile/numeric holds. Existing pure boundaries/PAR adapter and required five
roots, original source/assets/FD/owned cleanup/resource caps must pass. Next:
every shared RK trial and independent trajectories; new immutable runtime/data/
same UTC3D acceptance; corresponding field/data/production claim gates stay held.
