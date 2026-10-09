# Local synthetic 3D demo verification

Date: 2026-09-30. This is a local software demonstration, not a farm or
model validation. `npm run demo:3d` starts Vite on `127.0.0.1:5173` with a
dev-only middleware that returns the existing authored replay HTTP test
fixture. The separate `/demo/` page uses the normal `Replay` component and
prefills the synthetic job ID and replay kind. The demo page automatically
fetches the fixture and loads the actual Three.js scene, ECharts graph and
HTML table; the regular replay page still requires an explicit lookup.
The middleware rejects non-GET requests and any Bearer token other than the
local synthetic demo token. It refuses a configured operator API/TLS runtime.

Observed with Chromium via Playwright after opening `/demo/`: `3D 준비됨`
appeared without a click, the canvas reported 45 draw calls,
the selected stored timestamp moved from `2026-10-15T08:01:00Z` to
`2026-10-15T10:00:00Z` when the slider moved to 119, and no page errors
occurred. [Scene and summary capture](artifacts/local-synthetic-3d-demo.png)
shows point 60. The fixed/authored replay regression browser tests both passed.
`npm run typecheck` and `npm run build` passed. The built `dist/` contained
neither `/demo/` nor the synthetic demo token or fixture banner.

The middleware values are response doubles from `web/e2e/`; no PostgreSQL,
product Codex CLI, source collection, independent reviewer, crop growth,
harvest, purchased energy, future margin or ranking ran. The separately
stored-Run-to-HTTPS browser CI check remains pending and is not established
by this demo.
