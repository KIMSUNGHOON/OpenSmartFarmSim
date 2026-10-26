# 개별 기관 벡터의 첫 분수 후보 상태와 local/global 장부 — 2026-10-27

[계약](../contracts/crop-organ-fractional-candidate-v1.md) · [모듈](../backend/app/crop_organ_fractional_candidate.py) · [검사](../backend/tests/test_crop_organ_fractional_candidate.py) · [기계 증거](artifacts/crop-organ-fractional-candidate-20261027.json).

실제 새 벡터의 첫 수치 threshold 후보 시각에서 전체 상태/부분 유량과 local/global 장부·같은 시각1/2/4 부분 step 진단을 계산했다. 신규39/관련18, 총57개 검사가 통과했다. [직전 한 구간110검사](crop-organ-next-threshold-20261027.md)의 모든 원 자료·산출물을 보존했다. 아직 새 기관/material point·일정 채택/새 integrator CP·원 격자 잔여 재개·형상/새3D는 생성하지 않는다.

## 산출물과 계산 범위

`calculate_fractional_shoot_candidate`는 실제 Context/raw CP/외부 신뢰 SHA와 명시 exact 초 폭에서 원 probe를 호출한다. 실제 첫 기준의 upper exact 시각을 선택하고 원4stage/hash/배치·유량 순서/단위에 결속한다. 모든106+3n+m 상태와21+3n+3m partial 유량에 같은 연속식/정확 유리수 조합과 한 번 binary64 반올림을 적용한다. 실제 새 RHS로 domain/derived/원 curve residual·D0를 확인한다. 표현된 pending 기온 적분의 shoot 나이가 기준 미만이면 보정하지 않고 hold다.

[기존 후보 계약](../contracts/crop-funded-event-state-v1.md)의 순수 `_weights`/`_combine`/`_rounded`만 재사용했다. 기존107-vector의 `_ledgers`/`_refine`/CP를 새 벡터로 가장하지 않는다. 원 fixed RK4의 multiply-then-add와 새 exact-time 조합을 구분하고 θ=1 상태/유량의 정확 차이를 원 단위로 기록한다. 결과가 원 endpoint와 반드시 bit 일치한다고 주장하거나 고치지 않는다. 새 생물학적 계수/면적↔C 변환·절대 epsilon은 추가하지 않았다.

## exact local/global 합성

local 장부는 전체 carbohydrate/과실수·수관/공기 현열·수증기·열용량·reduced energy·각 leaf 나이/C·stem/root C와 합계다. 예산은 기존 `64*(steps+1)*ULP(scale)`이다. 원 root 초기 재고·현재 ordered birth bases/point totals에서 global 장부를 계산하고 현재 CP의 global residual도 정확 유리수로 재검사해 원 예산을 만족해야 한다.

pending lifetime/segment는 원 현재 prefix와 partial의 정확 합이다. 새 global residual은 **원 exact global residual + exact local residual**과 정확히 같아야 한다. 예산은 원 current global 예산과 local 예산의 합만 쓰며 추가 absolute epsilon/aggregation 예산을 넣지 않는다. 원 CP/prefix/point bytes와 조달 비용·현재 C/A/기관 IDs를 변경하지 않는다. 이 pending 합을 새 checkpoint로 채택하지 않는다.

같은 exact 시각까지 classical RK4 부분 step1/2/4를 계산한다. 모든 RHS stage의 domain과 각 substep endpoint의 누적 local/global 장부를 검사한다. refined 경로는 다른 국소 수치 경로여서 기준 미통과도 별도로 표시한다. dense 근을 다시 고르거나 모든 refined 나이를 기준에 맞추지 않는다. 차이는 국소 수치 진단이며 ODE/계수/측정/물리 출현 오차의 인증 상한이 아니다. 선택 상태/부분 RHS stage 사이의 연속 domain 유효성을 주장하지 않는다.

## 통과한 검사와 독립 재현

