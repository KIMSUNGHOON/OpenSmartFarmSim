# 현재 참조 I/O 후보의 실제 비교 — 2026-10-19 KST

[선행 단계/청크 비용](crop-solar-capture-pending-phase-cost-20261019.md) ·
[기계 증거](artifacts/crop-solar-current-read-candidate-evaluation-20261019.json).

상태: **제품 코드는 유지. 전달/ACL 후보는 미채택, 행 묶음 조회는 시험 전용 타당성 관찰**.
현재 native `gpt-6.1-sol/xhigh`의 실제 문맥 시각/해시를 기계 증거에 기록했다.
재귀 CLI/하위 에이전트나 변경 없는 native CI 반복은 실행하지 않았다.

## 이전 판단과 재검토

직전 계획은 역할 감사 SQL 왕복 감소 후보를 다음 대상으로 적었으나,
[15→4 SQL 후보](runtime-role-audit-phases-evaluation-20261019.md)는 이미 실제 청크 개선 부족으로 기각돼 있었다.
이를 대조해 그 후보를 재적용하지 않았다. 아래 비교는 원 SQL의 전달 방식,
현재 조회의 실제 입력 수와 시험 전용 행 묶음, 다른 권한 행렬 계산의 관찰이다.
추가 보안 회귀나 native CI를 앞세우기 전에 실제 청크 비용으로 후보를 좁혔다.

## 1. 원 SQL pipeline 전달: 미채택

19696:0은 실제 SCRAM의 같은 연결에서21감사/표본·ABBA2를 비교했다.
원 SQL/검사 순서를 유지한 pipeline wrapper의 감사 중앙값은0.170595→0.170835초였다.
같은 두 custody의 실제2/3단계는 다음과 같았다.

| 원 구현 초 | 후보 초 | 관측 |
| ---: | ---: | --- |
|7.151417|6.926988|약3.1% 감소|
|6.966264|7.158691|약2.8% 증가|

