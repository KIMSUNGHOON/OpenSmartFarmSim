# 현재 검증 비용 후보 3건 평가 — 2026-10-20 KST

[기계 증거](artifacts/solar-validation-cost-candidates-20261020.json) · [선행 감사 순서](solar-role-audit-sequence-20261020.md) · [원 독립64 실패](solar-current-guard-native-normal-20261020.md).

## 결과와 범위

제품 backend app261파일은 `8b5afe5` 원 bytes다. 기존 실제 SCRAM fixture의 같은 작업에서 후보마다 **기존→후보→후보→기존** 순서로 before→advance→confirm을 비교했다. 사전 기준은 평균 wall 감소2% 이상과 두 짝 모두 감소다. 각 quantum의 **SQL11,723/감사315/원천2,736·checkpoint counts/UTC04/06/08/10.123456Z**를 유지했다. 세 후보 모두 미채택이며 patch를 복원했다.

| 후보 | 기존 wall초, 두 구간 | 후보 wall초, 두 구간 | 평균 감소율 | 판단 |
|---|---|---|---:|---|
| 평면 경제 입력의 보호된 형식 변환 재사용 |7.887791 / 7.967006|9.040667 / 8.961247|−13.5424%|느려짐·미채택|
| 현재 연결 매개변수의 필요한 필드 투영 |7.814204 / 8.006772|7.705426 / 7.811860|1.9195%|2% 미달·미채택|
| 같은 SQL 안의 역할 이름→OID 해석 |7.901830 / 7.902079|7.834471 / 8.049894|−0.5091%|두 번째 짝 악화·미채택|

서로 다른 후보의 짝은 합산하지 않는다. 수치가 같은 정상 fixture를 확인한 비용 비교이며 완전한 보안 동등성, 독립 정상64 또는 실제 농장 검증의 수용이 아니다. 후보 전체 negative/security 회귀는 실행하지 않았다. 채택 기준 미달 뒤 같은 후보를 다시 실행해 더 좋은 수치를 고르지 않았다.

## 1. 평면 경제 입력의 변환

`MarketSourceStore._model`의 `OwnedEconomicRecord.model_validate_json`만 대상으로 삼았다. 중첩 목록이 없는 평면 값이며 현재 source/job/hash·principal/rights·모든 getter와 SQL, 매번 새로 수행하는 `model_dump`→canonical bytes/raw 비교는 유지했다. 모델/core schema/config·Python validator/code/globals·Decimal 상태를 매 호출 대조하고, 등록 연결 frame마다만 원문별 template을 보관하는 사설 후보였다. 반환 모델의 dict와 field set은 각각 새로 만들고 평면 불변 값만 공유하도록 제한했다.

후보 quantum마다 실제 호출2,016/검사2,016·frame4·miss180/hit1,836, fallback0이었다. 실제 재사용이 있었지만 의존성 대조 비용이 절감분보다 컸다. 기존 getter agreement의 미채택을 되돌린 것이 아니며, 이 정상 비용 관측만으로 순수성/모든 변경 반례가 증명된 것은 아니다. 제품 cache는 추가하지 않았다.

## 2. 현재 연결 필드

기존 CPU 표본의 Conninfo option 생성 비용과 설치된 Psycopg3.3.6 `_connection_info.py`를 대조했다. 사설 후보는 `_client`/`_shared_reader`에서 필요한7개 필드만 대상으로, native libpq180006의 compiled 기본값과 **매 호출 새로 읽은** `pgconn.info`를 비교했다. 현재 연결값을 보관하지 않았고, public method/native descriptor/default function의 identity/code가 달라지면 원 `get_parameters`로 돌아가도록 했다. 후보 quantum마다1,188회 native read/fallback0을 관측했다.

