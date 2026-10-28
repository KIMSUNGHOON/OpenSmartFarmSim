# 공급 제한 후속 기관의 탄소·형상 조달점 — 2026-10-29 KST

[실제 후속 후보](crop-supply-morphology-newborn-candidate-20261028.md)에 다음 기관의 명시 초기
탄소·크기·건설 탄소비와 원 생장호흡을 연결했다. **일정 소비·새 Context/CP 채택·반복·새 UI/3D는 아직 없다.**
[조달 모듈](../backend/app/crop_supply_morphology_newborn_point.py)·[seed/원 연산 연결](../backend/app/crop_supply_morphology_newborn_point_core.py)·
[점/전역·형상 원점 장부](../backend/app/crop_supply_morphology_newborn_point_books.py)는
[내부 계약](../contracts/crop-supply-morphology-newborn-point-v1.md)을 따른다.

실제 새 전진 CP/후보와 현재 부모·다음 source sequence/ID를 검증한다. 첫 조달점의 옛 sequence를
다시 사용하지 않는다. 현재 프로그램/상태와 명시 입력으로 공유 순수 조달 산술을 재사용하고,
이전 타입의 가짜 handle이나 이전 공개 point 진입점을 호출하지 않는다. 새 절간→선택 잎의
구조 C와 원 cStemG/cLeafG 생장호흡을 buffer에서 한 번만 차감하고 실제 새 stage를 계산한다.
기존 C/A/L/나이와 비대상 상태·원/새 k를 보존한다. 새 잎만 F(0)으로 초기화하고 길이0은 그대로다.

`C_seed*F >= k*X_seed`를 정확 분수·예산0으로 비교한다. seed extension/unmapped 분류는
추가 차감/호흡이 아니다. 부족한 C·높은 k·크기를 바꿔 통과시키지 않는다. 여기의 건설비는
탄소 단위이며 금액·농장 구매비나 마진 계산이 아니다.

물리와 형상 lifetime을 모두 보존하고 새 채널만0으로 추가한다. `after_geometry_baselines`는
기관 ID·단위/원 치수·그 시점의 물리 유입 적산·원점 시각/종류를 명시한다. 이전 기관은 실제
공급 제한 분기 시작, 첫 새 기관은 **처음의 material seed**를 유지한다. 현재 자란 크기로
원점을 옮기지 않으며 이번 기관만 새 seed를 원점으로 삼는다. C/thermal birth와 형상 원점은 구분한다.

| 검증 | 실제 결과 |
|---|---|
| 집중 검사 | **32개 한 실행 통과**. 실제 다음 sequence/부모·길이0/양수·선택 잎4조건, Decimal200 비용/열 한번·모든 기존 좌표·적합성/원점/global, 동일 재시도, 원본/권리·ID/시각·부족 C·현재/late source/profile/code/input/tolerance·RuntimeError·입출력 cap |
| 별도 생성·재계산 | **40조건 동일:34계산/6seed 적합성 보류**. 기존10개 채택 상태×새 잎 포함/미포함×길이0/.01m. 기존 자체 source의 k를 명시 입력에 유지.5개씩8순차 batch·원38파일 bytes/metadata 동일·값 보정0 |
| 실제 호출 | 후보 current1+new33RHS/요청, 성공 point는1 또는2stage. 양쪽 총2,820새 RHS·funding100·새 잎 초기화36(성공32+부적합 leaf 검증4). 기존 잎 초기화0. 원 owner 준비16프로세스의 old RHS 각2·원 receipt 자금 산술 각16은 별도 계측. exercise의 과거/old biology·옛 공개 point·CP/일정 채택·DB/network/write0 |
| 독립 산술 | app import/RHS0의 Fraction/Decimal200으로40결과·조달/seed 적합성50기관·기존 좌표4,842·점356/global2,676계정·형상 원점 식1,422·현재 clock474·birth300필드·실제 형상률474/재고률508·hash238/code2,890 대사 |
| 보존 | 이전206source/1output·원38파일·private:false132blob·이전 GUI1502·export9464·공개4732/834시점·봉인 build4865파일 보존. 외형5175 HTTP200;5180은 원 만료/PID 없음·저장 보존 |
| WSL·시간 | 순차 guard512MiB/PID·1GiB combined·600초/.25초 유지. 집중479.84초;8batch 각각226.90–236.74초/합계1,856.61초. 수용 phase 최대 PID259,837,952/합계294,305,792bytes(독립 검사 포함). owned remaining0·FD4→4·보호 프로세스 유지. 전체 호스트 메모리/한 작기 성능 수용 아님 |

