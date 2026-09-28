# 구현 순서

상태: **2026-09-27 C0 기본 구조는 호스팅 시험으로 수용됐고, C1 계약과 G1 구현은 진행 중이다.** 제품 주장은 [제품 명세](../docs/PROJECT_SPEC.md), 객체·절차 계약은 [아키텍처](../docs/ARCHITECTURE.md), 소프트웨어는 [기술 스택](../docs/TECH_STACK.md), 금액 계산은 [경제 계약](../docs/ECONOMICS.md), 시장 자료의 시점은 [시장 명세](../docs/MARKET_INTELLIGENCE.md)를 따른다. [첫 구현 범위](../docs/IMPLEMENTATION_SLICE.md)는 초기 구현 경계를 정하고, [구현 준비 현황](../docs/IMPLEMENTATION_READINESS.md)은 확인된 공백을 기록한다. 체크 가능한 일은 [작업 목록](todo.md)에 있다. 작업 체크는 해당 작업의 증거만 뜻한다.

## 작업 의존성

```mermaid
flowchart LR
  repo-bootstrap --> provenance-g0 --> thermal-synthetic-parameters --> thermal-contract --> fixture-policy --> thermal-engine
  repo-bootstrap --> compose-runtime --> durable-jobs --> decision-evidence-store --> cli-worker-store-bridge --> cli-worker
  repo-bootstrap --> db-driver-bootstrap --> durable-jobs
  durable-jobs --> job-intent-idempotency --> api-flow
  compose-runtime --> backend-ci
  db-driver-bootstrap --> backend-ci
  provenance-g0 --> cli-worker
  provenance-g0 --> market-context --> economic-ledger --> sales-settlement --> market-scenario --> economic-break-even
  fixture-policy --> economic-ledger
  fixture-policy --> market-scenario
  market-context --> market-scenario
  economic-ledger --> economic-break-even
  thermal-contract --> thermal-engine
  cli-worker --> api-flow
  market-context --> market-hold-store --> api-flow
  thermal-g1-publisher --> market-hold-store
  thermal-engine --> thermal-decision-clock-contract --> thermal-g1-publisher --> api-flow
  decision-evidence-store --> thermal-g1-publisher
  cli-worker --> thermal-g1-publisher
  market-scenario --> api-flow
  economic-break-even --> api-flow
  api-flow --> web-shell --> web-replay --> end-to-end-g1
  cli-worker --> end-to-end-g1
  compose-runtime --> end-to-end-g1
  provenance-g0 --> g0-authority-store
  durable-jobs --> g0-authority-store
  g0-authority-store --> kma-g0
  g0-authority-store --> market-source-g0
  thermal-contract --> kma-g0
  cli-worker --> kma-g0
  market-context --> market-source-g0
  cli-worker --> market-source-g0
  kma-g0 --> g2-evidence
  end-to-end-g1 --> g2-evidence
  market-source-g0 --> forecast-engine
  g2-evidence --> forecast-engine
  market-scenario --> forecast-engine
  forecast-engine --> g3a-evidence --> crop-ranking --> g3b-evidence
  economic-ledger --> g3a-evidence
  market-context --> g3a-evidence
  end-to-end-g1 --> service-economics --> g4-operations
  end-to-end-g1 --> g4-operations
  kma-g0 -.->|실제 원천 공개 시| g4-operations
  market-source-g0 -.->|시장 원천 유래 경로 공개 시| g4-operations
```

점선 선행 조건은 표시된 실제 원천 유래 공개 경로에만 적용된다. `market-source-g0`는 기존 출처·시장 계약, 영속 G0 승인 저장소와 CLI 작업자 뒤에서 병행할 수 있으며, 첫 합성 G1의 선행 조건이 아니다. 시장 자료에서 유래한 시나리오·근거 카드와 후속 미래 전망에는 해당 시장 G0가 필요하다.

