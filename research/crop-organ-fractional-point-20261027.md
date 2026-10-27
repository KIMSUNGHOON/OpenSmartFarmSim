# 실제 분수 후보의 첫 기관 탄소 조달점 — 2026-10-27

[계약](../contracts/crop-organ-fractional-point-v1.md) · [모듈](../backend/app/crop_organ_fractional_point.py) · [검사](../backend/tests/test_crop_organ_fractional_point.py) · [기계 증거](artifacts/crop-organ-fractional-point-20261027.json).

실제 [새 분수 후보](crop-organ-fractional-candidate-20261027.md)와 원 첫 출현 기준/논리 ID를 결속해, 같은 시각의 명시 새 절간과 optional 잎의 탄소 조달점을 계산했다. 신규42/관련123, 총165개 검사가 통과했다. 계산 결과에 새 기관 상태가 있지만 아직 일정/새 integrator CP로 채택하거나 원 격자 잔여를 전진하지 않는다. 저장/같은 상태3D·생물학/실제 생산 승인은 후속이다.

## 기관과 원 시각의 결속

`apply_fractional_material_point`는 원 Context/CP/candidate/initial binding SHA·정확 시각/floor·source event/threshold/sequence·현재 부모·명시 internode/optional leaf·권리/reviewer의 닫힌 입력을 받는다. 실제 후보37 RHS를 수행하고 입력이 그 결과와 같아야 한다. 사용자 선언으로 시각·순번·기관 ID·품종 초기 질량을 만들거나 고치지 않는다.

원 `crop_rational_new_internodes`의 entity/digest로 internode ID를 계산했다. 실제 나중 source의 같은 논리 절간 ID와 일치함을 검사했지만 그 source의 고정22도 forcing 시각/길이를 복사하지 않는다. leaf ID는 같은 entity+organ/slot0의 명시 research 정책이다. 한 논리 사건에 절간1개와 잎0/1개만 계산하며 품종의 해부학/잎 수를 검증했다고 하지 않는다. 부모는 실제 현재 internode를 명시하고 optional leaf는 새 절간에 연결한다. Root/placeholder·이미 사용한 event 또는 canonical organ ID는 거부한다.

## 비용과 상태 보존

새 벡터의 기존 `_jump`를 actual dense state에 internode→leaf 순으로 적용한다. 각 선언 C에 원 cStemG/cLeafG를 적용해 subevent마다 비용을 한 번씩 차감한다. per-kind 원 값과 한 번 반올림한 합계/정확 합계를 모두 보존한다. 혼합 비용률이나 생물학적 초기 질량 기본값은 만들지 않는다. 같은 before/input의 읽기 전용 재계산은 동일 결과이며 실제 두 번째 차감/일정 채택이 아니다.

기존 C_i/나이/면적/과실·기후/D0/root 하나를 보존한다. 새 internode C만 append하고 새 leaf만 age0/canonical F(0)/명시 C로 초기화한다. leaf ΔK/유입 현열/U103은 기존 point 산술이다. 새 stem 길이·mass→area 변환·공급 제한 형상은 아직 계산하지 않는다. 새 나이0은 이 numerical material point 기준이며 정확 생리적 출현/관측 시각이 아니다.

buffer·whole C·신규/합계 stem C·신규 leaf C·K/U·air/vapor/과실수/reduced energy의 exact residual을 기존64ULP(max abs terms) 예산으로 검사했다. source prefix/pending 연속 장부는 수정하지 않고 post-point global checkpoint로 채택하지 않는다. 전후 exact 시각/elapsed advance0이다. 성공 RHS는37+stem1(+leaf1)=38/39회다.

## 검증 결과

