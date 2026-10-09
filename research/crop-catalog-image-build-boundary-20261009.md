# 저장 결과 목록의 이미지 빌드 경계 보완 — 2026-10-09

[실제 hosted 실행37892105777](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/37892105777)은
head `973c57d`에서 backend 이미지를 만든 뒤 web Docker의 `RUN npm run build` 종료1로 실패했다.
`docker build --quiet`의 기록에는 하위 npm 오류가 없으며 **실패 원인은 미확정**이다.
동일 head의 별도 Web CI에서는 타입·단위·일반 제품 빌드가 통과했고 브라우저 검사는 당시 실행 중이었다.

조사 중 [목록 후보](web-crop-result-catalog-screen-candidate-20261009.md)의 원 승인 이미지
`web/src/assets/crop-result-empty.png`가 `.dockerignore`의 명시적 허용 목록에서 빠진 것을 확인했다.
별도 사설 복사본에서 이 이미지를 빼고 같은 Vite 제품 빌드를 실행했다.
원63940의 controller는 예상 실패를 재현하지 못해 종료1, 실제 빌드 자식은 종료0이었다.
Vite는 누락 이미지 URL을 런타임 해석으로 남기는 경고를 냈다. 따라서 이미지 누락을
위 hosted 실패의 원인으로 제시하지 않는다. 이 복사본은 실제 Docker export가 아니다.

정확한 PNG 하나를 허용하고 기존 실제 Docker context export 검사에 원 파일 SHA 대사를 추가했다.
이미지 빌드는 `--progress plain`으로 바꿔 다음 실패에서 공개 source의 실제 npm 오류를 남긴다.
기존 private/credential 제외 범위와 런타임 명령의 비공개 출력 처리는 유지한다.
운영 기반 확대가 아닌 현재 UI의 컨테이너 포장과 실패 진단 보완이다.

[검증 원 기록](artifacts/crop-catalog-image-build-boundary-reference-20261009.json): Python AST 문법,
승인 원 PNG와 선행 수용된 일반 제품 빌드 PNG의 SHA/95,662bytes가 같다.
원63940은 source1,576개·보호4 identity·기존 배포 dist·소유/child0을 보존했다.
표본 단일/합 RSS535,683,072/1,007,849,472bytes로 각512MiB/1GiB 이하다.
0.05초22표본이며 WSL 전체나 운영 용량 수용은 아니다. native CLI 문맥과 출력 hash를 기록했고 재귀 CLI0이다.

로컬 Docker Engine이 없어 실제 export·이미지 빌드와 수정판 hosted 검사는 미실행이다.
기존 CI의 실행 중인 백엔드 검사를 취소하는 추가 push를 하지 않는다.
새 목록 후보의 원 디자인/실제 공동 DB·브라우저 수용·배포와 실시간 U3도 미완료다.
