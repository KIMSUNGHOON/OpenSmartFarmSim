# 첫 구현 범위

상태: **내부 구현 계약 초안, 2026-09-27. `repo-bootstrap`과 `compose-runtime` C0는 수용됐다. 출처/G0 판정 계약 101개, 시장 문맥 87개, 합성 weather/economics fixture 30개와 열 trace 구조 계약 55개 집중 시험이 통과했다. 열 매개변수·포화압 법칙의 사전 등록, 서버 영속 승인 저장소, 실제 원천 G0와 G1 전체 경로는 아직 수용 전이다.** 세부 기준은 [제품 명세](PROJECT_SPEC.md), [아키텍처](ARCHITECTURE.md), [경제 계약](ECONOMICS.md), [시장 자료의 시점](MARKET_INTELLIGENCE.md), [기술 스택](TECH_STACK.md)을 따른다. 실제 준비 상태는 [구현 준비 현황](IMPLEMENTATION_READINESS.md)에 기록한다.

## 1. 목표와 확인할 사용자 경로

사용자가 확인한 국내 좌표 한 점, 과거 기간 하나, 개념적 온실 한 구역의 내부 경로를 끝까지 만든다. 사용자는 `decision_at`, 온실 구역·재배 가정, 날짜가 있는 농장 물량·가격·비용·투자·수금/지급 가정과 수요·공급·거시 조건부 충격을 입력한다. 중단 후 재개할 수 있는 작업은 **실제 런타임 Codex CLI `gpt-6-sol`과 `xhigh`**를 자료 조사·수집 계획, 수집 입력·권리·품질 검토, 최종 평가의 세 단계에서 실행한다. 서버가 각 구조화된 판단을 검사한다. 승인된 제공자 연결 도구 또는 직접 만든 것으로 명확히 표시한 합성 시험 자료가 변경 불가한 원천 기록과 스냅샷을 만든다. 수식과 버전을 확정한 열·수증기 모델은 실내 상태, 제어 상태, 모델 난방 열수요와 공급열을 결정적으로 계산한다. 버전이 고정된 시장 시나리오 엔진은 공통 충격과 계약·재고 제약 아래 날짜별 수확 `H`·판매 가능 `P`·판매 인정 `S`, 등급·채널·차감 전 계약가격과 증거가 완전한 경우의 조건부 순송금 단가·변동비·수금/지급 경로를 함께 계산한다. 실제 정산 완료 농가 순수취가는 정산서와 은행 입금 대사 전까지 보류한다. 별도 `Decimal` 계산기는 조건부 농장 운영 결과, 입력으로 정의할 수 있는 세 가지 손익분기 목표, 월별 현금 잔액을 계산한다. API는 완료 후 변경하지 않는 `run_id`를 제공하고, 3D 장면·그래프·표는 같은 `run_id + timestamp`를 읽는다. 평가 결과는 근거 없는 작물 선택을 명시적으로 `hold`하고 누락 증거를 제시한다.

**완료 경로는 두 가지다.** 합성 자료만 쓰는 **G1 계약 추적 시험**은 출처와 합성 여부를 표시한 변경 불가 입력과 실제 CLI 호출로 작업·화면 전체를 시험한다. 소프트웨어 연결과 결정적 재실행만 확인하며 외부 자료의 G0, 현장 정확도의 G2, G3 예측·순위를 입증하지 않는다. 권리를 확인한 **실제 자료 G0 경로**는 승인된 기상청 제품, 실측한 관측소·기간의 일사 `SI` 보유율, 확인된 시각 의미, 해당 용도의 이용권이 필요하다. 권리나 시각 의미가 없으면 `hold`를 기록하고 실제 자료 Run을 게시하지 않는다. 이때도 합성 자료로 계약은 시험할 수 있다. 실제 자료 보류를 합성 자료로 자동 대체하지 않는다.

