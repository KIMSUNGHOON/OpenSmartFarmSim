# 자동 출현 입력과 현재 농장·완료 줄기 작업 — v1

상태: 구현/수용 전. 선행은 [원 appearance 입력 증거](crop-leaf-appearance-input-evidence-v1.md)와
기존 [완료 morphology 조회](crop-morphology-execution-v1.md)다.
원 정책/초기 위치/프로필을 생성된 잎 선언으로 대신하지 않고 같은 농장/완료 parent에 결속한다.

`LeafAppearanceFarmBinding(parent_query,input_authority,input_rights=...)`는 기존 실제
MorphologyExecutionQuery/farm authority·JobStore와 같은 stem input authority를 사용한다.
새 표/역할·결과 row·서비스를 만들지 않는다. 원 parent 결과/기존 population/사용자 화면은 보존한다.

닫힌128KiB 요청은 study_id/revision/farm/input/rights/parent다.
farm은 원 scenario ID/revision/등록 SHA/crop ID, input은 appearance source schema/program ID·
원 program/source/evidence SHA다. parent는 실제 완료 job UUID/result SHA/numerical root SHA다.
rights는 `leaf-appearance-input-rights-v1`의 원 source SHA·가용 시각/판본·명시 비공개 사용 선언이다.
키/경로·임의 callback이나 unsigned root로 서버 원 결과를 대신하지 않는다.

prepare/current는 tenant/request와 서버가 읽은 원3bytes를 받는다.
현재 parent의 실제 completed/publication·서명/root와 요청의 parent/farm을 대사한다.
parent authority의 원 packet/binding으로 같은 decision의 원 stem arguments를 구성한다.
appearance 증거의 정책/초기/프로필·37code·검토와 원 parent program/source/evidence/root가 같아야 한다.
write=True는 양쪽 현재 계산/표시 권리, False는 표시 권리를 요구한다.
등록 occupancy/KST 달력·decision과 양쪽 available_at/기간을 유지한다.
decision 뒤 가용인 source는 과거 작업에 소급하지 않으며 필요하면 별도 늦은 decision의 합성 farm/parent를 사용한다.

2MiB binding은 원 등록/완료 job·서명/result/root·최초 계산 시각·입력/정책/초기/프로필·검토·현재 정책/코드를 묶는다.
per_tracked_shoot·품종/수치 초기조건 미검증·권리/G0–G4 미승인은 유지한다.
parent_result_binding_verified=True는 그 job/서명/root 연결만 뜻한다.
expected binding bytes를 대사하고 양쪽 현재 근거/권리·범위를 전후 검사한다.
서로 다른 저장소/resolver의 원자 snapshot은 주장하지 않으며 후속 게시기가 다시 확인한다.

수용: 닫힌 요청/크기·같은 parent/farm/원 단위·정책/기간·1µs 가용 경계와 혼합 거부,
실제 SCRAM의 별도 등록/완료 parent→prepare/read/write·독립 fresh 같은 bytes,
다른 tenant/미완료·취소/root·현재/늦은 양쪽 검토·권리/등록/권한 변경 거부다.
검증 구간의 생장/CLI·SQL쓰기0·원 행/파일/FD·3root/WSL 상한·소유 DB/역할/임시 파일 정리를 확인한다.
새 appearance 서명/worker/API/사용자 자동 실행·실제 자료/품종 관문은 별도다.
