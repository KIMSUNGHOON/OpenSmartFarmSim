# Supply morphology stored geometry v1

Render the HTTP SDK's original stored frame: IDs, parent IDs, lengths in m, leaf
areas in m2, at/phase and metadata remain unchanged. Use the existing authored
tomato leaflet geometry and materials; shape/azimuth/width/lighting are authored
appearance, not inferred cultivar traits. No growth equations or interpolation.

The stored parent graph is a forest. A segment starts at its declared parent's
tip; a null parent is an independent display root, never an implicit prior stem.
Reject missing parents, duplicate IDs, cycles, wrong units, nonfinite/negative
dimensions and more than512nodes/leaves. Never use epsilon to stretch a zero.
Keep a zero-length node's ID/placement while its collapsed segment is invisible.

Bound compound leaves attach to the declared tip. Unbound leaves retain null
parents in a separate authored display group. Do not fabricate attachment IDs.
Scale the actual one-sided triangle surface of the authored seven-leaflet asset
to the stored total leaf area. Zero area remains a collapsed, invisible leaf.
Display translations and straight-axis/leaf poses are explicitly authored.

Expose isolated records of original IDs/parents, display placement and measured
leaf surface area, plus actual stem meshes. Copy input metadata and never mutate
the frame. Disposal is idempotent, releases owned geometry/instance buffers and
leaves borrowed materials intact. Record/measurement methods reject after disposal.

Acceptance: all38original frames/358leaves/356nodes, independent triangle cross
products and transformed stem endpoints,4zero-length rows/114unbound leaf rows,
forest/selection immutability and adversarial shapes, whole types/isolated build/
independent execution, source/CAS/rights/UI/WSL preservation. Browser appearance,
screen integration and R2, product farm/cultivar/production claims remain pending.
Mesh QC permits5e-12relative triangle-area error and1e-14m absolute transformed
endpoint/length error. This renderer rounding budget never changes stored data.
