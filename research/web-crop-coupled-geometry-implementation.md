# 50구획 저장 수치 도형의 로컬 수용

2026-10-05 KST. [도형 계약](../contracts/web-crop-coupled-geometry-v1.md),
[실제 영수증/두 코드 해시](artifacts/web-crop-coupled-geometry-reference-20261005.json).
현재 CLI gpt-6.1-sol / xhigh(22:05:49.804Z turn)에서 설계·구현했다. 재귀 CLI는 없다.
이 수용은 CPU Three.js 도형이며 실제 WebGL/화면·품종 생산 검증이 아니다.

## 구현과 검증

`coupledCropGeometry.ts`/시험 각 한 파일을 추가했다. saved sample 전체에서 50개
C와 50개 N의 별도 공통 최대를 고정하고, 각 값을 그 단위의 최대에 대한 높이로 표시한다.
서로 다른 단위를 합치거나 과실 형태·숙기·생과 kg·수확량을 만들지 않는다.
100개 mesh가 한 BoxGeometry를 공유하고 material은 호출자 소유다.
기존 canopy의 논리 바닥 1 m²·triangle 면적 구현은 그대로 재사용한다.

영 값은 숨긴 0높이다. 잘못된 단위/50길이·negative/NaN/Infinity/최대,
JS 또는 GPU float32 양수 underflow를 거부한다. 임의 epsilon/최소 높이는 없다.
두 배열의 비율을 먼저 모두 검사해 실패한 갱신이 이전 확인 도형을 부분 변경하지 않는다.
공유 geometry 한 개의 idempotent dispose·parent 분리와 material 소유를 확인했다.

새 모듈 부재의 실제 Vitest RED(exit 1) 뒤 **103 passed/0 failed**다.
새 도형 17개, 기존 잎 triangle/기관 막대 13개·새 페이지 73개를 한 worker로 실행했다.
실제 Three.js mesh의 world-coordinate 상단–하단 높이와 구획 index/원 값/단위,
두 시점/반복 전환·매우 큰 finite 값·0/underflow·실패/정리를 대사했다.

```bash
cd web
nice -n 10 npm test -- --maxWorkers=1 src/coupledCropGeometry.test.ts src/cropGeometry.test.ts src/coupledCropReplay.test.ts
npm run typecheck
```

이전 실제 HTTPS 공개 합성 bytes의 **512시점·51,200개 C/N 수치**를 새 CPU mesh에
연결하는 별도 시험 **1개**도 통과했다. 각 slot의 높이×공통 최대와 원 값을
max(1e-9, 원 값×1e-6) 이내로 대사하고, 512개 LAI와 실제 한 면 triangle 면적도
max(1e-8, LAI×1e-6) 이내로 대사했다. 관측 최대 오차의 console 값은 영수증에
보존되지 않아 숫자를 보고하지 않는다. 허용 범위와 시험 통과만 기록한다.
임시 시험은 제거했고 새 서버/브라우저 요청으로 세지 않는다.

타입 검사도 통과했다. 한 Node worker를 순차 사용했고 DB·브라우저·Docker·새 패키지는 없다.
raw 프로그램/credentials/현장 자료를 추가하지 않았다.

## 다음 경계

페이지 조립과 수치 도형의 자식 두 개는 수용했다. 다음은 기존 React 화면의
판본/결과 선택 → 표·그래프·3D의 단일 UTC → 취소/권리 철회/과거 hold·접근성 →
디자인 정합/실제 SCRAM·TLS·브라우저 대사다. 부모 `web-crop-coupled-replay`는 미완료다.
기존 2–4시간 잠정 창에서 앞의 두 묶음을 완료했으며, 잔여 화면/실제 브라우저는
기존 v1 장면의 약 52분 실적과 새 50배열/페이지를 근거로 **집중 1–3시간**을 잠정 배정한다.
로컬 연구 장면 목표는 2026-10-05~06 KST이며 실제 검증 뒤 확정한다.
국내 독립 자료/채택 forcing/실제 Run 0개·전체 작기/startup·생과/자원/경제,
G0–G4 hold는 그대로다.
