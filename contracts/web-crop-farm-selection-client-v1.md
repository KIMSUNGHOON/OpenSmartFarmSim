# 등록 작물 선택 웹 SDK v1

U1의 등록 작물 선택 자식이다. 선행은 [현재 등록 작물 API](crop-result-farm-selection-v1.md)의 로컬 수용이다.
핵심5파일: 이 계약, `web/src/cropFarmSelection.ts`, `web/src/cropFarmSelection.test.ts`,
`web/src/api.ts`, `web/e2e/crop-farm-selection-recorded-responses.json`.
원 응답을 보존한 기존 수동 native harness와 검증 보고서/영수증은 지원 파일이다.

## 계약과 다음 한 단계의 수용 기준

- 기존 createApi의 동일 origin/Bearer·no-store·redirect 거부·AbortSignal을 사용한다.
  닫힌 farm3필드 scenario_id/scenario_revision/registration_sha256로 GET1회만 전송한다.
  query에 crop_id/tenant/token을 넣지 않으며 재시도·prefetch·계산/게이트 승인은 하지 않는다.
  30초/64KiB와 취소 전 무전송·늦은 응답 취소 거부를 유지한다.
- 응답의 version/scope·같은 farm3·최대32·crop_id 고유/오름차순과 닫힌 항목을 검사한다.
  원 ID/이름·품종·UTC6자리 occupancy의 양수 기간, profile_status=unavailable,
  origin=user/evidence_level=assumed와 두 승인 불리언을 보존한다.
  이름은 서버와 같은 Unicode 문자 수1–200/주변 공백·C0 제어 문자 거부를 적용한다.
  빈 목록은 성공이며 결과 존재·검증된 품종·실측/생산 예측으로 표시하지 않는다.
- 요청을 복사하고 대기 중 요청 변경을 거부한다. 반환한 farm/항목/기간은 transport 객체와 분리한다.
  현재 등록 metadata의 선택 후 결과 목록/기존 결과 query의 재검사는 유지한다.
- 실제 소유 SCRAM/HTTPS에서 보존한 성공 원문2개의 SHA/길이·원 metadata를 대사한다.
  변형/빈/32항목·Unicode 경계는 소프트웨어 시험이며 실제 다수 농장 검증으로 표시하지 않는다.
  집중/전체 웹 시험·타입/빌드의 원 종료와 소유 자원·source/기존 preview 보존을 확인한다.
  실패/자원 보류는 남기며 상위 U1·화면·실시간 U3·일반 운영/실제 작물 관문을 완료 처리하지 않는다.

다음은 기존 농장 목록 → 등록 작물 → 저장 결과 선택을 기존 생장3D/수확 조회에 연결하는 화면이다.
12ui-design의 승인 화면/HTML을 기준으로 구현하고 실제 DB/API/브라우저에서 별도로 수용한다.
