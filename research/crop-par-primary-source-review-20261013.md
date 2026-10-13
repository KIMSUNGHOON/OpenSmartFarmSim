# Solar PAR primary-source review — 2026-10-13

Decision: first implement an instantaneous, prescribed **solar PAR** boundary
using the unchanged crop optics. Pass incident photons to the existing crop
consumer, report PAR absorbed heat separately, and retain unresolved reflected
radiation as a boundary remainder. The NIR multilayer model and a joint-stage
adapter are subsequent work. [Calculation contract](../contracts/crop-greenhouse-radiation-par-v1.md).

## Actual research context and source custody

The current native Codex CLI session is
`01a0e064-b01b-7a22-8ef8-dd4afe0eb7dc`, model **`gpt-6.1-sol`**, effort **`xhigh`**.
Observed turn context `2026-10-13T08:15:40.478Z`, raw line SHA-256
`d047b64be278fc6dce48d81efaf954b5776afe993b51bab0f94b5c5f38a7850c`.
No recursive CLI was launched. The research skill requested a background
primary-source reader with the exact model/effort; it failed before research
with a model-capacity error. This proven native session performed and reviewed
the work directly; no alternate model supplied a decision.

The [source register](crop-par-source-register-20261013.json) records exact
URLs/product commit, retrieval UTC, bytes/hashes, units, QC, rights and reviewer.
All observation/publication/`available_at` timestamps are null: model code is
not an agricultural observation, and first public availability was not
reconstructed. Its stated creation date is not a decision-availability date.
New raw code snapshots and native context/output are retained privately under
`~/.local/state/OpenSmartFarmSim/20261013-radiation-par/`, immutable mode0400.
The initial retrieval-register writer attempted to overwrite an immutable file;
that metadata attempt failed and is retained. Complete v2 retrievals are the
reviewed register. No farm data, secrets or gate approvals were created.

## Primary equations and dimensional interpretation

Pinned [GreenLight Chapter8](https://raw.githubusercontent.com/davkat1/GreenLight/7a7b36870135aa38bbe81e65590dcf5473786bdd/greenlight/models/katzin_2021/definition/vanthoor_2011/greenhouse_vanthoor_2011_chapter_8.json)
defines the incident and down/floor-reflected absorbed PAR under
`/Heat fluxes/Global, PAR and NIR heat fluxes/`, final pointer segments
`rParGhSun`, `rParSunCanDn`, `rParSunFlrCanUp`, `rParSunCan`, `rParSunFlr`, `parCan`.
The equations are transcribed and implemented in the linked contract. Source
energy units are `W m**-2`; floor normalization is the project's declared area
interpretation, consistent with the existing crop LAI and capacities.
Photon conversion is `/Parameters/parJtoUmolSun`, source reference4.6µmol/J.
`/Parameters/Table 8.1/etaGlobPar` is the separate solar energy fraction0.5.
Both remain explicit research inputs; neither value is a domestic facility
measurement or a universal conversion of global radiation to PAR.

The [standalone crop extension](https://raw.githubusercontent.com/davkat1/GreenLight/7a7b36870135aa38bbe81e65590dcf5473786bdd/greenlight/models/katzin_2021/definition/vanthoor_2011/extension_crop_vanthoor_2011_for_standalone.json)
uses `/Auxiliary states/parGhCan`, `parFlrCan`, `parCan` with the same four
optical constants retained in the existing growth profile. The actual
[crop consumer](../backend/app/crop_growth_rates.py) already performs this
interception; passing absorbed photons into its incident field repeats it.

## Model limitations and project derivation

The source's PAR path includes one floor reflection. Its canopy reflection
factors reduce absorption but do not supply a complete repeated-reflection
transport solution. This project's positive remainder derives from subtracting
canopy and floor absorption from incident PAR; it must remain unallocated.
The exterior ledger splits downward incident PAR using explicit lumped cover
transmission/reflection and construction interception. These bookkeeping
categories do not add new source heat equations or infer where the remaining
light ultimately heats the structure, air, floor or cover.

In particular, `rParCan` has a source description suggesting incident radiation
but its expression aliases absorbed `rParSunCan`. The expression and the actual
consumer determine the interface; that description does not authorize a change
to the existing incident-photon contract. Source `tauCovPar` is also described
as reflection while its expression aliases transmission. Both mismatches are
recorded rather than propagated as unit/coordinate decisions.

The [earlier NIR review](crop-greenhouse-boundary-source-review-20261011.md#solar-radiation-par-interception-and-canopy-absorbed-heat)
documents a different virtual-cover/canopy/floor multilayer approximation.
PAR absorption cannot be reported as total absorbed solar energy. Before
joint integration, NIR and remaining canopy heat must have a distinct input
identity and an explicit sum policy; purchased energy remains unrelated.

## Rights and falsification

The pinned [BSD-3-Clause-Clear license](https://raw.githubusercontent.com/davkat1/GreenLight/7a7b36870135aa38bbe81e65590dcf5473786bdd/LICENSE.txt)
permits source/binary use and redistribution under its notice, disclaimer and
non-endorsement conditions, and grants no patent rights. The exact existing
[notice](../LICENSES/GreenLight-BSD-3-Clause-Clear.txt) is retained. Equation
adaptations and original synthetic fixtures are covered by this review; rights
to cited theses, linked datasets and images are not inferred.

Acceptance requires an independent80-digit original-form reference, positive
interior/exterior partitions, limiting cases and invalid-input holds. The actual
unchanged crop consumer must match an independent subtraction-root electron
transport reference with incident photons, and fail that equality with photons
intercepted twice. This proves the algebraic interface only. Real solar spectra,
facility optics, regional weather and independent local/future crop validation
remain external holds; G0–G4 stay `not_assessed`.