`repo-bootstrap`의 예정 파일은 `backend/pyproject.toml`, `backend/uv.lock`, `web/package.json`, `web/package-lock.json`, `.gitignore` 다섯 개다. `repo-bootstrap`의 잠금·설치 확인은 완료됐다. 후속 `compose-runtime`의 정적 골격 파일은 정확히 `compose.yaml`, `.env.example`, `backend/Dockerfile`, `web/Dockerfile`, `.dockerignore` 다섯 개다. Compose는 모듈형 백엔드의 web·API·수집·CLI·수치 계산 별도 서비스/작업자 역할과 PostgreSQL·영속 POSIX 아티팩트를 정의한다. `depends_on`의 시작 순서만 믿지 않고 PostgreSQL `pg_isready` 건강 검사와 `service_healthy` 조건을 쓴다. `.env.example`은 비밀값 없이 두고 실행 시 비밀 파일/관리자로 서비스별 최소 권한을 주입하며 PostgreSQL은 `POSTGRES_PASSWORD_FILE`을 쓴다. 비밀·제한된 원본 자료는 저장소와 빌드 문맥에서 제외한다. 실제 검증한 기반/배포 이미지의 버전·digest를 고정하고, PostgreSQL 18을 선택한다면 데이터 볼륨은 `/var/lib/postgresql`에 둔다. CLI 작업자에는 Docker 소켓을 마운트하지 않는다. `db-driver-bootstrap`은 Psycopg 잠금·로컬 연결과 JSON Schema 시험 의존성을 별도 확인해 `durable-jobs`의 다섯 파일 범위를 지킨다. `durable-jobs`는 작업 입력 복원과 게시 원자성을 다루고, `decision-evidence-store`는 실패·취소를 포함한 CLI 시도별 변경 불가 원문/JSONL 감사 보존을 별도로 검증한다. `cli-worker-store-bridge`는 단계별 임대, 검증된 보류의 열람 경로, 실행 사건 결합을 실제 CLI 작업자보다 먼저 검증한다. `g0-authority-store`는 형식 계약과 실제 서버 승인·보관 경계를 분리한다. 모듈형 Python 백엔드 하나에서 FastAPI, HTTPX 제공자 연결 도구, PostgreSQL 임대 작업, 제한된 **실제 Codex CLI `gpt-6-sol`/`xhigh` 작업자**, 결정적 NumPy/SciPy/Pint 열 모델, `Decimal` 농장 계산을 분리한다. React/TypeScript/Vite, MapLibre, Three.js, ECharts, HTML 표는 같은 API 기록을 읽는다. 이 계획은 LangChain, LangGraph, Deep Agents, Hermes 계층을 추가하지 않는다.

## 확인 지점과 필수 경로

| 확인 지점 | 완료 증거 | 허용되는 주장 범위 |
| --- | --- | --- |
| C0 — 실행 가능한 기본 구조 | `repo-bootstrap` 수용 뒤 Docker/Compose 호스트에서 `docker compose config -q`로 비밀값을 출력하지 않고 정식 모델 검증, 그 단계의 파일만으로 가능한 이미지 빌드, 앱 소스 없이 PostgreSQL의 `pg_isready` 준비와 재생성 후 데이터 보존 확인. 두 작업의 증거가 모두 필요하다. **수용:** [C0 Actions run 36303540834](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/36303540834)에서 두 Compose 모델·의존성 이미지 빌드·PostgreSQL 18.6 건강/재생성/데이터 보존·정리가 성공했다. 사용자 홈의 PostgreSQL 16.15는 별도 로컬 SQL 시험용이다. | 도구·구성·DB 기동/영속성 확인에 한정. web/API/작업자 전체 기동, 장애 복구, 실제 CLI 세 단계와 UI는 후속 작업이다. |
| C1 — 계약 확정 | 출처·권리·판본과 `MarketContext` 시험, 확정한 열·수증기 방정식·단위·제어 및 별도 합성 열 매개변수·포화압 법칙·사전 수용 한계, 작성자와 해시가 있는 합성 당일 출하·검수 및 명시적 사용자 시장 스트레스 입력. | 외부 자료 G0나 현장 정확도는 확인하지 않음. |
| C2 — 지속 백엔드 | 중복 처리·임대·복구되는 작업, 구조화 출력·보류·감사를 갖춘 실제 CLI 세 단계, 재실행 가능한 열·수증기와 `Decimal` 경제 원장, 날짜·판본·권리·계약·재고 제약을 지키는 수요·공급·거시 공동 시나리오, 시험값마다 전체 경로를 다시 계산하는 세 목표 손익분기, 버전 관리 API. | 근거를 표시한 조건부 계산에 한정; 거시 정밀도·미래 전망 주장 없음. |
| C3 — 첫 전체 사용자 경로 | 좌표 → 과거 기간 → 한 구역 → 실제 CLI 조사·검토·평가 → 변경 불가한 합성 입력 스냅샷 → Run → `unavailable`의 사용자 소유·명시 가정만 사용하는 조건부 공동 충격·날짜별 경제 결과 → 3D·그래프·표 → 최종 `hold`와 재시도·재시작 시험. 가짜 MarketSnapshot·자료 유래 전망·작물 순위는 내지 않는다. | **합성 자료 G1 계약 추적 시험**에 한정하며 검증된 전망은 없음. |
| C4 — 권리를 확인한 실제 원천 | 기상청 경로의 정확한 제품 권리·시각 의미·보유율·QC와 별도 시장 원천 경로의 정확한 제품 ID·발표/이용 가능/조회 시각·판본·권리·단위/등급/채널/지역/날짜 적합성·원본 해시·QC. 각각 승인 스냅샷 또는 사유가 있는 보류로 끝난다. | 해당 원천·범위의 G0에 한정. 두 실제 원천 경로는 첫 합성 G1의 선행 조건이 아니다. |
| C5 — 후속 구현과 주장 관문 | `g2-evidence` 뒤 `forecast-engine`의 버전 고정 ForecastRun과 보류, 독립 rolling-origin 증거에 따른 `g3a-evidence`, 이어서 `crop-ranking`의 대응 비교/보류와 `g3b-evidence`. 별도 `service-economics`의 요청별 실제 원가·서비스 수지·용량 시험을 거쳐 배포 계정·권리·운영 증거로 `g4-operations`를 평가한다. | 엔진 구현만으로 G3a/G3b를 열지 않는다. G4도 별도 관문이며 해당 기능의 증거 범위에 한정된다. |

