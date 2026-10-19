# 권한 배열 표현 평가: 실제 비용 기준 미달 — 2026-10-20 KST

[기계 증거](artifacts/solar-role-array-binding-evaluation-20261020.json) · [선행 snapshot 반례](solar-role-matrix-conditional-review-20261020.md).

## 판단

제한된 typed-list 후보를 실제 SCRAM/PostgreSQL에서 검토했다. 원 SQL·placeholder·두 statement 순서와 권한 함수는 유지했다. 최종 경계3검사와 별도 실제 worker quantum1검사는 통과했지만 **평균 0.572706% 느려 후보를 미채택**했다. 사전 기준인 평균2% 이상 감소/양쪽 짝 개선에 미달한다. 제품 app은 변경하지 않았고 같은 후보를 타이밍 선택 재시도하지 않는다.

전체 의미 보존 관문을 수용하기 전 수행한 사설 비용 적격성 검토다. 비용 미달로 확대 검증을 중단했으며 원 구현 수용 조건은 미충족 상태로 남긴다.

## 실제 검사 범위

- name[]/oid[]/text[]의 타입·값·순서·중복·빈 배열과 uint32 최대 OID를 원 변환과 실제 왕복 대사했다. OID 후보는 client int8[]를 원 SQL의 oid[]로 변환했다.
- 지원하지 않는 None/잘못된 값과 변환기·adapter·코드·전역·전용 dumper·encoding 변경에서는 원 인자 객체를 반환했다. 변경된 list/string/int dumper와 원 list 코드의 RuntimeError 메시지는 실제 실행으로 양쪽을 대사했다.
- import 전 바뀐 dump 코드/하위 클래스 hook/전역을 기본으로 학습하지 않았다. 기존 scalar/byOID mapping은 덮어쓰지 않았다.

[공식 adaptation 문서](https://www.psycopg.org/psycopg3/docs/advanced/adapt.html)는 연결·커서 설정의 상속과 원소 기반 dumper 선택을 설명한다. 문서는3.3.7.dev1이고 실제 설치는3.3.6이므로 설치 source SHA와 실제 동작을 기준으로 했다. 전체 NULL/잘못된 값의 서버 오류·custom cursor/소유권/수명·모든 전역 변경은 미검증이다. 이 세 검사를 전체 보안/동등성 수용으로 확대하지 않는다.

## 실제 계산 비용

원 CASE6/input64/output0..64/8/chunk1을 유지했다. 합성 소유 fixture에서41까지 준비한 뒤 `_before → private advance(budget1) → independent confirm`의42..45를 ABBA로 한 번 비교했다. 준비와 module import는 측정 구간 밖이며 각 bind의 현재 보호 검사·값 확인·복사는 구간 안이다.

|순서|단계|경로|실측 초|typed bind|
|---|---:|---|---:|---:|
|A|42|원 경로|8.174827549|0|
|B|43|후보|8.231465793|546|
|B|44|후보|8.425877837|546|
|A|45|원 경로|8.387661633|0|

감소율은 첫 짝−0.692837%, 둘째−0.455624%, 합산 평균−0.572706%다. 후보 fallback0이며 실제 원 bytes/counts/UTC84·86·88·90.123456초, current15/SQL9,929/role273/source2,280과 SQL caller map·현재 검사 순서를 대사했다. SQL 계수는 Connection.execute 코드를 바꾸지 않는 [Python PEP669 monitoring](https://docs.python.org/3.12/library/sys.monitoring.html)을 두 경로에 동일 적용했다. local event/콜백을 해제한 뒤 tool ID 반환까지 확인했다. 이는 계측 없는 원 정상64 처리량이나 호스팅 개선율이 아니다.

## 자원·재현 기록

최종 경계3은 guard30.481249초·최대 합1,037,565,952bytes, 비용1은148.725738초·합1,048,739,840bytes였다. 양쪽 단일 PID 최대144,003,072bytes·FD4→4·5root/원본2,148/두 frozen source·자산 보존·소유 PG/비좀비/임시/passfile0과 fixture schema/role0을 확인했다. 512MiB/PID·합1GiB·원600초 연구 guard를 유지했다. 건강한 서비스를 중단하지 않았다.

예상 RED1, 초기 collection의 module alias/pin 오류, 없는 adapter 속성 준비 오류, v3의 테스트 mapping 형태 오류, v4의 테스트 closure 코드 교체 오류를 별도 기록했다. earlier green1과 중간 부분 통과는 최종3+1에 더하지 않는다. 제품 관련 회귀/전체 backend/browser/원 독립64는 재실행하지 않았다. 기존 app261/d477b74b…/수용82는 이전 범위로 유지한다.

## 다음 수용 경계

[후속 실행 계획1](solar-role-matrix-plan-observation-20261020.md)을 실제 관측했다. 당시 다음 경계는 원 table/column SQL 각각의 실행 계획 관측이었다. 같은 소유 fixture의 원 인자·현재 auditor로 정상 상태를 확인하고, READ ONLY에서 원 두 SQL 각각의 EXPLAIN ANALYZE/BUFFERS/TIMING OFF를 한 번 수집한다. 노드·loops·rows·buffer/temp·planning/execution을 기록하되 중첩 비용을 합산하거나 원64 개선율로 환산하지 않는다. 새 DDL/자료·권한 cache·SQL 결합·예산 변경 없이 다음 구현 후보의 근거만 고른다.

원 정상64→독립 hold→HTTP취소→계산 중WebGL→WSL 적용은 남아 있다. 실제 품종 계수·권리 확인 원자료·독립 현장/미래 작기도 외부 의존성이다. 새 Solar 미배포·실제 농장 Run0·G0–G4 보류·전체 완료일 미정·goal active다. native CLI gpt-6.1-sol/xhigh 문맥·실제 출력/소스/종료 해시를 기록했고 재귀 CLI/하위 에이전트는0이다.
