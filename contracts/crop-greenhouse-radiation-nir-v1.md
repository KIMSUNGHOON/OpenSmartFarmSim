# Prescribed virtual solar NIR boundary — v1

`calculate_nir(scenario=...)` is a new instantaneous research calculation,
`prescribed-virtual-solar-nir-boundary-research-v1`. It adopts the pinned
[source equations/rights register](../research/crop-nir-source-register-20261013.json)
and [independent source audit](../research/crop-nir-independent-source-audit-20261013.md).
No existing PAR/crop profile or model identity changes.

## Input and source approximation

Closed object: `input_id` nonblank string1..200, `origin` exactly `synthetic` or
`reference_calculation`, `values` exactly the following `{value,unit}` quantities.
Values are finite int/float excluding bool; no defaults or inferred coefficients.

| Quantity | Unit | Domain |
| --- | --- | --- |
| outdoor_global_radiation | W/m2_floor | >=0 |
| solar_nir_fraction | 1 | [0,1] |
| leaf_area_index | m2_leaf/m2_floor | >=0 |
| nir_extinction_coefficient | m2_floor/m2_leaf | >=0 |
| cover_nir_reflectance | 1 | [0,1] |
| canopy_nir_reflectance | 1 | [0,1] |
| floor_nir_reflectance | 1 | [0,1] |
| construction_interception_fraction | 1 | [0,1] |

Floor-normalized prescribed radiation is a research coordinate, not an automatic
weather/geometry conversion. Let c/f denote cover/floor reflectance, t=exp(-k*LAI),
r=rhoCan*(1-t), a=(1-rhoCan)*(1-t). Virtual cover transmission is1-c,
virtual floor transmission1-f. Use source `tau12/rhoUp/rhoDn` **cover+canopy,
then +floor**. Do not substitute actual cover transmission or multiply it again.
Final virtual transmission is attributed to floor absorption. The source treats
only canopy as absorbing in the virtual stack; this is an optical approximation,
not an actual cover/floor thermal model. Real cover lower-side reflectance and
actual cover absorption are absent here.

## Stable algebra and partition

Use expm1 for1-t; source-equivalent positive expressions for absorption and
reflection denominators avoid subtracting almost equal values:

```text
x=1-c; y=1-f
d1=x+c*(t+a)
T1=x*t/d1; Rup1=c+x²*r/d1; Rdn1=r+t²*c/d1
Aup1=x*a/d1; Adn1=a*(1+c*t/d1)
d2=y+f*(T1+Adn1)
F=T1*y/d2
A=Aup1+T1*f*Adn1/d2
R=Rup1+T1²*f/d2
```

These are algebraic forms of the ordered source equations. Source1-T-R and
separate two-stream cavity equations are independent Decimal80 checks.
No clipping, epsilon denominator, guessed absorption or singular-case fallback.
Zero d1/d2, nonfinite/negative derived values, lost nonzero products/divisions
or attenuation underflow hold even when radiation is zero. Exact analytical
zero absorption is retained. Fraction roundoff may exceed1 by at most32ULP(1);
the actual residual is exposed, not clipped. Verify both cover+canopy incidence
partitions and final A+F+R=1 within32ULP at their largest magnitude.

N=G*solar_nir_fraction, V=(1-construction)*N. Return canopy=V*A, floor=V*F,
upward=V*R and construction_unallocated=construction*N. Their sum must equal N
within32ULP at the largest energy component. This is a **virtual NIR partition**;
construction is unallocated, not automatically air heat. Source `rGlobSunAir`
uses a different explicit expression; source actual `aCovNir` also belongs to
a different physical cover path. Neither is added to this partition.

Output carries normalized inputs, code/policy/source/notice/input/calculation
hashes, derived fractions/denominators, energy terms and residual/budget quantities.
`software_research_only`, `synthetic_virtual_solar_NIR_math_only`,
`G0_G4=not_assessed`, no state advance, photons, total solar/whole greenhouse
heat closure, air/floor thermal advance, actual farm prediction or deployment.

## Acceptance before implementation

Independent Decimal80 ordered source and cavity agree within1e-70; product
coefficients/heat agree relative2e-13/absolute0, analytic zeros exact. Cases
use exact binary64 input values in the oracle to separate arithmetic error from
decimal-to-binary input quantization, especially near perfectly reflecting layers.
Cases
cover ordinary/dark/zero LAI/k, lossless canopy, fully reflective cover/floor,
near-singular/very sparse/dense canopy, transparent cover and black floor.
Verify conservation/limits, scaling, optical-schema/units/bounds/singular/numeric
holds, input immutability/replay/identity, and that PAR formulas/extra actual cover
transmission are rejected. Existing PAR/ventilation consumers, required five
live service roots, originals/source/assets/FD/owned cleanup and512MiB/PID/
combined1GiB limits are preserved. Later: new solar joint/RK composition with
separate non-solar heat, then new immutable context/store/API/UTC3D acceptance.
