# 시작 유보 모델의 같은 저장 UTC 성장 연구 3D — v1

상태: **응답/순차 페이지 로컬 수용; 새 화면 미수용**, 2026-10-05 KST.
[새77개/웹 전체376개·typecheck/build](../research/web-crop-startup-pages-implementation.md)와
[기록 응답/파일·시험 증거](../research/artifacts/web-crop-startup-pages-reference-20261005.json)를 확인한다.
선행은 [v3 페이지 API 수용](../research/api-crop-startup-replay-implementation.md)과
기존 [coupled 수치 장면](web-crop-coupled-replay-v1.md)이다.
현재 CLI `gpt-6.1-sol / xhigh`에서 판단하며 재귀 CLI를 실행하지 않는다.
실제 화면 변경에는 기존 12ui-design·브라우저 검증 절차를 적용한다.

## 한 결과와 같은 시점

정확한 `crop-result-v3`/farm 참조를 새 `crop-startup-replay-v1` 응답과 대사한다.
닫힌 decoder는 manifest 판본·code9개/정책2개/모든 hash, 면적 양의 문자열/m²,
50 N/C/기관·온도/LAI·16누적/4진단·UTC/phase/status/hold/연구 범위를 검사한다.
같은 ID/등록/첫 DB UTC·상태/기간·manifest와 단위/수량만 순차 페이지로 합친다.
한 요청은 30초/2 MiB이며 최대512출력/128사건의 누락/중복/혼합·offset를 검사한다.
최대16회 순차 요청으로 sample/event를 모두 수집한 뒤 공통 척도와 표/그래프/3D를 만든다.
loading/cancel·현재 권리 거부·새 ID/계정/재조회·늦은 응답에는 이전 숫자/장면을 지운다.

표/그래프/장면은 **result ID + farm + manifest + saved sample.at** 하나를 읽는다.
재생은 저장 sample의 정수 인덱스만 이동하며 생장 방정식/미래 상태/보간을 계산하지 않는다.
기존 논리 바닥1 m²의 LAI 한 면 면적, C와 N의 서로 다른 고정 공통 척도·50구획 순서를
원 서버 값과 대사한다. 빈 초기/전량 제거 시 영 과실량을 그대로 표현하고 임의 seed를 만들지 않는다.
도형의 좌표/색/높이는 비교 표시이며 실제 키·열매 크기·개수/착과 위치·숙기/수확 시점이 아니다.
새 누적의 requested/realized/deferred/fruit respiration과 네 수지 진단은 서버 원값/단위다.
CH2O 질량과 개수 상당량을 생과 kg/판매량·실제 개수로 환산하지 않는다.

hold는 확인된 과거만 재생하고 소수 초 UTC를 실제 시각 순서로 비교한다.
last_confirmed는 별도 진단이며 정상 관리 후 sample로 추가하지 않는다.
빈 과거는 장면/숫자 없이 보류와 필요한 근거를 표시한다.
명시 진입·빈 sink 유보·전환 수렴 미평가/작은 구획 합성 오차와 합성·미게시·품종 미검증/
관문 미평가·실제 짧은 기간을 유지한다. 임의 animation을 생산 예측으로 표현하지 않는다.

## 두 구획과 수용 기준

1. **로컬 수용 — decoder/페이지 결합:** 새 client 모듈/집중 시험과 필요한 기존 HTTP
   연결만 추가한다. v3 판본/같은 ID/hash/UTC·단위/50배열·16누적/4진단을 원 응답과 대사한다.
   최대512/128·빈 과거/소수 초 hold·형식/범위/혼합/누락/중복·현재 거부·계정 변경/늦은 응답/
   취소와 기록된 실제 TLS 응답의 decoded JSON 원값을 검증한다. 원 wire bytes로 표시하지 않는다.
   기존 v1/v2의 해석·조회는 보존한다.
   이는 새 장면이나 브라우저 전체 수용으로 표시하지 않는다.
2. **다음 한 단계 — 화면/도형/실제 경로:** 기존 수치 geometry와 표/그래프를 같은 sample에 연결한다.
   선택 LAI/50 C/N·구획 좌표/원량·0/큰 값/대체·정리, typecheck/build/단위·집중 Chromium,
   키보드/모바일/확대/움직임 줄이기·WebGL 불가/loss/restoration을 확인한다.
   실제 SCRAM 저장→표준 HTTPS→브라우저에서 빈 초기/제거 후 재유입·완료/과거/빈 hold,
   같은 ID/UTC와 원 수치·mesh, 현재 거부/재조회·요청/GPU/타이머·서버/DB/password 정리를 대사한다.
   화면 산출물·실제 검증·미실행/외부 의존성 뒤에만 부모 replay 작업을 체크한다.

첫 구획의 산출물은 검증된 시계열 객체와 decoder/페이지/TLS 원값 대사다.
두 번째는 사용자가 볼 화면과 원값/mesh·실제 저장 경로 증거다.
새 framework·agricultural coefficient·큐/상주 service는 이 화면의 개발 선행이 아니다.
decoder/pages는 10월5일 KST 로컬 완료다. 남은 화면/도형·브라우저1–2시간과 실제 경로/
정리·보고0.5–1시간으로 **1.5–3 집중시간/10월5–6일 KST**를 둔다(하루4시간, CI 대기 제외).
국내 독립 자료0건/actual forcing·crop Run0개·전체 작기/생과 환산/자원·경제·G0–G4와
실제 예측/추천 날짜는 별도이며 개발과 자료 확보를 병행한다.