- 최종 신규39개: 실제07시 source의4 single-point 후보 전 상태/partial 유량·exact 시각/원 prefix·local/global residual과 예산 합성,37 RHS/0과거 전진·초기화/legacy ledger·point/CP 발급,6조건×양쪽 point의 미통과 hold, dense/refinement 단계 실패·권리/late profile/code·원 raw identity/cap·거짓 local/global 장부·반환 범위/비선형 해석해4차 수렴을 확인했다. 순수 장부 좌표의1leaf/2stock와128leaf/256stock를 검사했으며 실제 최대 API 목록 수용과 구별한다.
- 관련 기존 후보18개를 현재 원 source에서 재검사했다. 과거 단계의110/124/406을57에 더하지 않는다. 최초 missing-module red와 초기28 prototype 통과는 보존했다. 이후 domain 범위를 명시하고 불필요한 source 비교 분기를 정리한 최종 소스 전체39개를 다시 검사했다. prototype을 최종 통과로 중복 합산하지 않는다.
- 별도 두 프로세스가 같은 원6 Root/12 mixed Context에서2개 실제 기준×3개 명시 폭의6개 후보를 각각 계산했다.1/1,000,000초·1/8초·1/2^30초이며 근 시각/모든 결과6개가 같았다.16개 미통과 입력도 각각 hold다. 원82개 source의 bytes/metadata·Context/CP를 보존했다.
- 각 후보는 probe5+dense1+refinements31=37 RHS, 미통과는5 RHS였다. 각 프로세스302회와 별도 Root 준비6회를 기록했다. 계산 중 과거 advance/기존·새 초기화·old vector ledger/refine·point/새 CP·DB/CLI/network/write0이다.
- 앱을 import하지 않는 별도 유리수 산술로 trace의 dense/부분 RK4 상태21,402값·partial/pending 유량3,456값·exact local/global residual1,134개·예산1,008개·shoot 나이24개·full-step 차이1,026개를 대사했다. source RHS는 기존 컴포넌트를 공유하므로 독립 ODE/생물학 검증으로 확대하지 않는다.

자체 합성 조건의 기후량1→2부분 step 차이 대2→4부분 step 차이 비는 약16.107–17.380이었다. 별도의 비선형 해석해 검사와 함께 산술 수렴을 확인했으며 이 비를 실제 농장 정확도로 부르지 않는다. 개별 결과의 관측 크기는209,612–210,930bytes이며 원 응답2MiB/입력/CP cap은 유지한다. private packet은 여러 후보와 trace를 모은 검증 포장이므로 개별 API cap의 대체가 아니다.

## 보존과 외부 의존성

직전132 source/1 output 지문·private:false132 blobs·원 공개/경계/export 자료·512요청 byte-cap hold·기존 저장3D4,865파일과 두 화면을 보존했다. 모든 phase는 원512MiB/PID·소유+보호1GiB/600초/4MiB log·0.25초 sample·4,500 감시 항목/source·보호 identity·FD4→4/소유 잔여0 안에서 종료했다. HTTP5175/5180=200과5180 원 만료13:09KST를 유지하고 연장하지 않았다.

새 후보는 UI/API/worker 미연결이다. 전체 backend/frontend suite·새 browser/DB/API/worker·전체 주앱 build는 실행하지 않았다. hosted CI는 실제 push HEAD 조회로 별도 기록한다. 독립 국내 측정0·VTC 권리/대응 측정 미확인·실제 품종/allometry 채택0·512 byte-cap·최종 R2/첫 shader warning·한 작기/생산·자원/경제/거시/수급·자율 비교·제품 통합/G0–G4/전체 goal·전체 완료일은 미완료·미정이다.

## 다음 순서와 수용 기준

다음은 `stem-root-stock-fractional-material-point`: 실제 새 후보/원 첫 threshold·일정/sequence·현재 부모 ID와 명시 C/새 기관 선언을 결속하고 같은 분수 시각에 원 cStemG/cLeafG 비용을 한번만 차감하는 별도 research point다. 원 C_i/A/나이/D0·exact 시각/원 권리·buffer 부족·point 전후 C/K/U/기타 상태·중복/잘못된 부모/ID·source/late/독립/fresh/WSL 보존이 수용 기준이다. 이전107-vector point/CP를 가장하지 않으며 생물학적 기본 질량을 만들지 않는다. 아직 새 분수 CP/일정 채택·잔여 전진은 발급하지 않는다.

잠정 공수는 원 계약/ID20–35+새 점 결속/수지30–55+독립/실패35–65+fresh/보존15–25=100–180집중분이다. 이번 후보 단계110–195집중분 예상은 실제57검사/별도6후보·독립 산술 수용으로 대체한다. 다음 point 뒤 새 version의 분수 CP/명시 일정 채택·원 격자 잔여/분할 재개→실제 기관 시각/ID→공급 제한 형상→불변 같은 상태3D→한 작기/생산·자원/경제·거시/수급/자율 비교 순서를 유지한다. 실제 자료 확보는 합성 개발과 병행하고 예측·추천 게시 조건을 유지한다.

조사·설계·구현은 실제 native Codex CLI `gpt-6.1-sol` / `xhigh`에서 수행했다. turn/model/effort·raw LF SHA/관측 시각은 기계 증거에 기록했으며 재귀 CLI0이다. 계산 산출물은 검토 가능한 합성 연구 증거이고 자료/관문 승인이 아니다.
