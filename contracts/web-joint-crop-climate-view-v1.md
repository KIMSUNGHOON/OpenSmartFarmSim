# Joint crop/climate saved numerical view v1

Consumes the [typed reader](web-joint-crop-climate-replay-v1.md) through an explicit
joint format in the existing crop replay screen. Existing formats coexist.
The five-field lookup identifies a stored result and farm revision. Summary and
one page are read sequentially. Retain at most64 samples or8 events; original
total and selected range remain distinct. This view does not poll a running job.

Keep one selected original sample's result/farm/reference/UTC/index across table,
chart and WebGL. The adapter passes the original LAI, C/N arrays and calculated
canopy/air temperatures to the shared geometry interface. Do not manufacture an
old121-state response. Climate/plant/derived values,22 integrated transfers,
event totals and residual budgets keep original numbers and units.

LAI uses the existing one-square-metre floor normalization. Fifty C/N slots use
the existing explicitly labelled common logarithmic visual scale over the current
page. Temperature markers use that page's minimum/maximum in degrees Celsius on
a common linear vertical axis. Equal temperatures use the midpoint. Marker
geometry does not depict actual facility position, crop height, fruit size or
harvest. Charts join saved points without generating intermediate states.

Navigation/playback selects saved rows only and stops at the current page end.
Reduced motion disables automatic playback; hidden pages pause it. No-output
pages create no start/end/failed-boundary frame. A held result retains its hold
notice and distinguishes last-confirmed diagnostics from saved selectable outputs.
Management pages show original removal/before/after records and do not invent a
matching sample. WebGL failure leaves table/chart/navigation usable.

Selection/account/format changes, cancellation and request failures remove prior
values. Aborted reads settle before the next read. Epoch checks suppress late
responses. Page transitions reuse the identical checked summary/reference; a
fresh rights query reloads summary. Current server authorization applies to each
read, while already displayed data are not continuously reauthorized.

Use existing approved research design assets/styles, complete12ui alignment, and
verify exact original values and actual rendered geometry in isolated Chromium.
Actual DB/TLS integration, owned-process limits and original-input/user-preview
preservation are separate acceptance evidence from mocked browser responses.
No measured farm/cultivar accuracy, production, economic forecast, G0–G4 approval
or realtime U3 claim follows from synthetic screen checks.
