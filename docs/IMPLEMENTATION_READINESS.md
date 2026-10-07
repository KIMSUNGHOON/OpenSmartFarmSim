# 구현 준비 현황

**새 계산 조회 진척 (2026-10-07):** [현재 농장/DB query](../research/crop-cycle-calculation-current-query-implementation-20261007.md)를
실제 SCRAM12개·정상/관리 사건/수치 hold·원량/UTC·철회/변조·fork·63 source/자원 정리로 로컬 수용했다.
후속 [새 공개 투영](../research/crop-cycle-calculation-api-projection-implementation-20261007.md)도 새63개/구형42개·고유105개 분할·
실제25시간/7페이지·원량/UTC·hold·RHS0·import/FD·67 source 보존으로 수용했다.
[runtime factory](../research/crop-cycle-calculation-runtime-factory-20261007.md)도 새19개/기존136개·고유155개 분할,
실제 SCRAM same jobs/farm·재구성/9거부·계산/게시0·원 입력/FD/import·73 source/정리로 수용했다.
[별도 설정 loader](../research/crop-cycle-calculation-operator-loader-20261007.md)도 새57개/기존155개·고유212개 분할,
실제 SCRAM/TLS 파일·명시 flag/재구성·원 파일/FD·75 source/정리로 로컬 수용했다.
[인증 route/OpenAPI](../research/crop-cycle-calculation-route-openapi-20261007.md)도 새63개/관련 회귀221개·고유284개 분할,
원48 path/148 schema·78 source·한 query/투영 뒤 철회·원량/UTC/hold·세 import/FD/정리로 ASGI 자식만 수용했다.
[runtime/실제 TLS](../research/crop-cycle-calculation-runtime-tls-20261007.md)도 실제3개/runtime19개/회귀315개·고유337개 분할,
26 HTTPS 최대5.258614초/23,546bytes·원량/UTC·철회/변조·FD11→11/81 source·정리로 작은 API 부모까지 수용했다.
첫 두 TLS 실패와 실제 source policy/pytest logging FD 원인 확인은 수용 기록에 보존했다.
[새 SDK4파일](../research/web-crop-cycle-calculation-client-20261007.md)도 새178개 포함 웹 전체700개·타입/빌드·
34 공개 JSON/원량·UTC·검증 정보·원101 source/임시 정리로 수용했다. 새 HTTP/브라우저/3D 실행은0이다.
[현재 범위 선택](../research/web-crop-cycle-calculation-window-20261008.md)도 새19개 포함 웹 전체719개·타입/빌드·
원/새 source·검증 정보/UTC·취소/settlement·104 source/정리로 수용했다. 이 단계의 새 HTTP/브라우저/3D는0이다.
[새 같은 UTC 화면](../research/web-crop-cycle-calculation-view-20261008.md)도 새 Chromium15개/기존47개·
웹719개·타입/빌드·원27시점/5사건·113 source/정리로 합성 응답의 화면 부모까지 로컬 수용했다.
새 실제 등록 PG/TLS/WebGL은 [2 core파일 구현/시작](../research/web-crop-cycle-calculation-native-started-20261008.md) 후
기록 응답의 새/기존 브라우저와 실제 세 사례 준비를 통과했다.
[후속25시간 계산 완료 뒤 시험 TLS 만료 실패](../research/web-crop-cycle-calculation-native-tls-hold-20261008.md)를
실제 Vite 검사로 진단하고 계산 후 발급으로 수정했다.
[수정 실행의 실제 기능 검증](../research/web-crop-cycle-calculation-native-observed-20261008.md)은 시험 로그1통과·
34frame·24 HTTPS·원118 source/별도 정리를 확인했다. 원 명령 종료 기록 누락으로 최종 native/웹 부모는 보류다.
앱 CI의 구형 config 필드 거부는 [고유125개 분할·실제 SCRAM/TLS](../research/application-operator-policy-compatibility-20261007.md)로
로컬 수정했으며 [수정 판본의 hosted 세 Compose/정리](../research/artifacts/application-operator-policy-hosted-reference-20261008.json)도
10월8일 수용했다. 구형 판본 CI는
[C0/웹/작성 PG 성공·앱/Backend 실패로 종료](../research/artifacts/crop-cycle-calculation-view-ci-terminal-20261008.json)했다.
Backend 분할5의 설정 fixture도 기존125개 검증 수정에 포함되며 현재 source SHA가 같다.
`f2dc10f`의 [CI 종료 상태](../research/artifacts/full166-calendar-registration-ci-terminal-20261008.json)는
다른4workflow 성공, Backend 분할0/4/5 성공·1/2/3/집계 실패다. [Python·원격 PG 시험 수정](../research/calculation-ci-fixture-compatibility-20261008.md)은
고유19개 집중 검증을 통과했으며 hosted 수용은 별도다.
[작은 등록 누적 비용](../research/crop-cycle-calculation-prefix-cost-observed-20261008.md)은 정상/hold·수정한32회 시험을
분할 확인했다. 3,990걸음·확정9시점/2사건·원값/복원·권리·종료0/정리이며 전체166일 등록 비용 부모는 미수용이다.
[전체166일의 별도 합성 달력 등록](../research/crop-cycle-full166-calendar-registration-20261008.md)은
원750파일/네 stream·값/clock/격자 보존·73개 회귀·실제 SCRAM 농장/경제 달력·현재 권리/기간 거부·RHS0·종료0/정리로 수용했다.
[같은 전체 입력의 초기32회 비용](../research/crop-cycle-full166-prefix-cost-observed-20261008.md)도
3,990걸음·105시점/2사건·원 상태/행·현재 권리·129 source/정리·종료0으로 로컬 수용했다.
[후보 읽기 연결 개선](../research/crop-cycle-candidate-read-scope-implementation-20261008.md)도 고유37개 분할·
연결38→1/원 검증·산술·같은 첫3회60.421→30.737초·원량/권리/정리로 로컬 수용했다.
[입력 재검사 개선](../research/crop-cycle-calculation-recheck-cost-implementation-20261008.md)도 고유199개 분할·
같은 첫3회99→85검사/30.737→29.551초·체크포인트 전체/원량·늦은 변조/철회·복원/정리로 로컬 수용했다.
[개선 판본32회](../research/crop-cycle-calculation-full-budget-observed-20261008.md)는 같은 checkpoint/원량·권리/복원·
263 source/정리·종료0/358.024초로 관측 자식만 수용했다. 두 개선 전 advance575.494→304.344초다.
과거 delta QC2n/합1,056회로 전체 등록 장시간 실행/wall 예산을 보류했다.
[prefix 검증 증명](../research/crop-cycle-calculation-prefix-attestation-implementation-20261008.md)은
재개 입력/HEAD 직전 권한 철회 두 반례를 RED로 확인·복원하고 최종 수정판208개 분할·같은32회 원량/권리·266 source/정리·종료0으로 로컬 수용했다.
delta QC1,056→64회·advance304.344→290.225초·전체339.187초이며 입력 검사839회는 보존했다.
candidate 현재 bytes 검사 뒤 마지막 입력/권한 검사와 atomic HEAD 순서를 검증했다.
[계산 묶음 가능성](../research/crop-cycle-calculation-chunk-feasibility-observed-20261008.md)도 실제1통과/종료0·같은4,096전이/원105출력/2사건·
비계보 checkpoint 전체·2page/954,171bytes·268 source/정리로 수용했다. 제품128전이 제한은 유지했다.
[새 prefix 공개 연결](../research/crop-cycle-calculation-prefix-api-bridge-implementation-20261008.md)도 실제 RED 뒤 수정·
API193개/웹720개/Chromium15개·타입/빌드·새34 JSON/원량/UTC·270 source/종료0/정리로 로컬 수용했다.
[제한된 계산 묶음](../research/crop-cycle-calculation-bounded-chunks-implementation-20261008.md)도 고유177개·
실제4,096전이 저장/3,990걸음/원105출력·2사건·별도 Python 재개·274 source/종료0/정리로 로컬 수용했다.
요청4,096전이/실효128원경계·기존 bytes 한도·명시 서버v3이며 원 수식/격자/현재 권리를 유지한다.
[등록 농장의 두 큰 묶음](../research/crop-cycle-calculation-registered-chunk-cost-observed-20261008.md)도 실제 SCRAM1통과·
8,192전이/7,980걸음·원210출력/4사건·fork 재개·현재 권리/복사 입력 변조 거부·276 source/종료0/정리로 수용했다.
두 advance50.212/47.349초는 초기 구간 관측이다.
[전체 참조 용량](../research/crop-cycle-calculation-full-capacity-observed-20261008.md)도 고유10개·RHS0·456묶음/
전체47,809출력/5사건·예약 포함481,987,541bytes/512MiB·279 source/종료0/정리로 수용했다.
다음은 작은 등록 감독자의 fresh Python 복원 검증이다.9시간은 후속 실험 상한이다.
원 순수 실행의 재분류가 아니다.
전체166일 등록 비용·실제 품종 입력/국내 독립 자료0건과 G0–G4 보류는 유지한다. 아래 날짜별 기록은 당시 상태다.

