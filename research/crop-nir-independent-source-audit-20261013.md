# Independent NIR primary-source audit — 2026-10-13

The pinned GreenLight NIR boundary is an ordered **virtual cover → canopy →
floor** calculation. Its final transmission is assigned to floor absorption;
its final absorption belongs to the canopy. Actual cover transmission is not
an extra multiplier in these two source heat equations. This audit confirms
the algebra and its limits, without adopting optical coefficients, farm data,
an implementation, or a claim gate.

Reviewer: native delegated CLI thread `/root/nir_primary_evidence`, thread ID
`01a134c1-6bbe-7302-b173-31c0a8b94fc4`, parent session
`01a0e064-b01b-7a22-8ef8-dd4afe0eb7dc`. Actual child `session_meta` identifies
that parent and agent path. Actual child `turn_context` at
`2026-10-13T10:14:14.884Z` records **`gpt-6.1-sol` / `xhigh`**; raw context-line
SHA-256 is `852d2d76da1e28b103a17524802cfea1ac162a72ceec4750ea12919d2987980b`.
The invocation was a delegated thread in the existing native CLI, with the
exact model/effort requested by the parent. No CLI was launched recursively.
The native child rollout retains the actual invocation context and outputs;
this note is the review output, not deterministic gate approval.

## Source custody and rights

