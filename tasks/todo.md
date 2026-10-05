# 첫 구현 작업 목록

## 작물 생산·성장 3D 구현 (2026-10-04 현재 우선순위)

순서·병행 경로·일정의 가정은 [현재 계획](plan.md#작물-생산과-성장-3d-우선순위-2026-10-04),
관문은 [제품 명세](../docs/PROJECT_SPEC.md)를 따른다. 아래 후속 파일은 **예정 파일**이며
큰 묶음은 착수 전에 3~5파일의 작은 계약으로 나눈다. 아직 없는 모듈의 수용을 체크하지 않는다.

- [x] **`crop-model-baseline`** — 조사/설계 단계.
  산출물: [모델·품종·검증 조사](../research/crop-tomato-model-baseline-20261004.md),
  [원문/계수/권리 등록부](../research/crop-tomato-source-register-20261004.json),
  [첫 계산 계약](../contracts/crop-growth-research-v1.md).
  수용: Vanthoor/축약 TOMGRO/TOMSIM의 구현·권리·검증 비교, Axiany/Maxifort 한 작기
  개발 경계와 일반 계수의 적용 한계, 단위 정정·raw hash·actual CLI model/effort,
  국내 독립 자료의 필수 채널·권리·분할과 hold. 네 요청 문서의 의존성/수용 기준·링크 대조를 통과했다([수용 기록](../research/crop-priority-and-runtime-freeze-20261004.md#이번-재정렬의-문서조사-수용)).
- [x] **`crop-growth-rates`** — 로컬 순수 유량 계산 수용, 선행: `crop-model-baseline`와 필요한 식/계수 검토.
  구현 파일(5): `backend/app/crop_growth_rates.py`, `backend/tests/test_crop_growth_rates.py`,
  `fixtures/crop-growth-reference-parameters-v1.json`, `fixtures/crop-growth-reference-cases-v1.json`,
  `LICENSES/GreenLight-BSD-3-Clause-Clear.txt`.
  수용: 고정 식·단위·출처/권리의 광 동화·분배·호흡·기관 변화율, 야간/잎 면적 0,
  독립 고정 참조값·탄소 항등식·부적합 입력 거부와 재현. 원식의 작은 LAI/Gamma 영역과
  고갈 저장소 거부를 기록하고 가능한 조건에서 잎 0 연속성을 시험한다.
  확인: `cd backend` 뒤 `env PYTHONPATH=. nice -n 10 .venv/bin/pytest -q tests/test_crop_growth_rates.py`.
  [실제 수용](../research/crop-growth-rates-implementation.md): 86개/0.12초·60자리 Decimal
  참조 4사례/60수치·원문 52개 항목 대조. 전체 hosted/이미지·적분·G1/G2/G3/G4는 후속.
  사용자 산출물: 유량 표·검사 보고서. 국내 자료·G2·시장·전체 Compose가 착수를 막지 않는다.
- [x] **`crop-input-audit`** — 파일/채널 감사 수용, 실제 입력 채택 보류; 모델 개발과 병행.
  핵심 파일: `research/crop-forcing-audit.md`, `research/crop-forcing-register.json`,
  `contracts/crop-forcing-v1.md`.
  수용: 공개 archive 내 Reference303의 실제 채널/단위·UTC/DST·96m²/76.8m² 면적 기준·
  결측/QC·초기조건·밀도/적심/적엽/수확 사건을 대사하고 PAR/수관/CO₂ 누락은 보류.
  고정 값/변환의 raw hash와 권리를 기록한다. [실제 수용](../research/crop-forcing-audit.md):
  Reference 7 CSV/Weather 1 CSV·ReadMe/Economics 2 PDF와 파일/채널·결측/형식·시간/면적 대사.
  `research/crop-forcing-audit.py`를 추가해 불변 8 CSV의 hash/줄 수·byte-identical 재검사를 확인했다.
  시간대/62.5·76.8·96m²의 Reference 대응·수관/초기기관/사건·음수 CO₂/수확 날짜/품질 header는 hold.
  실제 forcing/Run 0개. 실제 replay 입력 채택은 기존 G0 검사를 별도로 통과해야 한다.
- [x] **`crop-photosynthesis-domain`** — 원식 지원 영역의 로컬 연구/계산 수용.
  구현 파일(3): `research/crop-photosynthesis-domain.md`, `contracts/crop-photosynthesis-domain-v1.md`,
  `backend/tests/test_crop_photosynthesis_domain.py`.
  수용: LAI→0의 온도별 특이점/부호·원식과 가능한 대안의 근거·적용 범위/단위/검증 가능성,
  품종 초기에 사용할 영역 또는 명시적 hold를 기록. 식을 바꾸면 새 모델 판본/독립 재현 필요.
  [수용 결과](../research/crop-photosynthesis-domain.md#실제-수용과-다음-구현): 새 영역 32개와 기존
  유량 86개를 합쳐 118개/0.18초. 독립 Decimal 대수·원식/초기조건 반례·A=0 경계 확인.
  원식/프로필 유지, 임의 clip/CO₂ 보상점 기본값 없음. 실제 품종 초기조건 QC는 hold.
- [x] **`crop-rate-image-inputs`** — 필요한 프로필/고지의 실제 이미지 수용.
  필요 근거: 현재 앱 이미지는 새 프로필/제3자 라이선스를 build context에서 제외한다.
  파일(3): `.dockerignore`, `backend/Dockerfile`, `scripts/check-application-images.py`.
  명시적 프로필 1개·라이선스 1개만 포함하고 실제 이미지에서 kernel import/프로필 해시·
  라이선스 해시를 확인한다. 관련 없는 fixture/라이선스 probe 제외를 기존 hosted 검사로 확인한다.
  [실제 수용](../research/crop-rate-image-inputs-implementation.md): `207e20e`의 hosted Docker
  build/context·읽기 전용 이미지 probe·프로필/고지 해시와 13개 제외 probe·모든 정리 통과.
  새 전체 backend CI·제품 CLI/G1/G4는 별도 미수용이다.
- [x] **`crop-growth-integration`** — 선언된 입력/사건의 로컬 연구 적분 수용.
  구현 파일(5): `backend/app/crop_growth_integration.py`, `backend/tests/test_crop_growth_integration.py`,
  `contracts/crop-growth-integration-v1.md`, `research/crop-integration-reference.py`,
  `fixtures/crop-integration-reference-v1.json`.
  수용: UTC 사건/초기조건·솔버/간격 고정, 기관/버퍼·LAI·온도 합·누적 호흡/제거,
  수지 잔차·양수성·수렴·동일 입력 재실행; 실패를 clipping으로 숨기지 않는다.
  [수용 증거](../research/crop-growth-integration-implementation.md): 적분 28개와 기존 118개,
  합계 146개/0.53초·60자리 독립 원식 2사례/11시점/165수치, 간격 반감 오차 감소
  15.476/15.843·탄소 수지/사건/고갈·정확한 온도 합과 해시 재실행을 통과했다.
  새 전체 hosted/DB·불변 저장·3D·제품 관문은 후속. 참조 작기 재현은 `crop-input-audit` 뒤;
  사용자 산출물은 상태 시계열/잔차 표이며 생과 수확/국내 예측이 아니다.
- [x] **`crop-result-storage`** — 로컬 합성 연구 결과의 불변 저장 수용.
  핵심 파일(3): `backend/app/crop_result_store.py`, `backend/tests/test_crop_result_store.py`,
  `contracts/crop-result-v1.md`. 새 결과 1표의 실제 SCRAM·권한 검사에 필요한 기본 꺼짐
  옵션과 기존 `runtime_roles.py`/로그인·owner 시험 fixture만 추가 연결한다.
  명시적 합성 연구 입력과 현재 farm/program 권리 제공자를 요구한다.
  수용: 연구 결과 ID·forcing/profile/model/solver·manifest/해시·claim scope/hold의 불변 저장,
  동일 판본/재시작 조회, 변조·다른 농장/테넌트 혼합 거부. 현재 accepted Run으로 자동 승격 없음.
  [실제 수용](../research/crop-result-storage-implementation.md): 저장 8개/기존 회귀 18개/
  생장 146개, 합계 172개/434.49초·0 skipped. 실제 SCRAM·별도 프로세스 동일 bytes,
  재시도/pending/해제·불변/외래키·실제 변조/현재 권리 철회/rollback·정리를 통과했다.
  [저장 packet](../research/artifacts/crop-result-storage-reference-20261004.json)은 합성 시험이다.
  실제 참조 입력의 감사/권리 연결·3D·전체 hosted/관문은 별도 미수용이다.
  조회 API의 로컬 수용은 아래 별도 작업에 기록한다.
- [x] **`api-crop-replay`** — 로컬 합성 연구 조회 API 수용. 선행: `crop-result-storage`.
  핵심 파일(3): `backend/app/api_crop_replay.py`, `backend/tests/test_api_crop_replay.py`,
  `contracts/api-crop-replay-v1.md`.
  기존 `api.py`/`api_runtime.py`의 선택 조립과 고정 OpenAPI/권한 회귀도 연결했다.
  수용: 인증/현재 권리·정확한 연구 결과와 농장 연결·단위/UTC·보류 범위의 조회;
  다른 결과/모델/입력 혼합과 철회·변조 거부. 확인: OpenAPI/실제 HTTPS/SCRAM 집중 시험.
  [실제 수용](../research/api-crop-replay-implementation.md): 316개/194.11초·GET 재적분 없음,
  HTTPS 10개 전체 응답 최대 5.580219초/기존 30초·같은 6시점·현재 권리/DB 변조·정리.
  [실제 JSON 응답](../research/artifacts/api-crop-replay-reference-20261004.json)은 시험 DB 자료다.
  3D/실제 작기·전체 hosted/제품 CLI·G0–G4는 이 수용 범위 밖이다.
- [x] **`web-crop-replay`** — 로컬 합성 연구 재생 수용, 선행: `api-crop-replay`.
  핵심 파일: `web/src/cropReplay.ts`, `web/src/cropReplay.test.ts`,
  `web/e2e/crop-replay.spec.ts`, `contracts/web-crop-replay-v1.md`.
  수용: 같은 결과 ID/시점의 잎 면적·기관 상태를 표·그래프·3D에 연결;
  모식 형태·연구/합성·hold와 보간 표시, 미계산 키/잎수/착과수/숙기 애니메이션 없음.
  현재 거부·재연결·키보드·WebGL 대체와 저장 수치/장면 대사를 실제 브라우저로 확인.
  실제 화면은 별도 `CropReplay`/`CropScene`/`CropChart`와 `cropGeometry` 모듈에 분리했다.
  [수용](../research/web-crop-replay-implementation.md): 웹 단위 209개(작물 49개)·집중 Chromium
  10개·실제 SCRAM→HTTPS→장면 대사 1개, typecheck/build·단위/UTC·권리/계정·정리 통과.
  사용자 산출물: [계산 기반 성장 연구 3D](../research/artifacts/crop-replay-final-desktop.png)와
  [로컬 실행법](../web/README.md#지금-3d를-직접-보기). 6시점/5분 합성 범위.
  실제 작기 입력 QC/국내 검증·과실/생과 생산량·전체 hosted CI/제품 관문은 별도 미수용.
- [x] **`crop-web-image-inputs`** — 실제 앱 이미지 실패 `0f3ce74`/37209918683의 최소 포장 보완.
  핵심 필요: `web-crop-replay`의 fixture import/디자인 자산이 Docker COPY/허용 목록에서 빠짐.
  [진단·실제 이미지 수용](../research/crop-web-image-inputs-implementation.md): 기존 e2e 경로로 같은
  fixture 이동/import, 자산 9개만 허용·17개 제외 probe/해시·production 데모 비포함 검사.
  로컬 COPY 모사 RED→GREEN/typecheck/build·이동 후 웹 단위 209개는 통과했다.
  `98d382a`의 실제 미선언 SVG 제외 반례를 폴더 자식 제외 한 줄로 수정했다.
  `d76410f`/37213151159의 실제 context 17 probe·image/TLS·UID/읽기 전용/전체 Compose·정리를 통과했다.
- [x] **`crop-fruit-model-spec`** — 원식/계수·권리·보류와 작은 개발 계약 수용.
  파일(3): `research/crop-fruit-cohorts-baseline.md`, `research/crop-fruit-source-register.json`,
  `contracts/crop-fruit-cohorts-v1.md`.
  수용: 원 과실 발달 구획/개수·질량·호흡/수확 경계식·필수 계수/초기조건/관리 사건의
  단위/권리/hash·참조/품종 적용성·총 과실 저장소 결합, 독립 수치/보존/사건 검증 계획.
  계수·생과 환산 미확인은 hold. 사용자 산출물은 근거표/구획 계약이며 농장 생산 예측이 아니다.
  [수용](../research/crop-fruit-cohorts-baseline.md): 원 PDF hash/6페이지 식·표와 코드 부재 대사,
  21개 값/상수·단위, 9.36/9.37 보존 반례·W1/빈 sink/초기·gate hold와 독립 검증 계획.
  새 계산/Run 0개. 원 불일치 해결은 `crop-fruit-allocation-policy`에 따로 둔다.
- [x] **`crop-fruit-transport`** — 고립된 순간 이동의 로컬 소프트웨어 수용; 국내/G2·전체 배분 선행 아님.
  구현 파일(4): `backend/app/crop_fruit_transport.py`, `backend/tests/test_crop_fruit_transport.py`,
  `fixtures/crop-fruit-transport-reference-parameters-v1.json`,
  `fixtures/crop-fruit-transport-reference-cases-v1.json`.
  수용: 원 50구획·온도 계수/단위·piecewise h=1의 순간 dN/dC·마지막 연구 유출·hash,
  독립 Decimal 17/20/23°C·0/첫/다중 구획, 개수·탄소 telescoping 수지·불변/거부 검증.
  배분/착과/호흡·적분/생과 kg/실제 과실 3D는 다음 범위. 사용자 산출물은 유량표/검사 보고서.
  [수용](../research/crop-fruit-transport-implementation.md): 새 92개/기존 포함 238개·0.71초,
  15사례·독립 3,090수치·byte-identical 참조 재생성. 원문 3개 계수/단위·hash 대사.
  독립 생성 코드를 추가했고 큰 유량 차감 3개 반례를 동등식으로 수정·미분 underflow도 hold.
- [x] **`crop-fruit-transport-image-inputs`** — 필수 transport 프로필의 실제 hosted 이미지 수용.
  예정 변경(3): `.dockerignore`, `scripts/check-application-images.py`,
  `research/crop-fruit-transport-image-inputs-implementation.md`.
  수용: 프로필 한 파일만 허용·실제 context hash/새 cases 제외와 읽기 전용 image에서
  ReferenceFruitTransportParameters 로딩; 기존 UID/TLS/전체 정리.
  [실제 수용](../research/crop-fruit-transport-image-inputs-implementation.md): `78b5d17`의 context 4회/
  17개 제외 probe·pinned profile, 읽기 전용 loader 1회·TLS 2경우와 image/3 Compose 정리 성공.
- [x] **`crop-fruit-allocation-policy`** — 명시적 착과/진입 질량의 개발 정책 수용; 자동 착과/실제 품종 미채택.
  수용: 원 9.36/9.37 보존 불일치·W1 Gompertz 경계/초기 seed·빈/고갈 sink·gate 판본,
  원/수정식 근거·별도 모델/프로필·독립 참조와 sum(A_j)=F/개수 보존·사건 정책.
  원식의 분모/계수를 조용히 수정하지 않는다. 실제 품종 입력/관문은 별도.
  [수용](../research/crop-fruit-allocation-policy.md): 원/공개 구현/문서/권리의 5개 출처 대사,
  원/epsilon 분모 각각 4개 반례. 명시적 S/W1·tail 분모의 별도 정책/제약·hold,
  독립 6개 정상/4개 hold·600개 탄소/개수 유입과 byte-identical 재실행. 제품 계산은 후속.
- [x] **`crop-fruit-allocation-rates`** — 순간 유입의 로컬 소프트웨어 수용; 실제 자동 착과/적분은 후속.
  구현 파일(2): `backend/app/crop_fruit_allocation.py`, `backend/tests/test_crop_fruit_allocation.py`.
  수용: 독립 600개 유입/4개 hold·두 수지/단위, 닫힌 입력/형태·유한성/영역/
  underflow/overflow·ULP 예산·입력 불변/hash/판본·같은 반복. 생물 계수/자동 착과/W1은 없음.
  [수용](../research/crop-fruit-allocation-implementation.md): 새 77개/기존 포함 315개·0.70초,
  독립 600개 유입/4개 hold·두 수지/최대 상대 오차 5.5511e−17·같은 입력 hash/불변.
- [ ] **`crop-cycle-capacity`** — 입력 감사/현재 적분 수용 뒤; 실제 참조 작기 재현의 필수 선행.
  필요 근거: 실제47,809시점/47,808 interval; 기관 단독v1은20,000 배열/100만 step,
  현재 기관·과실/startup은128 forcing/128 event·512 output·10,000 step·1일;
  166일/10초의 산술 1,434,240 step. 문헌 과실 모델 개발/국내 확보와 병행한다.
  작은 실행 계약부터 분해: bounded forcing 처리·연속 상태/누적 수지/사건·불변 manifest/저장,
  계산 해상도와 출력 시간/페이지의 분리·30초 응답/WSL 자원·재시작/동일 재현/실제 작기 부하.
  수용 전 한도 증대/임의 forcing 축약으로 whole-cycle 완료를 주장하지 않는다.
  - [x] **`crop-cycle-execution-contract`** — 실행 명세/원 격자 대사의 로컬 수용; 선행: 수용된 startup 적분과 입력 감사의
    source 형태/한도 관측. 국내 자료/G2는 개발 선행이 아니다. 실제 현재 코드의 전역 걸음 경계,
    상태/16누적·forcing/event/output cursor·관리 사건·실패/hold·불변 checkpoint/hash/현재 권리를
    대조한다. 분할/재시작으로 새 RK4 경계를 만들지 않는 정책과 출력 분리·WSL 부하 계획을
    계약하고, 순수 연속 실행 → 저장/페이지 → 실제 작기 부하의 후속 작업/수용 기준을 분해한다.
    수용 증거: 코드/원형 한도 표·독립 걸음/사건 경계 대사·해소/보류 목록·검토 기록.
    이 계약 수용을 실제 작기 실행이나 품종 생산 정확도로 표시하지 않는다.
    [착수 코드 감사](../research/crop-cycle-execution-inspection-20261005.md)에서 두 판본의 한도와
    출력 시각의 solver 경계 결합·원 seed/누적량·정확한 온도 clock·사건 처리 순서를 확인했다.
    [명세 수용](../research/crop-cycle-execution-contract.md): 원 solver6프로그램/630걸음·30분할 grouping,
    23벡터/2,783개 float64 round-trip·추가 경계/온도 prefix 반례·파일/CLI 검토로10월5일 KST 로컬 완료.
    이는 원 격자/표현과 실행 계약의 수용이며 새 모델의 실제 재시작은 다음 구현의 미수용 범위다.
  - [x] **`crop-cycle-continuation`** — 짧은 실제 RHS 중단/재시작의 로컬 수용; 선행: 위 실행 계약의 수용.
    예상3파일: `backend/app/crop_cycle_continuation.py`, `backend/tests/test_crop_cycle_continuation.py`,
    `contracts/crop-cycle-continuation-v1.md`. 우선 현재 짧은 입력/고정 실제 RHS로 새 provider를 검증한다.
    수용: 원121벡터/seed·16누적/clock·global counters·phase/cursor의 보호와 전역 격자·사건/output/hold 보존,
    기존6프로그램의 원값/단위/수지·별도 Python/JSON 복원·경계/t0/event+output/hold·변조/예산·입력 불변/hash.
    원 legacy 파일/모델/hash를 보존하고 새 code/manifest 판본을 고정한다. pytest 집중/회귀와 실제 별도
    프로세스 복원 증거 뒤 체크한다. 긴 입력/전체 작기나 실제 crop/prediction을 이 짧은 수용으로 대체하지 않는다.
    [실제 수용](../research/crop-cycle-continuation-implementation.md): 새101개/기존56개·총157개/70.91초,
    6프로그램×5예산30실제 분할/JSON 복원, 별도 Python6개/726float64·원 상태/16누적/clock·사건/hold와
    UTF-8/root 회귀 수정·정리. 1일/128 forcing·512 output·10,000 step을 그대로 유지한다.
  - [x] **`crop-cycle-input-stream`** — 불변 분할 입력/원 clock·grid reader의 로컬 수용; 선행: continuation 수용; bounded root/forcing·계산 anchor/event와
    hash/index/cursor·정확한 clock의 분할 provider/검증을3–5파일 계약으로 구체화한다. 실제 source 형태 규모의
    자작 합성 입력·연속성/원량·권리/QC 거부·큰 입력·메모리·재시작을 확인한다. 실제 archive 채택은 별도다.
    [실제 수용](../research/crop-cycle-input-stream-implementation.md):64개/3.63초·48,000자작 합성 구간/
    48,003경계·독립 clock/grid·별도 Python 복원·전체79.848초/30.23MiB·113,276,558bytes/tempfile·FD 정리.
    예정1,440,002RK4걸음은 계획 산술이며 실제 RHS는 미실행이다. 실제 archive/농장/품종 입력은 미채택이다.
  - [x] **`crop-cycle-stream-execution`** — 실제 긴 연구 실행의 로컬 수용; 선행: input stream/continuation 수용. bounded reader와 실제 RHS·전역
    grid/seed/clock/counters·phase를 새 긴 실행 판본에서 연결한다. 실제 긴 합성 프로그램·분할/별도 Python
    복원·수지/사건/hold·입력 불변/전역 budget·WSL 자원/정리를 검증한다. 현재 짧은 v1 한도/hash는 보존한다.
    reader 수용을 이 실행 수용으로 표시하지 않는다. 파일/전역 budget·기간/날짜는 source provider 실적 뒤 고정한다.
    예상3파일: `backend/app/crop_cycle_stream_execution.py`, `backend/tests/test_crop_cycle_stream_execution.py`,
    `contracts/crop-cycle-stream-execution-v1.md`. 원6프로그램과 실제1일/10,000step 초과 합성 프로그램의
    RHS/전역 수지·JSON/별도 Python 복원·hold/확인 과거/원 grid를 검증한다. 큰 clock-only 입력을 crop 실행으로 사용하지 않는다.
    [실제 수용](../research/crop-cycle-stream-execution-implementation.md): 새88개/기존56개·총144개/65.41초,
    6프로그램×3예산·canonical 사건 정규화 회귀,25시간/300구간/11,400실제 걸음·별도 Python7개/
    847float64·원 상태/누적/clock/수지/사건 hash·25시간 뒤 hold,263.879초/parent45.44MiB·정리.
    실제166일/품종/원 입력 채택·저장/3D/G0–G4 수용으로 표시하지 않는다.
  - [ ] **`crop-cycle-result-pages`** — 선행: 실제 stream 실행 수용. 불변 파일/reader → farm/current rights
    custody/API → 같은 UTC 3D를 각각3–5파일 작업으로 먼저 분해한다. 원 출력/sequence·chain/변조/atomic·
    재시작/GET 재적분 없음·실제 SCRAM/TLS/browser·페이지30초/정리 뒤 체크한다.
    아래 자식 작업의 증거가 모두 있을 때만 부모를 체크한다.
    - [x] **`crop-cycle-result-artifact`** — 불변 파일/reader의 로컬 수용; 선행: stream execution 수용. 구현3파일:
      `backend/app/crop_cycle_artifact.py`, `backend/tests/test_crop_cycle_artifact.py`,
      `contracts/crop-cycle-artifact-v1.md`. 새 cycle 판본의 bounded 불변 sample/event/checkpoint 분할과
      index/root를 만든다. 원 input/context·code/profile/grid/seed·전역 counter/prefix/parent를 연결하고
      completed/hold/확인 과거를 보존한다. 원량을 바꾸거나 GET/read에서 RHS를 실행하지 않는다.
      수용: 원6프로그램과1일/10,000step 초과 자작 합성 결과의 저장/별도 Python 읽기·동일 UTC/원값,
      새2MiB 이하 페이지의 유한 byte/record/전체 budget, hash/index/순서/중복/혼합 root 변조,
      pending event/중간 commit·실패/부분 파일·재시작·atomic 게시/FD/tempfile 정리.
      byte/record 상세 상한은 구현 계약과 실제 결과 크기로 고정한다. HMAC/current rights/DB/HTTP/3D는 후속이다.
      [실제 수용](../research/crop-cycle-artifact-implementation.md): 58개 고유 분할(57/55.36초+1/0.20초),
      25시간/11,400실제 걸음·93commit/27sample/5event·755,868bytes/127파일,
      별도 Python7개/847float64·실제 강제 종료2개/게시 전후 복구·읽기0.388759초/RHS0회·정리.
      기존40개 hash 보존/변조·hold·budget 거부를 확인했다. 10월5일 KST 로컬 완료; DB/API/3D와 hosted는 별도다.
    - [x] **`crop-cycle-storage-schema`** — schema만 로컬 수용; 선행: artifact 수용. 구현3파일:
      `backend/app/crop_cycle_result_schema.py`, `backend/tests/test_crop_cycle_result_schema.py`,
      `contracts/crop-cycle-storage-v1.md`. private POSIX 결과를 참조하는 새 불변 metadata/root 표를 만든다.
      수용: 실제 SCRAM의 등록 외래키·판본/범위/bytes/hash·정수 step/record/commit/storage 한도·
      중복/잘못된 root·metadata 혼합 거부, owner UPDATE/DELETE 거부·기본 runtime 네 role의 새 권한0,
      명시 migration/기존 row 보존·DB/password 정리. 경로/원본을 공개하지 않으며 파일 실재/HMAC/current rights는 custody다.
      [실제 수용](../research/crop-cycle-storage-schema-implementation.md): 74개 고유 분할(72/24.17초+2/1.10초)·
      실제 SCRAM/기본 네 role 거부·28종 column/17종 rehashed metadata·2종 FK/9종 malformed·정상 JSON128KiB/초과·
      owner 불변/중복/새 revision·부분 설치 rollback/기존 v3 row·DB/role/schema/password 정리0잔여·원42개 hash 보존.
      10월5일 KST 로컬 완료; 명시 flag/grant·실제 farm/file/current rights/HMAC와 hosted는 별도다.
    - [x] **`crop-cycle-storage-roles`** — 로컬 수용5파일(runtime_roles/operator_config와 각 시험·login_database); 선행: schema 수용.
      기본 false의 새 명시 flag·선택 grant를 연결한다. 수용: 실제 SCRAM의 authority SELECT/INSERT만 허용,
      다른 role/UPDATE/DELETE/TRUNCATE·과다 grant/잘못된 타입 거부, 누락/false의 기존 grant/config 호환·정리.
      표만으로 runtime 저장·전체 부모를 수용하지 않는다. 새 서비스/queue는 선행이 아니다.
      [실제 수용](../research/crop-cycle-storage-roles-implementation.md): 새21개/고유236개 분할(234통과/시험 routine 오기2실패·80.98초,
      오기 두 곳만 수정 뒤2통과·1.16초), 실제 네 SCRAM/58 직접 SQL 거부·선택 INSERT/SELECT·
      일곱 drift·기본 false/config·기존 v3 bytes·정리0잔여/원44개 hash 보존. 10월5일 로컬 완료; hosted/실제 자료는 별도다.
    - [ ] **`crop-cycle-result-storage`** — 부모, 선행 artifact/schema/명시 role 로컬 수용.
      아래 세 자식을 순서대로 검증한 뒤 현재 farm/input/실제 서버 계산·HMAC/게시 custody를 수용한다.
      기존 inline segments/20MiB 구조와 긴 root의 차이, SHA/ledger의 계산 인증 부족을 근거로 분해했다.
      - [x] **`crop-cycle-farm-binding`** — 3파일 module/test/[계약](../contracts/crop-cycle-farm-binding-v1.md).
        실제 SCRAM 등록 farm/crop/period/floor/source의 현재 권리와 preflight root 전용 선언을 결합한다.
        수용: closed canonical 요청·동일 root/프로필·현재 권리/availability/occupancy·중간 철회,
        별도 Python 동일 binding·파일/FD/DB/비밀 정리와 RHS/row/Run0개.
        [고유54개 분할 검증/수정·영수증](../research/crop-cycle-farm-binding-implementation.md)과
        원44개 hash 보존으로10월5일 로컬 수용했다. 부모 저장/다음 custody는 미완료다.
      - [x] **`crop-cycle-server-custody`** — 선행 farm binding 수용;5 core파일의 실제 writer/서명된 progress.
        [계약/수용 조건](../contracts/crop-cycle-server-custody-v1.md)의 닫힌 schema/budget을 고정했다.
        서버의 private root만 해석하고 frozen RHS로 계산하며 각 bounded advance의 현재 권리,
        intent/farm/input/header/code/HEAD·checkpoint를 domain HMAC에 묶는다.
        수용:6프로그램/긴 실제 RHS·같은 canonical 원량/UTC, 별도 Python·강제 종료/재시작,
        서명/HEAD 교체·부적절한 외부/혼합 결과·권리 철회 거부·writer/FD/temp 정리.
        [고유46개 분할/25시간 참조와 영수증](../research/crop-cycle-server-custody-implementation.md):
        순수41개/실제 SCRAM5개·실제 반례4개/reader FD 반례 수정·강제 종료4개·별도 Python121float64/
        같은27시점/5사건·서명 저장829,769bytes·정리/원46개 hash로10월5일 로컬 수용했다.
        단일46 GREEN/실제 품종 수용이 아니며 긴 참조는 마지막 invalid reader 정리 수정 전 판본이다.
      - [ ] **`crop-cycle-db-custody`** — 선행 server custody 수용;3–5파일의 metadata/HMAC/atomic 게시.
        [구현 전 닫힌 참조/게시·수용 계약](../contracts/crop-cycle-db-custody-v1.md)을 따른다.
        실제 SCRAM의 같은 farm/root·서버 실행 영수증·closed/code/header/고지·HMAC를 대사한다.
        수용: commit 전후 farm/source/input 권리 철회·교차 tenant/farm/root·혼합/부분 게시 거부,
        immutable retry/conflict·별도 프로세스 재적분 없는 읽기/복구·정리. 잠정2–3시간.
      남은 DB는 폐쇄 참조/HMAC1시간+실제 게시/철회/재시작·정리1–2시간의
      2–3집중시간/10월5–7일 KST 잠정이며 하루4시간/CI·실제 자료 대기는 별도다.
      필요해진 lease/cancel은 기존 worker 계약에 대조하며 새 queue/service를 먼저 만들지 않는다.
    - [ ] **`api-crop-cycle-pages`** — 선행: custody 저장 수용. 같은 저장 ID의 순차 sample/event 페이지를
      3–5파일로 제공한다. 수용: 실제 Bearer/TLS/SCRAM·current rights·같은 UTC/원량/index·
      30초/2MiB/유한 page budget·취소/중복·과거만 있는 hold/빈 hold·GET RHS0회·정리.
    - [ ] **`web-crop-cycle-pages`** — 선행: cycle API 수용. 새 판본 decoder/순차 페이지와 선택 UTC를
      3–5파일로 연결한다. 수용: 기록된 실제 TLS 응답의 원량/순서·혼합 ID/판본/hash·오래된 요청/중복/
      부분/권리 철회·hold 거부/보존, focused unit/typecheck/build. 기존 short decoder는 보존한다.
    - [ ] **`web-crop-cycle-replay`** — 선행: cycle client 수용. 같은 저장 ID/UTC의 상태·누적량·수지와
      성장 연구 3D를3–5파일로 연결한다. 수용: 실제 PG→TLS→WebGL·원 표/mesh·부분 페이지/hold,
      타임라인 변경·권리 철회·GET 재적분0회/저사양·반응형·키보드/정리. 실제 품종의 키/크기/
      수확·임의 애니메이션이나 새 G0–G4 통과로 표시하지 않는다.
  - [ ] **`crop-cycle-burden`** — 선행: 위 세 구현; 실제 RHS의 긴 합성 forcing/source 형태·부하/재현·중단/복원,
    원 수지/사건·불변 저장/조회·WSL 자원/정리를 검증한다. 실제 작업 분해/측정 뒤 global budget/날짜를 고정한다.
    원47,809시점/166일은 입력 형태이며 실제 품종/UTC/QC/초기/관리 채택 없이 crop 작기 수용으로 표시하지 않는다.
- [x] **`crop-fruit-cohort-rates`** — 고정 문헌 수요·이동/배분/유지 호흡의 로컬 순간 결합.
  [v2 계약](../contracts/crop-fruit-cohorts-v2.md)·제품 2파일/고정 프로필·독립 참조/생성 코드.
  [수용](../research/crop-fruit-cohort-rates-implementation.md): 새 86개/기존 포함 401개·0.89초,
  독립 24사례/8,592수치·세 수지·호흡 한 번·불변/hash·형태/범위/numeric hold.
  시간 적분/사건/전체 작기/자동 착과와 실제 수확·3D는 수용하지 않았다.
- [x] **`crop-fruit-cohort-image-inputs`** — 새 cohort 프로필의 실제 hosted 수용.
  [.dockerignore/script/보고서](../research/crop-fruit-cohort-image-inputs-implementation.md) 3파일.
  정확한 profile 1개 허용·실제 context hash/새 cases 제외·읽기 전용 pinned loader·
  UID/TLS/정리를 `784335d`/37224223039에서 실제 확인했다.
  context 4회/17 probe·pinned hash, loader 1회·TLS 2경우·image/3 Compose 정리와 49개 event를 대사했다.
- [x] **`crop-plant-cohort-rates`** — 전체 기관/과실 순간 수지의 로컬 수용; 적분 부모의 첫 작은 단계.
  [계약](../contracts/crop-plant-cohort-rates-v1.md)·제품 2파일·독립 생성기/참조.
  [실제 수용](../research/crop-plant-cohort-rates-implementation.md): 새 43개/기존 포함 444개·0.99초,
  독립 6사례/684수치·source/profile 호환·총 fruit 파생/기존 유지 호흡 교체·성장 단일 차감,
  전체 탄소/개수 수지·입력 불변/단위/형태/범위·numeric/empty/entry hold·재현/hash.
- [x] **`crop-fruit-cohort-integration`** — 짧은 연구 적분/관리 사건의 로컬 소프트웨어 수용.
  [고정 입력/수용 계약](../contracts/crop-plant-cohort-integration-v1.md)의 최대 24시간/128구간·
  512출력/10,000step·명시 RGR/S/W1·초기/같은 비율 N/C 관리 제거·RK4/누적 수지/manifest를 구현한다.
  독립 일정 forcing/해석해·간격 수렴, 동시 N/C 제거·누적 terminal/호흡·같은 재현,
  [수용](../research/crop-plant-cohort-integration-implementation.md): 새 44개/기존 포함 488개·6.52초,
  독립 2사례/11시점/1,309수치·개수 해석해 250개·수렴 15.5733/15.9740배,
  시간/자원/영역/실패·변경되는 caller solver 사본·재현/hash와 두 수지/사건을 통과했다.
  합성 24시간/512출력/8,687step도 57.85초·42,124 KiB peak RSS·3,639,251 bytes로 확인했다.
  사용자 산출물은 단위 있는 기관/구획 시계열·두 수지/사건 journal이다.
  전체 작기 처리/품종/초기 hold와 새 저장 판본 뒤 3D는 후속이다.
- [x] **`crop-coupled-artifact`** — 새 저장의 첫 자식; 계산 입력/결과·프로필의 불변 bytes.
  [계약](../contracts/crop-coupled-artifact-v1.md)·제품/시험 각 한 파일.
  [수용](../research/crop-coupled-artifact-implementation.md): 새 42개/기존 488개·530개 집중,
  두 참조 사례·별도 Python·재적분 없는 읽기·hold/소수 초 trial·판본/단위/수지/사건 거부.
  24시간/512출력/8,687step을 실제 재계산해 앞선 결과와 동일함을 확인했다.
  3,683,992 bytes·계산/검사 59.1135초·읽기/검사 0.3055초·85,224 KiB RSS다.
  파일 hash는 권리/승인이 아니다. farm/DB/SCRAM·API/3D는 아직 수용하지 않았다.
- [x] **`crop-coupled-result-storage`** — 수용된 artifact의 farm 결합 로컬 SCRAM 저장.
  [고정할 다음 계약](../contracts/crop-result-v2.md): 2 MiB 요청/20 MiB packet·서버 계산은 HTTP 밖,
  새 표 한 개/명시 기본 false flag·현재 farm/crop/batch/source/program 권리·HMAC custody.
  먼저 새 결과 v2의 model/profile/policy/code/solver·forcing/RGR/S/W1/관리·수지/hold와
  최대 bytes/조회 페이지·현재 farm/program 권리의 계약을 정의한다.
  계산은 HTTP 밖에서 완료·검증하고 불변 저장한다. 기존 v1 bytes/accepted Run을 변경하지 않는다.
  현재 v1 테이블은 schema/result-id/scope와 단일 profile에 고정돼 새 artifact를 저장하지 못한다.
  이 근거로만 새 테이블/명시적 기본 false role flag를 추가하며 일반 운영 조립을 재개하지 않는다.
  수용: 실제 SCRAM·같은 저장 bytes/재시작, 입력/결과/판본 혼합·변조/철회 거부·원자 저장/정리.
  새 조회 API·같은 시점 표/그래프/3D는 이후 별도 작은 검증으로 연결한다.
  [실제 수용](../research/crop-coupled-result-storage-implementation.md): 새 DB 8개/기존 저장 8개·
  farm/role/login 18개·수식/artifact 530개, **564 passed / 850.85초**.
  두 사례/hold·fresh store/별도 Python·정확한 artifact/packet·동시/동일/conflict/try-lock,
  현재 권리/계산 후·commit/반환 전 철회와 rollback·실제 역할/trigger/FK·owner 변조 거부/정리.
  시험 실행기 600초 timeout은 별도 기록했고 1,200초 안에 동일 전체 검증을 완료했다.
- [x] **`crop-coupled-operator-policy`** — 저장 v2 기본 policy가 기존 API 기동을 막는 회귀.
  근거: `bdcade9` Application CI의 `operator_config.py:98` 거부/Compose API exit 2.
  최소 변경은 기존 loader/시험 각 한 파일; 생략/정확한 false 수용·미구현 활성화/비 bool 거부.
  [로컬 증거](../research/crop-coupled-operator-policy-implementation.md): RED 2실패/1통과 뒤
  새 7개 포함 기존 operator/runtime 99개·실제 SCRAM/운영 TLS와 임시 자원 정리 통과.
  `d15cf92` [실제 hosted 수용](../research/artifacts/crop-coupled-operator-policy-ci-20261005.json):
  image/runtime 49개·실제 Compose API/작업자·collection/authority/세 정리 성공.
- [x] **`api-crop-coupled-replay`** — 로컬 합성 연구 API 수용; 선행: coupled 저장 v2·policy 회귀 복구.
  [계약](../contracts/api-crop-coupled-replay-v1.md): 같은 result ID/farm/hash·현재 권리의
  읽기 전용 64 sample/8 event 페이지·2 MiB 본문 상한, 원 512시점/사건의 순서/전체성 유지.
  수용: typed/OpenAPI·같은 저장 수치/단위/UTC·hold와 관리·페이지 누락/중복 없음,
  재적분 없는 조회/혼합·변조·현재 권리 철회 거부·선택 factory·실제 HTTPS/SCRAM 전체 본문 30초/정리.
  [실제 수용](../research/api-crop-coupled-replay-implementation.md): 새 API 29개 포함 고유 207개
  분할 검증(단일 GREEN 실행 아님)·512 sample/128 event·HTTPS 19개/두 runtime 재시작,
  최대 11.508339초/649,718 bytes·현재 권리/실제 변조 거부·정리. 새 hosted/브라우저는 별도다.
- [x] **`web-crop-coupled-pages`** — 성장 3D 부모의 첫 자식; 선행: 새 API 로컬 수용.
  [작은 계약](../contracts/web-crop-coupled-pages-v1.md)·새 decoder/시험과 기존 request의 취소 연결.
  [수용](../research/web-crop-coupled-pages-implementation.md): 새 73개/기존 62개·135 passed,
  실제 기록 TLS bytes 대사 1개·512시점/50배열·페이지 전체성/혼합/단위/권리 거부,
  소수 초 hold·취소/늦은 body/타이머/2 MiB/30초·typecheck/build. 새 브라우저/장면은 별도다.
- [x] **`web-crop-coupled-geometry`** — 작은 도형 자식의 로컬 수용; 선행: `web-crop-coupled-pages`.
  새 geometry/시험 각 한 파일로 별도 단위의 50개 C/N 공통 scale·원 구획 순서를 구현한다.
  기존 canopy의 triangle 면적을 재사용한다. 0·큰 값·underflow/잘못된 입력을 임의 최소
  도형으로 숨기지 않고 대체한다. 실제 mesh 좌표/수치/재사용 geometry·dispose를 검사한다.
  [작은 계약](../contracts/web-crop-coupled-geometry-v1.md)·[실제 수용](../research/web-crop-coupled-geometry-implementation.md):
  새 17개/기존 86개·103 passed·기록된 TLS 512시점/51,200 C/N·triangle 면적 대사 1개,
  타입/실제 CPU mesh/0/large/underflow·원자 갱신/정리. 실제 새 화면/WebGL/브라우저는 별도다.
- [x] **`web-crop-coupled-replay`** — 성장 연구 3D 부모의 로컬 소프트웨어 수용; 선행: 새 API·페이지·수치 도형 수용.
  [장면 계약](../contracts/web-crop-coupled-replay-v1.md): 같은 저장 ID/UTC의 512시점 페이지를
  원 순서/수치로 조립하고 잎 triangle 면적·50개 C/N의 별도 단위 비교 도형에 연결한다.
  먼저 decoder/페이지·수치 geometry의 작은 모듈/시험, 다음 기존 화면/표/그래프/장면,
  마지막 실제 저장→HTTPS→브라우저 대사/증거를 순차 구현한다. 새 생물 계수는 넣지 않는다.
  수용: hash/ID/등록/offset 혼합·누락/중복 거부, 취소/뒤늦은 응답·권리 철회 시 이전 장면 제거,
  같은 시점의 표/그래프/도형 수치·0/큰값/소수 초 hold·빈 과거, 키보드/mobile/reduced motion,
  WebGL 장애 대체·자원 해제와 실제 SCRAM/HTTPS/브라우저/서버·DB 정리.
  실제 키/형태/숙기/생과 kg가 아니라 미검증 합성 연구 재생임을 화면에 표시한다.
  [수용 영수증/화면](../research/web-crop-coupled-replay-implementation.md): 단위 129개·Chromium
  19개·실제 SCRAM/HTTPS/WebGL 1개, 실제 완료 6시점/과거 hold 1시점/빈 hold·900 C/N mesh·
  잎 한 면 면적·현재 권리 422/403·3→3 저장 행/GET 재적분 금지/정리.
  typecheck/build·기록 합성 데모 3상태도 통과. 512 UI는 shape 검증, pixel fidelity와 새 hosted는 미수용.
- [x] **`crop-fruit-startup-policy`** — 연구 정책/독립 대수 범위만 수용; 개발/국내 확보와 병행.
  빈 초기 tail/남은 양의 유입·생식기 이전/초기 N1·자동 착과/W1/RGR의 근거를 조사하고
  원/변형/명시 관리 입력을 분리한 판본으로 startup/초기 보존·독립 수치/실측 적용성을 검증한다.
  현재 생식기 순간 수용으로 전체 작기 첫날/생산 예측을 열지 않는다.
  [원천/단위/권리·초기/W1·S·RGR 조사](../research/crop-fruit-startup-policy.md):
  8개 raw hash, 9개 독립 보존/5개 hold·3개 미채택 대안·pre-onset C/N 반례,
  byte-identical 재생성/핀 대사. 명시적 빈 tail 유보 연구 변형을 수용했다.
  자동 착과·생식기 이전·실제 초기/품종/수확/G0–G4는 미수용이다.
- [x] **`crop-fruit-startup-rates`** — 선행: 위 정책·기존 배분/고정 profile.
  [순수 adapter 계약](../contracts/crop-fruit-startup-rates-v1.md)의 두 코드/시험 파일.
  수용: 요청/실현/유보·50개 C/N 유입, 실제 생장 호흡·필수 buffer 보정,
  독립 9개 값/5개 hold·유한/underflow/단위/입력 불변/hash·기존 집중 회귀.
  [실제 수용](../research/crop-fruit-startup-rates-implementation.md): 새 56개/기존 포함
  544개·6.89초·건너뜀0, 14개 실제 출력/hold와 원천/profile/독립 값/로그 hash.
  사용자 산출물: 요청/실현/유보·호흡/보존 표. 기관/적분/저장/3D 결합은 미수용이다.
  국내 자료 확보가 순수 개발을 막지 않으며 실제 생산·예측 게시에는 해당 G0–G3가 필요하다.
- [x] **`crop-plant-startup-rates`** — 순간 결합의 로컬 수용; 위 adapter와 기존 기관/구획 순간 계산이 선행.
  [두 파일 계약](../contracts/crop-plant-startup-rates-v1.md)의 새 모델에서
  buffer 유보/실현 생장 호흡·구획 이동/유지 호흡을 함께 대사한다.
  수용: 빈 초기/첫 명시적 진입/무진입·기존 판본 동등성, 독립 기관/개수 수지·
  불일치/수치 hold·불변/hash와 기존 집중 회귀.
  [실제 수용](../research/crop-plant-startup-rates-implementation.md): 새78개/전체622개·6.99초·
  건너뜀0, 독립22사례/4,796수치와 원 v1의6사례 값 동일·부분 보정 결함 거부를 확인했다.
  표/원 수치·hash 기록이 산출물이며 적분/저장/3D·새 hosted 수용은 남아 있다.
- [x] **`crop-startup-integration`** — 짧은 연구 적분의 로컬 수용; 선행: 새 기관 순간 결합/
  [같은 모델의 프로그램 계약](../contracts/crop-startup-integration-v1.md).
  새 판본의 짧은 적분/사건·누적 요청/실현/유보/호흡·기관/개수 잔차, 독립 참조·
  간격 수렴·past-only hold·현 자원 한도를 작은 구획으로 수용한다. 기존 v1 결과는 보존한다.
  tail 출현/전량 제거의 불연속에서 4차 수렴을 가정하지 않고 실제 오차/hold를 기록한다.
  [실제 수용](../research/crop-startup-integration-implementation.md): 새56개/전체678개·32.69초·
  건너뜀0, 독립6프로그램/23시점·2,829수치/550개수 해석해·기록한 수치 간격 반감 오차와
  24시간/512출력·7.95초/43.36 MiB를 확인했다. 원 v1과 겹치는2프로그램도 동일하다.
  사용자 산출물: UTC별 기관/50 N/C·누적 요청/실현/유보/호흡·보존/개별 오차 표.
- [x] **`crop-startup-artifact`** — 합성 연구 파일의 로컬 수용; 선행: 새 짧은 적분/manifest.
  [두 파일 계약](../contracts/crop-startup-artifact-v1.md): 별도 immutable 판본의 canonical 원
  입력/result·코드/profile/정책·네 수지·사건/hold와 재적분 없는 reader를 검증한다.
  수용: 실제6프로그램/hold·별도 Python·입력/사본 격리·변조/혼합 거부·24시간/512출력 읽기·
  집중 회귀/hash. [실제 수용](../research/crop-startup-artifact-implementation.md): 새79개/전체799개·49.85초·
  건너뜀0, 6프로그램 결과와 이전 적분의 동일·세 실제 hold·별도 Python/재적분 없는 reader·
  시점별 예산/확인 prefix·512출력 파일 3,519,579 bytes/읽기0.286초를 확인했다.
  사용자 산출물: 실제 immutable 파일 ID/hash·UTC 원 수치/hold. 10월5일 KST 완료다.
- [x] **`crop-startup-result-storage`** — 로컬 합성 연구 저장 수용; 선행: 새 artifact의 로컬 수용;
  [저장 v3 계약](../contracts/crop-result-v3.md). 기존 불변 v1/v2를 보존하고 새 farm/result ID·
  현재 source/program 권리·HMAC·원자성/철회/별도 Python·재적분 없는 읽기를 실제 SCRAM으로 검증한다.
  두 구획 모두 증거가 생긴 뒤 체크한다. 전체 잠정2–4시간/10월5–6일 KST, hosted 대기는 별도다.
  - [x] **schema/role/config 로컬 수용:** 새 표 installer와 명시 기본 false flag·선택 grant,
    누락/false operator 호환·타입/과다 grant 거부, 실제 SCRAM의 외래키/bytes/판본·불변 trigger·
    authority SELECT/INSERT·다른 role/수정 거부, 기존 role/config 회귀·DB/password 정리.
    [실제 수용](../research/crop-startup-storage-schema-implementation.md): 새20개/184개 고유 분할·
    실제 SCRAM/17개 잘못된 행·5개 grant 변화·owner trigger·불변 pin25개/정리0개를 확인했다.
  - [x] **custody 로컬 수용:** 새 store/test에서 원 요청과 현재 farm/crop/범위/권리·등록 참조를 묶고,
    builder 계산/hold·HMAC/변조/혼합 거부·동일/동시 재시도/rollback·별도 프로세스 읽기를 검증한다.
    [실제 수용](../research/crop-startup-result-storage-implementation.md): 새18개/집중119개·
    6프로그램/같은 bytes·현재 code hash·HMAC/22개 서명된 내용 변조 거부·commit 전후 철회,
    실제 SCRAM/별도 Python·DB/password 정리0개를 확인했다. 10월5일 KST 로컬 완료;
    API/새 3D와 hosted 전체 수용은 별도다.
- [x] **`crop-startup-replay-link`** — 합성 연구의 로컬 수용; 선행: 새 짧은 적분/manifest·artifact·새 저장 v3와 판본별 조회 계약.
  기존 불변 저장·현재 권리/조회·동일 UTC 3D에 새 모델을 명시적으로 연결한다.
  판본 혼합·권리 철회·취소/hold·원 수치/mesh/단위 대사와 실제 SCRAM/TLS/브라우저·정리를
  단계별로 검증한다. 임의 초기 seed/착과 모양·생과 kg를 추가하지 않는다.
  - [x] **`crop-startup-api-replay`** — 합성 연구 API 로컬 수용; 선행: v3 custody의 실제 SCRAM 수용;
    [새 페이지 API 계약](../contracts/api-crop-startup-replay-v1.md). 닫힌 typed/OpenAPI·같은 저장
    ID/hash/UTC·50 N/C/16누적/4진단·512출력/사건 페이지·현재 권리/변조/hold·GET 재적분 없음,
    실제 HTTPS 최대 페이지 전체 본문30초/재시작·정리.
    [실제 수용](../research/api-crop-startup-replay-implementation.md): 새47개/고유252개 분할·실제
    HTTPS/SCRAM19응답·최대512/128·최대14.248425초/700,084 bytes·정리0개를 확인했다.
    10월5일 KST 로컬 완료; 새 3D와 원격 수용은 별도다.
  - [x] **`crop-startup-web-pages`** — 합성 응답/페이지 로컬 수용; 선행: 위 API/새 [화면 계약](../contracts/web-crop-startup-replay-v1.md);
    새 닫힌 decoder/순차 페이지 수집에서 v3 ID/farm/hash·50 N/C/16누적/4진단·단위/UTC,
    최대512/128 전체성·혼합/누락/중복·취소·소수 초 hold/빈 과거/현재 거부를 검증한다.
    기록된 실제 TLS 응답의 원값/hash 대사와 기존 v1/v2 회귀·typecheck/build 뒤 체크한다.
    [실제 수용](../research/web-crop-startup-pages-implementation.md): 새77개/웹 전체376개·0skip·
    typecheck/build·실제 TLS decoded 원값/파일 hash, 최대16순차 요청/512sample·128event 전체성,
    현재 거부/취소·timers/listeners/stream 정리를 확인했다. 10월5일 KST 로컬 완료;
    장면/브라우저와 원격 수용은 별도다.
  - [x] **`crop-startup-web-geometry`** — v3 로그 비교 도형의 로컬 수용; 선행: 새 응답/페이지.
    실제 빈 초기의 극소 양수/Float32 관측을 근거로, 고정 공통 C/N 로그 축·영 숨김·원값 보존,
    극소/극대·50mesh/정리·기존 v2 선형/unsafe 대체를 새7개/기존 포함24개로 검증했다.
    [실제 수용/증거](../research/web-crop-startup-replay-implementation.md). 임의 seed/작물 최소량은 없다.
  - [x] **`crop-startup-web-replay`** — 합성 연구 화면의 로컬 수용; 선행: 새 응답/페이지·위 도형과 화면 계약;
    같은 v3 result ID/UTC의 표·그래프·50구획 성장 3D와 원량/mesh 대사,
    빈 과거/hold·권리/취소·WebGL HTML 대체·실제 SCRAM/TLS/브라우저·정리 후 체크한다.
    [실제 수용](../research/web-crop-startup-replay-implementation.md): 웹383개·Chromium31개·실제 경로1개,
    고유 완료12시점/15번 화면·1,500 C/N mesh·16누적/4진단·같은 UTC/원량·최대본문9.485초,
    행5→5/GET 재적분 없음·서버/DB/password 정리0잔여. 10월5일 KST 로컬 완료;
    이후 `1555610`의 [CI5개/백엔드3,456개·UID4개·동일 목록/정리·집계](../research/artifacts/crop-startup-replay-ci-20261005.json)도 수용했다.
    후속 continuation/reader/긴 RHS hosted·pixel fidelity·실제 품종/전체 작기/생과·G0–G4는 별도 미수용이다.
- [ ] **`crop-fruit-cohorts`** — 전체 구획의 부모 작업; 순간 수용만으로 완료하지 않는다. 개발 선행: `crop-fruit-transport`·`crop-fruit-allocation-rates`·고정 Gompertz 수요·명시적 관리 사건.
  참조 계수의 순수 모듈 개발은 국내 자료 접근/G2를 기다리지 않는다.
  실제 Axiany 적용에는 `crop-input-audit`와 해당 품종/관리·발달 근거가 추가로 필요하다.
  예정 파일(3): `backend/app/crop_fruit_cohorts.py`, `backend/tests/test_crop_fruit_cohorts.py`,
  `contracts/crop-fruit-cohorts-v2.md`.
  수용: 착과/발달 구획·개수·적심/적엽 사건의 고정 입력/품종 적용 범위와 기관 수지.
  확인: 독립 참조·개수/질량 보존·사건 경계 pytest. 일반 토마토 계수로 Axiany 숙기 승인 없음.
- [ ] **`crop-harvest-conversion`** — 선행: 과실 구획과 품종별 변환/수확 근거.
  예정 파일(3): `backend/app/crop_harvest.py`, `backend/tests/test_crop_harvest.py`,
  `contracts/crop-harvest-v1.md`.
  수용: 건물/생과중·밀도·수확 사건·등급/불량의 출처/단위, 제거·생과 kg/개수·누적 수지;
  미확인 변환계수/수확/등급을 기본 비율로 채우지 않음. 확인: 집중 pytest/실측 대조.
  사용자 산출물: 적용 범위/hold가 있는 생산량 시계열; 국내 미래 예측은 해당 G2/G3a 뒤.
- [ ] **`crop-climate-coupling`** — 선행: 생산 모델의 필요한 상태와 수관/PAR/CO₂ 근거.
  예정 파일(3): `backend/app/crop_climate_coupling.py`, `backend/tests/test_crop_climate_coupling.py`,
  `contracts/crop-climate-coupling-v1.md`.
  수용: 기존 실내 기온과 수관/광/CO₂·LAI/증산 관계, 시간 간격과 피드백 수지;
  기존 시나리오 작물 계수와 이중 반영 없음. 확인: 집중 열/수증기·탄소 수지/해상도 시험.
  단방향 forcing 재생은 결합 생산 모델과 구별한다.
- [ ] **`crop-water-nutrient`** — 선행: 작물/기후 결합·배지/급배액/성분 근거.
  예정 파일(3): `backend/app/crop_water_nutrient.py`, `backend/tests/test_crop_water_nutrient.py`,
  `contracts/crop-water-nutrient-v1.md`.
  수용: 증산·급액·배액·재순환·구매 용수/성분 재고 수지와 적정 수분 가정의 범위;
  실제 계량·처방/성분 없으면 소비/스트레스 예측 보류. 확인: 단위/수지·집중 pytest/실측 대조.
- [ ] **`crop-energy-purchases`** — 선행: 작물/기후 결합·설비 효율/계량/운전 근거.
  예정 파일(3): `backend/app/crop_energy.py`, `backend/tests/test_crop_energy.py`,
  `contracts/crop-energy-v1.md`.
  수용: 공급열/미충족 열과 구매 전력/연료·보조 설비/CO₂ 분리, 효율/COP·단위/적용 범위;
  근거가 없으면 변환 보류. 확인: 집중 수지/경계 pytest·계량/청구 대조.
- [ ] **`crop-execution-link`** — 선행: 해당 작물/자원 모델·불변 결과 계약과 현재 farm/batch/zone 연결.
  필요 근거: 현재 작물 v1은 내부 저장된 합성 연구 GET이며 사용자 계산 접수/소비·완료 결과 선택이 없음.
  작은 접수/작업자/저장/조회/UI 단계로 나눠 기존 계정/작업 저장소와 worker를 재사용한다.
  수용: 같은 농장/작물/배치·입력/모델/계수/UTC/현재 권리의 접수→실행→불변 결과 선택→3D,
  취소/재시도/재시작·혼합/늦은 변경 거부와 end-to-end 검증. 실제 입력은 해당 G0/G1 필요.
  연구 결과와 승인 Run을 구분하며 실제 제품 CLI/독립 해제·예측/추천 관문을 자동 승격하지 않음.
- [ ] **`crop-economic-link`** — 선행: 생산량·자원 계산·`crop-execution-link`와 같은 배치/달력의 경제 입력.
  예정 파일(3): `backend/app/crop_economic_link.py`, `backend/tests/test_crop_economic_link.py`,
  `contracts/crop-economic-link-v1.md`.
  수용: 같은 입력/결과 해시의 H/P/S·등급/반품/폐기/재고·자원/원가와 기존 Decimal 손익/현금;
  모델 수확 출처 유지·생산원가 한 번 반영·현재 권리/MarketContext/시점 검사·누락 시 hold.
  확인: 집중 pytest/원장 대사. 산출물 조건부 손익표; 미래 가격/마진은 경제 G3a 전 비공개.
- [x] **`crop-independent-data-protocol`** — 모델 개발과 병행하는 확보 준비.
  산출물(3): [프로토콜](../research/crop-independent-data-protocol.md),
  [필수 자료/권리 양식](../research/crop-independent-data-checklist.md),
  [실제 확보 상태](../research/crop-independent-data-status.json).
  수용: 동의/사용·표시·공유/철회·CLI 처리 범위, 센서/품종·관리/생육/수확·자원/경제 채널,
  보정/독립 작기 사전 분할과 as-of 절차, 확보 0건/검증 미통과의 명시. 링크/필수 필드 대조를 통과했다([수용 기록](../research/crop-priority-and-runtime-freeze-20261004.md#이번-재정렬의-문서조사-수용)).
- [ ] **`crop-independent-data-access`** — 선행: 프로토콜; **외부 접근 의존성**, 현재 0건.
  실제 계약 ID·권리/필드 범위와 사설 파일 해시/시각/QC·reserved 독립 작기를 상태 판본에 연결한다.
  수용: 직접 동의받은 국내 품종/관리·측정 자료와 미사용 기간의 접근/이용 근거.
  확인: 계약/동의·필수 채널·센서 오차·개발/보정/독립성 대조. 개인/제한 원문은 Git/프롬프트에 넣지 않음.
  프로토콜 완료는 이 접근 완료가 아니다. 최종 G2 전 해당 계산 증거를 연결하며
  KMA·전체 G1은 자료 획득 착수 조건이 아니다.
- [ ] **`crop-g3a-evidence`** — 선행: 해당 작물 출력 G2·생산 모델·권리 있는 미사용 미래 작기.
  예정 파일(3): `research/crop-g3a-protocol.md`, `research/crop-g3a-source-register.md`,
  `backend/tests/test_crop_g3a_gate.py`.
  수용: 결정 시각에 가능했던 입력만으로 사전 등록한 미래 수확/품질 검증,
  단순 기준선 대비 오차/편향/범위·지역/품종/관리 적용성. 보정/개발 참조 재사용 금지.
  확인: 독립 기간/시점/측정 대조와 관문 시험. 미래 경제는 별도 `g3a-evidence`, 추천은 G3b 필요.

## 운영 기반 고정 (2026-10-04)

`d19f7c0`의 [5개 CI/완료 범위](../research/crop-priority-and-runtime-freeze-20261004.md)를
현재 기반으로 고정한다. 결합 원천 Compose/최대 동시 성능/독립 custody 등 후속 기반은
핵심 작물 경로 또는 공개 관문에서 필요성이 입증될 때 재개한다. 아래 날짜별 수용 기록과
상위 미완료 체크를 보존한다. 새로운 기반 작업으로 다음 작물 모듈의 착수를 대체하지 않는다.

## 작성 Run 경제·평가 연결 (2026-10-01)

- [x] **`authored-economic-execution`** — 선행: 저장 작성 Run과 현재 농장/경제 판본 제공자.
  [입력/영수증 V3 계약](../contracts/authored-economic-execution-v1.md)의 접수·작업자·완료 금액/현금 조회와
  표준 런타임 조립을 구현했다. 실제 SCRAM에서 완료 부모·현재 권리·같은 경제 후보·안정 재요청,
  혼합/미완료/다른 테넌트/누락 제공자 거부 및 접수·게시 직후 변경 롤백을 확인했다.
  [집중 소프트웨어 증거](../research/authored-economic-execution-implementation.md): 서로 다른 시험 82개가 통과했다.
  호스팅 전체 CI·제품 CLI·독립 G1과 웹/평가 연결은 이 체크의 수용 범위 밖이다.
- [x] **`authored-calculation-assessment`** — 선행: `authored-economic-execution`.
  [평가 입력 V3](../contracts/authored-calculation-assessment-v1.md)에 작성 열·V3 경제 작업의
  완료 입력/영수증/농장·해제·문맥을 고정하고 공유 CLI 라우터의 별도 검증기·보류 조회에 연결했다.
  실제 SCRAM의 세 통합 사례·HTTPS 8개 응답, 혼합/다른 부모/변조/권리 철회/늦은 변경 롤백,
  기존 평가 호환과 브라우저 회귀를 확인했다([서로 다른 집중 시험 83개](../research/authored-calculation-assessment-implementation.md)).
  시험용 CLI·서명의 서버 소프트웨어 범위이며 새 호스팅 CI·작성 웹 부모 선택·제품 CLI·독립 G1은 후속이다.
- [x] **`authored-financial-selection`** — 선행: `authored-calculation-assessment`.
  [현재 작성 Run의 경제 입력·작업 이력 조회](../contracts/authored-financial-selection-v1.md)는 웹 부모 선택의 서버 선행 조건이다.
  현재 농장에 고정된 경제 판본을 서버에서 확인하고 같은 Run의 경제·평가 기록을 페이지별로 복원한다.
  실제 SCRAM의 선택·권한·혼합/외부/미완료/손상 거부·늦은 변경과 표준 HTTPS 30초 제한을 확인했다
  ([서로 다른 집중 시험 59개](../research/authored-financial-selection-implementation.md)).
  시험용 CLI·서명의 서버 소프트웨어 범위이며 작성 웹 선택·새 호스팅 CI·제품 CLI·독립 G1은 후속이다.
- [x] **`web-authored-economic-assessment`** — 선행: `authored-financial-selection`.
  같은 계정의 작성 Run 선택에서 같은 경제 판본의 접수·조회와 평가로 이어지게 한다.
  식별자를 직접 알지 않아도 저장 부모를 선택하게 하며, 응답 유실·재연결·계정 변경,
  실제 HTTPS/SCRAM 브라우저의 조건부 금액/현금·보류와 3D 연결을 확인한다.
  07 화면에서 현재 서버의 V3 입력을 고정하고 금액·월별 현금·보류 6개와 같은 Run의 3D를 연결했다.
  저장 기록 선택·새 요청 준비, 유실 재요청·계정 변경·현재 거부를 확인했다.
  [수용 증거](../research/web-authored-economic-assessment-implementation.md): 웹 단위 122개,
  집중 Chromium 19개, 실제 PostgreSQL 16.15/SCRAM·HTTPS 브라우저 1개가 통과했다.
  마지막 실제 연결은 29개 응답 헤더·최대 23.239초/요청 제한 30초이며 전체 본문 지연 측정은 아니다.
  정확한 웹 커밋의 [호스팅 작성 7개 묶음·웹/C0 CI](../research/web-authored-economic-assessment-implementation.md#hosted-verification-of-the-web-commit)도 통과했다.
  시험용 CLI·서명의 소프트웨어 범위다. 전체 백엔드 CI, 일반 지역 흐름·제품 CLI·독립 G1/G4는 후속이며
  전체 `web-shell`/`end-to-end-g1` 체크는 유지한다.

## 지역 원천에서 농장 작성 연결 (2026-10-01)

- [x] **`source-farm-selection`** (M) — 선행: 소유 조사·수집/검토와 농장 입력 계약.
  [원천 참조 계약](../contracts/source-farm-selection-v1.md)의 읽기 전용 제공자를 구현한다.
  실제 SCRAM의 정확한 완료 부모/원문/현재 등록 범위·저장 스냅샷·서명 문맥을 대사하고,
  다른 소유자/부모·미완료·변조·권리/포인터의 늦은 변경을 거부한다.
  쓰기 범위 없이 읽기 성공과 추가 저장 없음, 보류 표시·원본/숫자 미노출을 확인한다.
  [실제 SCRAM 집중 4개](../research/source-farm-selection-implementation.md)가 통과했다.
  합성 CLI/서명의 제공자 소프트웨어 범위이며 HTTP·웹/실제 제품 CLI·독립 G1은 후속이다.
- [x] **`api-source-farm-selection`** (M) — 선행: `source-farm-selection`.
  인증 GET·닫힌 OpenAPI·표준 런타임을 같은 authority 제공자에 연결한다.
  Bearer/테넌트·권한·보류/미준비 응답과 기존 30초 제한 아래 실제 HTTPS/SCRAM을 확인한다.
  [인증 API](../contracts/api-source-farm-selection-v1.md)와 표준 조립의
  [집중 66개](../research/api-source-farm-selection-implementation.md)가 통과했다.
  실제 HTTPS 12개 전체 응답 최대 0.582초, 쓰기 범위 0개와 저장 불변을 확인했다.
  합성 CLI/서명의 소프트웨어 범위이며 새 호스팅 CI·시장/경제/웹·제품 CLI·독립 G1은 후속이다.
- [x] **`farm-economic-candidate-selection`** (M, 합성 소프트웨어 범위) — 선행: `api-source-farm-selection`.
  [읽기 계약](../contracts/farm-economic-candidate-selection-v1.md)의 목록/현재 선택 제공자와 인증 API를 연결한다.
  선택 원천과 같은 서명 문맥/기간/목표의 저장 경제 후보·기존 시장 보류를 찾는다.
  이력 메타데이터와 현재 선택 검증을 나누고 다른 문맥·현재 권리 철회·페이지 경계를 확인한다.
  새 요금/작물 수치·G0 승인·시장 보류를 조회 중 만들지 않는다.
  - 읽기 제공자의 [SCRAM 집중 5개](../research/farm-economic-candidate-selection-implementation.md)가 통과했다.
    정확한 선택 참조로 실제 농장 등록까지 확인했다.
  - [인증 API](../contracts/api-farm-economic-candidate-selection-v1.md)의
    [집중 64개](../research/api-farm-economic-candidate-selection-implementation.md)가 통과했다.
    실제 HTTPS 20개 전체 응답 최대 7.844초/기존 30초 제한, 페이지 복구·권리 철회·쓰기 범위 0개를 확인했다.
    새 호스팅 CI·농장 웹·실제 제품 CLI·독립 해제/전체 G1은 후속이다.
- [x] **`web-source-farm-authoring`** (M) — 선행: `farm-economic-candidate-selection`.
  [웹 연결 계약](../contracts/web-source-farm-authoring-v1.md)을 따른다.
  저장 조사·수집/검토와 경제 후보 선택을 농장 폼에 연결해 선행 식별자 직접 입력을 줄인다.
  원천/경제 조합 변경·응답 유실·재연결·계정 변경을 확인하며 명시적 농장 숫자/권리 선언을 받는다.
  실제 HTTPS/SCRAM 브라우저에서 신규 등록→검토/작성 Run→경제/평가·같은 3D 연결을 검증한다.
  시험용 CLI/해제는 소프트웨어 범위이고 실제 제품 CLI·독립 전체 G1 체크는 유지한다.
  - 첫 [브라우저 클라이언트](../research/source-farm-client-implementation.md)는
    원천/후보의 정확한 참조·검증 표시·페이지와 UTC 마이크로초를 확인했다(집중 95개·typecheck/build).
    선택 UI·조합 변경/복구는 [화면 연결 후보](../research/source-farm-web-implementation.md)에서
    집중 Chromium 14개로 확인했다. 실제 HTTPS/SCRAM 직접 입력·원천 선택의 신규 등록→Run→3D는
    2개가 통과했고 3개 화면 대조도 실행했다(낮은 일치율, 정밀 수용 아님).
    [같은 새 Run의 경제/평가 연속 검증](../research/source-farm-financial-continuation-implementation.md)도
    실제 HTTPS/SCRAM 1개가 통과했다. 서버 금액·월별 현금·보류 6개·재접속·동일 3D와
    27개 전체 본문(최대 24.363초/기존 30초 제한)을 확인했다. 해당 판본의 호스팅 작성 7개 묶음·웹/C0도
    통과했다(호스팅 본문 최대 27.278초/기존 30초 제한).
    [화면 보완](../research/source-farm-layout-refinement-implementation.md)은 참조 상세 펼치기·나란한 요약·
    키보드 구역 이동을 확인했다(집중 14개 중 마지막 변경은 영향 사례 1개 재확인, build/typecheck).
    세 상태·세 화면 폭 대조에 넘침/페이지 오류가 없지만 디자인 정밀 수용은 주장하지 않는다.
    [등록 응답 미확인 잠금 보완](../research/source-farm-registration-lock-implementation.md)은
    연결 변경과 다른 접수/부모 전환의 차단을 33개 집중 Chromium과 build/typecheck로 확인했다.
    검증되지 않은 성공은 동일 입력 재확인을 유지하고, 확정 거부는 입력 검토와 연결을 다시 허용한다.
    `93e30a7`의 [최종 소프트웨어 수용](../research/source-farm-web-implementation.md#final-software-ui-acceptance-2026-10-01)은
    호스팅 웹 154/50개와 작성 브라우저 4개에서 저장 원천 선택→신규 농장 등록→경제/평가·같은 3D를 확인했다.
    본문 최대 26.3284초이며 낮은 디자인 일치율을 기록한다. 별도 경제 브라우저 1개 실패와
    후속 권한 감사 지연 보완은 분리하여 검증하고 제품 CLI·독립 G1/G4 체크는 유지한다.

## 런타임 권한 감사 지연 보완 (2026-10-01)

- [x] **`runtime-role-audit-batching`** (S) — 선행: 기존 SCRAM 권한 감사 계약과 `backend-ci-partition`.
  [측정·구현 증거](../research/runtime-role-audit-batching-implementation.md#all-role-query-batching-follow-up-2026-10-01)를 따른다.
  네 역할의 현재 권한 조회를 묶어 왕복을 줄이고 전체 역할/테이블/열/함수·grant option·중간 철회를 유지한다.
  수용: 집중 보안·조회 예산과 실제 HTTPS/Chromium의 경제→평가 보류→복구→3D 및 호스팅 검증을 확인한다.
  30초 전체 본문 제한을 올리거나 권한을 캐시하지 않는다. 로컬 서로 다른 보안 109개와 실제 브라우저 1개,
  본문 29개·최대 24.5048초가 통과했다. 감사 451회 유지, SQL 실행 14,763→7,998과 예산 시험의 15회 조회를
  확인했다. `7f49f52`의 호스팅 PostgreSQL 18 전체 2,253개·UID 4개 및 작성 7개 묶음 139회·웹/C0와 정리가 통과했다([최종 증거](../research/runtime-role-audit-batching-implementation.md#terminal-broad-backend-acceptance-at-7f49f52)). 256개 손익분기 비동기 검증과 G1/G4 수용은 별도다.

## 전체 백엔드 CI 실행 경계 보완 (2026-10-01)

- [x] **`backend-ci-partition`** (S) — 선행: 기존 `backend-ci` 실행 구조.
  [관측된 150분 시간 초과](../research/source-farm-web-implementation.md#hosted-ci-and-resource-checkpoint)를
  근거로 전체 백엔드 시험을 유한한 파일 묶음으로 나눈다. 체크 목록과 파일 집합을 결정적으로 대사해
  중복·누락/미분류가 없고 기존 전체 pytest/UID 검사·DB cleanup이 유지되는지 확인한다.
  제한 시간을 올리거나 느린 시험을 제외하지 않는다. 로컬에서는 한 묶음씩, 호스팅에서는 제한된 병렬도로
  검증한 뒤 전 묶음·UID 검사와 cleanup의 실제 호스팅 증거가 있을 때 체크한다.
  진행: [분할 계약](../contracts/backend-ci-partition-v1.md)과
  [검증 기록](../research/backend-ci-partition-implementation.md)을 추가했다.
  실제 기본 수집 2,205개/132파일과 6개 분할의 합집합·동일 전체 해시를 대사했고
  누락·중복은 0개다. 분할 도구 집중 시험 11개와 실패/누락을 거부하는 집계 프로그램을 확인했다.
  로컬 PG16 묶음 4는 253개/건너뜀 0개가 통과했다. `0fdecc2`의 웹·C0와
  작성 PG18 7개 묶음도 통과했다. 전체 6개 묶음은 2,204개 통과/기존 OpenAPI 기대값 1개 실패였고,
  UID/cleanup은 통과했다. 집계는 실패를 정확히 거부했다. V1/V2/V3 닫힌 계약 기대값을
  수정한 집중 2개가 통과했다. `5dc63f3`의 [호스팅 수용](../research/backend-ci-partition-implementation.md#hosted-acceptance-after-the-openapi-correction)은
  전체 2,205개/건너뜀 0개·같은 수집 해시·별도 UID 4개·내용 접근·전 묶음 cleanup과 최종 집계가
  통과했다. 이 체크는 CI 분할의 소프트웨어 범위이며 후속 UI 판본의 CI와 실제 제품 CLI·G1/G4는 별도다.

## 최대 손익분기 접수 성능 (2026-10-02)

커밋된 `c3ff00e`의 [호스팅 전체 회귀 수용](../research/break-even-admission-performance-implementation.md#terminal-hosted-regression-at-c3ff00e)은 PostgreSQL 18.6의 2,305개·별도 UID 4개, 동일 목록/정리와 작성 141회·웹 160/51·C0를 확인했다. 후속 보호된 접수 개선안은 별도 판본이며 최대 격자 수용 체크는 열어 둔다.

- [x] **`break-even-admission-performance`** — 선행: 기존 `api-flow`의 손익분기 계획 접수·실제 원천 저장 경로. 접수·참조 읽기·후보·원천·보류 보고서·서명 문맥의 여섯 모듈에서 연결과 조회 병목을 개선했다. [같은 코드의 로컬 수용](../research/break-even-admission-performance-implementation.md#same-code-compatibility-and-local-performance-acceptance)은 집중 47개, 동일 실제 256개 ASGI 접수 **29.5103초 < 30초**와 계산/취소/현재 결과 조회·두 시험값의 실제 TLS/별도 Python 작업자 11개를 확인했다. 전체 응답 10개 최대는 0.4551초다. 같은 판본의 호스팅 전체 회귀도 통과했다. 합성 소프트웨어 계약의 수용이며 보호된 최대 TLS 전체 응답·작업자 부하·취소/재시도/철회와 독립 CLI/G1/G4는 후속 수용을 계속 따른다.

- [x] **`break-even-maximum-protected-path`** — 선행: `break-even-admission-performance`의 실제 최대 접수 기준 통과, 기존 계산·비동기 검증 HTTP/운영자 조립. [명시적 실제 SCRAM·HTTPS 시험](../backend/tests/break_even_maximum_full_smoke.py)은 같은 256개 실제 시험값·1,630개 합성 원천에서 **1개 통과/4,527.33초**로 완료했다. [전체 경로 기록](../research/break-even-admission-performance-implementation.md#terminal-protected-maximum-path-acceptance-2026-10-02)은 별도 Python 계산 2,258.11초·검증 1,207.10초, 전체 256개 완료 결과 조회 3.7967초와 모든 HTTPS 본문 10개 최대 29.6373초 < 30초를 확인했다. 동일 접수 재사용·미인증 401·현재 보류 문맥 변경 후 503/금액 비표시·서버와 DB/암호 정리도 통과했다. 단일 로컬 합성 소프트웨어 수용이며 최초 접수 여유는 0.3627초다. 별도 최대 취소/임대 회복·원천 권리 철회·자동 운영 및 실제 제품 CLI/독립 관문 수용은 후속이다.

- [x] **`break-even-protected-admission-headroom`** — 선행: 로컬 접수 성능 수용과 실제 최대 HTTPS 시간 초과 반례. 효과가 확인되지 않은 참조 권한 확인 묶음은 되돌렸다. `04c517c`의 정적 필드명 검사 보완은 기존 거부/직렬화 규칙을 유지하고 집중 55개·작업자/현재 권리/취소/두 시험값의 실제 TLS·진단 12개를 통과했다. [로컬 최대 보호된 접수 수용](../research/break-even-admission-performance-implementation.md#protected-maximum-admission-accepted-locally)은 같은 실제 256개 표준 Bearer HTTPS 본문 EOF 29.6373초·동일 재접수 29.0140초를 확인했다. 최초 여유는 0.3627초이며 단일 로컬 표본의 접수 수용이다. 새 호스팅 회귀·최대 계산/검증/읽기 전체 경로와 별도 복구/철회·독립 CLI/관문은 후속 수용을 따른다.

## 실제 앱 운영 조립 (2026-10-02)

현행 `compose.yaml`과 두 Dockerfile은 의존성 이미지의 C0 골격이며 앱 역할은
`/bin/false`로 종료한다. API는 운영자가 만든 factory를 요구한다. 신규 발견·소비
연결은 기존 경제·손익분기 계산/검증 작업자의 임대 경로를 사용한다. 다음 작업은 기존
`api-flow`/`end-to-end-g1`의 이 공백을 작은 단위로 구현한다.

- [x] **`protected-api-operator-config`** (M) — 선행: 기존 `api-runtime` 조립과 로그인/내용 접근 정책.
  구현 파일(3): `backend/app/operator_config.py`, `backend/tests/test_operator_config.py`,
  `contracts/operator-config-v1.md`. 운영자 파일에서 명시적 정책·DB/아티팩트/TLS·Bearer와
  신뢰 의존성 참조를 읽어 기존 typed config/factory에 전달한다. HTTP·CLI 제안으로
  파일/모듈/키를 선택하지 못하며, 누락된 원천/검증기·독립 증거를 시험용 값으로 채우지 않는다.
  수용: 정상 사설 구성의 기존 HTTPS 조립, 잘못된 파일 소유/권한·경로·닫힌 스키마 거부,
  현재 역할/제공자 불일치의 고정 오류와 출력의 비밀 미포함. 확인: 해당 focused pytest와
  실제 SCRAM·HTTPS 시작/종료 시험. 실제 배포 자격증명 소유권과 G1/G4는 후속이다.
  [로컬 소프트웨어 수용](../contracts/operator-config-v1.md#local-software-acceptance--2026-10-02)은
  `bfc0ab0`의 집중 45개/5.61초로 닫힌 구성·실제 권한/경로·읽는 중 변경·핸들 정리,
  실제 SCRAM 로그인/현재 역할/제공자 결합/TLS 오류 거부와 별도 표준 HTTPS/Bearer 기동·
  접수/재조회·기동 후 권한 변경 503·종료/DB/비밀 정리를 확인했다.
  소유 UID/ACL 반례는 검사 결과 stub이며 독립 자격증명 소유권·새 호스팅 회귀·앱 Compose는 후속이다.
- [x] **`deterministic-job-discovery`** (M) — 선행: 실제 불변 작업 저장소·경제/손익분기 작업자.
  구현 파일(3): `backend/app/deterministic_job_discovery.py`,
  `backend/tests/test_deterministic_job_discovery.py`, `contracts/deterministic-job-discovery-v1.md`.
  고정 테넌트의 처리 가능한 경제·손익분기 계산/검증 UUID를 제한된 조회로 찾는다.
  같은 simulation 단계의 다른 입력을 잘못 임대하지 않으며, 실제 현재 권한·원본 입력 해시와
  각 작업자의 기존 입력 판별을 유지한다. 발견은 작업 임대/완료나 자료 승인 자체가 아니다.
  수용: 여러 종류·테넌트·미래 재시도·취소·손상/권한 철회의 실제 SCRAM 혼합 대기열에서
  소유 대상만 발견하고, 두 소비자의 경쟁은 기존 claim/lease가 결정한다. 확인: focused pytest.
  [실제 SCRAM 수용](../contracts/deterministic-job-discovery-v1.md#actual-scram-software-acceptance-2026-10-02)은
  집중 47개/22.11초로 읽기 전용 페이지 이동·현재 권한/역할·입력 손상 거부와 기존 작업자의
  경쟁/원자 게시·만료된 취소/소진 회복을 확인했다. 자동 전경 소비·새 파일의 호스팅 회귀,
  실제 제품 CLI/독립 G1/G4는 후속이다.
- [x] **`deterministic-worker-loop`** (M) — 선행: `deterministic-job-discovery`.
  구현 파일(3): `backend/app/deterministic_work.py`, `backend/tests/test_deterministic_work.py`,
  `contracts/deterministic-worker-loop-v1.md`. 보호된 factory가 만든 기존 작업자를 호출하는
  전경 소비 루프를 연결한다. 순차 실행·설정된 대기·종료 신호를 사용하고 HTTP 요청 안에서
  계산하거나 또 다른 CLI를 시작하지 않는다. 수용: 접수 뒤 수동 UUID 전달 없이 완료 조회,
  유휴 CPU/조회의 제한, 취소·프로세스 중단/재시작 뒤 기존 임대 회복과 부분 게시 없음.
  확인: 실제 별도 Python/SCRAM 프로세스 시험. CLI 조사/수집 검토/평가 연결은 별도로 유지한다.
  [실제 프로세스 수용](../contracts/deterministic-worker-loop-v1.md#software-acceptance-2026-10-02)은
  집중 37개/130.07초로 자동 경제·손익분기 계산/검증, 유휴 조회 간격·SIGTERM,
  취소·강제 종료 뒤 임대 회복·단일 게시·현재 완료 조회와 자원 정리를 확인했다.
  유휴 2.2초의 CPU는 0.03초, 최소 조회 간격 1.039초, 종료 0.114초였다.
  신호 처리의 잠금 사용과 모듈 진입 형식 오류를 수정했으며 새 호스팅 회귀·운영 구성은 후속이다.
- [ ] **`application-compose-runtime`** (M) — 선행: `protected-api-operator-config`,
  `deterministic-worker-loop`, 기존 수집/CLI 전경 서비스와 웹 빌드.
  아래 이미지·서비스/CI 두 하위 작업을 순서대로 수용한다. 최종 경계는 그대로 유지한다.
  기존 C0 모델에 명시적 앱 실행 override를 더해 소스·웹 산출물과 기존 전경 진입점을
  기동한다. 실제 프로세스/건강 확인·고정 이미지·서비스별 자격증명/UID·POSIX 아티팩트 연결,
  WSL 자원 한도와 실패 후 정리를 검증한다. 수용: 빈 호스팅 환경에서 빌드/기동·접수/처리/
  완료 재조회·재시작·비밀/볼륨 정리. fake CLI/시험 서명을 쓰는 시험은 소프트웨어 조립으로
  기록하며 실제 세 단계 CLI·독립 해제/3D/G1과 production G4 체크를 대체하지 않는다.
  - [x] **`application-images`** — 이미지 파일(5): `backend/Dockerfile`, `web/Dockerfile`,
    `.dockerignore`, `web/nginx.conf`, `contracts/application-images-v1.md`;
    수용 스크립트 `scripts/check-application-images.py`와 아래 공통 앱 workflow.
    기존 C0 의존성 target을 유지하고 별도 앱 target에 현재 소스/스키마·잠금/합성 fixture와
    정적 웹 산출물을 담는다. 웹은 고정 NGINX의 표준 TLS로 loopback API에 같은 출처로
    연결하며 API 인증서도 검사한다. 기본 UID·읽기 전용 운용·닫힌 기동과 빌드 입력 제외를
    확인하고 실제 hosted 이미지 빌드/기동 뒤에 체크한다. 코드·정적 bundle은 G1/G4 증거가 아니다.
    [실제 이미지 수용](../research/application-images-implementation.md)은 Docker 제외 반례 수정 후
    두 앱 이미지·UID/읽기 전용·닫힌 기동·정상 TLS/잘못된 상위 DNS 거부·정리를 확인했다.
  - [x] **`application-services-ci`** — 선행: `application-images`.
    파일(4): `compose.application.yaml`, `.github/workflows/application-runtime.yml`,
    `scripts/check-application-runtime.py`, `contracts/application-compose-runtime-v1.md`.
    신뢰된 운영자 구성/제공자를 별도 사설 경로로 주입하고 기존 API·전경 소비 진입점을
    실제 서비스로 연결한다. 고정 이미지·UID/자격증명/아티팩트·자원 상한을 검사하고
    호스팅의 정상 TLS/SCRAM 접수→자동 완료→현재 재조회·재시작·실패·정리로 수용한다.
    합성 권한/입력/키·시험용 CLI의 증거 범위와 독립 운영/G1/G4 보류를 기록한다.
    [실제 서비스 수용](../research/application-compose-runtime-implementation.md)은 tmpfs/재시작 포트
    반례 수정 뒤 표준 TLS/SCRAM 접수·자동 완료·현재 결과/동일 재시작·권한 변경 503과
    실제 자원/UID/마운트·정리를 확인했다. API/경제는 같은 기존 writer 권한이며
    조사/수집 자동 소비와 독립 자격증명/제품 CLI/G1/G4는 다음 항목이다.
  - [ ] **`application-source-consumers`** — 선행: `application-services-ci`, 기존
    보호된 authority/supervisor/dispatcher와 소유 원천 조사·수집 계약.
    조사·검토·평가 RPC 소비와 수집 작업의 자동 발견/전경 소비를 작은 계약별로 구현하고,
    실제 Compose에 명시적 서비스 UID·SCRAM/개인 비밀·socket/artifact 경계를 연결한다.
    수용: 지역 접수→소유된 조사/수집/검토 진행·현재 보류 또는 완료 조회·재시작/권한 철회/
    socket/임대 복구와 전체 정리. fake CLI 증거와 실제 모델 호출/독립 해제·G1/G4는 분리한다.
    - [x] **`cli-dispatch-loop`** — 파일(5): `backend/app/cli_dispatch_loop.py`,
      `backend/app/process_stop.py`, `backend/app/deterministic_work.py`,
      `backend/tests/test_cli_dispatch_loop.py`, `contracts/cli-dispatch-loop-v1.md`.
      고정 authority endpoint/UID/계정으로 기존 RPC를 반복 소비한다. 응답 유실·불일치·
      미완결에는 다음 요청 없이 멈추고, 정상 대기·신호/FD 정리를 유지한다.
      수용: 실제 별도 Unix RPC 프로세스·대기 간격·한 번의 실패 후 추가 요청 없음,
      공통 신호 추출 뒤 기존 결정적 소비자의 실제 SCRAM 회귀. Compose/제품 CLI는 후속이다.
      [로컬 수용](../research/cli-dispatch-loop-implementation.md): 새19+기존17개/5.95초,
      실제 반복 Unix RPC·불확실성 중단·신호/FD 정리와 기존37개/126.61초 실제 SCRAM 회귀.
      일반 계정 UID의 합성 소프트웨어 증거이며 hosted/source Compose·제품 CLI는 후속이다.
    - [x] **`collection-consumer`** — 파일(4): `backend/app/deterministic_job_discovery.py`,
      `backend/app/collection_consume.py`, `backend/tests/test_collection_consumer.py`,
      `contracts/collection-consumer-v1.md`. 같은 계정의 처리 가능한 소유 수집만 발견하고
      기존 임대/부모·원천 검증/원자 저장을 반복 호출한다. 고정 타입·권한·페이지/대기와
      종료/복구를 유지한다. [실제 SCRAM 수용](../research/collection-consumer-implementation.md):
      새34+기존47/14개, 합계95개/55.97초·무건너뜀; 자동 완료·취소·강제 종료 뒤 복구·
      부모 증거 훼손 보류·권한 철회·신호/프로세스/DB 정리. 목록 회귀12개/6.48초도 통과.
      `394ff78` 전체 hosted2,489/무건너뜀·UID4·작성141·웹160/51·C0/앱과 정리도 통과했다
      ([기록](../research/runtime-consumers-hosted-regression-20261004.md#collection-consumer-regression-at394ff78)).
      source Compose/실제 모델/독립 해제·G1/G4는 별도이며 상위 체크를 유지한다.
    - [x] **`collection-services-ci`** — 선행: `collection-consumer`, `application-services-ci`.
      파일(6): `compose.collection.yaml`, `scripts/check-application-runtime.py`,
      `scripts/application-collection-fixture.py`, `.github/workflows/application-runtime.yml`,
      `contracts/collection-compose-runtime-v1.md`, `backend/tests/test_application_collection_fixture.py`.
      기존 collector를 실제 소비자로 교체하는
      명시적 override와 사설 합성 부모 fixture를 연결한다. 수용: 실제 Docker/TLS/SCRAM
      수집 접수→자동 저장→현재 기록·재시작/동일 판본·부모 철회/권한 변화·UID/자원/정리.
      같은 writer 권한 공유와 fake CLI 범위를 기록하며 authority/supervisor Compose와
      실제 모델/독립 해제·G1/G4 체크를 대체하지 않는다.
      [`098d1d3` 실제 수집 단계 수용](../research/collection-compose-runtime-implementation.md):
      TLS/SCRAM 자동 원본3개 저장·동일 재시작/한 시도·부모 철회422·권한 변화503/소비자exit3·
      실제 UID/메모리/CPU/사설 마운트와 전체 정리. 전체 workflow는 뒤의 authority 실패로 미수용이다.
    - [x] **`authority-services-ci`** — 선행: `cli-dispatch-loop`, `application-services-ci`.
      파일(6): `compose.authority.yaml`, `scripts/check-application-runtime.py`,
      `scripts/application-authority-fixture.py`, `.github/workflows/application-runtime.yml`,
      `contracts/authority-compose-runtime-v1.md`, `backend/tests/test_application_authority_fixture.py`.
      고정 tenant·실제 별도 UID/SCRAM/소켓과
      키/원문 경계를 연결해 지역 접수가 서버의 현재 보류로 자동 닫히게 한다.
      수용: 실제 TLS 접수·서명/캡처/보류 조회·잘못된 peer/사설 파일 거부·소켓 정리/재시작·
      권한 변경 후 dispatcher 중단·전체 정리. fake CLI와 controller 소유 키/계정 및
      같은 supervisor UID의 자식이라는 한계를 보존한다. 제품 CLI/독립 custody/G1/G4는 후속이다.
      [`b8df8f9` 실제 수용](../research/authority-compose-runtime-implementation.md#corrected-actual-hosted-acceptance):
      표준 TLS 지역 접수→자동 검증 보류/결정·캡처·서명 각1개와 공개 보고서·소유 수집 거부422·
      사설 파일/잘못된 UID 거부·실제 자원/마운트·소켓 제거/동일 재시작·권한 변화503/dispatcher exit3·
      모든 정리 통과. 합성 factory 집중1/3.96초도 통과했다. `d19f7c0`의 전체 새 판본 회귀는 위 고정 기록에서 수용했고 결합 원천 경로는 미수용/보류다.

**운영 조립 체크포인트:** 구성/발견/루프의 실제 프로세스 시험 뒤 앱 이미지 기동을 확인하고,
같은 판본의 전체 CI가 끝난 뒤 `end-to-end-g1`의 실제 CLI·독립 증거와 브라우저 경로를 검증한다.
보호된 최대 손익분기 전체 경로는 75분 27초에 완료했다. 새 운영 구성·서비스 조립과
별도 최대 취소/복구/원천 철회·동시 처리량 수용은 계속 구분해 검증한다.
2026-10-03 재개 후 기존 CI 집계 실패의 [목록 안정화 수정](../research/backend-inventory-repeatability-implementation.md)을
기록했다. 집중 18개와 기본 목록 2,436개의 여섯 동일 수집은 통과했고, 같은 head의
전체 실행·집계도 `4867c1f`에서 통과했다: 백엔드 2,436개·별도 UID 4개·
모든 동일 목록/집계·정리, 작성 141회·웹 160/51·C0. 앱 서비스 조립과 실제 제품 CLI는 후속이다.

## 기존 구현 진행 기록

**완료 계산의 웹 평가 연결 (2026-10-01):** [06 계산 평가](../contracts/web-calculation-assessment-v1.md)는 기존 열·경제 작업 ID를 서버 검증 접수에 연결하고, 저장된 보류 근거를 조회·재연결한다. 웹 단위 93개, 집중 Chromium 6개와 실제 HTTPS/PostgreSQL 16.15/SCRAM·시험용 CLI 연결 1개가 통과했다([기록](../research/web-calculation-assessment-implementation.md)). 운영자 식별자 입력 경로이며 일반 지역 흐름·작성 Run 웹 경제/평가 부모 선택·실제 제품 CLI·독립 해제·G1은 후속이다. 전체 `web-shell`/`end-to-end-g1` 체크는 유지한다.

**필수 모델 변경 (2026-10-01):** [명시적 DB 이전·되돌리기](../contracts/cli-model-policy-migration-v1.md), 새 실행 검증과 개발 설정을 변경했다([161개 집중 시험](../research/cli-model-migration-implementation.md)). 과거 완료 항목의 모델명은 실제 실행 이력이며 보존한다. 새 모델의 제품 CLI·독립 해제·G1/G4 수용 체크는 유지한다.

**지역 조사→수집→입력 검토 웹 연결 진행 (2026-09-30):** 완료된 조사 작업의 ID로 기존 인증 원본 수집 API를 접수하고, 완료된 수집 ID로 기존 입력 검토 API를 접수하는 내부 화면 후보를 추가했다([계약](../contracts/web-owned-source-workflow-v1.md), [검증](../research/web-owned-source-workflow-implementation.md)). 단계별 실제 작업 상태와 검토 보류를 조회하며 응답 유실 때 같은 멱등 키를 유지한다. [저장 조사·수집·검토 이력](../research/owned-source-history-implementation.md)은 재연결 뒤 페이지별로 다시 찾는다. 실제 CLI·독립 출처/해제 증거, 자동 연결과 전체 `source-collection-worker`/`web-shell`/`end-to-end-g1` 수용은 남아 체크를 유지한다.

**작성 농장 웹 작업 연결 진행 (2026-09-30):** 기존 판본 조회·검토/계산 접수·서버 상태 확인·완료 Run 3D 이동에 더해 직접 작성한 가정과 권리 선언의 불변 등록 폼을 연결했다([증거](../research/authored-farm-web-workflow-implementation.md)). 사용자별 등록 판본의 서버 목록·커서와 단건 권리 재검사 선택도 추가했다([목록 증거](../research/authored-farm-catalog-implementation.md)). 같은 판본의 검토·계산 작업 이력 후보와 재연결 뒤 현재 권리/상태 재확인도 연결했다([작업 이력 증거](../research/authored-farm-activity-implementation.md)). [완료 Run 전체 목록 후보](../research/authored-run-catalog-implementation.md)는 저장 ID만 반환하며 웹에서 농장 선택 없이 찾고 현재 단건 조회 후 3D로 이동한다. 선행 조사·원본·시장·경제 기록 발급을 자동화한 일반 사용자 흐름, 실제 CLI·독립 해제·전체 G1은 남아 `web-shell`/`web-replay`/`end-to-end-g1` 체크를 유지한다.

**작성 농장 → 저장 Run → HTTPS/Chromium 합성 연결 진행 (2026-09-30):** 브라우저 작성 폼의 신규 등록 POST부터 신규 검토 작업 접수, 가짜 CLI 검토·합성 서명 해제, 신규 계산 작업 접수·실제 작업자 게시와 저장 Run 3D까지 로컬 PostgreSQL 16.15/SCRAM·HTTPS/Chromium 시험이 통과했다([증거](../research/authored-full-software-path-implementation.md)). 호스팅 백엔드 CI는 확인 중이다. 실제 CLI·독립 해제·사용자 원천 수집 입력·접수 지연 개선의 전체 G1 체크는 유지한다.

**작성 Run 접수 API 진행 (2026-09-30):** [계약](../contracts/api-authored-simulation-admission-v1.md)에 따라 현재 해제·농장 입력·최종 궤적을 확인한 후 인증된 작업 접수를 추가했다([로컬 검증](../research/api-authored-simulation-admission-implementation.md)). 실제 HTTPS/SCRAM CI와 신규 작업자 완료, 제품 CLI/독립 G1 수용 체크는 유지한다.

**작성 입력 검토 API 진행 (2026-09-30):** [계약](../contracts/api-farm-authored-review-v1.md)은 등록 해시·현재 권한·두 열 궤적을 재확인해 인증된 검토 작업을 접수한다([로컬 증거](../research/api-farm-authored-review-implementation.md)). SCRAM CI와 실제 CLI/독립 해제/G1 수용 체크는 유지한다.

**로컬 합성 3D 데모 제공 (2026-09-30):** [실행법](../web/README.md#지금-3d를-직접-보기)의 한 명령으로 직접 작성한 시험 응답을 3D·그래프·표에서 조작할 수 있다([브라우저 검증](../research/local-synthetic-3d-demo-implementation.md)). 실제 Run을 쓰는 전체 `web-replay`/G1/G4 체크는 유지한다.

**작성 농장 입력 API 진행 (2026-09-30):** [계약](../contracts/api-farm-authoring-v1.md)의 인증 접수·재조회와 표준 런타임 조립을 추가했다. OpenAPI/권한 로컬 검사는 통과했고 실제 SCRAM 시험은 CI 확인 대기 중이다. 사용자가 직접 쓰는 작성 폼, 실제 제품 CLI와 독립 G1 수용 체크는 유지한다.

**작성 Run 표준 HTTPS 조립 진행 (2026-09-30):** [조립 계약](../contracts/api-runtime-authored-run-v1.md)에 운영자 제공 저장소·별도 키를 기존 작업/농장 서비스에 묶는 선택 경로를 추가했다. 로컬 단위 검사는 통과했고 [실제 저장 Run→HTTPS→브라우저 명시 시험](../backend/tests/web_authored_thermal_replay_smoke.py)을 CI에 추가했다. SCRAM/HTTPS/브라우저 결과는 CI 확인 대기 중이며 제품 CLI·독립 G1 체크는 유지한다.

**작성 3D 브라우저 연결 진행 (2026-09-30):** [화면 계약](../contracts/web-authored-thermal-replay-v1.md)은 작성 Run의 120시점을 실제 WebGL·그래프·표·요약에 연결했고 [합성 브라우저 시험](../research/web-authored-thermal-replay-implementation.md)을 통과했다. 표준 HTTPS 조립·실제 제품 CLI·독립 해제/G1·전체 `web-replay` 수용은 남아 체크를 유지한다.

**작성 simulation 작업자 진행 (2026-09-30):** [작업자 계약](../contracts/farm-authored-simulation-worker-v1.md)은 실제 임대와 Run/영수증/완료의 원자 거래, 취소·해제 변경·오류·만료 롤백을 합성 SCRAM으로 시험했다([기록](../research/farm-authored-simulation-worker-implementation.md)). 작성 입력 API/3D·제품 CLI/독립 G1 체크는 유지한다.

**작성 Run API 진행 (2026-09-30):** [읽기 계약](../contracts/api-authored-thermal-run-v1.md)은 완료 작업·Run·120시점 응답을 인증된 내부 앱에 연결했다([시험](../research/api-authored-thermal-run-implementation.md)). 표준 HTTPS 조립·브라우저 작성 3D·실제 CLI/독립 G1 체크는 유지한다.

**작성 simulation 접수 진행 (2026-09-30):** [접수 계약](../contracts/farm-authored-simulation-v1.md)은 현재 입력·해제·Run 준비 패킷을 고정한 멱등 simulation 작업을 등록한다([SCRAM 시험](../research/farm-authored-simulation-implementation.md)). 별도 조회·3D·제품 CLI/독립 G1 체크는 유지한다.

**작성 입력 Run 저장 경계 진행 (2026-09-30):** [저장 계약](../contracts/farm-authored-run-store-v1.md)의 불변 테이블·선택적 v8 권한과 합성 행 게시·재조회, 단독 커밋 거부를 추가했다([SCRAM 시험](../research/farm-authored-run-store-implementation.md)). 실제 입력 접수·작업자는 아직 없다. 작성 입력 3D·실제 CLI/독립 G1 체크는 유지한다.

**작성 입력 Run 준비 진행 (2026-09-30):** [준비 계약](../contracts/farm-authored-run-preparation-v1.md)은 현재 저장 해제·농장 판본을 재검사하고 120단계의 최종 두 궤적·해시·식별자를 만든다([집중 시험](../research/farm-authored-run-preparation-implementation.md)). 게시·작성 입력 3D 연결, 실제 제품 CLI와 독립 해제/G1은 남아 있다. 기존 수용 체크는 유지한다.

**첫 내부 3D 열 재생 부분 구현 (2026-09-30):** [재생 계약](../contracts/web-thermal-replay-v1.md)에 따라 실제 장면·그래프·표·여섯 수치의 저장 시각을 연결했다([검증 기록](../research/web-thermal-replay-implementation.md)). 다음은 같은 농장 계획의 열·경제 완료 기록을 공통 Assessment에 연결하는 부분 작업이다. 전체 `web-shell` 선행·`web-replay`/G1/G4 수용은 남아 기존 체크를 유지한다.

**농장 경제 실행 연결 진행:** [경제 실행 계약](../contracts/farm-economic-execution-v1.md)은 경제 입력/영수증 v2가 같은 계획과 실제 완료 열 작업을 참조하도록 한다([검증 기록](../research/farm-economic-execution-implementation.md)). [첫 내부 3D 열 재생 뷰어](../contracts/web-thermal-replay-v1.md)도 부분 구현했으며, [우선순위](plan.md)에 따라 공통 Assessment에 앞서 저장된 Run을 장면·그래프·표로 확인한다. 전체 작성·실제 CLI/독립 G1/G4와 기존 작업 체크는 유지한다.

**농장 계획 열 실행 연결 진행:** [열 실행 계약](../contracts/farm-thermal-execution-v1.md)은 접수·작업자·작업별 Run 조회의 입력/영수증 v3가 같은 등록 계획과 완료 조사/수집/검토를 참조하도록 한다. [검증 기록](../research/farm-thermal-execution-implementation.md)은 실제 SCRAM·HTTPS와 가짜 CLI/합성 키의 소프트웨어 범위다. 공통 평가·3D·실제 CLI와 독립 전체 G1/G4 수용은 남아 기존 체크를 유지한다.

**저장 경제 가정 조회 연결 진행:** [조회 계약](../contracts/api-market-user-source-read-v1.md)은 같은 사용자의 7종 입력 목록·지정 판본을 기존 최초 작업/원본 해시와 대사한다. [구현 증거](../research/market-user-source-read-implementation.md)는 실제 SCRAM·Bearer의 소프트웨어 범위다. 숫자·단위·null을 보존하며 경제/시장 입력 화면·실제 모델·전체 G1/G4 수용이 남아 기존 체크를 유지한다.

**첫 웹 접수·조회 연결 진행:** [계약](../contracts/web-location-shell-v1.md)과 [검증](../research/web-location-shell-implementation.md)은 좌표/UTC 기간 요청·작업/보류 근거, 실제 TLS/SCRAM 브라우저와 가짜 CLI의 소프트웨어 범위다. 경제/시장 입력·카드, 지도, 3D·실제 모델·전체 G1/G4 수용이 남아 `web-shell` 및 기존 체크를 유지한다.

**공유 CLI 계약 조립 진행:** [실제 세 서비스 구성](../contracts/owned-cli-contracts-v1.md)과 [집중 검증 기록](../research/owned-cli-contracts-implementation.md)은 같은 저장소/등록부를 확인하는 소프트웨어 범위다. 실제 CLI·독립 검토/해제·전체 G1 수용까지 기존 체크를 유지한다.

**계산 완료 → 최종 보류 평가 연결 진행:** [평가 접수·검증 계약](../contracts/calculation-assessment-v1.md)은 실제 완료 열/경제 작업의 영수증·재계산·같은 서명 문맥을 다시 검사해 assessment 의도를 등록한다. 작물 프로필을 만들지 않으며 시장·공통 농장·현장·미래·대응 비교의 누락 사유를 기존 보류 조회로 제공한다. [구현 증거](../research/calculation-assessment-implementation.md)는 합성 키/가짜 CLI와 실제 SCRAM의 소프트웨어 범위다. 실제 CLI/독립 운영 조립·전체 농장/브라우저/G1/G4 수용까지 기존 체크를 유지한다.

**서명 문맥에 결합한 조사 연결 진행:** [고정 원본 조사 계약](../contracts/owned-research-v1.md)은 실제 등록 범위·원본·저장된 문맥을 접수/CLI 검증에 결합하며 초기 등록부의 보류와 과학적 주장 제한을 유지한다. [구현 증거](../research/owned-research-implementation.md)는 가짜 CLI·컨트롤러 키·실제 SCRAM의 소프트웨어 범위다. 실제 모델·독립 계획/운영 조립·자료/모델 채택·전체 브라우저/G1/G4 수용은 남아 기존 체크를 유지한다.

**수집·검토 HTTP 연결 진행:** [접수 계약](../contracts/api-owned-collection-v1.md)은 인증된 부모 UUID·멱등 키만 받아 기존 원본/문맥 검사와 원자 접수를 실행한다. [구현 증거](../research/api-owned-collection-implementation.md)는 합성 원천/키와 실제 SCRAM/Bearer의 소프트웨어 범위다. 실제 CLI·독립 운영 조립·자료 채택·전체 API/브라우저/G1/G4 수용은 남아 기존 체크를 유지한다.

**공유 CLI 계약 연결 진행:** [라우팅 계약](../contracts/cli-contract-router-v1.md)은 실제 단계·입력 판본·바이트 해시로 기존 서버 계약을 선택하고 검증기 판본·보류/게시 결과를 보존한다. [구현 증거](../research/cli-contract-router-implementation.md)는 실제 SCRAM 큐와 가짜 CLI의 소프트웨어 범위다. 미등록 입력은 호출 전에 보류하며 실제 모델·독립 운영 조립·전체 API/브라우저/G1/G4 수용은 남아 기존 체크를 유지한다.

**수집 원본 → 검토 연결 진행:** [연결 계약](../contracts/owned-collection-review-v1.md)은 실제 완료 수집 기록·조사 증거·서명 문맥을 다시 검사하고 스냅샷 후보와 새 검토 입력을 같은 거래로 저장한다. [구현 증거](../research/owned-collection-review-implementation.md)는 가짜 CLI와 합성 서명 키의 소프트웨어 범위다. 실제 CLI/독립 실행·해제·스냅샷 채택·전체 브라우저/G1/G4 수용까지 기존 체크를 유지한다.

**원본 수집 작업자 진행:** [수집 계약](../contracts/owned-fixture-collection-v1.md)은 완료 조사 결정·출력/검사 증거와 고정 원본을 재검증해 collection 의도를 등록하고 원본 기록·완료를 같은 거래로 게시한다. [구현 증거](../research/owned-fixture-collection-implementation.md)는 직접 작성한 합성 원본·가짜 CLI·실제 SCRAM/전경 프로세스의 소프트웨어 범위다. 실제 CLI·독립 격리/해제·수집 검토/스냅샷·브라우저/G0–G4 수용은 남아 체크를 유지한다.

**작업별 손익분기 완료 조회 진행:** [조회 계약](../contracts/api-job-break-even-result-v1.md)은 실제 완료 입력·영수증·게시·계획·재계산 결과를 대사해 기존 조건부 결과를 반환한다. [구현 증거](../research/api-job-break-even-result-implementation.md)는 합성 원천/키와 실제 SCRAM/Bearer의 소프트웨어 범위다. 자동 시험 가정·연속 해 증명·CLI/브라우저/G1/G4 수용은 남아 기존 체크를 유지한다.

**손익분기 수치 작업자 진행:** [작업자 계약](../contracts/break-even-calculation-worker-v1.md)은 서버가 접수한 불변 계획을 전체 재검증하고 기존 Decimal 격자 계산 결과·작업 완료를 한 트랜잭션에 저장한다. [구현 증거](../research/break-even-calculation-worker-implementation.md)는 실제 SCRAM 임대·취소·복구·롤백과 운영자 전경 실행의 소프트웨어 범위다. 작업별 결과 조회 연결 이후에도 자동 시험 가정·연속 구간 해 증명·CLI/브라우저/G1/G4 수용은 남아 기존 체크를 유지한다.

**손익분기 계획 HTTP 진행:** [접수 계약](../contracts/api-break-even-plan-v1.md)은 실제 저장된 시나리오의 권리·판본·고정 조건을 검증하고 서버가 만든 불변 계획을 simulation 의도로 저장한다. [증거](../research/api-break-even-plan-implementation.md)는 합성 원천/키와 실제 SCRAM/Bearer의 소프트웨어 범위다. 수치 작업자 연결 이후에도 자동 시험 가정 생성·연속 구간 해 증명·CLI/브라우저/G1/G4 수용은 남아 기존 체크를 유지한다.

**조건부 경제 계산 HTTP 진행:** [접수·완료 조회 계약](../contracts/api-economic-calculation-v1.md)은 실제 simulation 요청을 접수하고 불변 입력·게시 영수증·저장 원장을 대사해 기존 안전 결과를 반환한다. [구현 증거](../research/api-economic-calculation-implementation.md)는 합성 입력/키와 실제 SCRAM/Bearer의 소프트웨어 범위다. 전체 경제/손익분기·CLI/평가·브라우저/G1/G4 수용은 남아 기존 체크를 유지한다.

**조건부 경제 계산 작업자 진행:** [작업자/운영자 전경 실행 계약](../contracts/economic-calculation-worker-v1.md)은 고정 후보·시나리오/산식 판본을 실제 simulation 요청으로 받고 기존 Decimal 엔진으로 재계산한다. [소프트웨어 증거](../research/economic-calculation-worker-implementation.md)는 실제 임대·권한·결과/완료 원자성을 다룬다. 전체 경제/손익분기 작업·CLI/평가·브라우저/G1/G4 수용은 남아 기존 체크를 유지한다.

**조건부 경제 시나리오 HTTP 진행:** [등록 계약](../contracts/api-economic-scenario-v1.md)은 저장된 기준 입력·공통 충격을 검사하고 실제 요청·후보·수정 수치를 같은 거래로 저장한다. [구현 증거](../research/api-economic-scenario-implementation.md)는 합성 원천/키와 실제 SCRAM/Bearer의 소프트웨어 범위다. 전체 경제/손익분기 작업·CLI/평가·브라우저/전체 G1 수용은 남아 기존 체크를 유지한다.

2026-09-29 현재 **19개 완료, 20개 미완료**다. 각 작업은 한 번의 작업 세션에 다룰 수 있도록 제안했고, 지정 파일은 대체로 최대 다섯 개다. `decision-evidence-store`는 이전 작업의 시험을 새 검증 계약으로 이관해야 하므로 여섯 파일을 지정한다. `repo-bootstrap`의 잠금·설치·import 확인은 완료 증거이며, 앱 코드·시험·Compose가 필요한 아래 명령은 **후속 검증 절차**다. 해당 작업의 수용 증거를 기록한 뒤에만 체크한다. 외부 접근을 기다리는 상태는 완료가 아니다. 구현 전에 [기능 목록](../docs/IMPLEMENTATION_SLICE.md#6-범위-기능-목록과-구현-순서), [구현 순서](plan.md), [준비 현황](../docs/IMPLEMENTATION_READINESS.md)을 확인한다. 런타임 CLI의 정확한 모델·추론 강도는 전 과정에서 필수다.

- [x] **`repo-bootstrap`** — 선행: 없음. 예정 파일(5): `backend/pyproject.toml`, `backend/uv.lock`, `web/package.json`, `web/package-lock.json`, `.gitignore`. 설정·잠금 파일은 Git에 추적되고 `.gitignore`도 준비됐다. FastAPI `0.141.1`, Pydantic `2.13.5`, 개발용 pytest `9.1.1`과 React/ReactDOM `19.3.0`, Vite `8.3.1`, TypeScript `7.0.2`, Vitest `5.0.2`, React 타입 `19.3.0`을 고정했고 웹 검사·시험·빌드 스크립트를 정의했다. 수용 증거: 오프라인 캐시에서 `uv lock --check`, `uv sync --locked`, FastAPI/Pydantic import가 통과했고 `npm ci --strict-peer-deps`로 캐시의 43개 패키지를 설치했다. 이후 `node_modules`는 제거했다. 신규 온라인 의존성 설치나 앱 시험·자료형 검사·빌드 성공은 입증하지 않았다. 이 명령들은 해당 소스·시험을 만드는 후속 작업에서 확인한다.
- [x] **`compose-runtime`** — 선행: `repo-bootstrap`. 예정 파일(5): `compose.yaml`, `.env.example`, `backend/Dockerfile`, `web/Dockerfile`, `.dockerignore`. 수용: 모듈형 백엔드의 web/API/수집/CLI/수치 계산 별도 서비스·작업자 역할, PostgreSQL과 영속 POSIX 아티팩트를 정의한다. 빌드 문맥·Dockerfile을 명시하고 `.dockerignore`로 비밀·제한된 원본 자료를 제외한다. `depends_on`은 시작 순서만 보장하므로 DB `pg_isready` 건강 검사와 `service_healthy` 조건을 쓴다. `.env.example`은 비밀값 없이 두고 실행 시 비밀 파일/관리자로 서비스별 최소 권한을 주입하며 PostgreSQL은 `POSTGRES_PASSWORD_FILE`을 쓴다. 비밀·원본 자료를 저장소·이미지·로그에 넣지 않는다. 실제 검증한 이미지 버전·digest를 고정하고 PostgreSQL 18을 선택한다면 볼륨은 `/var/lib/postgresql`에 둔다. CLI 작업자에 Docker 소켓을 마운트하지 않는다. 확인: 부트스트랩 뒤 Docker/Compose 호스트에서 `docker compose config -q`로 비밀값 출력 없이 정식 모델 검증, 해당 단계 파일로 가능한 이미지 빌드, 앱 소스 없이 PostgreSQL 기동·`pg_isready`·컨테이너 재생성 뒤 데이터 보존 시험. 앱 명령·건강 확인 끝점은 소스 구현 뒤 정한다. web/API/작업자 전체 기동·복구·CLI 세 단계·UI는 후속 작업이다. 장기 실행 CLI 서비스 정의는 작업별 비특권 컨테이너·임시 파일시스템·제한된 외부 통신의 G4 증거가 아니다. 수용 증거: 로컬 standalone Compose `v5.5.1`의 기본·`app` 프로필 `config -q`가 통과했다. [GitHub Actions C0 run 36303540834](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/36303540834) (커밋 `41cb865`)에서 Docker/Compose의 기본·`app` 구성, web/API 의존성 이미지 빌드, 고정 PostgreSQL 18.6 이미지의 건강 확인·`pg_isready`, DB 컨테이너 재생성과 `c0-persisted` 행 보존, 비밀·볼륨 정리가 모두 성공했다. 현재 호스트에 Docker Engine은 없으며 앱 역할 기동·작업자 복구·G1은 후속 작업이다.
- [x] **`provenance-g0`** — 선행: `repo-bootstrap`. 변경 파일(4): `backend/app/provenance.py`, `backend/app/gates.py`, `backend/tests/test_provenance.py`, `backend/tests/test_gates.py`. 내용 해시로 결합한 출처 ID·원본 SHA-256, 제품/버전·시각·단위·QC·권리·합성 표시를 고정했다. 서버 소유 저장소 인터페이스가 승인 정책·원본·원천/검사/권리 증거를 조회한 범위에서만 G0 `pass`를 계산하고, 합성·누락·변조·미승인·시간/범위 불일치에는 사유가 있는 `hold`를 만든다. 독립 xhigh 감사의 관측시각·인코딩된 URL 구분자·잘못된 ID 반사 결함을 RED→GREEN으로 보완했다. 수용 증거: `cd backend && uv run --locked --no-sync pytest -q tests/test_provenance.py tests/test_gates.py`에서 **101 passed**. 시험 저장소의 `pass`는 실제 원천 G0 승인 증거가 아니다. 인증·테넌트·영속 승인 저장소는 `g0-authority-store`, 실제 제공자 권리·판본은 원천별 G0에서 검증한다. 아카이브 증거 없는 `retrieved_at > decision_at`은 보류한다.
- [x] **`thermal-synthetic-parameters`** — 선행: `provenance-g0`. 변경 파일(5): `fixtures/synthetic-thermal-parameters-v1.json`, `fixtures/manifest-v2.json`, `fixtures/README.md`, `contracts/thermal-sources.md`, `backend/tests/test_thermal_parameter_fixture.py`. 공식 NWS PDF의 포화압 식·hPa 단위와 BIPM의 K/°C·hPa/Pa 변환을 정확한 CLI `gpt-6-sol`/`xhigh` 조사·별도 독립 검토 세션 `01a0e210-df86-7e10-8c8e-d29a946c0e7d`으로 대조했다. 공식 법칙의 발표일·정확도·정의역은 미상이며 `289–293 K`는 합성 시험 가정으로만 쓴다. 시설·초기 상태·제어·60초 substep과 실행 전 잔차/반걸음 한계를 출처 또는 가정·단위·판본으로 등록했다. 기존 weather/economics v1 원본과 manifest v1은 바꾸지 않았다. manifest v2가 열 fixture 23,380바이트의 SHA-256 `a2254564e1c3f72290d65d40222e62a23e50407969d12e049a345582aa45f77f`를 고정하고 자체 해시는 담지 않는다. 수용 증거: RED→GREEN, 관련 시험 **120 passed**, 독립 식·차원/수치·권리 범위 검토, 원본 핀과 `git diff --check` 재확인. 독립 검토는 이전 fixture/manifest 바이트에만 결합되며 서버 입력 링크·엔진 연산순서·실제 G0/G1/현장 정확도는 계속 `hold`다.
- [x] **`thermal-contract`** — 선행: `provenance-g0`, `thermal-synthetic-parameters`. 변경 파일(4): `contracts/thermal-v1.md`, `contracts/thermal-v1.schema.json`, `contracts/thermal-sources.md`, `backend/tests/test_thermal_contract.py`. 단일 구역 열·수증기, 출처·단위·제어·적분·잔차의 합성 trace 계약을 확정했다. 관측이 없는 합성 원천은 명시적 `null`과 별도 가상 적용 기간으로 표현하고, 2개 인접 시간의 원본 해시·필드별 단위 지도·등록 계산 규칙과 입력 ID·이전 trace 상태 이월을 검사한다. arbitrary 단위와 잘못된 규칙 ID 반례를 RED→GREEN으로 막았다. 수용 증거: 정확한 CLI `gpt-6-sol`/`xhigh` 구현 세션 `01a0e23f-749a-79a2-aa59-a459527f7837`, 독립 재감사 `01a0e245-0da7-7e12-b3d7-809226973ed7`, 관련 계약·매개변수·fixture 시험 **258 passed**, manifest v1/v2 원본 바이트 해시 대조와 `git diff --check`. 이 수용은 구조·출처 연결 계약에 한정한다. 결정적 엔진·서버 링크·실제 G0/G1 Run과 현장 정확도는 후속 작업 및 관문이다.
- [x] **`fixture-policy`** — 선행: `thermal-contract`. 변경 파일(5): `fixtures/README.md`, `fixtures/synthetic-weather-v1.json`, `fixtures/synthetic-economics-v1.json`, `fixtures/manifest-v1.json`, `backend/tests/test_fixture_policy.py`. 직접 작성한 합성 기상과 당일 출하·검수 경제 원장의 작성자·방법·권리·단위·시각 의미를 명시하고 원본 바이트를 SHA-256으로 고정했다. 사용자 수요·공급·거시 값은 자료 유래 전망이 아닌 가정이다. 수용 증거: 선행 열 계약 독립 재감사 후 관련 전체 시험 **258 passed** 중 fixture 정책 **30 passed**, manifest v1/v2 원본 바이트 길이·해시 재계산 일치. weather/economics v1과 manifest v1 원본은 변경하지 않았고, 합성 입력은 실제 G0/G2/G3 증거가 아니다.
- [x] **`db-driver-bootstrap`** — 선행: `repo-bootstrap`. 변경 파일(2): `backend/pyproject.toml`, `backend/uv.lock`. Psycopg `3.3.6`/`psycopg-binary` `3.3.6`을 런타임에, Draft 2020-12 스키마 시험용 `jsonschema` `4.26.0`을 처음 dev 그룹에 잠갔고, 후속 G1 승인 trace의 런타임 검증을 위해 같은 판본을 런타임 의존성으로 옮겼다. 수용 증거: `uv lock --check`, `uv sync --locked --group dev`, 두 라이브러리 import가 통과했고, 사용자 로컬 PostgreSQL 16.15 Unix 소켓에 Psycopg로 연결해 버전과 `numeric` 계산을 확인했다. Compose PostgreSQL 18.6·앱 역할 권한·서비스 복구는 이 결과로 입증하지 않았다. 비밀을 설정·잠금 파일이나 시험 로그에 넣지 않았다.
- [x] **`durable-jobs`** — 선행: `compose-runtime`, `db-driver-bootstrap`. 변경 파일(5): `backend/app/db.py`, `backend/app/job_store.py`, `backend/app/jobs.py`, `backend/tests/test_jobs.py`, `backend/tests/test_job_recovery.py`. PostgreSQL에서 `(tenant, stage, input hash, key)` 중복 제출, 임대·만료·재시도·취소, 내용주소 아티팩트와 트랜잭션 게시를 검증했다. 결정적 수집·시뮬레이션은 AI 결정 없이, AI 세 단계는 결정 참조와 함께 게시하며 완료 결과를 덮지 않는다. 수용 증거: 실제 로컬 PostgreSQL 16.15에서 `OSSF_TEST_PG_DSN=… uv run --locked --group dev pytest -q tests/test_jobs.py tests/test_job_recovery.py` **35 passed**, `git diff --check`; 손상 입력 격리와 재시작·충돌·부분 게시 시험 포함. 이는 게시 메커니즘의 수용이다. 임의의 결정 해시를 실제 CLI 출력·검사와 결합하는 일, 시도별 종료·원문 감사, 고아 아티팩트 안전한 정리, 운영 PostgreSQL 18 앱 권한·격리는 각각 `decision-evidence-store`·`cli-worker`·G4에서 확인한다.
- [x] **`decision-evidence-store`** — 선행: `durable-jobs`. 변경 파일(6): `backend/app/db.py`, `backend/app/job_store.py`, `backend/tests/test_job_evidence.py`, `backend/tests/test_job_recovery.py`, `backend/tests/test_jobs.py`, `contracts/decision-evidence-v1.md`. 커밋 `bee69fc`에서 시도별 프롬프트·출력 스키마·최종 출력·JSONL/도구 사건·서버 검사 보고서의 불변 증거와 종료 사유를 테넌트·시도 ID에 결합했다. 서버 소유 권리/보관 판정이 제한 원문과 해시 공개를 통제하고, 인증 principal의 메타데이터·감사·아티팩트·취소 범위를 분리했다. 실제 출력·검사 보고서 해시 및 결정을 재확인한 성공 게시만 허용한다. RED→GREEN 권한 회귀 후 로컬 PostgreSQL 16.15 집중 시험 **63 passed**, 독립 CLI `gpt-6-sol`/`xhigh` 감사 2회에서 저장 계약 차단 문제 없음. 저장된 CLI 식별 문자열은 실제 실행 증명이 아니다. 단계 제한·검증된 hold 보고서·실행 사건 결합은 다음 `cli-worker-store-bridge`; 실제 CLI와 G0/G4는 별도 보류다.
- [x] **`backend-ci`** — 선행: `compose-runtime`, `db-driver-bootstrap`. 변경 파일(1): `.github/workflows/backend-tests.yml`. 수용: PR/main의 호스팅 러너가 고정된 uv/Python과 Compose의 PostgreSQL 18.6 이미지 digest로 전체 백엔드 시험을 실제 DB에 연결해 실행한다. 매 실행 임시 비밀번호는 파일로 전달하고 로그·DSN에 넣지 않으며 DB 포트는 loopback 무작위 포트다. 종료 시 DB와 비밀 파일을 지운다. 정적 YAML/shell 검사 외에 실제 Actions 실행의 통과와 DB 시험 미건너뜀을 확인해야 체크한다. 이 결과는 앱 역할의 운영 격리나 G1 전체 경로 증거는 아니다. 수용 증거: 최초 Actions 실행 `36312871330`은 러너에 `rg`가 없어 시험 전에 실패했고 `grep`으로 수정했다. [Actions 실행 36312898250](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/36312898250)은 PostgreSQL 18.6 실제 연결·백엔드 **744 passed, 0 skipped**·DB/비밀 정리 성공을 기록했다. 독립 CLI `gpt-6-sol`/`xhigh` 정적 감사와 YAML·shell 구문 검사도 통과했다.
- [x] **`cli-worker-store-bridge`** — 선행: `decision-evidence-store`; 후속: `cli-worker`. 변경 파일(5): `backend/app/db.py`, `backend/app/job_store.py`, `backend/tests/test_job_evidence.py`, `backend/tests/test_job_recovery.py`, `contracts/decision-evidence-v1.md`. 허용된 AI 단계만 단일 PostgreSQL 임대 트랜잭션에서 점유하고, 서버 검증을 통과한 `hold` 보고서를 성공 게시와 구분해 불변·테넌트 범위로 보관한다. 시도 ID에 결합한 CLI 기동·JSONL·최종 출력·종료 사건 또는 권리상 원문 보관 보류를 검사하며 누락·변조·늦은 기록, 실패·취소의 가짜 보류를 거부한다. 수용 증거: 실제 로컬 PostgreSQL 16.15의 관련 시험 **107 passed**, 실제 Codex CLI 0.157.1 JSONL 출력 형식 smoke, 독립 `gpt-6-sol`/`xhigh` 감사; [호스팅 백엔드 CI 36315895271](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/36315895271)의 PostgreSQL 18.6 **806 passed, 0 skipped**. 저장 계약 수용이며 제품 작업자의 실제 실행·신뢰 실행 증명·G4 격리는 후속이다.
- [x] **`job-intent-idempotency`** — 선행: `durable-jobs`; 후속: `api-flow`. 변경 파일(4): `backend/app/db.py`, `backend/app/job_store.py`, `backend/tests/test_job_idempotency.py`, `backend/tests/test_jobs.py`. `(tenant, stage, idempotency_key)` 유일 제약 아래 같은 키·정규화 입력 재요청은 원래 작업 ID를 돌려주고 다른 입력은 충돌로 거부한다. 동시 요청·테넌트/단계 범위를 검증했다. 기존 DB에는 owner가 앱 시작 전에 `upgrade_job_intent_key`를 트랜잭션으로 실행하며, 중복된 과거 의도가 있으면 임의 병합 없이 중단한다. 수용 증거: 로컬 PostgreSQL 16.15 순차·동시·업그레이드 RED→GREEN 관련 시험 **113 passed**, 독립 CLI `gpt-6-sol`/`xhigh` 재감사 수용, [호스팅 백엔드 CI 36316629677](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/36316629677)의 PostgreSQL 18.6 **812 passed, 0 skipped**. HTTP 409 매핑·운영 업그레이드 실행은 `api-flow`·G4에서 확인한다.
- [x] **`g0-authority-store`** — 선행: `provenance-g0`, `durable-jobs`. 변경 파일(5): `backend/app/g0_store.py`, `backend/app/g0_authority.py`, `backend/tests/test_g0_store.py`, `backend/tests/test_g0_authority.py`, `contracts/g0-evidence-v1.md`. 수용: 서버가 승인한 정책 판본, 원본 내용주소와 불변 출처 ID, 권한 있는 검토자의 원천·변수별 프로젝트 검사·용도별 권리 증거를 테넌트/제품/버전/지점/원본 해시/유효시각에 결합해 영속 보관한다. 요청자가 만든 정책·증거 문자열·검토자 표시는 G0 통과 근거가 아니다. 누락·변조·취소·만료·다른 용도/테넌트·오래된 정책에서 보류하고, 승인 기록 변경은 덮어쓰지 않고 새 판본을 만든다. 원본 바이트와 비밀은 저장소 밖의 권한 제한 저장소에 두며 실제 제공자 권리 승인 자체는 후속 원천별 작업에서 확인한다. 사용자 로컬 PostgreSQL 16.15의 동시성·재시작/불변성 시험은 가능하지만 Compose 18.6·실원천 G0 수용을 대신하지 않는다. 수용 증거: 독립 CLI `gpt-6-sol`/`xhigh` 재감사에서 자기 기입 QC·권리·누락된 필수 시각을 통한 오승인 경로를 수정한 계약으로 통과했고, 로컬 PostgreSQL 16.15 집중 시험 **26 passed**를 재실행했다. `ReviewProof`는 서버의 독립 검토 저장소가 제공해야 하며 시험의 가짜 resolver가 낸 `pass`는 실제 제공자 G0 승인이 아니다.
- [ ] **`cli-worker`** — 선행: `cli-worker-store-bridge`, `provenance-g0`. 예정 파일(5): `backend/app/cli_worker.py`, `backend/app/cli_contracts.py`, `contracts/decision-v1.schema.json`, `backend/tests/test_cli_worker.py`, `backend/tests/test_cli_contracts.py`. 수용: 격리된 작업자가 셸 문자열이 아닌 인자 배열로 `codex exec`를 호출한다. 정확한 `gpt-6.1-sol`/`xhigh`, 읽기 전용 작업 입력, `research`·`collection_review`·`assessment` 단계별 구조화 출력을 사용한다. 서버가 스키마·증거 ID·소유권·출처 권리·보류를 검사한다. 버전·프롬프트/입출력 해시·JSONL/도구 이벤트·시도·사용량·종료 이유를 보존하고 재시도마다 새 시도 ID를 만들고, 실제 검증 출력이 있을 때만 새 decision ID를 만든다. 로컬 실제 CLI 스키마 간단 실행이 성공해야 체크할 수 있다. 확인: 해당 pytest 파일과 기록된 실제 CLI 단계 호출; 인증·스키마·권리 문제는 대체 모델이 아니라 보류 또는 통제된 실패로 처리한다. 진행 증거: 커밋 `e436f9a`/`a9a2a7f`의 실제 subprocess·단계별 서버 검증 후보, 로컬 PG16 집중 시험 **23 passed, 0 skipped**, 보정 전 로컬 실제 CLI 세 단계의 검증된 `hold` smoke. 독립 xhigh 감사의 격리/프로세스/권한 지적을 코드 범위에서 보완했고, 제품 격리·도구/egress 제한·신뢰 실행 증명이 없어 기본 생성자가 차단된다. 체크는 유지한다. 추가 증거: `scripts/run-cli-smoke.sh --check`는 CLI·권한·PG를 모델 호출 없이 검사했고, `--run`은 개인 임시 Codex 홈에서 보정 후 실제 CLI 세 단계를 모두 실행해 각 단계의 검증된 `hold`·0 종료·JSONL/최종 출력 해시·decision ID를 확인했다([비밀 제거 기록](../research/cli-worker-posthardening-smoke.md), 1 passed, 입력 42,940·출력 538토큰). 이는 개발용 합성 subprocess 증거다. 제품 작업별 격리·독립 실행 증명·운영 계정은 여전히 보류하며 기본 생성자 차단과 작업 미체크를 유지한다.
  - 로컬 `bubblewrap`의 최소 네임스페이스에서 자격증명·모델 호출 없이 Codex 실행 파일의 버전 조회만 성공했다([관측 기록](../research/cli-isolation-feasibility.md)). 이는 격리 방식 채택이나 외부 통신 제한 증명이 아니며 `cli-worker` 수용 상태를 바꾸지 않는다.
  - 실제 CLI 한 번의 합성 열 `collection_review`가 서버 계약 검증을 통과하고, 시험용 독립 실행 검증기·해제 서명 아래 두 trace Run까지 연결됐다([비밀 제거 기록](../research/thermal-cli-review-smoke.md)). 실제 subprocess·결정·게시 연결의 국소 증거이나 운영 격리·독립 권한·연구/평가 단계·웹 종단 간 경로는 입증하지 않아 체크는 유지한다.
  - [정확한 CLI 설계 검토](../research/execution-boundary-cli-review.md)에 따른 [서명된 실행 완료 기록 후보](../contracts/cli-execution-attestation-v1.md)는 Ed25519 공개키 검증과 PostgreSQL 불변/nonce 제약을 통해 JobStore의 입력·기동·캡처·결정에 결합한다. 추가 정확한 CLI 검토 뒤 실제 자식 프로세스가 받은 stdin 프롬프트·출력 스키마 바이트 해시도 서명 필드에 넣고 invocation/launch 기록과 대조한다. 서로 다른 바이트를 보존·실행한 fake CLI 회귀 시험을 포함한 집중 19개 시험이 통과했다. `CliProcessSupervisor` 프로세스 관측 코어의 fake CLI 성공·시간 초과·늦은 폴링·미완료 자식 정리·별도 로컬 프로세스 실행 5개 시험도 통과했다. 이 관측 코어만으로는 별도 서비스·서명 발행기·작업자 연결을 입증하지 않았다; 후속 IPC 후보는 아래에 기록한다. 로컬 fake CLI/시험키와 요청 역할 금지 시험은 소프트웨어 경계만 검증한다. 별도 계정의 실제 프로세스 감독자·비밀키/운영 DB 역할·독립 release가 없으므로 `cli-worker`와 실제 G1은 계속 보류다.
  - `ExecutionAttestationIssuer` 후보는 감독자가 실행 전 작업·시도·입력에 묶이고 저장된 호출과 서버 계약을 대조해 직접 기동한 뒤, 영속 캡처·원문·검증 결정이 관측값과 같을 때만 서명한다. 최종 작업 종료 전에 서명할 수 있지만 공개 검증기는 종료 상태도 요구한다. fake CLI/동일 프로세스 시험키의 PG16 통합 9개 시험은 세 AI 단계, 봉인 전 서명 거부, 입력/PID/JSONL 변경 거부, 동일 서명 재전송, Unicode 경로와 게시 전 서명의 비승인을 확인했다. 이 발행기 시험만으로 별도 서비스/키 격리·작업자 IPC·PG18 운영 역할을 수용하지 않아 체크는 유지한다.
  - 추가 정확한 `gpt-6-sol`/`xhigh` IPC 검토 뒤 감독자 Unix socket 서버·공개키 작업자 클라이언트·서명 전 pending 검증을 연결했다([계약](../contracts/cli-execution-attestation-v1.md#local-supervisor-ipc-candidate)). 작업자에 CLI 경로/자격증명/서명키를 주지 않고, 고정 테넌트 임대·세 AI 단계의 저장/서명/조건부 종료를 지원한다. 별도 로컬 프로세스 fake CLI/시험키 시험에서 UID/테넌트/바이너리 거부, 동시 시도 예약, 취소/연결 해제/시간 초과/정상 종료 정리, 누락/변조 서명·원문 거부, 캐시 서명의 취소 재검사를 확인한다. 로컬 PG16 백엔드 전체 **1,075 passed**(기존 Pydantic 경고 2개), 그중 IPC 신규 34개가 통과했다. 동일 OS UID·소유자 DB 시험이므로 독립 키/계정/PG18 권한·불변 배포·실제 모델 실행/열 release 수용을 뜻하지 않으며 실제 G1/G4 체크는 유지한다.
  - 정확한 CLI 검토의 DB 권한 요구에 따라 [실행 역할 정책 후보](../contracts/runtime-role-policy-v1.md)를 추가했다. 전용 비로그인 스키마 소유자와 새 request/worker/supervisor/authority 역할을 분리하고, 일반 역할의 증거 직접 읽기/쓰기·DDL·역할 상승을 막는다. PUBLIC 컬럼/전역·스키마 기본 권한과 외부 SECURITY DEFINER, 상속·grant option·허용 목록을 검사하며 실패 시 설치 거래를 되돌린다. 권한 정책 신규 **29개 시험**과 로컬 PG16 백엔드 전체 **1,104 passed**(기존 Pydantic 경고 2개)를 확인했다. 현재 감독자 IPC 작업자의 직접 DB 호출은 이 worker 정책으로 실행할 수 없으므로 신뢰 authority RPC와 실제 별도 로그인/계정 연결은 다음 필수 작업이다. 역할 정책 시험은 배포·G1/G4 수용이 아니다.
  - [authority RPC 후보](../contracts/authority-rpc-v1.md)는 일반 작업자가 DB·CLI 자격증명·서명키·입력/임대 토큰 없이 다음 작업 실행만 요청하게 한다. 신뢰 서버 안의 기존 실행기가 고정 테넌트 임대·입력/판단 검증·서명 검증·조건부 저장을 맡고, 서버 시작/호출 전에 실제 authority DB 역할과 전체 권한 정책을 검사한다. 별도 로컬 authority/감독자 프로세스와 제한된 SQL 역할·fake CLI/시험키로 세 AI 단계와 성공/보류, 외부 테넌트 큐 보존, 임의 요청 필드/UID/권한 변동 거부, 지연 프레임, 취소/연결 손실/정상 종료와 중복 임대를 시험했다. 긴 응답 대기를 포함한 RPC 신규 **32개 시험**과 로컬 PG16 전체 **1,136 passed**(기존 Pydantic 경고 2개)를 확인했다. 실제 로그인/운영 UID·키 분리, 경계 내 정확한 모델 실행·불변 배포·열 release/G1/G4 수용은 여전히 보류하며 체크를 유지한다.
  - [로그인 정책 v2 후보](../contracts/runtime-login-policy-v2.md)는 v1 NOLOGIN 요구를 유지하면서 명시적 새 정책으로 LOGIN/NOINHERIT·무상속 역할을 만들고, 별도 비밀 제공 전에는 PASSWORD NULL로 둔다. JobStore와 감독자 읽기의 모든 v2 연결에서 실제 SCRAM·최초 로그인/세션/현재 역할·DB 범위를 확인한다. 관리자 역할 바꾸기, 잘못된/없는 비밀번호, 인증 생략 응답, 로그인/권한 변동과 반복 설치를 거부했다. 별도 DB 사용자·같은 OS UID의 authority/감독자와 fake CLI/시험키로 세 AI 단계의 저장을 확인했다. 로그인 신규 **25개 시험**과 로컬 PG16 전체 **1,161 passed**(기존 Pydantic 경고 2개)가 통과했고, 기존 로컬 DB 인증 설정을 바꾸지 않은 임시 DB를 정리했다. authority 자격증명 보유자의 직접 SQL 가능성도 시험/기록했다. 운영 UID·키/자격증명 소유권 분리, TLS/HBA/배포·실제 모델/열 release·G1/G4 수용은 보류하며 체크를 유지한다.
  - [콘텐츠 접근 정책 후보](../contracts/content-access-v1.md)를 추가해 authority 소유 콘텐츠에 명시적 감독자 그룹 읽기를 허용한다. 열린 파일/디렉터리의 UID·그룹·정확한 모드·ACL·해시를 검사하고 기존 권한을 자동 변경하지 않는다. 같은 모드에 숨은 실제 ACL 세 반례를 재현해 거부했으며, 저장 집중 **26개 시험**과 실제 SCRAM/공유 저장소 세 추가 경로를 포함한 로컬 PG16 전체 **1,190 passed**(기존 Pydantic 경고 2개)가 통과했다. CI에 별도 실제 Linux UID의 읽기/쓰기/생성·비밀 파일 접근 시험을 추가했다. 이는 합성 바이트의 파일 권한 시험이며 전체 서비스·테넌트/작업 격리·실제 키/계정·정확한 모델/열 release·G1/G4 수용은 계속 보류한다.
  - [실제 UID 서비스 통합 시험](../research/uid-service-integration-verification.md)을 추가해 기존 authority/감독자 RPC·LOGIN v2·콘텐츠 정책을 함께 검증한다. 별도 커널 UID와 SCRAM 사용자로 세 AI 단계, 서명/저장·최종 보류·다른 테넌트 큐 보존, 소켓 그룹에 속한 잘못된 UID 거부와 비밀/콘텐츠 접근 거부를 확인하는 호스팅 전용 절차다. 기존 같은 UID의 실제 SCRAM 경로 **6 passed**, 로컬 신규 세 경로 수집을 확인했다. 실제 서비스 시험은 루트 CI 실행 증거가 필요하며, 컨트롤러 fork 메모리·fake CLI/시험키는 독립 비밀 소유권·작업별 컨테이너/CLI UID·실제 모델·열 release·G1/G4 수용이 아니다. 체크는 유지한다.
  - [일반 작업자 실행 명령](../contracts/cli-dispatch-v1.md)을 앱 코드에 추가했다. 소켓·authority UID·테넌트·대기 설정만 받아 기존 RPC를 한 번 호출하고, 상태 참조/고정 오류만 출력하며 응답 손실 때 자동 재시도하지 않는다. 실제 subprocess/Unix 소켓 집중 **17 passed**를 확인했다. 호스팅 UID 서비스 시험의 일반 작업자도 읽기 전용 코드/스키마 사본에서 새 명령을 exec하도록 연결했다. authority/감독자는 여전히 컨트롤러 fork·fake CLI/시험키를 사용하므로 독립 키/계정·실제 모델·열 release·G1/G4 수용은 보류하며 체크는 유지한다.
  - [감독자 foreground 명령](../contracts/cli-supervise-v1.md)은 신뢰 운영 코드의 zero-argument factory로 기존 SupervisorServer를 기동하며 자격증명/모델/작업 인자를 받지 않는다. 새 프로세스의 실제 Unix 소켓·버전/정상 종료·SIGTERM·기동/서비스 오류와 기존 소켓 보존 집중 **10 passed**를 확인했다. 실제 UID 통합 시험의 감독자를 직접 exec하도록 연결해 중간 대기 프로세스와 상속 메모리를 제거했고, 해당 호스팅 실행 증거는 별도로 확인한다. 시험용 factory/fake CLI·키와 authority fork는 운영 조립·독립 비밀 소유권·실제 모델·열 release·G1/G4 수용이 아니며 체크는 유지한다.
  - [권한 서버 foreground 명령](../contracts/cli-authority-v1.md)을 추가해 기존 AuthorityServer와 production 차단을 유지하고, 시험용 조립에 공개 검증키·자신의 SCRAM 설정만 전달한다. 실제 인증 세 단계·성공/보류 저장, SIGTERM, 다른 DB 역할 거부, 기존 소켓 보존과 고정 오류의 집중 **13 passed**를 확인했다. 실제 UID 시험에서도 권한 서버를 직접 exec해 세 명령 모두 부모 메모리 없이 기동하도록 연결했다. 해당 호스팅 실행은 별도로 확인하며 root 시험 컨트롤러의 비밀 소유권·fake CLI와 감독자의 UID 공유·실제 모델/배포·열 release·G1/G4 수용은 계속 보류한다.
- [x] **`market-context`** — 선행: `provenance-g0`. 예정 파일(3): `backend/app/market.py`, `backend/tests/test_market_context.py`, `backend/tests/test_market_asof.py`. 수용: `MarketContext`는 정확히 `{kind: "available", snapshot_id}` 또는 `{kind: "unavailable", hold_report_id}`인 판별 유니온이다. 다른 변형의 ID, 임의 필드, `null`을 거부하고 Scenario·Economic scenario·Economic result·Assessment 사이의 변형과 ID가 일치해야 한다. 보류 사유·누락 증거는 참조한 Market hold report에 기록한다. 첫 G1에서 불가 문맥의 조건부 계산은 `origin=user`, `evidence_level=assumed`인 사용자 가정만 받고 Assessment는 `hold`한다. 후속에는 독립적인 권리·적용성·원장/정산 대사를 확인한 비공개 농장 기록을 해당 농장의 조건부·과거 계산에만 받을 수 있으며 공개 시장 전망이나 작물 순위로 승격하지 않는다. `ForecastRun`은 불가 문맥을 거부한다. `available_at > decision_at`이거나 과거 판본을 모르는 결정 입력도 거부한다. 수용 증거: 정확한 두 변형과 서버 참조/테넌트·결정시각·권리·판본/G0 참조, 네 객체 일치, 첫 G1 사용자 가정·최종 보류를 확인했다. 독립 xhigh 감사에서 발견한 Pydantic 인스턴스 및 중첩 권리 객체 검증 우회는 RED→GREEN으로 막았다. `cd backend && uv run --locked --group dev pytest -q tests/test_market_context.py tests/test_market_asof.py`에서 **87 passed**. 시험 저장소의 `available`은 실제 승인 MarketSnapshot이 아니며, 운영 영속 저장소·시장 원천 G0는 후속 작업이다.
- [x] **`thermal-engine`** — 선행: `thermal-contract`, `fixture-policy`. 변경 파일(4): `backend/app/thermal.py`, `backend/app/thermal_units.py`, `backend/tests/test_thermal.py`, `backend/tests/test_thermal_replay.py`. 커밋 `37f3f14`의 버전 고정 단일 구역 열·수증기 엔진은 고정 원본 manifest v2와 기상·시설 합성 입력에서 인접한 2시간의 60초 Euler 후보 trace를 만든다. UTC 시각·단위·제어·용량·포화·안정성·잔차/반걸음 한계·첫 trace 원시 해시를 통한 둘째 상태 이월을 검사하며 `run_status=candidate`만 반환한다. 잘못된 입력·원천/단위는 `ThermalHold`다. 수용 증거: 문서화 명령 관련 시험 **263 passed**, 독립 CLI `gpt-6-sol`/`xhigh` 재감사 세션 `01a0e25d-ff20-7af2-9f4f-24a385639754`에서 후보 계산 범위 차단점 없음. 구매 에너지·실제 온실 정확도·승인 G1 Run은 주장하지 않는다. 고정 manifest v2의 승인 보류는 유효하다.
- [x] **`thermal-decision-clock-contract`** — 선행: `thermal-engine`; 후속: `thermal-g1-publisher`. 변경 파일(5): `backend/app/thermal.py`, `backend/tests/test_thermal.py`, `backend/tests/test_thermal_contract.py`, `contracts/thermal-v1.md`, `contracts/thermal-v1.schema.json`. 후보의 사용자 계획시각 D와 서버가 증명해야 할 검토시각 R, 결정 문맥 ID, `ex_ante`/`ex_post_replay`, 실제/가상 결정 표지를 분리해 Run ID와 두 trace에 결합했다. `ex_ante`에서는 공개 가능시각이 D를 넘는 입력을 거부하고, 모든 경우 원본 수집시각이 R을 넘으면 거부한다. 레거시 3인자 호출은 후보만 만들고 승인 schema를 통과하지 못한다. 수용 증거: 커밋 `aa97e3f`, 정확한 CLI `gpt-6-sol`/`xhigh` 감사 세션 `01a0e2a9-9801-7082-8225-8ded6c665f2f`, 열/계약/재현/fixture 정책 **285 passed**와 `git diff --check`. 서버의 불변 D/R 권한 증명과 새 필드를 채우는 게시기는 후속이므로 실제 G1은 보류다.
- [ ] **`thermal-g1-publisher`** — 선행: `thermal-engine`, `thermal-decision-clock-contract`, `decision-evidence-store`, `cli-worker`; 후속: `api-flow`. 예정 파일(5): `backend/app/thermal_publisher.py`, `backend/app/thermal_run_store.py`, `backend/tests/test_thermal_publisher.py`, `backend/tests/test_thermal_run_store.py`, `contracts/thermal-g1-publisher-v1.md`. 수용: 서버가 작업자가 실제 기동·종료하고 최종 출력/JSONL을 봉인한 CLI 실행 증명, 테넌트·검증된 결정·불변 입력 스냅샷·시각, 원본 manifest SHA와 별도의 새로운 해제 증거 판본, 합성 자체 검토·권리/QC·원 단위/적용 기간·법칙/모델 판본·시간별 입력 ID를 독립 확인한다. 후보 두 trace를 재계산·검사하고 첫 trace를 `accepted`로 재직렬화한 최종 원시 SHA에 둘째 carry의 해시·basis를 다시 결합해 연속성/schema를 검증한다. 두 최종 바이트와 G1 판정·코드/환경 판본을 테넌트 범위의 한 DB 거래로 게시하며 실패·재시도는 부분 Run을 남기지 않는다. v2 원본 manifest를 소급 수정하지 않는다. 합성 소프트웨어 관문 시험은 실제 원천 G0·현장 G2·구매 에너지·작물/마진 근거가 아니다. 실제 G1 전체 경로는 `end-to-end-g1`에서 별도 검증한다. 진행 증거: 커밋 `7074720`/`621acad`의 게시 소프트웨어 계약과 D/R·서명된 결정 문맥 통합, 관련 로컬 PG16 **311 passed**, [호스팅 백엔드 CI 36318356211](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/36318356211) 전체 **977 passed, 0 skipped**. xhigh 감사의 코드 해시·해제 시각 결함을 보완했고, `ex_ante`는 D 시점 원천 증거 프로토콜 전까지 항상 보류한다. 추가 연결 후보: `ThermalReviewContract`가 서명 문맥·불변 스냅샷의 정확한 검토 입력과 일반 CLI 결정 검증을 열 게시 제안 바이트에 결합했고, 모의 권한·캡처를 사용한 관련 집중 시험 12개(그중 PG16 통합 3개)와 백엔드 전체 997개가 통과했다. 실제 권한 resolver·CLI 실행·독립 release·운영 DB 역할 증명이 없어 실제 G1 게시 수용은 아직 아니다.
  - [계획 사건 소프트웨어 후보](../contracts/planning-event-v1.md)가 서버 PostgreSQL 관측 시각과 명시적 가상 D를 구분해 불변 사건·문맥을 한 거래로 기록하고, 공개키 검증기가 실제 저장 사건의 서명·해시·범위·시각을 확인한다. 기존 DecisionContext 및 Market hold와 연결한 신규 **34개**를 포함한 열 게시/저장 관련 집중 **63 passed**를 확인했다. 시각 역행은 거래 전체를 되돌리며 과거 시각을 actual로 주입할 수 없다. 새 코드를 G1 코드 해시 목록에 넣었고 원본 manifest는 유지했다. 공유 owner/시험키이므로 독립 계획 권한·DB 역할/키·운영 clock·실제 CLI/해제·G1/G4 수용은 여전히 보류하며 체크는 유지한다.
  - 후속 [계획 DB 로그인 후보](../contracts/planning-login-policy-v1.md)는 별도 SCRAM 작성/읽기 계정을 만들고 연결마다 권한을 재검사한다. 작성자는 서버 `recorded_at`을 지정할 수 없고 두 계정은 변경·삭제·TRUNCATE·DDL·역할 상승이 거부된다. 발급/검증 기본 경로는 지정 계정을 요구하며 owner/임의 callback은 명시적 합성 시험으로만 허용한다. 기존 경로 집중 **108 passed**, 최종 권한·드리프트·원자 설치·문맥 연결 **35 passed**를 확인했다([증거](../research/planning-event-implementation.md)). 동일 OS UID/시험키·DB 전체 테넌트 읽기·운영 clock/독립 키·제품 조립·실제 CLI/release 보류가 남아 실제 G1/G4나 작업 완료를 주장하지 않는다.
  - [계획 발급 RPC 후보](../contracts/planning-rpc-v1.md)는 고정 OS peer/tenant의 별도 서명 프로세스와 읽기 전용 공개 검증 클라이언트를 연결한다. 새 Python 프로세스의 실제 계획 사건 → 불변 스냅샷/문맥 → 수집 검토 대기열 연결과 소켓/시각/요청·응답 범위·권한 변동·응답 유실을 포함한 신규 **28개**, 관련 집중 **79 passed**를 확인했다. 유실 후 한 기록만 남고 자동 재시도하지 않으며 여러 저장소의 원자성이나 HTTP 의도 복구를 주장하지 않는다. 동일 UID/시험키이므로 운영 factory/키·UID 독립성·실제 CLI/독립 release·G1/G4 보류와 미완료 체크는 유지한다.
  - [계획 서비스 foreground 후보](../contracts/cli-plan-v1.md)는 운영자 factory로 직접 기동하고, 문맥 저장소의 인증된 기존 authority 역할 연결을 추가했다. 새 계획/호출자 프로세스의 실제 SCRAM 문맥 저장·검토 대기열, 종료/고정 오류·잘못된 계정·권한 변동·기존 소켓 보존 관련 집중 **105 passed**(명령 **12개**, 새 저장소 **4개**)를 확인했다. 함께 쓰던 시험 credential 파일명 충돌을 분리했고 권한 관문은 유지했다. CI에 별도 planner/caller UID·양방향 비밀 파일 거부·rogue peer 거부·두 문맥/검토 대기열 시험을 추가했으며 root가 아닌 로컬에서는 실행하지 않았다. 운영 factory/독립 키·clock·실제 CLI/release·G1/G4 보류와 체크는 유지한다.
- [x] **`economic-ledger`** — 선행: `fixture-policy`, `market-context`. 변경 파일(4): `backend/app/economics.py`, `backend/app/economic_contracts.py`, `backend/tests/test_economics.py`, `backend/tests/test_economics_cash.py`. 커밋 `b831f46`의 `Decimal` 원장은 날짜별 `H/P/S`·반품·폐기·재고, 기초 재고 원가, 매출 인정·수금, 생산·판매·고정비 단일 반영, 감가상각·자산 처분, CAPEX·대출과 영업이익/영업현금/자기자본 현금을 대사한다. 누락된 중요 비용은 `unknown/hold`이며 열수요를 구매 에너지로 변환하지 않는다. 수용 증거: 집중 시험 **134 passed**, 독립 CLI `gpt-6-sol`/`xhigh` 감사 `01a0e238-1609-7282-8461-5243dcaa931a`, [C0 Actions](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/36310438310) 통과. 판매별 원천 공제와 조건부 순송금 단가는 별도 `sales-settlement`에서 검증하며 실제 농장 경제성·미래 마진·작물 순위는 보류한다.
- [x] **`sales-settlement`** — 선행: `economic-ledger`. 변경 파일(5): `backend/app/economic_contracts.py`, `backend/app/economics.py`, `backend/tests/test_economics.py`, `backend/tests/test_economics_cash.py`, `backend/tests/test_economics_settlement.py`. 커밋 `3228ae2`에서 판매별 할인·반품과 사용자 소유·불변 판본의 G1 수수료 상계·별도 비용 지급·수금을 `Decimal`로 대사한다. 상계는 동일 판매의 비용·서버 검증 원문에 결합하고 미수금·운영 미지급금만 함께 줄인다. 매출·비용·은행 현금에 중복 반영하지 않는다. 누락·일부/미래 수금·반품·재고 미대사는 단가를 `hold`한다. 완전 대사된 무반품 합성 사례의 단가만 **조건부 순송금 단가**로 표시한다. 나눗셈의 `ROUND_HALF_UP`과 산식 판본 v9를 고정해 호출자 반올림 환경이 달라도 전체 결과와 ID가 같도록 했다. 수용 증거: RED→GREEN 반올림 회귀, 집중 시험 **169 passed**, PG16 포함 백엔드 전체 **703 passed**, 독립 CLI `gpt-6-sol`/`xhigh` 감사와 수정 판단. 실제 정산서·은행 입금·농가 실수취가·G0/G3 승인 근거는 없으며 Assessment는 `hold`다.
- [x] **`market-hold-store`** — 선행: `market-context`, `thermal-g1-publisher`; 후속: `api-flow`. 변경 파일(5): `backend/app/db.py`, `backend/app/market_hold_store.py`, `backend/app/market.py`, `backend/tests/test_market_hold_store.py`, `contracts/market-hold-v1.md`. 수용: 첫 합성 G1에서 시장 G0를 아직 평가하지 않았다는 서버 소유 보류 보고서를 실제 PostgreSQL에 불변으로 보관한다. 임의 요청·CLI 문장이 보고서 승인 권한이 되지 않으며, ID/정규 바이트 해시·테넌트·공통 DecisionContext의 D/모드/실제·가상 표지·평가 범위·원인·누락 증거를 묶고 재시도/정정은 덮어쓰지 않는다. 다른 테넌트나 다른 D/모드의 ID, 변조, 표시권 없는 원문을 거부하고 사용자에게 안전한 사유만 보여 준다. CLI 작업 hold와 시장 hold를 혼동하거나 가짜 MarketSnapshot을 만들지 않는다. 실제 PG16 재시작·동시성·권한/무결성 시험과 독립 CLI `gpt-6-sol`/`xhigh` 감사가 필요하다. 수용 증거: RED→GREEN 집중 시험 **93 passed**, 로컬 PostgreSQL 16 백엔드 전체 **983 passed**, 실제 서버 재시작 전후의 동일 서명 보고서 재검증, 동시성·테넌트·D/모드·범위 변경·고아 스냅샷·DB 요청 역할/변조 회귀. 독립 CLI `gpt-6-sol`/`xhigh` 감사 `01a0e2d9-4e4c-78e2-80a3-51493a9cd247`의 세 결합 지적을 코드와 시험으로 보완했다. 실제 시장 G0, CLI/열 G1, API 연결, 배포 역할·키 증거는 별도 보류다.
- [ ] **`market-scenario`** — 선행: `market-context`, `fixture-policy`, `economic-ledger`, `sales-settlement`. 예정 파일(5): `contracts/market-scenario-v1.schema.json`, `backend/app/market_scenario.py`, `backend/tests/test_market_scenario.py`, `backend/tests/test_market_scenario_asof.py`, `backend/tests/test_market_scenario_economics.py`. 수용: 버전이 고정된 수요·공급·거시 조건부 공동 충격과 공통 충격이 날짜별 수확 `H`·판매 가능 `P`·판매 인정 `S` kg, 등급·채널, 차감 전 계약가격과 증거가 완전한 경우의 조건부 순송금 단가, 변동비, 수금·지급을 일관되게 바꾼다. 정산서·판매별 은행 입금 대사 전에는 정산 완료 농가 순수취가 `net_p`를 게시하지 않고 `hold`한다. 재고 보존·계약 인수/판매 제약, 발생일과 현금일, 가격·매출·마진·현금의 구분과 동일 원가의 중복 인식 방지를 시험한다. 모든 입력은 적용 날짜·판본·`available_at`·`decision_at`/as-of·출처·이용/표시/재배포 권리를 보존하고, 자료 입력에는 원천 URL/제품 ID·관측/발표/수집 시각·원본 해시·QC와 검토자를 연결한다. `MarketContext.kind=unavailable`인 첫 G1에서는 사용자가 소유하고 명시한 `origin=user`, `evidence_level=assumed` 가정만 조건부 스트레스에 쓰고 Assessment는 `hold`한다. 자료 유래 전망·작물 순위·가짜 MarketSnapshot은 내지 않는다. `available`이면 유효한 권리·판본과 `available_at <= decision_at`인 G0 승인 MarketSnapshot을 요구한다. 결과는 조건부 계산이며 거시 정밀도나 미래 예측 주장은 이후 독립 증거와 관문을 기다린다. 확인: `cd backend && uv run pytest tests/test_market_scenario.py tests/test_market_scenario_asof.py tests/test_market_scenario_economics.py`. 진행 증거: 커밋 `69d12e0`의 첫 `unavailable`/사용자 가정 경로와 교차 테넌트 구조화 오류 누출 회귀 RED→GREEN, 시장·경제 관련 **281 passed**, 호스팅 PG18 전체 **977 passed, 0 skipped**. 추가 후보: `MarketCandidateStore`가 파생 후보·새 숫자 판본을 한 PostgreSQL 거래에 불변 고정하고 재조회 시 해시·테넌트·입력 manifest를 확인한다([저장 계약](../contracts/market-candidate-store-v1.md)). 로컬 PG16 통합 시험 **4 passed**, 백엔드 전체 **1001 passed**다. 기초 원장·충격·권리·정산의 운영 원천 저장소, 실제 승인 MarketSnapshot의 `available` 경로, 결과 영속화·API 연결은 남아 있어 체크는 유지한다. 영속 Market hold의 소프트웨어 저장 계약은 별도 `market-hold-store`에서 수용했다.
  - 서명된 Market hold와 DecisionContext를 공동 시나리오·경제 원장 및 PostgreSQL 후보 재생에 연결한 통합 시험을 추가했다([검토 기록](../research/market-hold-joint-integration-review.md), [통합 시험](../backend/tests/test_market_signed_hold_integration.py)). 기초 원장·충격·권리·정산은 여전히 시험용 메모리이고 실제 계획 사건/배포 권한이 없어 `market-scenario`는 보류다.
  - 시장·경제 결과의 기말 재고 tuple 키를 손실 없이 저장할 [정규 JSON 코덱과 PostgreSQL 결과 기록](../contracts/market-result-codec-v1.md)을 추가했다. 서명된 Market hold와 후보를 조회 시 다시 계산하는 로컬 PG16 통합 시험이 통과했다. 원천의 운영 영속화·API 조회·독립 CLI 검토는 남아 있어 `market-scenario`는 보류다.
- [ ] **`economic-break-even`** — 선행: `economic-ledger`, `market-scenario`. 예정 파일(2): `backend/app/break_even.py`, `backend/tests/test_break_even.py`. 수용: 관리용 운영이익·영업 현금·누적 자기자본 현금의 손익분기를 각각 지정한 kg 또는 KRW/kg 변수·범위에 대해 **매 시험값마다** 충격·등급·채널·`H/P/S`·가격·계약·재고·변동비·수금/지급을 포함한 날짜별 시나리오 경로 전체를 다시 계산한다. 스칼라 영점식만 대입하지 않는다. 유효한 영점, 해 없음, 단조롭지 않은 분기를 구별하고 실현 가능성은 주장하지 않는다. 확인: `cd backend && uv run pytest tests/test_break_even.py`. 진행 증거: `backend/app/break_even.py`의 사전 고정 유한 격자 후보와 `backend/tests/test_break_even.py`의 실제 시장 시나리오·원장 재계산 **11 passed**, 계약 경계 [break-even-grid-v1](../contracts/break-even-grid-v1.md). 파생 후보·숫자 판본 세 개의 PostgreSQL 재조회와 매 시험값의 시장·경제 경로 재계산을 확인했다. 추가 `BreakEvenStore`는 신뢰 권한 아래 검증된 계획·계산 결과를 한 PostgreSQL 거래에 고정하고 재조회 시 전체 경로를 재계산한다(손익분기 집중 **15 passed**). 기초 원장·충격·권리·정산은 시험용 메모리이고 계획 생성도 시험 코드다. 운영 원천·계획/시도값 생성, 연속 구간의 모든 해/해 없음 증명, 현재 필수 모델의 독립 CLI `gpt-6.1-sol`/`xhigh` 경제·구조 감사가 없어 수용 체크는 유지한다.
  - [서명된 Market hold 통합 시험](../backend/tests/test_market_signed_hold_integration.py)은 세 PostgreSQL 시장 후보와 한 손익분기 계획·결과를 새 저장소 인스턴스에서 재생하고 보류 범위 변경 시 거부한다. 기초 원장·충격·권리·정산과 계획 생성은 시험용 메모리/코드이므로 `economic-break-even` 수용 체크는 유지한다.
- [ ] **`source-collection-worker`** — 선행: `cli-worker`, `decision-evidence-store`, `fixture-policy`; 후속: `api-flow`. [계약](../contracts/owned-fixture-collection-v1.md)에 따라 서버가 검증한 같은 테넌트의 완료 조사 선택만 받고 고정 제공자·원본/메타데이터·기간/결정시각·권리/QC를 확인한다. 첫 어댑터는 기존 직접 작성 합성 자료이며 임의 URL/파일/원문 요청을 받지 않는다. 실제 임대·취소/만료/복구·권한 변동·원본 손상·원자 게시와 별도 전경 프로세스를 검증한다. 수집 검토·스냅샷 채택·실제 정확한 CLI/독립 격리 증거와 전체 연결 수용까지 미완료로 둔다. 실제 제공자 G0는 원천별 후속 작업에서 승인한다. [소프트웨어 구현 증거](../research/owned-fixture-collection-implementation.md)를 참조한다.
- [ ] **`api-flow`** — 선행: `source-collection-worker`, `durable-jobs`, `job-intent-idempotency`, `cli-worker`, `market-context`, `market-hold-store`, `thermal-g1-publisher`, `market-scenario`, `economic-break-even`. 예정 파일(5): `backend/app/api.py`, `backend/app/api_contracts.py`, `backend/app/orchestration.py`, `backend/tests/test_api.py`, `contracts/openapi-v1.json`. 수용: 버전 관리된 제출·상태 확인·조회 경로가 좌표, 출처·시장 보류, 변경 불가 스냅샷, Run, 시계열/manifest, 조건부 공동 시장 시나리오·경제 결과와 전체 경로 손익분기, 평가를 연결한다. 잘못된 테넌트·참조·단위를 거부하고 부분 결과를 노출하지 않는다. 확인: `cd backend && uv run pytest tests/test_api.py`와 생성 OpenAPI·검토 계약 비교.
  - [구현된 API 조립 후보](../contracts/api-runtime-assembly-v1.md)가 명시적 v4·기존 아티팩트 루트·TLS·Bearer·여섯 저장소·등록부를 같은 요청 인증으로 연결한다. 시장 원천의 보류/문맥 권한 대체를 막고 작업 저장소도 매 연결 유효 권한을 검사한다. 실제 Python API 서비스 프로세스의 지역 접수·작업·서명 보류·조건부 경제/손익분기·빈 열 조회와 시작/권한 변동 거부를 새 **31개**, 기존 경로까지 집중 **224개**로 확인했다([증거](../research/api-runtime-assembly-implementation.md)). 합성 자료/키 시험이며 운영 설정·원천/계획 생성·실제 Codex/Run/브라우저·독립 release·G1/G4가 남아 체크는 유지한다.
  - [조건부 손익분기 HTTP 조회](../contracts/api-break-even-read-v1.md)가 고정 계획의 전체 격자 경로를 재계산해 세 목표·kg/KRW/kg 단위·영점/구간/비단조/보류·현금 부족을 안전하게 표시한다. [명시적 로그인 v4](../contracts/runtime-break-even-login-policy-v4.md)는 계획 저장소도 실제 SCRAM/매 연결 유효 권한 검사에 묶는다. 새 조회 시험 13개와 로그인 시험 5개 및 기존 권한·API 회귀의 실행/수정 내역은 [증거](../research/break-even-read-implementation.md)에 기록했다. 운영 원천·계획 생성·전체 조립·독립 경제/CLI/release·브라우저/G1/G4가 남아 체크는 유지한다.
  - [시장 계산 로그인 프로필 v3 후보](../contracts/runtime-market-login-policy-v3.md)가 명시적 선택으로 세 계산 테이블의 authority 읽기/삽입과 보류·후보·결과 저장소의 매 연결 SCRAM/유효 권한 검사를 연결한다. 실제 DB 인증·서명 보류→후보→조건부 결과→HTTP 재계산, 권한 변동/다른 로그인 거부를 신규 **18개**, 기존 역할·시장/API·열 경로까지 집중 **110개**로 확인했다([증거](../research/market-runtime-implementation.md)). 원천 저장소는 합성 자료이며 전체 보호 조립·운영 자격증명/DB 정책·실제 CLI·독립 release·G1/G4가 남아 체크는 유지한다.
  - [버전 관리 OpenAPI 후보](../contracts/openapi-v1.md)는 현재 여덟 경로의 안정 operation ID·Bearer·AND 권한과 요청/응답을 고정한다. 좌표의 엄격한 닫힌 형식, 실제 권한 부족 거부, 문서 재생성/참조, 비운영 CLI 검사와 실제 HTTPS의 같은 계약 반환을 새 **19개**, 기존 API/인증/열 연결까지 집중 **166개**로 확인했다([증거](../research/openapi-implementation.md)). 나머지 제출·전체 운영 조립·실제 Codex·독립 release·브라우저/G1/G4가 남아 수용 체크는 유지한다.
  - [로컬 HTTPS 시작 후보](../contracts/api-https-service-v1.md)는 운영자 factory의 인증된 FastAPI를 Uvicorn `0.54.0`으로 실행한다. 실제 Python CLI 자식·합성 인증서/Bearer·SCRAM PG16으로 TLS 접수/재접수/조회, 비신뢰 인증서·평문 거부와 종료를 확인했다. 새 시험 **31개**, 기존 인증/API/열 검증 집중 **137개**가 통과했다([증거](../research/api-https-service-implementation.md)). 공개 TLS·전체 보호 factory/설정·운영 계정·Compose 앱·실제 Codex·독립 release·전체 G1/G4가 남아 수용 체크는 유지한다.
  - [요청별 서비스 인증 후보](../contracts/http-identity-v1.md)는 서버 고정 Bearer의 테넌트·권한·만료를 API와 저장소의 같은 문맥 공급자에 연결한다. 합성 토큰으로 실제 PG16 동시 접수·다른 테넌트 거부·권한 부족·스레드 전달·종료/취소/복사 문맥의 권한 해제를 새 **33개**, 기존 HTTP/등록부/열 검증까지 집중 **151개**로 확인했다([증거](../research/http-identity-implementation.md)). 실제 HTTPS 서버·프록시·운영 계정/토큰 발급·회수·브라우저 세션·독립 release·전체 G1/G4가 없어 수용 체크는 유지한다.
  - [지역 접수·조사 등록 후보](../contracts/api-location-research-v1.md)의 `POST /v1/locations`가 등록 범위·자료 목록 해시를 고정한 조사 입력을 인증된 기존 authority로 저장한다. 두 계층의 권한·테넌트 분리·재요청/동시성·변경 충돌·제한된 JSON·실제 SQL 권한 변동을 새 HTTP 시험 **35개**, 기존 조회·시각·CLI/게시 연결까지 집중 **88개**로 확인했다([증거](../research/location-research-implementation.md)). 최초 조사 준비의 문맥은 null이고 공간 지원은 조사 대기다. 실제 registry/인증 조립·CLI 조사·자료 수집·후속 서명 문맥·G1 경로는 아직 보류여서 체크를 유지한다.
  - [해시 고정 조사 등록부](../contracts/research-registry-v1.md)가 접수와 CLI 입력 권한 검증의 같은 불변 범위를 공급한다. 등록부/입력 변조·누락/변경 문맥·테넌트 분리·proceed 거부와 지역 접수→fake CLI 자식→영속 hold→HTTP 재조회/재접수를 최종 집중 **35개**로 확인했다([증거](../research/research-registry-implementation.md)). 등록부는 제공자 후보 조회만 허용하며 자료 권리/QC 승인이나 실제 모델 호출 증거가 아니다. 실제 registry/인증 조립·독립 원천/실행·release·G1/G4와 체크 보류는 유지한다.
  - [검증된 작업 보류 HTTP 조회](../contracts/api-job-hold-v1.md)가 세 CLI 단계의 불변 보고서에서 안전한 누락 근거 범주·개수·보류 사유·기록 시각을 반환한다. API와 저장소의 metadata/artifact/auditor 권한을 적용하고, artifact만으로 감사용 원문을 읽던 반례를 RED→GREEN으로 막았다. 새 HTTP **22개**와 원문 저장/CLI/등록부/게시 연결 집중 **151개**를 확인했다([증거](../research/job-hold-http-implementation.md)). 시험은 fake CLI와 합성 증거이며 실제 모델·운영 계정/권한·독립 release·전체 G1과 체크 보류는 유지한다.
  - 첫 읽기 슬라이스로 [작업 상태 HTTP 계약](../contracts/api-job-status-v1.md)과 `GET /v1/jobs/{id}`를 추가했다. 테넌트·`metadata` 권한과 저장소 조회를 모두 검사하고, 임대 토큰·입력·멱등 키·CLI 원문 없이 상태·시각·사유 코드만 반환한다. 로컬 PG16 집중 시험은 14개 통과했다. 제출·나머지 조회·실제 인증 공급자·전체 OpenAPI와 G1 경로가 남아 있어 체크는 유지한다.
  - [시장 보류 HTTP 조회 계약](../contracts/api-market-hold-v1.md)과 `GET /v1/market-hold-reports/{id}`가 영속 저장소의 안전한 투영을 읽는다. 테넌트·표시 권한, 과거 범위의 읽기 전용 보류, 오류 세부정보 비노출을 로컬 PG16에서 시험했다. 보고서 발행·실제 인증/권한 공급자·나머지 API와 G1 경로는 보류다.
  - [합성 열 Run HTTP 조회 계약](../contracts/api-thermal-run-read-v1.md)의 `GET /v1/runs/{id}`, `/series`, `/manifest`가 두 trace의 120개 수치점과 원본 manifest의 사용 출처·권리·미해결 항목을 표시용으로 투영한다. 세 경로 모두 게시기의 완전한 해제 필드를 요구하며, 저장소 시험의 간단한 서명 패킷은 전부 거부한다. API 집중 PG16 시험에서 테넌트·표시권·단위·시간 연결·입력 해시·미게시 후보를 확인했다. 시험 서명·해제 대역을 실제 CLI/G1 증거로 승격하지 않으며 전체 오케스트레이션과 브라우저는 남아 있다.
  - [조건부 경제 결과 HTTP 조회 계약](../contracts/api-economic-result-read-v1.md)의 `GET /v1/economic-results/{id}`는 테넌트 범위의 고정 결과를 전체 공동 시나리오·원장 경로로 재계산한 뒤 사용자 가정·시장 `unavailable`·Assessment `hold`와 단위가 명확한 십진 수량/금액만 투영한다. 다른 테넌트·범위 변경·잘못 결합한 결과 ID·내부 오류 상세를 거부하는 로컬 PG16 통합 시험이 통과했다. 공개 필드의 별도 정확한 CLI 설계 감사, 제출·월별 현금·손익분기·실제 인증/DB 역할·CLI/G1 증거는 남아 있어 체크를 유지한다.
- [ ] **`web-shell`** — 선행: `api-flow`. 예정 파일(5): `web/index.html`, `web/tsconfig.json`, `web/src/main.tsx`, `web/src/App.tsx`, `web/src/api.ts`. 수용: 국내 좌표·기간 한 건과 한 구역·날짜별 경제 및 수요·공급·거시 조건부 가정을 입력하고 `MarketContext`의 시장 근거 또는 불가·보류 보고서 카드, 지속 작업의 현재 단계, 명시적 보류 사유를 키보드로 확인할 수 있다. 첫 G1의 가정 출처와 조건부 결과를 표시하고 자료 유래 전망으로 표현하지 않는다. MapLibre 지도 위치를 농장 수준의 정밀도로 오해하게 하지 않는다. 확인: `cd web && npm run typecheck && npm run build` 후 API와 함께 키보드 경로 점검.
- [ ] **`web-replay`** — 선행: `web-shell`. 예정 파일(5): `web/src/Replay.tsx`, `web/src/ZoneScene.tsx`, `web/src/ResultsTable.tsx`, `web/src/Replay.css`, `web/src/Replay.test.tsx`. 수용: Three.js 장면·ECharts·HTML 표가 동일한 `run_id + timestamp`의 값과 단위를 읽는다. WebGL을 쓸 수 없어도 표·문장과 키보드 제어를 제공한다. 월별 조건부 금액을 시간별 계측값으로 보간하지 않으며 생장 애니메이션을 만들지 않는다. 확인: `cd web && npm run test && npm run typecheck && npm run build` 후 선택한 시각의 값 비교.
- [ ] **`end-to-end-g1`** — 선행: `web-replay`, `cli-worker`, `compose-runtime`. 예정 파일(4): `scripts/run-g1.sh`, `backend/tests/test_e2e_g1.py`, `web/e2e/flow.spec.ts`, `contracts/g1-evidence.md`. 수용: 실제 PostgreSQL/Compose 환경에서 구현된 web/API/수집·CLI·수치 작업자를 기동하고, 합성 자료 요청이 복구 가능한 작업과 실제 CLI 세 단계를 모두 거쳐 결정적 열·사용자 가정만의 수요·공급·거시 공동 충격·날짜별 조건부 경제 출력, 일치하는 3D·표, 최종 작물 선택 `hold`까지 완료된다. 작업자 실패·재시작 후 복구를 확인한다. `unavailable` MarketContext의 Market hold report를 유지하고 가짜 MarketSnapshot·자료 유래 전망·순위를 게시하지 않는다. 증거에 버전·해시·시도·재시작 동작을 기록한다. 모의 시험만으로 체크하지 않으며 결과는 합성 자료 G1 계약 추적 시험에 한정한다. 확인: `bash scripts/run-g1.sh`, 집중 pytest, 실제 스택의 Playwright 시험; 비밀을 제거한 증거를 보존한다.
- [ ] **`kma-g0`** — 선행: `g0-authority-store`, `thermal-contract`, `cli-worker`. 예정 파일(5): `backend/app/kma_asos.py`, `backend/app/kma_semantics.py`, `backend/tests/test_kma_asos.py`, `backend/tests/test_kma_g0.py`, `contracts/kma-product-v1.md`. 수용: 허용된 HTTPX 연결 도구가 실제 연결 제품의 정확한 ID, 공식 관측소·기간 보유율, `SI` MJ/m²·`TM` KST 의미, 호출당 31일 분할, 제공자 QC와 프로젝트 QC의 구분, 변경 불가 원본 해시, 이용·저장·표시·재배포 권리를 기록한다. **외부 장애물:** 권리/운영 승인, 측정한 `SI` 보유율, 정확한 `SI` 적산 구간/`TM` 경계를 전문 CLI 조사로 입증해야 한다. 없으면 실제 자료는 `hold`한다. 확인: 단위·음수·구간 시험 후 권리가 확인된 시범 요청과 G0 기록; 그 전에 좌표·기간을 고르지 않는다.
- [ ] **`market-source-g0`** — 선행: `g0-authority-store`, `market-context`, `cli-worker`. 예정 파일(5): `backend/app/market_sources.py`, `backend/app/market.py`, `backend/tests/test_market_sources.py`, `backend/tests/test_market_source_g0.py`, `contracts/market-source-v1.md`. 수용: 실제 승인한 시장 제품만 허용 목록 어댑터로 수집·정규화하고 정확한 원천 URL/제품 ID, 관측·발표·`available_at`·조회 시각, 원본 판본/개정과 변경 불가 원본 해시, 원 단위와 변환 버전, 제공자/프로젝트 QC, 검토자, 접근·이용·저장·가공·표시·재배포 권리를 기록한다. 품목·품종/등급·거래 단계/채널·지역·날짜/적용기간·단위가 요청과 맞는지 검사하고 `available_at <= decision_at`인 당시 판본만 해당 용도 G0에 채택한다. 통과하면 불변 MarketSnapshot과 `{kind: "available", snapshot_id}`를 게시하고, 권리·판본·품질·적합성이 불명확하면 Market hold report와 `{kind: "unavailable", hold_report_id}`만 게시한다. 시장 참고가격을 농가 실수취가로 둔갑시키지 않는다. **외부 장애물:** 연결할 제품은 아직 정하지 않았으며 정확한 제품별 권리·원본 판본/공표 지연·개정 이력을 CLI 조사와 제공자 근거로 확인해야 한다. 이 작업은 첫 합성 G1의 선행 조건이 아니지만 자료 유래 시나리오·실제 시장 근거 표시·후속 전망의 선행 조건이다. 확인: 권리/시각/등급·채널·단위 불일치와 개정 자료의 과거 유입을 거부하는 집중 시험, 승인된 제품의 권리 범위 내 시범 요청·원본 해시 재계산·G0 게시/보류 기록; 근거가 없으면 게시를 보류하고 체크하지 않는다.
- [ ] **`g2-evidence`** — 자료 획득/프로토콜은 `crop-independent-data-access`에서 모델 개발과 병행한다. 최종 판정 선행: 검증 대상 출력의 G0·계산/재현 G1 증거; `kma-g0`는 해당 기상 자료를 쓸 때, `end-to-end-g1`은 전체 경로를 주장할 때 요구한다. 예정 파일(3): `research/g2-protocol.md`, `research/g2-source-register.md`, `backend/tests/test_g2_gate.py`. 수용: 독립 국내 온실 센서/보정 기간, 기후 비교, 주장할 공급열 또는 구매 에너지에 대응하는 계량만 사전 등록한다. 검사 전에 적용 범위와 손실 기준을 기록한다. **외부 장애물:** 협력 농장의 동의와 실측값. 확인: 출처 이용 허락, 미사용 기간 비교 보고서, 관문 시험; 증거가 생길 때까지 G2는 보류한다.
- [ ] **`forecast-engine`** — 선행: `market-source-g0`, `g2-evidence`, `market-scenario`. 예정 파일(5): `backend/app/forecast.py`, `backend/app/forecast_validation.py`, `backend/tests/test_forecast.py`, `backend/tests/test_forecast_asof.py`, `contracts/forecast-run-v1.schema.json`. 수용: 승인된 MarketSnapshot이 있는 `available` 문맥만 받고 `decision_at` 당시 이용 가능한 원본 판본/특성(`feature_cutoff`)으로 모델·매개변수·코드/환경·학습 자료·시드·출력 해시가 고정된 별도 ForecastRun을 만든다. 검증된 범위에서는 후보별 미래 수확 `H`, 등급/packout별 판매 가능 `P`, 계약·재고 제약 후 판매 인정 `S`, 농가 순수취가·비용·수금/지급·현금의 공동 경로를 버전 고정 산술로 계산하고, 자료·변환·현장 근거 또는 G3a 적용 증거가 없으면 예측 게시 대신 명시적 `hold`와 누락 증거를 남긴다. 독립 rolling-origin 계획은 매 `decision_at` 전에 이용 가능했던 판본만 학습·특성 선택·구간 보정에 쓰고 이후 정산·관측은 정답에만 쓰며, 시점 복원이 안 되는 회차는 제외한다. 사전 등록된 계절/직전값·당시 발행 전망 기준선과 판매 kg·등급·실수취가·비용·현금 부족의 오차/편향/구간 포함률을 독립 기간에서 비교하도록 한다. **외부 장애물:** 동의 받은 국내 농장의 수확·등급·정산·계약·비용·현금 기록과 결정 당시 판본·독립 기간이 아직 없다. 확인: 불가 문맥/미래 정보 유입 거부, 버전 재실행·수량/원장 보존·누락 시 보류 시험과 미사용 기간 검증 계획 검토; 엔진 완료만으로 미래 마진이나 G3a를 열지 않는다.
- [ ] **`g3a-evidence`** — 선행: `forecast-engine`, `economic-ledger`, `market-context`. 예정 파일(3): `research/g3a-protocol.md`, `research/g3a-source-register.md`, `backend/tests/test_g3a_gate.py`. 수용: 동의를 받은 수확·등급·판매·반품·재고·정산·계약·비용·현금 기록과 `decision_at` 당시 판본으로 개별 후보의 사전 등록된 rolling-origin 시험과 기준선 비교를 **엔진 개발·보정에 쓰지 않은 독립 기간**에서 뒷받침한다. **외부 장애물:** 농장 기록·권리·독립 기간. 확인: 원장 대사, 시점 분리, 사전 손실 기준·오차/편향/구간 포함률 보고서, 관문 시험; 통과 전에는 미래 마진을 내지 않는다.
- [ ] **`crop-ranking`** — 선행: `g3a-evidence`. 예정 파일(5): `backend/app/ranking.py`, `backend/app/ranking_validation.py`, `backend/tests/test_ranking.py`, `backend/tests/test_ranking_hold.py`, `contracts/ranking-v1.schema.json`. 수용: 이번 결정에 실제 가능한 후보 둘 이상을 같은 `decision_at`·지역·온실/관리·면적·평가 달력·시작 재고·목표·계약/판로·자원 제약으로 맞추고 같은 시장/기상 충격 아래 ForecastRun과 날짜별 관리용 이익·현금을 비교한다. 후보별 G0~G3a 적용 범위와 G3b 대응 증거를 매 평가에서 재검사하고 불확실성 구간의 겹침, 순위 역전, 관측 가능한 대응 결과의 후회/최악 손실, 미판매 기말 재고와 비용을 기록한다. 후보가 둘 미만이거나 범위·제약·대응 증거가 부족하거나 우열을 구별할 수 없으면 `hold`와 후보별 이유를 내며 G3b가 독립 대응 검증을 통과한 범위에서만 순위를 게시한다. **외부 장애물:** 개발·보정과 분리된 국내 후보 대응 시험구/작기 기록·권리·공통 목표의 반사실 결과가 아직 없다. 확인: 후보 한 개, 충격 불일치, 구간 겹침, G3b 누락의 보류 시험과 동일 달력/면적·후회 손실의 대응 자료 시험; 엔진 구현만으로 순위를 열지 않는다.
- [ ] **`g3b-evidence`** — 선행: `crop-ranking`. 예정 파일(3): `research/g3b-protocol.md`, `research/g3b-source-register.md`, `backend/tests/test_g3b_gate.py`. 수용: 실행 가능한 작물 둘 이상을 같은 결정·시설·면적·달력·목표·공통 충격 아래 **엔진 개발·보정·후보 선택에 쓰지 않은 독립 자료로** 대응 비교하고, 순위·후회 손실·순위 역전·보류 평가와 제외 기준을 사전 등록한다. **외부 장애물:** 협력 농장의 대응 기록과 공유권. 첫 G1과 별개다. 확인: 대응 비교 집단 감사, 사전 손실 기준 보고서와 관문 시험; 통과 전에는 순위를 내지 않는다.
- [ ] **`service-economics`** — 선행: `end-to-end-g1`. 예정 파일(5): `backend/app/cli_worker.py`, `backend/app/job_store.py`, `backend/app/service_economics.py`, `backend/tests/test_service_economics.py`, `ops/service-economics-evidence.md`. 수용: 농장 경제 원장과 분리해 기간별 무료/유료·완료/실패/취소 요청, 단계별 실제 Codex CLI 호출·사용량·청구액과 재시도 시도 ID, 자료 API/지도 타일·계산·저장·백업·지원 변동비, 유료 매출과 고정 운영비를 청구서·작업 기록과 대사한다. `Decimal`로 서비스 공헌이익=매출−전체 요청량 연동 비용, 영업 잔여액=공헌이익−고정비, 완료 요청당 실효 변동원가=무료·실패·재시도 포함 전체 변동비/완료 요청 수를 계산하며 완료 0건이면 마지막 지표는 미정의로 표시한다. 무료 수요·판매 구성·용량이 고정되고 유료 요청당 공헌이익이 양수인 단순 경우에만 조건부 유료 요청 손익분기를 내며, 무료 수요·재시도율 등이 함께 변하면 각 시험 유료 요청 수에서 전체 비용/매출 경로를 다시 평가한다. 예상 수요와 동시 처리량·CLI/API 한도·지연·운영 재원을 비교하고 비용/계정 증거가 없으면 G4를 `hold`한다. **외부 장애물:** 실제 운영 계정 청구액·자료/타일 비용·유료 매출·요청량/재시도·고정비와 운영 재원 증거가 없다. 확인: 무료/유료/실패/재시도 대사, 0건·비단조/용량 초과 손익분기 시험, 실제 청구서와 계정·부하 기록을 비밀 제거해 증거 문서에 연결; 엔진 시험만으로 수익성이나 G4를 주장하지 않는다.
- [ ] **`g4-operations`** — 선행: `end-to-end-g1`, `service-economics`; 실제 기상청 원천을 쓰는 공개 경로에는 `kma-g0`, 시장 원천 유래 경로에는 `market-source-g0` 추가. 예정 파일(5): `ops/deployment.md`, `ops/rights-register.md`, `ops/cli-account-evidence.md`, `backend/tests/test_security_g4.py`, `web/e2e/accessibility.spec.ts`. 수용: 실제 배포 계정으로 정확한 CLI 모델·추론 강도, 인증·조건·한도·비용, 스키마·격리·외부 통신을 입증한다. `service-economics`의 실측 요청 원가·수지·용량/한도·운영 재원 증거를 대사하고 원천·지도 타일 권리, 테넌트 보안, 백업 복원, 관측성, 접근 가능한 브라우저 경로도 시험한다. **외부 장애물:** 계정·운영자·권리·호스트·실측 부하/비용·매출/재원. 확인: 배포·복구·보안·접근성·서비스 수지 보고서와 범위를 밝힌 G4 관문; G3a/G3b 주장은 각각 별도 관문이 필요하다.

**시장·경제 입력 저장 진행 후보:** [MarketSourceStore](../backend/app/market_source_store.py)가 기존 7종 사용자 가정을 실제 불변 작업 입력에 결합하고 기준/충격 pin을 생성한다. [저장·v5 계약](../contracts/market-user-source-store-v1.md), [시험](../backend/tests/test_market_source_store.py), [구현 증거](../research/market-user-source-implementation.md)를 참조한다. 실제 자료 승인·입력/계획 오케스트레이션·전체 CLI/브라우저/운영 수용은 남아 있어 market-scenario, economic-break-even, api-flow 체크는 변경하지 않았다.

- [ ] **`thermal-simulation-worker`** — 선행: `durable-jobs`, `thermal-g1-publisher`, `cli-worker`; 후속: `api-flow`, `end-to-end-g1`. [작업자/전경 실행 계약](../contracts/thermal-simulation-worker-v1.md)에 따라 명시적 작업·테넌트·현재 권한/임대/불변 입력과 실제 승인 검토에 결합해 Run과 완료를 한 거래로 게시한다. 취소·만료·프로세스 실패/새 시도, 오류 비공개, 다른 모델 작업 미소비를 확인한다. [소프트웨어 진행 증거](../research/thermal-simulation-worker-implementation.md)는 SCRAM·합성 검토/키의 집중 177개와 실제 자식 정상/중단 후 복구를 확인했다. 실제 CLI·독립 검토/해제·운영 factory·전체 API/브라우저 G1 수용은 남아 체크를 유지한다.

**API 연결 진행:** [완료 열 작업의 Run 조회](../contracts/api-job-run-v1.md)가 작업 게시/영수증·입력 해시와 실제 Run을 대사해 기존 공개 요약을 반환한다. [구현 증거](../research/api-job-run-implementation.md)는 합성 검토와 실제 SCRAM/인증된 조립의 소프트웨어 범위다. 실제 CLI·제출/오케스트레이션·브라우저 G1은 남아 api-flow 체크를 유지한다.

**열 HTTP 접수 진행:** [접수 계약](../contracts/api-run-submission-v1.md)은 실제 저장 판본·완료 검토·권리/QC·독립 실행/해제를 검사한 뒤 같은 v2 작업을 멱등 등록하고 거래 안에서 현재 Scope/핀을 재검사한다. [구현 증거](../research/api-run-submission-implementation.md)는 합성 검토/키와 실제 SCRAM/Bearer 연결의 범위다. 실제 CLI·전체 농장/경제 Scenario·조사/수집/평가 오케스트레이션·브라우저/G1/G4는 남아 체크를 유지한다.

**시나리오 HTTP 진행:** [등록/조회 계약](../contracts/api-scenario-intent-v1.md)은 서버 테넌트를 결합해 현재 Scope/실제 참조 아래 불변 열 의도를 등록하고 판본·해시·최초 시각만 반환한다. [구현 증거](../research/api-scenario-intent-implementation.md)는 같은 판본 재시도·충돌/새 판본·조회 격리·HTTP 실행 연결과 기존 접수의 JSON 계약 회귀를 다룬다. 전체 농장/경제 Scenario·CLI/오케스트레이션·브라우저/G1/G4는 남아 체크를 유지한다.

**경제·시장 가정 HTTP 진행:** [7종 사용자 가정 접수](../contracts/api-market-user-source-v1.md)는 완전한 기존 모델/바이트를 검사하고 요청·원천 등록을 같은 거래로 묶는다. [구현 증거](../research/api-market-user-source-implementation.md)는 실제 SCRAM·새 Bearer 조립·중간 Scope/저장소 변경·충돌 롤백을 다룬다. 산술·수집 완료를 만들지 않으며 전체 CLI/경제 작업·브라우저/G1/G4는 남아 체크를 유지한다.

- [ ] **`thermal-scenario-store`** — 선행: `thermal-g1-publisher`, `market-hold-store`; 후속: `api-flow`. [계약/명시적 로그인 v6](../contracts/thermal-scenario-store-v1.md)에 따라 합성 열 Scenario의 스냅샷·모델·문맥·시장 보류 참조를 불변 판본으로 저장하고 현재 권한/핀을 재검사한다. [소프트웨어 증거](../research/thermal-scenario-store-implementation.md)는 등록·재조회·충돌·권한 변동·참조 보류와 기존 프로필 회귀를 다룬다. 완전한 농장/경제 Scenario와 제출·작업자/Run 연결·독립 운영 권한의 수용까지 체크는 유지한다. [농장 재생 계획 접수 후보](../contracts/farm-replay-scenario-v1.md)는 실제 조사 입력·열/경제 판본을 공통 문맥과 불변 작업 입력으로 묶는다([증거](../research/farm-replay-scenario-implementation.md)). 전체 작성과 열/경제 작업·평가의 이 판본 참조는 계속 후속이다.

  - [시나리오 실행 연결 증거](../research/thermal-scenario-execution-implementation.md): 입력/영수증 v2가 실제 저장된 판본과 Run을 결합하고 게시 전후 Scope 철회·문맥/핀 불일치는 결과를 공개하지 않는다. 명시적 v6 조립과 Bearer 조회는 같은 실제 SCRAM 저장소를 읽는다. 합성 캡처/키 시험이며 전체 농장 Scenario·HTTP 접수·실제 CLI/독립 release·브라우저/G1/G4는 남아 체크를 유지한다.

## 경제 웹 입력·계산 연결 후보 (2026-09-29)

[농장 공통 평가 연결 후보](../contracts/farm-calculation-assessment-v1.md)는 같은 계획의
실제 완료 열·경제 작업을 평가 입력 v2와 공유 CLI 보류에 연결한다
([진행 기록](../research/farm-calculation-assessment-implementation.md)). 실제 HTTPS 연결을
확인했으며 혼합 거부·거래 롤백·기존 경로 호환 시험도 통과했다. 다음 부분 작업은
전체 농장 입력 작성이다. `api-flow`와 전체 농장/G1 수용 체크는 유지한다.
[입력 작성 모듈 지도](../CAPABILITIES-farm-authoring.md)의 첫 작업은
[farm-inputs 계약](../contracts/farm-inputs-v1.md)의 닫힌 전체 입력과
열 계산 입력 변환, 경제 배치/날짜 범위 검사다. 해당 계약의 집중 시험 이후
변경 불가 등록과 실제 스냅샷/검토/해제, 실행·Assessment 결합, 전체 원장/농장
작성 화면으로 진행한다. 모듈 제공자 시험만으로 기존 작업 체크를 해제하지 않는다.
[첫 제공자 증거](../research/farm-inputs-implementation.md)는 새 시설값의 실제 수식
반영과 120개 시점의 일치, 달력/면적·경제 배치 범위와 기존 계산 회귀를 다룬다.
영속 등록은 내부 후보이며 새 스냅샷의 독립 검토/해제·실행·화면으로
연결하지 않았다.
[내부 등록 후보](../contracts/farm-authoring-storage-v1.md)는 실제 저장된
조사·원천/문맥·경제 후보와 사용자 소유·이용 선언, 작성된 계산 입력/해시를
하나의 불변 작업 의도로 묶고 현재 권한·참조를 재검사한다
([실제 SCRAM 검증](../research/farm-authoring-storage-implementation.md)).
새 스냅샷 독립 검토/해제·작업자/평가·공개 API/작성 화면은 계속 후속이다.
[작성 입력 열 궤적 후보](../contracts/farm-thermal-candidate-v1.md)는 저장 판본의
현재 권한·원천 재검사 전후에 120개 수치 시점을 완주하고 원본 합성 엔진과
전 시점 일치 및 재계산을 확인했다
([검증 기록](../research/farm-thermal-candidate-implementation.md)).
결과는 게시 전 후보이므로 위 체크와 G1·3D 수용은 그대로 둔다.
[작성 입력 검토 접수 후보](../contracts/farm-authored-review-v1.md)는 현재 등록·권한과
두 궤적 해시를 검토 작업의 불변 입력·서버 CLI 판단 계약에 연결한다
([실제 SCRAM 검증](../research/farm-authored-review-implementation.md)).
공유 CLI 라우터의 선택적 경로와 동일 저장소 결속을 검증했다. 운영 조립·실제
제품 CLI 실행·독립 해제·Run 게시가 남아 전체 작업 체크는 유지한다.
[완료 검증 후보](../contracts/farm-authored-review-completion-v1.md)는 실제 저장된
작업·판단·캡처·서명 실행 증거를 대사한다
([합성 CLI/키 검증](../research/farm-authored-review-completion-implementation.md)).
실제 제품 CLI·독립 해제·Run/3D 연결과 기존 수용 체크는 유지한다.
[독립 해제 검증 후보](../contracts/farm-authored-release-v1.md)는 현재 코드·입력,
별도 검토자 서명과 세 보고서·참조 원문 해시를 묶는다
([합성 증거 시험](../research/farm-authored-release-implementation.md)).
실제 검토자 발급·그 패킷의 영속 보존/게시·제품 CLI/G1·3D는 여전히 수용 전이다.
[해제 패킷 저장 후보](../contracts/farm-authored-release-store-v1.md)는 실제
SCRAM 권한 역할에서 합성 서명 바이트를 변경 불가로 보존하고 현재 근거를 재검사한다
([집중 시험](../research/farm-authored-release-store-implementation.md)).
독립 발급·실제 CLI·작성 Run 게시/3D와 기존 수용 체크는 유지한다.

`economic-break-even`/`api-flow`의 후속 코드 수용에는 큰 격자의 전체 완료 검증을 비동기 접수·작업 조회·결과 읽기로 분리하는 경로가 포함된다. 현재 동기 읽기는 원천·권리와 원장 전체를 재검사하므로 2개 시험의 성공이나 HTTP 바이트 제한을 256개 시험의 처리량 증거로 쓰지 않는다. 기존 30초 요청 제한 아래 재확인·취소·권리 철회·최대 격자 부하를 검증하고, 준비 전 운영 성능을 보류한다.

[재계산 참조 기록 후보](../contracts/break-even-replay-evidence-v1.md)를 실제 저장 계획·전체 시장/원장 재생에 연결했다. 참조의 원본 대신 식별자/해시를 기록하고 권리 철회·제공자 교체·코드 변경·취소 및 기존 격자를 [집중 43개](../research/break-even-replay-evidence-implementation.md)로 확인했다. 불변 비동기 작업/게시·완료 조회와 실제 256개 격자 부하는 후속이며, `economic-break-even`/`api-flow` 체크를 해제하지 않는다.

[256개 결과 바이트 경계 보완](../research/break-even-capacity-implementation.md)은 기존 1 MiB 결과 한도와 64 KiB 입력 한도를 분리해 집중 6개로 확인했다. 큰 격자의 원천은 메모리 fixture이며 256개 SCRAM 작업자 부하 증거는 아니다.
[비동기 검증 접수·작업자 후보](../contracts/break-even-verification-v1.md)는 실제 완료 계산의 해시와 현재 구현을 불변 입력에 묶고, 전체 재계산을 최종 작업 잠금 밖에서 수행한 뒤 테넌트 비공개 참조 증거·작은 영수증·완료를 원자 게시한다([구현·검증 기록](../research/break-even-verification-implementation.md)). 기존 공개 결과 읽기는 계속 전체 재계산을 요구한다. 다음 순서는 현재 권리·부모·참조를 검사하는 완료 조회, 보호된 운영자/HTTP·웹 연결, 실제 256개 격자 부하·취소·재시도·철회 검증이다. 전체 작업 체크와 관문은 유지한다.

[완료 검증 결과 조회 후보](../contracts/break-even-verified-result-v1.md)는 실제 작업/게시/비공개 증거와 현재 부모·참조·권한을 검사하고 기존 조건부 금액 문자열을 반환한다. 시장·원장·손익분기 재계산을 끈 실제 SCRAM 비교와 변조/철회·실제 불허 권한 추가 및 저장소 회귀를 [집중 11개](../research/break-even-verified-result-implementation.md)로 확인했다. 경제·시장 참조는 한 인증 연결에서 조회하고 마지막 전체 권한 감사를 유지한다. HTTP/운영자·웹과 실제 256개 부하/30초 제한 검증, 독립 CLI/G1/G4는 후속이며 전체 작업 체크는 유지한다.

[비동기 검증 HTTP·보호된 작업자 후보](../contracts/api-break-even-verification-v1.md)는 4 KiB의 실제 완료 계산 UUID 요청과 기존 결과 읽기 권한을 표준 HTTPS 조립에 연결했다. 작업자/OpenAPI 69개와 실제 SCRAM·HTTP/별도 Python 작업자 4개를 확인했다([기록](../research/api-break-even-verification-implementation.md)). 2개 시험의 HTTPS 전체 응답 5개 최대는 0.5033초이며 30초 제한을 유지했다. SDK/웹·실제 256개 부하·취소/재시도/권리 철회와 운영·독립 CLI/G1/G4는 후속이다. 전체 작업 체크는 유지한다.

서버 판본 `160118c`의 [호스팅 전체 백엔드 수용 기록](../research/api-break-even-verification-implementation.md#terminal-hosted-backend-at-160118c)은 PostgreSQL 18.6의 6개 묶음·동일 전체 목록을 대사해 **2,290 passed, 0 skipped**와 별도 Linux UID **4 passed**, 모든 DB/비밀번호 정리 성공을 확인했다. 같은 판본의 작성 7개 묶음 141회·웹 154/50개·C0도 통과했다. 후속 웹·계산 잠금 수정과 실제 256개 부하는 별도 판본/검증이며 전체 작업 및 독립 관문 체크는 유지한다.

[SDK·웹 비동기 검증 후보](../contracts/web-break-even-verification-v1.md)는 실제 계산 완료 뒤 검증 작업을 요청하고, 같은 부모의 미확인 접수와 별도 검증 상태·완료 결과를 연결했다. 웹 단위 160개·전체 Chromium 51개와 모바일 미확인/대기 상태를 확인했다([기록](../research/web-break-even-verification-implementation.md)). 실제 SCRAM·HTTPS/별도 Python 작업자의 브라우저 3개도 통과했고 SDK 전체 본문 44개 최대는 10.3936초다. 최대 256개 부하·30초 응답·취소/재시도/철회, 자동 운영자·독립 CLI/G1/G4의 기존 수용을 계속 확인한다. 전체 작업 체크는 유지한다.

[계산 완료 잠금 보완 후보](../research/break-even-calculation-fence-implementation.md)는 최종 전체 재계산이 취소 요청을 막는 실제 DB 반례를 확인하고, 두 계산은 잠금 밖에서 수행하며 완료 거래는 관측 참조·현재 권리와 검사된 계획 행을 대사하도록 연결했다. 집중 취소 시험은 RED→GREEN이며 원자성·늦은 변경·기존 읽기·재생의 집중 회귀 45개가 통과했다. 실제 256개 접수·작업자·30초 조회·취소/재시도/철회, 자동 운영 조립과 독립 CLI/G1/G4의 기존 수용 체크는 유지한다.

[경제 화면 계약](../contracts/web-economic-workspace-v1.md)과 [검증 기록](../research/web-economic-workspace-implementation.md)은 사용자 소유 숫자 가정의 새 판본 등록, 실제 원장·공동 충격 선택, 시나리오/계산 접수와 완료 서버 금액·보류 조회를 연결한다. 금액은 서버 문자열/null을 그대로 표시하며 응답 유실은 같은 단계의 입력·키로 재확인한다. 새 숫자의 권리·공동 가정 판본 등록·선택 후보를 추가했다([기록](../research/web-joint-amendment-implementation.md)). [월별 현금 조회 후보](../contracts/api-economic-cash-flow-v1.md)는 같은 완료 증명·읽기 권한·원장 재계산을 검사하고 한국 월 구분·UTC 최저 잔액 시각을 표로 연결한다([검증 기록](../research/web-economic-cash-implementation.md)). [손익분기 화면 후보](../contracts/web-break-even-workspace-v1.md)는 실제 저장 판매·수금과 순서가 있는 공동 가정 판본을 계획·완료 결과에 연결하며, 응답 유실 시 고정 제출 해시로 저장 접수 기록을 조회한다([검증 기록](../research/web-break-even-workspace-implementation.md)). 일반 원장·정산 작성, 전체 농장 입력, 자동 시험 가정 생성·새로고침/미저장 접수 복구·실제 CLI·최종 작물 평가·3D/전체 G1과 독립 G0/G2/G3/G4 수용은 남아 있다. 기존 작업 체크와 관문을 해제하지 않는다.