구현의 필수 경로는 `repo-bootstrap → compose-runtime + db-driver-bootstrap → durable-jobs → decision-evidence-store → cli-worker-store-bridge → cli-worker`, `provenance-g0 → thermal-synthetic-parameters → thermal-contract → fixture-policy → thermal-engine → thermal-decision-clock-contract → thermal-g1-publisher`, `market-context + fixture-policy → economic-ledger → sales-settlement → market-scenario → economic-break-even`, 그리고 이들이 합쳐지는 `api-flow → web-shell → web-replay → end-to-end-g1`이다. `api-flow`에는 영속 `market-hold-store`, `market-scenario`, `economic-break-even`이 모두 선행하고, `end-to-end-g1`에는 `compose-runtime`도 선행한다. 첫 경로는 좌표·기간·구역·합성 원천을 각각 하나씩 쓰고 당일 출하·검수 원장을 다룬다. `unavailable`이면 첫 G1 조건부 스트레스는 `origin=user`, `evidence_level=assumed` 가정만 받고 Assessment는 `hold`다. `available`이면 유효한 권리·판본과 `available_at <= decision_at`을 갖춘 G0 승인 MarketSnapshot을 요구한다. 조건부 시나리오의 계산 재현은 미래 수확·가격·마진·거시 변수의 예측 정확도를 입증하지 않는다. 필수 런타임 CLI와 최종 보류가 포함되며 모의 작업자로 완료할 수 없다. 열 매개변수·계약과 합성 후보 엔진의 연산 순서·잔차는 수용됐다. `run_status=candidate`의 실제 CLI 실행·출력 증명, 서버 입력 연결, 독립 재계산, 승인 trace 두 개의 최종 해시 재결속과 원자 게시가 `cli-worker`와 `thermal-g1-publisher`의 연결에서 입증될 때까지 G1 Run은 막는다. 고정 manifest v2의 보류를 소급 삭제하지 않고 새 해제 증거 판본을 기록한다. 기존 날씨·경제 fixture v1은 바꾸지 않고 새 열 매개변수와 함께 manifest v2로 묶는다. 중요한 경제 입력이 빠지면 0으로 채우지 않고 미확인으로 둔다.

후속 미래 전망 경로는 `market-context + cli-worker → market-source-g0`, `kma-g0 + end-to-end-g1 → g2-evidence`, `market-source-g0 + g2-evidence + market-scenario → forecast-engine → g3a-evidence → crop-ranking → g3b-evidence`다. `g3a-evidence`에는 `economic-ledger`와 `market-context`도 선행한다. 엔진의 계약 시험은 독립 농장 기록의 G3a 검증이나 대응 후보의 G3b 검증을 대신하지 않는다. 공개 조건부 서비스 경로는 `end-to-end-g1 → service-economics → g4-operations`이고 G3a/G3b 또는 시장 원천 G0가 무조건 선행하지 않는다. 실제 기상청 원천 또는 시장 원천 유래 기능을 공개할 때에는 각각 해당 G0와 권리 검사가 추가된다.