`MarketContext`는 정확히 `{kind: "available", snapshot_id}` 또는 `{kind: "unavailable", hold_report_id}`다. 보류 사유와 누락 증거는 참조한 Market hold report에 둔다. 그 보고서는 승인된 MarketSnapshot의 증거가 아니다. 첫 G1 내부 시범에서 `unavailable`이면 `origin=user`, `evidence_level=assumed`로 표시한 사용자 가정만 **조건부** 농장 계산에 쓰고 최종 Assessment는 `hold`한다. 후속 단계에서는 접근·이용권, 해당 농장·기간·채널·계약 적용성, 원장·정산 대사를 독립 확인한 비공개 농장 계약·정산·원장을 조건부 또는 해당 농장의 과거 계산에 쓸 수 있다. 이 기록도 공개 시장 전망이나 작물 순위의 근거로 승격하지 않는다. 후속 객체인 `ForecastRun`에는 승인된 `MarketSnapshot`이 필요하다. 결정 당시 시장 근거는 `available_at <= decision_at`을 충족해야 한다. `decision_at` 뒤에 관측한 과거 날씨로 만든 결과에는 **사후 재현**(`ex_post_replay`)을 표시하며 당시의 예측으로 취급하지 않는다.

첫 G1의 시장 조건부 스트레스도 `unavailable`일 때는 사용자가 직접 소유·명시한 `origin=user`, `evidence_level=assumed` 가정만 사용한다. 이 경로는 자료 유래 전망·작물 순위·가짜 MarketSnapshot을 만들지 않는다. `available`이면 권리와 판본이 유효하고 `available_at <= decision_at`인 G0 승인 MarketSnapshot을 요구한다. 수요·공급·거시 충격의 크기와 방향, 가격·물량·비용 전가 경로는 입력의 근거와 적용 범위를 보존한다. 조건부 산술의 재현은 거시 변수의 정밀도나 미래 가격·수확·마진 예측의 검증이 아니다. 그런 주장은 이후 독립 증거와 해당 관문을 기다린다.

**후속 구현 경로는 첫 합성 G1과 별개다.** `market-source-g0`는 실제 제품의 권리·판본·시점·단위·품질·적합성을 확인해 시장 G0 스냅샷 또는 보류 보고서를 만든다. 이 작업은 첫 합성 경로를 막지 않지만 자료 유래 시장 시나리오와 근거 카드, 이후 ForecastRun의 선행 조건이다. `forecast-engine`은 시장 G0 및 필요한 G2/현장 근거 뒤 버전 고정 미래 경로 또는 명시적 보류를 만들고, 독립 농장 기록의 rolling-origin 시험을 거친 `g3a-evidence` 전에는 미래 마진을 게시하지 않는다. `crop-ranking`은 G3a 이후 같은 실행 가능한 조건에서 후보를 대응 비교하거나 보류하며, 독립 `g3b-evidence` 전에는 순위를 게시하지 않는다. `service-economics`는 첫 G1 뒤 농장 손익과 분리된 요청별 서비스 수지·한도·재원 근거를 준비하고, 실제 계정·청구·수요 증거를 포함한 G4 전에 공개 운영을 열지 않는다.

## 2. 초기 설정 작업에서 만들 실행 명령

`repo-bootstrap`의 다섯 파일 `backend/pyproject.toml`, `backend/uv.lock`, `web/package.json`, `web/package-lock.json`, `.gitignore`와 잠금 설치 확인이 완료됐다. `compose-runtime`의 `compose.yaml`, `.env.example`, `backend/Dockerfile`, `web/Dockerfile`, `.dockerignore`도 준비됐다. [C0 Actions 실행](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/36303540834)에서 두 Compose 모델, web/API 의존성 이미지 빌드, PostgreSQL 18.6 건강 확인·컨테이너 재생성 뒤 데이터 보존이 통과했다. 앱 역할 전체 기동과 실제 CLI 세 단계, API·브라우저 경로는 후속 작업이다.

다음 명령은 각 후속 소스·시험이 생길 때 해당 작업의 범위를 확인한다. C0 수용은 위 호스팅 실행으로 별도 확인했다.

```sh
(cd backend && uv run pytest)
(cd web && npm ci && npm run typecheck && npm run test && npm run build)
docker compose config -q # compose-runtime: Docker/Compose 호스트에서 비밀값 출력 없이 구성 검증
```

