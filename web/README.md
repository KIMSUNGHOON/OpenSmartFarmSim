# Internal web shell

## 계산 접수 후 메뉴 이동 — 2026-10-21

[메뉴 이동 유지 수정](../research/execution-navigation-retention-20261021.md)을5174의 기존 화면에 적용했다.
새 빌드를 받으려면 한 번 새로고침한 뒤 인증 연결하고 같은 접수 파일로 기존 작업을 다시 연결한다.
이후 앱 내부 메뉴를 오가도 선택 모델·접수 파일·계산 작업 ID를 유지하고 현재 상태를 다시 조회한다.
다른 메뉴에서는 자동 조회/3D를 멈추며 저장 결과는 같은 작업에서 다시 연다.
계정 변경/연결 해제는 작업과 선택 파일을 지운다. 페이지 새로고침의 영속 복원은 이번 범위가 아니다.
실제 전체 작기/지역·품종 예측과 최종 제품 UI는 후속이며 전체 goal은 paused를 유지한다.

## 현재 접속 — 2026-10-21 재시작 복구

http://localhost:5173/ 는 완료 합성166일 저장 재생, http://localhost:5174/#ventilation-execution 은 기존 합성 환기 계산/3D입니다. [복구 검증](../research/WSL-post-boot-recovery-20261021.md)에서 원 결과/같은 토큰·키·두 화면을 확인했습니다. 사설 접속 안내는 `~/.local/state/OpenSmartFarmSim/20261009-full-harvest-user-preview/run-v35/service/OPEN-UI.private.txt`, `~/.local/state/OpenSmartFarmSim/20261013-ventilation-user-activation/user-service-v3/OPEN-UI-ISOLATED-POSTBOOT-20261021.private.txt`입니다. 새 CO₂ 사용자 적용은 후속입니다. 아래 날짜별 안내는 당시 기록입니다.

## 현재 접속·인증 갱신 — 2026-10-17

기존 화면은 http://localhost:5173/ , 합성 환기 계산/3D는 http://localhost:5174/#ventilation-execution 이다. [2026-10-17 인증/TLS 갱신](../research/frozen-preview-authentication-renewal-20261017.md)에서 원 결과/두 화면을 보존했다. 사설 안내는 `~/.local/state/OpenSmartFarmSim/20261009-full-harvest-user-preview/run-v27/service/OPEN-UI.private.txt`, `~/.local/state/OpenSmartFarmSim/20261013-ventilation-user-activation/user-service-v3/OPEN-UI-ISOLATED-20261017.private.txt`다. 토큰은 동일하며 공통/환기 인증은2026-10-18 20:50KST까지다. 새 Solar 사용자 배포·정상64단계 실행은 미완료이며 다음은 단계별 시간 계측이다. 아래 접속 기록은 당시 상태다.

**2026-10-13 WSL 재시작 복구:** 기존 저장 재생5173은 `run-v23/service/OPEN-UI.private.txt`, 원 joint5174는 `service-v1/serve-v25/OPEN-UI.private.txt`, 환기5174는 기존 `user-service-v3/OPEN-UI-ISOLATED.private.txt`의 접속 정보를 사용한다. 환기 서버는 `serve-v6`이며 같은 원 결과/코드·키를 유지했다. 인증 유효 종료는2026-10-14 21:53KST다. [복구/617수치 검사](../research/crop-greenhouse-solar-integration-implementation-20261013.md)를 참조한다. 새 일사 계산은 화면에 아직 미배포다.

**현재 — 2026-10-13:** [새 환기 모델의 로컬 사용자 적용](../research/crop-isolated-ventilation-user-activation-20261013.md)을 수용했다. 아래 새 접속 안내로 합성 계산과 저장3D를 확인한다. 지역/실제 품종·전체 작기·생산/경제 예측·최종 통합 UI는 미완료이며 이후 날짜별 기록은 당시 상태다.

## 새 환기 모델의 로컬 사용자 실행 — 2026-10-13