- 최종42개: 실제4 single-point 후보×stem-only/both·전 상태/원 ID·Decimal120의 명시 C/T와 순차 buffer/열량·canonical ID와 실제 나중 source 일치, 잘못된 시각/sequence/parent/단위/rights/candidate hash·부족한 buffer·동일 before 재현·실제 manual history의 event/organ 충돌·38/39 RHS/새 leaf만 초기화·late profile/code/rights·응답 cap·RuntimeError·원 bytes를 확인했다.
- 기존 internode54/leaf69, 총123개를 현재 source에서 재검사했다. 과거 후보57/한 구간110을165에 더하지 않는다. 최초 missing-module red와 최초31 prototype 통과를 보존했다. 성장 비용의 단위를 명시한 최종 소스 전체42개를 다시 검사했고 prototype을 통과 수에 중복 합산하지 않는다.
- 별도 두 프로세스가 원6 Root/12 actual mixed Context를 복원하고2개 실제 첫 사건×stem-only/both×3개 명시 C/T 조건, 총12결과를 각각 계산해 동일함을 확인했다. 각 프로세스462 RHS·별도 준비8 RHS(Root6+실제 raw CP 복원2)를 기록했다. stem core12/leaf core6·새 leaf 초기화6이며 과거 advance/기존 초기화/stem geometry/old public point·old vector ledger/refine·DB/CLI/network/write/새 CP0이다.
- 앱을 import하지 않는 독립 Decimal120/정확 유리수 산술이 중간·최종 상태2,994값·조달량186개·point residual126개/예산126개·ID78항목·leaf 열량12항목을 대사했다. 원82파일 bytes/metadata와 Context/CP를 보존했다. source RHS는 기존 컴포넌트를 공유하며 독립 ODE/생물학 검증으로 부르지 않는다.

실제4조건에서 순차 차감과 합계를 한 번 차감한 결과가 달랐다. 원 순차 연산을 보존하고 합성 비용으로 바꾸지 않았다. 관측 응답243,710–248,279bytes/원2MiB cap이며 여러 결과를 모은 private packet을 개별 API cap과 구분한다. 전체 최대 목록 지원은 아직 주장하지 않는다.

## 보존과 남은 범위

직전136 source/1 output 지문·private:false132 blobs·원 공개/경계/export/512요청 byte-cap hold·보호된3D 빌드4,865파일과 두 화면을 보존했다. 원512MiB/PID·소유+보호1GiB/600초/4MiB log·0.25초 sample·4,500 감시 항목/source·보호 identity·FD4→4/소유 잔여0을 유지했다. HTTP5175/5180=200이며5180 원 만료13:09KST를 연장하지 않았다.

새 기능은 UI/API/worker 미연결이다. 전체 backend/frontend suite·새 browser/DB/API/worker·전체 주앱 build는 실행하지 않았다. hosted CI는 실제 push HEAD의 별도 조회로 기록한다. 독립 국내 측정0·VTC 권리/대응 측정 미확인·실제 품종/allometry 채택0·512 byte-cap·최종 R2/첫 shader warning·한 작기/생산·자원/경제/거시/수급·자율 비교·제품 통합/G0–G4/전체 goal 및 전체 완료일은 미완료·미정이다.

## 다음 한 단계와 후속 재개

다음은 `stem-root-stock-fractional-context-checkpoint`다. 실제 point 결과/입력/원 source와 after C_i/A/나이/D0·exact 시각·원 grid 위치·논리 사건/일정 소비·개별 기관의 exact birth/air 기준·원/pending/point/global 장부를 새 version의 immutable Context/CP에 결속한다. 명시 첫 기준만 소비하며 다음 기준도 이미 지났다면 건너뛰거나 snap하지 않고 phase hold로 남긴다. source-selected simulation/development 원점을 보존한다.

Context snapshot의 외부 신뢰 SHA/실제 Root/source와 새 typed CP를 복원하며 과거 RHS/point/기존·새 초기화0, CP당 현재 검증만 허용한다. 직접 captured state/flow/ID/시간/권리·code/profile·자체 재해시/late/cap·독립/fresh/GUI/WSL을 검증한다. 첫 단계에서는 새 격자 잔여를 전진하지 않고, 이어 원 dt의 잔여→정규 grid/후속 사건·분할 최종 bytes·실패 prefix를 별도로 수용한다. old fixed CP/handle을 가장하지 않는다.

잠정 공수는 계약/표현20–35+capture/CP30–50+복원·실패/독립/fresh45–75+보존15–25=110–185집중분이다. 이번 point 단계100–180집중분 예상은 실제165검사/별도12점·독립 수용으로 대체한다. 이후 기관 시각/ID→공급 제한 형상→불변 같은 상태3D→한 작기/생산·자원/경제·거시/수급/자율 비교를 유지한다. 실제 자료 확보는 합성 개발과 병행하고 예측·추천 게시 게이트는 유지한다.

조사·설계·구현은 실제 native Codex CLI `gpt-6.1-sol` / `xhigh`에서 수행했다. turn/model/effort·raw LF SHA/관측 시각은 기계 증거에 기록하며 재귀 CLI0이다. 결과는 검토 가능한 합성 연구 계산이고 자료/관문 승인이 아니다.
