# Owned source steps in the internal web shell v1

Status: internal software connection candidate. This surface joins the
[location request](web-location-shell-v1.md) to the existing
[owned ingestion and review HTTP](api-owned-collection-v1.md) contracts.
It does not grant source rights, adopt a thermal snapshot, publish a Run or
accept G0/G1.

After the registered research job is `succeeded`, the work page may submit
`POST /v1/ingestions` with its exact job ID and one stable client intent key.
It reads the returned `collection` JobStatus. Once that job is `succeeded`,
it may submit `POST /v1/collection-reviews` with the collection job ID and a
different stable intent key. It reads the returned `collection_review`
JobStatus and, if held, the bounded hold report. The server rechecks the
parent, source, rights, signed context and tenant at each admission.

The browser stores stage keys and job statuses only in page memory. An
uncertain response does not create a new key or imply completion; the same
button resubmits the exact parent/key. Navigating among screens preserves the
in-memory stage state. Changing the authenticated API connection or research
job discards it. Server status is fetched explicitly; the client does not
advance a stage from elapsed time or a synthetic fixture label.

The UI reports separate research, collection and review statuses and shows
the verified review hold evidence names. It never shows raw source bytes,
CLI prompts, credentials or private reason details. A successful review is
still a reviewed **candidate**. The signed independent release, current
farm/economic/market references, simulation admission and exact Run read are
separate gates. Browser state loss after a full refresh remains a recovery
gap for these source jobs; this contract makes no durable-history claim.
