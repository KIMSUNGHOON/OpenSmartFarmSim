# 공급 제한 새 궤적의 후속 출현 후보 — 2026-10-28 KST

[실제 새 기관 재개](crop-supply-morphology-newborn-resume-20261028.md)의 genuine Context와
전진 CP에서 다음 문턱의 수치 시각 구간·상한 상태/부분 적산량을 계산했다.
**후속 조달·일정 소비·새 기관/CP·새 저장 결과/3D는 아직 없다.**
[후보 모듈](../backend/app/crop_supply_morphology_newborn_candidate.py)과
[부분 구간 장부](../backend/app/crop_supply_morphology_newborn_candidate_books.py)는
[내부 계약](../contracts/crop-supply-morphology-newborn-candidate-v1.md)을 따른다.

실제 current CP의 다음4stage·단조 shoot polynomial에서 정확 이분법으로 첫 미소비 threshold를
좁힌다. 상한을 선택하되 계산 age를 threshold에 맞추지 않는다. 같은 단계의 dense state/부분 유량과
실제 새 RHS를 대사하며 같은 선택 시각의1/2/4substep을 따로 계산한다. 이전 trajectory/typed handle을
이식하지 않았다. 기존 원 비용·형상/탄소·birth/ID/부모·권리·점 장부와 원 수치 격자는 그대로다.

현재 branch binary64와 부분 유량을 **분수로 정확히 더하고 다시 float로 반올림하지 않는다**.
물리 root와 형상 분기의 누적 원점을 구분해 current→candidate local, seed→candidate branch와
원 root/global을 대사한다. 각 residual/budget은 실제 current CP + local 값과 정확히 같아야 한다.
실제 current clocks·potential deficit·canonical diagnostics도 같은 시각에 계산한다.

| 검증 | 실제 결과 |
|---|---|
| 집중 검사 | **33개 한 실행 통과**. 실제 다음 구간/근·모든 dense state/유량·local/branch/global 합, 같은 시각1/2/4·실제 차이, canonical tolerance9·CP 변조5·현재/도중 source/profile/code·tolerance 변경·domain/RuntimeError·raw/output cap/precision·old biology/조달/CP 미호출 |
| 별도 생성·재계산 | **18개 후보 동일**. 수용된10개 실제 post-material 상태의1/1000초 + 원4source의1/100·1/10000초8조건. 잎 포함/미포함·0/양수 seed 길이·기존 원 k 조건 유지.6개씩3순차 batch이며 각 원 source38파일 bytes/metadata 동일 |
| 실제 호출 | 매 후보 current1 + new33RHS(원 구간4+dense1+1/2/4진단28), 각 프로세스6후보/204회.3batch×생성/재계산으로 총1,224새 RHS. 각 프로세스의 원 owner 준비 old RHS2·원 receipt 자금 산술16회는 별도. exercise의 과거/old RHS·조달/funding·잎 초기화·CP 발급·DB/network/write0 |
| 독립 근/수치 | app import/RHS0의 정확 Fraction으로18후보·238이분·dense2,586상태/1,972부분 유량, RK4 82,752상태/15,776적산량·실제 형상률8,800/재고률9,520·18단조 certificate를 대사. 같은 원 상태의 정밀도별 구간 포함 관계도 일치 |
| 독립 장부/clock | local5,048·branch5,048/global 합5,048, 원점 형상식2,640·재고식952·기관 clock880·shoot clock72·deficit880/canonical1,760·시각별 차이2,586·hash126/code1,476 대사. 예측/ODE 전역 오차 보증 아님 |
| 보존 | 이전200source/1output·원38파일·private:false132blob·이전 GUI1502·export9464·공개4732/834시점·봉인 build4865파일 보존. 외형5175 HTTP200;5180은 원 만료/PID 없음·저장 보존 |
| WSL | 순차 guard512MiB/PID·1GiB combined·600초/.25초.3batch 각각217.88/214.83/213.33초; 수용 phase 최대 PID149,549,056/합계214,978,560bytes. owned remaining0·FD4→4·보호 프로세스 유지. 전체 호스트 메모리/한 작기 성능 수용 아님 |

