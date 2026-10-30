# 원 저장 상태의 잎·줄기 3D 화면 — 2026-10-31

[수용된 기하](crop-supply-morphology-stored-geometry-20261030.md)와
[HTTP SDK](crop-supply-morphology-http-sdk-20261030.md)를
[연구 화면](../web/src/SupplyMorphologyReplayPage.tsx)에 연결했다.
**같은 합성 저장 상태를 확인하는 화면의 소프트웨어 수용**이다.
새 유한 사용자 preview 적용은 다음 단계다.

공개 원101파일/38시점의 정확 시각·phase·기관 ID와 부모 관계를 보존했다.
한 선택이 실제 잎·줄기 mesh, 원 면적/길이·탄수화물/정확 나이/형상 부족분 표,
원 수지 장부와 저장 순서 그래프를 함께 바꾼다. 중간 성장 상태를 생성하지 않는다.
null 부모/미부착 초기 잎과 길이0 기관은 원 의미를 유지한다.
원 terminal hold, G0–G4 미평가와 R2 미승인을 화면에서 확인할 수 있다.

## 검증

- 집중44검사: 선택/URL/불량·이전 판본 설정16, 고정 환경광/변조·상한·취소6,
  실제 기하13, 기존 HTTP SDK9를 재실행했다.
- 전체 웹 TypeScript와 새 생성 도구/별도 Vite 설정의 타입 검사가 통과했다.
  [공식 단일 스레드 옵션](https://devblogs.microsoft.com/typescript/announcing-typescript-7-0/#single-threaded-mode)을
  사용했으며 strict 설정과 WSL 메모리 상한은 유지했다.
- 실제 Windows 격리 Chrome에서38시점 전부의 면적/길이/ID/부모/0길이·원 at/phase,
  표의 탄수화물/정확 나이/부족분과 원 수지 장부, 그래프 값을 대사했다.
  메뉴/reload·3종 기관 보기·키보드/마우스 회전·카메라 초기화·유휴 렌더 정지·끝 재생,
  모바일390px, 잘못된 자료 제거/재시도와 WebGL 미지원 표 유지가 통과했다.
  이 실행의 실제 브라우저 요청1,411건은 GET뿐이며 오류/경고/외부 페이지 요청은0이었다.
- 별도 지연 응답에서 실제 대기 초와 미검증 화면 제거를 확인했다.
  고정 조명 자산을 변조하면3D가 보류되고 검증된 원본 표는 유지됐다. 오류/경고0이다.
- 새 임시 Chrome 프로필의 직접 CDP 검사에서 visible→hidden→visible과
  같은20번 시점의 정지를 확인했다. 초기 native 창은 이미 hidden이었다.
  visible 양 구간에는 명시 focus emulation을 사용하고, 숨김 구간에서는 해제했다.
  Playwright가 붙은 창의 최소화/다른 탭만으로 hidden이 되지 않은 앞선 시도들은
  통과 수에 포함하지 않는다. 원 프로필과 테스트 창은 종료/삭제했다.
- 저장 원412source/1output, CAS124개·입력 metadata32개·원 false/true 권리,
  동결 GUI 등 보존 사슬과 실행 중5175를 확인했다.
  성공한 검사는 WSL PID512MiB/합산1GiB·600초 상한을 지켰다.
  **Windows Chrome RSS와 전체 호스트 메모리는 측정하지 않았다.**

공개 빌드 명령은 다음과 같다. 기존 출력은 덮어쓰지 않는다.

```sh
node web/build-supply-morphology.mjs /absolute/new/output-directory
```

생성233파일은 검증한 빌드232파일과 동일하고 자체 build manifest만 추가된다.
원101자료와 필요한 글꼴/고지만 포함한다. 일반 제품 UI/서버와 별도 진입점이다.
전체 웹 suite/전체 제품 build·실제 API/worker/DB와 새 전체 CI는 이번에 실행하지 않았다.
수용 전 HEAD61183b22의 GitHub Actions 조회는0건이었다. CI 녹색으로 표시하지 않는다.

## 렌더링과 디자인

실제 브라우저에서 Three.js `PMREMGGXConvolution`의 X4122 경고를 재현했다.
[PMREM](https://threejs.org/docs/pages/PMREMGenerator.html)과
[공식 픽셀 읽기 API](https://threejs.org/docs/pages/WebGLRenderer.html)를 사용해
같은 RoomEnvironment를 미리 생성한 뒤
[DataTexture](https://threejs.org/docs/pages/DataTexture.html)로 읽는다.
원6,291,456bytes의 half-float 조명은 gzip1,194,775bytes이고 두 SHA를 검사한다.
런타임 GGX 생성과 경고 숨김을 사용하지 않는다. 작물 수치/mesh는 바꾸지 않았다.
생성 도구의 첫 채집은 예상 셰이더 경고와 favicon404 때문에 exit1이었다.
그 bytes의 지문/유한값·소비 검사는 별도로 통과했으며 이 채집을 정상 UI 검사로 세지 않는다.
고정 Three.js0.186.1과 MIT 고지를 유지한다. 이 조명은 재배 일사/에너지 자료가 아니다.

12ui-design0.2.65의 실제4시안을 검토하고 C의 생성 레이아웃을 통합했다.
기존 변환에서 동일 LayerDoc을 무료 파생해 실제 화면 PNG와 `improve --target`을 실행했다.
kit을 읽고3아이콘과 레이아웃을 적용한 후 데스크톱/모바일/오류 상태를 직접 비교했다.
이 close는 **이미지 기반 unanchored 계획**이며 DOM coverage/픽셀 일치 수용은 아니다.
사진·임의 그래프 값 대신 사용자 요구인 실제 WebGL/원 저장값을 유지했다.
없는 줄기 두께·품종/수확 사실을 시안에서 가져오지 않았다. 최종 사실감 R2는 미승인이다.

초기 생성 CSS의 고정 zoom 때문에 재확인 버튼을 클릭할 수 없었던 문제를
반응형 컨테이너로 수정했다. Linux Chrome 자원 초과, 타입 오류/용량 종료와
별도 타입 설정의 의존성 경로 오류도 원 기록을 남기고 수정/분리 검증했다.

[실제 데스크톱](artifacts/supply-replay-desktop-20261031.png) ·
[실제 모바일](artifacts/supply-replay-mobile-20261031.png) ·
[원 자료 보류](artifacts/supply-replay-hold-20261031.png) ·
[기계 증거](artifacts/crop-supply-morphology-stored-web-20261031.json)

native 작업 세션의 정확 gpt-6.1-sol/xhigh·출력/코드/검사 지문을 기계 증거에 기록했다.
재귀 CLI·새 모델 계산·DB/worker 실행0이다. 도구의 goal 교체는 미완료 goal 때문에
거부됐으며 기존 전체 goal은 active/incomplete다. 과거10월22일09시 기한을 새 날짜로 바꾸지 않는다.

## 다음 범위

새 빌드의 loopback·유한 소유 preview를 적용하고 실제 주소에서 다시 확인한다.
이 적용은0.5–1집중시간의 계획 범위이며 실제 기동/화면 결과로 갱신한다.
현재 자료는 합성305181/1024초→512초다. 실제 한 품종·한 작기/과실·수확,
생산·자원/Decimal 경제·거시/수급·자율 비교와 제품 통합은 미완료다.
독립 국내 품종/농장 자료0·G0–G4 미평가/R2 미승인과 전체 완료일 미정을 유지한다.
