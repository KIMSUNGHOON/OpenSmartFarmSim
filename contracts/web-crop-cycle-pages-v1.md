# 긴 작물 연구 결과의 웹 조회 계약 — v1 후보

상태: **구현 준비 후보·cycle runtime 긴 HTTP 수용 전**, 2026-10-06 KST.
작업 `web-crop-cycle-pages`; [API](api-crop-cycle-pages-v1.md) 전체 수용이 코드 착수의 선행이다.
현재 실제 Codex CLI `gpt-6.1-sol / xhigh`에서 기존 decoder/실제 짧은 TLS/공개 DTO를 대조했다.
turn_context `2026-10-05T23:53:08.250Z`, 원 line SHA
`e38b9052100d7996209dfa1b5ab60c18236b6d3b47d740468fb432b9fac65a22`, 재귀 실행0회다.
이 계약은 새 UI/3D·API·품종/작기 수용이 아니다.

## 같은 저장 참조

새 `cycleCropReplay.ts`의 조회는 닫힌 result_id/farm4개로 구성한다.
`crop-cycle-result-v1:<64 hex>`를 기존 v1/v2/v3 ID로 바꾸지 않는다.
응답의 닫힌 top9개, reference·summary·manifest·page의 실제 API 키와 literal/정수/유한량/
단위/기간·UTC를 검증한다. source/프로필/정책/코드/HEAD/proof/payload 등 hash와 첫 DB
recorded_at, farm/study/revision/reference 전체가 바뀌면 같은 결과로 합치지 않는다.
계수·권리 선언·tenant·경로·private ID를 받아들이지 않는다.

sample은 원50 N/C·기관/온도/LAI·16누적/4진단과 같은 UTC다.
기존 startup sample 검증 함수의 본문은 그대로 export하여 재사용할 수 있다.
기존 startup decoder/manifest·한도·완료 조건을 cycle 응답에 적용하거나 변환하지 않는다.
네 residual/budget 쌍도 검사하며 frontend가 생장식·과실·수지 값을 새로 계산하지 않는다.

completed 결과의 출력은 선택된 원 시점이다. 첫/마지막 출력이 input start/end일 필요가 없고
출력0개도 허용한다. hold의 확인 과거와 last_confirmed/solver phase·소수 초 UTC를 따로
검증하며 진단을 정상 sample로 추가하지 않는다. 미래/중복/역순 기록은 거부한다.
CH2O·개수 상당량을 생과 kg/실제 개수·판매량/경제 결과로 환산하지 않는다.

## 페이지와 자원

public API는 summary 단독 조회와 samples/events 단독 페이지 조회를 제공한다.
summary에는 offset/limit를 보내지 않고 page view는 canonical offset/limit만 보낸다.
공통 request의 현재 Bearer/AbortSignal·전체 body30초/2MiB를 그대로 사용한다.
닫힌 lookup/query를 먼저 검증하고 응답 후 선택 identity와 취소 상태를 다시 확인한다.

순차 iterator는 먼저 summary를 확인하고 각 원 종류의 offset0부터 반환된 next_offset을
따라간다. 원 byte budget으로 limit보다 적은 기록도 허용하되 next는 실제 record 수만큼
진행해야 한다. total 이하/같은 total의 마지막 빈 page, 같은 reference와 종류/limit/
offset/UTC를 대사한다. 요청은 한 번에 하나이며 같은 시점을 중복 수집하지 않는다.
최대131,072 record를 기존 short의512/128·16요청 한도로 제한하지 않는다.
1record씩 진행하는 최악의 형식도 total에 따른 유한 요청 상한으로 끝나야 한다.

페이지 getter/iterator는 한 페이지 단위로 처리해 caller가 모든 원 배열을 보관하지 않아도
전체 저장 범위를 읽을 수 있게 한다. 이 단계에서 global mesh 축이나 전체 3D 표시를
만들지 않는다. 중간 페이지는 완료된 전체 결과로 표시하지 않고, iterator 종료 시에만
종류별 count/마지막 next와 수집 완전성을 확인한다. 누락/혼합/부분 성공을 성공으로 반환하지 않는다.
권리 오류·새 계정/ID·취소·늦은 응답은 caller에 오류로 전달하며 이전 숫자/장면을 복원하지 않는다.
화면의 표시 범위·공통 축·정리와 실제 저사양 측정은 다음 `web-crop-cycle-replay`에서 수용한다.

## 첫 작은 구현과 수용

예정5 core파일: 새 decoder/페이지 module·집중 시험, 기존 `api.ts`의 factory 연결,
기존 `startupCropReplay.ts`의 본문 변경 없는 sample helper export,
실제 합성 TLS의 공개 decoded JSON fixture 한 파일이다. fixture는 wire bytes/운영 이력/
실제 농장 데이터가 아니며 인증 값·원 private 입력을 포함하지 않는다.

1. 실제 short/25시간의 summary/sample/event/hold 공개 JSON을 원량·UTC·전체 참조와 대사한다.
2. 별도 판본/단위·잘못된 타입/nonfinite·50배열·추가 필드·수지·혼합 참조·미래/중복을 거부한다.
3. 같은 lookup/참조로 순차 진행, 짧은 byte page·출력0·빈 끝·hold·offset/total 한도,
   취소/선택 변경/권리 오류/늦은 응답·완전성·최대 동시 요청1개를 확인한다.
4. focused unit/typecheck/build와 기존 startup 응답/페이지 의미 보존을 확인한다.
   한도용 재배열/복제 fixture는 형식 시험으로 표시하고 실제 긴 생장 계산으로 보고하지 않는다.

API 긴 응답 예산 통과 전 구현을 착수하지 않는다. client2–3집중시간 추정은 실제 시험 실적으로
갱신한다. UI/실제 PG→TLS→WebGL은 별도4–6시간이며 client와 합쳐6–9집중시간이다.
실제 전체 작기/품종/G0–G4 수용은 별도다.
