# 완료 전체 생장 결과의 API·3D 미리보기

첫 대상은 수용된 합성 166일 부모다. 원 서명 DB backup과 입력/artifact를 복원하고
기존 보호 API·같은 FarmAuthoringService/current query·제품 App을 사용한다.
작물 RHS·행 생성·게시·증명 발급을 조회 경로에서 금지한다.

## 작은 구현 범위

`web/src/cycleCropWindow.ts`, `web/src/CycleCropReplay.tsx`,
`web/src/calculationCycleCropWindow.test.ts`, `web/src/HarvestReplay.tsx`와 이 계약이다.
기존 저장 범위 조작에 원 저장 시점 번호 이동/마지막 시점 이동을 추가한다.
새 레이아웃·UI U1/U3·계산 작업자·모델·API schema는 이 자식의 대상이 아니다.

0 기반 정수 index는 현재 summary의 sample_count 미만이어야 한다.
기존 같은 query/limit·취소/세대/현재 권리 검사를 사용하며 메모리에는 현재 범위만 남긴다.
순서 이동 이력은 요청 성공 뒤에 확정한다. 실패·계정 변경·취소 때 원값/3D를 지운다.
UI 번호는 1 기반이며 원 UTC·수치만 그린다. 저장 시점 사이를 보간하지 않는다.
수확을 선택하지 않은 상태를 명시하며 기존 다른 부모의 수확을 자동 연결하지 않는다.

## 수용 증거

- 집중 window 회귀·타입·제품 빌드. 범위/거부/취소/늦은 응답을 확인한다.
- 원 backup/hash/서명 result ID/최초 저장 시각·같은 실제 SCRAM DB를 유지한다.
- 실제 HTTPS summary·첫/마지막/중간 원 sample·모든 5관리 UTC·bytes/시간을 대사한다.
- 실제 App/WebGL에서 같은 UTC의 C/N 50구획·LAI·표/그래프를 대사한다.
  API 응답/metadata/UTC를 시험용으로 교체하지 않는다.
- 현재 권리/계정 거부와 복원, 조회 RHS/행 생성/게시/증명0,
  원 입력/artifact/backup·기존 미리보기·source·FD/소유 정리를 확인한다.
- WSL 관측 단일512MiB/합1GiB 안에서 제한된 검증을 수행한다.
  검증 전 기존5173을 보존하고, 수용 뒤 별도 실제 기동/접속 안내를 기록한다.

실제 품종·독립 농장 자료·G0–G4와 전체 수확·실시간 진행 U3 수용은 별도다.
