# 새 잎 조달 뒤 같은 전역 시계의 재개 — 연구 v1

상태: **합성 재개 수용** — [153신규/74회귀·독립24문맥/60시점](../research/crop-leaf-funded-birth-continuation-20261026.md). [조달점](crop-leaf-funded-birth-point-v1.md)의 동일 산술을 재사용한다.
새 생리 계수·면적→질량 역산·출현 예측을 추가하지 않는다. 초기 양의 수관/명시 새 구조
성장의 합성 범위와 기존600초/4096걸음/512잎 한계를 유지한다.

`prepare_context(parent_context,raw_parent_checkpoint,expected_parent_sha256,inputs)`는
원 고정 목록 CP의 현재 상태를 검증하고 조달점 전이를 적용한다. 원 root context와 원 CP,
동일 시각의 새 목록/상태·원 D0·초기/출현별 C/나이/공기온도 누적 기준, 연속 누적량,
명시 점 유량/사건 이력·코드/profile/단위·원 dt/count를 불변 bytes에 결속한다.
이후 `adopt_births(context,raw_checkpoint,expected_sha256,inputs)`로 현재 새 CP에서도
다음 조달점을 채택한다. 원 event/leaf ID 재사용은 거부한다. 같은 시각의 다른 batch는
호출 순서를 사건 번호로 기록한다. 제거/빈 수관/실제 줄기 attachment 검증은 후속이다.

현재 점 산술은 검증된 상태를 받는 내부 경계로 추출해 두 API가 재사용한다. 기존 root용
public API/계수/수치 알고리즘은 보존하며 원36조건의 identity 외 수치 동등성을 대사한다.
조달점 채택은 현재 RHS1+새 목록 RHS1, 과거 적분/현재 A 재정규화0이다.

새 `Context`/`Checkpoint`는 기존 고정 목록과 다른 version/schema다.
`context_bytes`/`restore_context`는 원 root context와 외부 신뢰 SHA로 canonical frozen
snapshot을 결속한다. 복원은 hash/schema/코드/profile/이력/단위 검사만 하며 과거 RHS/점 계산0이다.
trusted SHA는 후속 서버의 권한 있는 저장/서명 경로가 공급해야 한다. 자기 계산 hash나
Python 내부 필드 재작성은 신뢰 경계가 아니다.

`start`, `checkpoint_bytes`, `restore_checkpoint`, `advance_chunk`가 실제 재개를 제공한다.
현재 CP 검증 RHS1회 뒤 걸음마다 새 RK4 stage4회다. 모든 기관/기후와 C_i/a/A는
같은 stage/원 RHS로 계산한다. 전역 step/정확 binary-rational elapsed를 유지하고,
새 잎만 나이0/양의 F(0)/명시 Ci에서 시작한다. 원 잎 A/Ci/D0·과실/공기와 이전 prefix를
초기값으로 되돌리지 않는다. 점 전/후의 동일 시각은 phase/사건 번호로 구별한다.

연속 누적량은 원 prefix와 새 segment 적분을 따로 보존한다. lifetime 값은 둘의 1회 합으로
파생하며 중복 적분하지 않는다. 점 성장호흡/구조 C/buffer 차감·열용량/현열은 별도 장부다.
segment의 원7수지+잎별 나이/C와 root부터의 전역 수지·출현 이후의 잎별 나이/C를 검사한다.
whole C 수지는 점 성장호흡을 유출로, canopy/reduced 현열과 열용량 수지는 점 유입을 반영한다.
신규 C는 내부 buffer→구조 전이이므로 외부 광합성/유입으로 더하지 않는다.
호흡의 화학열을 임의 현열로 바꾸지 않는다. 반올림 예산은 원/점/segment 예산과 ulp 집계로
결속하며 임의 절대 epsilon을 두지 않는다. chunk 경계가 최종 CP bytes를 바꾸면 실패다.

Context 합/응답2MiB, 새 CP1MiB, 남은 구간32,768scalar/step_budget1..128 상한.
canonical/중복 JSON key·bool/비유한·닫힌 필드/단위/shape·source/정책/시간/prefix·원/점 장부를
검사한다. 완료 CP 복원은 허용하고 추가 전진은 거부한다. 부분 stage/domain/장부 실패는
마지막 확정 sample/장부/prefix와 hold·CP=None을 반환한다. 미확정 점/endpoint를 게시하지 않는다.
DB/CLI/network/쓰기0, software_research_only/G0_G4=not_assessed다.

수용: 원6합성 조건/초기·중간·끝의 조달, 2회 이상의 출현과 이력 중복 거부,
원 시계/C_i/a/A/D0·누적량/점/phase/ID 보존, 같은 사건 계획의 모든 수용한 분할과
최종 CP bytes, trusted context/CP roundtrip·복원 재계산0, 기존1→2잎/최대512잎·bytes/scalar/격자 경계,
코드/profile/현재 파생량/장부/실패 prefix, 독립 수지/새 구간 RK4·fresh process와 WSL.
수용 계산 뒤 불변 저장/무계산 reader→strict SDK→같은 상태의 실제 새 잎3D로 연결한다.
실제 출현/공급 제한 A·품종/독립 농장·한 작기/생산·자원/경제/자율 비교·G0–G4/R2는 남는다.
