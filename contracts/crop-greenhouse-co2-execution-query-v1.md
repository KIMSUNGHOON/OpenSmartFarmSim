# CO₂·일사 실행 진행 조회 — v1

Status: functional35 accepted; shared WSL capacity and new user activation pending.
[전체 기능 수용](../research/crop-greenhouse-co2-execution-query-20261021.md)은 제어15/실제 DB18/독립2=35검사를 확인했다.
source2f8b5e9/CI39533373500의24와 source3eb99bd/CI39534107848의11은 서로 같은324지문이며,
수용 시 현재 파일과도 같았다. 원 UTC/최초 시각·권리/파일·DB fence·조회31계측0/정리를 대사했다.
[사전 증거](../research/artifacts/crop-greenhouse-co2-execution-query-preflight-20261021.json)와
[첫 기록 필드 누락/수정](../research/artifacts/crop-greenhouse-co2-execution-query-evidence-fix-20261021.json)은 보존한다.
다음은 [확정 구간 원 조회](crop-greenhouse-co2-prefix-v1.md)이며 HTTP/runtime·웹/사용자 적용은 후속이다.
2026-10-21. native Codex CLI `gpt-6.1-sol / xhigh`에서 검토하며 재귀 CLI를 실행하지 않는다.
선행은 [실행 핵심](crop-greenhouse-co2-execution-core-v1.md)의 worker/독립 소비자 기능 수용이다.
[Solar 조회](crop-greenhouse-solar-execution-query-v1.md)의 읽기 경계와 기존 jobs를 재사용한다.

`Co2ExecutionQuery(checkpoint_store,result_store)`는 같은 jobs/server/admission/binding의 정확한
CO₂ checkpoint/result 타입과 현재 code/역할/포인터를 요구한다. 현재 계정·농장/입력·자료 권리를
metadata와 기존 읽기 범위로 확인한다. create/execute/write 범위를 조회에 요구하지 않는다.
조회는 수치 계산·복원·checkpoint 확인·작업 접수/임대·결과 쓰기를 실행하지 않는다.

## 응답과 현재성

닫힌 `joint-co2-solar-execution-query-v1` 응답은16KiB 이하이며 다음을 제공한다.

- 기존 공개 job 상태·cancel_requested·DB에서 얻은 관측 UTC인 observed_at.
- checkpoint_status none/current/unavailable. current일 때 원 HEAD/proof/artifact/provenance,
  계산 걸음/건수, 원 computed_through_utc와 최초 DB checkpoint_recorded_at.
- 현재 확인 이력과 일치하는 정상/수치 hold의 원 result ID·농장 참조·status/provenance.
- `synthetic_joint_co2_solar_math_only`, G0–G4 not_assessed와 명시 false 승인 표지.

입력/원천/권리 판본은 각각 `joint-co2-solar-execution-input-v1`, `joint-co2-solar-input-source-v1`,
`joint-co2-solar-input-rights-v1`이다. result ID는 `joint-co2-solar-result-v1`만 허용한다.
원4099 checkpoint 사건 한도를 유지한다. 다른 tenant/stage/입력 판본·없는 작업은 None이며,
다른 판본을 CO₂ 이력으로 파싱하지 않는다. 토큰/임대 자격·원 입력/매개변수·경로·권리 원문은 반환하지 않는다.

읽기 전용 repeatable-read에서 job/최신 확인 사건/link/publication/outcome/terminal 묶음을 검사한다.
서명 custody의 현재 HEAD/progress와 DB 확인 사건이 같아야 한다. 미기동은 none, 잠긴 파일이나
DB가 아직 확인하지 않은 HEAD는 unavailable이다. 계산된 생장 시각과 조회 관측 시각을 구분하며
임의 진행률을 생성하지 않는다. normal publication1·수치 hold publication0과 원 결과/이력을 대사한다.

현재 권리·입력/서명·승인 표지/판본이 잘못되면 Hold다. 별도 읽기 거래의 DB 묶음/결과 재검사,
잠금을 해제한 사이의 directory descriptor/inode·HEAD/서명 ancestry 확인과 직렬화 뒤 현재성 검사를
유지한다. 유효한 계산 전진·묶음 변경이나 응답 중 잠금 경합이면 Pending이며 부분 응답은 반환하지 않는다.

## 수용 기준

1. 순수 DTO에서 잘못된 판본/범위·정수 bool/건수·결과 family·승인 표지/추가 필드를 거부한다.
2. 실제 SCRAM의 queued/canceled/미확정/확정·heartbeat/재시도·최초 UTC, 정상/hold 원 결과·busy lock을 확인한다.
3. 읽기 범위/현재·늦은 철회, 잘못 추가된 불변 checkpoint 사건, 반환된 bundle fault, 응답 중 DB/HEAD/
   directory 변경에서 올바른 Hold/Pending·쓰기/수치 호출0과 원 데이터/현재 상태를 검증한다.
   시험 actor의 별도 상태 변경은 query의 SQL0 계측과 구분한다.
4. 독립 fresh 같은 DB/키/파일에서 observed_at만 제외한 원 DTO·최초 확인 UTC를 대사하고,
   철회·조회 계산/SQL/작업 변경0·소유 schema/role/process/passfile/temp/FD 정리를 확인한다.
   기존 원 자료/두 미리보기와 공통 자원 기준은 실행 핵심 계약을 따른다.

순수 DTO는 HTTP 경로를 설치하지 않는다. 이후 보호 접수/진행/취소 HTTP·명시 runtime→typed web→
같은 UTC3D→WSL/사용자 적용을 별도 수용한다. 전체 작기/자원/경제·실제 CLI 종단 간·농장 검증/
G0–G4/실제 품종 예측·추천은 기존 상위 작업의 후속이다.
