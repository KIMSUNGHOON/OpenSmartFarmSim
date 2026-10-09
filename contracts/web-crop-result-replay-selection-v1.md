# 저장 결과 선택에서 기존 재생으로 전달 v1

U1 화면의 선행 자식이다. 선행은 현재 등록 작물/결과 목록 API와 두 웹 SDK의 로컬 수용이다.
핵심5파일: 이 계약, `web/src/SelectedCropReplay.tsx`, `web/src/CycleCropReplay.tsx`,
`web/src/HarvestReplay.tsx`, `web/e2e/selected-crop-replay.spec.ts`.
격리된 컴포넌트 시험용 HTML/TSX harness와 증거는 지원 파일이다.

## 계약과 다음 한 단계 수용

- 선택은 닫힌 kind/farm4/result_id와 수확의 parent_result_id다. 현재 SDK가 반환한 metadata에서
  복사한 불변 선택만 전달한다. 생장은 verified 생장 ID, 수확은 등록 수확 ID와 verified 부모를 요구한다.
  invalid/null 선택 또는 미연결 api는 이전 3D/수확을 제거하며 잘못된 선택을 전송하지 않는다.
- `SelectedCropReplay`는 선택 farm/부모/ID 전체를 key로 기존 calculation-cycle 화면을 연다.
  별도 판본 dropdown이나 수동 ID 복사 없이 같은 farm4의 생장 summary/sample을 현재 query로 읽는다.
  기존 운영자 수동 조회 경로와 공개 DTO·원 수치/UTC는 유지한다.
- 수확 선택은 같은 부모의 생장 조회 뒤 원 수확 ID를 기존 HarvestReplay에 전달해
  summary→bounded page를 한 번 읽는다. 기존 source/hash/farm/UTC 결속 검사를 유지하며
  summary의 부모/farm/source hash가 다르면 page 요청 전에 거부한다.
  부모·권리 실패 시 두 화면을 함께 제거한다. 선택 metadata를 결과 검증으로 대신하지 않는다.
- 외부 초기 ID/선택·계정 변경, null 선택, 취소 뒤 늦은 성공/실패는 이전 값을 복원하지 않는다.
  원 초기 선택의 자동 조회는 한 번이며 관련 없는 rerender/범위 이동에서 중복 접수하지 않는다.
  이후 수동 ID 편집/조회·취소와 페이지 이동의 기존 동작을 보존한다.
- 실제 Chromium에서 선택→같은 UTC/원 C/N·수확 수량/단위, growth-only/harvest의 요청 수,
  invalid/null/변경·현재 권리/부모 불일치·취소/늦은 응답·계정 교체와 페이지 오류를 확인한다.
  기존 생장/수확 브라우저 회귀·전체 웹/타입/빌드와 원 종료·source/자원·소유 정리를 기록한다.
  시험의 metadata/시각을 연결한 합성 fixture는 실제 공동 DB 증거가 아니다.

이 자식은 기존 화면으로의 전달만 수용한다. 농장→작물→결과 목록 UI, 실제 DB/API/재시작과
상위 U1·실시간 U3·일반 운영/실제 작물 관문은 후속이다. 임의 성장 애니메이션을 추가하지 않는다.
