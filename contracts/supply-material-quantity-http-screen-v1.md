# 같은 material 저장 상태의 수량·자원 HTTP/3D 계약 v1

`supply-material-quantity-http-replay-v1`은 [수치 조회](supply-material-quantity-window-v1.md)의
자체 공개 QA 결과와 [material 공개 재생](supply-material-public-replay-v1.md)을 결속한다.
새 계산·농장 API·예측·추천 계약이 아니다. 원 결과/코드·입력과 이전 화면은 불변이다.

## 입력과 검증

- 원 model `own-public-v1`의106파일/13,985,230bytes와 수량 `own-public-v1/quantities.json`
  59,468bytes를 사용한다. 수량 파일은 저장된 공개 fixture와 동일 bytes다.
- 수량 fixture SHA `21010f126c84ee9964643374c0565ecf0c4f017905276483a26dc562ca27a260`,
  canonical result SHA `ccc1d63a51279017b4b8400d8dfc5cbb59da8b23a7be899858ecb273f2010dbd`
  /40,481bytes, projection code SHA
  `bcece9513506fd8085d6a6f5e1a6fa9015b1e2ca47e372065c4e7a7058e17500`을 고정한다.
- 기존 strict graph reader를 한 번 사용한다. root/index/115 code·권리/NOTICE·원 계보,
 4개 frame의 원 descriptor/state SHA·source cursor·시각/phase와 재배면적을 확인한다.
- UTF-8 오류·중복 key·깊이/비유한 값·미지 필드·권리/단위/지문 변경을 거부한다.
  정수는 정수 lexical 형식이어야 한다. float 원 좌표는 원 Python float lexical 형식을 보존해
  canonical SHA를 검증하고 binary64 값과 대조한다. `JSON.stringify`로 원 float를 정규화하지 않는다.
- 파일별2MiB와 기존 graph 총64MiB 제한을 유지한다. HTTP는 GET, no-store,
  credentials omit, redirect error다. 성공 한 번은107파일/14,044,698bytes다.

## 반환과 산술

`readMaterialQuantityReplay(readFile, signal)`은 `summary()`, `frame(index)`, `window(first,last)`를 반환한다.
모든 반환값은 독립 복사다. `frame`은 같은 원 상태의 `morphology`와 `quantities`다.
수량은50개 과실 발달 구획의 탄수화물·과실 수 상당량, 정확 binary64 합,
10개 lifetime counter와 실제 참조를 보존한다. 8개 열·수분 counter는 원 부호를 유지한다.

구간은 양끝을 포함한다. BigInt 분수로 인접 차와 끝−시작 및 망원합을 대사한다.
한 시점의 합은0이다. 동일 시각 `material_before`→`material_after`는 사건 번호가1 증가하며,
과실 재고와 연속 counter의 차는0이어야 한다. terminal counter는 음수/감소를 거부한다.
브라우저는 생장/RHS·DB·worker·CLI를 실행하지 않는다.

## 화면과 상태

`supply-material-quantities-replay.html`은 기존 `SupplyMaterialScene`을 사용한다.
동일 선택의 잎 면적·절간 길이/부모·phase/정확 시각, 과실 재고2개·50구획,
선택 구간 유출과 열·수분8항목이 함께 바뀐다. 그래프의 가로축은 원4개 저장 순서다.
반올림8자리 표시는 정확 분수/원 float를 대체하지 않는다. 매우 작은 음수도 부호를 보존한다.

메뉴/새로고침은 root와 수량 result SHA에 결속한 index/view/panel/first를 보존한다.
시점을 앞당기면 first≤index로 제한한다. 재검증 시작/실패 때 이전3D·표·그래프를 제거한다.
취소·이전 요청 응답은 현재 결과를 대체하지 않는다. WebGL이 없으면 명시 보류와 검증된 표를 제공한다.
390px에서는 페이지 가로 넘침 없이 표 안에서 스크롤하며, 열·수분8행을 모두 노출한다.

## 주장과 수용

이는 자체 합성4상태의 소프트웨어 연구 재생이다. 개별 실제 과실·생과kg·수확·관개량·구매 전력/연료·
청구액·매출·마진·작물 순위로 환산하지 않는다. 제작 잎 형태/자세/조명은 예측 변수가 아니다.
G0–G4 `not_assessed`, R2 `not_approved`, 전체 목표 미완료를 유지한다.

수용은 strict/부정 입력·정확 산술·복사·취소/latest 검사, 전체/설정 타입,
실제 HTTP, 실제 Chrome의4시점 mesh/수량/시각 대사·메뉴/reload·모바일·오류 복구·유휴,
기존 불변 자료/GUI·WSL 보존을 요구한다. [실제 결과](../research/supply-material-quantity-screen-20261031.md).
