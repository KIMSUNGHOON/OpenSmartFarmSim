# 시작 유보 계산 — 농장 결합 불변 저장 v3

날짜: 2026-10-05 KST. **합성 연구 custody의 로컬 수용**이다.
구현 commit `0e5e012`; 선행 [schema/명시 권한](crop-startup-storage-schema-implementation.md)은 `ec7c634`다.
[v3 저장 계약](../contracts/crop-result-v3.md),
[119개 시험/실제 SCRAM·저장 ID/hash·정리 증거](artifacts/crop-startup-result-storage-reference-20261005.json)를 확인한다.

## 실제 CLI와 변경 범위

현재 Codex CLI 세션 `01a0e064-b01b-7a22-8ef8-dd4afe0eb7dc`의 실제
turn_context `2026-10-05T02:35:01.174Z`에서 **gpt-6.1-sol / xhigh**를 확인했다.
같은 세션에서 설계/구현/검토했으며 CLI를 재귀 실행하지 않았다.
실제 context line hash와 출력 코드/시험 hash를 증거에 보존한다. 제품 runtime CLI는 미수용이다.

새 store/test 두 파일에 한정했다. 변경 없는 v1의 farm/current-right checks를 재사용하며
새 `crop-result-v3` 표·HMAC domain·artifact reader를 사용한다.
현재 farm/crop/달력/면적·등록/source hash·program available_at와 계산/display 권리를
계산 전후·commit 직전·commit 뒤 반환 전·조회 시 검사한다.
서버 builder가 직접 계산하고, 완료된 동일 요청/GET은 재적분 없이 읽는다.
HTTP 계산 접수·새 큐/작업자·상주 서비스는 추가하지 않았다.

원 요청/농장 binding·권리 정책·저장/farm 검증 코드와 artifact bytes/hash를 닫힌
20 MiB packet에 묶는다. 같은 intent는 한 immutable row이고 다른 요청은 conflict,
잠긴 intent는 pending, 정정은 새 revision이다. v1/v2·모델/artifact/profile **25개 pin**과
선행 schema installer의 동일 코드, 나머지 role/config/fixture **5개 파일의 동일 bytes**를 확인했다.

## 통과한 검증과 발견한 수정

- 최종 **119통과/0건너뜀·1,150.57초**의 단일 집중 실행이다.
  새 custody 18개, artifact 79개, schema/role/config 20개와 기존 farm/v2 constructor 2개다.
  현재 전체 백엔드나 새 API/3D의 통과로 확대하지 않는다.
- 여섯 프로그램(빈 무유입·빈 진입·첫 구획만·전량 제거 후 재유입·양의 tail·밤)을
  실제 SCRAM으로 저장했다. 현재 코드 hash·첫 DB UTC·packet/artifact bytes와
  새 HMAC domain을 독립 HMAC 계산으로 확인했다. fresh store와 별도 fork Python
  프로세스에서 계산 함수를 실패하도록 바꿔도 같은 bytes를 읽었다.
- 동시/동일 재시도·충돌/새 revision·try-lock, 현재 scope/source/program 철회,
  farm/crop/기간/available_at·단위/origin/ID/권리 선언을 검사했다.
  잘못된 요청 14종과 비정규 JSON/중복/비유한/UTF-8/크기 5종은 저장하지 않았다.
- 수치 hold는 확인된 과거만 보존한다. 실제 다른 role의 접근과 authority 수정,
  owner trigger·HMAC/행/등록 job FK·owner payload 변조를 거부했다.
  서버 HMAC와 hash를 다시 계산한 내용 변조 **22종**도 binding/reader 대사에서 거부했다.
- 초기 구현 부재의 RED 뒤 첫 DB 집중 실행은 14통과/1실패·879.55초였다.
  역할 교체 시험 helper가 store 생성 전에 기존 farm service에서 거부되어,
  exact store의 생성 경계를 시험하도록 고쳤다. 실제 거부 조건을 완화하지 않았다.
- commit 뒤 program 권리 철회에도 반환되는 RED **1실패/38.14초**를 실제 DB에서 재현했다.
  거래 밖에 반환 전 current-right check를 추가했다. 최종 program/source/write-scope
  세 시험 모두 통과했다. commit 전 철회는 부분 행 없이 rollback, commit 뒤 철회는
  완전한 불변 행을 보존하며 반환을 보류한다. 권리 회복 후 동일 요청은 재계산하지 않는다.

## 자원·정리와 수용 경계

기존 PostgreSQL 16.15/잠긴 Python·Psycopg/pytest를 재사용했다. 단일 private loopback/SCRAM
DB·순차 nice 시험, 32연결/16 MB shared buffers/1 MB work memory였다.
초기 15개 과정의 실측 879.55초와 새 commit 경계/회귀를 근거로 최종 private 시험 harness의
wall budget만 1,800초로 잡았다. 제품 HTTPS의 30초 제한은 변경하지 않았다.
최종 wall 1,151.15초·child 최대 RSS **192.64 MiB**다. fork/큰 schema 거부 시험을 포함하며
전체 작기 처리량/실제 농장 성능으로 취급하지 않는다.
최종 **임시 역할/schema/발급 비밀번호 파일0개**, DB 종료/status exit3와 private cluster/
관리자 비밀번호 제거·소유 서버0개를 확인했다. 초기/RED 실행도 별도로 정리했다.

원천/program 권리 공급자는 합성 시험용이다. 실제 SCRAM/DB 무결성 시험은 자료의
실제 권리/QC·독립 농장/제품 CLI·G0–G4 승인이나 작물 예측·추천 수용이 아니다.
새 startup API/3D·전체 작기·생과 kg·자원/경제 결합은 남아 있다.
운영 기반은 `d19f7c0`으로 고정하며 국내 독립 자료0건/actual forcing·crop Run0개와
품종 초기/자동 S/W1/RGR·pre-onset·전체 작기의 외부 의존성은 유지한다.

## 다음 한 단계와 일정

다음은 [새 페이지 조회 API](../contracts/api-crop-startup-replay-v1.md)다.
같은 저장 ID/hash/UTC의 50 N/C·16누적/4진단, 512출력/사건 페이지와 현재 권리/
변조·hold/GET 재적분 없음, 실제 TLS/SCRAM 최대 전체 본문30초·재시작/정리를 확인한다.
사용자 산출물은 페이지 JSON/원값 대사·HTTPS 영수증이며, 그 다음 같은 UTC 성장 3D다.

custody는 **10월5일 KST 로컬 완료**다. API는 typed/조립1–1.5시간과 권리·페이지/
실제 HTTPS·정리1–1.5시간으로 **2–3 집중시간**을 추정한다. 하루4시간의 개발 시간
기준 목표는 **10월5–6일 KST**, CI 대기는 별도다. 실제 예측/추천 완료일은 독립 자료/
검증 작기 확보 전에 정하지 않는다. 자료 확보와 개발을 병행한다.
12:18 KST의 선행 원격 `d105daa`는 네 workflow 및 Backend 0–3파트가 성공,
4/5파트가 실행 중이다. 이번 schema/custody는 그 SHA에 없으며 전체 수용/새 push는
같은 실행의 terminal·여섯 목록/정리·UID/집계를 확인한 뒤 진행한다.
