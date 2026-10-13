# Current-state solar and ventilation acceptance — 2026-10-13

Accepted [current-state composition](../contracts/crop-greenhouse-solar-joint-v1.md)
and [code](../backend/app/crop_greenhouse_solar_joint.py), following
[pure virtual NIR](crop-greenhouse-radiation-nir-implementation-20261013.md).
[Machine evidence](artifacts/crop-greenhouse-solar-joint-implementation-20261013.json)
records actual native `gpt-6.1-sol`/`xhigh` context/output hashes and protected
tool exits. No recursive CLI. Actual farm Runs0/G0–G4 `not_assessed`.
This is one shared instantaneous state; NIR time integration/storage/3D is
still pending and the accepted ventilation user service stays unchanged.

## Same-state composition

One explicit solar input supplies global radiation, construction interception
and PAR+NIR energy fractions summing to1 under the named two-band research
assumption. Current leaf/pinned SLA supplies one LAI to both optical paths.
Current air temperature/vapor supplies ventilation; current signed canopy
energy/capacity supplies the unchanged crop/exchange temperature.
One NIR calculation, one ventilation calculation, one PAR calculation and one
core joint RHS are called. The crop receives **incident PAR photons**, retaining
its existing single interception. Explicit non-solar heat+absorbed NIR becomes
the existing PAR adapter's non-PAR complement; that adapter adds absorbed PAR.
Ventilation adds sensible/vapor contributions once to the other air forcing.

Old total heat/non-PAR heat/incident PAR/LAI inputs are rejected. The normalized
original scenario and all source/notice/component/policy/input/calculation hashes
remain auditable under a new identity. Caller labels cannot establish physical
provenance: future server admission must bind the component definitions and
evidence before accepting real inputs. Virtual NIR cover/floor/reflection and
unallocated construction receive no canopy/air credit; this is not a physical
whole-greenhouse or total exterior solar thermal closure.

## Passed verification

Original32002:0: **25 new tests**,0.35s pytest. After adding explicit source/notice
identity fields, original24554:0 verified the final code: **415 focused tests,
0 skipped**,1.44s pytest/1.973s guard. They include pure NIR95, prior PAR/RHS and
unchanged growth/joint/ventilation consumers; the prior441-test PAR RK evidence
remains valid for its unchanged version.

Five independent Decimal80 whole-stage examples compare **585 scalars**:
derived quantities, plant/100 cohort/climate rates and exchanges. PAR/NIR
independent optics plus outdoor sensible/vapor equations supply the existing
app-free original joint oracle. Day/dark, reverse outdoor air, signed non-solar
heat and changed leaf pass relative5e-12/absolute5e-14 and all seven core
balance budgets. Actual call capture confirms shared LAI/air state, incident
photon coordinate and once-only heat/air sums. Changing NIR optics alters
canopy heat without changing instantaneous photosynthesis/air rates; darkness
removes both solar contributions. Replay/immutable inputs and closed spectral/
schema/unit/origin/profile/singular/numeric holds pass.

The guard preserves **five required live roots/dynamic descendants**, both frozen
UI source/asset sets,2,148 original entries, HTTP5173, FD4→4 and owned process/
PG/passfile0. Peak136,171,520bytes/PID,858,079,232bytes combined, seven nominal
0.25s samples;512MiB/PID/combined1GiB limits unchanged. No source/config changed
during the guard. Full CI, current browser/WebGL, whole DB repetition and actual
farm validation were not run for this additive instantaneous calculation.

## User-visible record and next step

Both localhost5173/5174 development feeds identify the NIR/solar work as **not
deployed**. The existing scene continues its accepted ventilation model.
This publication changes status data only; it does not accept current DOM or
new 3D behavior. No arbitrary animation represents these numerical results.
Original98866:0 verified both actual HTTP feeds200/`no-store`, byte-identical
to the reviewed19:38:28KST source, SHA-256
`57776218b9fb0112de449c8baf4ba7b5991b65ee932fd7050fd569ec6152da7f`.
Five roots/2,173 frozen ventilation files/old UI sources and assets/FD4→4/
owned cleanup0 passed; combined peak815,382,528bytes. Current DOM was not rerun.

Next implement PAR/NIR/ventilation on **every shared RK trial**, preserving old
integration/profile/immutable result identities. Acceptance requires independent
full108-state and component-transfer trajectories, explicit PAR/NIR/non-solar
heat partitions, step reduction, dark/changed-leaf behavior, manual split/last
confirmed holds and original service/resource preservation. Then bind a **new**
input/context/checkpoint→store/API→same UTC3D and test normal/hold/cancel/current
rights before user adoption. The NIR parent and PAR runtime parent remain open.

Actual local optical/facility/cultivar/weather and independent local/future farm
and market/economic records remain external dependencies. Development may use
explicit synthetic inputs; production, future margin and crop rankings require
their corresponding gates. Overall completion date and remaining implementation
hours are unknown. Automatic goal state is still usage-limited; user-delegated
manual continuation does not change it. No push or full CI was performed here.