**http://localhost:5174/#ventilation-execution** 을 연다.
사설 접속 안내는 다음 파일이다. 접근 토큰과 작업/농장 식별자는 이 파일에서 확인하며 공개 문서에 복사하지 않는다.

```text
~/.local/state/OpenSmartFarmSim/20261013-ventilation-user-activation/user-service-v3/OPEN-UI-ISOLATED.private.txt
```

1. **내부 시험 연결 → 접근 토큰 → 연결 설정**으로 연결한다.
2. 안내 파일의 기존 작업/농장 값을 입력하고 **기존 계산 조회 → 같은 저장 결과 3D 열기**로 저장9시점을 본다.
3. 새 실행은 안내 파일의 새 접수 파일을 선택하고 **계산 접수**를 누른다. 진행/확정 부분3D·취소·완료 저장 결과를 확인한다.

현재 새 서비스는 `user-service-v3/serve-v4`, 고정 구현은 `6b4ffe8`이며 기존5173과 공동 API/작업자를 유지한다.
현재 인증 유효 종료는 **2026-10-13 22:43 KST**다. 종료 시 새 서비스는 정지하고 모델 경로를 원래 설정으로 복구한다.
별도 저장 영역과 결과는 유지한다. 새 서비스 재시작 전후 원문6개와 같은 저장9시점의 실제3D를 검증했다.
두 화면의 개발 기록은15초마다 조회한다. 연결 작업의 남은 시간0은 해당 로컬 적용의 완료이며 전체 제품 완료일은 미정이다.

아래 이전 접속 안내는 기존 공동 계산/저장 재생과 당시 상태에 관한 기록이다.

<a id="joint-execution-user-preview"></a>

**2026-10-11 21:19 KST:** [계산 중 연속 수치3D의 사용자 연결](../research/crop-climate-joint-prefix-advance-browser-20261011.md)을 합성128초 범위로 수용했다.
현재 새 환기 모델 적용은 서명 입력의 판본 호환 문제로 보류했다. [동시3D 검증·원 서버 복구](../research/crop-worker-metadata-memory-20261012.md) 뒤 기존 결과 조회를 확인했다. 현재 접속 파일은 아래 `run-v21`/`serve-v24`다. [사용자 API·메모리 수정/복구](../research/crop-ventilation-user-input-progress-20261012.md)에서 새 합성64/64와 원 결과/856파일·키·권리·동일 토큰 보존을 확인했다.
새 모델 최종 동시3D는 합1GiB 초과로 적용 보류다. 기존 두 계산 화면을 복구했다.
두 주소의20:11 KST 기록·15초 재조회·390px를 실제 확인했다. 기존2–4집중시간은 재산정 중이며 새 모델 미배포·전체 제품 완료일 미정이다.
새 환기 모델의 [완료 결과 웹 검증](../research/crop-greenhouse-ventilation-web-terminal-implementation-20261012.md)은 로컬 수용이며 사용자 서버에는 아직 미배포다.
5173은 완료 저장 결과 재생,5174는 같은 사용자 DB의 계산 상태/확정 부분 결과 자동 조회다.

## 계산 상태로 바로 진입 — 2026-10-11

**http://localhost:5174/#crop-execution** 을 새로 열거나 새로고침한다.
5173은 완료 결과 재생용이다. [진행 안내 조각](preview-progress-notice.html)을 기존 index의 `<body>` 바로 뒤에 넣은 별도 entry를 NGINX의 정확한 `/`와 `/index.html`에서 제공한다. 원 index·JS/CSS·API·DB는 보존한다. 기존5173을 새로고침하면 로그인 없이 최신5174로 이동할 수 있다. 복구 시 entry의 경로와 두 NGINX location을 함께 복원하며, 안내가 없으면 위5174주소를 직접 연다.
첫 화면의 **제품 개발과 배포 상태**와 **09 계산 진행 상태** 메뉴/바로가기에서 확인할 수 있다.
인증 설정이 펼쳐지고 연결 전/작업 선택 전을 명시한다. 인증 설정 뒤에도 계산 화면을 유지한다.
보호 토큰과 기존 작업 선택 값은 아래의 현재 `OPEN-UI-ADVANCE.private.txt`를 사용한다. 기존 토큰을 보존하고 서버를 복구했다.
기존 검증 작업은64/64 완료·9시점/3사건이다. 새 계산에는 검토된 새 접수 요청이 필요하며 같은 파일 재접수는 같은 작업을 연다.
[실제 화면8경로 기록](../research/product-ui-current-status-entry-20261011.md)은 타입/빌드와 원 DB 응답의 상태/시각 일치를 확인했다.
개발/배포 안내는 이 화면 빌드 시점의 기록이다. 새 환기 모델 미배포·최종 UI와 실제 생산/마진/추천 보류는 유지한다.

