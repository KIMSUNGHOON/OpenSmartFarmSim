# Internal web shell

## 지금 3D를 직접 보기

`web/`에서 Node `22.22.3`, npm `11.16.0`으로 다음을 실행합니다.

```bash
npm ci --strict-peer-deps
npm run demo:3d
```

브라우저에서 `http://127.0.0.1:5173/demo/`를 열면 합성 3D 장면이
자동으로 나타납니다. 실제 저장 내역을 만들 필요가 없습니다. 120개 저장 시각,
그래프와 표를 조작할 수 있습니다.
이 명령은 loopback 전용 Vite 서버와 직접 작성한 합성 HTTP 응답만 실행합니다.
PostgreSQL, 운영 토큰, 기상 수집, 제품 Codex CLI, 현장 자료는 사용하지 않습니다.
화면 값은 브라우저 소프트웨어 데모이며 작물 성장·수확·사업성을 예측하지
않습니다. `npm run build`의 일반 서비스 산출물에는 이 데모 페이지와 응답이
포함되지 않습니다. [실제 브라우저 캡처](../research/artifacts/local-synthetic-3d-demo.png)와
[검증 기록](../research/local-synthetic-3d-demo-implementation.md)이 있습니다.
종료하려면 터미널에서 Ctrl-C를 누르세요.

The current screen submits registered synthetic location research and reads
its real server job/hold status. The third screen lists exact stored economic
assumptions, registers a numeric revision and admits/reads a selected conditional
ledger calculation, including a manually requested monthly cash table. A
break-even section selects existing sale/collection and saved trial revisions,
admits a finite plan and reads its completed result. The fourth screen looks up
an already registered authored farm version, submits review and thermal work,
reads server job/hold status, and opens a completed stored Run. It does not
provide a farm authoring form or issue an independent release. The last verified
farm ID, revision and registration hash are kept in this browser tab only; after
reconnection the server must authorize and confirm the exact version before it
appears again. Tokens and review/simulation job IDs are not stored. The fifth screen replays
either a fixed or a farm-authored synthetic thermal Run in Three.js, a chart, an HTML table and six
text values with one selected stored timestamp. Full farm input,
baseline/event/settlement authoring, automatic trial assumptions, durable
job reload recovery, a server list of owned farm versions, map, full replay
acceptance and production hosting are pending. See the
[location contract](../contracts/web-location-shell-v1.md) and
[economic contract](../contracts/web-economic-workspace-v1.md) and
[break-even contract](../contracts/web-break-even-workspace-v1.md) and
[thermal replay contract](../contracts/web-thermal-replay-v1.md) and
[authored replay contract](../contracts/web-authored-thermal-replay-v1.md).

## Software checks

Use Node `22.22.3` and npm `11.16.0`:

```bash
npm ci --strict-peer-deps
npm run typecheck
npm run test
npm run build
npx --no-install playwright install chromium
npm run test:browser
```

Run from `web/`. The browser suite starts its own loopback server on 5173 and
refuses to reuse an existing service. Browser responses in that suite are
explicit test doubles, not completed product CLI work. CI runs these checks
with pinned actions/tools and `npm audit --audit-level=high`. Set
`OSSF_TEST_WEB_PORT` to another available loopback port when 5173 serves the
local 3D demo. The authored workflow's browser verification is recorded in
[its implementation evidence](../research/authored-farm-web-workflow-implementation.md).

## Connect an operator-assembled API

Supply absolute paths to protected TLS files outside the web source/build
directory. The API must already be assembled using the
[runtime contract](../contracts/api-runtime-assembly-v1.md) and its authenticated
server-owned registry. The browser must trust the browser-facing certificate.
For an internal deployment using a private CA, point the upstream CA setting
to its public certificate; TLS verification stays enabled.

```bash
OSSF_WEB_API_ORIGIN='https://127.0.0.1:8443' \
OSSF_WEB_API_CA='/protected/api-ca.pem' \
OSSF_WEB_TLS_CERT='/protected/web-cert.pem' \
OSSF_WEB_TLS_KEY='/protected/web-key.pem' \
npm run dev
```

Open `https://127.0.0.1:5173`, expand **내부 시험 연결**, and enter the
operator-issued token in the page. Never place the token in a URL, command,
environment file, repository or screenshot. The token remains in page memory.
The server must register the exact tenant, coordinate, UTC period and goal;
the example button does not register or approve a source. `npm run preview`
serves only the static build and has no API proxy.

## Real local integration

After locked backend installation and Chromium installation, set
`OSSF_TEST_PG_DSN` through a protected local test configuration and run from
`backend/`:

```bash
uv run --locked --group dev pytest -q -s tests/web_shell_smoke.py tests/web_economic_smoke.py tests/web_break_even_smoke.py
```

The completed thermal replay has a separate explicit smoke:

```bash
uv run --locked --group dev pytest -q -s tests/web_thermal_replay_smoke.py
```

The authored Run has a separate explicit stored-Run-to-browser smoke:

```bash
uv run --locked --group dev pytest -q -s tests/web_authored_thermal_replay_smoke.py
```

It needs the same protected `OSSF_TEST_PG_DSN` and locked Chromium setup. The
backend CI runs this authored smoke after its database tests. Its review,
release and CLI authorities are synthetic software fixtures, not G1 proof.

