# 새 기관 전후 저장3D 화면 v1

상태: [17집중·전체/설정 타입·실제 Chrome](../research/supply-material-stored-screen-20261031.md)의 기능 수용.
[strict SDK](supply-material-http-replay-v1.md)가 검증한4frame만 사용한다.
새 frame이나 생장 상태를 브라우저에서 계산하지 않는다.

선택 index/원점 UTC·정확 분수 초/phase/ID/부모는 SDK 원 값을 유지한다.
`material_before`, `material_after`, `original_grid_endpoint`, `declared_end`를 구분하고
같은 정확 시각의 채택 전후를 다른 frame으로 선택한다. before는 dense-before이고 checkpoint가 아니다.
새 phase를 이전 CP의 phase로 바꾸어 기존 renderer에 넘기지 않는다.

새 version의 layout/mesh/scene은 기존의 실제 잎·절간 geometry·질감/조명을 재사용한다.
원 m²의 단면 잎 면적과 m의 절간 길이/부모 관계를 mesh에 결속한다.0치수는 늘리지 않는다.
초기 미연결 잎은 별도 표시 원점에 놓고 없는 부모를 만들지 않는다. 새 잎의 초기 면적도 원 저장값이다.
소엽 형태·방향/굵기·직선 축·독립 뿌리/미연결 표시 위치·재질/조명은 제작 표시 규칙이다.
계산 길이 합계를 실제 작물 키로, 이 합성 시계를 관측 출현 시각으로 게시하지 않는다.

원본 표·시계/수지와 선택/그래프/3D는 같은 frame을 가리킨다. 저장 순서 그래프는 시간 비례 축이 아니다.
재생은 원4frame을 순서대로 선택하고 끝에서 멈추며 숨김/해제·유휴에 상시 렌더링하지 않는다.
카메라 회전/확대·초기화와 연결/미연결/전체 보기,390px 모바일과 WebGL 보류의 원 표를 제공한다.

root별 별도 selection key와 URL에 index/view/panel만 저장한다. 메뉴 이동/새로고침은 이를 유지한다.
source/권리/hash 검증 실패나 재조회 시작 때 이전 canvas/표/그래프를 제거하고 복구 버튼을 제공한다.
정상 경로는 GET만 사용하며 외부 network/API/DB/worker/CLI를 호출하지 않는다.

별도237파일의 고정 public 미리보기는 원 파일 hash/bytes·허용 경로·첫 유효기간으로 제공한다.
기존 source/DB·키/미리보기와 그 만료를 변경하지 않는다. 이번 공개본은 합성4frame/722좌표·11→12잎이며
실제 품종 한 작기/생산량·에너지 구매/매출·수익/자율 추천, G0–G4/R2는 별도 수용이다.
