# Internal web shell

## 기존 제품 앱의 로컬 동시 기동 — 2026-10-09

현재 사용자 확인용 **http://localhost:5173/** 은 `src/App.tsx`의 제품 빌드와 실제 HTTPS API
`https://127.0.0.1:8445`, 보존한 원 서명 DB의 별도 복원본을 사용한다.
**완료된 합성166일 계산의47,809저장 시점/5관리 사건·수확47,813행**을 조회한다.
아래 `demo:3d` 명령은 이 기동에 사용하지 않았다.
이 주소는 이번 WSL 세션의 내부 미리보기다. WSL/서버 종료 또는 읽기 계정 만료 뒤에는 재기동해야 한다.

새 접속 토큰과 원 결과의 다섯 입력값은 저장소 밖의 보호 파일에 있다.

`~/.local/state/OpenSmartFarmSim/20261009-full-harvest-user-preview/run-v3/service/OPEN-UI.private.txt`

2026-10-10 기존 서비스 종료를 확인한 뒤 보존 원본으로 재기동했다.
이전 토큰 대신 위 새 안내를 사용한다. 인증된 생장/수확 summary의 원 wire 일치·계산0을
[복구 기록](../research/crop-climate-joint-result-store-implementation-20261010.md#기존-사용자-ui의-실제-종료-확인과-복구)에서 확인했다.

1. 위 파일을 로컬 편집기로 열고 **내부 시험 연결 → 접근 토큰 → 연결 설정**을 선택한다.
2. **08 성장 연구 3D → 저장 결과 판본: calculation cycle v1**을 선택한다.
3. 안내의 다섯 필드를 입력하고 **저장 연구 조회**를 누른다.
4. 안내의 수확 ID를 **저장 수확 결과 ID**에 입력하고 **저장 수확 조회**를 누른다.
   현재3행의 원 시각·질량/단위와 전체47,813행 합계를 확인한다. **생장 시점 보기**는 같은 UTC의 저장3D로 이동한다.
5. **원 저장 시점 번호**에 예를 들어 **23905**를 넣고 **저장 시점으로 이동**을 누르면 중간의 저장 수치3D를 본다.
   **마지막 저장 시점**은 원47809번째로 이동한다. 표·그래프·LAI/과실50구획은 같은 원 UTC/값이다.
   생장 범위를 새로 읽으면 수확 선택이 초기화될 수 있어 수확 ID를 다시 조회한다.

접근 토큰은 읽기 전용이며 약24시간 유효하다. 토큰을 저장소·URL·로그·스크린샷에 복사하지 않는다.
이전 생장 전용/원3시점 미리보기의 토큰·안내는 현재 서버에 사용하지 않는다.
같은 원 부모의 전체 수확만 연결한다. 다른 부모의 작은 수확 ID를 붙이지 않는다.

**실시간 계산 상태 연결은 미완료다.** 이 부모는 계산이 완료됐고 재생 버튼은 저장된 계산 시간을 이동한다.
계산 중 진행률·새 checkpoint를 자동으로 받지 않는다. 현재 선택한 작은 범위만 읽으며 중간 상태를 보간하지 않는다.
3D는 LAI·과실 구획의 수치 모식도다. 실제 작물 외형·품종 생산·생과 수확·마진 예측·추천이 아니다.
지역부터 작물 생산·자원·경제까지 자동 연결한 최종 통합 UI/U1/U3도 미수용이다.

[현재 실제 기동·검증과 화면](../research/crop-harvest-full-user-preview-20261009.md),
[U0–U5 순서·수용 기준·조건부 일정](../tasks/plan.md#최종-제품-ui-통합--2026-10-09-사용자-요청)을 확인한다.
미리보기는 압축을 끈 production mode 빌드다. 일반 압축 빌드는 WSL 단일 RSS 한도 실패를 별도 보류한다.
목록 선택 코드는 포함되지만 원 디자인/실제 선택 경로의 U1 수용은 남았으므로 위 수동 조회를 안내한다.

## 지금 3D를 직접 보기

`web/`에서 Node `22.22.3`, npm `11.16.0`으로 다음을 실행합니다.

```bash
npm ci --strict-peer-deps
npm run demo:3d
```

브라우저에서 다음 주소를 엽니다.

- **계산 기반 성장 연구 3D:** `http://127.0.0.1:5173/demo/?view=growth` — 저장 수식 결과 6시점/5분의 LAI·기관 탄소량을 실제 3D/표/그래프에서 확인합니다.
- **수치 보류 진단:** `http://127.0.0.1:5173/demo/?view=growth&state=hold` — 실제 저장 시험의 실패 진단이며 정상 성장 장면을 표시하지 않습니다.
- **기존 열 재생:** `http://127.0.0.1:5173/demo/` — 120시점/두 시간의 직접 작성한 열 시험 응답입니다.

3D 장면은 자동으로 나타납니다. 성장 장면의 잎 배치/패치 수는 모식도이며
바닥 1m²당 한 면 잎 면적은 저장 LAI와 같습니다. 기관량은 mg_CH2O/m²로
생과 kg·착과수·숙기·수확 예측이 아닙니다. 성장 데모 응답은 실제 SCRAM/HTTPS
소프트웨어 시험에서 기록한 공개 합성 결과이며 시험 DB는 정리됐습니다.
[성장 화면](../research/artifacts/crop-replay-final-desktop.png)과
[검증·범위](../research/web-crop-replay-implementation.md)를 확인하세요. 이 데모는 서버 저장 내역을 만들거나 보여주지 않습니다.
실제 API에 연결한 내부 작업 화면의 **저장된 판본 → 목록 보기 → 작업 이력 보기**와는 별개입니다.
각 데모의 저장 시각·그래프·표를 조작할 수 있습니다.
이 명령은 loopback 전용 Vite 서버와 기록된 공개 합성 계산/열 시험 응답을 실행합니다.
PostgreSQL, 운영 토큰, 기상 수집, 제품 Codex CLI, 현장 자료는 사용하지 않습니다.
화면 값은 브라우저 소프트웨어 데모이며 작물 성장·수확·사업성을 예측하지
않습니다. `npm run build`의 일반 서비스 산출물에는 이 데모 페이지와 응답이
포함되지 않습니다. [실제 브라우저 캡처](../research/artifacts/local-synthetic-3d-demo.png)와
[검증 기록](../research/local-synthetic-3d-demo-implementation.md)이 있습니다.
종료하려면 터미널에서 Ctrl-C를 누르세요.

## 저장 Run의 비용과 평가 확인

실제 내부 HTTPS API에 연결한 환경에서 사용합니다. 현재 계정의 완료 작성 Run과
그 농장에 고정된 경제 판본·현재 열람 권한이 있어야 합니다.

1. **07 작성 Run 경제·평가 → 저장 Run 목록 조회**에서 Run을 선택합니다.
2. 저장 경제·평가 기록이 있으면 먼저 선택해 현재 결과를 조회합니다. 새 계산이 필요하면
   **새 경제 요청 준비 → 선택 Run 경제 계산 요청**을 누릅니다.
3. **경제 상태·결과 확인**으로 완료 서버 금액을 읽고 **작성 Run 월별 현금 조회**를 엽니다.
4. **작성 Run 평가 요청 → 작성 평가 상태 확인**으로 보류 근거를 읽습니다.
   **같은 Run 3D 열기**는 같은 저장 열 Run을 엽니다.

04 작성 농장 화면의 완료 Run에서도 **경제·평가 열기**로 이동할 수 있습니다.
재연결 뒤에는 목록에서 저장 기록을 다시 선택합니다. 응답 유실 때는 같은 요청의
재확인 버튼을 사용합니다. 합성 3D 데모에는 이 경제 저장 기록이 없습니다.
금액은 사용자 가정의 조건부 산술이며 검증된 미래 마진·작물 추천이 아닙니다.
[검증 범위와 남은 보류](../research/web-authored-economic-assessment-implementation.md)를 확인하세요.

The current screen submits registered synthetic location research and reads
its real server job/hold status. When research succeeds, the work screen can
admit owned fixture ingestion and collection review through their existing
server endpoints, then read both job statuses and a review hold. These stage
IDs remain in page memory during a request. After a full refresh, reconnect and
use **저장된 조사 보기** on the work screen to find the tenant's stored research
job and its latest linked collection/review jobs. **저장된 시도 보기** pages
through earlier collection/review jobs for that research. The lookup rechecks current
research source/context authority and holds new admission if it has changed. This is
an internal candidate path, with no G0 approval or Run publication. The third
screen lists exact stored economic assumptions, registers a numeric revision
and admits/reads a selected conditional
ledger calculation, including a manually requested monthly cash table. A
break-even section selects existing sale/collection and saved trial revisions,
admits a finite plan and reads its completed result. The fourth screen can
register an authored farm version from explicit user assumptions and already
registered research, market hold and economic references. It can also look up
an existing version, list the tenant's stored registrations and that version's review/simulation job history, submit review and thermal work, read server job/hold status,
and open a completed stored Run. The same screen can list the account's completed Run IDs
without selecting a farm; opening an item makes an exact current server read before 3D replay.
The form does not discover prerequisite records
or issue an independent release. An uncertain registration is retried with the
same frozen request. The last verified
farm ID, revision and registration hash are kept in this browser tab only; after
reconnection the server must authorize and confirm the exact version before it
appears again. Tokens and review/simulation job IDs are not stored. The fifth screen replays
either a fixed or a farm-authored synthetic thermal Run in Three.js, a chart, an HTML table and six
text values with one selected stored timestamp. Automatic source research and
nontechnical farm input,
baseline/event/settlement authoring, automatic trial assumptions, durable
cross-category Run catalog, map, full replay
acceptance and production hosting are pending. See the
[location contract](../contracts/web-location-shell-v1.md),
[owned source workflow](../contracts/web-owned-source-workflow-v1.md) and
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
`Authored API PostgreSQL smoke` CI runs this authored smoke and the composite
authored browser test after its focused database/API tests. The broad backend
workflow excludes only that composite browser file; both checks remain in CI. Its review,
release and CLI authorities are synthetic software fixtures, not G1 proof.

The [composite authored path](../research/authored-full-software-path-implementation.md)
also registers an owned farm, runs its synthetic review/release and actual
publication worker, then checks the registered version, new review and thermal
jobs admitted by Chromium, their worker completions, and the resulting Run over HTTPS:

```bash
uv run --locked --group dev pytest -q -s --tb=short tests/test_authored_full_software_path.py
```

It uses the same protected PostgreSQL test setup. The browser fills the authored
form and submits registration over HTTPS. It then admits a fresh review job;
the harness executes
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
double checks and an explicit stored Run HTTPS browser smoke; hosted CI
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

## Join completed calculations for assessment

Use **06 계산 평가** with an operator-assembled authenticated API. Supply the
completed thermal and economic job IDs for the same supported calculation
context. The server revalidates both parents; the browser does not create crop
evidence or determine compatibility. Current assessments finish held, displaying
the public missing evidence categories. Separate authored Run receipts are not
supported by this join yet.

An uncertain POST retains its parents and key for the same retry. Save the
request record before reloading if the reply is lost. A known assessment job
can be reopened using **저장 평가 조회** after reconnecting; read failures use GET
retry and do not create another assessment. Tokens are not stored. General
regional orchestration and unknown-admission reload recovery are still pending.
See the [contract](../contracts/web-calculation-assessment-v1.md) and
[verification record](../research/web-calculation-assessment-implementation.md).