Primary source: [GreenLight Chapter 8 at commit
7a7b36870135aa38bbe81e65590dcf5473786bdd](https://raw.githubusercontent.com/davkat1/GreenLight/7a7b36870135aa38bbe81e65590dcf5473786bdd/greenlight/models/katzin_2021/definition/vanthoor_2011/greenhouse_vanthoor_2011_chapter_8.json).
The retained private raw file was independently read and hashed: 130,649 bytes,
SHA-256 `c0fb7a025533f15b80cb6cd60aafdc19be9fe42df6b8183cf97b83fc086138b3`.
JSON parsing and exact definition/pointer inspection succeeded. The existing
[source register](crop-par-source-register-20261013.json) records retrieval
`2026-10-13T08:17:44.443683+00:00`, product/revision, QC and custody.
`observed_at`, `published_at` and `available_at` remain null; this is model
software rather than an agricultural observation. Dimensionless optics and
source heat units `W m**-2` apply; floor-area normalization remains the
project's explicit interpretation.

The pinned [Clear BSD license](https://raw.githubusercontent.com/davkat1/GreenLight/7a7b36870135aa38bbe81e65590dcf5473786bdd/LICENSE.txt)
permits use and source/binary redistribution subject to preserving its notice,
conditions and disclaimer; endorsement requires permission and no patent
license is granted. The [retained notice](../LICENSES/GreenLight-BSD-3-Clause-Clear.txt)
hash was independently confirmed as
`96ce8c1f3d7b5473f473417c2785c63b74148edaddc2b9b6d40a6bbe3b7f4b6a`.
These permissions do not automatically cover cited papers, observations or
other third-party material. No raw content is republished here.

## Exact source order and meanings

Use prefix `P=/Heat fluxes/Global, PAR and NIR heat fluxes/`; joining `P` with
each name below gives its original JSON pointer. The three original function
pointers are `/Lumped cover layers/functions/` followed by the exact function
names `tau12(tau1, tau2, rho1Up, rho1Dn, rho2Up, rho2Dn)`,
`rhoUp(tau1, tau2, rho1Up, rho1Dn, rho2Up, rho2Dn)` and
`rhoDn(tau1, tau2, rho1Up, rho1Dn, rho2Up, rho2Dn)`.

For top layer 1 and bottom layer 2 their source definitions are:

```text
tau12 = tau1*tau2/(1-rho1Dn*rho2Up)
rhoUp = rho1Up+tau1**2*rho2Up/(1-rho1Dn*rho2Up)
rhoDn = rho2Dn+tau2**2*rho1Dn/(1-rho1Dn*rho2Up)
```

Define source aliases `c=rhoCovNir`, `f=rhoFlrNir`,
`t=exp(-kNir*lai)` and `r=rhoCanNir*(1-t)` for the following transcription:

| Pointer suffix | Definition or exact layer arguments |
| --- | --- |
| `tauHatCovNir` | `1-c` |
| `tauHatFlrNir` | `1-f` |
| `tauHatCanNir` | `t` |
| `rhoHatCanNir` | `r` |
| `tauCovCanNir` | `tau12(1-c,t,c,c,r,r)` |
| `rhoCovCanNirUp` | `rhoUp(1-c,t,c,c,r,r)` |
| `rhoCovCanNirDn` | `rhoDn(1-c,t,c,c,r,r)` |
| `tauCovCanFlrNir` | `tau12(tauCovCanNir,1-f,rhoCovCanNirUp,rhoCovCanNirDn,f,f)` |
| `rhoCovCanFlrNir` | `rhoUp(tauCovCanNir,1-f,rhoCovCanNirUp,rhoCovCanNirDn,f,f)` |
| `aCanNir` | `1-tauCovCanFlrNir-rhoCovCanFlrNir` |
| `aFlrNir` | `tauCovCanFlrNir` |
| `rNirSunCan` | `(1-etaGlobAir)*aCanNir*etaGlobNir*iGlob` |
| `rNirSunFlr` | `(1-etaGlobAir)*aFlrNir*etaGlobNir*iGlob` |

These equations are in the pinned [Chapter 8 source](https://raw.githubusercontent.com/davkat1/GreenLight/7a7b36870135aa38bbe81e65590dcf5473786bdd/greenlight/models/katzin_2021/definition/vanthoor_2011/greenhouse_vanthoor_2011_chapter_8.json).
Both virtual outer layers have transmission plus reflection equal to one.
Their transmission therefore represents escape into the assigned outer
channel, rather than absorption inside those virtual layers. The source
explicitly interprets downward escape as physical floor absorption.
`/Lumped cover layers/NIR/rhoCovNir` aliases `rhoCovNirVanthoorUp`; the virtual
cover uses that same value on both faces. Actual cover lower-face reflection
and actual `tauCovNir` do not enter this virtual partition.

The canopy heat enters `/State equations/Temperature states/tCan`; the floor
heat enters `/State equations/Temperature states/tFlr`. The source's
`P/rGlobSunAir` additionally has NIR contribution
`etaGlobAir*(aCanNir+aFlrNir)*etaGlobNir*iGlob`.
`P/rGlobSunCovE` separately uses actual `aCovNir`. Crediting the actual cover
term in addition to a complete virtual exterior partition needs its own
accounting review. Virtual reflection is not an air-heating prescription.

## Independent mathematical derivation

The following is a project derivation from two incident canopy streams,
independent of the source's layer-composition procedure. Set
`a=(1-rhoCanNir)*(1-t)`, `x=1-c`, `y=1-f`; then `t+r+a=1` in exact arithmetic.
Normalize exterior incident NIR to one. If `d` and `u` are the downward and
upward streams incident on the canopy, the cavity balances are
`d=x+c*(r*d+t*u)` and `u=f*(t*d+r*u)`. Solving gives:

```text
D = (1-c*r)*(1-f*r)-c*f*t*t
  = x*y+(c*y+x*f)*(t+a)+c*f*a*(a+2*t)
d = x*(1-f*r)/D
u = x*f*t/D

Acan = a*(d+u) = a*x*(y+f*(a+2*t))/D
Afloor = y*(t*d+r*u) = x*y*t/D
R = c+x*(r*d+t*u)
  = c+x*x*(r*(y+f*(t+a))+f*t*t)/D
```

The sum `Acan+Afloor+R=1` follows from the two stream balances. Every term
in the factored determinant and every absorption/reflection numerator is
nonnegative on the passive domain. These expressions equal the ordered
source result where both source denominators are positive:
`D1=1-c*r`, `D2=1-f*rhoCovCanNirDn`, `D=D1*D2`.
This is a virtual optical balance, not a proof of total farm energy balance.
For the source prefactor `S=(1-etaGlobAir)*etaGlobNir*iGlob`, the three virtual
channels sum to `S`; their destinations in the reduced model still require
explicitly declared boundaries.

The parent's proposed stable layer evaluation is also algebraically sound:
`D1=(1-c)+c*(t+a)`, top absorption `A1up=(1-c)*a/D1`, bottom absorption
`A1dn=a*(1+c*t/D1)`, and
`D2=(1-f)+f*(tauCovCanNir+A1dn)`.
Top and bottom incidence respectively obey
`T1+R1up+A1up=1` and `T1+R1dn+A1dn=1`.
Final canopy absorption is `A1up+T1*(f*A1dn/D2)`; floor absorption is
`T1*((1-f)/D2)`. This avoids evaluating canopy absorption by cancellation in
`1-T-R`. Ratio-first grouping avoids losing a tiny product before dividing
by a small denominator. These are equivalent arithmetic rearrangements,
not extra optical coefficients or new physics.

## Limits and focused acceptance suggestions

Assume explicit `c,f,rhoCanNir` in `[0,1]`, nonnegative finite `kNir,lai`, and
representable operations. For finite attenuation, mathematical `t>0` and
`D1>=t>0`; finite arithmetic can still lose this property through underflow
or cancellation. `q=-expm1(-kNir*lai)` preserves small positive `1-t` for
near-zero attenuation. A negative residual caused by `1-T-R` must not be
silently clipped into an accepted zero. Use the documented equivalent
nonnegative calculation or an explicit numerical hold.

Suggested independent checks, **not executed in this audit**:

1. Compare ordered source composition against the two stream solution above
   using independently written high-precision arithmetic. Check each
   directional coefficient and both denominators, not only their final sum.
2. `lai=0` or `kNir=0`: `t=1,r=a=0`, canopy absorption is zero and floor
   absorption is `(1-c)*(1-f)/(1-c*f)` whenever `1-c*f>0`.
3. `c=f=0`: canopy absorption is `a`, floor absorption is `t`, reflection is
   `r`. A perfectly reflecting canopy (`rhoCanNir=1`) has zero absorption.
   A perfectly reflecting floor has zero floor absorption when denominators
   remain valid. A perfectly reflecting cover admits no exterior energy.
4. Exact `c=f=1` with `a=0` gives `D2=0`, including the transparent-canopy
   case. Generic source composition is undefined. Zero irradiance does not
   validate undefined optics; a special limiting branch would require an
   explicit, separately reviewed contract. Do not add an epsilon denominator.
5. Approach each regular limit from admissible values, including nearly
   transparent and nearly lossless canopy, reflective cover/floor, and large
   attenuation. Verify positive channels, conservation and explicit holds for
   nonrepresentable positive quantities. A thick-canopy limit with regular
   denominators has floor absorption tending to zero.

Only this note was written. Raw/pointer/license hashes and the native metadata
were inspected; no tests, model trajectories, application/fixture/config
edits, database or browser operations, service control, or new CLI invocation
were performed. Domestic optical applicability, measured climate/resource
validation and all associated claim gates remain held.
