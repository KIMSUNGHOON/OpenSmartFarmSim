# 현재 개별 기관 CP와 초기 줄기 이력의 열적 시계 — 2026-10-27

[계약](../contracts/crop-organ-current-shoot-clock-v1.md) · [모듈](../backend/app/crop_organ_current_shoot_clock.py) · [검사](../backend/tests/test_crop_organ_current_shoot_clock.py) · [기계 증거](artifacts/crop-organ-current-shoot-clock-20261027.json).

현재 실내기온의 원 lifetime 적분을 실제 선택 초기 shoot/internode와 연결하는 읽기 전용 연구 계산을 수용했다. 신규79/관련45, 총124개 검사가 통과했다. 기존 [가변 목록 재개](crop-organ-funded-continuation-20261027.md)의 source/상태/CP/장부를 보존한다. 자동 threshold 출현·공급 제한 형상·한 작기/생산·화면 연결은 아직 수용하지 않았다.

## 이번 산출물과 근거

`derive_current_shoot_clock`는 실제 새 Context와 외부 신뢰 raw CP SHA를 받아 현재 CP를 검증한다. 원 global step/exact elapsed/phase/event/prefix·선택 crop/stem roots/index/상태 hash·권리와 모델/code/profile을 보존한다. 초기 source의 발달 시작과 시뮬레이션 시작을 구분하며, 실제00시/07시/08시 선택·3/4개 초기 절간을 사용했다.

shoot와 초기 절간은 각 저장 나이에 `(I_air−T_base×elapsed)/86400`을 더한다. 저장 float64 적분의 정확한 유리수 해석이며 관측/해석해가 아니다. 새 명시 절간은 원 ordered history의 event/부모/ID·정확 시각·원 air integral부터 계산한다. 기준을 `since_declared_material_point`로 표시하고 생리적 출현으로 승격하지 않는다. 선택 shoot의 기준온도 사용도 명시한다. root_system에는 절간 시계를 붙이지 않는다. 음의 변화는 자르지 않으며 결과 나이가 음수면 hold다.

연구·설계 판단은 현재 실제 Codex CLI `gpt-6.1-sol` / `xhigh`의 native turn 증거로 기록했다. 별도 CLI 재귀 실행0이다. 기존 [저장 시계](../backend/app/crop_funded_shoot_clock.py)/[epoch 처리](../backend/app/crop_funded_shoot_epochs.py)의 산술과 실제 원 선택 연결을 사용했으며 새 외부 자료/실제 품종 계수는 채택하지 않았다.

## 통과한 검증

- 최초67개: 6조건×양쪽 point×초기/중간/완료 CP의 정확 나이·원점/ID·원 bytes, 복수점/동시점 순서, signed 산술/음수·단위·비유한값·CP hash/상한·권리/늦은 변경·현재 RHS1회/기존 초기화·point/과거 계산0.
- 추가12개: 실제 유효한 낮은 기온/높은 줄기 기준온도의 현재 CP가 음수 나이로 hold, own/prior code·RHS 중 profile 변경·최종 원 store read 변경·원 use/display 거부·자체 재해시 CP의 시간/누적/sequence 오류·RuntimeError 전달·반환 복사본 보존.
- 기존 시계/epoch45개를 현재 source에서 재검사했다. 신규79와 관련45를 합산한124이며, 다른 단계의 과거 검사 수는 더하지 않는다.
- 최초 missing-module red를 보존했다. 추가 검사의 첫 두 시도는 합성 입력의 상위 domain 거부로 각1실패/11통과했다. 처음 air0은 leaf 기준온도 아래였고, 다음은 원10..34도 합성 window 밖이었다. 최종 검사는 원18도 기온/leaf 기준온도를 유지하고 직접 선언한 합성 stem 기준온도20을 원 clock/anchor에 일관되게 부여해 통과했다. 제품 공식·허용 window·수치 허용 오차는 변경하지 않았다. 앞선 실패를 삭제하거나 통과로 합산하지 않는다.

