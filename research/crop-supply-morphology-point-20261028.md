# 공급 제한 출현 후보의 실제 탄소·형상 조달점 — 2026-10-28 KST

[수용된 새-law 출현 후보](crop-supply-morphology-candidate-20261028.md)에 명시된 새 기관의
초기 탄소·치수·건설비와 원 성장호흡 비용을 연결했다. [내부 계약](../contracts/crop-supply-morphology-point-v1.md)을 따른다.
**일정 소비·새 Context/CP 채택·이후 전진/반복·새 UI/3D 연결은 아직 없다.**

## 계산과 실제 범위

[조달 코어](../backend/app/crop_supply_morphology_point_core.py)는 실제 원 timeline/current schedule의
첫 미소비 ID·현재 부모와 명시 새 k/C/길이·잎 F(0)/온도를 결속한다. `C_seed*F >= k*X_seed`를
정확 분수·오차 예산0으로 확인하고 원 cStemG/cLeafG의 구조 C+생장호흡을 buffer에서 한 번만
차감한다. seed의 형상 대응 C/미대응 C는 따로 분류하며 추가 비용을 만들지 않는다.
부족한 seed의 C·k·치수를 바꿔 통과시키지 않는다. 실제 품종 allometry 수용이 아니다.

원 커널은 길이 양수만 지원했으므로 [새 기관 stage](../backend/app/crop_supply_morphology_birth_stage.py)를
추가했다. 원 파일을 보존하고 internode 길이0만 추가로 허용한다. 그 guard/오류 문구를 되돌린
함수 본문은 원 본문과 동일하고 양수 사례의 출력도 같다. 0 길이를 epsilon으로 바꾸지 않으며
실제 0 상태에서 생장률을 계산한다. 나머지 원 unsupported domain은 그대로 보류한다.

[진짜 source 연결](../backend/app/crop_supply_morphology_point.py)은 새 후보를 실제 다시 계산하고
원 source/ID/시각·초기 binding·권리를 대사한다. 기존 기관의 C/A/L/나이와 비대상 상태를 원 값으로
보존한 채 실제 새 절간→선택 잎을 추가한다. 잎의 열용량·sensible 유입과 실제 새 stage를 연결한다.
새 영수증은 정확 시각/air integral·기준온도/초기 C·부모를 보존한다.

[점·전역 장부](../backend/app/crop_supply_morphology_point_books.py)는 point residual/budget와
원 root/실제 birth/누적/point 식을 재구성하고 기존 global+점 residual·예산 합을 대사한다.
새 기관의0 continuous flow·초기 형상 source를 구분하며 실제 시각의 모든 current clock을 갱신한다.
전역 결과는 **미채택 preview**이며 새 CP나 과거 root 재실행을 뜻하지 않는다.

| 검증 | 실제 결과 |
|---|---|
| 집중 검사 | **36개 한 실행 통과**. 길이0/양수·잎 포함/미포함·실제 유지 좌표/비용 한번·Decimal200·stateless retry·seed exact 경계/부적합·scope/ID/권리·funding·도중 입력/tolerance/source/profile/code·RuntimeError/출력 cap |
| 별도 producer/consumer | 실제4Context × 길이0/양수 × 잎 포함/미포함 = **16결과 동일:10계산/6부적합 보류**. 기존 명시 k의 두 조건을 그대로 사용. 값 보정0·원 candidate4개/원 CP·현재 source38파일 bytes/metadata 동일 |
| 실제 호출 수 | 각 준비는 원 Root2RHS·새0. 각16요청의 candidate current+stage34=544RHS. 성공10점의 point stage14RHS·주요5커널 각각14회(후보 쪽 각각544회). 새 잎 초기화6회: 성공 잎4 + 부적합 잎의 순수 검증2. 과거/old RHS·old jump/조달·새 CP·DB/network/write0 |
| 독립 산술 | app import/RHS0의 Decimal200/Fraction으로16결과·조달 기관/적합성14, 기존 좌표1,380·점104/전역710계정·현재 clock124·새 baseline14/ID·C·base42항목·stage 형상124/stock134/수지110·원 program100/parameter110항목·hash40 대사 |
| 보존 | 기존180source/1output·원 source38파일·private:false132blob·이전 GUI1502·export9464·공개4732/834시점·봉인 build4865파일 보존. 외형5175 HTTP200;5180은 원 만료/PID 없음·저장 보존 |
| WSL | 순차 guard512MiB/PID·1GiB combined·600초/.25초. 수용 phase 관측 최대 PID176,021,504/합계287,490,048bytes. owned remaining0·FD4→4·보호 프로세스 보존. 전체 Windows/호스트 메모리 측정 아님 |

