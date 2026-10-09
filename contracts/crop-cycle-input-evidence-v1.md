# 원 입력 수학 검사의 서버 영수증 — v1

상태: **구현 후보**, 2026-10-06 KST. 근거는 [원 검사 비용](../research/crop-cycle-input-validation-cost-observation-20261006.md)과
[바이트 대사 실험](../research/crop-cycle-input-witness-experiment-20261006.md)이다.
운영 기반이나 계산식 변경 없이 `backend/app/crop_cycle_input_evidence.py`, 집중 시험, 이 계약의
3 core파일로 먼저 검증한다. 실행 중인 전체166일의53개 source는 변경하지 않는다.

## 인터페이스와 신뢰 범위

`InputEvidenceAuthority(profiles, notice_raw, *, integrity_key, issuer_id, key_id)`는 서버가 지정한
정확한 프로필·고지·별도 영수증 전용 키와 bounded ID를 고정한다. `issue(directory, root_sha256)`는
소유권/읽기 전용 현재 bytes를 먼저 확인하고 원 `InputPacket`의 전체 preflight와 원 `prepare_context`를
실제 실행한다. 같은 root의 모든 현재 참조 bytes를 다시 확인한 뒤 canonical/HMAC 영수증 bytes를 반환한다.
원 manifest/계획·격자 index·
121 seed·initial/정확한 Fraction clock을 보존한다. UTC 검증 시각과 코드/프로필/환경도 기록한다.
실패 시 영수증을 발행하지 않는다. RHS·자료 채택·농장 권리 승인은 수행하지 않는다.

`verify(directory, root_sha256, evidence_raw)`는 닫힌1MiB 이하 canonical JSON·정확한 판본/issuer/key ID·
서명·현재 코드/프로필/고지/Python과 모든 현재 root/blob SHA·정확한 inventory/총 bytes를 대사한다.
성공 시 불변 `VerifiedInputEvidence`를 반환하며 `context`는 읽을 때마다 독립 JSON 사본이다.
`rights_or_gate_approval`은 항상 false다. `InputPacket`/`StreamContext`를 private token으로 위조하거나
새 객체에 캐시를 주입하지 않는다. 현재 factory와 farm/runtime/API는 이 단계에서 변경하지 않는다.

키는 호출자가 서버 비밀 설정에서 제공한다. 새 키 서비스·DB 표·외부 API를 추가하지 않는다.
키를 영수증/로그/브라우저/공개 receipt에 포함하지 않는다. 같은 키·issuer/key ID를 보존한 별도
프로세스의 재시작 검증을 시험한다. 키/ID 분실 또는 교체는 기존 영수증을 거부하며,
알 수 없는 키로 fallback하지 않는다. 자동 키 회전·실제 운영 설정/배포의 키 보관 수용은 별도다.

입력은 기존 서버 소유 파일 계약에 따라 no-follow 디렉터리·euid/0700과 단일 링크/0400 regular 파일·
ACL/읽기 전후 metadata/크기 한도를 검사한다. 영수증은 이전 원 검사와 동일 bytes에만 적용된다.
성공 후의 미래 변조는 새 reader의 각 실제 읽기에서 SHA를 재검사해야 한다. 키/프로세스 메모리
침해나 미래 불변성을 보장하는 증거로 설명하지 않는다. 현재 농장/테넌트/권리·등록·현재 Scope는
후속 연결에서 전후 재검사하며, 이를 입력 schema/QC 증명으로 대체하지 않는다.

## 판본과 후속 연결

영수증 자체에 새 판본/코드 SHA/HMAC domain을 부여하고 원 input normalization SHA·context manifest·
원 계산/저장 root는 그대로 보존한다. 기존 연구 HMAC은 이 서버 영수증으로 받지 않는다.
소스/프로필/환경이 달라지면 기존 증명을 새 버전으로 묵시 전이하지 않는다.
빠른 typed reader/context factory와 원 결과의 역사 재생·실제 farm/DB/HTTP/3D 수용은 후속 작은 작업이다.
현재 v1 reader/engine/API 경로는 이 영수증을 소비하지 않는다.

## 수용

- 원 전체 검사 실패는 발행 거부; 원 context/index/initial/seed/clock/계획을 byte 의미 그대로 보존.
- 재조회는 최초 전체 parser/normalization/preflight를 재호출하지 않으면서 현재 모든 원 bytes를 대사.
- 서명/payload/issuer/key ID/판본/code/profile/notice/environment·비정규/중복/NaN/크기 오류,
  root/blob 변조·누락·symlink/여분 파일·쓰기 허용/다중 링크·잘못된 소유를 거부하고 FD를 정리.
- 별도 Python 재시작에서 같은 서버 제공 키로 같은 context를 확인하고, 다른/분실 키는 거부.
- 고정166일 **입력**에서 원 발행/재조회 비용과 같은 원 context/index·749 blob·113,920,841bytes·
  RHS0·FD/자원·원53개 source 보존을 기록. 전체166일 계산 성공이나30초 HTTP 수용으로 확대하지 않음.
  발행의 원 byte 대사는 검사 전후 두 번이고 재조회의 대사는 한 번이며, 비용/실제 읽기를 구분해 기록.

사용자 산출물은 계약·검증/비용 보고서·비밀을 제거한 불변 receipt다.
`crop-cycle-burden-replay-restore`와 부모는 실제 전체 결과·typed reader·현재 권리/API/3D 검증 전 미수용이다.
실제 품종/독립 국내 자료0건과 G0–G4·생산 예측/추천 보류를 유지한다.
