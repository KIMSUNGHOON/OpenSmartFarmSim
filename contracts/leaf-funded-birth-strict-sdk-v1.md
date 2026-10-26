# 조달된 새 잎 저장 결과의 브라우저 SDK — 연구 v1

상태: **자체 합성 SDK 수용** — [122검사·실제 HTTP133시점/424파일](../research/leaf-funded-birth-strict-sdk-20261026.md).
[strict export](leaf-funded-birth-export-v1.md)의 새 형식을 읽는다.
기존 stock SDK/고정3잎 형식·원 GUI·제품 API 계약을 바꾸지 않는다.

`loadLeafFundedBirthReplay(scenario,signal)`은 코드에 고정한6조건의 root/index SHA만 신뢰한다.
`readFundedLeafReplay(readFile,anchor,signal)`은 호출자가 별도로 신뢰한 불변 anchor를 요구한다.
다운로드한 index 자체를 신뢰 anchor로 삼지 않는다. `LeafFundedBirthRequest`는 이전 요청을 취소하고
이미 취소된 요청이 뒤늦게 완료되어도 결과를 반환하지 않는다. 원본/공유 mutable cache를 반환하지 않는다.

닫힌 index/root/source·권리/notice/코드/profile와 point/frozen context/raw CP/DTO를 결속한다.
UTF8·중복 JSON 키·깊이64·source/index/context/DTO2MiB, CP1MiB·512frame/512leaf·32,768scalar·600초를 검사한다.
sample/state/context/point/history/prefix의 내부 SHA는 원 JSON 부분의 bytes로 확인한다.
Python의 `2.0`, `-0.0`, 지수 표기를 JS로 재직렬화하지 않는다.
곡선 원문 SHA와 초기화의 `rate_model_version` 포함 곡선 identity SHA를 구별한다.

원 step/exact 분수 초·출현 전후 phase·같은 시각의 사건번호/순서를 보존한다.
가변 ID/C_i/a/A·원 생성 영수증/시계와 C 기준·point/segment/lifetime 장부·기록 QC를 검사하고
원 DTO의 분리된 복사본을 반환한다. 생장 계산/보간·면적→질량·줄기 위치/키/과실/수확 추정을 하지 않는다.
초기 attachment는 `separate_authored_asset_required`, 새 잎은 `declared_not_bound`로 유지한다.

수용: 원6조건114frame/324파일, 실제 producer의1→2/512/fractional/같은 시각 경계19frame/100파일,
모든54종 wire 변조·재해시 index/원 DTO 의미/단위·QC·권리 거부, abort/latest request/분리된 결과,
전체 웹 타입과 독립 번들·원424파일의 HTTP 조회를 대사한다. 비공개132blob·기존 화면/자료·WSL 한계를 유지한다.
실제 품종/관측·G0–G4/R2·원 clock/줄기 부착 결속·같은 상태의 새 잎3D/제품 통합은 후속이다.
