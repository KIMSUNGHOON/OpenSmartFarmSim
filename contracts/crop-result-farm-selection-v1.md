# 저장 결과 선택을 위한 등록 작물 조회 v1

U1의 빠진 의존성이다. 기존 작성 농장 목록/요약은 등록 hash를 제공하지만 작물 ID·이름을
제공하지 않는다. 결과 목록에는 crop_id가 필수이므로 이 조회 없이 사용자가 ID를 추측해야 한다.
기존 metadata 목록/현재 등록 검사를 재사용하며 DB 표·role·queue·작물 계산은 추가하지 않는다.

핵심5파일: 이 계약, `backend/app/crop_result_catalog.py`, `backend/app/api_crop_result_catalog.py`,
각 기존 집중 시험 파일. OpenAPI inventory/snapshot, 기존 수동 SCRAM/HTTPS harness와 증거는 지원 파일이다.

## 계약

- `GET /v1/crop-research-result-catalog/farm-crops`, operation `getCropResearchFarmSelection`.
  현재 Bearer/작물 READ_SCOPES 전부, 닫힌 query3필드 scenario_id/scenario_revision/registration_sha256,
  빈 GET body를 요구한다. tenant는 인증 주체에서만 읽는다.
- 같은 현재 query/farm graph에서 등록 입력·현재 자료/표시권을 다시 읽는다.
  닫힌 응답은 `version=crop-research-farm-selection-v1`, `scope=registered_user_inputs_only`,
  farm3필드, items≤32, `selection_validation_required=true`, `rights_or_gate_approval=false`다.
- 항목은 원 crop_id/batch_id·species/variety·UTC occupancy, 원 profile_status=unavailable,
  origin=user/evidence_level=assumed만 표시한다. crop_id 오름차순·고유성을 유지한다.
  이름·달력·계수를 추측하거나 등록 의도를 검증된 작물로 표시하지 않는다. 빈 목록도200이다.
- 64KiB/no-store/코드 판본 header를 유지한다. 초과하면 truncate하지 않고 hold다.
  bytes 투영 전후 같은 등록·권리를 재검사하고 응답 직전 현재 tenant/scope를 확인한다.
  401/403/422/503과 기존 안전 오류 envelope를 사용한다.
- 등록 선택 metadata이며 결과 존재나 파일/수치·관문 승인을 뜻하지 않는다.
  이후 crop별 결과 목록과 선택 결과 query의 현재 검사도 유지한다.

## 다음 한 단계 수용

1. 두 이름의 Unicode·원 ID/UTC·빈/최대32·고유/순서·닫힌 query/typed DTO/bytes,
   다른 tenant/등록·철회/투영 뒤 변경·현재 주체·미구성을 집중 시험하고 기존 목록/OpenAPI를 보존한다.
2. 별도 소유 SCRAM 복원 DB/실제 HTTPS에서 현재 원 농장의 작물 metadata를 대사하고,
   잘못된 hash/타 계정·현재 권리 실패와 bytes/시간·조회 값/RHS/게시0을 기록한다.
   원 입력/서명/계산 중인 producer·미리보기/기존 배포 파일을 유지하고 소유 자원을 정리한다.
3. 실제 원 종료와 증거가 있을 때만 이 조회를 수용한다. 웹 SDK·선택 화면·실시간·실제 작물 관문은 별도다.

이 서버 계약을 고정하면 화면 설계는 준비할 수 있다. 실제 UI 게시 수용은 이 조회와 목록 SDK의
수용 뒤에 진행하며 기존 U1·U3를 완료 처리하지 않는다.