개인 영역 원문을 공개 저장소에 전재하지 않았다. 실제 코드/phase/원 출력 hash와 계측은
[구조화 기록](artifacts/crop-supply-morphology-point-20261028.json)에 있다. 새 외부 자료·품종 계수 채택0이다.

## 실패와 수정

길이0 커널과 새 point의 첫 RED는 각각 모듈 부재였다. 첫 조달 연결 검사에서는 새 절간의
기준온도를 emergence profile에서 찾았으나 실제 원 수치 출현은 shoot timeline에 보존했다.
그 원 값에 연결한 뒤 실제 조달점/0 stage2검사와 전체36검사가 통과했다. 임의 기본값을 넣지 않았다.
점의 반올림 예산은 차이만 남겨 원 operand 규모를 잃지 않도록 before/after 항을 유지한다.
원 모델·입력·기존 저장 자료와 프로필을 수정하지 않았다.

## 다음 한 단계·의존성과 일정 근거

다음 `supply-morphology-post-point-context`는 실제 point/source/원 CP·exact 시각/ID·146상태(잎 포함 사례),
새0 길이 stage·74global 장부와 원/새 k·birth/누적을 **진짜 새 Context/CP**에 결속한다.
일정은 그 채택에서 한 번만 소비한다. trusted 원 bytes·현재/late source/profile/code/rights·입력/point
변조/크기·seed hash·독립/fresh를 검증하고, cold restore에서 과거 RHS/point/잎 초기화0을 계측한다.
현재 RHS 검증은 별도로 기록한다. 원본/GUI/WSL을 보존하며 이전 타입의 가짜 handle이나 geometry
invariant validator로 바뀐 상태를 복원하지 않는다. 원 격자 전진·반복 부모는 그 자체로 완료되지 않는다.

작업을 새 owner/seed·일정/장부45–75 + cold restore/변조·현재/late30–50 + 독립/fresh/보존15–25로
나눠 **잠정90–150집중분**으로 잡는다. 이어 원 격자 잔여/공동 적분·분할 재개90–155,
새 owner에서의 다음 후보/조달·반복과 독립 장기 체인120–200이 필요하다. 합계300–505집중분의
낮은 신뢰 추정이며, 기존90–160분 단일 초안은 새0 stage/owner와 재개·반복의 실제 분해로 대체한다.
그 뒤 불변 저장/무계산 reader/strict SDK/같은 상태 실제3D180–300집중분 초안을 다시 검토한다.
제품 farm/worker/최종 R2와 실제 자료 확보는 별도이고 전체 제품의 완료일은 미정이다.

이번에 새 DB/API/worker/browser·전체 backend/frontend suite를 실행하지 않았다. 전체 작기·과실/수확,
자원 구매·Decimal 경제/거시·수급/자율 비교·제품 통합·실제 품종/국내 독립 측정0·G0–G4 미평가/R2
미승인을 유지한다. 자료 확보는 합성 개발과 병행하며 whole goal은 active/incomplete다.

실제 native turn2026-10-28T11:13:22.653Z의 gpt-6.1-sol/xhigh를 관측했다. 원 LF SHA는
`745a8baf38d4f48aa9a831d081bcc4feb0f5e5c2709e9e6a9c86f3298d2cb350`, 재귀 CLI0이다.