`compose-runtime` C0는 Docker/Compose 호스트에서 정식 Compose 모델 [`docker compose config -q`](https://docs.docker.com/reference/cli/docker/compose/config/)와 web/API 의존성 이미지를 확인하고, PostgreSQL의 `pg_isready` 준비 상태와 컨테이너 재생성 뒤 데이터 보존을 [호스팅 실행](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/36303540834)에서 검증해 수용했다. 비밀이 풀린 `docker compose config` 출력을 증거로 남기지 않았다. 현재 로컬 호스트에는 Docker Engine과 소켓이 없어 앱 역할 기동·작업자 복구·실제 CLI 세 단계·UI 경로는 후속 `end-to-end-g1`에서 확인한다.

## 3. 제안하는 프로젝트 구조

```text
backend/app/       FastAPI, 출처·관문 계약, 작업, CLI 작업자, 결정적 계산기
backend/tests/     집중 Python 시험과 데이터베이스 복구 시험
web/src/           좌표·작업 흐름, MapLibre 지도, Three.js 구역, ECharts와 표
web/e2e/           브라우저 경로와 접근 가능한 재생 시험
contracts/         버전 관리 JSON 스키마, 열 모델 계약, OpenAPI 출력
fixtures/          직접 만든 합성 원천·가정 기록과 manifest
ops/               배포·권리·계정·G4 증거
research/          G2/G3 시험 계획과 출처 등록부
scripts/           재현 가능한 G1 수용 실행기
compose.yaml       자체 운영 web/API/작업자/PostgreSQL/볼륨 구성
.env.example       비밀값 없는 환경 변수 이름과 설정 예시
backend/Dockerfile  부트스트랩 파일부터 빌드할 모듈형 백엔드 이미지 정의
web/Dockerfile      부트스트랩 파일부터 빌드할 웹 이미지 정의
.dockerignore       비밀·원본 자료의 빌드 문맥 제외
```

백엔드는 모듈형 Python 코드베이스 하나로 두고 Compose에 web·API·수집·CLI·수치 계산의 별도 서비스/작업자 역할과 PostgreSQL을 정의한다. PostgreSQL은 지속 작업과 메타데이터를, 영속 POSIX 아티팩트 볼륨은 내용 해시로 식별한 변경 불가 원천·정규화 입력·CLI 이벤트·출력 객체를 보관한다. [Compose `depends_on`](https://docs.docker.com/compose/how-tos/startup-order/)만으로 DB 준비를 보장하지 않으므로 `pg_isready` 건강 검사와 `service_healthy` 조건을 사용한다. PostgreSQL 18을 **검증 후 선택한다면** [공식 이미지](https://hub.docker.com/_/postgres)의 데이터 볼륨 위치는 `/var/lib/postgresql`이다. 실제 검사 전에는 버전이나 digest를 정하지 않는다.

`.env.example`에는 비밀값을 넣지 않고 실행 시 [비밀 파일/관리자](https://docs.docker.com/compose/how-tos/use-secrets/)에서 서비스별 최소 권한으로 주입한다. PostgreSQL에는 `POSTGRES_PASSWORD_FILE`을 사용하며 비밀 파일과 제한된 원본 자료는 저장소·빌드 문맥·이미지에서 제외한다. 기반/배포 이미지의 버전과 digest는 실제 빌드·실행을 확인해 고정한다. CLI 작업자에 Docker 소켓을 마운트하지 않는다. 장기 실행 Compose CLI 작업자 정의만으로는 작업마다 별도 비특권 컨테이너·임시 파일시스템·제한된 외부 통신을 입증하지 못하며, 이 격리와 G4 검증은 후속 작업에 남는다. CLI는 권리를 확인한 입력만 받고 제공자 HTTP 접근은 승인된 연결 도구가 맡는다.

## 4. 코드 형태 예시

스냅샷 ID를 지어내지 않고, 근거가 없는 상태를 자료형 계약에 나타낸다.

```python
from typing import Annotated, Literal, Union
from pydantic import BaseModel, ConfigDict, Field

class AvailableMarket(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kind: Literal["available"]
    snapshot_id: str

class UnavailableMarket(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kind: Literal["unavailable"]
    hold_report_id: str

MarketContext = Annotated[
    Union[AvailableMarket, UnavailableMarket], Field(discriminator="kind")
]
```

모듈 사이에서는 단위와 UTC 시각을 명시하고 계산 전에 입력 버전을 고정한다. 이 예시는 형태만 정의한다. 서버가 소유권·권리·당시 판본·관문 증거를 따로 검사한다. 보류 사유와 누락 증거는 `hold_report_id`가 가리키는 보고서에 기록한다. `ForecastRun`의 `snapshot_id` 자리에 `hold_report_id`를 넣지 않는다.

## 5. 시험 방법과 수용 기준

1. **출처 기록/G0:** 합성 자료에는 `synthetic`, 작성자, 생성 방법, SHA-256, 단위, 시각 의미, 권리를 기록한다. 실제 기상청 기록에는 정확한 제품 ID, 관측소, 원 요청, 권리, 제공자 QC 유무, 변환 버전도 연결한다. `SI`의 적산 구간이 불명확하거나 값이 음수·야간에 부적절하거나 필수 자료·권리가 없으면 이유를 명시해 보류한다. `SI` 보유율 측정과 권리 확인 전에는 시범 관측소·기간을 정하지 않는다.
2. **지속 작업/CLI:** 중복 제출은 같은 작업으로 처리한다. 임대 만료·작업자 재시작·취소·429/5xx·스키마 오류·계정 부재·권리 거절에서 감사 기록과 올바른 상태가 남는다. 세 단계 각각에 실제 CLI 버전·모델·추론 강도, 입출력 해시, 출처 참조, JSONL 이벤트, 검사 결과, 사용량, 시도 ID를 기록한다. 재시도에는 새 시도 ID를 만들고 실제 검증 출력이 있을 때만 새 AI decision을 만들며, 게시된 판단과 Run은 바꾸지 않는다.
3. **물리 G1 추적 시험:** 코드 작성 **전에** 방정식·매개변수·제어·초기 상태·적분 계약을 확정한다. 모든 계수의 출처를 연구·실측·명시적 가정 중 하나로 밝힌다. 열·수증기 수지 잔차, 단위, UTC/KST, 구간 일사 변환, 결측, 야간 일사, 설비 용량, 안정적 적분, 고정 입력 재실행을 시험한다. 수치 허용 오차와 QC 기준은 이 문서에서 지어내지 않고, 확정한 모델·출처 근거로 시험 전에 등록한다. 열량 `kWh_th`를 구매 전력·연료·요금으로 표시하지 않는다.
4. **경제·시장 시나리오 G1 추적 시험:** 직접 작성한 날짜별 원장은 첫 합성 사례의 **당일 출하와 검수**만 다룬다. 운송 중이거나 검수 대기 중인 재고는 후속 계약이 필요하다. 첫 G1에서 시장이 `unavailable`이면 경제 입력과 수요·공급·거시 스트레스는 명시적 사용자 가정(`origin=user`, `evidence_level=assumed`)만 쓴다. 후속 단계의 `quoted`/`measured` 기록은 앞서 정한 권리·적용성·원장 검사를 통과한 범위에서만 쓴다. 공통 충격, 계약·재고 제약, 결정 시각·판본·`available_at`·as-of·권리·출처를 검사한다. `H → P → S`, 등급·채널·차감 전 가격·조건부 순송금 단가·변동비의 공동 변화, 반품·폐기·기말 재고, 판매 인정분만의 매출, 생산원가 한 번 반영, 발생일과 현금일, 반올림, 수금/지급·현금 대사, 세 손익분기 목표를 시험한다. 각 목표의 시험 kg 또는 KRW/kg마다 날짜별 시나리오 경로 전체의 재계산과 변수·범위·해 없음을 확인한다. 중요한 비용이 빠지면 0이 아니라 미확인으로 둔다.
5. **API/화면:** OpenAPI 스키마는 잘못된 참조를 거부하고 작업, 출처·시장 보류, Run 시계열·manifest, 조건부 경제 결과, 평가를 제공한다. 키보드 사용자는 시각을 골라 장면·그래프·HTML 표에서 같은 값과 단위를 확인할 수 있다. WebGL이 작동하지 않아도 표·문장 경로를 제공한다. 월별 조건부 금액을 보간해 시간별 실측값처럼 보여 주지 않는다.
6. **전체 경로:** 합성 자료 요청이 지속 작업과 실제 CLI 세 단계를 거쳐 좌표에서 최종 `hold`까지 진행한다. 재현 가능한 열·경제 기록과 일치하는 화면 값을 확인한다. 실제 기상청 경로는 별도로 G0 증거를 통과하거나 근거를 기록하고 보류한다. 별도 증거 없이 시험 결과를 G2/G3/G4로 표시하지 않는다.

## 6. 범위, 기능 목록과 구현 순서

첫 범위에는 작물 생장·수확 예측, 구매 에너지·요금 예측, 미래 마진, 작물 순위, 식물 생장 애니메이션이 없다. 사용자 입력 물량·비용으로 만든 조건부 산술은 예측이 아니다. 이 문서는 온실 계수·센서 허용 오차·경제 정확도 비율·관측소를 가정하지 않는다. 첫 열·수증기 수지는 방정식·계수·제어·수분 유입과 배출·초기 상태·단위·적분 설정·잔차 시험을 CLI 조사로 확정하고 검토하기 전까지 **제안된 계약**이다.

다음 영문 소문자 ID는 [작업 목록](../tasks/todo.md)의 작업 이름이기도 하다.

| 기능 ID | 구현 결과 |
| --- | --- |
| `repo-bootstrap` | **완료:** Python/web 설정·잠금 파일과 웹 검사·시험·빌드 스크립트, `.gitignore`; 오프라인 잠금·설치·import 확인 |
| `compose-runtime` | **완료:** 다섯 파일의 빌드 문맥·이미지 정의, 별도 서비스 역할, DB 준비·영속성 및 비밀 분리의 C0 호스팅 시험 수용 |
| `provenance-g0` | 변경 불가한 출처·권리·품질·관문 기록 계약 |
| `thermal-synthetic-parameters` | 1차 근거의 포화압 법칙과 버전 고정 합성 시설·초기·제어·수치 기준, manifest v2 |
| `thermal-contract` | 버전을 고정한 열·수증기 모델 계약 확정 |
| `fixture-policy` | 직접 작성한 합성 G1 추적 입력과 manifest |
| `durable-jobs` | PostgreSQL 임대·중복 처리·복구·게시 상태 |
| `decision-evidence-store` | CLI 시도별 불변 종료·출력/검사·권리별 감사 아티팩트; 실제 검증 출력에만 AI 결정 ID |
| `g0-authority-store` | 서버가 소유한 출처·권리·검토 정책과 변경 불가 G0 승인 증거 저장소 |
| `cli-worker` | 제한된 실제 CLI 단계·스키마·보류·감사 |
| `market-context` | 결정 당시 시장 자료의 가용/불가 구분과 ForecastRun 분리 |
| `thermal-engine` | 결정적 단일 구역 물리 Run |
| `economic-ledger` | `Decimal` 조건부 원장과 날짜별 현금 |
| `sales-settlement` | 판매별 공제·수금과 미수금/미지급금 대사, 증거가 완전한 조건부 순송금 단가 |
| `market-scenario` | 수요·공급·거시 공동 충격, 시점·권리·재고·계약 제약을 따르는 조건부 날짜별 경로 |
| `economic-break-even` | 전체 날짜별 시나리오 경로를 다시 계산하는 서로 다른 손익분기 목표 세 가지 |
| `api-flow` | 버전 관리된 HTTP 제출·조회 경로 |
| `web-shell` | 좌표·입력·작업·보류 화면 |
| `web-replay` | 동기화된 3D·그래프·표 재생 |
| `end-to-end-g1` | 실제 CLI를 쓰는 합성 자료 계약 추적 시험 수용 |
| `kma-g0` | 권리를 따로 확인하는 실제 ASOS 경로 |
| `market-source-g0` | 실제 승인 시장 제품의 어댑터·정규화·시점/권리/품질 검사와 G0 MarketSnapshot 또는 보류; 첫 합성 G1과 병행 |
| `g2-evidence` | 독립 온실 실측 계획과 증거 |
| `forecast-engine` | G0 시장·G2/현장 근거 뒤 버전 고정 ForecastRun 또는 보류; 엔진만으로 미래 예측 주장 불가 |
| `g3a-evidence` | 독립 작물·경제 미래 검증 |
| `crop-ranking` | 같은 결정·시설·면적·달력·목표와 공통 충격의 후보 비교 또는 보류; G3b 전 순위 비공개 |
| `g3b-evidence` | 후보 간 대응 비교와 순위 검증 |
| `service-economics` | 농장 경제와 분리한 실제 요청별 서비스 원가·매출·용량·재원 대사; G4 선행 |
| `g4-operations` | 운영 계정·격리·권리·실측 서비스 수지·배포 증거 |

구현 순서와 외부 증거 의존성은 [구현 순서](../tasks/plan.md)에 있다. 코드 작업 체크는 해당 작업의 수용 증거만 뜻하며 다른 주장 관문의 통과를 뜻하지 않는다.
