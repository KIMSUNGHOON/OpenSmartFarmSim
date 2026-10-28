# 탄소 공급 제한 면적·절간 길이와 같은 시점 기후 — 2026-10-28 KST

실제 저장 Context/CP에 결속한 **한 시점의 공급 제한 공동 RHS**를 구현했다.
[API/범위](../contracts/crop-supply-morphology-bound-stage-v1.md),
[원 설계](../contracts/crop-supply-limited-morphology-v1.md)를 따른다.
같은 형상·기후에서 실제 buffer 가용량이 다른 두 합성 저장 경로의 기관별 유입·면적/길이
속도가 달라지고, 같은 면적 속도가 열용량·유입 현열과 기후 미분에 연결됨을 확인했다.
**시간 전진·새 CP·한 작기·새 UI/3D 연결은 아직 구현하지 않았다.**

## 계산과 원 상태의 연결

[공동 커널](../backend/app/crop_supply_morphology_stage.py)은 기존 실제 carbon→상대 sink 배분/
기관별 유지호흡→구조 유입의 extension/unmapped 분류→면적/열용량→exchange/energy 순서다.
`e=min(g,k*P/F)`, `X_dot=F*e/k`를 명시 합성 건설비로 계산한다. 실제 g를 caller 값이나
순 stock 미분으로 대체하지 않는다. 구조 유입은 이미 원 생장호흡 비용을 지불했으므로
새 분류에서 buffer 차감/호흡/환급을 추가하지 않는다. 미대응 유입에서 굵기나 수확량을 만들지 않는다.
기존 모든 소스·계수·권리 판본은 보존했고 새 품종 계수/실측 채택은 0이다.

[진짜 CP 결속](../backend/app/crop_supply_morphology_rhs.py)은 원 선택 절간·선언/수치 출현의
실제 ID/부모·exact clock, 현재 C/A/D0·공통 floor와 현재 code/profile/source/rights를 검사한다.
원 state prefix를 보존하고 실제 현재 시계/곡선의 legacy 절간 나이·길이만 새 상태에 덧붙인다.
초기 잎 부모는 추정하지 않고 뿌리 clock도 만들지 않는다. 원 형상을 k에 맞춰 보정하지 않으며
현재 mass–geometry 대응은 미평가다. 새 결과는 integrator CP가 아니고 전진 시간은 0이다.

검사·독립 실행의 기관 목록은 잎6·절간5·뿌리1, 원130상태와 추가10상태다.
새 상태의 derivative에는 실제 제한 A_dot/L_dot, 기존 C/기후와 새 절간 age가 같은 stage로 들어간다.
커널은 carbon/leaf partition/stem-root partition/exchange/area-energy를 각각 한 번 호출한다.
입력 CP의 기존 현재1RHS와 새 공동1stage를 구분하며, branch 길이 point 계산도 따로 기록한다.
유지호흡의 C 감소는 이 합성 정책에서 즉시 형상 축소로 바뀌지 않는다.
원문의 다른 모델과 이 정책의 차이·권리는 [원문 조사](supply-morphology-primary-equations-20261027.md)에 있다.

## 확인한 증거

| 범위 | 실제 결과 |
|---|---|
| 집중 검사 | **고유52개 통과**: 기존 정의49개 한 실행 + 새 원 자료 접근/late code3개 별도 실행. 생산 코드와 기존49 정의는 두 실행 사이 동일하며 전체52를 한 호출로 실행했다고 하지 않는다. 실제 공급/수요 제한·0공급/0잠재·defer/비용/단위·clock/lineage·변조/late/domain/cap/RuntimeError 포함 |
| 별도 producer/consumer | 진짜 source2개 × k 조건2개의 **4결과 동일**. cold consumer는 원 Root 준비2RHS 후 기존 원 capture/새 repeat Context를 복원하며, 과거 적분/조달/잎 초기화 없이 현재 CP4RHS와 새 공동4stage를 실행 |
| 준비와 exercise 구분 | producer의 새 합성 원 자료 생성 준비는 기존590RHS를 사용했다. 이를 0으로 보고하지 않는다. 결과 계산 exercise에서는 실제 CP당 현재1RHS/새1stage, 새 주요5커널 각1회·leaf potential6/stem potential5회 |
| 독립 산술 | app import/RHS0의 Decimal200/Fraction reader로 **4결과·520원 상태·44형상 분류·48재고 속도·44시계·44장부**와 원 component 입력36항목·source hash12개 대사 |
| 부작용/자료 | fresh 계산 구간의 과거 적분·점 조달/초기화·DB/네트워크/CLI/쓰기0, source38파일 bytes/metadata 동일. 원 source/출력·private:false132blob·이전 GUI1502파일·export9464파일·공개4732파일/834시점·봉인 build4865파일 보존 |
| WSL | PID당512MiB/소유+보호1GiB·600초·0.25초 관측의 순차 guard. 해당 수용 phase 최대 PID89,018,368bytes/합계132,706,304bytes, 각 owned remaining0·FD4→4. 전체 호스트/Windows 메모리 측정은 아님 |

