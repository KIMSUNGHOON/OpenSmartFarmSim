# OpenSmartFarmSim

지역을 고르면 기상·시설·작물·시장 자료의 출처를 확인하고, 온실 시나리오를 계산해 3D로 재생하며, **평가한 작물 중 어떤 선택이 목표에 가장 맞는지** 근거와 불확실성을 설명하는 오픈소스 프로젝트입니다. 수확 시점의 수요·공급과 거시 비용 변화도 재배 결정의 조건으로 다룹니다.

**현재 상태: C0 실행 기본 구조 검증 완료, 합성 계산·조건부 경제·조사/수집·API와 첫 내부 3D 연결 구현 중 (2026-10-04).** [C0 GitHub Actions 실행](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/36303540834)에서 Compose 이미지 빌드와 PostgreSQL 재생성 뒤 데이터 보존을 확인했습니다. 내부 웹 후보가 있으며 검증된 추천 모델은 아직 없습니다. **사업성은 핵심 기능**입니다. 첫 내부 시범은 입력한 판매량·가격·비용을 바탕으로 조건부 마진·손익분기·월별 현금 부족을 계산하고, 수급·거시 자료는 결정 시점에 알 수 있던 시장 시나리오의 근거로 제시합니다. 수확기의 가격·판매량·미래 이익 예측과 작물별 수익 순위는 각각 독립 검증 후에만 엽니다. 초기에 지원할 범위는 **대한민국의 좌표 한 점·온실 한 구역·과거 기상 재현**입니다. 첫 계산은 온실의 온도·습도·설비 반응과 모델이 계산한 난방 열수요/공급열을 다룹니다. 실제 연료·전력 사용량은 설비 효율이나 계량 근거가 확인되기 전까지 표시하지 않습니다. 식물 생장·수확·순이익도 현장 검증 전까지 예측 결과로 내지 않습니다.

작물 순위에는 **같은 지역·시설·평가 기간·목표에서 여러 후보를 비교한 독립 검증 자료**가 필요합니다. 이를 확보하는 일은 외부 협력에 달려 있으며, 작물별 모델만 따로 검증해 순위를 열지 않습니다. 각 평가에서 입력 실행과 후보의 자료·모델·현장·비교 관문(G0~G3)을 다시 확인합니다. 근거가 부족하면 **판단 보류**와 필요한 자료를 보여줍니다. G4 운영·권리·설치 검증 전 단계는 내부 시범이며 공개 production 서비스가 아닙니다.

## 현재 내부 웹 구현

[손익분기 비동기 검증 화면 후보](contracts/web-break-even-verification-v1.md)는
계산 완료 확인 → 검증 작업 요청 → 별도 검증 상태 → 현재 완료 결과 조회를 연결합니다.
검증 접수 응답을 잃으면 같은 계산 작업으로 재확인하며, 완료 전·취소·불일치에는
금액을 표시하지 않습니다([검증 기록](research/web-break-even-verification-implementation.md)).
최대 256개 취소/재시도/원천 권리 철회, 자동 운영 조립과 독립 CLI/G1/G4는 남아 있습니다.
[접수 성능 보완](research/break-even-admission-performance-implementation.md)은
같은 256개 ASGI 접수를 29.5103초로 확인했고, 집중 47개와 작업자·현재 결과 조회·
두 시험값의 실제 TLS 11개가 통과했습니다. 접수 보완 판본의 호스팅 백엔드 2,306개·
별도 UID 4개, 작성 141회·웹 160/51·C0도 통과했습니다. 실제 최대 HTTPS의
30초 시간 초과 반례는 입력 검사 보완 후 같은 256개 표준 인증 HTTPS 접수
29.6373초·동일 재접수 29.0140초로 로컬 통과했습니다. 같은 256개의 보호된 로컬 전체 경로도
75분 27초에 통과했습니다. 별도 계산·검증과 전체 결과 조회, 동일 접수 재사용·
현재 문맥 변경 후 금액 비표시·정리를 확인했습니다. 최초 접수 여유는 0.3627초로,
동시 처리량이나 production 응답 여유를 확인한 것은 아닙니다.

