# 검증 계산 결과의 같은 UTC 웹·3D 연결 — v1 개발 계약

2026-10-07 KST. native Codex CLI `gpt-6.1-sol / xhigh`, 재귀 CLI0회.
작업 `crop-cycle-calculation-client-view`의 선행은
[새 API의 실제 runtime/TLS 수용](api-crop-cycle-calculation-transport-v1.md)이다.
이 계약의 작성은 SDK·화면·실제 브라우저 수용이 아니다.
기존 [범위·3D 계약](web-crop-cycle-replay-v1.md)의 원값/현재 범위/직렬 요청 의미를 따른다.

## 현재 코드와 연결 경계

기존 `web/src/cycleCropReplay.ts`는 `crop-cycle-result-v1` ID,
`crop-cycle-replay-v1` 응답, 원 execution/manifest literal만 받는다.
`cycleCropWindow.ts`와 `CycleCropReplay.tsx`도 이 타입과 API에 결속돼 있다.
새 서버의 verified ID/validation을 구형 ID로 바꾸거나 필드를 삭제해 통과시키지 않는다.
기존 sample/event 단위·수지 검사와 원 장면/그래프의 수치 모식도는 재사용한다.

새 조회는 `/v1/crop-cycle-calculation-research-results/{result_id}`와
`crop-cycle-verified-result-v1:<64 hex>`를 사용한다. 서버의 실제 OpenAPI/공개 DTO를 기준으로
`crop-cycle-calculation-replay-v1`, verified artifact ref, 새 engine version,
`runtime_roles_code_sha256`, `input_read_context` dependency 및 두 input_validation 객체를 검증한다.
`context_sha256`과 원 `validated_context_sha256`은 각 의미를 보존하며 서로 대체하지 않는다.
summary의 evidence/validated context/engine/calculation code/dependency와 reference의 대응도 대사한다.

같은 farm·result ID·study/revision·recorded_at·reference 전체가 바뀐 페이지는 합치지 않는다.
추가 필드·잘못된 literal/단위/형태·비유한 수치·미래/역순/중복 UTC·부당한 hold는 거부한다.
완료 출력0개, 확인 과거 hold와 빈 hold, solver 진단의 소수 초 UTC를 보존한다.
일반 CH2O·개수 상당량을 생과 kg/판매량/농장 정확도나 예측·추천으로 변환하지 않는다.

## 작은 구현 순서와 다음 한 단계의 수용 기준

1. **`crop-cycle-calculation-client` — 새 SDK와 공개 fixture, 4 core파일.**
   새 `web/src/calculationCycleCropReplay.ts`, 집중 시험,
   `web/src/api.ts`의 명시 factory 연결과 합성 공개 DTO fixture 한 파일이다.
   원 `cycleCropReplay.ts`/기존 SDK의 literal·의미를 보존한다.
   기존 startup sample/coupled event/UTC validator와 공통 인증 request를 재사용한다.
   summary/page와 순차 iteration은 원64/8 상한·30초/2MiB·단일 진행 요청을 유지한다.
   실제 새 공개 projection의 summary/sample/event/과거·빈 hold를 원량/UTC/전체 provenance와 대사한다.
   잘못된 새·구형 판본 혼합, validation 대응 불일치·부당한 next/offset/total·byte-short page,
   현재 권리 오류·취소·늦은 응답·선택 변경·종류별 끝/빈 마지막 page를 검사한다.
   최대 동시 요청1개, 이미 끝난 iterator의 추가 요청0개와 실패 후 부분 성공 비반환을 확인한다.
   공개 fixture는 소유 합성 응답이며 인증/tenant/키·원 private 입력을 포함하지 않는다.
   focused unit·typecheck·build 및 기존 cycle/startup/API 회귀가 통과해야 이 자식만 체크한다.
2. **`crop-cycle-calculation-window-view` — 저장 참조·현재 범위와 기존 3D 판본 선택.**
   SDK 수용 후 bounded window의 typed 새 참조와 기존 연구 화면의 명시 판본 선택을 작은 계약으로 고정한다.
   현재 범위의 sample64/event8 이하, 원 sample 인덱스 선택·표/그래프/장면의 동일 ID/UTC,
   입력/계정/범위 변경·권리 실패 때 이전 배열/장면/timer 제거를 검증한다.
   현재 범위 C/N 비교 척도·LAI 한 면 면적·연구/품종 미검증/미평가 표시는 보존한다.
   원 v1/v2/v3/cycle 선택과 의미를 유지하고 새 framework·재계산·보간·임의 생장 애니메이션을 추가하지 않는다.
   기존 화면 확장에는 `12ui-design`과 실제 브라우저 검증을 적용한다.
3. **`crop-cycle-calculation-native-browser` — 실제 소유 PG→새 보호 설정/TLS→WebGL.**
   앞의 SDK/화면 수용 후 서버·브라우저 연결/정리의 작은 계약을 고정한다.
   소유 등록 농장의 실제 계산 결과/관리 사건과 확인 과거·빈 hold를 조회해
   원 sample/event·50 C/N·LAI·표/그래프/mesh/선택 UTC를 대사한다.
   읽기 parser/context/QC/RHS/advance/put/proof 발급0, 전체 본문30초/2MiB,
   단일 HTTP 요청·권리/계정 오류·모바일/키보드·WebGL loss/restore·이전 renderer/observer/timer 정리를 확인한다.
   실제 HTTP/원 결과/브라우저 캡처·DB/역할/비밀/server/PG PID/data 정리 증거 뒤에만 부모를 체크한다.

다음 한 단계는 1번 SDK4파일이다. 사용자가 확인할 산출물은 새 공개 형식과 원량/UTC 대사,
SDK 검증 기록이다. 화면 캡처와 실제 WebGL은 2·3번의 산출물이다.
형식용 큰 total/복제 fixture와 실제 생장 계산 범위는 별도로 기록한다.

## 의존성과 일정

원 client·범위 helper·화면/native 시험과 새 DTO의 판본 차이를 확인한 작업 분해에 근거해
SDK2–3집중시간, 범위/화면2–4집중시간, 실제 PG/TLS/WebGL·정리3–5집중시간의
**작은 웹 연결7–12집중시간 잠정**으로 둔다. 실제 실패와 통과 실적으로 각 추정을 갱신한다.
CI 대기·전체166일 등록 prefix 비용/저장·복원·실제 저사양 기기·pixel fidelity·
생과/물/양분/구매 에너지·Decimal 경제와 외부 자료 확보는 포함하지 않는다.
실제 승인 품종 입력·국내 독립 검증 자료·실제 작물 Run0건과 G0–G4 보류는 유지한다.
계산 개발과 자료 확보를 병행하며, 최종 생산 예측·추천/공개 운영 날짜는 외부 증거 확보 전 확정하지 않는다.
