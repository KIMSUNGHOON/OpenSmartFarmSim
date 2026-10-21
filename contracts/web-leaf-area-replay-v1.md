# 저장된 잎 면적과 같은 UTC의 제작 3D — 연구 v1

상태: [자체 합성 저장/같은 UTC3D 수용](../research/leaf-area-stored-replay-20261022.md). [불변 잎·줄기 결과](crop-leaf-area-artifact-v1.md)의 public17파일만 읽는 별도 화면이다.
원 farm/job API·기존5176/다른 화면은 유지한다. 새로운 실제 품종/관문·생산/수익/작물 선정 수용이 아니다.

- SDK는 고정 root/index의 원 bytes SHA, 입력/원 stem root/input·각 frame bytes와 닫힌 모델/단위·선언 ID/원 UTC를 검증한다.
  불일치/중단/부족한 파일에는 데이터/geometry를 대신 생성하지 않는다. GET만 사용하고 재계산하지 않는다.
- 원 stem DTO의 미터 길이·분수 출현은 유지하고 각 선언 leaf의 attachment ID에서 제작 geometry를 배치한다.
  계산 면적(m2)을 단면 leaflet 삼각형 면적과 대사한다. 실제 instance/world 행렬의 측정 면적 오차는 relative1e-9 이내다.
  petiole/rachis는 대상에서 제외하며 길이/폭·소엽 수·각도/반경/표면은 제작 가정임을 밝힌다.
  이는 원 관측의 면적 정의나 품종 형태를 검증했다는 의미가 아니다.
- 같은 UTC/root/result/leaf ID·원 면적을 실제 mesh/표/그래프에 연결하고, 저장12시점만 재생한다.
  첫/끝/선택·정지/유휴·모바일과 WebGL 불가 때 원 표를 확인한다. 잎 수는 초기 선언이며 예측이 아니다.
- 기본 인자가 없는 기존 줄기 geometry/화면은 같은 모습·ID/길이·고정 제작 잎과 정리를 유지한다.
  잘못된 새 leaf binding은 기존 제작 잎으로 대체하지 않는다.

집중 unit·타입/build/audit·기존 외형/형태/실행 browser 회귀와 새 화면을 hosted에서 확인한다.
현재 WSL에서는 큰 Node/Chromium 빌드를 겹치지 않고 원7root를 포함한 감시 아래 정적 적용/전용 Chrome을 검증한다.
실제 캡처/원17파일 HTTP와 원 화면/파일 보존 뒤 체크한다. 최종 사실감 R2·새 잎/관리·한 작기/실제 품종 검증은 후속이다.