## 계산 상태·확정 부분 결과 자동 조회와 저장3D — 2026-10-11

**http://localhost:5174/** 에서 제품 App·실제 HTTPS API `https://127.0.0.1:8446`·영속 PostgreSQL·별도 자동 계산 작업자를 함께 실행한다.
같은 DB에 접수한 작업의 상태·확정 checkpoint와 계산 중 저장된 부분 결과의 표·그래프·수치3D를 자동 조회한다.
완료/hold 뒤 같은 저장 UTC의 결과3D를 연다.
현재 대상은 명시된 합성 입력의128초/64걸음 소프트웨어 검증이다. 전체 작기의 동적 기후나 실제 품종 예측을 제공하는 최종 제품은 아니다.

접속 토큰·기존 작업 ID/농장 필드·Windows에서 파일을 여는 경로는 다음 보호 파일에 있다.

`~/.local/state/OpenSmartFarmSim/20261010-joint-execution-live-preview/service-v1/serve-v24/OPEN-UI-ADVANCE.private.txt`

1. 위 파일을 로컬 편집기로 열고5174에서 **내부 시험 연결 → 접근 토큰 → 연결 설정**을 선택한다.
2. **08 성장 연구 3D → joint 실행 · 계산 상태와 완료 3D**를 선택한다.
3. 새 계산은 다음 파일을 업로드하고 접수한다.

   `~/.local/state/OpenSmartFarmSim/20261010-joint-execution-live-preview/service-v1/requests/advance128-user-v1.json`

4. 작업 상태·확정 checkpoint와 **계산 중 확정된 생장**을 확인한다. 새 저장값이 없으면 마지막 확인 시각을 유지한다.
   완료되면 **같은 저장 결과 3D 열기**를 누른다.
   이미 검증된 완료 작업은 보호 안내의 작업 ID와 농장 필드로 **기존 계산 조회**한다.
   같은 파일을 다시 접수하면 같은 작업으로 연결되며 새 계산을 만들지 않는다.

현재 토큰의 유효시각은 위 보호 안내 파일에서 확인한다. 페이지 메모리에만 두며 새로고침 뒤에는 다시 연결한다. 이번 복구는 기존 토큰을 보존했다.
자동 조회는 이전 응답 완료 뒤10초를 기다리고 서버 조회 시간이 추가된다. 일시 오류는 최대60초 간격으로 재시도한다.
이번 실제 브라우저에서 계산 중 원 저장 시점5개의 연속 전진→완료 원9시점/관리3사건·재접속을 확인했다.
실제 장면 관측 간격은33–34초였다. 매 시점이 즉시 갱신되는 성능 보장이나 전체 작기 성장 검증은 아니다.
탭 숨김/화면 이탈은 화면 조회를 멈춘다. 서버 계산 중단은 별도 취소 요청과 작업자 확인이 필요하다.
토큰을 저장소·URL·로그·스크린샷에 복사하지 않는다.