## 현재 우선순위와 외부 의존성 — 2026-10-04

운영 기반은 `d19f7c0`의 [완료 범위/CI 5개 통과](../research/crop-priority-and-runtime-freeze-20261004.md)로
고정했다. 후속 운영 조립은 핵심 작물 기능/관문에 필요한 증거가 있을 때 재개한다.
[생장 유량 모듈](../contracts/crop-growth-research-v1.md)은
[로컬 86개/0.12초와 독립 참조 대조](../research/crop-growth-rates-implementation.md)로 수용했다.
[작은 수관 적용 정책](../research/crop-photosynthesis-domain.md)은 기존 유량과 함께
118개/0.18초로 수용했고 [프로필/원 고지 이미지 포함](../research/crop-rate-image-inputs-implementation.md)은
실제 hosted Docker 실행/정리로 수용했다. `d251df9`의 전체 backend 2,671개·
별도 UID 4개와 같은 판본 CI 5개도 통과했다. 새 성장 화면 변경의 hosted CI는 별도다.
[시간 적분](../research/crop-growth-integration-implementation.md)은 적분 28개/기존 118개를
합쳐 146개/0.53초·독립 165수치·수렴/수지/사건으로 로컬 수용했다.
[불변 합성 연구 저장](../research/crop-result-storage-implementation.md)까지 집중
172개/434.49초·실제 SCRAM/별도 프로세스·변조/철회/정리로 로컬 수용했다.
[저장 조회 API](../research/api-crop-replay-implementation.md)도 집중 316개/194.11초·
실제 TLS/SCRAM 10개 전체 응답/변조·철회·정리로 로컬 수용했다.
[계산 기반 성장 연구 3D](../research/web-crop-replay-implementation.md)도 웹 209개·
집중 Chromium 10개·실제 저장/HTTPS/장면 대사 1개로 로컬 수용했다.
[실제 파일/채널 감사](../research/crop-forcing-audit.md)도 완료했다. 실제 입력 채택은
시간대/면적·수관/초기기관·사건·형식/결측과 전체 작기 한도 때문에 보류다.
[과실 구획 명세](../research/crop-fruit-cohorts-baseline.md)도 수용했다.
[과실 순간 이동](../research/crop-fruit-transport-implementation.md)도 새 92개/기존 포함
238개·독립 3,090수치로 로컬 수용했다. transport 프로필 포장도 실제 hosted 이미지로 수용했다.
[명시적 착과/진입 질량 배분 정책](../research/crop-fruit-allocation-policy.md)은 독립 대수/수치로
수용했다. [순수 제품 배분](../research/crop-fruit-allocation-implementation.md)도 새 77개/기존 포함
315개·독립 600개 유입/4개 hold로 로컬 수용했다.
[문헌식 수요·50구획 순간 결합](../research/crop-fruit-cohort-rates-implementation.md)도 새 86개/기존 포함
401개·독립 8,592수치로 로컬 수용했다.
[전체 기관의 순간 결합](../research/crop-plant-cohort-rates-implementation.md)도 444개 집중·684수치로 수용했다.
[짧은 시간 적분/관리 사건](../research/crop-plant-cohort-integration-implementation.md)도 488개·1,309수치/해석해 250개로 수용했다.
24시간/512출력은 57.85초·42,124 KiB로 확인했다.
[저장 선행 artifact](../research/crop-coupled-artifact-implementation.md)도 집중 530개,
같은 512출력 3,683,992 bytes·읽기/검사 0.3055초로 수용했다.
[farm/program 결합 DB 저장](../research/crop-coupled-result-storage-implementation.md)도
실제 SCRAM·564개/850.85초·현재 권리/동일 bytes/원자성/변조/철회와 정리로 수용했다.
[페이지 조회 API](../research/api-crop-coupled-replay-implementation.md)는 고유 207개 분할 검증·
실제 HTTPS 19개·최대 11.508339초/649,718 bytes·현재 권리/재시작/정리로 로컬 수용했다.
다음은 [같은 저장 ID/UTC의 50구획 연구 3D](../contracts/web-crop-coupled-replay-v1.md)다.
자동 착과/빈 초기 작기·실제 품종은 보류한다.
전체 작기 실행 계약/국내 확보를 병행한다. `d15cf92`의
[시간 적분/artifact·v2 저장 CI 5개](../research/artifacts/crop-coupled-storage-ci-20261005.json)는
3,070개·별도 UID 4개·동일 목록/여섯 정리·집계까지 통과했다.
새 API·웹 페이지/도형 판본의 hosted와 새 장면/브라우저 수용은 별도다.
순서는 [수정 계획](../tasks/plan.md#작물-생산과-성장-3d-우선순위-2026-10-04)을 따른다.

[단일 Axiany 작기 모델/권리 조사](../research/crop-tomato-model-baseline-20261004.md)와
독립 자료의 [권리·분할 프로토콜](../research/crop-independent-data-protocol.md)을 준비했다.
일반 문헌 계수는 승인 품종 프로필이 아니고 실제 forcing/초기조건 QC는 남아 있다.
[국내 동의/실측/독립 작기는 0건](../research/crop-independent-data-status.json)이다.
계산 개발과 자료 확보는 병행한다. 실제 제품 CLI·독립 해제·전체 G1 및 현장/미래/추천·
공개 운영 G2~G4는 각 증거가 없으면 hold다. 아래 날짜별 기록은 당시 확인 상태다.

**원천→농장 참조 제공자 (2026-10-01):** [읽기 계약](../contracts/source-farm-selection-v1.md)은
정확한 완료 조사·수집의 현재 등록 범위와 이미 저장된 원본 스냅샷/서명 문맥을 확인한다.
[SCRAM 집중 4개](../research/source-farm-selection-implementation.md)가 통과했으며 쓰기 범위 없이
원본/숫자를 노출하지 않는 참조와 보류 표시를 반환한다.
[인증 HTTP/표준 조립](../contracts/api-source-farm-selection-v1.md)은
[집중 66개](../research/api-source-farm-selection-implementation.md)와 실제 HTTPS 12개 전체 응답
(최대 0.582초/기존 30초 제한, 쓰기 범위 0개)으로 확인했다.
같은 원천 문맥의 [저장 경제 후보 제공자](../contracts/farm-economic-candidate-selection-v1.md)는
[SCRAM 5개](../research/farm-economic-candidate-selection-implementation.md)와 실제 농장 등록 연결을 확인했다.
[인증 목록/현재 선택 API](../contracts/api-farm-economic-candidate-selection-v1.md)의
[집중 64개](../research/api-farm-economic-candidate-selection-implementation.md)도 통과했다.
HTTPS 20개 전체 응답 최대 7.844초/기존 30초 제한, 페이지 복구·권리 철회·쓰기 범위 0개를 확인했다.
농장 작성의 [저장 원천·경제 선택 화면 후보](../research/source-farm-web-implementation.md)는
집중 Chromium 14개로 조합 변경·권리 동의 취소·동일 입력 재확인·계정 변경을 확인했다.
실제 HTTPS/SCRAM 신규 등록→검토/Run→3D의 두 경로도 통과했고,
[같은 새 Run의 경제/평가 연속 검증](../research/source-farm-financial-continuation-implementation.md)은
로컬 1개와 해당 판본의 호스팅 작성 7개 묶음·웹/C0를 확인했다.
`5dc63f3`의 [전체 백엔드 2,205개·UID/cleanup/집계](../research/backend-ci-partition-implementation.md#hosted-acceptance-after-the-openapi-correction)도 통과했다.
[화면 보완](../research/source-farm-layout-refinement-implementation.md)의 참조 상세·키보드 이동과
[등록 미확인 잠금](../research/source-farm-registration-lock-implementation.md)은 집중 브라우저로 확인했다.
`93e30a7`의 [최종 UI 소프트웨어 수용](../research/source-farm-web-implementation.md#final-software-ui-acceptance-2026-10-01)은
호스팅 웹 154/50개와 작성 브라우저 4개에서 저장 원천 선택→신규 농장 등록→경제/평가·동일 3D를 확인했다.
본문 최대 26.3284초이며 화면 대조의 낮은 일치율은 유지한다. 별도 경제 브라우저는 실패했고,
[후속 권한 감사 보완](../research/runtime-role-audit-batching-implementation.md#all-role-query-batching-follow-up-2026-10-01)의
로컬 보안 109개·실제 브라우저 1개는 통과했다(본문 최대 24.5048초/기존 30초 제한).
새 감사 코드의 호스팅 검증과 실제 제품 CLI·독립 해제/전체 G1 수용은 후속이다.

**작성 Run 경제·평가 웹 후보 (2026-10-01):** [07 화면](../contracts/web-authored-economic-assessment-v1.md)은
저장 Run을 선택해 현재 서버의 V3 경제 입력으로 접수하고 금액·월별 현금·보류 근거와 같은 3D Run을 확인한다.
저장 이력에서 현재 결과를 다시 읽으며 재연결 후에는 기록 선택 뒤 새 계산을 별도로 준비한다.
웹 단위 122개·집중 Chromium 19개와 실제 PostgreSQL 16.15/SCRAM·HTTPS 브라우저 1개가 통과했다
([검증 기록](../research/web-authored-economic-assessment-implementation.md)). 마지막 실제 연결은 POST 2개,
응답 헤더 29개·최대 23.239초, 보류 6개·120시점 3D를 확인했다. 응답 헤더 지연은 전체 본문 지연 측정이 아니며
제품의 전체 본문 제한은 기존 30초다. 12ui 대조는 낮은 일치율로 정밀 디자인 수용을 주장하지 않는다.
시험용 CLI·서명의 소프트웨어 범위다. 일반 지역 조사/수집과 농장 작성의 자동 연결,
새 호스팅 전체 CI·실제 제품 CLI·독립 해제·G1/G4는 남아 있다.

**작성 Run 경제 입력·작업 이력 조회 후보 (2026-10-01):** [조회 계약](../contracts/authored-financial-selection-v1.md)은
현재 작성 Run과 농장에 고정된 경제 입력 V3를 확인하고 같은 부모의 경제·평가 기록을 페이지별로 복원한다.
실제 PostgreSQL 16.15/SCRAM의 선택·권한·손상/비표준 JSON 거부·권리 철회·늦은 변경과 OpenAPI,
표준 HTTPS의 10개 응답·기존 브라우저 회귀를 포함한 서로 다른 집중 시험 59개가 통과했다
([검증 기록](../research/authored-financial-selection-implementation.md)). HTTP 최대 24.769초는 기존 30초 제한 안이며
그 HTTPS 측정 뒤 추가한 바이트 검사도 실제 DB 두 사례로 다시 확인했다.
이력은 결과 승인 증거가 아니며 현재 금액/현금·평가 조회가 필요하다. 작성 웹 선택·새 호스팅 CI·실제 제품 CLI·독립 G1/G4는 남아 있다.

**작성 Run 평가 연결 후보 (2026-10-01):** [평가 입력 V3](../contracts/authored-calculation-assessment-v1.md)는
완료 작성 열·경제 작업과 현재 농장/해제/문맥의 해시를 고정하고 공유 CLI 라우터의 별도 검증기에 연결한다.
실제 PostgreSQL 16.15/SCRAM에서 세 통합 사례와 표준 HTTPS의 8개 응답·보류 6개를 확인했다
([검증 기록](../research/authored-calculation-assessment-implementation.md)). 최대 HTTP 응답은 25.346초로
기존 30초 제한 안이다. 기존 평가/OpenAPI/라우터 회귀 65개와 부모 결합의 반례 시험 12개도 통과했다.
가짜 CLI·시험 서명의 소프트웨어 범위이며 작성 부모의 웹 선택, 새 호스팅 전체 CI와 실제 제품 CLI·독립 G1/G4는 남아 있다.

**작성 Run 경제 연결 후보 (2026-10-01):** [별도 경제 입력/영수증 V3](../contracts/authored-economic-execution-v1.md)는
현재 작성 농장·해제·완료 Run과 같은 경제 후보를 접수/작업자/금액·현금 조회에 고정한다.
[소프트웨어 검증](../research/authored-economic-execution-implementation.md)의 실제 PostgreSQL 16.15/SCRAM·HTTPS,
혼합 거부와 늦은 변경 롤백·OpenAPI를 포함한 서로 다른 집중 시험 82개가 통과했다.
이후 작성 공통 평가의 서버 연결을 추가했다. 웹 부모 선택과 실제 제품 CLI·독립 G1/G4 수용은 남아 있다.

**완료 계산의 웹 평가 후보 (2026-10-01):** [화면 계약](../contracts/web-calculation-assessment-v1.md)에 따라 완료 열·경제 작업을 접수하고 현재 상태·공개 보류 범주를 확인한다. 응답 유실 때 같은 요청을 유지하고, 저장 작업 ID로 새로고침 후 조회한다. 웹 단위 93개·집중 Chromium 6개, 실제 HTTPS/PostgreSQL 16.15/SCRAM·시험용 CLI 연결 1개가 통과했다([검증 기록](../research/web-calculation-assessment-implementation.md)). 작성 농장의 웹 부모 선택, 일반 지역 흐름의 자동 부모 선택·미확인 접수 복구·실제 제품 CLI·독립 해제와 G1은 남아 있다.

**필수 모델 변경 (2026-10-01):** 개발·제품 런타임 모두 `gpt-6.1-sol`/`xhigh`로 변경한다([이전 계약](../contracts/cli-model-policy-migration-v1.md), [검증 기록](../research/cli-model-migration-implementation.md)). 현재 개발 세션은 해당 모델·강도로 실행 중이다. 아래 과거 `gpt-6-sol` 실행 결과는 당시 증거로 보존하며, 새 모델의 실제 제품 작업자 실행·독립 해제·배포 계정 비용 검증으로 인정하지 않는다.

**작성 Run 저장 목록·웹 후보 (2026-09-30):** 소유 테넌트의 불변 Run ID·계산 작업 ID·기록 시각을 페이지별로 조회한다([계약](../contracts/api-authored-thermal-run-v1.md), [시험](../research/authored-run-catalog-implementation.md)). 내부 웹은 농장 선택 없이 목록을 다시 찾고 선택한 Run의 정확한 현재 조회 후 3D 화면으로 이동한다. 목록에는 현재 표시 검증이 필요하다고 명시하며, 정확한 Run 조회가 기존 해제·권리·게시 증거를 다시 검사한다. 합성 브라우저 검증 범위이며 실제 CLI·독립 G1은 남아 있다.

**지역 조사→수집·검토 내부 화면 후보 (2026-09-30):** 기존 인증 `/v1/ingestions`와 `/v1/collection-reviews`를 완료된 부모 작업에 순서대로 연결하고 서버 상태·검토 보류를 표시한다([계약](../contracts/web-owned-source-workflow-v1.md), [검증](../research/web-owned-source-workflow-implementation.md)). [저장 작업 이력](../contracts/api-owned-source-history-v1.md)은 전체 새로고침 뒤 조사와 수집·검토 이전 시도를 다시 찾는다. 브라우저·PostgreSQL 합성 소프트웨어 범위이며 실제 CLI·독립 출처 승인, 자동 농장 입력 연결 및 G0/G1/G4는 보류한다.

**작성 입력 판본·작업 이력 후보 (2026-09-30):** 같은 계정의 불변 등록 판본을 서버에서 페이지별로 다시 찾고, 선택 시 단건 조회로 현재 입력·권리와 해시를 확인한다([목록 검증](../research/authored-farm-catalog-implementation.md)). 검토·계산 작업 이력도 해당 판본과 해시에 묶어 페이지별로 조회하고, 선택 시 현재 판본과 실제 작업 상태를 다시 확인한다([작업 이력 검증](../research/authored-farm-activity-implementation.md)). 두 목록은 과거 메타데이터이며 철회된 판본의 사용을 허가하지 않는다. 완료 Run은 별도 목록으로 조회한다. 실제 제품 CLI·독립 해제·전체 G1은 남아 있다.

**작성 농장 웹 작업 연결 (2026-09-30):** 직접 작성한 농장 가정·권리 선언을 입력해 불변 판본으로 등록하거나 기존 판본을 조회한 뒤 검토/계산 접수·상태/보류 확인·완료 Run 3D 이동을 구현했다. 마지막으로 확인한 판본 ID·해시만 탭에 저장하고 재연결 때 인증 GET/해시를 재확인하며 접근 철회·변경은 복원하지 않는다([기록](../research/authored-farm-web-workflow-implementation.md)). 검토·계산 작업의 재연결 복구 후보는 위 이력 경로에 있다. 기존 합성 HTTP Chromium 집중 4개와 웹 단위 시험 73개가 통과했고, 완료 Run 전체 목록의 재조회·현재 단건 보류·3D 이동을 추가로 시험했다. 작성 폼은 기존 조사·원본·시장 보류·경제 참조를 사용자가 알아야 하는 내부 도구이며 지역 선택만으로 자료를 발급하지 않는다. 새 작성 POST를 포함한 PostgreSQL 16.15/SCRAM·HTTPS·Chromium 전체 소프트웨어 경로도 로컬 1회 통과했고 호스팅 백엔드 CI는 확인 중이다. 실제 제품 CLI·독립 해제와 전체 G1 및 `web-shell`/`web-replay` 수용은 보류한다.

**작성 농장 → 저장 Run → 실제 HTTPS/Chromium 합성 연결 (2026-09-30):** 실제 PostgreSQL 16.15/SCRAM에서 브라우저가 작성 폼을 제출해 농장을 등록하고 **신규 검토·신규 계산 작업을 각각 접수**했다. 두 작업 사이에 하네스의 가짜 CLI 검토·합성 실행 서명·합성 독립 해제를 저장했고, 실제 계산 작업자가 Run을 원자 게시했다. 브라우저의 실제 HTTPS 8개 응답·120시점 3D/표 대조와 콘솔 오류 0개를 로컬 1회 통과했다([검증](../research/authored-full-software-path-implementation.md)). 처음 검증한 완료 증명과 계산 후보를 후속 조립에서 고정했으므로 반복 재검증/철회의 단독 증거는 아니다. 실제 제품 CLI·독립 검토 발급·원천 수집 입력·접수 지연 개선·전체 G1은 보류한다.

**작성 Run 접수 HTTP 후보 (2026-09-30):** [계약](../contracts/api-authored-simulation-admission-v1.md)은 현재 해제·입력·최종 두 궤적을 재검사하는 인증 POST를 표준 런타임에 연결했다([검증](../research/api-authored-simulation-admission-implementation.md)). 작성형 API의 실제 HTTPS/SCRAM 집중 CI는 51개 시험을 통과했다. 신규 작업의 완료·게시·브라우저 전체 합성 흐름도 [별도 통합 시험](../research/authored-full-software-path-implementation.md)에서 확인했다. 제품 CLI·독립 G1은 남아 있다.

**작성 입력 검토 HTTP 후보 (2026-09-30):** [계약](../contracts/api-farm-authored-review-v1.md)은 등록 입력의 인증된 검토 작업 접수와 표준 런타임 조립을 추가했다([검증](../research/api-farm-authored-review-implementation.md)). OpenAPI·실제 SCRAM 집중 CI 51개 시험을 통과했다. 제품 CLI 실행·독립 해제·Run 게시·전체 G1은 계속 보류다.

**직접 열어 볼 수 있는 합성 3D 데모 (2026-09-30):** `web/`의 `npm run demo:3d`에서 로컬 전용 시험 응답과 기존 3D 재생 화면을 연결했다([캡처](../research/artifacts/local-synthetic-3d-demo.png), [브라우저 검증](../research/local-synthetic-3d-demo-implementation.md)). 실제 저장 Run의 표준 HTTPS 브라우저 시험, 사용자 농장 작성·자료 수집·제품 CLI·독립 G1/G4 수용과 구분한다.

**작성 농장 입력 HTTP 후보 (2026-09-30):** [계약](../contracts/api-farm-authoring-v1.md)은 기존 불변 입력 서비스를 인증 POST/GET과 표준 HTTPS 조립에 연결한다([검증 기록](../research/api-farm-authoring-implementation.md)). OpenAPI·실제 SCRAM 집중 CI 51개 시험을 통과했다. 브라우저 직접 입력 폼도 로컬 PostgreSQL/SCRAM·HTTPS 경로에서 등록 200과 서버 재조회로 확인했다. 제품 CLI·독립 검토/해제·전체 G1은 계속 보류다.

**작성 Run 인증 읽기 후보 (2026-09-30):** [계약](../contracts/api-authored-thermal-run-v1.md)은 완료 작업의 게시/입력 결속과 별도 작성 Run의 120시점 열 값을 내부 인증 API에서 읽는다([집중 시험](../research/api-authored-thermal-run-implementation.md)). 검토 근거의 읽기 재검사에서 불필요한 검토 생성 권한을 제거했다. 실제 제품 CLI·독립 해제, 표준 HTTPS 조립·브라우저 작성 3D와 전체 G1은 계속 보류다.

**작성 입력 독립 해제·Run 준비 후보 (2026-09-30):** [접수 계약](../contracts/farm-authored-review-v1.md)은 저장된 농장 판본·현재 원천/권한과 120단계 계산의 두 결과 해시를 변경 불가 `collection_review` 작업으로 묶는다([검증](../research/farm-authored-review-implementation.md)). [완료 검증 계약](../contracts/farm-authored-review-completion-v1.md)은 저장된 결정·CLI 캡처와 서명 실행 증거를 대사한다([시험](../research/farm-authored-review-completion-implementation.md)). [해제 검증 계약](../contracts/farm-authored-release-v1.md)은 현재 코드/잠금·완료 증명과 별도 검토자 서명·보고서 원문을 검사한다([시험](../research/farm-authored-release-implementation.md)). [영속 저장 계약](../contracts/farm-authored-release-store-v1.md)은 합성 서명 패킷의 실제 SCRAM 보존·불변성과 선택적 권한 분리를 검증했다([시험](../research/farm-authored-release-store-implementation.md)). [Run 준비 계약](../contracts/farm-authored-run-preparation-v1.md)은 현재 해제·작성 입력을 재검사해 최종 두 궤적의 ID/해시/이어짐을 계산한다([시험](../research/farm-authored-run-preparation-implementation.md)). 준비 바이트는 미게시다. 운영 조립·실제 제품 CLI·독립 검토/해제 발급·원자 Run 게시·작성 입력 3D 연결과 전체 G1은 미수용이다.

**작성 입력 Run 영속 경계 후보 (2026-09-30):** [저장 계약](../contracts/farm-authored-run-store-v1.md)은 별도 불변 테이블과 권한을 명시적으로 설치한다. v8 SCRAM 권한, 합성 Run 행의 게시·재조회, 단독 행 커밋 거부 및 같은 거래의 작업 완료를 시험했다([기록](../research/farm-authored-run-store-implementation.md)). 시험의 준비 함수와 완료 증명은 합성 대역이며 실제 작업자·제품 CLI·독립 해제·3D는 아직 미구현이므로 G1은 계속 보류다.

**작성 simulation 접수 후보 (2026-09-30):** [접수 계약](../contracts/farm-authored-simulation-v1.md)은 등록 판본·서명 해제·120단계 최종 패킷을 다시 확인해 같은 작업 하나를 등록하며 접수 중 증거가 바뀌면 롤백한다([시험](../research/farm-authored-simulation-implementation.md)). 작성 Run API/3D·제품 CLI·독립 해제와 G1은 계속 보류다.

**작성 simulation 작업자 후보 (2026-09-30):** [작업자 계약](../contracts/farm-authored-simulation-worker-v1.md)은 임대한 작성 작업을 현재 해제·입력으로 재검사하고 Run/영수증/완료를 한 거래에 묶는다([합성 SCRAM 시험](../research/farm-authored-simulation-worker-implementation.md)). 취소·권리/해제 변경·오류·임대 만료 때 부분 Run이 남지 않음을 확인했다. 실제 제품 CLI와 독립 해제·인증 API/3D·전체 G1은 아직 보류다.

**첫 내부 3D 열 재생 후보 (2026-09-30):** [재생 계약](../contracts/web-thermal-replay-v1.md)은 완료된 Run의 120개 저장 시각을 실제 Three.js 장면·그래프·HTML 표·여섯 수치 요약으로 연결한다. [소프트웨어 검증 기록](../research/web-thermal-replay-implementation.md)은 키보드·반응형·WebGL 장애/복구와 실제 HTTPS/SCRAM 브라우저 연결을 구분한다. 전체 입력·공통 농장 Assessment·실제 CLI/독립 G1/G4 수용은 남아 있고 작물 생장·수확·미래 마진·순위를 검증한 결과가 아니다.

**농장 경제 실행 연결 후보 (2026-09-29):** [계약](../contracts/farm-economic-execution-v1.md)은 같은 등록 계획과 실제 완료 열 v3 작업을 경제 v2 접수·작업자·금액/월별 현금 조회에 연결한다. [검증 기록](../research/farm-economic-execution-implementation.md)은 실제 SCRAM·합성 권한의 완료/롤백 및 HTTPS 지연 수정과 집중 검증을 기록한다. [첫 내부 3D 열 재생 뷰어](../contracts/web-thermal-replay-v1.md)도 부분 구현했으며, 공통 Assessment·전체 작성·열 비용 결합·실제 CLI/독립 G1/G4는 미수용이다.

**농장 계획 열 실행 연결 후보 (2026-09-29):** [실행 계약](../contracts/farm-thermal-execution-v1.md)은 실제 계획 판본·원본 핀·완료 조사/수집/검토를 접수·계산·완료 조회에서 다시 검사한다. [집중 검증](../research/farm-thermal-execution-implementation.md)은 실제 SCRAM과 HTTPS/Bearer의 소프트웨어 범위다. CLI 실행기와 해제 키는 시험용이며, 공통 평가·열 비용 결합·3D와 실제 CLI/독립 G1/G4는 미수용이다.

**농장 재생 계획 등록 후보 (2026-09-29):** [계약](../contracts/farm-replay-scenario-v1.md)에 따라 실제 조사 입력·등록부, 열 시나리오, 사용자 경제 후보를 판본별로 묶는 API를 추가했다. [증거](../research/farm-replay-scenario-implementation.md)는 실제 SCRAM 저장/재조회·권한 철회·불일치 거부와 HTTPS/Bearer 조립을 기록한다. 좌표는 `pending_research`이며 실제 기상의 공간 대표성, 전체 농장/정산 작성, 열과 비용의 결합, 후속 실행/평가·3D와 실제 CLI/독립 G1/G4는 미수용이다.

확인일: **2026-09-27.** 확인된 증거와 막힌 사항을 기록한 문서이며 관문 통과 기록이 아니다. 로컬 상태는 작업 트리와 버전·PATH 검사로 확인했다. 로컬 CLI 조사 세션의 성공은 현재 CLI 작업에서 보고되었지만, 제품 작업자 경로는 실행하지 않았다. 아래 출처 페이지는 **검토 후보**이며 채택된 데이터셋이 아니다. [첫 구현 범위](IMPLEMENTATION_SLICE.md), [자료 기준선](RESEARCH_BASELINE.md), [검증 관문](PROJECT_SPEC.md#6-검증과-수용-관문)을 함께 본다.

| 준비 항목 | 2026-09-27의 증거·상태 | 다음에 필요한 확인 작업 | 관련 구현·관문 |
| --- | --- | --- | --- |
| 저장소의 실행 출발점 | `repo-bootstrap`과 Compose C0 골격을 커밋했다. [C0 실행 36316629672](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/36316629672)에서 설정·의존성 이미지와 PostgreSQL 18.6 기동·영속성 검사가 성공했고, [백엔드 CI 36318356211](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/36318356211)에서 실제 PostgreSQL 18.6에 연결한 전체 백엔드 시험 **977 passed, 0 skipped**와 DB/비밀 정리를 확인했다. `g0-authority-store`의 로컬 PostgreSQL 16.15 계약 시험은 수용됐으나 독립 검토 resolver·제공자 증거가 없어 실제 원천 G0 통과는 없다. | 앱 역할의 기동·권한, 실제 CLI 작업자·API·웹과 합성 G1 종단 간 경로를 검증한다. | `repo-bootstrap`, `compose-runtime`, `fixture-policy`, 합성 자료 G1 추적 시험 |
| 로컬 Python/web 도구 | `python3 3.12.3`, Node `22.22.3`, npm `11.16.0`, uv `0.11.14`의 버전 명령이 성공했다. 백엔드는 FastAPI `0.141.1`·Pydantic `2.13.5`·개발용 pytest `9.1.1`, 웹은 React/ReactDOM `19.3.0`·Vite `8.3.1`·TypeScript `7.0.2`·Vitest `5.0.2`·React 타입 `19.3.0`으로 설정·잠금 파일을 맞췄다. 오프라인 캐시에서 `uv lock --check`, `uv sync --locked`, FastAPI/Pydantic import와 `npm ci --strict-peer-deps`(43개 패키지)가 통과했다. 이후 `node_modules`는 제거했다. 후속 Psycopg/psycopg-binary `3.3.6`과 런타임 jsonschema `4.26.0`은 잠금·동기화·import를 확인했고, Psycopg는 사용자 로컬 PostgreSQL 16.15 Unix 소켓에 연결했다. | 앱 소스·시험이 생긴 뒤 백엔드 pytest와 웹 자료형 검사·시험·빌드 및 API 실행을 확인한다. | `repo-bootstrap`, `web-shell` |
| 로컬 서비스 도구 | PATH에 `docker`, `podman`, `psql`, `postgres`, `pg_ctl`이 없고 `/var/run/docker.sock`도 없다. 사용자 홈의 독립형 `docker-compose` v5.5.1로 이 저장소의 기본·`app` 프로필 `config -q`가 임시 외부 비밀 파일 아래 통과했다. 사용자 네임스페이스는 가능하지만 rootless Docker 필수 `newuidmap/newgidmap`이 없고, 사용자 권한만으로 필요한 root 소유 setuid 권한을 설치할 수 없다. Podman의 단일 UID 예외도 현재 subordinate UID/GID 할당과 helper 부재를 해결한다는 근거가 없다. PostgreSQL 16.15는 공식 소스를 사용자 홈에 빌드해 Unix 소켓 전용으로 기동·연결·중단했다. 별도로 C0 Actions에서 목표 PostgreSQL 18.6 이미지 기동과 볼륨 영속성이 확인됐다. | C0는 호스팅 러너에서 통과했다. 앱 역할의 최소 권한 DB 계정·기동·복구와 실제 CLI 격리는 각각 후속 작업에서 확인한다. | `compose-runtime`, `durable-jobs`, `end-to-end-g1`, G4 |
| Codex CLI 사용 가능 여부 | 로컬 `codex-cli 0.157.1`과 정확한 `gpt-6-sol`/`xhigh` 조사·구조화 출력 smoke를 확인했다. `cli-worker-store-bridge` 저장 계약은 수용됐다. 커밋 `e436f9a`/`a9a2a7f`의 실제 subprocess 작업자 후보는 로컬 PG16 **23 passed, 0 skipped**이며 보정 전 로컬 실제 CLI의 조사·수집 검토·평가 세 단계가 각각 검증된 `hold`로 종료됐다. 독립 감사 뒤 격리/권한 코드를 보완했다. `scripts/run-cli-smoke.sh --check`는 개인 자격 파일 권한·CLI 버전·전용 PG 연결을 모델 호출 없이 확인했다. 보정 후 실제 `--run`에서 정확한 모델·강도의 세 단계가 각각 검증된 `hold`로 끝났으며 [비밀 제거 실행 기록](../research/cli-worker-posthardening-smoke.md)에 해시·사용량을 남겼다(1 passed, 입력 42,940·출력 538토큰). 제품 작업별 격리·독립 실행 증명이 없어 운영 생성자는 기본 차단한다. | 확인된 실제 CLI 경로에 독립 실행 증명과 신뢰 작업자/서버 권한을 결합하고, `end-to-end-g1`의 작업·조회·재생을 잇는다. 비특권 컨테이너·임시 파일시스템·egress 제한과 운영 계정은 G4에서 별도 증명한다. | `cli-worker`, `end-to-end-g1`, G4 |
| 운영용 CLI 계정 | 배포 주체의 인증·모델 접근·사용 한도·실제 청구액·허용 조건·지연·격리/외부 통신은 시험하지 않았다. | 실제 운영 계정과 계약으로 접근·조건·실측 비용/한도·도구 제한·복구·보류 동작을 확인한다. | G4, 공개 출시 |
| 기상청 관측소와 자료 보유율 | [기상청 G0 적용 가능성 조사](../research/kma-g0-feasibility.md)는 API허브·공공데이터포털·개방포털의 서로 다른 제품 계약과 공식 지점정보 후보를 대조했다. API허브의 96지점은 2020년 기준, 개방포털 105개는 다른 경로의 표시다. 시범 좌표·지점·기간이나 `SI`/`icsr` 실측 보유율은 정하지 않았다. 인증키 호출도 수행하지 않았다. | 권한 있는 제품·지점의 실제 응답으로 지점별 요소 보유, 관측소 거리·고도·운영 이력과 현장 대표성을 검사한다. 그 전에는 시범 대상과 실제 원천 G0를 승인하지 않는다. | `kma-g0`, 실제 자료 Run |
| ASOS 시간 요소의 의미 | [기상청 G0 조사](../research/kma-g0-feasibility.md)의 공식 명세 대조에서 API허브 `kma_sfctm3.php`는 `TM` KST, `SI` MJ/m², 요청당 최대 31일로 확인했다. 별도 공공데이터포털 제품 `15057210`은 `icsr` MJ/m², 페이지 인자·`totalCount`, 전일 자료 11시 이후 안내가 있다. 값의 한 시간 적산 시작·끝, `00:00` 귀속, 두 경로의 동일성, 공공데이터포털 `tm` 시간대는 미확정이다. | 제공자에게 구간/시간대·값 동일성을 확인한 후 각각의 제품별 경계·누락·UTC 변환 시험을 한다. 확인 전에는 일사 강도 변환과 실측 열 입력을 보류한다. | `kma-g0`, `thermal-contract`, 실제 자료 Run |
| ASOS `SI` 품질 | [기상청 G0 조사](../research/kma-g0-feasibility.md)는 개방포털 화면/API 표에 일사 QC가 빠진 반면 기상청 데이터위키의 변수 목록에는 일사 QC가 열거된 **공식 자료 간 불일치**를 기록했다. 연결 제품의 실제 `SI`/`icsr` QC 필드·코드와 결측/정정 경로는 미확인이다. | 제공자 설명과 실제 응답으로 QC 공급 여부를 확인한다. 없으면 `not supplied`로 보존하고 결측·음수·야간·구간/공간 타당성에 대한 프로젝트 검사를 별도로 정의한다. | `provenance-g0`, `kma-g0` |
| 기상청 제품 이용권 | [기상청 G0 조사](../research/kma-g0-feasibility.md)에 따르면 공공데이터포털 제품 [`15057210`](https://www.data.go.kr/data/15057210/openapi.do)은 무료·공공누리 제1유형 출처표시·개발/운영 자동승인으로 표시된다. API허브 `kma_sfctm3.php`에는 이를 자동 이전할 수 없다. 실제 연결 경로의 계정/한도, 제3자 권리, 원본 저장·변환·화면 표시·재배포 조건은 미승인이다. | 연결할 정확한 제품·경로에 대해 각 사용 행위의 권리·출처 문구·운영 조건을 확인하고 원본은 권한 제한 저장소에 보관한다. 확인 전 실제 원천 G0는 보류한다. | `kma-g0`, G0, G4 |
| 원천 판본과 결정 당시 시장 자료 | 승인된 시장 원천 판본이나 `decision_at` 근거가 없다. 나중에 수집한 자료나 개정 가격을 과거 결정의 입력으로 곧바로 쓸 수 없다. | 선택한 제품마다 `published_at`·`available_at`·`retrieved_at`, 원래 판본/개정, 적용 범위와 권리를 조사한다. 없으면 `{kind: "unavailable", hold_report_id}`를 만들고 사유·누락 증거는 참조한 Market hold report에 기록한다. 첫 G1에서는 `origin=user`, `evidence_level=assumed`인 명시적 사용자 가정만 조건부 스트레스에 쓰며 Assessment는 `hold`다. 가짜 MarketSnapshot이나 자료 유래 전망을 만들지 않는다. `available`에는 유효한 권리·판본과 `available_at <= decision_at`인 G0 승인 MarketSnapshot이 필요하다. 후속 비공개 농장 계약·정산·원장은 권리·적용성·원장 대사를 확인한 뒤 해당 농장의 조건부 또는 과거 계산에만 쓸 수 있다. | `market-context`, `market-scenario`, 시장 G0, 후속 G3a |
| 실제 시장 원천 G0 연결 | [시장 제품 후보 조사](../research/market-source-candidates.md)에서 공식 일별 API `15156057`, KAMIS #16, 연간 CSV `15134477`의 메타데이터를 비교했으나 세 제품 모두 G0 채택 `hold`다. 실제 어댑터·정규화·원본 해시/QC·시장 G0 게시 시험이 없고, 제품별 최초 공개·과거 판본·용도별 권리도 미확인이다. | `market-source-g0`에서 CLI 조사로 **실제로 연결할 정확한 URL/제품 ID**와 관측·발표·이용 가능·조회 시각, 개정 판본, 단위/품종·등급/거래 단계·채널/지역/날짜 적합성, 원본 해시·QC·검토자와 용도별 권리를 확인한다. 승인된 범위만 G0 MarketSnapshot으로 게시하고 불명확하면 Market hold report를 남긴다. 자료 유래 시나리오·시장 근거 카드·ForecastRun은 그 전까지 보류하되 첫 합성 G1은 진행할 수 있다. | [`market-source-g0`](../tasks/todo.md), 시장 G0, 후속 `forecast-engine` |
| 물리 모델·후보 엔진 | `thermal-engine`은 2시간 합성 후보 계산으로 수용됐다. D/R 결정시각 계약은 `aa97e3f`, 서명된 공통 DecisionContext와 게시기 통합은 `621acad`에 있다. 열·게시·저장·fixture 로컬 PG16 집중 시험 **311 passed**와 독립 xhigh 감사의 결함 수정, [호스팅 CI 36318356211](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/36318356211) 전체 **977 passed, 0 skipped**를 확인했다. 이는 합성 사후 재생 소프트웨어 계약이다. `ThermalReviewContract`의 서명 문맥·스냅샷 입력 연결과 열 제안 바이트 도출은 관련 집중 시험 12개(그중 모의 권한·캡처 PG16 통합 3개) 및 백엔드 전체 997개를 통과했다. 실제 CLI 실행·독립 검토 권한/해제/계획 사건·운영 DB 권한 증거가 없어 G1 Run은 **HOLD**이고 `ex_ante` 게시도 D 시점 원천 증거가 없어 항상 보류다. | 신뢰 가능한 제품 CLI 실행과 독립 해제·D 시점 판본/권리 증거, DB 역할 분리를 실제 작업/게시 경로에 연결한다. 현장 G2·실제 G0·구매 에너지/작물 정확도는 별개다. | `thermal-decision-clock-contract`, `thermal-g1-publisher`, 합성 G1 추적 시험 |
| 경제 입력과 시험 자료 | 직접 작성한 weather/economics v1·manifest v1 원본 해시와 합성 정책 시험 30개를 확인했다. `economic-ledger`(커밋 `b831f46`)의 기본 `Decimal` 원장과 `sales-settlement`(커밋 `3228ae2`)의 판매별 상계·수금·미수금/미지급금 대사가 수용됐다. 정산 집중 시험 **169 passed**, PG16 포함 백엔드 전체 **703 passed**이며 반올림 환경 간 전체 결과·ID 결정성을 회귀 시험했다. 승인된 농장 원장·정산서·은행 입금은 없다. | `market-scenario`가 수요·공급·거시 충격과 날짜별 `H/P/S`, 차감 전 계약가격/조건부 순송금 단가, 비용·현금을 함께 재계산하고 `economic-break-even`이 각 시험값에서 전체 경로를 다시 평가한다. 정산 완료 농가 순수취가와 실제 마진·전망은 독립 원장·정산/은행 대사와 G2/G3 증거 전까지 보류한다. | `fixture-policy`, `economic-ledger`, `sales-settlement`, `market-scenario`, `economic-break-even` |
| 수요·공급·거시 공동 시나리오 | 커밋 `69d12e0`은 `MarketContext.kind=unavailable`과 사용자 소유 가정에 한정해 수요·공급·거시 공동 충격, 날짜별 H/P/S·계약/재고·가격/비용/현금을 결정적으로 재계산한다. 교차 테넌트 원문이 구조화 오류에 노출되던 반례를 RED→GREEN으로 막았고 시장·경제 관련 **281 passed**, 호스팅 전체 **977 passed, 0 skipped**다. 파생 후보·새 숫자 판본의 PostgreSQL 원자 고정과 새 저장소 인스턴스 재조회 후보는 [저장 계약](../contracts/market-candidate-store-v1.md)의 로컬 PG16 통합 **4 passed**, 백엔드 전체 **1001 passed**로 확인했다. 기초 원장·충격·권리·정산의 운영 원천 저장소와 실제 농장·시장 자료, 승인 MarketSnapshot, 충격의 확률/전가·미래 정확도 증거는 없다. | 영속 Market hold 보고서를 API에 연결하고 자료 원천 G0와 `available` 경로를 별도로 구현하며, `economic-break-even`이 시험값마다 전체 경로를 다시 계산하도록 연결한다. 정산·현장·미래 검증 전에는 실제 순수취가·미래 가격/마진·작물 순위를 보류한다. | `market-scenario`, `market-hold-store`, `economic-break-even`, G1·후속 G3a/G3b |
| API·작업·재생 | PostgreSQL 작업·AI 증거 저장·단계 임대와 의도 멱등 제약을 수용했다. CLI 작업자·열 게시기·시장 시나리오의 **소프트웨어 후보**가 커밋됐고 [호스팅 CI 36318356211](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/36318356211)은 PostgreSQL 18.6 전체 **977 passed, 0 skipped**다. 영속 Market hold의 합성 소프트웨어 저장 계약은 로컬 PostgreSQL 16 전체 983개 시험과 실제 서버 재시작 검증을 통과했다. 운영 DB 업그레이드/최소 권한, 실제 CLI와 독립 게시 증거, Market hold의 API 연결, 손익분기·API 인증/HTTP 409·Compose 앱 역할·브라우저 경로는 남아 있다. | `economic-break-even`과 신뢰 실행/해제 경계를 만든 뒤 같은 DecisionContext에 묶인 인증 API를 연결한다. 3D·그래프·표의 `run_id + timestamp` 값과 보류 이유를 종단 간 검증한다. | `cli-worker`, `thermal-g1-publisher`, `market-hold-store`, `economic-break-even`, `api-flow`, `web-replay`, `end-to-end-g1` |
| G2 현장 비교 | 동의를 받은 국내 온실 센서 시계열, 시설 사양, 독립 보정/시험 기간, 대응되는 공급열·에너지 계량 자료가 없다. | 전문 CLI 조사로 협력 농장과 시험 계획을 정하고 이용 허락을 확보한다. 독립 실내 온습도와 주장할 에너지 물리량 각각을 실측과 비교한다. 시험 전에 손실 기준을 등록한다. | `g2-evidence`, 국내 현장 물리 정확도 주장 |
| 미래 경로 계산 구현 | 버전 고정 ForecastRun·특성 절단시각 검사·모델/매개변수와 독립 rolling-origin 검증 절차를 실행할 코드가 없다. 승인된 MarketSnapshot과 G2/현장 적용 증거도 없다. | `market-source-g0`와 `g2-evidence` 뒤 `forecast-engine`에서 당시 이용 가능 판본만 쓰는 수확 `H`·등급별 `P`·판매 인정 `S`·농가 실수취가·비용·현금의 공동 경로 또는 명시적 보류를 구현한다. 모델/입력/출력 버전과 검증 범위를 고정하고 독립 자료가 없으면 예측을 게시하지 않는다. | [`forecast-engine`](../tasks/todo.md), `g3a-evidence` 전 구현 |
| G3a 작물·경제 전망 | 동의를 받은 수확·등급·판매·반품·재고·정산·계약·구매 에너지·노동·비용·현금 기록 중 결정 당시 판본과 독립 시험 기간을 갖춘 자료가 없다. | 협력 농장 기록을 확보·대사한 뒤 `forecast-engine`과 분리된 미사용 기간에서, 각 `decision_at` 이전의 학습·특성/구간 보정만 허용하는 rolling-origin 시험과 사전 기준선·손실 기준을 평가한다. 독립 G3a 증거가 통과할 때까지 미래 마진은 보류한다. | `forecast-engine`, [`g3a-evidence`](../tasks/todo.md), 미래 수확·마진 주장 |
| 후보 비교 계산 구현 | 같은 실행 가능한 후보를 공통 결정·시설·면적·달력·목표/충격으로 맞추고 불확실성 겹침·후회 손실·보류를 검사하는 코드가 없다. | `g3a-evidence` 뒤 `crop-ranking`에서 후보별 적용 관문과 계약/제약을 재검사한다. 후보 둘 미만·우열 구별 불가·대응 검증 누락이면 순위를 보류하고 후보별 이유를 기록한다. | [`crop-ranking`](../tasks/todo.md), `g3b-evidence` 전 구현 |
| G3b 작물 간 순위 | 같은 실행 가능한 결정·온실·면적·달력·목표·공통 시장 조건에서 짝을 이룬 **독립** 작물 기록과 공유권이 없다. 이 협력 경로는 **첫 G1 구현 관문과 별개**다. | 협력 자료 접근권을 확보하고 개발·보정·후보 선택에서 분리된 대응 비교·제외 기준·후회 손실/순위 역전/보류 평가를 사전 등록한다. 작물별 모델의 개별 검증이나 비교 엔진만으로 순위를 열지 않는다. | `crop-ranking`, [`g3b-evidence`](../tasks/todo.md), 작물 순위 |
| 서비스 자체의 경제성 | 농장 원장과 별도인 무료/유료·실패/재시도 요청량, 실제 Codex CLI 청구, 자료 API/타일·계산·저장·백업·지원 비용, 유료 매출·고정비·운영 재원 증거가 없다. | 첫 G1 뒤 `service-economics`에서 실제 작업·청구·매출 기록을 대사하고 `Decimal` 공헌이익·영업 잔여액·완료 요청당 실효 변동원가(완료 0건은 미정의)를 계산한다. 무료 수요·재시도 변화 때 전체 유료 요청 손익분기 경로를 다시 계산하고 수요·동시 처리량·한도와 운영 재원을 대조한다. 실측이 없으면 G4 보류다. | [`service-economics`](../tasks/todo.md), `g4-operations` 전 구현·증거 |
| G4 공개 운영 | 배포 호스트, 백업 복원, 허가된 지도 타일·자산, 원천 운영 승인, 실측 CLI/서비스 비용·매출/재원, 계정 조건·작업별 비특권 컨테이너/임시 파일시스템/제한된 외부 통신·접근성/성능 증거가 없다. C0의 Compose 정의는 이 격리 증거가 아니다. | 자체 운영 배포와 복구를 연습하고 작업별 CLI 격리·외부 통신 제한, 권리·실제 계정 동작·`service-economics`의 요청별 비용/수지·한도·재원·테넌트 분리·브라우저 접근성 검사를 기록한다. 실제 원천 유래 기능에는 각각 해당 G0도 확인한다. | `service-economics`, [`g4-operations`](../tasks/todo.md), 공개 서비스 |

**정적 Compose 검사 보완:** [공식 standalone 배포본](https://github.com/docker/compose/releases/tag/v5.5.1) `v5.5.1` Linux x86_64를 게시된 SHA-256과 대조해 사용자 로컬 경로에 설치했다. 이 저장소의 `compose.yaml` 기본·`app` 프로필은 임시 외부 비밀 파일을 사용한 `docker-compose config -q`에서 통과했다. 이는 [Docker가 레거시로 분류하는 독립 실행형 설치](https://docs.docker.com/compose/install/standalone/)이며 Docker Engine·소켓을 제공하지 않는다. [Docker rootless 설치 조건](https://docs.docker.com/engine/security/rootless/)은 root 소유 setuid `newuidmap/newgidmap`을 요구한다. 현재 호스트의 사용자 권한만으로 그 조건을 충족할 수 없다. [C0 Actions 실행](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/36303540834)에서 의존성 이미지 빌드와 PostgreSQL 18.6 기동·영속성은 검증됐다. 전체 앱 서비스 실행과 복구는 아직 미검증이다.

사용자에게 농업 과학의 전문 판단을 요구하지 않는다. 출처와 분야 조사는 전문 Codex CLI 조사가 맡는다. 사용자는 자기 농장의 선호나 관리하는 기록만 동의·접근 조건에 따라 제공한다. 협력 기관이나 제공자 승인을 기다리는 상태는 **외부 증거 대기**로 표시하며 코드 작업 완료로 처리하지 않는다. 측정 근거와 사전 등록된 시험 없이는 수치 수용 비율이나 모델 정확도 주장을 정하지 않는다.

**사용자 가정 자료의 지속성 보완 후보:** [7종 원천 저장 계약](../contracts/market-user-source-store-v1.md)에 따라 불변 작업 입력·판본·해시·실제 로그인에 결합한 저장/재생을 구현했다. [구현 증거](../research/market-user-source-implementation.md)는 합성 시험 범위를 기록한다. 실제 제공자 자료·권리/QC 검토, 보호된 운영 설정·입력 오케스트레이션·CLI/전체 G1/G4는 계속 보류다.

**결정적 simulation 연결 후보:** [열 작업자](../contracts/thermal-simulation-worker-v1.md)는 실제 불변 작업·현재 임대/권한에 결합해 Run과 완료를 한 거래로 게시하며 전경 프로세스 실행을 제공한다. [증거](../research/thermal-simulation-worker-implementation.md)는 성공·보류·취소·만료·롤백·프로세스 중단 후 새 시도를 기록한다. 실제 Codex/독립 증거·HTTP 제출·워크플로/브라우저·운영 G1/G4는 남아 있다.

**첫 웹 접수·조회 연결 후보:** [웹 계약](../contracts/web-location-shell-v1.md)과 [증거](../research/web-location-shell-implementation.md)에 따라 한국어 입력·작업/보류 화면, 고정 DTO 검증·동일 요청 재확인, 실제 TLS/SCRAM/Chromium 연결을 검증했다. 320/768/1440px·글자 200%와 키보드 시험이 통과했다. 시험 실행기는 가짜 CLI이며 완전한 농장/경제/시장 입력과 카드·지도·3D·실제 모델·전체 G1/G4는 남는다. 새 웹 CI의 정확한 head 결과는 별도 확인한다.

**저장 경제 가정 조회 후보 (2026-09-29):** [조회 계약](../contracts/api-market-user-source-read-v1.md)과 [증거](../research/market-user-source-read-implementation.md)는 실제 SCRAM 저장소의 사용자 소유 목록·지정 판본, 최초 입력/해시 대사, 읽기 전용 Bearer를 다룬다. 금액/수량 문자열·단위·null을 그대로 읽으며 기록이나 산술 결과를 생성하지 않는다. 사용자 경제/시장 입력 화면, 실제 모델·독립 근거·전체 G1/G4 수용은 남아 있다.

## 경제 웹 입력·계산 연결 후보 (2026-09-29)

[경제 화면 계약](../contracts/web-economic-workspace-v1.md)과 [검증 기록](../research/web-economic-workspace-implementation.md)은 사용자 소유 숫자 가정의 새 판본 등록, 실제 원장·공동 충격 선택, 시나리오/계산 접수와 완료 서버 금액·보류 조회를 연결한다. 금액은 서버 문자열/null을 그대로 표시하며 응답 유실은 같은 단계의 입력·키로 재확인한다. 새 숫자의 권리·공동 가정 판본 등록·선택 후보를 추가했다([기록](../research/web-joint-amendment-implementation.md)). [월별 현금 조회 후보](../contracts/api-economic-cash-flow-v1.md)는 같은 완료 증명·읽기 권한·원장 재계산을 검사하고 한국 월 구분·UTC 최저 잔액 시각을 표로 연결한다([검증 기록](../research/web-economic-cash-implementation.md)). [손익분기 화면 후보](../contracts/web-break-even-workspace-v1.md)는 실제 저장 판매·수금과 순서가 있는 공동 가정 판본을 계획·완료 결과에 연결하며, 응답 유실 시 고정 제출 해시로 저장 접수 기록을 조회한다([검증 기록](../research/web-break-even-workspace-implementation.md)). 일반 원장·정산 작성, 전체 농장 입력, 자동 시험 가정 생성·새로고침/미저장 접수 복구·실제 CLI·최종 작물 평가·3D/전체 G1과 독립 G0/G2/G3/G4 수용은 남아 있다. 기존 작업 체크와 관문을 해제하지 않는다.