[Psycopg API](https://www.psycopg.org/psycopg3/docs/api/objects.html#psycopg.ConnectionInfo.get_parameters)와 [libpq의 compiled/default/현재 option 구분](https://www.postgresql.org/docs/18/libpq-connect.html)을 참고했다. 웹 Psycopg 문서는3.3.7.dev1이고 실제 설치는3.3.6이며, 설치 source/lock SHA는 기계 증거에 기록했다. native 기본값 투영과 fallback의 완전한 호환성을 승인하지 않았다. 두 짝 모두 빨랐으나 평균1.9195%로 기준 미달이어서 제품 helper/의존성/설정 변경은 없다.

## 3. 같은 현재 SQL의 역할 식별

원 `_allowed`의 전체 expected triples와15개 감사 SQL, 별도 table/column 검사, 실제 `has_table_privilege`/`has_any_column_privilege` 및 grant option 검사는 유지했다. 두 행렬 SQL 안에서만 `MATERIALIZED` CTE로 그 statement의 정책 역할 이름을 `regrole::oid`로 해석해 native 권한 함수에 전달했다. 이전 Python 질의에서 구한 OID나 권한 결과를 보관하지 않았다. 이전15→4 SQL/pipeline/direct ACL 또는 grouped expected-array 후보의 재시도가 아니다.

근거는 PostgreSQL16의 [유효 권한 함수 name/OID 인자](https://www.postgresql.org/docs/16/functions-info.html#FUNCTIONS-INFO-ACCESS-TABLE), [OID 별칭](https://www.postgresql.org/docs/16/datatype-oid.html), [CTE materialization](https://www.postgresql.org/docs/16/queries-with.html#QUERIES-WITH-CTE-MATERIALIZATION)이다. 문서만으로 동시 rename/drop/recreate 등의 동등성을 승인하지 않았다. 두 번째 짝이 느려졌고 평균도 악화되어 후보를 미채택했다. 별도 concurrency/negative suite나 제품 구현으로 진행하지 않았다.

## 보존과 다음 한 단계

고유 사설 trial3건은 모두 자식0·guard합187.770743초였다. 단일/합 RSS 최대141,316,096/1,013,350,400bytes·5root/원본2,148/두 frozen source·자산·FD4→4/소유 PG·임시·passfile0을 확인했다. 이전64/순서2/관측4를 새 검사 수에 더하지 않았다. 실제 native CLI `gpt-6.1-sol` / `xhigh` 문맥/원행 SHA, 사전 기준·probe·원 결과·source pin/종료 증거 SHA를 결속했다. 재귀 CLI/하위 에이전트·새 CI 접수·제품 변경은0이다. 웹 문서는 소프트웨어 동작의 참고 자료이며 농업/경제 자료 채택이나 권리/관문 승인이 아니다.

다음은 `SolarServerCustody._open`→`_Session.advance`의 **기존 intent 재개 경로**를 작은 범위로 검토한다. 현재 `_open`의 첫 full current 확인 뒤 `_immutable`/directory open을 거쳐 `advance`의 첫 full guard가 다시 실행된다. 아직 중복으로 판정하지 않았다. 기존 intent에서 첫 guard 이전에 발생할 수 있는 실제 파일 생성/쓰기·resolver/callback과 잠금/오류 경계를 먼저 대조한다. 쓰기 전 검증, 새 intent/default `_open`/worker adoption과 마지막 게시·현재성 검사를 보존할 수 있다는 근거가 있을 때만 호출 소유권 후보의 계약/사설 시험을 준비한다. 현재 검사를 단순히 지우거나 authority 결과를 cache하는 변경은 승인하지 않는다. 관련 작업 분해/수용 기준은 [계획](../tasks/plan.md)에 연결했다.

원 CI39280701330은 최종 실패·저장41/64이며 현재 실행 중이 아니다. 독립 정상64→독립 hold→실제 HTTP취소→계산 중WebGL→WSL 용량/사용자 적용 순서를 유지한다. 새 Solar 미배포·농장 Run0·실제 자료/독립 검증/G0–G4와 전체 완료일 미정·goal active다. 이번 guard합은 연구 시험의 실제 소요이며 전체 완료 일정으로 환산하지 않는다.

최종 게시 `focused-solar-validation-cost-candidates-status-v1`는 자식0·guard1.362652초였다. 관련 링크2,612개·선행 원 증거/현재 app hash와 원 actor를 대사했다. 두 HTTP200/동일bytes/no-store·frozen HTML/환기2,173파일·원본2,148/5root/FD4→4/소유 정리를 확인했다. 진행 기록은2026-10-19T17:25:41.462537Z이며 UI 코드·DOM/WebGL을 다시 검증한 것은 아니다.