전역 preview는 실제 원 root·birth·현재 누적/point 식과 before global+점 residual/budget를 대사한다.
기존 형상 global은 유지하고 새 기관의 연속 장부는0으로 시작한다. 각 기관의 current clock을
실제 시각/air integral에 맞춰 기록하되 원 벡터 나이는 보정하지 않는다. 결과는 여전히 미채택
preview이며 영속 농장 사건/구매 거래가 아니다. 같은 before-source 재시도는 동일 bytes를 반환한다.

## 검증 이력과 실제 범위

첫 RED는 모듈 부재였다. 첫 실제 조달 검사1개와 확장32검사가 통과했다. 코드/모델 입력을 바꿔
보류를 통과시키지 않았다. 기존 수용 모듈·프로필·원 자료를 수정하지 않았다. 독립 검증은 이전의
hash 고정 app-free 산술을 재사용하고 새 point·원점/clock·재고·열/수지 합을 대사했다.
개인 영역 원문은 공개 저장소에 전재하지 않았다. [구조화 증거](artifacts/crop-supply-morphology-newborn-point-20261029.json)에
실제 phase·raw pin·호출 수·보존 결과가 있다. 새 외부 자료/품종 계수 채택0이다.

## 다음 한 단계와 의존성·작업량

다음은 **`supply-morphology-successor-post-point-context`**다. 실제 수용 point/current source/CP·
정확 시각/ID와 after state/program/organs/costs·birth/**geometry origins**·통합 lifetime/point/global을
진짜 새 Context/초기CP에 결속한다. 실제 다음 threshold는 채택에서 한 번만 소비하고 numerical
age를 맞춰 끌어내리지 않는다. before/after 두 phase를 원 prefix에 연결하며 원 격자를 유지한다.
Cold restore는 과거 RHS·조달/funding·잎 초기화를 실행하지 않고, 초기CP 복원은 실제 현재
새 stage1회를 검증한다. trusted 원 proof/hash·변조/현재/late·크기·독립/fresh/보존이 수용 기준이다.

현재 재개 모듈은 첫 post-material owner만 받는다. 이후 여러 출현의 형상 원점은 현재 grown
seed로 다시 잡을 수 없고, source/current CP 타입 검증도 그대로 대체할 수 없다. 따라서 이전
owner/반복40–65집중분 초안은 실제 의존성 분해로 바꾼다.

| 남은 작업 | 잠정 집중 작업량 |
|---|---|
| 실제 후속 point의 새 Context/초기CP·수용 proof/일정·cold restore·현재 검증 | **45–80분**: 결속/일정20–35+복원/proof15–25+독립/fresh/보존10–20 |
| 그 진짜 family의 가변 inventory/global·원 격자/extended CP·분할/cold·실패 prefix | 60–100분, 첫 Context 수용 뒤 갱신 |
| 같은 family의 다음 후보/명시 조달·일정 단일 소비/반복 전역 체인·독립/fresh | 65–115분, 실제 proof/선언 규모 뒤 갱신 |
| 불변 저장/무계산 reader/strict SDK·같은 상태 실제3D | 180–300분 초안, 수치 반복 수용 뒤 재산정 |

남은 수치 owner/재개/반복은170–295집중분의 낮은 신뢰 작업량 추정이다. 한 작기 성능·제품
farm/worker 통합·최종 R2·독립 자료 확보 기간은 포함하지 않는다. 실제 품종/국내 독립 측정0·
G0–G4 미평가/R2 미승인이다. 자료 확보는 합성 개발과 병행한다. 전체 작기·과실/수확·자원 구매·
Decimal 경제/거시·수급·자율 비교·제품 UI 통합은 미완료이며 전체 완료일은 미정이다.
새 DB/API/worker/browser·전체 backend/frontend suite는 실행하지 않았다. whole goal은 active/incomplete다.

설계/구현 native turn2026-10-28T14:18:12.808Z와 이어진 검증 turn2026-10-28T22:30:25.735Z 모두
gpt-6.1-sol/xhigh를 실제 관측했다. 각 LF SHA는 `b93bb0b9656f7f46d3771cc309193d9d1842bd6806a8ddc3d3410c84c2c680d5`,
`ef34b744ab7ae951e51070f2bdab923b4258ba2b4884ff80525ba1d271671c6b`이며 재귀 CLI0이다.
