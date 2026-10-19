# 현재 권한 감사 순서·허용 행렬 후보 평가 — 2026-10-20 KST

[기계 증거](artifacts/solar-role-audit-sequence-20261020.json) · [선행 독립 정상 실패/현재 비용](solar-current-guard-native-normal-20261020.md).

## 실제 순서 관측

제품 app261파일은8b5afe5 원 bytes다. 기존 실제 SCRAM fixture의 한 worker quantum에서 원 감사·SQL·결과를 그대로 전달하며 순서를 관측했다. **감사315/SQL11,723/원천2,736/쓰기3·원 checkpoint counts/UTC04.123456Z**를 확인했다. 비감사 SQL6,998개와 발견한 권한 callback4종의46,828호출을 barrier로 기록했다. callback은 principal·입력 권리·review resolver·input resolver다. 원문 SQL/인자/행은 기록하지 않았다.

기록된 barrier가 사이에 없는 같은 연결/정책·로그인·관측한 transaction status의 연속 감사는 **4쌍**이었다. client read_only 속성의 일치는 실제 서버 read-only 상태의 승인이 아니다. 위치는 `MarketCandidateStore._reference_guard`의 감사 후 `read_scope` 종료 감사다. source에서도 그 사이에는 반환과 조건 분기가 있다. 이 관측은 모든 Python 부작용을 포괄하거나 감사 삭제를 승인하지 않는다. 감사315회의 전체 생략·권한 결과 cache를 정당화하지 않으며, 이4쌍을 제거하는 제품 변경도 하지 않았다.

| 현재 직접 감사 호출자 | 횟수 |
|---|---:|
| JobStore.connect |111|
| ThermalRunStore.connect |72|
| connect_market |36|
| MarketSourceStore.read_scope 종료 |36|
| MarketCandidateStore._reference_guard |52|
| MarketCandidateStore.read_scope 진입/종료 |4/4|

trace는2,154,328bytes로 사설 보관했다. 선택 callback/SQL 경계·동일 scope의 제한된 관측이며 profiler/관찰 비용이 포함된다. 감사 시간의 합이나4쌍을 처리량 개선율로 환산하지 않는다.

## 다른 작은 후보1: 허용 행렬의 전달 표현 — 미채택

원 Python `_allowed`에서 만든 `(role, OID, privilege)` 전체를 그대로 출발점으로 사용했다. 사설 후보는 이를 `(role, privilege) → OID[]`로 묶어, 상수 SQL 조건과 bound parameter로 expected membership을 표현한다. 실제 `has_table_privilege`/`has_any_column_privilege`·grant option·별도 table/column 검사와 나머지 감사 SQL은 유지한다. [PostgreSQL 권한 함수](https://www.postgresql.org/docs/16/functions-info.html#FUNCTIONS-INFO-ACCESS-TABLE), [ANY 비교 의미](https://www.postgresql.org/docs/16/functions-comparisons.html#FUNCTIONS-COMPARISONS-ANY-SOME)를 참고했다. 기존 기각15→4 SQL/pipeline/direct ACL 후보와 다른 전달 표현의 시험이다.

| ABBA 짝 | 기존 wall초 | 후보 wall초 | 감소율 |
|---|---:|---:|---:|
| 첫 짝 |8.024152|7.937739|1.0769%|
| 둘째 짝 |8.017596|7.871131|1.8268%|

각 quantum에서 감사315·SQL11,723·원천2,736과 원 counts/UTC04/06/08/10.123456Z를 유지했다. 평균 **1.4517%**로 사전2% 기준을 충족하지 못했다. 후보는 미채택이며 patch는 복원했다. 추가 negative grant/보안 회귀·제품 구현·새 독립64는 수행하지 않았다. 정상 fixture의 비교를 완전한 보안 동등성이나 처리량 수용으로 확대하지 않는다. 같은 후보는 새 근거 없이 반복하지 않는다.

## 보존과 다음 한 단계

관측1+trial1의 고유2건은 자식0·guard45.121624/62.073638초였다. 단일/합 최대 RSS141,316,096/1,005,670,400bytes,5root/원본2,148·두 frozen source/자산·FD4→4/소유 PG·임시·passfile0을 확인했다. 이전64와 진단4를 새 검사로 합산하지 않았다. 실제 native CLI `gpt-6.1-sol` / `xhigh` 문맥/원행 SHA·실행/원 증거 SHA는 기계 증거에 결속했다. 재귀 CLI/하위 에이전트·제품 코드 변경·새 CI 접수는0회다.

다음은 `MarketSourceStore._model`의 반복 형식 해석을 현재 source/job/hash·권한 검사와 구분할 수 있는지 검토한다. 기존 [의존성 검토](market-current-reference-dependency-guard-20261019.md)의 모델/validator·현재성 반례와 실제 소비/가변성·코드/정규화 의존성을 먼저 대조해야 한다. getter·현재 SQL/검토·권리나 canonicality 검사를 생략하는 후보는 승인하지 않는다. 닫힌 작업 안에서 같은 원문에 대한 순수 작업을 특정하고 그 의존성을 보존할 수 있을 때만 사설 비용 비교를 진행한다. 이전 getter agreement의 미채택을 되돌리는 작업이 아니다.

원 독립64는 CI39280701330의41/64 실패로 미수용이다. 정상→독립 hold→실제 HTTP취소→계산 중WebGL→WSL 사용자 적용 순서, 새 Solar 미배포·농장 Run0·실제 자료/G0–G4와 전체 완료일 미정·goal active를 유지한다.

최종 게시 `focused-solar-role-audit-sequence-status-v1`은 자식0·guard1.360926초였다. 관련 링크2,609개·기존64/선행 실패 증거와 app261 원 hash·원 actor를 대사했다. 두 HTTP200/동일bytes/no-store·frozen HTML/환기2,173파일·원본2,148/5root/FD4→4·소유 정리를 확인했다. 진행 기록은2026-10-19T16:56:25.903494Z이며 UI 코드·DOM/WebGL을 다시 검증한 것은 아니다.