The [composite authored path](../research/authored-full-software-path-implementation.md)
also registers an owned farm, runs its synthetic review/release and actual
publication worker, then checks the registered version, new review and thermal
jobs admitted by Chromium, their worker completions, and the resulting Run over HTTPS:

```bash
uv run --locked --group dev pytest -q -s --tb=short tests/test_authored_full_software_path.py
```

It uses the same protected PostgreSQL test setup. Registration happens in the
backend test harness. The browser admits a fresh review job; the harness executes
a fake CLI and stores synthetic observer/reviewer signatures. The browser then
admits a fresh simulation job, the harness executes the deterministic worker,
and the browser reads its stored Run.
The 180-second timeout on both browser admissions is provisional pending latency work.
Its CLI and reviewer are synthetic test authorities.

It completes an owned farm thermal job, projects the verified immutable Run,
and compares the first/last stored points and six numeric fields with the
actual HTTPS browser scene, chart and HTML table. It captures desktop/tablet/
phone screens in pytest's temporary directory. Its CLI and release authorities
are synthetic software fixtures. It does not establish product CLI execution,
independent G1 or production readiness.

This explicit smoke creates disposable SCRAM roles, an actual API, Vite HTTPS
proxy and an isolated Chromium context. It checks queued admission, persisted
fake-CLI hold, repeated intent with one stored job and rejection of an
untrusted upstream certificate. Only the isolated synthetic browser fixture
ignores its ephemeral browser-facing certificate error; the upstream and
Python HTTPS checks verify certificates. Services and temporary database password files
are cleaned up. The economic smoke also checks an exact decimal revision, actual scenario and
calculation admission, worker completion, result and monthly cash display, and identical retry
with one stored calculation job. Its data/keys are self-authored synthetic
fixtures, and it invokes no CLI. These smokes are not yet part of hosted web CI
or full G1. [Evidence](../research/web-economic-workspace-implementation.md)
records the scope and remaining holds.

The self-hosted font is pinned as `@fontsource-variable/noto-sans-kr@5.3.0`.
Its original [OFL notice](public/licenses/noto-sans-kr-OFL.txt) is copied to
the static build's `/licenses/noto-sans-kr-OFL.txt`.

## Open a completed thermal replay

With the assembled API connected, choose **05 3D 열 재생**, select fixed or
authored thermal replay, enter an owned completed thermal job UUID, then choose
**저장된 Run 조회**. The API must permit the job/Run/snapshot and, for a farm v3
job, the current farm selection reads. The authored path additionally needs
current farm registration, release, source-right and authored Run read scopes;
its [standard HTTPS runtime option](../contracts/api-runtime-authored-run-v1.md)
requires a protected operator factory. The authored browser path has response
double checks and an explicit stored Run HTTPS browser smoke; whole backend CI
acceptance and the actual product CLI path remain separate.
This screen reads existing results; it does not submit a new simulation or
invent a demo Run. Expand **완료된 열 작업 선택** to change or reread the record.
Use the slider, previous/next minute, table timestamp buttons or optional
automatic playback. Temperature color and the heat bar are relative to this
Run, with explicit legends. The geometry is conceptual and has no measured
farm dimensions. All six values remain available when WebGL fails.

Three.js `0.186.1`, ECharts `6.1.0` and Three types `0.186.0` are locked.
Original notices for Three, ECharts, its d3 material, zrender and tslib are
served from `public/licenses/`. No crop, equipment or stock 3D asset is shipped.
See the [fixed replay verification](../research/web-thermal-replay-implementation.md)
and [authored replay verification](../research/web-authored-thermal-replay-implementation.md)
for browser checks, screenshots and remaining holds.

## Apply a saved assumption

The economic screen can explicitly select an existing numeric edit slot, confirm
ownership/use/display rights with redistribution denied, register the rights and
a new joint-shock revision, and select that exact revision for calculation.
Knowledge time and applicability must cover the pinned decision/period. The
server still rejects invalid rights, units, conservation and settlement paths.
General baseline/event/settlement authoring is pending. See the
[implementation evidence](../research/web-joint-amendment-implementation.md).

## Monthly cash

After reading a completed economic result, request its monthly cash explicitly.
The [cash API](../contracts/api-economic-cash-flow-v1.md) revalidates the same
job proof, immutable inputs, current read scopes and ledger replay. Amounts
remain exact server decimal strings; unavailable cash stays null/“미확인”.
The table groups months in Asia/Seoul and labels minimum-balance instants as UTC.
It shows at most 12 months per page with manual next/first-page requests and a
keyboard-scrollable region. This is conditional user-assumption arithmetic;
it is not a future margin forecast or farm validation. See the
[cash implementation evidence](../research/web-economic-cash-implementation.md).

## Stored trial break-even plans

Choose an owned baseline, actual sale/collection terms, a target, quantity or
price, decimal range/step and 2–256 saved joint revisions in grid order. The
server checks rights, settlement, each derived value and fixed assumptions;
the browser does not generate or calculate trial assumptions. Unknown plan
admission reads the [historical receipt](../contracts/api-break-even-plan-receipt-v1.md)
with a canonical full-submission digest. Missing receipts keep the original
write unresolved; never-stored-intent resubmission and reload recovery remain
pending. Worker/result reads retain current source validation and full replay.
Listed zeros and crossing intervals remain distinct; a crossing is not an
exact continuous root. See the [verification record](../research/web-break-even-workspace-implementation.md).
