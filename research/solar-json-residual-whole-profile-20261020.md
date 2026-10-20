# 실제 계산 구간의 남은 JSON 비용 — 2026-10-20 KST

[기계 증거](artifacts/solar-json-residual-whole-profile-20261020.json) · [앞선 비용 미수용](solar-json-current-state-reference-guard-20261020.md).

9a82303과 같은 연구 source에서 원42/후보43단계의 `before → advance → confirm` 전체를 cProfile로 관측했다. 원 CASE6/input64/output0..64/8·chunk1을 유지했고, 원41단계 이력을 준비한 뒤 실제 worker 경로를 사용했다. 후보는 소유 시험에서 storage loader만 교체했다. 이 한 검사는 **새 성능 비교나 원64 완주 수용이 아니다**. 유효한 앞선 ABBA를 반복하지 않았다.

| 관측 항목 | 원42 | 후보43 |
| --- | ---: | ---: |
| 계측 중 전체 초 | 12.968670440 | 15.171197479 |
| binding current 호출 | 15 | 15 |
| SQL execute | 9,929 | 9,929 |
| role / 원천 SQL | 273 / 2,280 | 273 / 2,280 |
| 저장 load | 5 | 5 |

두 구간에서 원 checkpoint bytes/counts/UTC와 현재·SQL 호출 순서를 보존했다. 후보의5 scope에서 source pair218·fallback0·1MiB/폐기를 확인했다. DB의 역할/schema0·FD4→4·소유 잔여0이다. guard156.246239초·최대 합 RSS1,060,970,496bytes/1GiB·단일145,444,864bytes/512MiB, 원5root/2,148·두 frozen UI source/자산을 보존했다.

## 실제 호출 위치

후보의 `_ready`9,027회/cumulative1.852170초, Legacy `current`9,027회/1.821609초, JSON `current`9,032회/own0.808668초·cumulative1.345564초를 관측했다. 조립 `_guard_assembly`6,862회/1.600270초의 호출자는 사설 `_records`2,976회·`prepare_commit`2,924회와 기존 조립 경계다. **이 중첩 시간들을 합산하지 않는다.**

원/후보의 Psycopg `wait`는 각각10,478회/own2.7269·2.7276초다. JSON encoder `iterencode`는16,390/16,670회·own1.6049/1.4579초다. 이 숫자는 profiler 비용과 서로 다른 인접 원 단계를 포함한다. 차이를 개선율·인과 효과로 해석하지 않는다. 기존 실제 ABBA의 평균−2.252640% 판정은 그대로다.

후보 상태 비교의 원 `_JSONReferences.current`는 모듈의 각 항목마다 문자열 검사와 반복 사전 조회를 수행한다. Legacy 비교도 각 이름에서 globals/builtins를 다시 읽고 builtin fallback을 먼저 계산한다. 이는 원 감시나 관측을 삭제하지 않고 줄일 수 있는 다음 작은 표현 경계다. 새 입력/권리/HEAD/proof cache나 관측 축소는 선택하지 않는다.

## 다음 한 단계

`crop-solar-json-guard-dictionary-lookup`: 승인한 참조를 유지하며 위 두 조회 루프의 반복 작업만 줄인다. 일반적인 정확한 문자열 키를 비교하고, 예상 형식이 아닌 모듈 키는 원 전체 stamp로 대조한다. 최초 JSON/pristine 승인·변경 중 캡처 거부·현재 모든 binding·mutable/default/closure/builtin/실행 한도·관측 위치를 유지한다.

원 oracle와 늦은 변경·특수 모듈 키·원 fallback/오류/수명을 대조하고 기존173검사를 두 Python판에서 확인한다. 이후 최종 변경 source의 원 전체 ABBA 평균2% 이상/양짝 개선과 실제 현재/권리/원 IO·정리가 필요하다. 이전 유효 timing 시험을 유리한 값까지 반복하지 않는다.

제품 app261개는 유지했다. 기존173·전체 backend/browser·새 CI·원64·WebGL은 이번에 재실행하지 않았다. 실제 농장 Run0·G0–G4/미래 생산·마진·최적 추천·전체 완료일은 보류/미정이며 goal active다. native CLI gpt-6.1-sol/xhigh 문맥·source/출력 SHA를 기록했다. 후속 순서는 제품 연결/회귀→원 독립 정상64→hold/취소→계산 중WebGL→WSL 적용이다.
