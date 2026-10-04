# 50개 C/N 수치 도형 — v1

상태: **로컬 CPU 도형 수용; 화면/WebGL/브라우저 미수용**.
선행은 [웹 페이지 조립](web-crop-coupled-pages-v1.md), 부모는
[같은 저장 시점 연구 3D](web-crop-coupled-replay-v1.md)다.
현재 CLI gpt-6.1-sol / xhigh에서 설계하고 재귀 호출은 없다.

새 geometry/시험 각 한 파일에서 C와 N을 분리한다. 각 단위의 공통 최대는
확인된 saved sample 전체에서 고정하며 양의 값/최대의 비율을 도형 높이로 사용한다.
구획 1–50의 원 순서/단위/수치를 보존한다. 이는 단위 있는 3D 비교 도표이고
실제 과실 크기·숙기·착과 위치/개수나 수확 계산이 아니다.

100개 mesh가 한 unit-height BoxGeometry를 공유한다. C/N material은 호출자가 소유한다.
기존 canopy의 triangle 잎 면적은 별도 재사용한다. 영 값은 숨긴 높이 0이고
최소 높이를 붙이지 않는다. 잘못된 값/길이/단위/최대 또는 JS/GPU float32의
양수 underflow는 도형 불가로 거부해 화면의 표 대체로 연결한다.
모든 비율을 먼저 검증하여 실패 시 이전 도형을 부분 갱신하지 않는다.
dispose는 idempotent이며 공유 geometry 한 개를 해제하고 material을 해제하지 않는다.

수용은 실제 Three.js world-coordinate 높이·slot/unit/value, 공통 척도/반복 갱신,
0/매우 큰 finite 값·잘못된 입력/underflow 거부·원자 갱신/해제다.
[103개 집중·이전 TLS 수치의 CPU 도형 대사 1개](../research/web-crop-coupled-geometry-implementation.md)를
통과했다. 브라우저에서 실제 그려진 결과/카메라/접근성/현재 권리 철회는 부모 단계에서 검증한다.
