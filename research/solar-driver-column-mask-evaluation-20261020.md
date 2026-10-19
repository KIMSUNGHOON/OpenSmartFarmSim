# 호출자별 SQL 시간과 native 컬럼 predicate 평가 — 2026-10-20 KST

[기계 증거](artifacts/solar-driver-column-mask-evaluation-20261020.json) · [선행 실행 계획](solar-role-matrix-plan-observation-20261020.md).

## 원 계산 구간의 실제 관측

원 CASE6/input64/output0..64/8/chunk1의44까지 준비하고45번째 before→private advance→confirm 한 구간을 관측했다. Connection.execute 코드는 바꾸지 않고 PEP669 start/return과 정확한 code로 거른 global unwind를 사용했다. [Python 공식 문서](https://docs.python.org/3.12/library/sys.monitoring.html)에 맞춰 event/콜백을 해제하고 tool ID를 반환했다. 초기 로컬 unwind 등록은 CPython이 거절했으며 fixture 전에 global/code filter로 수정해 반환/오류 probe를 확인했다.

|경로|관측 초|
|---|---:|
|before|0.645372066|
|private advance|3.986888560|
|independent confirm|3.743109131|
|구간 전체|8.375369757|
|그중 Connection.execute 구간|3.494792239|
|그중 runtime_roles|2.280158393|

runtime_roles4,095회, 원천 SELECT2,280회의 경과0.497616397초를 포함해 current15/SQL9,929/role273/source2,280을 대사했다. SQL 매개변수·행·cursor 값은 수집하지 않았다. 동시에 활성 execute는1개이며 원 bytes/counts/UTC90.123456초와 계산step1/start0/CLI0을 보존했다. execute 시간에는 driver/변환/서버/대기가 섞인다. 관측 밖에는 연결·commit 등 다른 DB 동작도 있으므로 이를 순수 서버 시간이나 DB 전체 시간으로 표시하지 않는다.

## native 컬럼 mask: 한정된 동등성

PostgreSQL16.15 공식 [acl.c](https://github.com/postgres/postgres/blob/REL_16_15/src/backend/utils/adt/acl.c)와 [aclchk.c](https://github.com/postgres/postgres/blob/REL_16_15/src/backend/catalog/aclchk.c)의 실제 source SHA를 기록했다. native has_any_column_privilege는 table 권한 뒤 직접 column 권한을 검사하며, 쉼표 권한 목록은 비트 mask의 합집합이다. 이에 따라 expected=False에서는 일반/GRANT OPTION을 한 번의 native ANY 검사로 묶고, expected=True에서는 이미 확인한 table 권한과 GRANT OPTION을 이용하는 축약식을 검토했다.

실제 SCRAM/READ ONLY에서 baseline·request column SELECT·column UPDATE+grant·table SELECT·table UPDATE+grant·authority column SELECT+grant·PUBLIC column INSERT의7상태/112 role-privilege row/224 expected boolean case를 대사했다. 같은 column SQL 원/후보의 정상/hold와 원 auditor의 각 복원을 확인했다.

to_regprocedure EXECUTE를 회수하면 원 native 검사는 False지만 새 함수 식별 guard는42501을 내는 실제 반례가 있었다. 함수 식별자를 regprocedure literal cast/qualified equality로 비교하는 대안은 그 상태에서도 원 결과를 보존했다. native has_any_column EXECUTE 회수는 양쪽42501이며, project-first foreign 함수는 guard=False로 원 predicate를 사용해 동일 hold였다. 최종 direct 비교는9상태다. 임시 권한·함수 복원/원 감사 성공을 확인했다. 전체 operator/준비된 plan/현재·늦은 변경/HTTP 통합과 native kernel의 일반 동등성 수용은 아니다.

## 실제 비용: 기준 미달로 후보 제외

원 table/column statement 분리·params·현재 검사는 유지했다. PostgreSQL160015에서 column SQL 한 인자만 바꾸는 사설 후보를 원42..45 ABBA 한 번 비교했다. guard가 SQL에 포함되며 양 후보 구간 각각273회 실행했다. caller map/current 순서·원 bytes/counts/UTC84/86/88/90.123456초·current15/SQL9,929/role273/source2,280을 보존했다.

|순서|단계|경로|실측 초|
|---|---:|---|---:|
|A|42|원|8.126155100|
|B|43|후보|8.194141786|
|B|44|후보|8.139790187|
|A|45|원|8.353361515|

평균 감소0.883428%, 짝별−0.836640%/+2.556711%로 사전 평균2%/양짝 개선에 미달했다. **후보 미채택·제품 app 유지**다. 비용 기준 미달이므로 전체 operator/prepare/오류 closure·제품 구현/관련 회귀로 확대하지 않았다. v1 비용 시험은 복사된 이전 배열 hook의 없는 bind 속성 때문에 후보 측정 전에 실패했다. 유효한 ABBA packet이 없어 제외했고, 해당 fixture 조립 한 줄을 제거한 v2만 최종 비용1이다. 초기 native v1도 최종 경계1에 더하지 않는다.

## 검증과 다음 경계

최종 driver1/경계1/비용1의 guard는125.360424/16.548727/146.971106초였다. 최대 합1,052,299,264/단일144,003,072bytes·FD4→4·5root/원본2,148/두 frozen source·자산·소유 PG/비좀비/임시/passfile0·fixture schema/role0을 확인했다. 원512MiB/PID·합1GiB·연구600초와 실제 actor360초 조건을 유지했다. 기존 app261/d477b74b…/수용82는 이전 범위이며 전체 backend/browser/원64 CI는 재실행하지 않았다.

다음은 checkpoint confirm의 progress→snapshot→progress 소비와 파일 검증 소유권 검토다. 기존 별도 cProfile의 confirm에는46commit full load3회(307.709/308.562/301.709ms)가 기록되어 있다. 새 PEP669 시간과 합산하지 않는다. 실제 _snapshot은 _load의 head/digest를 사용하고 parsed data를 버린다. 각 읽기의 HEAD/proof/원 파일·오류 검증과 최종 progress equality의 역할을 대조한 뒤, 같은 현재 검증을 보존할 수 있는 작은 경계를 정한다. 검증 생략/권리 cache/예산 변경·새 CI를 먼저 도입하지 않는다.

원 정상64→독립 hold→HTTP취소→계산 중WebGL→WSL 적용과 실제 품종 계수·권리 확인 원자료·독립 현장/미래 작기는 남는다. 새 Solar 미배포·실제 농장 Run0·G0–G4 보류·전체 완료일 미정·goal active다. native CLI gpt-6.1-sol/xhigh 실제 문맥·소스/출력/종료 SHA를 묶었고 재귀 CLI/하위 agent0이다.

## 사용자 상태 게시

[게시 영수증](artifacts/solar-driver-column-status-publication-20261020.json): 기존5173/5174가 같은 최신 JSON·HTTP200/no-store를 제공했다. frozen HTML/환기2,173/5root/원본2,148·FD4→4·소유 잔여0을 보존했다. guard1.397370초·최대 합947,367,936bytes다. UI code/DOM/WebGL·새 모델 배포·원64 CI는 재실행하지 않았다.