## 별도 프로세스와 독립 산술

원6 Root와12개 mixed Context/24개 실제 저장 CP를 두 개의 독립 프로세스가 각각 읽었다. 원 CP의 step2/5/8과 두 point 전후를 포함하며, 결과24개가 동일하다. Context 복원 중 RHS0, 실제 시계 유도마다 현재 CP RHS1회로 각 프로세스24회였다. 검증 준비를 위한 원 Root 생성6회는 별도다. 과거 point/성장 전진/기존 잎 초기화·DB/CLI/network/쓰기 호출은0이었다.

앱을 import하지 않는 별도 산술이 초기 원 source/누적값/정확 시각으로 나이122개를 계산했다. 이를 포함한 시각·원 기관/순서·권리/기준 검사는510개다. 두 수를 독립 검사의 합처럼 더하지 않는다. 원82개 파일의 bytes/metadata와 모든 입력 Context/CP bytes를 보존했다. 결과의 관측 크기는12,644–14,412bytes이며 전체 최대 목록 지원 증거로 확대하지 않는다. 새 ODE/생물학 검증이나 새 농장 관측은 아니다.

## 보존과 남은 범위

모든 실행은 원 단일 PID512MiB/소유+보호1GiB·600초·4MiB log와 보호 프로세스 identity 안에서 진행했다. 원4,500개 감시 항목/각 source·FD4→4·종료 뒤 소유 잔여0을 확인했다. [직전 재개](crop-organ-funded-continuation-20261027.md)의122 source/1 output 지문·406검사 기록, private:false132 blobs·기존 public/export/경계 입력·원 최대 요청의 byte-cap hold를 보존했다.

기존 저장3D 빌드4,865파일과 원 외형 화면을 보존했다. HTTP5175/5180은200이고5180의 원 만료 `2026-10-27T04:09:40.286474+00:00` (13:09KST)를 연장하지 않았다. 이 계산은 새 UI/API/worker에 연결하지 않았다. 전체 backend/frontend suite·새 browser/DB/API/worker·전체 주앱 build는 실행하지 않았다. hosted CI 결과는 실제 push HEAD의 별도 조회로 판정하며 로컬 통과를 hosted 통과로 바꾸지 않는다.

독립 국내 농장 측정0건·VTC 코드/자료의 권리/대응 측정 미확인·실제 allometry/품종 계수 채택0·최종 사실감 R2/첫 shader warning·512잎/기관 byte-cap이 남는다. 실제 작기/수확/구매 에너지·경제/미래 마진·거시/수급·자율 비교/추천, 제품 통합·G0–G4와 전체 goal은 미완료다.

## 다음 한 단계

다음은 실제 새 CP의 다음 한 걸음에서 원 RK4 stage/기온 적분 다항식과 초기 shoot의 다음 threshold를 연결하는 읽기 전용 후보 계산이다. 원 dt/global index·선택 clock/source/rights/profile, 실제 accepted endpoint/원 전체 state·누적·장부와의 대사, exact root bracket/endpoint 규약·비단조/부족한 정밀도의 명시 hold·실패 시 원 CP 보존·fresh/독립 산술을 수용해야 한다. 이전 leaf 벡터의 후보/CP를 새 벡터로 가장하지 않는다. 현재 candidate 검증 뒤에만 실제 분수 material point/채택/재개·기관 시각/ID 연결을 진행한다.

원 코드/계약20–35 + stage/다항식 결속25–45 + 독립/endpoint/실패30–50 + fresh/보존15–25 = 잠정90–155집중분이다. 기존 시계 단계60–115집중분 예상은 이번 실제 산출물과 검증으로 대체한다. 위 예상은 다음 좁은 소프트웨어 단계이며 자료 확보/품종 검증과 전체 제품 완료 날짜는 미정이다. 개발은 실제 자료 확보와 병행하고 예측·추천 게이트는 유지한다.
