# Owned collection Compose runtime v1

Status: [actual hosted collector software acceptance passed](../research/collection-compose-runtime-implementation.md).
Overall source-service workflow/authority acceptance remains pending.

The additive `compose.collection.yaml` is used after `compose.yaml` and
`compose.application.yaml`, with profile `runtime`. It replaces the C0 collector
placeholder with the existing backend-app target and the exact
`app.collection_consume --factory <operator reference>` entrypoint. It supplies
no default source authority, research executable or approval/release evidence.

Required additional inputs are `OSSF_COLLECTION_PRIVATE_DIR` and
`OSSF_COLLECTION_FACTORY`. The former is an existing operator-owned protected
directory, mounted readonly at `/run/operator/collection`; its `plugins` directory
contains the trusted factory. It must supply current principal, scoped SCRAM
credentials and the exact existing collection service/registry/store. A HTTP/job
field cannot select it. The artifact mount is the existing explicit writer root;
missing host paths fail rather than being created.

Collector uses UID11001:GID11010, the existing API/simulation authority writer
class. These processes have separate private mounts but shared writer authority;
this is not independent credential or release custody. The existing foreground
consumer owns current checks, bounded discovery, safe metadata, stop and lease
recovery. Root/operator mounts are readonly, capabilities dropped, temporary
space nonexecutable and bounded, PID64, memory256MiB, CPU0.5, bounded local logs,
explicit restart and30-second graceful stop. No host port is published.

## Hosted software proof

The existing real application harness gains an explicit `--collection` mode
using this override. It keeps normal TLS/Bearer and SCRAM, creates a private
synthetic completed research parent using the existing fake executable, then
POSTs ingestion through the actual API. The real collector discovers it without
a UUID argument, checks parent/source rights and publishes once. A trusted
operator-only container read validates the original record and reports bounded
software-hold metadata. The public HTTP interface continues to expose job status,
not raw collection bytes.

Required evidence: actual collector image/process/UID/resources/private mounts,
automatic completion and safe current record; API/collector restart preserves
the same job/record and one attempt; current source proof revocation holds a new
request and grant drift stops/refuses current access; all owned processes,
volumes/passwords/tags/private files are removed on success or failure.
The API/economic runtime proof must still pass separately. This acceptance
closes only the deterministic owned collector's service assembly. Authority/
supervisor/dispatcher Compose, general regional source research, actual product
CLI, independent source/release/custody, G0–G4 and forecasts/rankings remain held.