감사183/role SQL2,745/원천1,824·중복 순서/원 값·UTC·checkpoint/원량은 같았다.
일관된 개선 근거가 없어 미채택했다. 제품의 SQL·연결 수명·권한 검사·수식은 바꾸지 않았다.
Psycopg의 [pipeline 문서](https://www.psycopg.org/psycopg3/docs/advanced/pipeline.html)는 전송/동기화 동작을 설명하며,
로컬 DB의 개선 여부는 이 실제 관찰로 판단했다. 설치된 lock은3.3.6이며 문서 페이지는3.3.7.dev1로 표시됐다.

## 2. 원 조회 footprint: 원천74·파생 입력34

1753:0은 기존 실제1→2단계를 계측했다. current12/registration24/재구성1·감사183,
연결144/SQL7,113·원천1,824·원 순서/UTC/proof를 보존했다.

| 원천 종류 | 호출 수 | 고유 키 수 |
| --- | ---: | ---: |
|economic_input|816|34|
|economic_scenario|48|1|
|input_rights|840|35|
|joint_shock|48|1|
|settlement_applicability|24|1|
|settlement_evidence|48|2|

총 원천 고유 키는74개다. 별도로 파생 입력34개를816회 조회했고 모두 미존재였다.
키/ID/원문은 공개하지 않고 집계와 순서 SHA만 기록했다.
벽시계9.494572초는 profiler/SQL 관찰 비용을 포함하며 다른 실행과의 성능 비교로 쓰지 않는다.

## 3. 시험 전용 행 묶음: 약5% 개선, 제품/보안 수용 아님

63672:0은 기존 pure verifier의 논리 getter·권리/현재 principal·role 감사와 비교 digest를 그대로 실행했다.
시험 코드만 DB 응답을 검증 시작 때 읽은 행으로 공급하고 끝에서 실제 DB 행을 다시 읽어 비교했다.
이 시험의 SQL interception과 tenant 전체 조회는 제품 구현으로 허용하지 않는다.

| 항목 | 원 구현 | 시험 후보 |
| --- | ---: | ---: |
|실제2단계 초|6.681044|6.341740|
|실제3단계 초|6.687740|6.325373|
|기존 개별 source SELECT|1,824|76|
|기존 개별 candidate-input SELECT|816|34|
|추가 전후 bulk SELECT|0|92|
|논리 원천 호출/role 감사|1,824/183|1,824/183|

두 실제 비교는 약5.1%/5.4% 감소했다. 같은 원 수치·UTC·checkpoint/원량·논리 읽기 순서와
검증 전후 실제 행 일치를 확인했다. 전체 처리량/원64·늦은 철회·수명/오류 경로 수용을 뜻하지 않는다.
전체 tenant에는 source85행/candidate-input11행이 있었다. 사용된74/34 키와 구분한다.

94960:1의 첫 시험은 tenant 전체 행 수를 사용 키 수와 같다고 가정해 실패했다.
정확한 내부 원인 위치를 수집하지 못했으므로 그 generic hold를 단일 원인으로 확정하지 않는다.
가정을 고치고 제한된 위치 기록을 추가한 뒤63672:0이 통과했다. 실패는 통과 수에 더하지 않았다.

## 4. 직접 ACL 행렬 후보: 더 느려 미채택

35079:0은 table/column 두 행렬의 계산만 시험 namespace에서 교체했다.
직접 ACL과 PUBLIC을 집계하고, 현재 소유자/superuser/membership/누락 역할·관계는 기존
PostgreSQL privilege 함수를 사용하는 후보였다. 감사 중앙값은0.195579→0.365118초,
실제 두 청크는7.197148→8.627488초/7.264936→8.970142초였다. 더 느려 기각했다.
원 값/UTC·감사/원천 순서는 보존했지만 보안 동등성 수용으로 세지 않으며 제품에 적용하지 않았다.
[PostgreSQL 권한](https://www.postgresql.org/docs/16/ddl-priv.html)과
[ACL 함수](https://www.postgresql.org/docs/16/functions-info.html#FUNCTIONS-INFO-ACCESS-TABLE)는 후보의 공식 근거다.
공개 문서 참조이며 농업/경제 자료를 채택하거나 복제하지 않았다.

## 다음 구현 범위

다음은 [닫힌 참조 행 묶음 계약](../contracts/market-current-reference-row-readset-v3.md)의 개발 단계다.
초기 full 검증과 각 current 경계를 유지하고, pure verifier 한 번의 필요한 정확한 키만 대상으로 한다.
전후 실제 DB 행·기존 모든 논리 getter/rights/principal·role 감사·코드/실행 소유/수명 검증을 갖춘 뒤
관련 철회/행·상태 변경·예외/복제 Context/청크 취소·임대와 paired 비용으로 수용 여부를 판단한다.
원64 정상→독립 hold→HTTP 취소→계산 중 WebGL→WSL 용량/사용자 적용은 그 이후 별도 수용이다.

통과한4개 관찰은 로컬58 회귀에 더하지 않는다. 각 guard는 원본2,148항목/5root/frozen 두 화면,
512MiB/PID/합1GiB·FD4→4·소유 PG/임시/passfile0을 확인했다.
성공 guard 합산 RSS 최대992,423,936bytes였다. 첫 실패도 보존/정리를 통과했다.
전체 backend/browser·fresh exec/SIGKILL은 재실행하지 않았다. 실제 농장 Run0·G0–G4 미평가·새 Solar 미배포다.
실제 자료/독립 농장/미래·대응 비교 외부 의존성과 전체 완료일 미정·goal active를 유지한다.

69769:0에서 기각/미채택 범위와 다음 primitive를 두 UI에 같은 no-store bytes로 게시했다.
현재 두 제품 파일/역할 감사 source pin·3syntax·로컬 링크2,333개·원 actor/header·frozen HTML/환기2,173파일·
5root/상한/FD/소유 정리를 확인했다. 합산 RSS893,460,480bytes였고 UI 코드/DOM/WebGL은 변경·재검사하지 않았다.
