# Supply morphology HTTP replay v1

Load only `./supply-morphology-replay/own-public-v1/` against the independently
installed anchor, using accepted original graph and stored-quantity validators.
Reuse the existing bounded HTTP reader: no credentials/cache/redirects,2MiB per
stream and64MiB total,512frames and32768coordinates. No new crop calculation.

`loadSupplyMorphologyReplay(signal)` returns a research replay with `summary()`
and `frame(index)` defensive copies. Keep original time/phase/IDs, quantity units,
birth/geometry/ledger evidence, source rights, terminal hold and G0–G4/R2 unchanged.
Retain no caller-owned frame/summary reference; a changed selection copy must not
change any later selection or another load. Reject invalid indices.

`SupplyMorphologyRequest.load()` aborts and invalidates the previous generation;
`cancel()` invalidates an outstanding result. An older response cannot replace
the latest result even when a test transport ignores abort. No shared data cache.

Acceptance: focused HTTP/stream/failure/abort/latest/copy tests; an independent
real HTTP server's original101files/38frames/6208coordinates and request policy;
whole types/isolated build; original sources/rights/CAS/UI/WSL and cleanup.
Full stored HTTP SDK acceptance is limited to this own-public research family.
Same-state realistic3D, live farm rights/worker integration, a whole cultivar
season, production/resources/economics/macros/autonomous comparisons and all
claim gates remain separate tasks.
