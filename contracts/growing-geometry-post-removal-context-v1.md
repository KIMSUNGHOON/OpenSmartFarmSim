# 제거 후 면적·장부를 보존하는 문맥 — 연구 v1

상태: [82신규/231관련·fresh36문맥 수용](../research/growing-geometry-post-removal-context-20261024.md).
[명시 제거 point](growing-geometry-leaf-removal-point-v1.md) 다음의 문맥/복원 자식이다.
새 문맥은 다음 연속 구간의 준비물이며 이 단계에서 시간을 전진시키지 않는다.
기존 [고정 목록 continuation](crop-growing-geometry-continuation-v1.md)의 checkpoint를 새 길이로 위조하지 않는다.
첫 사건·양의 잔여 수관과 연속 C/용량 유출0의 합성 범위만 지원한다. 원32초/nonzero 유출 결과와 기존 UI는 유지한다.

## 공개 호출과 권위

- `prepare_context(*, parent_context, raw_parent_checkpoint, expected_parent_sha256, inputs)`는
  원 context·신뢰한 원 CP bytes/SHA와 명시 제거 입력으로 기존 point를 한 번 검증/계산한다.
  임의로 재해시한 point 결과를 수용하는 인자는 없다. 원 현재 CP에서만 차감하므로 사건 후 상태를 다시 차감하지 않는다.
- 남은 원 잎 메타데이터와 현재 a/A·기관/기후 상태를 원 순서대로 결속하고 새 explicit-LAI RHS를 한 번 평가한다.
  point의 원 CP 복원 RHS1회와 사건 후 RHS1회만 허용한다. 초기 정규화·과거 replay/적분·시간 전진0이다.
  사건 자체는 통과해도 사건 후 연속 RHS의 적용영역을 벗어나면 새 문맥을 반환하지 않는다.
- `snapshot(context)`, `checkpoint_bytes(context,checkpoint)`,
  `restore_checkpoint(context,raw_bytes,*,expected_sha256)`는 불변 typed handle·코드/profile/environment/bytes를 검증한다.
  복원은 이 문맥이 만든 최초 사건 후 checkpoint와 모든 bytes가 같아야 한다. 생장/point/RHS 계산0이다.

context는 frozen dataclass와 immutable bytes다. 외부 JSON/다른 model handle은 거부하고 모든 JSON view는 복사본이다.
입력/caller의 parent/profile은 수정하지 않는다. 이 Python 경계는 실제 farm 권한/서명 custody나 악성 in-process 코드의 격리를 제공하지 않는다.
외부 bytes의 기대 SHA는 신뢰한 호출자가 보관하며 임의 재해시를 승인된 이력으로 해석하지 않는다.

## 보존하는 내용

manifest/root는 새 모델/코드·point/parent 모델과4profile/환경, 원 request/program/seed·parent CP/point 입력·결과 SHA,
새 active program/seed bytes와 원 격자/사건 index·남은 step·state layout을 고정한다.
현재 footprint/k·정책/forcing을 바꾸지 않는다. 원 program의 initial_area와 curve는 원 메타데이터로 유지한다.
이 값으로 현재 A를 다시 초기화하지 않는다. 남은 ID와 원 전체 목록의 index mapping을 저장한다.

최초 checkpoint는 phase=`after_removal_before_next_step`, segment_step_index=0,
원 global step index/elapsed와 정확 Fraction 경과 초를 가진다. 새 UTC/가짜 시간 이동은 없다.
last_confirmed의 현재 a/A·다른 C/N·기후/단위는 point 이후 상태와 같다.
남은 잎의 D0는 원 seed의 동일 index에서 선택하고 원 전체 D0/초기 영수증과 제거 마지막 상태도 보존한다.
사건 전21개 누적량과 사건의 C/용량/signed 현열은 별도 장부이며 새 segment의21개 누적량은 명시0이다.
원 총량을0으로 바꾸거나 사건 유출을 과거 구간에 다시 더하지 않는다.

context의 새 bytes 합은2MiB, checkpoint는256KiB 이하·원512잎/600초/32,768 sample scalar 한도를 유지한다.
남은 horizon이0인 사건 후 snapshot은 저장할 수 있지만 다음 걸음 지원으로 표시하지 않는다.
복원/조회는 DB·CLI/network/쓰기0이며 새 서비스를 추가하지 않는다.

수용은 합성6조건의 초기/중간/완료·분수 dt·한 잎/동시 제거, 실제 원 a/A/D0와 모든 과거/사건/새0 장부의 대사,
현재 A와 canonical curve의 미세 차이를 보존하는 복원·재초기화/시간 전진 차단·동일 bytes,
snapshot view 변경·다른 parent/handle·코드/profile/environment·해시/단위/목록/장부/시각의 rehash 변조·크기/중복/비유한 거부,
기존 point/continuation 회귀·독립 fresh와 원 자료/4root/WSL 보존이다.
scope=`software_research_only`, claim_scope=`synthetic_post_removal_context_only`, G0_G4=`not_assessed`다.
실제 다음 구간/분할 재개·복수 사건·출현/공급·새 불변 저장/3D·전체 작기/생산·자원/경제/추천과 G0–G4/R2는 후속이다.
