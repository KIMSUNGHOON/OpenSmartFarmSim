# 현재 계산 조회의 검증 사실 묶음 v1

2026-10-09 KST. 실제 native Codex CLI `gpt-6.1-sol`/`xhigh` 판단, 재귀 CLI0.
선행 전체 부모의 실제 조회 비용은7.384–8.383초다.
변경 전 실제 cProfile에서 summary의 result verify/snapshot8회, sample64의9회,
sample64 DB 연결345회가 관측됐다. 전체 파일과 현재 권한을 캐시하지 않는다.

## 이번 작은 변경

core4: 이 계약, `backend/app/crop_cycle_calculation_result_read_context.py`,
`backend/app/crop_cycle_calculation_current_query.py`,
`backend/tests/test_crop_cycle_calculation_query_facts.py`.

`CalculationResultReadContext.facts()`는 같은 검증 문맥의 summary/context/identity를
독립 사본으로 만든 뒤 기존 `recheck()`를 한 번 수행해 반환한다.
개별 기존 속성과 page/close/실패의 계약은 유지한다. 원 증명·입력·artifact/모델과
서명 authority 코드는 바꾸지 않는다. 파일 metadata만으로 무결성을 대신하지 않는다.

현재 query가 세 개별 속성 대신 이 묶음을 사용한다. `_current`의 현재 farm/원 record/HMAC·
scope·권리/입력·trace 전후 검사와 reader.page의 실제 원 bytes/전체 재검사는 그대로 수행한다.
공개 응답 형식/64sample·8event/2MiB·서명 계보/합성 hold는 유지하며,
새 조회 code/dependency hash를 실제 identity에 기록한다. 새 gate/자료 채택은 없다.

## 수용 기준

1. 실제 정상/수치 hold 증명에서 기존 세 속성과 facts의 모든 값·단위/UTC/identity가 같다.
   사본 변조는 원 문맥·후속 응답을 바꾸지 않는다. facts 반환 전 전체 verify1회다.
2. input/HEAD/page/서명 authority 변경·반환 직전 변경을 거부하고 FD/cache를 닫는다.
   기존 현재 query의 철회·scope/tenant·늦은 행/입력/선언 변경 거부 시험을 유지한다.
3. 실제 전체 부모의 같은5요청/순서·원 record/페이지/UTC와 자원을 대사한다.
   실제 cProfile의 summary8→6/sample9→7, input proof16→12/18→14가 기준이며
   현재 farm 검사·DB 연결 횟수는 이 변경으로 줄이지 않는다.
4. 동일 조건의 변경 전후 실제 wall 비용이 잡음보다 개선되고 집중 회귀가 통과해야 유지한다.
   원 도구 종료0·실제 SCRAM·원본/source/기존 미리보기 보존·FD/소유 정리를 확인한다.
   단일512MiB/관측 합1GiB와300초 전체 부모 비용 측정 상한을 유지한다.

이 작은 변경만으로 전체 수확 writer/registry/API·3D나 UI U1/U3를 완료하지 않는다.
DB 연결 반복 비용은 별도이며 이후 실제 수확 실행의 작업 분해/예산으로 이어간다.
실제 품종/독립 농장 자료·G0–G4와 생산/경제·추천의 보류는 유지한다.
