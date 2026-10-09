# 저장 시작 유보 모델 — 인증된 페이지 조회 API

날짜: 2026-10-05 KST. **합성 연구 API만 로컬 수용**했다.
구현 commit `7d4d310`. [계약](../contracts/api-crop-startup-replay-v1.md),
[시험/응답·code hash/실제 TLS·SCRAM·정리 증거](artifacts/api-crop-startup-replay-reference-20261005.json)를 확인한다.

## 실제 CLI와 구현 범위

현재 CLI 세션 `01a0e064-b01b-7a22-8ef8-dd4afe0eb7dc`의 실제 turn_context
`2026-10-05T03:26:20.736Z`에서 **gpt-6.1-sol / xhigh**를 확인했다.
같은 세션에서 API 설계/구현/검토했으며 CLI를 재귀 실행하지 않았다.
context line hash와 출력 파일 hash를 증거에 보존했다. 실제 제품 runtime CLI는 별도 미수용이다.

새 GET 경로는 v3 result ID/등록 farm과 같은 현재 READ/source/program 권리·HMAC를 요구한다.
새 optional store/factory와 명시 startup flag를 같은 service/jobs/principal에 묶는다.
기본 비활성은 503, 잘못된 factory/flag 조합은 연결 전에 거부한다.
조회·투영 뒤에도 현재 권리/tenant를 다시 확인한다.

기존 v2의 단위/기관/50 N/C·페이지 타입을 재사용했다. 새 누적16개·수지 진단4개,
program/정책2개/code9개·artifact dependency/manifest, 면적 문자열/단위와 연구 한계를
닫힌 타입으로 제공한다. floor area는 원 문자열을 보존하며 양의 면적을 schema와 runtime에서
같이 검사한다. 새 222행 API 모듈과 조립/시험/고정 OpenAPI 총6개 파일에 한정했다.
새 계수·방정식·큐/worker·Framework·상주 서비스는 추가하지 않았다.

원 inputs/profile/notice·권리 선언·tenant/HMAC/key는 공개하지 않는다.
연구/미게시/품종 미검증·관문 미평가, 명시 진입/유보·전환의 수렴 미평가와 작은 구획의
약8.52% 합성 수치 오차를 유지한다. 생과 kg/수확·자원/미래 마진·추천으로 바꾸지 않는다.

## 통과한 검증과 계약 갱신

- **252개 고유 시험을 분할 수용**했다: 투영/공통 OpenAPI 106개·103.89초,
  실제 DB/HTTPS 3개·431.28초, 기본 runtime/operator·기존 v1/v2 회귀143개·68.57초다.
  새 API 시험은 총47개이며 건너뜀0개다. 이를 252개 단일 실행이나 전체 backend 통과로 쓰지 않는다.
- 첫 RED는 새 모듈 부재였다. 초기 순수 투영26개가 통과했고, 확대106개 중 공통 snapshot
  3개가 실패했다. 공식 `python -m app.api_openapi --write`로 새 계약을 export한 뒤
  현재 라우트/CLI check와 최종106개가 통과했다. 판정/시간 제한을 완화하지 않았다.
- 여섯 시작 프로그램의 원값·전량 제거 후 재유입, 512출력/128사건 페이지의 전체성/순서/
  같은 hash, hold/빈 과거·소수 초/별도 진단, 재적분 없음과 현재 권리/tenant·query/body/
  cap·형식/행/모델/단위/수지 변조를 확인했다.
- 기존 **46개 경로/128개 schema가 동일**하며 새 경로1개/schema10개만 추가됐다.
  새 모델/프로필/artifact·v1/v2/v3 custody/기존 coupled API의 **28개 pin**을 보존했다.
- 실제 표준 HTTPS/Bearer·SCRAM으로 19개의 **전체 본문**을 읽었다.
  최대 **14.248425초/700,084 bytes**로 30초/2 MiB 제한 안이다.
  동일 재조회·권리 철회·다른 tenant·서버 재시작, 현재 완료/과거 결과와 원량/hash를 대사했다.

## 자원·정리와 외부 의존성

기존 PostgreSQL16.15·잠긴 Python/psycopg/pytest를 사용했다.
각 실행은 단일 private loopback/SCRAM DB·32연결/16 MB shared buffers/1 MB work memory와
순차 nice 시험이었다. 최대 페이지/모든 응답의 과정 child 최대 RSS는 **434.49 MiB**다.
합성 최대 packet/페이지 검증의 수치이며 실제 전체 작기/동시 처리량으로 확대하지 않는다.
HTTPS server 두 차례 종료/join, 각 실제/회귀 실행의 역할/schema/비밀번호0개·DB 종료와
private cluster/관리자 비밀번호 제거, 현재 소유 서비스0개를 확인했다.

자료/권리 공급자·key는 합성 시험용이다. 실제 TLS/SCRAM은 software 경계의 증거이며
자료 G0·독립 G1–G4/제품 CLI·국내 작물 예측/추천의 수용이 아니다.
국내 독립 자료0건/actual forcing·crop Run0개·전체 작기/생과 kg·자원/경제의 holds는 유지한다.
개발/자료 확보를 병행하고 운영 기반은 `d19f7c0` 범위로 고정한다.

선행 `d105daa`는 [hosted CI5개·backend3,370개/별도UID4개](artifacts/crop-plant-startup-math-ci-20261005.json),
여섯 동일 목록/정리·집계로 기관 시작 RHS/적분/artifact까지 수용했다.
그 SHA에 새 저장/API는 없다. 저장까지의 `92cade3` CI는 같은 실행을 유지하며 확인 중이고,
이번 API는 아직 원격 수용 전이다. 진행 중 실행을 취소하는 push는 하지 않는다.

## 다음 한 단계와 일정

다음은 [같은 UTC 성장 3D 연결](../contracts/web-crop-startup-replay-v1.md)이다.
먼저 새 응답 decoder/순차 페이지 결합에서 v3 ID/farm/hash·50 N/C/16누적/4진단을
검사하고, 512출력/128사건·누락/혼합/취소·소수 초 hold/빈 과거·현재 거부를 확인한다.
이후 같은 원값·UTC로 기존 수치 도형/표/그래프를 연결하고 실제 저장→TLS→브라우저를 수용한다.
불변 sample 인덱스만 이동하며 임의 seed/보간/실제 과실 숙기·생과중을 추가하지 않는다.

API는 **10월5일 KST 로컬 완료**다. 다음 decoder/pages0.5–1시간, 화면/도형·브라우저1–2시간,
실제 저장 경로/정리·보고0.5–1시간으로 **2–4 집중시간**을 추정한다.
기존 coupled 화면의 129단위/19Chromium/실제 경로1개 경험이 근거이며 하루4시간 기준
목표는 **10월5–6일 KST**, CI 대기는 별도다. 실제 작기/예측·추천 날짜는 자료 확보 뒤 추정한다.