[경제·손익분기 작업 발견](contracts/deterministic-job-discovery-v1.md)은 고정 계정의
대기 작업을 읽기 전용 페이지로 찾고 기존 작업자가 임대·복구·완료를 처리하게 합니다.
실제 SCRAM을 포함한 집중 47개가 통과했습니다.
[자동 전경 소비](contracts/deterministic-worker-loop-v1.md)도 별도 Python/SCRAM을 포함한
37개 시험으로 경제·손익분기 계산/검증·종료·취소·강제 종료 뒤 회복을 확인했습니다.
[보호된 운영자 구성](contracts/operator-config-v1.md)은 명시적 비밀 파일과 신뢰된
의존성 factory를 기존 API에 전달합니다. 집중 45개로 파일/구성 검사, 실제 SCRAM·
표준 HTTPS/Bearer 기동·접수/조회·기동 후 권한 변경 차단·종료/정리를 확인했습니다.
발견·소비 판본 `c9bc689`의 호스팅 웹 160/51·작성 141회·C0는 통과했습니다.
전체 백엔드는 여섯 파트 성공 뒤 목록 해시 집계 실패로 수용을 보류했습니다.
[시험 목록 안정화](research/backend-inventory-repeatability-implementation.md)는 수집 시 생성한
UUID를 고정하고 새 전체 목록 회귀를 추가해 집중 18개와 여섯 동일 수집을 통과했습니다.
`4867c1f`의 실제 호스팅 백엔드 2,436개·별도 UID 4개와 모든 동일 목록/집계·정리,
작성 141회·웹 160/51·C0도 통과했습니다. 구성·발견·전경 소비의 소프트웨어 회귀를 수용했습니다.
[앱 이미지 수용](research/application-images-implementation.md)은 별도 target의 실제 Docker 빌드,
비특권 UID·읽기 전용·닫힌 기동·표준 TLS/잘못된 상위 DNS 거부와 정리를 확인했습니다.
[API·웹·자동 경제 작업자 Compose 후보](contracts/application-compose-runtime-v1.md)를 추가했고,
실제 서비스의 TLS/SCRAM 접수→자동 완료→현재 결과→동일 재시작·권한 변경 차단과
[정리도 통과했습니다](research/application-compose-runtime-implementation.md). 수집/CLI 운영 연결,
독립 자격증명 소유권·실제 제품 CLI/G1/G4는 후속입니다.
[조사 RPC 반복 소비](research/cli-dispatch-loop-implementation.md)는 실제 소켓 시험36개와
기존 결정적 소비37개, `7225546`의 전체 호스팅 백엔드2,455/별도UID4·작성141·웹160/51·
C0/앱 서비스 회귀를 통과했습니다. [수집 자동 소비](research/collection-consumer-implementation.md)도
실제 SCRAM95개로 자동 완료·취소/복구·부모 증거 훼손/권한 철회·정리를 확인했습니다.
같은 `394ff78`의 전체 hosted 백엔드2,489/별도UID4·작성141·웹160/51·C0/앱과 정리도 통과했습니다.
[수집 Compose 단계](research/collection-compose-runtime-implementation.md)는 실제 TLS/SCRAM 자동 저장·
동일 재시작·부모 증거 철회/권한 변경 차단·UID/자원과 정리를 통과했습니다.
같은 workflow의 조사 RPC 단계는 실패 원인을 수정 중이며, 실제 모델·독립 해제/G1/G4는 후속입니다.

