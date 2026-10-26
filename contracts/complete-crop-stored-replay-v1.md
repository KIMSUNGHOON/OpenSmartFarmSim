# Stored complete crop viewer v1

Status: accepted for synthetic research replay on 2026-10-27 KST. Final visual quality, farm runtime integration and biological validation remain open.

The viewer consumes the existing [strict SDK](complete-crop-strict-sdk-v1.md). It does not calculate growth, extend a trajectory, create intermediate crop states or approve a claim gate.

## Mapping

- `CompleteCropFrame.internodes`: one straight vertical segment per stored ID, in stored sequence; its length in metres is unchanged. The sum is tracked axis length, not measured plant height.
- `CompleteCropFrame.leaves`: one authored compound-leaf surface per stored ID. Its one-sided triangle area equals the stored area in square metres within relative `5e-12`. Its base attaches to the end of the declared parent internode. Multiple declared QA leaves can share a parent.
- Leaf azimuth is a stable authored function of ID. Blade shape, seven leaflet meshes, stem thickness, petiole form, materials, bed, lighting and camera are visual assets. They are not measured cultivar parameters. There is no fruit geometry in the computed scene.
- Exact model origin, fractional elapsed seconds, phase, checkpoint identity including `null`, leaf/parent IDs and source artifact are retained. A validated dense candidate is labelled as having no checkpoint.
- Triangle normalization changes geometry scale only; it does not infer mass, carbon, specific leaf area or crop coefficients. The table uses stored carbon and thermal age directly.

## Interaction and failure

The range control, buttons and autoplay select original frames. Autoplay advances one stored frame per 900 ms and pauses on document hiding. It is not elapsed-time playback. Graph x coordinates use explicitly labelled stored order; the y axes start at zero. No middle growth is interpolated.

The URL contains scenario, trusted artifact and frame. Invalid, ambiguous or mismatched cursors start at frame zero. Menu return and reload retain the same valid cursor. A selected source is persisted before validation finishes, including when source validation fails. A selected source is persisted before validation finishes, including when source validation fails. A selected source is persisted before validation finishes, including when source validation fails. Fetch cleanup aborts abandoned loads; a former scenario cannot replace the currently selected source.

The scene renders on demand for selection, resize or camera interaction. Initial framing and explicit camera reset fit the current mesh; later automatic framing only increases distance when needed. User camera interaction stops automatic fitting. Idle frames do not schedule a render loop. Owned geometries, instances, textures, controls and renderer are disposed; shared borrowed plant materials are retained.

Source failure removes the scene, tables and graphs. A retry revalidates the original files. WebGL failure leaves verified original table values available. The immutable public research viewer does not supply a live farm rights review; that integration remains a separate product requirement.

## Accepted evidence

[Research record](../research/complete-crop-stored-replay-20261027.md) records the actual CLI context, code/input hashes, 110 focused unit checks, current full web type check, separate viewer build, 16 native Chrome browser tests and live preview smoke.

All 12 accepted datasets / 834 stored frames were rendered and compared with the raw files. Browser assertions cover leaf triangle area, internode length and identity, parent identity, exact time/phase, carbon/age table values and graph points. Unit checks independently measure world triangles by cross products and segment bounds at endpoints and birth boundaries. Desktop/mobile captures were inspected.

The accepted UI range is 3–7 leaves and 3–4 internodes in these datasets. Schema caps do not prove maximum-size rendering or repair the separate held 512-leaf serialized request. A cold shader compiler warning remains; headless browser screenshots do not complete physical visible-window R2 acceptance.

The QA initial leaf areas and internode lengths are biologically inconsistent. Their proportions are preserved and disclosed. This contract does not establish cultivar morphology, a crop cycle, yield, purchased resources, margin or autonomous crop ranking. See [product scope and gates](../docs/PROJECT_SPEC.md).