[P5 기능](../research/crop-climate-joint-prefix-ui-implementation-20261010.md)→
[reader v5](../research/crop-climate-joint-prefix-read-cost-implementation-20261011.md)→
[P6a 정상/hold/취소](../research/crop-climate-joint-prefix-cancel-browser-20261011.md)→
[P6b 실제 사용자 기동](../research/crop-climate-joint-prefix-user-activation-20261011.md)→
[A2 연속 시점 전진](../research/crop-climate-joint-prefix-advance-browser-20261011.md)을 각각 기록했다.
개발·검증용 별도 DB에서 실행한 작업은 이 사용자 DB에 자동 노출되지 않는다.
새 [환기 농장 결속](../research/crop-greenhouse-ventilation-farm-binding-implementation-20261011.md)은 실제 SCRAM 새6/회귀6그룹·fresh 동일·조회9수치 호출0을 통과했고 최종 보존 확인 뒤 로컬 수용했다. 새 모델은 UI 미배포이며 서버 custody/결과 API→worker/같은 UTC3D 수용이 남았다. 기존 계산 화면/개발·배포 안내는 유지한다.
기존5173은 아래의 완료166일 저장 재생용으로 유지한다. 두 주소의 통합/최종 U0–U5와 전체 U3는 미완료다.
현재3D는 저장 LAI·과실 구획·온도의 수치 모식도이며 최종 디자인·G0–G4·실제 생산/미래 마진/추천 보류는 유지한다.

## 기존 제품 앱의 로컬 동시 기동 — 2026-10-09

현재 사용자 확인용 **http://localhost:5173/** 은 `src/App.tsx`의 제품 빌드와 실제 HTTPS API
`https://127.0.0.1:8445`, 보존한 원 서명 DB의 별도 복원본을 사용한다.
**완료된 합성166일 계산의47,809저장 시점/5관리 사건·수확47,813행**을 조회한다.
아래 `demo:3d` 명령은 이 기동에 사용하지 않았다.
이 주소는 이번 WSL 세션의 내부 미리보기다. WSL/서버 종료 또는 읽기 계정 만료 뒤에는 재기동해야 한다.

새 접속 토큰과 원 결과의 다섯 입력값은 저장소 밖의 보호 파일에 있다.

`~/.local/state/OpenSmartFarmSim/20261009-full-harvest-user-preview/run-v21/service/OPEN-UI.private.txt`

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

**5173은 완료 저장 결과 화면이다.** 이 부모는 계산이 완료됐고 재생 버튼은 저장된 계산 시간을 이동한다.
계산 중 진행률·새 checkpoint를 자동으로 받지 않는다. 현재 선택한 작은 범위만 읽으며 중간 상태를 보간하지 않는다.
[새 계산 화면의 실제 서버/브라우저 검증](../research/crop-climate-joint-execution-browser-implementation-20261010.md)은 완료/hold/취소3경로를 통과했다.
그 격리 시험 서버는 종료됐다. [E9b 지속 사용자 연결](../research/crop-climate-joint-execution-user-preview-20261010.md)은 수용했고 새 계산 화면은 아래5174 안내를 따른다.
최근 공동 작물·기후32초 모델은 [API 투영](../research/crop-climate-joint-result-projection-implementation-20261010.md)과
[같은 세션 현재 조회10개 검사](../research/crop-climate-joint-current-query-implementation-20261010.md)까지 수용했다.
[보호 HTTP](../research/crop-climate-joint-http-route-implementation-20261010.md)도 실제 SCRAM/HTTPS·원 bytes/UTC·철회/취소로 수용했다.
[명시 서버 조립](../research/crop-climate-joint-runtime-implementation-20261010.md)도 실제 SCRAM/TLS·오조립/철회·계산0으로 수용했다.
[typed 웹 reader](../research/crop-climate-joint-web-client-implementation-20261010.md)도 웹457개/실제 HTTPS2개·
타입/제한된 비압축 빌드로 수용했다.
[그 모델의 표·그래프·같은 UTC3D](../research/crop-climate-joint-numerical-view-implementation-20261010.md)도
고유501개·실제 SCRAM/HTTPS/WebGL과 원값/권리/정리로 로컬 수용했다.
새 화면은 source/bundle 검증까지이며 **현재5173의 고정 빌드에는 배포하지 않았다.**
5173에서는 기존 결과가 자동 교체되거나 실행 중 새 checkpoint를 받지는 않는다.
5174는 계산 상태와 확정 부분 결과3D를 자동 조회한다. 128초의 여러 시점 전진은 수용했고 전체 U3는 미완료다.
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
# 개발 진행 확인 — 2026-10-12

