# Cycle 원 입력의 현재 농장/권리 결합 — 구현과 검증

상태: **로컬 소프트웨어 수용**, 2026-10-05 KST. `crop-cycle-farm-binding`.
[계약](../contracts/crop-cycle-farm-binding-v1.md),
[불변 영수증](artifacts/crop-cycle-farm-binding-reference-20261005.json),
[선행 schema/권한](crop-cycle-storage-roles-implementation.md)을 확인한다.
현재 실제 Codex CLI `gpt-6.1-sol / xhigh`,09:51:56.077Z turn_context/원 line SHA를 기록했다.
동일 CLI 세션에서 재귀 실행0회다. 제품 runtime CLI 실행/G0–G4 수용으로 표시하지 않는다.

## 구현과 실제 의존성 분해

3파일은 `backend/app/crop_cycle_farm_binding.py`,
`backend/tests/test_crop_cycle_farm_binding.py`, 계약이다.
기존 v3의 inline segment/program SHA·20MiB row를 긴512MiB 파일에 적용하는 공백과
artifact SHA/ledger 검사가 실제 서버 계산의 인증을 대신하지 못하는 근거로 저장 부모를 나눴다.
현재 farm/input 결합 → 실제 서버 writer/서명된 progress → DB HMAC/atomic 게시 순서이며
부모 `crop-cycle-result-storage`는 세 자식의 증거가 모두 있을 때까지 미완료다.
새 서비스/queue/dependency는 추가하지 않았다.

CycleFarmBinding은 정확한 FarmAuthoringService·고정 authority/SCRAM·현재 전체 grant 감사와
명시 cycle storage flag를 요구한다. 기존 farm의 등록 job/요청 SHA·원천/현재 경제 입력과
crop/batch/zone/floor·occupancy/농장 달력/decision을 다시 읽는다.
128KiB 이하 canonical closed 요청은 파일 경로 대신 root SHA/program ID와 별도
`crop-cycle-input-rights-v1` 선언을 받는다. root 전용 current provider를 최초 identity/policy_version에 고정한다.
계산 준비는 research_calculation/display, 읽기는 display의 exact True를 검사한다.
callback의 선언 변경과 중간 farm/source/scope/입력 파일 변경을 거부한다.

현재 canonical root/reader 내부 root·실제 root 파일/전체 preflight block·프로필/normalizer/모델 코드/
Python 판본을 대사한다. input root의 canonical codec은 원 input reader의 ASCII escape 규칙을
그대로 사용한다. farm/request/binding의 UTF-8 codec과 혼용하지 않는다.
이 검사에서 RHS/advance와 crop row/Run은0이다. 원 InputPacket의256자 이하 block input_id와
synthetic origin을 유지하며 새 요청 identifier는 기존 crop Identifier1..200자다.

## 실제 검증과 수정 기록

실제 Python3.12.3/Psycopg3.3.6/Pytest9.1.1·native PostgreSQL16.15를 사용했다.
각 private loopback SCRAM cluster는 순차1개,32connections/16MB shared/1MB work/16MB maintenance,
nice10이다. hosted3.12.13/18.6 수용은 별도다.

| 실행 | 관측과 수용 범위 |
| --- | --- |
| 처음49개 | 48통과/1실패·1147.47초; source 철회 주입 대상에 해당 method가 없었음 |
| 처음 유효 통과 | 47개; 같은 오기의 late-source 시험은 callback 예외로 잘못 통과해 수용에서 제외 |
| 추가 반례4개 | 3실패/1통과·94.19초; callback 후 root/block 변경·reader 내부 root 변경을 놓침 |
| 코드 수정 뒤 집중8개 | 8통과/45deselected·212.61초; 실제 source/late-source·4반례·정상 SCRAM·별도 Python/FD 재검증 |
| Unicode 반례 | 1실패/53deselected·1.18초; 다른 canonical codec의 root 비교가 한글 원 block ID를 거부 |
| 원 input codec으로 수정 | Unicode와 정상 farm2개 통과/52deselected·30.49초 |
| 최종 고유 검증 | **54개 분할 수용**;47+8−중복2+Unicode1. 단일54 GREEN/전체 backend가 아님 |

