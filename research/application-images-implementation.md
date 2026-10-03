# Application images — 2026-10-03

Status: isolated hosted image software acceptance passed. Actual API/worker
Compose and product CLI/independent G1/G4 are separate boundaries.

The [image contract](../contracts/application-images-v1.md) adds explicit
`backend-app`/`web-app` stages without replacing C0 dependency targets.
Source, schemas, exact synthetic fixtures and original-prefix locked venv are
copied explicitly; static web uses pinned official NGINX. Credentials/factories
remain external. No arithmetic or source/model gate changed.
Review used existing Codex CLI session `01a0e064-b01b-7a22-8ef8-dd4afe0eb7dc`,
`gpt-6.1-sol` / `xhigh` (turn metadata `2026-10-03T00:51:10.130Z`). No recursive
CLI was launched. Source pin/rights are in the contract and stack.

## Failure and correction

[Run 37088871716](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/37088871716)
at `aa472a4a15314f8e1effbed6455c711f8a2b9ad6` failed actual exported Docker
context exclusion before app builds. Negated directory rules reopened children
after initial exclusion. Each directory now excludes children again before
allowing specific patterns/names. The assertion is preserved; diagnostics name
only twelve known synthetic probe paths. Failure cleanup passed; no actual
private data or secret was used. Failed job log SHA-256:
`43ce3d50d437886c9b2ca09c8e4523d6809cc2b85c2b1e7604353e2704046ccd`.

## Hosted acceptance

[Run 37088984265](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/37088984265)
at `02ac6ac8a1739762c456fc6897cb226e45ef0234` passed:

- Actual context export excludes twelve poison files and admits current source
  and the exact existing required PNG asset.
- Both app targets build on Ubuntu24.04. Backend UID11001/GID11010, web
  UID/GID11002; readonly imports/digests and absent pytest/uv pass. Missing private
  operator config exits2 with the existing fixed startup error.
- Final web has no Node/npm/source tests or vendor fallback HTML. Readonly run
  and missing-TLS startup rejection pass.
- Normal CA/IP HTTPS serves current index/assets, asset404 and identical license
  notices. Cache policy, Bearer forwarding and removed forwarded headers pass.
- A reachable same-CA wrong-DNS-name HTTPS fixture yields502; the matching name
  yields200. Verification remains enabled. This fixture is not the product API.
- Unique containers, image tags and temporary files are removed. Shared build
  cache remains; no unrelated host resource changed.

Hosted local image IDs: backend
`sha256:4f4ab2773f2a5e0fe2c7250bf8574ebecc52a3daf75376f014f3eeb603db2470`,
web `sha256:4f17acfb684dd0f945407405f6479ec7025bf357114d76c7e35a566cf368051b`.
These are runner IDs, not published registry manifests/G4 release pins.
Calculation digest `6ed29db3653a7c8e82b373941fde28f3d25d759fc22444428774495e9e5f1f9a`
and lock digest `e73e9ec049e80bfa4ad96afc33bfa25f5fddab60d60771284d6292178241beb3`
are unchanged. Actual job log:
`/tmp/ossf-ci-images-02ac6ac-111105059234-20261003.log`, SHA-256
`425729302e23a51ea9939fe853078909bafde2321b4166bc4c8f552c172c20d8`.

Local web TypeScript/Vite build passed with demo/API/TLS switches unset
(`/tmp/ossf-application-web-build-20261003.log`). Existing ReplayChart/ZoneScene
chunks exceed500kB; warning remains visible. WSL has no Docker Engine; hosted
evidence supplies actual image execution. Python syntax/whitespace checks passed.
Review corrected venv prefix, asset allowlist, TLS fixture readiness and cleanup
of partially built tags. No UI design or money/quantity code changed.

| File | SHA-256 |
| --- | --- |
| `backend/Dockerfile` | `517f1914e2840d154309795db435055a294daad65484e0d45e726aa1fcad5915` |
| `web/Dockerfile` | `b8f94cd12c4400ef0f0938138b96b5b0faf4c61c0df18c02b7e7052944c2d785` |
| `.dockerignore` | `7743c47994f68e04c46270474782ddb637b2ef55fc2cbffc324dea8f8888f215` |
| `web/nginx.conf` | `c137560a877cf0230d89b9a775bf4e46e9ad2b2de73fc9bd9d724f782bc5ea84` |
| `scripts/check-application-images.py` | `a82c232c820af008b4c07d1ecfaa2d3a1aeab3b57a5c9085fd55ff162a392549` |

This accepts image plumbing with synthetic certificates/HTTPS fixture. Actual
authenticated API/worker orchestration, CLI/independent release, source rights,
crop outputs, future margins, ranking and G4 remain separate acceptance.