## 병행 가능한 외부 증거 경로

전문 Codex CLI 조사는 합성 자료 소프트웨어를 만드는 동안 [기상청 관측소 메타데이터](https://data.kma.go.kr/tmeta/stn/selectStnList.do?pgmNo=123), [ASOS 시간자료 보유율/QC](https://data.kma.go.kr/data/grnd/selectAsosRltmList.do?pgmNo=36&tabNo=2), [API 필드](https://apihub.kma.go.kr/apiList.do), 제품별 [권리](https://data.kma.go.kr/cmmn/static/staticPage.do?page=pageCr)를 조사할 수 있다. 실제 자료 연결 도구는 제품 ID·권리·`SI` 구간/`TM` 경계·시범 대상의 측정된 보유율이 입증될 때까지 `hold`다. 목록에 있다는 이유만으로 시범 관측소·기간을 고르지 않는다. 합성 자료 경로는 그 실제 자료 증거 없이 진행할 수 있지만, 표시와 기록으로 G0 통과로 잘못 취급되지 않게 해야 한다.

시장 원천도 아직 선택하거나 채택하지 않았다. `market-source-g0`는 실제 연결할 제품의 정확한 ID·원본 판본·공표 및 접근 가능 시각·용도별 권리·적합성·QC를 확인한 경우에만 MarketSnapshot을 게시한다. 권리 또는 과거 판본을 복원할 수 없으면 Market hold report를 남긴다. 이 대기 상태는 첫 합성 G1을 막지 않지만 시장 자료 유래 경로와 ForecastRun은 막는다.

협력 농장의 동의와 센서·정산·계약 접근권도 동시에 추진할 수 있다. G2에는 국내 현장의 독립 기후 측정과 주장할 물리량에 대응하는 계량이 필요하다. `forecast-engine`은 승인 시장 스냅샷과 G2/현장 근거 위에서 연구용 실행 또는 명시적 보류를 구현한다. G3a에는 시점을 분리한 수확·등급·판매·재고·정산·비용·현금 기록과 결정 당시 판본으로 한 독립 검증이 필요하다. `crop-ranking`은 그 뒤 후보 대응 비교와 구별 불가 시 보류를 구현한다. G3b에는 같은 실행 가능한 결정에서 비교할 작물 후보 간 대응 자료가 추가로 필요하다. **G3b 협력 자료 조사는 첫 G1 구현의 선행 관문이 아니다.** 사용자가 전문 농업 판단을 할 필요는 없다. CLI 조사가 증거와 아직 풀리지 않은 질문을 정리한다. 이는 코드 완료 여부와 다른 외부 접근 문제다.

G3a/G3b 없이도 조건부 서비스에 대한 G4 평가는 가능하다. 그 전에 `service-economics`에서 무료·유료·실패·재시도 요청과 실제 CLI 청구·자료 API/타일·컴퓨트·저장·백업·지원비, 유료 매출·고정비를 별도 원장으로 대사한다. 실제 배포 계정, 작업마다 별도 비특권 CLI 컨테이너·임시 파일시스템·제한된 외부 통신과 스키마 시험, 허가된 원천·지도 타일, 백업·복구, 실측 한도·비용·수요·운영 재원도 필요하다. 장기 실행 Compose CLI 서비스나 C0만으로 이 격리를 입증하지 않는다. C3나 C4만으로 공개 운영 준비 또는 전망 주장을 인정하지 않는다.

사용자 가정 원천의 후속 진행 후보는 [저장 계약](../contracts/market-user-source-store-v1.md)과 [구현 증거](../research/market-user-source-implementation.md)에 기록했다. API source factory에 연결할 7종 읽기 인터페이스와 실제 작업 pin을 제공하며, 시장/경제 전체 작업의 선행 증거와 미완료 범위는 기존 작업 목록을 유지한다.

열 게시기·지속 작업 다음의 [명시적 simulation 실행 후보](../contracts/thermal-simulation-worker-v1.md)를 추가했다. 서명 검토가 준비된 작업의 Run/완료를 원자적으로 연결하는 프로세스이며, 실제 검토·release·API 제출·평가와 전체 G1의 기존 선행 증거는 여전히 필요하다.
