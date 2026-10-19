# 권한 matrix 조건부 평가: snapshot 반례로 제외 — 2026-10-20 KST

[기계 증거](artifacts/solar-role-matrix-conditional-review-20261020.json) · [이전4문장 반례](solar-role-tail-protocol-and-cursor-evaluation-20261020.md) · [선행 decoder 제외](solar-codec-dispatch-evaluation-20261020.md).

## 원 오류 순서: 한정된 정상/오류 사례 통과

원 runtime_roles의 table/column matrix 두 SELECT와 bound 인자를 그대로 CASE의 순서 있는 EXISTS로 감쌌다. 새 product SQL 함수/schema/서비스·권한 결과 cache는0이다. [공식 CASE](https://www.postgresql.org/docs/16/functions-conditional.html#FUNCTIONS-CASE)의 분기 평가 설명을 실제 소유 SCRAM/READ ONLY에서 대조했다. 문서가 언급한 planning-time 예외까지 일반적으로 해결했다고 판단하지 않았다.

첫1검사는 정상 기본 응답NULL, table 위반과 뒤 column 오류가 함께 있는 경우, 앞 위반 없이 뒤 오류만 있는 경우를 확인했다. 원4문장 일괄 실행의 실제 반례도 같은 fixture에서 재현했다.

| 조건 | 원 auditor | 조건부 두 matrix | 이전4문장 묶음 |
|---|---|---|---|
|table 위반·뒤 column SQL 오류|RolePolicyHold/table matrix·INTRANS·후속SELECT 성공|table reason·INTRANS·후속SELECT 성공|뒤 P0001·첫 fetch 전 실패·INERROR|
|table 정상·뒤 column SQL 오류|P0001·INERROR|P0001·INERROR|이미 앞 행에서 미동등 확인|

이 결과는 첫 오류 순서의 해당 사례만 확인한다. 전체 현재 권리/동시 변경/일반 planner 동등성이나 제품 수용이 아니다.

## 동시 변경: 실제 statement snapshot 차이

[PostgreSQL READ COMMITTED](https://www.postgresql.org/docs/16/transaction-iso.html#XACT-READ-COMMITTED)는 연속 SELECT의 관측 시점이 다를 수 있다고 설명한다. [함수 volatility](https://www.postgresql.org/docs/16/xfunc-volatility.html)는 STABLE 함수가 호출한 query의 snapshot을 사용한다고 설명한다. C 함수 자체의 snapshot 관리까지 동일하다고 확대하지 않았다.

최종 두 번째1검사는 **명시적 project-first search_path와 소유 invoker 함수**를 사용했다. table 함수는 advisory barrier를 쓰므로 VOLATILE, column 함수는 원 native column 검사에 소유 jobs.updated_at flag를 읽는 STABLE이다. 실제 pg_proc의 v/s·prosecdef=False를 확인했다. 원 두 SQL/인자는 바꾸지 않았다. 각 모드에서 실제 pg_locks 대기를 관측한 뒤 별도 admin이 합성 fixture timestamp 변경을 commit하고 barrier를 해제했다. read-only reader가 각각의 원 SQL 또는 같은 CASE를 실행했다.

| 동일 동기화 조건 | 실제 반환 | transaction |
|---|---|---|
|원 두 statement|새 flag를 보는 뒤 column 검사에서 RolePolicyHold/runtime_column_grant_matrix|INTRANS|
|합친 CASE statement|처음 snapshot의 column predicate를 사용해 reason NULL|INTRANS|

원 경로가 보류한 조건에서 후보는 정상 값을 반환했다. **일반 동등성이 없으므로 조건부 결합 후보를 제외하고 비용 trial을 하지 않았다.** 기본 pg_catalog 함수/현재 runtime의 권한 취약점이나 원 hosted CI 시간 제한 원인으로 보고하지 않는다. 모든 실제 동시 GRANT 사례를 검사한 것도 아니다. 해당 일반 후보를 기각할 반례가 있으므로 추가 성능/제품 구현/전체 회귀로 진행하지 않았다.

## 복원·검증 범위

각 모드 전·후 및 최종 정리에서 UPDATE RETURNING으로 원 timestamp의 정확한 복원을 확인했다. 소유 함수/권한·advisory locks를 정리하고 원 auditor의 정상 결과를 대사했다. 최종 오류 순서1·snapshot 반례1만 고유2건이다. guard17.558807/17.337405초·최종 최대 단일120,627,200/합583,577,600bytes·FD4→4·5root/원본2,148/두 frozen source/자산·소유 PG/비좀비/임시/passfile0을 확인했다. 기존82/전체 backend/browser/원64는 재실행하지 않았다. app261/d477b74b…는 유지했다.

초기 private 생성의 따옴표 SyntaxError 두 건을 보존했다. 첫 실패 뒤 shell이 이전 status publisher를 실행한 order-v1은 실제 종료0·보존/정리를 확인했지만 semantic test에서 제외했다. 이후 준비 단계는 실패 시 실행을 멈췄다. snapshot-v1은 없는 attempt column, v2는 claim closure 제약이 금지한 attempt_count 변경으로 실패했다. DB 제약을 유지한 채 실제 updated_at만 사용하는 후속으로 고쳤다. v3는 barrier를 STABLE로 선언한 예비 관측이라 제외했고, v4의 올바른 VOLATILE/STABLE 관측도 v5의 정확한 복원 검사로 대체했다. 모든 초기 소유 fixture 종료/잔여0을 별도 보존하며 최종2에 더하지 않는다.

## 다음 작은 경계

같은 SQL/두 statement 경계를 유지하는 **권한 matrix bound-array 표현 검토**다. 기존 late profile의 array dump5,853회·원소 판별8,916회는 관측 근거이며 개선율이 아니다. 설치 Psycopg3.3.6 array.py의 원소 추론/변환/인용과 [공식 list adaptation](https://www.psycopg.org/psycopg3/docs/basic/adapt.html#lists-adaptation)·[PostgreSQL array syntax](https://www.postgresql.org/docs/16/arrays.html#ARRAYS-IO)를 대조했다. 웹 Psycopg 문서는3.3.7.dev1이므로 설치 source/lock을 별도로 해시했다. 이 자료는 아직 새 serializer 승인 근거가 아니다.

수용 조건은 실제 name[]/oid[]/text[] roundtrip의 타입/값/순서/중복·empty/null/잘못된 입력·기존 오류, client encoding·기본/교체 dumper/adapter·코드/수명/소유권을 검증하는 것이다. 지원하지 못하거나 변경된 binding은 원 경로를 사용하고, 초기의 미승인 설정을 기본으로 학습해 생략하지 않는다. SQL/placeholder·원 권한 함수/statement 순서·현재 source/권리 검사를 유지한다. 가능할 때만 원 실제 worker quantum 평균2%/양짝 개선을 전체 guard 비용과 함께 비교한다. 권한/자료 결과 cache·SQL 문자열 삽입·새 schema/함수/서비스·원 actor/input/chunk/poll/retry360/RSS 변경은 없다. 최종 source의 관련 회귀와 정상64는 이후 별도 수용이다.

원 정상64→독립 hold→HTTP취소→계산 중WebGL→WSL 사용자 적용, 실제 농장 자료/독립 작기·G0–G4는 남는다. 새 Solar 미배포·실제 농장 Run0·전체 완료일 미정·goal active다. native CLI gpt-6.1-sol/xhigh의 실제 문맥·사전/소스/종료 해시를 기록했고 재귀 CLI/하위 에이전트는0이다.

## 사용자 상태 게시

[게시 증거](artifacts/solar-role-matrix-review-status-publication-20261020.json): 두5173/5174 HTTP200·동일 최신 상태/no-store·frozen HTML/환기2,173/5root/원본2,148·FD4→4·소유 잔여0을 확인했다. guard1.367823초·합488,210,432bytes다. UI code·browser DOM/WebGL·전체 backend·원 정상64는 재실행하지 않았다.
