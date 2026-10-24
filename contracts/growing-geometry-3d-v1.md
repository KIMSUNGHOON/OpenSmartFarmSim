# 저장 면적·기후 결과의 사실적 잎3D — v1

상태: [소프트웨어·실제 Chrome 수용](../research/growing-geometry-3d-20261024.md). [원 결과/SDK](growing-geometry-web-replay-v1.md)의6개 합성32초 프로그램만 표시한다.
`growing-geometry-replay.html`은 원 leaf ID/현재A/열적 나이·기후/LAI·정확 at와 같은 시점의3D/표/그래프를 제공한다.
계산된 면적을 원래 제작한7소엽 표면 삼각형에 대응하며 실제 PBR 잎 재질/잎맥·회전/확대를 제공한다.
처음/이전/다음/마지막·저장 시점 range/재생과 scenario/artifact/frame URL로 같은 선택을 복구한다.
저장하지 않은 중간 상태나 과장한 성장·임의 과실/키를 만들지 않는다.

별도 `authored-three-leaf-scaffold-v1`은 제작 줄기1.6m와 own-leaf-0/1/2의 부착 높이/방향을 선언한다.
이는 그림을 위한 asset이며 계산된 키·줄기 발달/기관 배치가 아니다. 기존24시간 저장 줄기/가짜 MorphologyFrame·지문과 합치지 않는다.
표면과 원 면적의 mapping만 저장 데이터가 결정한다. artist pose는 같은 ID에서 고정하며 leaf ID/목록·수량이 맞지 않으면 거부한다.
원 DTO/artist 선언을 변경하지 않고 renderer는 삼각형 단면 면적의 상대차5e-12 이내를 수용 기준으로 한다.

브라우저는 strict SDK가 모두 통과한 원 결과만 표시한다. 메뉴/새로고침/뒤로 가기·키보드/모바일을 지원한다.
잘못된 URL은 고정한 첫 시점으로 돌아오며, 변조/권리/응답 실패·늦은 이전 요청은 이전3D/값을 남기지 않는다.
WebGL2 불가/상실 때3D를 보류하고 같은 원 표/탐색은 유지한다. 숨김 때 재생을 멈추고 유휴 draw0/RAF·observer·GPU 자원 해제를 검사한다.
새 local API/DB/키·서비스를 만들지 않고 수용 뒤 기존 gateway에 새 정적 entry/판본만 추가한다.

수용은6×17시점/306현재 면적·ID/시각과 원 수량·실제 삼각형의 대사, 표/그래프/URL/메뉴/reload/hold/취소·유휴/모바일,
실제 사용자 Chrome·콘솔·GET/POST0·기존 화면/원 파일/4root·WSL 상한이다. 승인된 기존 디자인과 실제 캡처를 대조한다.
source·geometry/화면 집중 검사·타입/build·브라우저가 통과한 증거 범위만 보고한다.
현재 farm 실행/과학 검증·실제 품종·한 작기/생산/자원·경제/추천과 최종 사실감 R2는 별도다.

기본/전체 보기와 가로↔세로 전환 때 실제 잎 vertex의 투영 경계가 NDC ±0.98 안에 들어오는지 확인한다.
사용자의 의도적인 회전/확대는 별도 조작이다. 저장값/원 면적을 화면 크기에 맞춰 바꾸지 않는다.
실제 창 숨김 검사에서는 Playwright의 기본 focus emulation을 제외하고 실제 document.hidden 전환을 먼저 확인한다.
