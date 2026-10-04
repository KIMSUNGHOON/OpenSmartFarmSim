# 과실 순간 이동의 필수 프로필 포장 — 2026-10-05 KST

상태: **최소 변경 구현·로컬 loader/정적 검사 완료; hosted 실제 이미지 수용 대기**.
`crop-fruit-transport-image-inputs`를 완료로 체크하지 않는다.

## 구체적 기능 의존성과 변경

[순간 이동](crop-fruit-transport-implementation.md)의 고정 프로필은 기존
`.dockerignore`의 `fixtures/**`에서 제외된다. 새 계산을 이미지에서 호출하려면
이 파일이 필요하다. [운영 기반 고정](crop-priority-and-runtime-freeze-20261004.md)에
대한 예외는 이 실제 입력 공백의 보완이다.

계획대로 다음 3파일만 변경했다.

- `.dockerignore`: `crop-fruit-transport-reference-parameters-v1.json` 한 파일을 허용한다.
- `scripts/check-application-images.py`: 실제 export context의 프로필 hash 일치와
  독립 시험 cases 제외를 검사한다. backend의 기존 UID/GID 11001/11010·읽기 전용
  probe에서 `ReferenceFruitTransportParameters`로 실제 bytes를 읽어 pinned hash/
  profile ID·50구획을 확인한다. context event에 검사한 공개 profile hash를 기록한다.
- 이 보고서: 변경 근거와 현재 검증 범위·다음 수용 증거를 기록한다.

기존 Dockerfile의 선언된 `fixtures/*.json` 복사를 사용한다. 파일/디렉터리 일반
허용, 새 이미지 target·서비스·의존성·인증 흐름은 추가하지 않는다.
독립 참조 cases와 17개 private/미선언 probe, 원문 PDF/연구 자료는 계속 제외된다.
원 프로필 hash는
`09ea5e176bc745361e8e3ec8945b0f8abb0b2b427b4e9c459d0663cf390e9070`이다.

## 검증과 남은 수용

로컬에서는 실제 pinned bytes의 profile ID/구획 수/매개변수 로드와 이미지 검사
스크립트·내부 backend probe의 Python AST를 확인했다. 변경은 정확한 한 파일
예외와 검사에 한정하며 `git diff --check`를 통과했다.
이 loader/정적 검사는 Docker ignore 처리나 실제 image 실행을 대신하지 않는다.

현재 WSL2에는 Docker Engine이 없으므로 이미지/Compose는 로컬에서 실행하지 않았다.
다음 의미 있는 코드 판본의 기존 Application runtime verification에서 실제 Docker
context/hash·새 cases 제외·읽기 전용 loader·UID/TLS·image/세 Compose 정리 증거가
모두 확인된 뒤 이 작업의 실제 수용과 checkbox를 갱신한다.
이 패키징은 전체 작기·착과/배분·수확이나 G0–G4 관문을 열지 않는다.
