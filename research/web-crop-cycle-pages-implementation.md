# 긴 저장 결과의 웹 decoder와 순차 페이지 수용

상태: **로컬 소프트웨어 수용, 2026-10-06 KST**.
source snapshot `61ac06069f3510cda8248eea4b5b72117b49d04a`와
[불변 영수증](artifacts/web-crop-cycle-pages-reference-20261006.json)을 고정했다.
[실제 runtime/API](api-crop-cycle-runtime-implementation.md)를 선행으로 구현한
[5 core파일 계약](../contracts/web-crop-cycle-pages-v1.md)의 수용이다.

## 무엇을 연결했는가

`cycleCropReplay.ts`의 닫힌 decoder, summary/page getter와 한 페이지 단위 iterator를
기존 `api.ts`의 Bearer/AbortSignal·30초/2MiB request에 연결했다.
기존 startup sample helper의 본문을 바꾸지 않고 export만 추가했다. 원50개 C/N·
16누적·4진단·단위/UTC를 재사용하고 네 residual/budget 쌍을 검증한다.
cycle manifest/reference와40,000,000걸음·131,072기록 한도는 별도로 검사한다.

실제 합성 short12개/25시간11개의200 공개 decoded JSON을 원 raw와 그대로 대사했다.
이는 wire bytes·운영 목록·실제 농장 이력이 아니다. fixture는857,787bytes이며 인증 값,
원 forcing·농장 개인정보·권리 선언을 포함하지 않는다. 브라우저 번들에 fixture를 연결하지 않았다.
서버가 권리와 custody·canonical manifest hash를 검증한다. 클라이언트 검사는 그 서버 판단이나
관문을 대신하지 않으며 새로운 생장 계산·생과 kg·추천을 만들지 않는다.

iterator는 summary를 먼저 받고 실제 next_offset을 따라 한 페이지씩 제공한다.
전체 배열을 쌓지 않고 현재 원 페이지64 sample/8 event 이하만 반환한다.
소비자가 다음 요청을 할 때 진행하며 같은 API instance에서 HTTP 동시 요청은1개다.
종단까지 count/total을 대사한 뒤에만 `complete:true`를 반환한다. 중단/부분 페이지에는
완료 표시를 주지 않는다. 출력0·선택 출력은 허용하고 완료 출력의 시작/끝을 강제하지 않는다.
hold의 소수 초/last_confirmed는 정상 frame과 분리한다. 같은 summary가 있을 때
sample은 hold 이전, event는 hold 시각 이하만 허용한다.

## 통과한 검증

| 검증 | 결과 |
| --- | --- |
| 새 cycle 집중 | 120개 통과 |
| 기존 startup/coupled/API 포함 집중 | 4파일·296개/6.22초 통과 |
| 웹 전체, 의존성 수정 전 | 18파일·503개/6.47초 통과 |
| 타입 검사/빌드 | 종료0, Vite750ms; 기존500kB chunk 경고 유지 |
| 원량/보존 | 실제23 공개 응답 동일·helper export만 추가·backend49개 hash 동일 |

잘못된 판본·단위·타입/nonfinite·50배열·추가/누락 키·수지·혼합 hash/첫 recorded_at·
중복/역순/미래·hold 이후 기록을 거부했다. byte-short 페이지·출력0·빈 종단과
형식용513개 단일 기록 페이지,131,072종단 offset을 확인했다.
이 한도 fixture는 저장 형식 시험이며 긴 작물 계산이나 그 부하 수용이 아니다.
응답 중 lookup/query/summary 변경·취소·권리 오류, 요청 중복·소비자 중단도 확인했다.
첫 시험은 module 부재, 페이지 시험은 factory 부재로 실패한 뒤 구현으로 통과했다.
현재 실제 `gpt-6.1-sol / xhigh` CLI의 개발·다섯 축 자체 검토를 기록했으며 재귀 호출0회다.

## 남은 단계와 게시 조건

`web-crop-cycle-pages`만 완료했다. 다음은 현재 범위 helper → 화면/같은 UTC3D →
실제 PG/TLS/WebGL이다. 해당 연구3D는 **4–6집중시간**, 하루4시간 기준
**2026-10-06–08 KST 잠정**이며 실제 브라우저/응답·정리 실적에 따라 갱신한다.
새 브라우저·3D 시험은 이번에 실행하지 않았다. 전체 작기 부하·생과·자원/경제는 별도다.

`d61bcb3`의 hosted 웹은 단위·타입·빌드를 통과했으나 간접 개발 의존성
source-map-js1.2.1의 high 감사에서 실패했다. browser step은 실행되지 않았다.
공식 수정판1.2.2의 단일 잠금 갱신을 별도 검증하며 실패한 CI를 로컬 결과로 수용하지 않는다.
현재 실제 품종 입력·독립 국내 자료·crop Run은0건, G0–G4는 미평가이며
미래 생산량·마진·추천 완료 날짜는 자료 확보/검증 이후 정한다.
