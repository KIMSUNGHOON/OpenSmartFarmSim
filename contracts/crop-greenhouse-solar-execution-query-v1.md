# 현재 일사 실행 진행 조회 — v1

2026-10-17. native Codex CLI `gpt-6.1-sol / xhigh`에서 판단한다. 재귀 CLI는 실행하지 않는다.
[실행 핵심](crop-greenhouse-solar-execution-core-v1.md)의 조회 경계다.

`SolarExecutionQuery(checkpoint_store,result_store)`는 같은 jobs/server/admission/binding을 가진 정확한
Solar checkpoint/result 타입·현재 code/역할/포인터를 요구한다. 읽기 권한으로 현재 계정·농장/입력·자료 권리를 확인한다.
create/execute/write 권한을 조회에 요구하지 않는다. 조회는 계산·복원·checkpoint 확정·작업/결과 쓰기를 호출하지 않는다.

읽기 전용 repeatable-read의 job/최신 확인 사건/결과 연결/publication/outcome/terminal 묶음을 검증한다.
서명 custody의 현재 HEAD/progress·provenance와 확인 사건을 대사하고, 별도 읽기 거래에서 DB 묶음/결과 행을 재검사한다.
그 사이 작업이 바뀌면 Pending이며 부분 응답을 게시하지 않는다. 직렬화 뒤에도 현재 입력/농장/자료 권리를 다시 검사한다.
현재 권리·입력·code/행/서명이 틀리면 Hold다.
다른 tenant·stage·입력 판본/없는 작업은 None이다. 다른 판본은 Solar 이력 파싱 전에 구분한다.

닫힌 `joint-solar-execution-query-v1` 응답은16KiB 이하이며 다음을 포함한다.

- 기존 공개 job 상태·cancel_requested·새 관측 UTC
- checkpoint_status none/current/unavailable, 원 HEAD/proof/artifact/provenance 해시·단계/건수/계산 UTC·최초 DB 확정 UTC
- current인 경우 정상/수치 hold의 원 result ID·farm 참조·status/provenance
- top/checkpoint/result의 literal rights_or_gate_approval=False·G0–G4 not_assessed

미기동은 none, 파일 잠금/아직 DB가 확인하지 않은 새 HEAD는 unavailable이다. 임의 진행률이나 재계산 값을 만들지 않는다.
완료 result/progress/확인 사건/link/attempt/terminal은 같아야 하며 normal publication1·hold publication0을 구분한다.
결과와 checkpoint의 provenance는 같아야 한다. 토큰/임대 자격·원 입력·매개변수/내부 경로·review/rights 원문은 반환하지 않는다.
순수 DTO 모듈은 이 단계에서 HTTP 경로를 설치하거나 새 공개 요청 API를 추가하지 않는다.

## 수용 기준

1. 실제 SCRAM에서 queued/canceled/미확정/확정/heartbeat/재시도·동일 원 HEAD/UTC/최초 시각·normal/hold result·busy lock을 검증한다.
2. 읽기 scope·현재/늦은 권리·잘못된 code/입력/provenance/승인/확인 사건·결과/link/상태 변경에 실패하고 조회 수치/SQL 변경0을 확인한다.
3. 독립 fresh 같은 DB/키/파일에서 observation time을 제외한 원 응답을 대사한다. 원본/기존 서비스·두 UI·5root/동적 자식·WSL 한도/FD/소유 정리를 유지한다.

합성32초 software 조회다. 확정 prefix의 sample/event 선택·접수/진행/취소 보호 HTTP/runtime·typed 웹/같은 UTC3D·사용자 적용·전체 작기·실제 자료/G0–G4/예측·추천은 별도다.
