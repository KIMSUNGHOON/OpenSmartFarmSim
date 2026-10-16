# Solar input evidence v1

The accepted solar [context](crop-greenhouse-solar-continuation-v1.md),
[UTC](crop-greenhouse-solar-time-v1.md) and [files](crop-greenhouse-solar-storage-v1.md)
receive new source/evidence types and HMAC domain. Existing22/25-ledger evidence,
keys, profiles, equations and user services remain unchanged.

The same owned0700 directory/closed0400 six files and nofollow/single-link/
canonical JSON/size checks apply. `source.json` has version,scenario,solar,
ventilation,events,output_steps,step_seconds,step_count,time_origin and mandatory
`provenance`. All origins are synthetic. Four profiles and notice retain exact
accepted bytes. Source≤1MiB,profiles/notice≤128KiB,evidence≤2MiB.

Provenance reuses `provenance.SourceRecord`, including its safe HTTP(S) locator,
product/version/revision,observation/publication/availability/retrieval,source
reviewer/evidence ID and content identity. Its raw SHA binds canonical original
program fields excluding source version/provenance; whole source SHA binds both.
Synthetic author/method are mandatory; station/grid and request details are empty.
All four times are present; availability follows publication and precedes retrieval.
Every original quantity block, event quantity, dt and count has exactly one variable
with its original unit/instant semantics. Provider QC is explicitly not supplied;
project checks are separate passed **initial software contract** checks with this
QC version. All5 declared rights have allowed status and current review references.
These are owned synthetic declarations, not external rights or G0 approval.

The trusted current review resolver retains the six-field review shape and only
accepts this source SHA/status/synthetic-solar-software scope. Reviewer/evidence
IDs in provenance, project checks and rights match that current review. Changed,
missing,revoked,unknown or mismatched review/declarations hold.

`SolarInputEvidenceAuthority.issue` reads current bytes/review, reconstructs the
solar context with **one** composed PAR/NIR/ventilation/core RHS and exact UTC,
then binds the original context/program/initial full solar composition/41-ledger
identity/provenance/source-profile-code-policy hashes. No advance,management or
checkpoint restore occurs. Distinct HMAC domain/version binds issuer/key and QC/
normalization/source metadata. Key bytes are never placed in evidence or manifests.

`verify` requires trusted source/context/binding hashes and current server key/
review/raw/profiles/environment/code/provenance. It performs zero context/UTC
construction,numerics,restore or CLI. Issue/verify reread source/review before
return. Verified properties return copies and `rights_or_gate_approval=False`.
No unsigned fallback,model mixing or cached permanent authorization is accepted.

Acceptance:11 accepted programs preserve original source/solar/weather/initial
state/full composition/UTC/provenance; actual issue counts1each and verify/fresh0.
Reject missing/changed rights/QC/times/vintage/unit/coverage/source/raw hash,
mixed old evidence and scopes,code/profile/policy/environment/key/issuer changes,
late mutation/revocation,malformed files/JSON/path/FD and bounds; exercise128events/
512outputs and preserve frozen sources/results/five roots/512MiB+1GiB caps.

Synthetic software evidence only; G0–G4 not assessed. Farm/current rights,
server custody/database/API/worker/3D and real production/economic validation are
subsequent requirements. No real source is adopted by this contract.