**5173에서도 직접 확인:** `http://localhost:5173/` 을 새로고침하면 상단에 같은 개발 기록의5단계·갱신 시각·작업량 추정을 인증 없이 표시한다. 두 주소의 `/development-status.json`은 같은 현재 기록을 제공한다. [검증/복구 기록](../research/product-ui-inline-development-progress-20261012.md)을 참조한다. 이 기록은 계산 작업의 실시간 진행률이 아니며 현재 원 작업은64/64완료다.

현재 상태 화면은 **http://localhost:5174/#crop-execution** 이다. 새로고침하면 인증 없이 상단에서
최근 검증 완료 단계·다음 작업·기록 갱신 시각·새 모델의 배포 여부·남은 집중 작업량을 확인한다.
개발 기록을15초마다 다시 읽는다. 단계 수용뿐 아니라 구현 중인 작업, 검증 착수·실패·수정 후 확인도 기록에 게시한다. 완료 표시는 수용 증거가 있을 때만 바뀐다. 선택한 계산의 진행률은 인증/작업 선택 뒤 별도로 조회한다.

**두 주소 모두 개발 진행을 직접 표시한다.** 5173 상단과 **[5174의 제품 개발과 배포 상태](http://localhost:5174/#crop-execution)**는 같은 공개 기록을 사용한다. 2026-10-13 07:30 KST 기록에서 기존 입력/결속 판본의 조회 검증과 예상 시간 미정·판단 시각·철회 사유를 확인한다. [실제 브라우저·보존 검증](../research/product-ui-estimate-validity-20261012.md)을 통과했다.
현재 원 작업은64/64완료이고 새 환기 모델 사용자 적용은 입력 증거 판본 호환 처리/같은 배치 재검증까지 보류한다.
백엔드와 자동 작업자를 유지한 채 정적 UI만 갱신했다.5173은 기존 완료166일 저장 재생을 유지한다.
전체 제품 완료일과 실제 생산/경제/추천 관문은 미완료다.

`development-status-v2`는 `remaining_focused_hours: null`을 미정으로 표시하며 `estimate_reviewed_at`과 `estimate_reason`이 필수다.
v1의 기존 숫자 범위는 계속 읽는다. 두 소비자는 최신보다 오래되거나 동시각에 충돌하는 기록을 거부하고 조회 실패 때 마지막 유효 기록을 유지한다.

`web/public/development-status.json`은 검토된 개발 상태의 공개 기록이다. 자료·토큰·개인 농장 기록을 넣지 않는다.
배포 NGINX의 `/development-status.json`은 저장소 밖 `published/current.json`을 `no-store`로 제공한다.
검증 진행을 확인하거나 단계를 수용한 뒤 source의 시각/상태/근거를 갱신하고, handoff의 `current_ui_development_status_feed.published_directory`를 사용한다:

```sh
python3 -B scripts/publish-development-status.py --published-dir <handoff의-published_directory>
```

게시기는 원 기록을 SHA256 판본 파일로 보존하고 current 파일만 원자 교체한다. 같은 bytes 재시도는 무변경,
과거/동시각 충돌·형식/범위 오류는 거부한다. 게시 후 실제HTTP bytes/시각과 handoff의 current SHA를 대사한다.
재기동/배포 시 새 dist와 해당 NGINX alias를 함께 유지해야 한다. dist의 내장 기록은 빌드 당시 fallback이다.
오래된 시각·조회 실패는 화면에 명시하며, 이 feed는 전체 Codex 실행 로그나 실제 농장 계산 자료가 아니다.


## 일사 저장 화면 후보 — 2026-10-17

[구현/검증 기록](../research/crop-greenhouse-solar-saved-web-implementation-20261017.md)의 Solar 선택 화면은 소스와 실제 CI 캡처로 확인한다. 현재5173/5174에는 미배포다. 합성 기록 응답의 같은 UTC/단위·표/그래프/WebGL을 검증했으며 실제 API/저장 화면 결합과 사용자 적용은 S1b/S2b/S4를 따른다.
