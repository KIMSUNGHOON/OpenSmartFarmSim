# Authored farm input review v1

Status: internal review-admission contract after immutable
[registration](farm-authoring-storage-v1.md) and complete
[numerical trajectory](farm-thermal-candidate-v1.md). The review remains
`collection_review`; it is not an authored snapshot release or G1 Run.

The server accepts an exact tenant-owned farm id, revision, registration SHA-256
and caller idempotency key. It rereads the registration under current read and
review-create scopes, including owned research, original source bytes/rights,
signed DecisionContext, Market hold and economic pins. It recalculates the
complete 120-step authored candidate. The review input records the exact
registration/farm/numeric/source/binding/code and two trace hashes, original
snapshot, decision context and temporal scope. No coordinate, user farm record,
money or raw restricted third-party byte enters the CLI input.

Before commit, the server repeats all current checks and requires identical
canonical input bytes. The review job is immutable and uses the existing
`collection_review` stage with a distinct `farm-authored-review-input-v1`
version. Equal idempotency requests reuse the original job; changed bytes
conflict. The server's trusted CLI contract accepts only the current exact
input and tenant. Its deterministic authority permits a software-scope
`proceed` decision with no agricultural or economic claims; a CLI hold remains
a hold. On `proceed` the artifact binds the exact review input, registration,
candidate and both trace hashes. Actual CLI execution/capture verification
remains a separate worker and independent release requirement.

Rechecking an already stored review input uses current farm read scopes.
Creating or retrying a review job still requires `collection_review_create`.
This permits read-only verification during a later authored Run lookup without
granting the reader review-submission authority.

The review output cannot assert parameter accuracy, source ownership, G0/G2,
crop growth, energy purchase, future margin or crop ranking. User rights remain
asserted, not independently proven. The fixed original publisher and accepted
Run table remain untouched. A future authored release must verify an actual
completed CLI review, separate reviewer authority and complete runtime
code/environment custody before any published Run.

The optional `OwnedCliContractRouter` route selects this contract by exact
`collection_review` stage and `farm-authored-review-input-v1`. Installation
requires the authored service, owned research, source collection review and
farm Assessment to share the same JobStore, thermal/context store, registered
source authority, candidate store and farm selection object. Replacing any
installed service or its authority pointers holds the router. The existing
review and assessment routes remain available when the authored route is not
installed. Operator runtime assembly, actual CLI execution and independent
process/release proof remain separate acceptance steps.
