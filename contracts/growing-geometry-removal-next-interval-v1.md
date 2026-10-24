# 잎 제거 후 실제 구간·분할 재개 — 연구 v1

상태: [96신규/313관련·독립24조건 수용](../research/growing-geometry-removal-next-interval-20261024.md).
[제거 후 문맥](growing-geometry-post-removal-context-v1.md)의 현재 상태에서 전진한다.
첫 사건/양의 잔여 수관·연속 leaf C/용량 유출0의 명시 합성 범위를 유지한다.
원32초/nonzero 유출 결과·기존 모델/프로필·현재 UI는 바꾸지 않는다. 빈 수관/출현·공급·복수 사건과 전체 작기는 후속이다.

`start(context)`, `checkpoint_bytes(context,checkpoint)`, `restore_checkpoint(context,raw_bytes,*,expected_sha256)`,
`advance_chunk(context,checkpoint,step_budget)`를 제공한다. context는 준비된 post-removal Context다.
새 모델/코드 identity와 같은 context/root를 가진 별도 immutable checkpoint만 수용한다.
기존 parent/post-removal snapshot의 bytes를 새 checkpoint로 위조하지 않는다.
복원/전진 전 검증은 현재 RHS1회이며 초기 면적 정규화/과거 replay·point 재계산0이다. start는 현재 RHS를 새로 계산하지 않는다.

남은 잎 a/A·C/N/기후에서 기존 shared-stage 고정 RK4를 수행한다.
각 걸음은 현재 k1과 k2/k3/k4·endpoint의 새4회 평가와 같은 stage의21개 flux 적분을 쓴다.
원 dt/global index/정확 Fraction 경과 초와 original D0/초기 영수증을 잇고, 현재 A를 curve로 다시 맞추지 않는다.
step_budget은 bool 제외 정수1–128, 원 remaining horizon까지만 진행하며 완료 상태의 재전진은 hold다.
원600초/32,768 scalar·post context2MiB/CP256KiB·응답2MiB의 연구 한도를 유지한다.

checkpoint에는 원21개 누적량, 사건 C/용량/signed 현열, 새 segment21개 누적량을 각각 보존한다.
원 전체 D0/초기 영수증·제거 마지막 상태는 불변 context의 원 bytes에 보존하고 checkpoint에는 각 SHA와 사건 snapshot SHA를 결속한다.
active D0와 현재 상태만 checkpoint에 직접 싣는다. 같은 원 영수증을 반복해CP256KiB를 소진하지 않는다.
새 segment 수지는 기존 `_balances`의64ulp/걸음 정책으로 사건 직후 상태부터 평가한다.
별도로 원 parent seed→현재 상태의 C/N·수관/공기 현열·증기·용량·reduced energy와 남은 각 잎 시계를 검증한다.
과거/새 flux를 한 번씩, 사건의 C/용량/현열 유출을 각각 한 번만 넣는다.
사건에서 바뀌지 않는 과실 N·공기/증기·나이에는 사건 유출/보정0을 사용한다.
이0은 이 명시 사건 모델의 보존 선언이며 실제 물/조직 제거를 측정했다는 뜻이 아니다.

global 수치 예산은 원 checkpoint의 대응 budget+point의 대응 budget(불변량은0)+새 segment budget+
현재 global 원 항 규모64ulp의 합이다. active leaf 시계의 원 budget은 original index로 선택한다.
과거/사건/segment 원 장부나 수치를 예산에 맞추지 않는다. 이는 binary64 회계 기준이며 생물학적 오차 한도가 아니다.

원 context/코드·프로필/환경/원 CP·point SHA·현재 source/목록/단위·격자/상태·21장부/수지·영수증과 prefix를 결속한다.
JSON view는 복사본이다. 외부 expected SHA는 신뢰한 호출자가 보관하며 이 순수 경계는 farm 권한/서명 custody가 아니다.
prefix의 전체 역사 검증은 이후 불변 산출물 계약에 남기며, 조회에서 과거 걸음을 재실행하지 않는다.
동일 원 상태의 전체/분할·여러 예산은 같은 sample/누적량과 최종 checkpoint bytes를 만들어야 한다.

수치/domain/걸음 직렬화 실패는 `status=hold`, 명시 시각/단계/이유·실패 직전 last_confirmed를 반환한다.
실패한 endpoint나 다음 상태는 반환하지 않는다. `checkpoint`는 hold에서None이고 별도 `confirmed_checkpoint`는 마지막 유효 prefix다.
입력/기존 checkpoint·원 source는 변경하지 않으며 DB/CLI/network/파일 쓰기0이다.
호출/원 handle/외부 checkpoint/예산·최종 응답 용량 오류는 예외로 거부하며 부분 결과 게시가 없다.

수용은6조건×초기/중간 사건×한 잎/동시 두 잎, 실제 C/N·열/물·현재 A/나이 전진,
독립 RK4/고정밀 장부·원점 수지와 원 D0·정확 시각/단위, 모든 단일 cut/여러 예산의 같은 bytes,
코드/profile/환경·raw SHA/형상/시각/장부/다른 모델/문맥의 결과 혼용·누락/이중 사건/소진·단계별 실패/경계 거부,
fresh 원 CP 복원/과거 전진0·원 자료/4root/WSL 보존이다. 합성 검증 수를 실제 농장/품종 정확도로 세지 않는다.
scope=`software_research_only`, claim_scope=`synthetic_post_removal_joint_continuation_only`, G0_G4=`not_assessed`다.
새 불변 저장/같은 시점3D·실제 cultivar/전체 작기·생산/자원/경제·거시/수급·추천과 R2/G0–G4는 후속이다.
