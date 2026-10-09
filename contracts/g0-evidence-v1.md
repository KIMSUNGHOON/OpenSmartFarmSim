# G0 authority evidence v1

This contract connects the source metadata in `backend/app/provenance.py` to the
G0 evaluator in `backend/app/gates.py`. It governs storage and decision evidence;
it does not approve any actual provider or grant provider rights.

## Authority boundary

`G0Authority` obtains an authenticated tenant, reviewer identity, and scoped
capability from a server supplied `principal_provider`. It also requires a
server configured `review_resolver(tenant_id, evidence_id)` backed by independently
reviewed material. Registration, policy
approval, source review, variable check review, rights review, revocation, and
evaluation each require their own capability. The request cannot supply a
principal, signing key, raw reader, or approved evidence object. A proposed
policy's reviewer and approval timestamps are replaced with the authenticated
reviewer and server time. The approved policy always requires `observed_at`,
`published_at`, and `available_at`, even if a privileged proposal omits them.
The reader projects these minimum requirements onto older signed policy rows
before evaluation, while preserving the original approved digest in the decision.
Text in `SourceRecord` names the review that is required; its status and reviewer
labels do not create that review. Approval requires resolver material with
nonempty content whose SHA-256 matches its declared digest. The material must
match the authenticated tenant and reviewer, exact record ID, revision, raw hash,
provider, product ID/version, source URL, location, check variable/name/version,
or right action and intended use. Rights conditions must be affirmed by that
material. A caller cannot supply `conditions_met` to create a right approval.
Each signed approval stores its review metadata and content digest; the
review content remains in the resolver's access controlled evidence store.

The server must supply a persistent secret signing key of at least 32 bytes,
separate from the database, and a tenant scoped content address reader. Neither
key nor raw bytes are stored in `g0_entries`. The reader returns exact raw bytes
for `(tenant_id, raw_sha256)` from a permission limited store outside the
repository. Registration checks the raw hash, and evaluation checks it again.
Unavailability or a mismatch leads to `hold`.

## Stored rows and versions

`install_g0_schema` creates one append only `g0_entries` table in an explicitly
selected PostgreSQL schema. Every row has a tenant, kind, immutable entry ID,
canonical JSON payload, SHA-256, HMAC-SHA-256 over its indexed identity and
digest, and server recording time. A trigger rejects updates and deletes.
Reads verify the digest, signature, model schema, and indexed identity. A
tampered row cannot supply an approval. Reads also check that a review's signed
proof binding agrees with the approved evidence and indexed tenant/purpose.
The normal database role must not be
allowed to disable triggers or read the signing key; PostgreSQL 18 role grants
remain a separate G4 check.

The kinds are record, policy, source review, check review, right review,
revocation, and decision. Records preserve the `SourceRecord` content ID and
raw SHA-256. Policies preserve their model digest and version. Policy versions
within one tenant, source scope, action, and use are append only and receive a
monotone generation number. The newest generation recorded by `decision_at`
is evaluated, including when it holds; the evaluator never falls back to an
older passing policy. A correction creates a new record, proof, or policy
version. Revocations are separate signed rows. Prior decisions remain
unchanged.

## Decision behavior

The public evaluation input is tenant, record ID, intended action, intended
use, and optional UTC `decision_at`. The store resolves all other material.
Each decision is serialized with its own ID, tenant, purpose, time, G0 result,
status, reason codes, and the original approved policy digest when one was
resolved. A revoked policy is projected into the gate with its revocation
time; the original approval digest remains separate in the decision. The
decision also retains the requested UTC time and server evaluation time. The
authority holds future or malformed decision
times. Historical evaluation sees only rows recorded by that time and source
or policy evidence available by that time. Missing, stale, expired, revoked,
cross tenant, cross purpose, QC, rights, raw integrity, and tamper cases
produce `hold`. A stored `pass` is scoped to the exact tenant, record, action,
use, and time; it is not a general provider approval or a later G1–G4 gate.

Concurrent writes and evaluations for one tenant take a PostgreSQL transaction
advisory lock. A decision therefore observes a complete committed approval
set and is written in the same transaction as its evaluation. Decisions and
approval rows cannot be rewritten.

## Verification boundary

The tests use a plainly self authored fake resolver, metadata, and bytes solely
to check software contracts. Its passes are not real G0 approvals. They do not
establish actual external source rights, QC, reviewer
authority in a deployed identity provider, or PostgreSQL 18 application role
separation. The focused PostgreSQL tests require `OSSF_TEST_PG_DSN` and create
and drop their own schema. An operational deployment must provision separate
database roles, an access controlled raw store, persistent signing key,
reviewer identity mapping, an independent source specific review resolver with
retained evidence content, and provider rights before G0 passes can
be adopted for real data.
