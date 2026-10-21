# 사실적인 작물 외형: 사용자 정정과 첫 구현

상태: 2026-10-21, 첫 외형 확인본 제공. 사실적 시각 품질과 저장 생장 연결은 미완료다.
기존 수치 모식도는 사용자가 요구한 사실적 작물 3D의 완료 증거가 아니다.
제품 요구는 [명세 §5.4a](../docs/PROJECT_SPEC.md#54a-사실적인-작물-3d--2026-10-21-사용자-정정),
진행 순서/미수용 작업은 [계획](../tasks/plan.md#사실적인-작물-3d-우선-수정--2026-10-21)과
[todo](../tasks/todo.md)에 고정했다.

## 판단 주체와 범위

현재 native Codex CLI 세션의 2026-10-21T09:10:52.921Z turn context를 직접 확인했다.
model=`gpt-6.1-sol`, effort=`xhigh`, 원 context line SHA-256=
`e8ed59551dd468f185755c59964e19a60898e68acd8bb34693f670b257c1d436`.
이 세션의 도구 실행/작성 코드가 실제 출력이며 CLI를 재귀 실행하지 않았다.
새 도메인 계수·품종 프로필·관문 승인을 만들지 않았다.

첫 구현은 기존 `three@0.186.1`을 쓰는 별도 정적 진입점 `web/crop-appearance.html`이다.
기존 계산 서비스/DB/키와 원 UI를 변경하지 않는다. 줄기/곡선 가지, 복엽의 잎맥과 굴곡/가장자리,
꽃받침/송이 과실의 입체 표면, 환경광/그림자와 회전/전체/과실/잎 카메라를 직접 작성했다.
텍스처도 결정적 코드로 제작했다. 외부 사진/3D 모델/HDR 파일을 다운로드하거나 배포하지 않는다.
새 패키지·엔진·에이전트 프레임워크 의존성은 추가하지 않았다.

## 근거와 권리

아래 페이지는 2026-10-21에 현재 세션에서 조회했다. 참고 설명을 검토했으며 원문 이미지나
표를 제품 자산/작물 입력으로 채택하지 않았다. 따라서 외부 이미지의 재배포 권리를 주장하지 않는다.
기관 개수/간격/색/크기·온실 배치는 직접 작성한 **대표 외형의 제작 가정**이다.
이 모델을 Axiany 등 특정 품종의 계측 형태로 부르지 않는다.

- [NC State Extension: Solanum lycopersicum](https://plants.ces.ncsu.edu/plants/solanum-lycopersicum/):
  복엽/잎 가장자리·줄기·과실의 종 수준 외형을 확인한 참고다. 국내 생장·품종 보정 자료가 아니다.
- [Three.js MeshPhysicalMaterial](https://threejs.org/docs/pages/MeshPhysicalMaterial.html):
  표면 반사/거칠기·환경 맵과 기능별 렌더링 비용을 확인했다. 필요한 표면 기능만 사용한다.
- [Three.js WebGLRenderer](https://threejs.org/docs/pages/WebGLRenderer.html):
  WebGL2, 출력 색 공간·톤 매핑과 자원 정보/그림자 설정을 확인했다.

소스 코드·직접 제작 표면은 저장소 Apache-2.0 범위다. 기존 Three.js(MIT), 자체 호스팅 Noto Sans KR(OFL)
고지는 기존 `web/public/licenses/`를 그대로 제공한다. 모델과 텍스처의 버전은
`authored-tomato-appearance-v1`이며 화면에서 생장 계산 연결 전의 외형 연구임을 밝힌다.

## 디자인 도구 관측

`12ui-design`의 draft를 4후보로 한 번 호출했다. 참조 검색이
`Corpus inspiration response is ambiguous`로 실패했고, 제시된 동일 검색 resume도 같은 오류로 종료했다.
`next --json`은 `draft error`, 실행 없음/산출 이미지 없음을 확인했다.
승인 시안·디자인 일치/close 수용을 주장하지 않는다. 기존 UI의 한국어 서체·색/조작 관례를
재사용하고 이번 핵심인 실제 3D 형상을 구현했다. 생성 이미지로 WebGL 렌더링을 대체하지 않았다.

## 검증과 남은 수용

hosted 집중 검증은 타입·기하의 유한값/곡면·정리·빌드·보안 감사와 **빌드된 정적 결과의 실제 Chromium**을 확인한다.
브라우저에서는 전체/과실/잎 렌더링·회전 전후 이미지 차이·모바일·WebGL 불가,
API 요청/임의 생장 슬라이더 없음·오류 없음과 캡처를 확인한다.
아래에 CI 결과와 실제 로컬 화면 확인을 기록한다. 기존 전체 웹 회귀·수치/DB 검증을 새로 수용한 것으로 세지 않는다.

### 실제 결과

[source87cb0ec / CI39578040554](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/39578040554)의
타입·기하3검사·빌드된 정적 결과 Chromium3검사·빌드·audit0을 확인했다.
첫 CI39576719391의 테스트 `this` 타입 오류, 초기 시각 검토의 과실 겹침/과한 하이라이트,
첫 native의 favicon404를 수정했다. 과실은 별도 보수적 bounding sphere 분리 검사도 수행한다.
실패/수정과 최종 원본 hash는 [공개 증거](artifacts/realistic-crop-appearance-20261021.json)에 기록했다.

같은 source의 정적137파일을 실제 HTTP 바이트/SHA-256으로 대사하고
[확인용 주소](http://localhost:5175/crop-appearance.html)를 별도 정적 서버로 제공했다.
Windows의 전용 Chrome에서 직접 전체/과실/잎을 전환·표시했고 JavaScript/console 오류0,
API 요청0과 3초 유휴 중 frame4→4를 확인했다. 관측 첫 표시는 같은 세션에서0.557초였으며
일반 기기 성능 약속이나 냉시작 수용으로 사용하지 않는다. 창은 확인할 수 있게 열어 두었다.

실제 캡처: [전체](artifacts/tomato-appearance-native-plant-20261021.png),
[과실](artifacts/tomato-appearance-native-truss-20261021.png),
[잎](artifacts/tomato-appearance-native-leaf-20261021.png).
이번 검사는 6.710초·.25초26관측, WSL 합산 peak919,973,888bytes/PID139,603,968bytes였다.
기존 보호5root와 두 기존 화면200을 확인했고 backend/기존 UI·DB를 변경하지 않았다.
Windows Chrome/Node 메모리는 이 WSL 관측에 포함되지 않으므로 공통 용량/전체 부하 수용을 주장하지 않는다.
큰 로컬 빌드/Chromium 회귀를 WSL에서 실행하지 않았다. 첫 정적 서버만 소유 identity/pidfd로 교체했다.
새5175의 추가 RSS도 이후 관측에 포함하도록 handoff의 보호 대상은 기존5+정적 뷰어1의6root로 갱신했다.
상한은 유지한다. 전용 Chrome에서 중복으로 연 확인 탭 하나만 닫고 기존5174 시연과 최종 외형 탭을 유지했다.

현재 화면은 형태·카메라·재질의 1차 구현이다. 잎/줄기 접속·표면 미세 디테일·조명/온실 장면의
현실감은 더 개선할 수 있으며 사진 수준 완성으로 채택하지 않았다. 품종/시기별 외형 사진·측정의
사용/표시/배포 근거, 시기별 형태와 현재 저장 출력의 대응은 외부/후속 의존성이다.
외형 제작과 독립 농장 자료 확보는 병행한다. 기존 전체 goal은 paused이며 이 사용자 정정의 범위만 실행했다.

자동 검증 통과는 사실적 외형의 최종 품질 수용이 아니다. 캡처를 검토해 잎/과실/줄기 연결과
표면·조명의 부족한 부분을 개선한다. G0–G4는 변경하지 않는다. 다음은 외형 품질 확정/권리와
시기별 형태 근거 → 저장 상태 대응 → 같은 실행/UTC의 계산 기반 성장 → 자원/경제 연결이다.
특정 품종의 기관 수·실제 키·숙기·수확량을 추정해 만드는 타임라인은 포함하지 않는다.
