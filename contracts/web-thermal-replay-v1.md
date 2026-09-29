# First internal thermal replay viewer v1

Status: next implementation candidate, prioritized after farm economic execution
by the user's request on 2026-09-29. This document is a scope, not acceptance
evidence for web-replay, whole G1 or a production service.

## Input and display

The existing authenticated web shell gains a read-only replay screen. It reads
an actual completed thermal job's Run through GET /v1/jobs/{job_id}/run, then
the same Run's existing summary, series and manifest endpoints. No calculation,
source approval or generated data is performed in the browser. The client
rejects mismatched run identities, synthetic/claim scope, time ordering, units,
nonfinite values or incomplete responses and clears stale results on connection
or selection changes. Authorization and source/display rights remain server
decisions on every request; the token stays only in page memory.

A single selected stored point supplies the timestamp and all values to a
Three.js conceptual single-zone greenhouse, graph, accessible HTML table and
text. The existing series exposes indoor temperature, humidity ratio, relative
humidity, model heat demand/delivery and delivered heat for that time step.
Use those exact fields and units. Geometry is explanatory and has no surveyed
dimensions; it is not a farm plan. Source synthetic status and ex-post provenance
are visible, and the manifest explains rights and outstanding evidence.

Time selection uses stored points without creating interpolated simulation
states. Playback, if enabled, advances between those points and states its
display speed. Color and any heat indicator have a textual legend. Unsupported
control/ventilation fields remain unavailable rather than inferred from heat.
The screen does not add crop growth or purchased-energy/cost animations.

## Focused verification

- Prove one run_id + timestamp drives scene, graph, table and text after time
  selection, and stale or mismatched responses cannot repaint a prior result.
- Verify keyboard time controls, pause/reduced motion, narrow screens and 200%
  text. WebGL failure or context loss preserves all values and controls in HTML.
- Run locked TypeScript/unit/build/browser checks and an actual HTTPS/Bearer/
  SCRAM completed-Run browser smoke with clearly synthetic test authorities.
- Follow the existing UI design and required 12ui alignment workflow; record
  render/source comparison, dependency versions and relevant licenses.

Paired farm assessment, full input authoring, actual product CLI, independent
custody/release, full web-replay/G1 and G0/G2/G3/G4 acceptance remain subsequent
work. A visible 3D scene establishes the renderer's software behavior only.