처음 workspace root에서 단독 수집한 명령은 app import 경로 오류였다.
native runner는 backend cwd에서 실행했다. 그 수집 오류를 expected missing-implementation RED로 세지 않는다.
실제 세 input 반례와 Unicode RED 로그·소스 판본/수정 diff를 보존했다.
원49개의 source/late-source 오기를 실제 current 경제 source provider에 수정하고 두 경우를 다시 검증했다.
요청/권리/availability/농장·crop/등록/입력 version/hash/program ID의16반례,
비 canonical/중복/NaN/UTF-8/empty/oversize6개, 현재 scope/source/input 권리8가지,
고정 profile/provider/policy/farm/identity/code/고지·reader/파일/expected bytes11가지,
exact True 반환5가지와 occupancy/fresh process를 포함한다.

최종 정상 fixture는 **3,496bytes**, SHA
`993bb2e23275aa6e04567fc3fa3cd39bc5c4c753773f8c7984c859a91c3892b1`의 canonical binding이다.
현재 읽기와 동일 bytes, 준비5.560829초/읽기5.819576초를 관측했다.
원 입력은11,548참조 bytes·2구간·3anchor/3output·event0·예정120step이다.
그120은 preflight 산술이며 crop RHS 실행이 아니다. jobs/events counts는 변하지 않고 crop row/Run0개다.
별도 Python fork의 실제 재접속/동일 bytes와 반복 current의 FD 수 보존을 확인했다.
이 process 검증은 실제 운영 UID/자격증명 소유권의 독립성을 증명하지 않는다.

모든5개 DB 실행 뒤 role/schema/runtime 비밀번호0개·PG stop/status3·private cluster/admin 파일
제거·소유 서버0개를 확인했다. 최대 관측 순차 자식RSS는136.21484375MiB다.
WSL 전체/동시 process group의 합계 측정이 아니다. 원44개 계산/저장/API/schema source SHA를 보존했다.
원 로그와 실제 fixture binding/접속정보는 private `/tmp`, 공개 영수증은 hash/수치/정리만 기록한다.

## 다음 한 단계와 외부 의존성

[서버 custody 후보](../contracts/crop-cycle-server-custody-v1.md)는 private resolver/intent에서
frozen writer가 실제 RHS를 실행하고 새 HEAD의 HMAC proof를 먼저 fsync한 뒤 atomic HEAD를 게시한다.
실제 선택 HEAD의 대응 서명으로 복원하며 unsigned 새 계산 delta를 채택하지 않는다.
구체 closed proof/byte/file budget은 구현 전에 고정한다.
그다음 DB metadata/HMAC/commit 전후 현재 권리·immutable retry를 연결한다.
성장3D는 이후 같은 저장 ID/UTC의 API/client 경로로 연결한다.

첫 결합2–3시간/10월5–6일 예상은10월5일 로컬 수용으로 대체한다.
다음 module/test/계약3–5파일은 계약/adapter/proof1–2시간+실제 writer/현재 권리/복원1–2시간+
강제 종료/변조/정리1시간, **3–5집중시간/10월5–7일 KST 잠정**이다.
DB custody2–3시간을 포함한 남은 저장 부모는5–8시간/10월5–8일 KST 잠정이며
하루4시간 기준/CI·외부 자료 대기를 제외했다. 실제 실적에 따라 갱신한다.
기존 단일5–8시간은 분해 전 추정이며 전체 세 자식의 기준은7–11시간이었다.

`ff6eb3d`의 Web/C0/Application/Authored workflow는 terminal success,
Backend는 두 파트 실행/나머지 대기라 전체 수용 전이다. 이 단계는 그 SHA 밖이며 push는 대기한다.
이전 `fe41e22`의 [전체 CI 수용](artifacts/crop-cycle-stream-ci-20261005.json)은 그대로다.
실제 input 채택/국내 독립 측정/actual crop Run0개, 현재 profile_applicability는
`unvalidated_for_registered_crop`다. 신뢰된 provider의 실제 정책·자료/리뷰/권리와 독립 검증은 미확보다.
server/DB custody·cycle API/client/3D·166일 실제 RHS 부하·생과/자원/Decimal 경제 결합,
실제 runtime CLI·G0–G4·생산/전망/추천 게시 날짜는 미수용/보류를 유지한다.