[원천→농장 참조 제공자](contracts/source-farm-selection-v1.md)는 정확한 완료 조사·수집에서
이미 저장된 원본 스냅샷과 서명 문맥을 검증한다([SCRAM 집중 4개](research/source-farm-selection-implementation.md)).
같은 참조의 [인증 API](contracts/api-source-farm-selection-v1.md)와 표준 HTTPS 조립도
[집중 66개](research/api-source-farm-selection-implementation.md)로 확인했다.
같은 원천 문맥의 [저장 경제 후보 목록/현재 선택](contracts/farm-economic-candidate-selection-v1.md)과
[인증 API](contracts/api-farm-economic-candidate-selection-v1.md)도
[SCRAM 5개](research/farm-economic-candidate-selection-implementation.md)와
[집중 64개·실제 HTTPS 20개 전체 응답](research/api-farm-economic-candidate-selection-implementation.md)으로 확인했다.
조회는 새 입력이나 승인을 발급하지 않는다. [농장 작성 화면 연결 후보](research/source-farm-web-implementation.md)는
저장된 완료 조사·수집과 경제 판본을 선택하고 참조만 읽기 전용으로 옮긴다.
조합 변경·동의 취소·응답 유실·재연결을 집중 Chromium 14개로 확인했으며
실제 HTTPS/SCRAM 신규 등록→검토/Run→3D의 두 경로도 통과했다.
같은 새 Run의 서버 금액·월별 현금·평가 보류·재접속·동일 3D도
[실제 HTTPS/SCRAM 집중 1개](research/source-farm-financial-continuation-implementation.md)로 확인했다.
같은 새 Run 연결의 호스팅 작성 7개 묶음·웹/C0도 통과했다.
[화면 보완](research/source-farm-layout-refinement-implementation.md)은 참조 상세 펼치기,
넓은 화면의 나란한 요약과 키보드 구역 이동을 확인했다.
`93e30a7`의 [최종 UI 소프트웨어 수용](research/source-farm-web-implementation.md#final-software-ui-acceptance-2026-10-01)은
호스팅 웹 154/50개와 작성 브라우저 4개에서 저장 원천 선택→신규 농장 등록→경제/평가·동일 3D를 확인했다.
본문 최대 26.3284초이며 낮은 디자인 일치율은 기록된 한계다. 별도 경제 브라우저 1개 실패와
[후속 권한 감사 지연 보완](research/runtime-role-audit-batching-implementation.md#all-role-query-batching-follow-up-2026-10-01)은
분리하여 검증한다. `7f49f52`에서 작성 7개 묶음 139회·웹/C0가 통과했고 별도 경제 브라우저의
29개 전체 본문 최대는 17.0664초다. 같은 판본의 전체 백엔드 2,253개·UID 4개와 정리가 통과해
권한 감사 보완을 소프트웨어 범위에서 수용했다. 실제 제품 CLI·독립 G1/G4 수용은 남아 있다.

[07 작성 Run 경제·평가](contracts/web-authored-economic-assessment-v1.md)는 저장 Run을 선택해
같은 농장에 고정된 V3 경제 입력으로 계산을 요청하고, 서버 금액·월별 현금·보류 6개·같은 3D Run을 확인한다.
재연결 후 저장 기록을 선택할 수 있으며 미확인 접수는 같은 요청으로 재확인한다
([웹 단위 122개·집중 Chromium 19개·실제 HTTPS/SCRAM 브라우저 1개](research/web-authored-economic-assessment-implementation.md)).
시험용 CLI·서명의 소프트웨어 범위다. 일반 지역 흐름과 실제 제품 CLI·독립 G1/G4는 남아 있다.

[작성 Run의 경제 입력·작업 이력 조회](contracts/authored-financial-selection-v1.md)는
현재 농장에 고정된 경제 입력 V3와 같은 Run의 경제·평가 작업을 서버에서 다시 찾는 웹 선행 기능이다
([집중 시험 59개](research/authored-financial-selection-implementation.md)).
이력 선택 뒤에는 실제 결과를 현재 권리로 다시 조회해야 한다. 위 07 화면이 이 조회와 작성 경제·평가를 연결한다.

[작성 Run의 경제 실행 후보](contracts/authored-economic-execution-v1.md)는 현재 농장 판본과
실제 완료 작성 Run을 별도 경제 입력/영수증 V3에 묶고 기존 금액·월별 현금 조회를 제공한다
([SCRAM·HTTPS/OpenAPI 검증](research/authored-economic-execution-implementation.md)).
작성 Run의 공통 평가 서버 연결도 아래 후보에 추가했다. 웹 부모 선택은 위 07 후보에 연결했고 실제 제품 CLI·독립 G1은 후속이다.

[작성 Run 평가 연결 후보](contracts/authored-calculation-assessment-v1.md)는 실제 완료 작성 열·경제 작업을
평가 입력 V3에 고정하고 별도 CLI 검증기로 기존 보류 6개를 저장·조회한다
([SCRAM·HTTPS 검증](research/authored-calculation-assessment-implementation.md)).
현재 권리·해제·입력 해시와 부모의 문맥을 재검사하며 혼합·변조·늦은 변경을 거부한다.
가짜 CLI와 시험 서명으로 확인한 서버 경로이며 실제 제품 CLI·독립 G1은 남아 있다.

[06 계산 평가 화면](contracts/web-calculation-assessment-v1.md)은 같은 조건의 완료 열·경제 작업을 서버에 접수하고, 저장된 평가 상태·보류 근거를 조회하거나 재연결 후 다시 엽니다([실제 HTTPS/SCRAM·브라우저 증거](research/web-calculation-assessment-implementation.md)). 현재 운영자 작업 식별자 입력 경로이며 일반 지역 흐름의 자동 연결, 작성 농장의 웹 경제·평가 부모 선택과 실제 제품 CLI·독립 G1 수용은 남아 있습니다.

합성 3D 재생은 [로컬 데모 실행법](web/README.md#지금-3d를-직접-보기)에 따라 브라우저에서 직접 볼 수 있습니다. 이 화면은 실제 농장 계산·자료 조사·작물 추천의 시연이 아닙니다.

[지역 조사→원본 수집→수집 입력 검토 화면 후보](research/web-owned-source-workflow-implementation.md)를 내부 웹에 연결했습니다. 실제 서버 작업 상태와 검토 보류를 단계별로 조회하지만, 합성 자료 작업 완료가 실제 원천 G0 승인이나 Run 게시를 뜻하지는 않습니다.
[저장된 원천 작업 이력 후보](contracts/api-owned-source-history-v1.md)는 재연결 뒤 같은 계정의 조사 기록을 찾고 선택한 조사의 최근 수집·검토 작업과 이전 시도 목록을 복원합니다([소프트웨어 검증](research/owned-source-history-implementation.md)). 현재 원천·문맥을 확인할 수 없는 기록은 이력으로만 보이며 새 접수는 보류합니다.

[첫 웹 화면](web/README.md)은 등록된 합성 좌표·UTC 기간의 조사 요청, 실제 작업 상태와 보류 근거 조회를 구현한 후보입니다. [경제 화면](contracts/web-economic-workspace-v1.md)은 저장 가정 조회·새 숫자 판본 등록, 선택 원장/수급·거시 공동 가정의 계산 요청과 완료 서버 결과를 연결합니다. 새 숫자의 권리 확인·공동 가정 판본 등록·선택과 [월별 현금 조회](research/web-economic-cash-implementation.md)를 연결하는 후보를 추가했습니다. [손익분기 화면 후보](contracts/web-break-even-workspace-v1.md)는 기존 판매·수금과 저장된 시험 판본을 선택하고 계획·완료 결과를 조회하며 응답 유실 시 저장 접수 기록을 확인합니다([검증 기록](research/web-break-even-workspace-implementation.md)). 일반 원장·정산 작성, 지역 선택에서 농장 작성까지의 자동 연결, 자동 시험 가정 생성과 새로고침 후 복구는 남아 있습니다. [첫 웹 검증 기록](research/web-location-shell-implementation.md)에는 실제 HTTPS API·PostgreSQL과 브라우저 연결 시험이 있습니다. 그 시험의 CLI는 직접 작성한 가짜 실행기이며 실제 모델·전체 농장/경제 입력·3D를 포함한 종단 간 G1·공개 운영 수용은 남아 있습니다.

열·경제 입력을 함께 고정하는 [농장 재생 계획 등록 후보](contracts/farm-replay-scenario-v1.md)를 추가했습니다. 등록된 조사 좌표·기간, 열 시나리오와 경제 판본의 해시, 서명 문맥·결정 시각·시장 보류를 검사하고 실제 작업 저장소에 변경 불가 입력을 남깁니다([검증 기록](research/farm-replay-scenario-implementation.md)). 등록은 입력 선택 의도이며 전체 농장 작성·열과 비용의 물리적 결합·공통 평가 연결·3D·전체 G1 수용은 남아 있습니다.

[농장 계획을 사용하는 열 실행 후보](contracts/farm-thermal-execution-v1.md)는 새 입력/영수증 v3로 접수·계산·완료 조회를 연결합니다. 같은 계획 판본과 실제 완료 조사·수집·검토의 연결을 재검사하며, 현재 권한이 없거나 다른 조사 작업이면 보류합니다([소프트웨어 검증](research/farm-thermal-execution-implementation.md)).

[농장 경제 실행 후보](contracts/farm-economic-execution-v1.md)는 같은 계획과 실제 완료 열 작업을 경제 입력/영수증 v2에 연결하고, 금액·월별 현금 조회에서도 현재 연결을 검사합니다([검증 기록](research/farm-economic-execution-implementation.md)). 전체 평가·열과 구매 에너지/비용의 물리적 결합·실제 CLI와 독립 G1/G4 수용은 남아 있습니다. [첫 내부 3D 열 재생 뷰어](contracts/web-thermal-replay-v1.md)를 구현했습니다. 저장된 합성 계산의 온도·습도·모델 열수요/공급열을 같은 시각의 장면·그래프·표로 확인합니다([검증 기록](research/web-thermal-replay-implementation.md)). 실제 서버 Run 연결과 WebGL 장애 시 HTML 대체를 시험하는 내부 후보이며, 작물 생장·수확 예측과 전체 G1/G4 수용은 남아 있습니다. [공통 Assessment 연결 후보](contracts/farm-calculation-assessment-v1.md)도 구현했습니다. 실제 HTTPS 접수·재요청과 가짜 CLI 보류 조회, 혼합 거부·거래 롤백·기존 경로 호환 시험을 확인했습니다([진행 기록](research/farm-calculation-assessment-implementation.md)). 전체 농장 입력 작성의 [첫 제공자](contracts/farm-inputs-v1.md)를 구현했습니다. 명시적 시설·제어값을 실제 열 수식 입력으로 변환하고 재배 면적·달력과 경제 배치/날짜 범위를 검사합니다([검증 기록](research/farm-inputs-implementation.md)). [내부 영속 등록 후보](contracts/farm-authoring-storage-v1.md)는 실제 조사·문맥·경제 후보와 사용자 권리 선언, 작성한 계산 입력을 변경 불가 판본으로 묶습니다([검증 기록](research/farm-authoring-storage-implementation.md)). 작성된 스냅샷의 독립 검토·해제, 실제 작업자 실행, 공개 API와 전체 작성 화면 연결은 다음 단계입니다.

[작성 입력 열 궤적 후보](contracts/farm-thermal-candidate-v1.md)는 저장된 농장 판본에서 120개의 온도·습도·공급열 계산 시점을 재현합니다([검증 기록](research/farm-thermal-candidate-implementation.md)). 이 후보 자체는 승인 Run이나 3D 게시 대상이 아닙니다.
[작성 입력 검토 접수 후보](contracts/farm-authored-review-v1.md)는 이 궤적의 입력·두 결과 해시를 기존 CLI 검토 작업에 묶습니다([검증 기록](research/farm-authored-review-implementation.md)). [완료 검증 후보](contracts/farm-authored-review-completion-v1.md)는 저장된 결정·캡처·서명 실행 증거를 대사합니다([시험 기록](research/farm-authored-review-completion-implementation.md)). [독립 해제 검증 후보](contracts/farm-authored-release-v1.md)는 현재 코드·입력과 별도 검토자의 서명·보고서 원문을 묶고, [영속 저장 후보](contracts/farm-authored-release-store-v1.md)가 패킷을 변경 불가하게 보존·재검사합니다([시험 기록](research/farm-authored-release-store-implementation.md)). 실제 제품 CLI 실행과 독립 해제 발급·G1 수용은 후속입니다.
[작성 입력 Run 준비 후보](contracts/farm-authored-run-preparation-v1.md)는 유효한 저장 해제와 현재 농장 판본을 다시 확인한 뒤 120개 계산 시점의 최종 두 궤적·해시·Run ID를 준비합니다([시험 기록](research/farm-authored-run-preparation-implementation.md)). 이후 작성 작업자가 이 바이트를 게시하고 별도 API·3D 화면이 조회할 수 있습니다. [합성 서비스·브라우저 연결 시험](research/authored-full-software-path-implementation.md)은 미리 등록한 판본 조회부터 브라우저의 신규 검토·계산 작업 접수, 시험용 CLI 검토·서명 해제, 저장 Run의 실제 Chromium 3D 재생까지 확인했습니다. 사용자 농장 작성·수집과 실제 제품 CLI·독립 해제는 아직 한 흐름으로 검증되지 않았습니다.
[작성 Run 저장 후보](contracts/farm-authored-run-store-v1.md)는 별도 불변 테이블에서 작업 완료와 원자 저장·재조회를 검사합니다([시험 기록](research/farm-authored-run-store-implementation.md)). 제품 CLI·독립 검토 발급과 전체 G1 증거는 남아 있습니다.
[작성 simulation 접수 후보](contracts/farm-authored-simulation-v1.md)는 현재 작성 입력·서명 해제·최종 궤적을 다시 확인하고 동일 요청을 변경 불가 작업 하나로 등록합니다([시험 기록](research/farm-authored-simulation-implementation.md)).
[작성 simulation 작업자 후보](contracts/farm-authored-simulation-worker-v1.md)는 임대한 작업의 Run·영수증·완료를 같은 거래에서 게시하고, 취소·만료·오류 때 부분 Run을 되돌립니다([SCRAM 시험](research/farm-authored-simulation-worker-implementation.md)). 현재 시험은 가짜 CLI와 합성 해제를 사용합니다. 실제 제품 CLI·독립 해제/G1은 남아 있습니다.
[작성 농장 웹 작업 후보](research/authored-farm-web-workflow-implementation.md)는 농장 수치와 권리 선언을 직접 입력해 등록하고, 저장된 판본을 조회해 검토·열 계산 작업을 접수하며, 완료된 저장 Run의 3D 화면으로 이동합니다. [저장 판본 목록](research/authored-farm-catalog-implementation.md)에서 같은 계정의 등록 입력을 다시 찾고 선택할 때 현재 권리와 해시를 확인할 수 있습니다. [검토·계산 작업 이력 후보](research/authored-farm-activity-implementation.md)에서 재연결 후 저장된 작업을 선택해 상태와 연결된 Run을 다시 열 수 있습니다. 같은 계정의 [완료 Run 목록](research/authored-run-catalog-implementation.md)도 농장 선택 없이 조회하고, 선택할 때 현재 단건 조회를 거쳐 3D로 이동합니다. 작성 폼은 기존 조사·원본·시장 보류·경제 판본의 식별자를 요구하는 내부 도구이며 이 자료를 자동으로 찾거나 농업 수치를 제안하지 않습니다. 합성 HTTP Chromium 시험과 로컬 PostgreSQL 16.15/SCRAM·HTTPS 전체 소프트웨어 경로가 통과했고 호스팅 백엔드 CI는 확인 중입니다. 실제 제품 CLI·독립 해제와 G1 수용은 남아 있습니다.
[작성 Run 조회 API 후보](contracts/api-authored-thermal-run-v1.md)는 완료 작업과 별도 작성 Run ID를 인증된 요약·120시점 열 응답에 연결합니다([시험 기록](research/api-authored-thermal-run-implementation.md)). [작성 Run 3D 화면 후보](contracts/web-authored-thermal-replay-v1.md)는 브라우저의 실제 3D·그래프·표를 같은 저장 시점에 연결하고 합성 응답으로 확인했습니다([화면 캡처](research/artifacts/authored-thermal-replay-desktop.png), [검증 기록](research/web-authored-thermal-replay-implementation.md)). [표준 HTTPS 작성 Run 조립 후보](contracts/api-runtime-authored-run-v1.md)와 작성 폼→신규 작업→저장 Run→브라우저의 합성 시험도 있습니다. 일반 사용자 원천 입력 흐름, 실제 제품 CLI·독립 해제/G1은 남아 있습니다.
[저장 작성 Run 전체 목록 API 후보](contracts/api-authored-thermal-run-v1.md)는 같은 계정의 완료 Run 식별자를 다시 찾되 현재 표시 가능 여부는 정확한 Run 조회에서 재검사합니다([검증 기록](research/authored-run-catalog-implementation.md)). 내부 웹은 이 목록을 페이지별로 읽고 현재 단건 조회가 실패하면 3D 표시를 보류합니다.
[작성 농장 입력 API 후보](contracts/api-farm-authoring-v1.md)는 기존 불변 입력 등록부에 인증된 등록·재조회 경로를 추가합니다. 합성 자료의 권리와 입력 연결을 현재 시점에 다시 검사하며, 등록 자체는 계산 완료나 작물 추천을 뜻하지 않습니다.
[작성 입력 검토 접수 API 후보](contracts/api-farm-authored-review-v1.md)는 등록된 입력 해시를 다시 확인하고 검토 작업을 대기열에 넣습니다([로컬 검증 기록](research/api-farm-authored-review-implementation.md)). 접수만으로 CLI 검토나 독립 해제가 완료되지는 않습니다.
[작성 Run 접수 API 후보](contracts/api-authored-simulation-admission-v1.md)는 독립 해제 기록이 준비된 판본만 다시 확인해 시뮬레이션 작업을 접수합니다([로컬 검증 기록](research/api-authored-simulation-admission-implementation.md)). 작업자가 완료·게시하기 전에는 3D 조회 결과가 아닙니다.

## 문서 읽는 순서

1. [입문 안내](docs/DOMAIN_PRIMER.md): 농업과 시뮬레이션의 기본 개념
2. [제품 명세](docs/PROJECT_SPEC.md): 사용자 흐름, 추천의 의미, 수용 기준과 단계
3. [자료·연구 기준선](docs/RESEARCH_BASELINE.md): 입력 자료, 출처, 권리, 결측 처리, 모델 근거
4. [아키텍처](docs/ARCHITECTURE.md): 구성 요소, API·작업·실행 기록 계약과 운영 요건
5. [비용·마진 계약](docs/ECONOMICS.md): 가격·원가 증빙, 손익·현금흐름, 손익분기와 검증 경계
6. [시장·거시 명세](docs/MARKET_INTELLIGENCE.md): 수요·공급·출하기 가격과 비용 시나리오, 결정 시점 자료와 전망 검증
7. [기술 스택](docs/TECH_STACK.md): 필수/선택 소프트웨어와 이유, 버전·배포 정책, 외부 의존성
8. [한국어 설계 백서](docs/whitepaper/README.md): 근거·수식·경제 계산과 검증 관문을 통합한 설계 제안
9. [에이전트 작업 지침](AGENTS.md): 개발 판단·증거·검증의 기본 절차
10. [첫 구현 슬라이스](docs/IMPLEMENTATION_SLICE.md): 내부 완주 경로와 시험 가능한 경계
11. [구현 준비 현황](docs/IMPLEMENTATION_READINESS.md): 관측된 도구·자료·권리·외부 증거 상태
12. [구현 순서](tasks/plan.md): 의존성·체크포인트·외부 증거 경로
13. [구현 작업 목록](tasks/todo.md): 작은 작업별 수용 기준과 확인 절차
14. [첫 화면 설계 기준](docs/UI_DESIGN.md): 합성 재생·조건부 경제·보류 표시와 접근성

## 라이선스와 공개 범위

이 저장소에서 새로 작성하는 코드와 문서는 [Apache License 2.0](LICENSE)으로 공개합니다([OSI 승인 목록](https://opensource.org/licenses), [공식 원문](https://www.apache.org/licenses/LICENSE-2.0.txt)). 이 선택은 기상청·FAO·WUR 등의 자료나 외부 라이브러리·3D 자산에 권리를 부여하지 않습니다. 각 자료와 자산은 원래의 이용조건을 따르며, 공개 배포 전에 개별 권리와 출처표시를 확인합니다. 설치 가능한 사용자 서비스는 아직 없습니다. [직접 작성한 합성 입력](fixtures/README.md)은 소프트웨어 계약 시험용으로만 공개하며, 실제 농장 관측·시장 자료나 검증된 예측 결과가 아닙니다.

사용자는 농업 배경지식이 없어도 범위와 한계를 이해할 수 있어야 합니다. **Codex CLI `gpt-6.1-sol` `xhigh`는 개발 중 조사·설계에도, 배포 제품에서 지역 선택 후의 자료 조사·수집 판단과 작물 판단에도 필수**입니다(2026-10-01 변경). [런타임 작업자 계약](docs/ARCHITECTURE.md#필수-codex-cli-런타임-작업자)에 호출·격리·기록·실패 시 보류를 명시했습니다. 기존 DB는 [모델 이전 계약](contracts/cli-model-policy-migration-v1.md)에 따라 과거 실행 기록을 보존하며 변경합니다. 실제 배포 계정의 모델 접근, 인증·계약 조건, 한도·비용은 아직 검증되지 않아 공개 출시 전에 확인해야 합니다. 계산 모델의 고정 입력 재실행과 새 AI 판단은 서로 다른 작업입니다.
