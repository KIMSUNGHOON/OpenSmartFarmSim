# Joint crop/climate typed web reader v1

This consumes [protected HTTP](api-crop-climate-joint-route-v1.md) and its
[explicit runtime](crop-climate-joint-runtime-v1.md). It is a reader for owned
synthetic research results, preceding same-UTC 3D and user execution/U3.

`createApi()` adds `jointCropClimateSummary`, `jointCropClimatePage` and
`jointCropClimatePages`. Lookup contains only result ID and the four HTTP farm
references. The new result prefix/schema/model and 108-state layout are distinct
from the existing 121-state cycle response. Returned batch/zone and full reference
identity must remain identical across summary/pages.

The decoder validates closed objects, known units, finite quantities, 50 C/N
cohorts, inventory domains, 22 transfers, management removals and residual budgets.
It keeps original quantities and strings; it neither runs crop/heat equations nor
estimates missing values. Identity/profiles/code maps have closed keys and digest
shapes. Manifest/management/reference bindings are compared. HMAC, native code
acceptance, context hash proof and current rights remain the server's responsibility.
Browser shape checks cannot approve data or G0–G4.

UTC strings retain microseconds. Integer-microsecond checks bind every point to
the declared start/step/index grid, including hold's failed boundary. Summary
contains the actual last confirmed state. Pages are bounded to 64 samples or
8 events and the existing 2MiB/30-second transport. Count/cursor/order/hold
boundaries and requested offset/limit are checked. Empty terminal pages remain
valid; full iteration reports completion only after exact total and ordering.

Request identity, query and supplied summary are checked before and after awaits.
One reader request is in flight at a time. Abort, changed selection/summary/query,
foreign pages, late replies, server access denial and incomplete iteration never
produce a completed result. Existing authenticated no-store transport is reused.
No new storage, framework, worker or source authority is introduced.

The recorded fixture contains only directly authored synthetic public responses
captured from verified HTTPS/SCRAM. It retains original wire response slices and
is licensed as project-authored test material, not third-party or measured farm
data. Fixture hashes, original responses and numerical-call-zero evidence belong
in the implementation record. Focused malformed-response/transport/iteration
checks and TypeScript verification precede UI use. Existing SDK regressions,
owned-process cleanup, original inputs and the current user preview are preserved.
This contract does not accept a new screen, live progress, full joint crop cycle,
harvest/energy purchases, future margin or recommendations.
