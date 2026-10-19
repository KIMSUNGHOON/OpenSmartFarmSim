# 원 권한 matrix 실행 계획 관측 — 2026-10-20 KST

[기계 증거](artifacts/solar-role-matrix-plan-observation-20261020.json) · [배열 후보 미채택](solar-role-array-binding-evaluation-20261020.md) · [이전 실제 quantum profile](solar-worker-late-quantum-observation-20261020.md).

## 실제 관측

원 auditor가 사용한 table/column SQL과 bound 인자를 소유 합성 SCRAM fixture에서 수집했다. 실제 PostgreSQL16.15의 READ ONLY transaction에서 각각 정상 SELECT→EXPLAIN ANALYZE/BUFFERS/FORMAT JSON/TIMING OFF→정상 SELECT를 실행했다. 두 statement는 합치지 않았다. SQL/인자 SHA·원 auditor 전후 정상 결과와 rollback을 확인했다. 새 함수/DDL/권한 cache·제품 변경은0이다.

[공식 EXPLAIN](https://www.postgresql.org/docs/16/sql-explain.html)에 따라 ANALYZE는 실제 문장을 실행하고 계측 비용을 추가한다. TIMING OFF여도 전체 statement 시간은 측정한다. 아래는 이번 소유 데이터 한 관측이며 일반 처리량/호스팅 원인이나 원64 개선율이 아니다.

|원 statement|planning ms|execution ms|검사 조합|expected rows|join|
|---|---:|---:|---:|---:|---|
|table|0.063|0.742|728|62|Hash Left Join|
|column|0.193|1.286|416|62|Hash Left Join|

4개 role·26개 table과7/4개 privilege의 조합이며, 해시 batch1·peak15kB다. 두 최상위 관측의 shared/local/temp block은0이다. 함수 내부 전체 cache/IO가 없다는 증거로 확대하지 않는다. 중첩 노드의 buffers/시간을 합산하지 않았다. 원 정상 응답은 두 경우 모두 행 없음이었다. 이번 plan에서 예상 행 수와 실제 조합은 맞고, 해시 spill/예상 밖의 조인 확대가 확인되지 않았다. 따라서 이 관측만으로 SQL 재작성을 선택하지 않는다.

## 검증·범위

집중1검사 통과·guard16.305423초·최대 단일144,003,072/합1,030,746,112bytes·FD4→4·5root/원본2,148/두 frozen source·자산/소유 정리 보존, fixture schema/role0이다. 같은 앱의 이전82·전체 backend/browser·원 정상64는 재실행하지 않았다. native CLI gpt-6.1-sol/xhigh·실제 소스/출력/종료 SHA를 묶었고 재귀 CLI/하위 agent0이다.

## 다음 한 단계

기존 profile은 Connection.wait exclusive2.2959초/inclusive4.1004초와 driver phase 합만 제공한다. 서로 중첩되므로 합산하지 않는다. 다음은 원 CASE6/input64/output0..64/8/chunk1의45번째 `_before→private advance→confirm` 한 구간에서 **SQL 호출자·phase별 driver 경과 시간**을 관측하는 것이다. 원 Connection.execute 코드·SQL/인자/statement/현재 검사 순서를 유지하고 PEP669 start/return/unwind callback에서 매개변수·행·cursor 값은 읽거나 저장하지 않는다. 원 current15/SQL9,929/role273/source2,280·bytes/counts/UTC·계측 해제/원본/5root/상한/정리가 수용 기준이다. 이 시간에는 driver/변환/대기가 함께 포함되므로 순수 서버/네트워크 시간으로 표시하지 않는다.

동일 fixture의 이전 전체 guard126.702480초/이번 ABBA148.725738초를 근거로 집중 실행1회 약2–3분을 예상한다. 설계·후속 구현/회귀·호스팅64·브라우저·외부 자료 확보 시간은 포함하지 않는다. 자원 상한이나 사실상 오류가 있으면 근거를 기록하며 서비스 중단/입력 축소/원 예산 확대 없이 대응한다.

최종 제품 경로의 원 정상64→독립 hold→HTTP취소→계산 중WebGL→WSL 적용과 실제 품종/권리 확인 원자료·독립 작기 자료는 남아 있다. 새 Solar 미배포·실제 농장 Run0·G0–G4 보류·전체 완료일 미정·goal active다.

## 사용자 상태 게시

[게시 영수증](artifacts/solar-role-array-plan-status-publication-20261020.json): 기존5173/5174는 동일 최신 JSON·HTTP200/no-store이고 원 frozen HTML/환기2,173파일·5root/원본2,148을 보존했다. guard1.366687초·합953,602,048bytes·FD4→4·소유 잔여0이다. JSON 상태만 바꿨으며 DOM/WebGL/새 모델 배포·원64 CI는 실행하지 않았다.

기존 CI도 재확인했다. 최신 진단39328214424와 원 정상39321398376은 completed/failure 그대로다. 이번 app 변경과 새 CI 접수는0이며 기존 미완료를 해소했다고 표시하지 않는다.
