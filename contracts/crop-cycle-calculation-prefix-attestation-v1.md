# 현재 bytes를 검증하는 prefix 증명 — v1 개발 계약

2026-10-08 KST. `crop-cycle-calculation-prefix-attestation`의 구현 전 계약이다.
선행은 [실제32회와 순회 비용](../research/crop-cycle-calculation-full-budget-observed-20261008.md)이다.
현재 전체 등록 계산의 wall 예산·장시간 실행은 보류이며 이 계약 자체가 구현 수용은 아니다.
판단은 현재 native Codex CLI `gpt-6.1-sol / xhigh`에서 하고 재귀 CLI를 실행하지 않는다.

## 목적과 구현 경계

현재 n번째 호출의 과거/새 delta 물리 검증2n회를, 실제 새 delta의 고정된 검증으로 바꾼다.
서버가 검증한 이력의 현재 전체 bytes와 서명 체인을 매번 확인한다.
mtime/inode만의 무결성 확인·현재 권리 cache나 외부가 제안한 checkpoint의 채택은 허용하지 않는다.

첫 core는 다음6파일이다.

1. `backend/app/crop_cycle_calculation_prefix.py`: 닫힌 검증 claim·실제 delta 검증/인증된 prefix reader.
2. `backend/app/crop_cycle_calculation_server_custody.py`: 명시 새 private 판본·proof/재개/progress 결속.
3. `backend/tests/test_crop_cycle_calculation_prefix_attestation.py`: 실제 계산/복원·변조·검사 횟수/자원 반례.
4. `research/crop-cycle-calculation-prefix-cost.py`: 기존 Costs로 새 prefix/현재 blob 검사 비용을 계측한다.
5. `backend/tests/crop_cycle_full_prefix_cost_smoke.py`: 새 경로의 계측 수용 조건을 연결한다.
6. 이 계약. 기존 SCRAM/저장/현재 조회 회귀를 재사용한다.

현재 수동 시험은 `artifact.prefix_verify` 호출이 양수여야 한다고 요구하므로 새 경로에는
그 조건을 그대로 적용하지 않는다. 새 `prefix.authenticated_read`를 양수로 확인하고, 관측 범위의
과거 `_load_prefix`/물리 QC는0회로 검사한다. 기존 수동 시험의 관측 밖 원 `_load_prefix` 대사는
독립 원량 검증으로 유지한다. 계측 판본/새 이름·중첩 비용 정의와 원 함수 복원을 검증한다.

context/입력 증명/farm/artifact의 source와 수식·RK4/clock/원 출력 격자는 보존한다.
helper는 기존 artifact의 `_validate_delta`·고정 header/형식 검증을 명시적으로 사용한다.
기존 public writer/reader의 검증 경계를 바꾸지 않는다. 서버의 새 재개 경로가 별도 검증 증명을 요구한다.
새 서비스·DB schema·runtime 설정 필드는 추가하지 않는다.

## 판본과 인증 경계

서버/intent/HEAD proof는 각각 `crop-cycle-verified-server-custody-v2`,
`crop-cycle-verified-server-intent-v2`, `crop-cycle-verified-server-head-v2`로 구분한다.
identity/intent/HEAD HMAC domain도 각각 `ossf-crop-cycle-verified-server-identity-v2`,
`ossf-crop-cycle-verified-server-intent-v2`, `ossf-crop-cycle-verified-server-head-v2`의 NUL 종료 bytes다.
v1 파일·서명·입력/과거 결과는 보존하며 v2로 재발급하거나 묵시 복원하지 않는다.
v1 실행은 고정된 이전 코드/환경에서 재현하는 대상이고 새 구현에 이전 proof를 넘기면 거부한다.
원 과거 bytes를 변환하는 migration은 이 작업에 없다.

v2 HEAD proof의 기존7필드에 `validation` 하나를 더한다.
그 객체는 다음6필드만 받는다.

| 필드 | 실제로 결속하는 값 |
| --- | --- |
| `version` | `crop-cycle-verified-prefix-validation-v1` |
| `validation_code_sha256` | 현재 prefix validator source SHA |
| `checkpoint_sha256` | meta checkpoint SHA; numerical hold면 null |
| `confirmed_checkpoint_sha256` | `_validate_delta`가 확인한 checkpoint SHA 또는 null |
| `counts` | 실제 확정 `samples`/`events`의 비음수 정수 두 필드 |
| `summary_sha256` | 실제 최신 result meta의 canonical SHA; 초기에는 null |

