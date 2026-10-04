# 기관/50과실 구획의 저장 선행 artifact — v1

상태: **로컬 합성 artifact 수용; 실제 DB/권리 저장은 후속**.
선행은 [짧은 적분 수용](crop-plant-cohort-integration-v1.md)이다.
현재 개발 CLI `gpt-6.1-sol / xhigh`에서 설계하며 재귀 CLI를 실행하지 않는다.

## 경계와 호출

`calculate_coupled_artifact(program_raw, *, growth_profile, cohort_profile,
transport_profile, notice_raw)`는 서버가 받은 canonical UTF-8 JSON 프로그램을
고정 적분기로 계산해 immutable bytes를 반환한다. 입력에 결과/계수/승인/테넌트를
받지 않는다. 계산은 HTTP handler 밖에서 호출하는 후속 저장 경로의 구성 요소다.
외부 작성 결과를 계산 완료로 받아들이는 import 인터페이스가 아니다.

`read_coupled_artifact(raw, *, expected_sha256, growth_profile, cohort_profile,
transport_profile, notice_raw)`는 신뢰 저장 참조에서 받은 bytes SHA-256과 현재 고정
모델/프로필/코드·scope/입력·출력 형태/시각·수지를 검사하고 새 사본을 반환한다.
조회는 재적분하지 않는다. `expected_sha256` 자체와 artifact hash는 소유권/승인
서명이 아니다. 후속 DB 경계가 HMAC·현재 farm/program 권리를 먼저 검증해야 한다.

초기 artifact는 **모든 블록 origin=synthetic**인 프로그램만 받는다. 입력 ID의
길이/비음수·단위/50구획·UTC/solver/시간/연산 상한은 적분 계약을 유지한다.
같은 입력 ID가 다른 블록을 뜻하면 거부한다. 실제 관측/외부 참조 자료는 별도
rights/QC/source 연결 판본까지 받지 않는다. `CoupledArtifactHold`로 거부한다.

## 불변 bytes와 출력

- 프로그램 원 canonical bytes 상한 **1 MiB**, 전체 artifact 상한 **16 MiB**.
  정규화 전 원문과 그 SHA-256을 보존한다. 큰 입력은 계산 전에 거부한다.
- 닫힌 artifact에는 `schema_version=crop-coupled-artifact-v1`,
  `claim_scope=synthetic_crop_math_only`, `program_raw_utf8`, `program_sha256`,
  `profile_raw_utf8`(growth/cohort/transport 세 개), `notice_raw_utf8`,
  `artifact_code_sha256`, 원 적분 `result`, `artifact_id`만 들어간다.
- `artifact_id=crop-coupled-artifact-v1:<sha256>`는 그 ID를 제외한 canonical
  bytes hash다. 현재 고정 profile/notice bytes를 그대로 담는다. 입력/결과의
  integrator hash 규칙과 UTF-8 artifact hash 규칙을 혼용하지 않는다.
- result의 model/profile/policy/code/solver·정규화 input hash·result hash,
  provenance/assumptions/UTC/수렴 상태를 대사한다. 현재 코드와 다르면 hold다.
- 각 sample의 닫힌 단위/상태·50 N/C·누적 외부 유량·LAI/합산 fruit C와 두 수지/
  ULP 예산을 검사한다. sample은 요구 출력의 순서 있는 앞부분이다. 완료에는
  모든 출력/사건과 planned step이 있어야 한다. hold에는 확인된 과거만 있다.
- 관리 journal은 원 사건 시각/ID·같은 구획 N/C 제거 비율과 전후 상태를 대사한다.
  trial 진단의 hold 시각은 UTC 소수 초를 허용하고 sample 시각은 정수 초다.

이 artifact에는 farm/tenant/batch/DB 시각/권리 선언·서명·Run/G1/G4 승인이 없다.
일반 품종 적용/생과 수확/판매·예측/추천 자료로 게시할 수 없다. 실제 PostgreSQL
저장 v2는 이 bytes와 농장/프로그램 권리를 원자적으로 묶는 별도 수용 작업이다.
기존 crop-result-v1의 bytes/조회/테이블/role을 변경하지 않는다.

## 수용과 다음 단계

1. 실제 public integrator의 두 독립 참조 사례를 artifact로 계산하고 exact bytes/
   profile/notice·모델/코드/입력 hash를 확인한다. 새 reader/별도 Python도 같은 bytes를 읽는다.
2. 조회의 재적분 없음, caller 입력/reader 사본 변경의 격리와 동일 입력 재현을 확인한다.
3. 실제 numeric hold의 phase/time/last-confirmed와 과거 시점만 보존한다.
4. 과대/비canonical/중복 키/비유한/추가 입력, 비합성/서로 다른 동일 ID를 계산 전 거부한다.
5. byte/신뢰 hash·모델/코드/프로필/단위/길이/시점/수지/사건 혼합을 거부한다.
6. 실제 CLI·시험/파일 hash와 로컬 자원을 기록한다. DB/SCRAM·권리/원자성·API
   30초 본문/페이지·3D는 이 첫 단계의 수용으로 체크하지 않는다.

다음은 `crop-coupled-result-storage`: 명시적 farm/program 권리·같은 불변 bytes를
새 DB 판본에 저장하고 실제 SCRAM·재시작/변조·철회/rollback·정리로 수용한다.
