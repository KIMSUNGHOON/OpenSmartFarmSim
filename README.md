# OpenSmartFarmSim

지역을 고르면 기상·시설·작물·시장 자료의 출처를 확인하고, 온실 시나리오를 계산해 3D로 재생하며, **평가한 작물 중 어떤 선택이 목표에 가장 맞는지** 근거와 불확실성을 설명하는 오픈소스 프로젝트입니다. 수확 시점의 수요·공급과 거시 비용 변화도 재배 결정의 조건으로 다룹니다.

**현재 상태: C0 실행 기본 구조 검증 완료, 합성 계산·조건부 경제·조사/수집·API와 첫 내부 3D 연결 구현 중 (2026-09-30).** [C0 GitHub Actions 실행](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/36303540834)에서 Compose 이미지 빌드와 PostgreSQL 재생성 뒤 데이터 보존을 확인했습니다. 내부 웹 후보가 있으며 검증된 추천 모델은 아직 없습니다. **사업성은 핵심 기능**입니다. 첫 내부 시범은 입력한 판매량·가격·비용을 바탕으로 조건부 마진·손익분기·월별 현금 부족을 계산하고, 수급·거시 자료는 결정 시점에 알 수 있던 시장 시나리오의 근거로 제시합니다. 수확기의 가격·판매량·미래 이익 예측과 작물별 수익 순위는 각각 독립 검증 후에만 엽니다. 초기에 지원할 범위는 **대한민국의 좌표 한 점·온실 한 구역·과거 기상 재현**입니다. 첫 계산은 온실의 온도·습도·설비 반응과 모델이 계산한 난방 열수요/공급열을 다룹니다. 실제 연료·전력 사용량은 설비 효율이나 계량 근거가 확인되기 전까지 표시하지 않습니다. 식물 생장·수확·순이익도 현장 검증 전까지 예측 결과로 내지 않습니다.

작물 순위에는 **같은 지역·시설·평가 기간·목표에서 여러 후보를 비교한 독립 검증 자료**가 필요합니다. 이를 확보하는 일은 외부 협력에 달려 있으며, 작물별 모델만 따로 검증해 순위를 열지 않습니다. 각 평가에서 입력 실행과 후보의 자료·모델·현장·비교 관문(G0~G3)을 다시 확인합니다. 근거가 부족하면 **판단 보류**와 필요한 자료를 보여줍니다. G4 운영·권리·설치 검증 전 단계는 내부 시범이며 공개 production 서비스가 아닙니다.

## 현재 내부 웹 구현

합성 3D 재생은 [로컬 데모 실행법](web/README.md#지금-3d를-직접-보기)에 따라 브라우저에서 직접 볼 수 있습니다. 이 화면은 실제 농장 계산·자료 조사·작물 추천의 시연이 아닙니다.

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
[작성 농장 웹 작업 후보](research/authored-farm-web-workflow-implementation.md)는 농장 수치와 권리 선언을 직접 입력해 등록하고, 저장된 판본을 조회해 검토·열 계산 작업을 접수하며, 완료된 저장 Run의 3D 화면으로 이동합니다. 작성 폼은 기존 조사·원본·시장 보류·경제 판본의 식별자를 요구하는 내부 도구이며 이 자료를 자동으로 찾거나 농업 수치를 제안하지 않습니다. 합성 HTTP Chromium 시험과 로컬 PostgreSQL 16.15/SCRAM·HTTPS 전체 소프트웨어 경로가 통과했고 호스팅 백엔드 CI는 확인 중입니다. 실제 제품 CLI·독립 해제와 G1 수용은 남아 있습니다.
[작성 Run 조회 API 후보](contracts/api-authored-thermal-run-v1.md)는 완료 작업과 별도 작성 Run ID를 인증된 요약·120시점 열 응답에 연결합니다([시험 기록](research/api-authored-thermal-run-implementation.md)). [작성 Run 3D 화면 후보](contracts/web-authored-thermal-replay-v1.md)는 브라우저의 실제 3D·그래프·표를 같은 저장 시점에 연결하고 합성 응답으로 확인했습니다([화면 캡처](research/artifacts/authored-thermal-replay-desktop.png), [검증 기록](research/web-authored-thermal-replay-implementation.md)). [표준 HTTPS 작성 Run 조립 후보](contracts/api-runtime-authored-run-v1.md)와 저장 Run→HTTPS→브라우저의 별도 합성 시험도 있습니다. 작성 폼부터 이 화면까지 하나로 연결한 사용자 흐름, 실제 제품 CLI·독립 해제/G1은 남아 있습니다.
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

사용자는 농업 배경지식이 없어도 범위와 한계를 이해할 수 있어야 합니다. **Codex CLI `gpt-6-sol` `xhigh`는 개발 중 조사·설계에도, 배포 제품에서 지역 선택 후의 자료 조사·수집 판단과 작물 판단에도 필수**입니다. [런타임 작업자 계약](docs/ARCHITECTURE.md#필수-codex-cli-런타임-작업자)에 호출·격리·기록·실패 시 보류를 명시했습니다. 실제 배포 계정의 모델 접근, 인증·계약 조건, 한도·비용은 아직 검증되지 않아 공개 출시 전에 확인해야 합니다. 계산 모델의 고정 입력 재실행과 새 AI 판단은 서로 다른 작업입니다.
