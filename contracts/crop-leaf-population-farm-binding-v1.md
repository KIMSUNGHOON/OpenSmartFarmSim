# 출현 잎 입력과 현재 농장·완료 줄기 작업 — v1

상태: [순수33/실제 SCRAM2·fresh 수용](../research/crop-leaf-population-farm-binding-20261023.md).
선행은 [leaf 입력 증거](crop-leaf-population-input-evidence-v1.md)와
기존 [완료 morphology 조회](crop-morphology-execution-v1.md)다.

`LeafPopulationFarmBinding(parent_query,input_authority,input_rights=...)`는 기존 실제
`MorphologyExecutionQuery`/농장 authority와 새 leaf 입력 authority를 사용한다.
parent와 leaf는 같은 stem input authority·JobStore/명시 runtime identity를 공유한다.
새 표/역할·Run/leaf 계산 결과는 만들지 않는다.

닫힌128KiB 요청은 study_id/revision/farm/input/rights/parent다.
farm은 기존 scenario ID/revision/등록 SHA/crop ID, input은 leaf source schema/program ID와
원 program/source/evidence SHA다. parent는 실제 완료 job UUID/result SHA/numerical root SHA다.
rights는 `leaf-population-input-rights-v1`의 원 source SHA·가용 시각/판본과 명시 비공개 사용 선언이다.
요청 경로/키·임의 callback 또는 서명 없는 root 대체는 없다.

prepare/current는 tenant·request와 서버가 읽은 leaf 원3bytes를 받는다.
현재 parent query의 실제 completed/publication/서명/원 root와 요청 parent/farm을 대사한다.
parent authority가 읽은 원 packet과 binding으로 leaf 증거의 parent arguments를 서버에서 구성한다.
parent의 원 program/source/evidence와 root가 모두 같아야 한다.
write=True는 양쪽 자료의 현재 계산/표시 권리, False는 표시 권리를 요구한다.
등록 crop occupancy/KST 달력·decision UTC와 양쪽 available_at/기간 검사를 유지한다.

2MiB binding은 원 farm 등록/parent job·서명 결과/최초 계산 시각/원 root,
leaf 출처·초기/출현 지문·입력 증거/검토와 현재 정책·코드를 결속한다.
per_tracked_shoot와 실제 품종 미검증·수치 초기조건 미검증/권리·G0–G4 미승인을 유지한다.
`parent_result_binding_verified=True`는 해당 job/서명/root 연결의 확인이며 생물학적 검증이 아니다.
현재 조회는 expected binding bytes와 같아야 하고 양쪽 현재 근거/범위·권리를 전후 검사한다.
서로 다른 파일/DB/resolver의 원자 snapshot은 주장하지 않으며 후속 게시기가 다시 검증한다.

새 leaf 자료가 기존 farm decision 이후 가용이면 그 과거 작업에 소급 결속하지 않는다.
필요한 경우 더 늦은 decision의 별도 합성 farm/parent 작업을 등록하며 기존25표/작업·파일은 보존한다.

수용: 순수 닫힌 요청/단위·같은 parent/farm/기간·1µs 가용 경계와 변조 거부,
실제 SCRAM의 별도 등록/완료 parent→prepare/read/write·독립 fresh 같은 bytes,
다른 tenant/미완료·취소/다른 root·권리/검토·등록/권한의 현재/늦은 변경 거부다.
검증 구간 생장·CLI/SQL쓰기0, 원 행/저장물/FD·원2서비스/WSL 상한·소유 PG/schema/role/passfile 정리를 대사한다.
leaf 서명/worker/API/사용자 화면 통합과 실제 자료/품종 관문은 후속이다.
