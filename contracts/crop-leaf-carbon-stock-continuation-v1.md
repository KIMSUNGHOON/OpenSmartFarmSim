# 현재 개별 탄소·나이·면적을 보존하는 분할 재개 — 연구 v1

상태: **고정 목록의 합성 재개 수용** — [138신규/297관련·별도6context/18checkpoint](../research/crop-leaf-carbon-stock-continuation-20261025.md). [짧은 적분](crop-leaf-carbon-stock-dynamics-v1.md)의 같은 식/격자/한계를 사용한다.
현재107+3n상태와21+3n누적량을 복원하며 aggregate leaf를 따로 적분하거나 현재 A/C_i를 초기값으로 재맞추지 않는다.
명시된 고정 잎 목록·합성 elapsed 구간이며 조달된 출현/농장 UTC·관측 검증·예측/추천을 발급하지 않는다.

## 불변 경계

- `prepare_context(program=...,step_seconds=...,step_count=...,**profiles)`는 처음에만 정규화·초기 RHS를 계산한다.
  원 요청/정규 program/seed(state·초기 면적 영수증·첫 RHS/D0)/manifest를 각각 canonical immutable bytes로 고정한다.
  manifest는 새 engine/schema/정책·원 short/component code·4profile/float 환경·dt/count/단위·ID/layout/유량 단위를 결속한다.
  Context는 frozen typed handle이며 `.program`은 원 요청의 복사본이다. context합2MiB/원600초·32,768scalar 한계를 유지한다.
- `start(context)`는 초기 확정 sample과0장부/prefix checkpoint를 만들며 추가 RHS0이다.
- `advance_chunk(context,checkpoint,step_budget)`는 정수1–128걸음을 전진한다. 현재 endpoint 검증1회 뒤 걸음당 새4stage다.
- `checkpoint_bytes(context,checkpoint)`는 같은 context의 immutable bytes를 준다.
- `restore_checkpoint(context,raw_bytes,expected_sha256=...)`는 **외부가 신뢰하는 원 bytes SHA**를 필수로 받는다.
  다른 프로세스는 원 요청/같은 code/profile/환경으로 같은 context를 먼저 만들고 현재 checkpoint를 복원한다.

checkpoint는 새 version/context SHA·step_index·cursor=index+1·sample별 prefix SHA,
현재 last_confirmed sample·모든 global/perleaf 누적량과 원 seed 대비 잔차/예산을 닫힌 canonical JSON으로 보존한다.
512잎의 개별 장부를 위해 checkpoint 상한은512KiB다. 서명/영속 게시·자료/관문 승인은 제공하지 않는다.
과거 sample은 재계산하지 않고 신뢰한 prefix를 보존한다. hash 재계산만으로 진본을 증명하지 않으며
후속 서버의 권한 있는 불변 저장/서명 경로가 expected SHA를 공급해야 한다. Python 내부 필드 재작성 공격의 보안 경계가 아니다.

## 검증·재개와 실패

비유한/중복 key/잘못된 UTF-8·비canonical/누락/여분·다른 schema/context/격자·벡터 길이/float 타입·유량 단위/시각,
현재 C_i/a/A/기후 domain·파생량/D−D0/장부·반올림 예산 불일치를 거부한다. code/profile/환경의 현재 판본도 검사한다.
복원/전진 검증은 같은 short의 현재 RHS1회와 순수 sample/장부 helper를 사용하며 초기 `_prepare`/과거 전진0이다.
현재 A는 F(age)와의 차이를 가진 채 복원한다. 원 D0·ID/순서/분모·초기 영수증은 고정 seed/program에 묶인다.
동일 격자의 원 short와 모든 수용한 분할에서 sample/상태/누적량·잔차/예산이 bit 단위로 같아야 한다.
chunk크기/실행 시각/복원 횟수는 payload identity에 넣지 않아 최종 checkpoint bytes도 분할과 무관해야 한다.

입력/context/checkpoint/budget 오류는 `ContinuationRejected`이며 전진0이다. 완료 checkpoint는 복원/조회 가능하나 재전진은 거부한다.
수치/domain/장부/부분 단계 실패는 `hold`·실패 step/stage·마지막 확정 sample/장부·checkpoint=None을 반환한다.
부분 endpoint나 미확정 checkpoint를 게시하지 않는다. cancel/crash/외부 예외를 정상 hold로 바꾸지 않는다.
DB·CLI/network/쓰기0, scope=`software_research_only`, claim=`synthetic_leaf_carbon_stock_continuation_only`, G0_G4=`not_assessed`다.

## 수용

원6조건의4step 모든 composition과 대표32초 구간의 모든 단일 cut·여러 예산을 원 short와 대사한다.
초기/중간/완료의 trusted digest/canonical roundtrip, 실제 현재 C_i/A/D0·과거 누적량·동일 최종 bytes,
재초기화/과거 재계산 차단·현재 평가 횟수·반환 copy와 malformed/code/profile/환경/단위/시간/한계/실패 prefix를 검증한다.
512잎/512KiB·2MiB/step 상한과 별도 fresh의 같은 context/raw hash·이어 계산, 원4root/자료/WSL 보존을 수용한다.
실제 작기/농장·생산·자원/경제·같은 상태3D와 G0–G4는 별도다.