원 root/현재 CP의 출처·권리와 trusted 원 hash가 계속 필요하다. self-hash가 독립 출처나 farm
custody/관문 승인을 대신하지 않는다. 이 시간 구간은 합성 수치 polynomial의 구간이며 실제
생물학적 출현 시각이나 ODE 전역 오차 보증이 아니다. 원 구간이 문턱을 포함하지 않으면 이후
구간을 탐색해 성공시키지 않는다. 값/age/계수를 보정하지 않고 보류한다.

## 실패와 수정

첫 RED는 모듈 부재였다. 첫 실제 검사에서는 장부 helper가 이미 분수로 바뀐 상태를 다시
`Fraction.from_float` 입력으로 처리해 실패했다. 원 float 상태를 한 번 변환하도록 호출을 고쳤다.
수치/허용치/입력은 변경하지 않았다. 수정 후33집중검사와3batch18후보·독립 산술이 통과했다.
기존 수용 모듈/프로필/원 자료는 수정하지 않았고 이전 raw pin을 전부 보존했다.

독립 검증은 hash를 확인한 이전 app-free 보존식/단계 산술을 재사용하고, 새 seed·현재 CP·원점
형상/clock/재고 식을 대사했다. 단계의 건설 유입/형상률과 재고률은 정확 분수로 확인했다.
외부 품종 매개변수·독립 농장 자료를 새로 검증했다고 주장하지 않는다.
[구조화 증거](artifacts/crop-supply-morphology-newborn-candidate-20261028.json)에 phase·raw pin·호출 수와
보존 결과를 기록했다. 개인 영역 원문은 공개 저장소에 전재하지 않았다. 새 외부 자료/계수 채택0이다.

## 다음 한 단계·수용 기준과 일정

다음은 `supply-morphology-newborn-successor-material-point`다.

1. 실제 새 후보/current CP·그 시각의 부모와 다음 source entity/ID에 명시 새 seed C/치수/k·선택
   잎/온도를 결속한다. 이전 후보/Context로 가장하지 않고 실제 다음 sequence를 사용한다.
2. `C_seed*F >= k*X_seed` 적합성을 원 선언 그대로 확인하고 원 성장호흡 비용·buffer debit과
   열/용량을 한 번만 반영한다. 기존 C/A/L/나이/clock·비대상 상태와 원/새 k를 유지한다.
3. actual new state·birth/point/local/global preview, 부족/권리/현재/late/cap/재시도·독립/fresh/
   원 자료/GUI/WSL을 대사한다. 아직 일정 소비나 CP 채택을 완료한 것으로 제시하지 않는다.

잠정35–60집중분(현재 source/seed·조달20–30 + 점/전역/실패·독립/fresh/보존15–30)이다.
이후 genuine owner/일정 단일 소비·후속 반복/전역 체인40–65집중분 초안을 유지한다.
남은 조달/반복75–125집중분과 불변 저장/무계산 reader/SDK/같은 상태 실제3D180–300집중분은
낮은 신뢰 작업량 추정이며 실제 proof 규모에 따라 갱신한다. 한 작기 성능·제품 farm/worker 통합·
최종 R2·독립 자료 확보의 기간을 포함하지 않는다.

실제 품종/국내 독립 측정0·G0–G4 미평가/R2 미승인이다. 자료 확보는 합성 개발과 병행한다.
전체 작기·과실/수확·자원 구매·Decimal 경제/거시·수급·자율 비교·제품 UI 통합은 미완료이며
전체 완료일은 미정이다. 새 DB/API/worker/browser·전체 backend/frontend suite는 실행하지 않았다.
whole goal은 active/incomplete다.

실제 native turn2026-10-28T13:42:24.422Z의 gpt-6.1-sol/xhigh를 관측했다.
원 LF SHA는 `a9e30fcd78baac951c88caf31bb70a8578db6f7c5a389a3fc4b36c93ea3e0051`, 재귀 CLI0이다.