초기 claim은 고정 header의 초기 checkpoint·count0에 결속한다.
advance claim은 선택된 이전 signed prefix와 현재 bytes를 확인하고 **실제 새 delta의 물리/수지 검증을
통과한 뒤에만** 생성한다. publisher는 writer의 임의 mutable checkpoint/summary를 승인 근거로 받지 않는다.
finalize claim은 같은 최신 delta의 검증 claim을 보존하고 원 root/commit 목록과 terminal 상태를 확인한다.
source/의존성·고지/입력·farm/tenant·현재 권리와 실행 key는 기존 서버의 고정 경계를 따른다.
클라이언트/CLI는 key나 claim 발행 인터페이스를 받지 않는다. 서명 자체를 자료 권리·G0/G2 승인으로 사용하지 않는다.

검증 증명은 기존 HEAD proof 안에 넣어 proof 수·bytes/files의 기존 한도를 유지한다.
기존 **현재 권리 확인 → proof fsync → 현재 권리 확인 → atomic HEAD** 순서와 crash/orphan 정책을 유지한다.
입력/증명·디렉터리 identity와 source가 바뀌면 정상 결과를 반환하지 않는다.

## 현재 prefix reader와 재개

reader는 선택 HEAD와 genesis까지의 모든 proof HMAC/parent/sequence/판본·validation 관계를 확인한다.
고정 header와 실제 commit 체인, 모든 참조 page의 **현재 전체 bytes/SHA**·bounded regular file·
소유/권한/link·resource 한도를 검사한다. signed claim과 실제 meta/parent/checkpoint·counts를 대사한다.
과거 page의 물리 검증을 반복하는 대신 그 bytes를 검증한 v2 서버 증명을 소비한다.
전체 과거 blob의 현재 해시 검사는 유지하며 현재 숫자/페이지를 임의로 교체할 수 없다.

정확한 factory가 만든 닫힌 불변 prefix 객체만 내부 서버 재개/progress에 사용한다.
최신 checkpoint는 기존 공식 serializer/validator로 검사하고 기존 writer의 exclusive lock·
context·현재 HEAD identity에 결속한다. hold/완료는 추가 계산하지 않으며 빈 초기 상태는 명시적으로 다룬다.
서버 public advance/inspect/page와 응답 field 집합은 유지하고 새 private 판본 provenance를 기록한다.
현재 query의 기존 proof decoder 사용도 대조해 인증된 read-only 경로가 작동함을 검증한다.
terminal result 증명 발행/게시의 기존 전체 물리 QC와 page 검사는 유지한다.

## 수용 기준

1. 기존 실제6프로그램/hold·분할·fresh Python 복원에서121상태/seed/clock/cursor·원 확정 행과 수지를 대사한다.
   같은 새 판본의 연속/분할 checkpoint 및 proof 관계가 같고 조회/완료 재시도 RHS0이어야 한다.
2. 실제 연속 호출의 과거 delta QC 반복을 RED로 계측한다. 새 delta는 writer와 독립 publisher 검사 각각1회,
   정상 재개/progress에서는 과거 `_load_prefix`/물리 QC0회를 확인한다. 실제 현재 bytes 검사는 항상 실행한다.
3. v1/다른 key·code·context·scope·proof parent/sequence/claim/summary/count·rehashed chunk/page,
   metadata를 복원한 변조·누락·symlink/link·닫힌 문맥/lock·unsigned delta를 거부한다.
   claim 발행을 우회한 caller dict·mutable writer state와 numerical hold의 가짜 계속 실행도 거부한다.
4. 계산/검증/proof 전후·HEAD 전후의 실제 중단·늦은 변조/현재 권리 철회에서 선택된 이전 HEAD만 복원한다.
   별도 Python·현재 등록/권리의 실제 SCRAM·DB 게시/현재 조회·원 형식 공존 회귀를 확인한다.
5. 같은 전체 입력의 초기32회에서 원 checkpoint/확정 행·검증 호출 수·현재 bytes/서명 비용을 분리한다.
   FD/cache·262개 이상 관련 source·원 입력/과거 이력·PG/비밀/실제 명령 종료/정리를 검증한다.
   source/버전 변경은 원 증거와 구분하며 계측기를 고치는 경우 비용 정의 변경도 기록한다.
6. 기존 입력/저장/응답 한도를 유지하고 실제 proof bytes·현재 재개/검증 메모리를 확인한다.
   보고서/영수증 뒤 이 자식만 체크한다. 전체 작기 wall 예산과 DB/API/3D 부모는 해당 실제 증거를 기다린다.

전체 이력의 bytes/HMAC 순회 비용은 이 구현 뒤에도 남는다. 그 실제 비용과 현재 권리/계산·저장 비용을
확인해 전체 실행 예산을 정한다. 현재 실제 품종/국내 독립 자료/측정 농장 작물 Run0과 관문 hold는 유지한다.
