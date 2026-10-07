# 현재 저장 작기 조회의 API/runtime 연결 — v1

2026-10-07 KST. [현재 농장 조회](crop-cycle-current-query-v1.md)를 기존
`/v1/crop-cycle-research-results/{result_id}`에 명시적으로 선택 연결한다.

`ApiRuntimeDependencies.crop_cycle_current_query_factory`는 선택적 비공개 callable이다.
선택 시 기존 cycle result store factory/권한 flag가 있어야 하며 연결 전에 조합을 검사한다.
factory는 `result_store`를 받아 정확한 `CurrentCycleQuery`를 반환하고, 같은 runtime의 store·
jobs·farm service를 공유해야 한다. 잘못된 반환/교체는 assembly 거부다. 기본 기존 reader는 유지한다.
`create_app(..., crop_cycle_current_query=...)`와 route installer도 같은 authority를 대사한다.

새 경로는 조회 `open(...)` 안에서 기존 순수 공개 투영과 전체 JSON bytes를 준비한다.
투영 뒤에도 현재 DB/권리/trace/입력/result를 확인한 후 문맥을 닫는다. 기존 상태 코드·닫힌 query·
Scope·401/403/404/422/503·no-store와 전체 응답30초/2MiB를 유지한다.
공개 JSON schema와 원 math provenance는 유지하며 새 조회 판본/code는
`X-OSSF-Crop-Query-Version`, `X-OSSF-Crop-Query-Code-SHA256` 헤더로 표시한다.
키·private 증명/경로·DB HMAC는 공개하지 않는다.

실제 등록 합성 농장의 원 RHS/DB 저장/QC 발행 뒤 실제 runtime·SCRAM/TLS에서 모든 작은
시점/사건·같은 UTC/원량·summary/끝 페이지·재시작을 대사한다. 현재 계정/권리·투영 후 철회·
trace/파일 변조 거부, 조회 parser/QC/RHS0·응답 전체 크기/시간·서버/FD/DB/역할/비밀/PG 정리를
확인해야 `crop-cycle-query-runtime` 및 현재 조회 부모를 수용한다.
전체166일/3D/관문 수용과 실제 품종/검증 자료는 계속 별도다.
