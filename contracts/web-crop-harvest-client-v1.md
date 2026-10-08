# 등록 수확 결과 웹 SDK — v1

2026-10-09 KST. native Codex CLI `gpt-6.1-sol / xhigh`, 재귀 CLI0회.
선행 [실제 SCRAM/HTTPS 수용](../research/crop-harvest-runtime-tls-implementation-20261009.md) 뒤
`crop-harvest-client`를 구현한다. core5파일은 이 계약·`web/src/harvestReplay.ts`·
`web/src/harvestReplay.test.ts`·`web/src/api.ts`의 명시 factory 연결·
`web/e2e/harvest-recorded-responses.json`이다.

## 다음 한 단계 수용 기준

- 기존 Bearer/AbortSignal·30초·2MiB request와 `/v1/crop-harvest-research-results/{result_id}`를 사용한다.
  닫힌 farm/result lookup·summary/records·offset/limit≤64를 검사하고 진행 요청은 최대1개다.
- [서버 DTO](../backend/app/api_crop_harvest_replay.py)의 모든 중첩 필드·판본·단위·UTC·유한 수량·
  합성/미평가/승인false를 검사한다. 원 source/result/farm·환산/배정 판본·미배정·관측 비교 상태를 보존한다.
  알 수 없는 필드·혼합 판본/농장·잘못된 참조·형태·수량을 거부한다.
- 정확 수량의 분자/분모는 문자열로 보존하고 bounded BigInt로 정규형과 제공된 Float64 표시값의
  최근접 짝수 반올림을 검사한다. 검증 때문에 수확/경제 모델을 실행하거나 저장값을 대체하지 않는다.
  할당 비율·미배정 합과 주어진 원 수량의 관계를 검사한다. 브라우저가 HMAC/파일 hash·현재 권리 검사를 대신하지 않는다.
- summary/page의 공통 provenance와 배정 선언을 대사한다. 순차 iterator는 원 end UTC·같은 시각의
  terminal→event 순서·중복/역순·offset/next/total·전체성·취소/늦은 응답·변경된 선택을 검사한다.
  동시 요청/자동 prefetch·전체 배열 수집은 하지 않는다. 끝/실패/소비자 종료 뒤 추가 요청이 없다.
  한 질량 parameter hash의 전역 판본·근거/코드·배정 선언은 행/페이지 사이에 같아야 한다.
  segment의 실제 구간 차이는 보존한다. 다음 페이지의 기준은 반환 객체와 분리한 이전 행의
  시간/종류·전역 identity 문자열 snapshot이며 소비자의 반환 객체 변경이 기준을 바꾸지 않는다.
- 소유 실제 HTTPS 원 summary/6행 body를 fixture로 사용한다. 분할/빈 끝 body는 원 body에서 구성한 bytes가
  실제 HTTPS 영수증의 SHA/길이와 일치할 때만 그 원 응답과 동일하다고 표시한다.
  기타 변형은 형식/거부 시험이며 실제 농장·새 계산·새 HTTP 증거로 표시하지 않는다.
- 집중 시험·기존 소비자를 포함한 웹 전체·typecheck/build·원 source 보존과 소유 임시/프로세스 정리,
  원 도구 종료를 확인한 뒤 SDK와 이미 수용된 선행 자식의 HTTP/SDK 부모만 체크한다.

## 후속 범위

같은 UTC 수확 표/3D·실제 DB/API/WebGL·전체166일 질량 부하·기후/자원/Decimal 경제는 후속이다.
실제 품종 계수/독립 농장 자료·G0–G4·생산/미래 마진/추천·배포를 이번 SDK로 수용하지 않는다.

## 로컬 수용

2026-10-09 00:26 KST. [검증 보고서](../research/web-crop-harvest-client-implementation-20261009.md)·
[원 종료/source/정리 영수증](../research/artifacts/web-crop-harvest-client-reference-20261009.json)의 집중94개/웹814개·타입/빌드·원 종료0으로 SDK와 HTTP/SDK 부모를 수용했다.
시험 전 계약 snapshot은 영수증에 보존한다. 표/3D·실제 생산/관문은 후속이다.

## 최종 보완 수용

2026-10-09 00:32 KST. 앞선94/814 candidate 기록은 보존하고, 전역 질량 판본 혼합과 반환 객체 변경의
세 실제 RED 반례를 보완한97/817·현재 타입/빌드·원 종료0으로 최종 SDK 판본을 대체했다.
[최종 영수증](../research/artifacts/web-crop-harvest-client-v2-reference-20261009.json)의458 source/정리와 시험 전 snapshot을 따른다.
