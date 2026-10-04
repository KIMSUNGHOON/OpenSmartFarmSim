# 과실 구획의 필수 프로필 포장 — 2026-10-05 KST

상태: **로컬 입력/정적 검사 통과; 실제 hosted 이미지 수용 전**.

[순간 구획 계산](crop-fruit-cohort-rates-implementation.md)의 고정 프로필은 기존
Docker 허용 목록에서 제외된다. 실제 앱 이미지에서 이 계산을 사용하기 위한
최소 의존성으로 한 파일 예외와 기존 이미지 검사를 보완했다.
[운영 기반 고정](crop-priority-and-runtime-freeze-20261004.md)의 기능 의존성 조건에 따른다.

변경은 `.dockerignore`, `scripts/check-application-images.py`, 이 보고서다.
`fixtures/crop-fruit-cohort-reference-parameters-v1.json`만 허용하고 기존 Dockerfile의
선언된 복사를 사용한다. 실제 exported context에서 원본과 hash를 대사하며 새
독립 cases가 제외되는지 확인한다. 기존 읽기 전용 backend probe는 실제 bytes로
`ReferenceFruitCohortParameters`를 로드하고 pinned hash·profile ID/50구획을 확인한다.
context/loader event에도 검사한 공개 profile hash를 기록한다.

고정 profile SHA는
`b453b4ffe618f26041e4ec6a1b1b7d2e5f38edb3d42adaaad4fa3cd4fbb99cbb`이다.
새 일반 디렉터리 허용·서비스·dependency나 runtime 권한은 추가하지 않는다.
17개 private/미선언 probe와 기존 UID/TLS·image/Compose 정리는 기존 검사에서 유지한다.

로컬 실제 loader와 검사 script/내부 probe의 AST를 확인했다. WSL2에 Docker Engine이
없어 실제 context/이미지·Compose는 실행하지 않았다. 로컬 로딩/AST는 Docker 수용의
대체 증거가 아니다. 다음 의미 있는 코드 판본의 Application runtime verification에서
context hash·cases 제외·읽기 전용 loader·UID/TLS/정리가 실제 성공한 뒤 체크한다.

이 포장은 시간 적분·생과 수확·실제 품종의 수용이나 G0–G4 게시 관문을 열지 않는다.
