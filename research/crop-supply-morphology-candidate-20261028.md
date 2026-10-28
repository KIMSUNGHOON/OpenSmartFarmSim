# 공급 제한 새 궤적의 첫 출현 후보 — 2026-10-28 KST

[실제 새 Context/CP의 공동 적분](crop-supply-morphology-continuation-20261028.md) 다음에
첫 출현 후보의 정밀화를 구현했다. [후보 모듈](../backend/app/crop_supply_morphology_candidate.py)은
실제 새 CP의 다음 원 격자 구간과 같은 stage를 사용한다. **기관 생성·일정 소비·새 CP 발급과
새 UI/3D 연결은 아직 없다.** [내부 계약](../contracts/crop-supply-morphology-candidate-v1.md)을 따른다.

## 계산·장부와 수용 증거

첫 미소비 문턱을 포함한 새-law dense 다항식의 단조성을 검사하고 정확 유리수 근 범위를
명시 허용오차까지 좁힌다. 상한 시각의140상태와101부분 유량을 원4stage/dense 가중치에서
계산한다. 실제 새 RHS/도메인을 다시 검사하며, 표현된 air integral이 문턱을 넘지 못하면
시각·나이를 조정하지 않고 보류한다. 해당 수치 다항식의 근 범위이며 실제 출현 시각 오차가 아니다.

[부분 장부](../backend/app/crop_supply_morphology_candidate_books.py)는 current→candidate의
64계정과 실제 원 root/birth/point를 재구성한다. 기존 branch/lifetime에 부분 유량을 **정확
분수 합**으로 결속하고, current residual+local residual·원 budget+local budget을 대사한다.
길이/나이를 C에 더하지 않으며 실제 stock ID/기관 시계·원 D0/이력을 보존한다. construction/
unmapped/유입·실현량·deficit와 canonical gap/잠재 곡선의 적분 차이는 따로 기록한다.

| 범위 | 확인한 결과 |
|---|---|
| 최종 집중 검사 | **33개가 한 실행에서 통과**. 실제 bracket/근·전체 dense/RK4·64장부·동일 시각 차이·잘못된 tolerance/raw/hash/재해시 CP·문턱 없음·정밀도 한계·도중 tolerance/code/profile/원 접근 변경·domain/RuntimeError·출력 cap 포함 |
| 별도 producer/consumer | 실제 기존4Context × 허용오차1s/1ms/1μs = **12후보 원 바이트 동일**. 세 정밀도의 근 범위가 조건별로 중첩. 원 CP/구간·각 stage hash/시각·point/일정 보존 |
| 실제 호출 수 | 준비에서 각 프로세스의 원 Root2RHS·새0RHS. 후보당 새 current1+새 stage/endpoint33=34RHS: 원 구간4+dense1+1/2/4진단28. 전체 각 current12/stage396, 주요5커널 각각408회. 과거/old RHS·조달/초기화/새 CP·DB/network/write0 |
| app 없는 독립 산술 | Decimal200/Fraction으로12후보/156이분, dense 상태1,680/유량1,212·RK4 상태53,760/유량9,696·stage 형상5,280/재고5,760, local/branch/global 각각3,072계정·deficit528·canonical 진단1,056·clock576·동일 시각 차이5,040·source hash84 대사. app import/RHS0 |
| 회귀·보존 | 수정 전/후12후보의 정상 입력 수치는 동일하고 code/calculation hash만 변경. 원 source38파일 bytes/metadata·기존174source/1output·private:false132blob·이전 GUI1502·export9464·공개4732/834시점·봉인 build4865파일 보존 |
| WSL | 순차 guard:512MiB/PID·1GiB combined·600초/.25초. 수용 phase 최대 PID162,430,976/합계246,599,680bytes. owned remaining0·FD4→4·기존 보호 프로세스 보존. Windows/전체 호스트 메모리 측정 아님 |

원 코드·phase·개인 영역 출력 hash와 호출 계측은 [구조화 증거](artifacts/crop-supply-morphology-candidate-20261028.json)에 있다.
새 외부 자료/품종 계수 채택0이며 개인 영역 원문·후보 전체 수치는 공개 저장소에 전재하지 않았다.

## 발견한 문제와 실제 수정

최초 RED는 새 모듈 부재였고 실제2검사→27검사→추가5검사가 통과했다. 별도12후보 대사 뒤
호출자가 계산 도중 tolerance dict를 바꾸면 결과가 실제보다 좁은 허용오차로 표시될 수 있음을
발견했다. 회귀 검사에서 **예외가 발생하지 않는 실패**를 재현한 뒤, 검증된 입력 복사본으로
계산하고 반환 전 caller 입력을 다시 대사하도록 수정했다. 수정 전 원 코드/결과를 보존했다.
최종33검사와 최종 별도12후보를 다시 실행했고 정상 입력 수치는 그대로였다.

독립 산술 첫 실행은 재사용한 순수 함수에 RK4 가중치 이름을 제공하지 않아 NameError로
중단됐다. 고정 RK4 가중치를 dense 가중치와 구별해 제공한 별도 script/phase가 모든 대사를
통과했다. 이 수정은 계산기·입력·기대 수치를 변경하지 않았다. 실패 phase를 성공으로 덮지 않았다.

## 다음 한 단계와 남은 범위

다음 `supply-morphology-fractional-material-point`는 이 실제 새 후보·원 source/다음 ID/부모와
**명시 새 기관 k·seed C·치수·온도/권리**를 결속한다. `C_seed*F >= k*X_seed`의 적합성을
검사하고 원 생장호흡 비용·buffer 차감·유입 sensible/capacity를 각각 한 번만 반영한다.
부적합 seed는 보류하며 k/치수/탄소를 맞춰 고치지 않는다. 기존 C/A/L/age·비대상 상태와
point/local/global 수지·재시도·실패/현재/late·독립/fresh/보존이 수용 기준이다.
이 단계도 일정 소비/새 Context/CP·잔여/반복 채택은 별도 후속으로 남긴다.

예상은 입력/seed 적합성20–35 + 조달/장부25–40 + 집중·독립/fresh20–35 + 보존5–10 =
**잠정70–120집중분**이다. 이후 새 Context/일정 단일 소비·반복 재개90–160 + 반복 검증30–60,
불변 저장/무계산 reader/SDK/같은 상태 실제3D180–300집중분 초안이다. 낮은 신뢰 추정이며
조달점 수용 뒤 갱신한다. 실제 자료 확보·최종 R2/제품 farm 통합과 전체 완료일은 아직 미정이다.

이번에 새 API/DB/worker/browser·전체 backend/frontend suite를 실행하지 않았다. 외형5175 HTTP200,
5180 원 만료/PID 없음·저장 빌드 보존. 실제 품종/국내 독립 측정0·G0–G4 미평가/R2 미승인,
전체 작기/과실/수확·자원 구매·Decimal 경제/거시·수급·자율 비교/제품 통합은 미완료다.
이 자료 확보를 합성 개발의 선행 조건으로 바꾸지 않는다. 전체 goal은 active/incomplete다.

원 native CLI의 실제 turn2026-10-28T10:40:44.605Z에서 gpt-6.1-sol/xhigh를 관측했다.
원 LF SHA는 `24be48ef625fa6c6063cbc8bcc459009d15d9b7ced2c8db5e7aa71ff470b53a7`, 재귀 CLI0이다.