실제 raw/코드/phase/개인 영역 증거 hash는 [구조화 기록](artifacts/crop-supply-morphology-rhs-20261028.json)에 있다.
자체 false-redistribution 자료 raw는 공개 기록에 전재하지 않았다.
별도 consumer의 실제 준비 비용·current validation은 새 단계의 호출 수와 합치지 않았다.

## 중단 전 실패의 원인과 수정 범위

중단 당시 생산2파일/시험1파일의 hash가 보존본과 같은지 확인한 뒤 재개했다.
47통과/2실패의 두 검사는 첫 잎에 양의 공급이 있다고 가정했다. 원 case1은 초기 잎3개의
sink가 모두0이고, 이후 복사한 잎도0이어서 전체 잎 유입이0이었다. 이 상태의 성장0은 계약에 맞다.
처음 수정한 검사에서도 양의 공급 사례가 없음을 실제 재실행으로 확인했다.

기존 자료를 수정하지 않고, **0 가중치 잎과 양의 가중치 잎이 함께 있는 새 자체 합성 입력**을
저장·초기 결속·실제 threshold 조달·repeat CP까지 생성했다. 새 input/program/scenario의
동일 신원을 함께 명시했다. 중간의 신원 불일치 오류도 보존했다. 공급 변화 시험은 양의 유입이
확인된 모든 대응 기관을 비교하고, 0 공급 기관의 성장0도 계속 확인한다. 기존 capacity 키는
`incoming`이며 검사에서 잘못 쓴 `inflow`를 바로잡았다. 생산2파일은 이 재개 중 변경하지 않았다.
과거의 부적합 outflow 입력·node 개수/디렉터리 준비·단위 인수 오류와 최초 RED 기록도 남겨 둔다.
실패를 skip하거나 가중치0을 실제 농장 계수로 변경하지 않았다.

## 다음 구현과 남은 조건

다음은 `supply-morphology-shared-stage-resume`다. 실제 수용된 branch와 명시 k/원 기관을
genuine 새 Context/CP로 보존하고, 원 grid 잔여·shared-stage RK4로 시간을 전진시킨다.
새 면적/길이·나이와 누적 e/b·잠재/실현/deficit를 같은 장부에 넣어 전체/분할/cold restore bytes,
현재 clock/원 C·열·수증기 수지와 실패 prefix를 확인한다. 원 D0는 이력으로 남기며 canonical K와
적분 잠재의 차이를 ULP로 숨기지 않는다. 새 법칙에서 다음 threshold가 확인되면 마지막 확정
prefix에서 hold하고 old trajectory 후보를 가져오지 않는다.

상태/장부60–100 + 적분/CP60–100 + 수렴/분할/실패75–135 + 보존15–25로
**잠정210–360집중분**, 낮은 신뢰다. 이후 새 법칙의 반복 funded birth→불변 저장/같은 상태 실제3D다.
새 k와 seed C/치수 적합성·새-law 사건/장부 수용 전에는 반복 성장 전체를 지원한다고 하지 않는다.
이후 한 품종/한 작기·과실/수확·자원·Decimal 경제·거시/수급·자율 비교/제품 farm/worker를 진행한다.

이번에 새 UI·DB/API/worker·전체 backend/frontend suite를 실행하지 않았다. 외형5175 HTTP200은
유지하고5180은 원 만료/PID 종료와 저장 빌드를 보존했다. 최초 원512 최대 요청 byte cap·전체 주앱
build/최종 R2·실제 품종/권리/allometry·국내 독립 측정/미사용 작기·경제/후보 비교 자료는 남아 있다.
이들 확보는 합성 개발과 병행하며 미래 수확/마진/순위 게이트를 대체하지 않는다.
전체 goal은 active/incomplete, G0–G4 미평가·R2 미승인이고 전체 제품 완료일은 미정이다.

부모 native CLI의 실제 context `2026-10-28T09:02:07.305Z`, `gpt-6.1-sol`/`xhigh`를
`2026-10-28T09:03:18.660169Z`에 관측했다. 원 LF SHA는
`af85c87cb7e68473aef3bfef29f27103c099cf3239862a2684103e50f03a90a9`, 재귀 CLI0이다.
