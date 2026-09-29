# Internal location web shell v1

Status: software candidate covering initial location research admission and
public job/hold reads. Full `web-shell` acceptance in
[tasks](../tasks/todo.md) also requires economic assumptions, market cards,
and the remaining API orchestration; it is still pending.

## Input and transport

The Korean React client receives one coordinate and separate UTC date/time
fields. It creates an increasing period of exactly two hours and the existing
`historical-thermal-replay` goal. Example coordinates and virtual application
time are explicitly synthetic test inputs; they establish no observation,
provider coverage, farm precision, G0 adoption or future prediction.

The fixed relative routes are POST `/v1/locations`, GET `/v1/jobs/{uuid}` and
GET `/v1/jobs/{uuid}/hold-report`. Authentication is an operator-issued Bearer
token retained only in the API closure; the password input is cleared after
connection. No token is persisted or embedded in the build. Permission is
checked by the existing server on every request. This manual internal setup
does not implement production login/session lifecycle.

One intent UUID and immutable body are retained while an admission response
is unresolved. Retry sends that exact body/key. Input changes/new input are
disabled for an unknown outcome. Retry is manual, with a 30-second request
timeout; no model/provider calls run in the browser. Page reload/disconnection
clears in-memory tracking, so this shell does not yet recover existing jobs
across browser sessions. The server's durable records remain authoritative.

Successful status must be exactly 202 for admission or 200 for reads. Closed
DTOs validate identifiers, enumerations, bounds, point/job identity and hold
categories. Responses are limited to 65,536 bytes while streaming; malformed
UTF-8/JSON or unsupported data is rejected. Raw error bodies, private source
IDs and generated prose are never rendered. A fixed Korean error category
explains refusal/unresolved responses.

Job timestamps accept valid explicit RFC3339 offsets and up to six fractional
digits. Invalid calendar dates are rejected; the original server string is
preserved, and the readable clock is labelled KST. UTC labels belong to the
submitted virtual period and are not appended to offset-bearing server times.

## Display

Only the actual returned job stage/state, attempts and recorded times are
shown. Manual refresh retrieves the current status, then its stored bounded
hold report. Job/report stages must agree. Missing categories are translated
from a fixed allowlist; unknown raw evidence cannot become product copy.
There is no invented CLI completion, estimated completion time, progress
percentage, crop output, purchased energy, forecast margin or ranking.

The two real screens have named keyboard controls, visible focus, a skip link,
status/alert semantics and responsive single-column layouts. No WebGL is used
in this slice. The approved p1/p2 design exports supply shell/card hierarchy;
the exclusions in [UI_DESIGN](../docs/UI_DESIGN.md) govern their content.
Noto Sans KR is self-hosted with its original OFL notice.

## Local assembly and verification

[Web instructions](../web/README.md) define loopback HTTPS proxy configuration.
The browser-facing certificate/key are required when the API proxy is enabled.
The upstream must be a credential-free loopback HTTPS origin, and TLS
verification remains enabled. Optional CA bytes affect only the server-side
agent. Vite is a development server; static production serving, trusted public
TLS, production authentication, CSP, full accessibility/performance and G4
remain separate work. Preview does not assemble the API proxy.

[Evidence](../research/web-location-shell-implementation.md) distinguishes
mocked browser tests from the real TLS/SCRAM browser integration. The latter
uses a self-authored fake CLI and synthetic credentials and proves software
connections only. It does not satisfy actual-model or full G1 acceptance.
