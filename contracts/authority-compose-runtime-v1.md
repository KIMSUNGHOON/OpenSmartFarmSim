# Scoped authority/supervisor/dispatcher Compose v1

Status: [hosted regional hold software acceptance passed](../research/authority-compose-runtime-implementation.md#corrected-actual-hosted-acceptance)
atb8df8f9. Combined owned-source orchestration/whole-head regression remain pending.
Observed failures and focused fixes are in the
[implementation record](../research/authority-compose-runtime-implementation.md).

The first `098d1d3` hosted stage closed the research job as hold but did not
produce the expected validated public hold report. A local actual SCRAM
regression reproduced `invocation_evidence_withheld`: the private fixture's
evidence callback took four arguments instead of the existing six-argument
storage contract. Correcting the fixture produced the original registry's
two-missing-evidence validated hold (RED1/2.55s, GREEN1/2.51s). Production storage,
rights gates and isolation guard are unchanged. Hosted signed/separate-UID
acceptance remains pending; the corrected harness asserts the public reason
`ai_validated_hold` before reading the hold report.

The corrected `4083bd6` hosted stage produced that validated hold and both
public missing-evidence categories, then failed its operator inspection.
Actual SCRAM/supervisor regression reproduced `KeyError: disposition` because
`list_decisions` is a restricted metadata projection. Inspection now reads the
tenant/job/attempt-scoped immutable decision row directly, preserves the public
projection and verifies the stored signature/capture relation. Its same signed
local path passed1/3.85s after RED1/4.09s. A preceding instant fake child failed
closed with `execution_attestation_unverified`; the fixture uses the existing
`valid_slow` fake mode, as the separate supervised tests do. This is synthetic
test timing, not a production timing or execution guarantee. Hosted acceptance
remains pending.

The additive `compose.authority.yaml` follows the C0/application files, with
profile runtime. It deploys the existing exact factory entrypoints:
`app.cli_supervise`, `app.cli_authority` and `app.cli_dispatch_loop`. It provisions
no source approvals, production executable, credentials, migration or release
authority. The production CliWorker isolation guard stays closed; the hosted
factory is explicitly synthetic.

## Private process and IPC boundary

| Process | UID / primary GID | Mounts and access |
| --- | --- | --- |
| Authority | 11001 / 11010, supplemental11020 | Its own readonly private factory/authority SCRAM/public key; artifact writer; supervisor socket readonly; own dispatcher socket writable |
| Supervisor | 11003 / 11020, supplemental11010 | Its own readonly private factory/supervisor SCRAM/private signing key/fake executable/private CLI home; artifacts readonly; own socket writable |
| Dispatcher | 11004 / 11030 | Authority socket readonly; no artifacts/private credential/key mounts; no network |

Authority and supervisor socket directories are respectively owned by
11001:GID11030 and11003:GID11020, mode02750 (setgid, no group write); existing services create0660 sockets
and enforce exact peer UID. Dispatcher expects authority11001; authority accepts
dispatcher11004; supervisor accepts authority11001 and authority expects
supervisor11003. Readonly IPC mount does not grant directory modification.
Protected private directories/files retain0700/0600 and explicit no-follow
validation in trusted factories. The explicit artifact ContentAccess policy is
owner11001/reader GID11010, directories0750/files0640 with no POSIX ACL.

API and simulation remain the same writer class as authority. A supervisor's
fake child still shares its UID/key access; the fixture controller provisions
all keys/accounts. These are observable process/mount distinctions, not
independent custody or production per-job containment. Product CLI installation,
per-job credentials/egress/cgroups and execution attestation need separate proof.

Required operator inputs: authority/supervisor private directory and trusted
factory references, both existing socket directories and a fixed RPC tenant.
No user request chooses these. Roots are readonly, capabilities dropped,
no-new-privileges andPID64; authority/supervisor/dispatcher memory limits
768/512/128MiB and CPU0.5/0.5/0.25. Temporary space and logs are bounded; restart
is explicit. DB/supervisor/socket health dependencies order startup. Socket
existence is only startup readiness; peer/role/rights checks still govern RPC.
Existing socket paths are refused rather than silently removed or retried.

## Required acceptance

The actual hosted application harness uses normal TLS/Bearer location admission,
the original immutable ResearchRegistry contract and a fake executable under
the separate supervisor. Automatic dispatch must produce the server-derived
hold for missing source evidence/signed context, retain real invocation/capture/
signature references and allow only current authorized hold lookup. It must not
turn that hold into collection admission or approve a crop/source/Run.

Inspect actual UIDs, mounts, readonly/resource/peer/credential boundaries. Graceful
restart must remove/recreate owned sockets and preserve the same held job/report;
fresh peer/grant denial must fail closed and stop unresolved dispatcher polling.
All test containers/volumes/passwords/keys/socket directories/tags are removed,
including failure paths. Existing separate economic/collection runtime checks
must continue to pass. General owned-source success orchestration and collection
review/assessment dispatch, actual product model/independent release/G0–G4 remain
subsequent evidence; this increment verifies the initial regional research hold.
