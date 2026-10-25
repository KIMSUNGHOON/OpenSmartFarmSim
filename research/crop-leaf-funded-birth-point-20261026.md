# 새 잎의 구조 탄소 조달점 — 2026-10-26 KST

**수용: 조건부 합성 점 계산만.** [계약](../contracts/crop-leaf-funded-birth-point-v1.md)의
새 잎 Ci를 원 buffer에서 차감하고 원 cLeafG의 성장호흡·면적 열용량/유입 현열을 반영했다.
trusted 원 CP의 현재 상태만 복원하고, 같은 시각의 새 목록 RHS를 평가한다.
기존 source/계수와 고정 목록 적분·재개는 변경하지 않았다.
[연구 판단/권리와 다음 순서](crop-leaf-funded-births-design-20261026.md),
[수용 JSON](artifacts/crop-leaf-funded-birth-point-20261026.json),
[독립36조건의 점 장부 CSV](artifacts/crop-leaf-funded-birth-point-20261026.csv).

## 실제 검증

- **신규74개**: 원6합성 조건의 초기/진행 CP, 최소1기존잎/동시 새 잎·512결과 목록,
  양의 F(0)/요청 A 정규화 영수증, 기존 C_i/a/A/D0·과실/공기·과거 CP/장부/시각 보존,
  독립 Decimal 비용/열수지와 반환 copy, exact binary-rational elapsed, 1현재+1새 상태 평가,
  재초기화/과거 적분0, 닫힌 입력·ID/단위/시간/floor/hash/코드 전후/profile·상한·고갈/실패 원자성.
- **관련297개**: 기존 stock RHS101·dynamics58·continuation138 모두 통과했다.
- **독립36조건**: 별도 producer가 원6조건×초기/중간/완료×새 잎1/2를 계산했다.
  다른 프로세스의 app-free Decimal110 reader가 F(0)·탄소/열 수지·모든 보존 block,
  정확 시각·원 프로그램/context/성장 profile SHA와 CP/결과 hash를 대사했다.
  마지막 source-bound reader의 기록 counter는1,224이며 app import/모델 호출0이다.
  원 bundle1,219,795byte/SHA24b32e618f0a973e5e899d8def2dac2a2f4f4a99fb6938c374882ea97589ff5c.

새 code 약196행, focused test286행이다. 첫 연결 검사에서 기준온도에 현재 기후의
10..34°C 제한을 잘못 적용했던 부분을 제거했다. 기준온도는 원 계약처럼 유한값으로 받고,
현재 Ta≥Tbase와 incoming/current 온도 domain은 원 RHS가 검사한다.
추가 검사에서는 테스트의 반환 alias, 변경하지 않은 exact numerator, 생성 중 이미 거부된
가짜 profile, 축소 수관의 원 U 불일치를 수정했다. 수치/물리 domain이나 cap을 완화하지 않았다.

모든 guarded 단계는512MiB/PID·1GiB 소유+보호 합계/0.25초·600초·로그4MiB를 적용했다.
최종 신규23.657초/PID74,870,784/합계127,983,616byte,
관련131.561초/PID110,551,040/합계163,504,128byte,
독립 producer14.144초/합계95,645,696byte, source-bound reader1.059초/합계53,383,168byte.
모두 terminal0·원4500항목/보호2root·source 보존·소유 잔여0/FD4→4다.
Windows 프로세스는 WSL RSS 측정 밖이다.

## 범위와 다음 조건

현재107+3n벡터에서 원 buffer/U104만 점 차감/유입하고 새 age0/A/C_i를 덧붙였다.
기존 전체 C_i 합계/과실·줄기/공기·D0와 누적 유량은 재초기화하지 않는다.
결과에는 원 CP/manifest·새 목록/같은 시각 state/rates·5수지·조달 영수증과 hash가 있다.
**checkpoint=None**이며 변경 목록의 다음 시간 적분/불변 저장/새 잎3D 연결은 아직 없다.
기존5177 화면은 이 새 조달점 결과를 재생하지 않는다.

이는 이미 조달된 숨은 기관의 공개가 아니라 명시된 새 구조 성장의 합성 가정이다.
실제 초기 질량·출현 빈도/공급 제한 A·품종 계수의 근거/권리/검증은 미확보다.
원 출현/attachment 자료 결속·사건 이력 중복 방지·빈 수관 시작/동시 제거도 후속이다.
실제 농장 측정/독립 작기0·G0–G4/R2·생산량·자원/구매량·경제·거시/수급·자율 비교는 승인하지 않는다.

다음은 새 context/사건 이력에 점 전이를 채택하고 원 전역 시계/과거 prefix/D0와
연속+점 장부를 보존한 채 다시 적분하는 단계다. [계획](../tasks/plan.md)의 후속 수용 기준을 따른다.
기존 주앱 전체 bundle·실제 표시 창/R2는 별도 보류이며 이번 Python 계산으로 해결됐다고 하지 않는다.
전체 backend/UI/hosted CI를 새로 통과했다고 주장하지 않는다. 현재 변경과 관련된 검증만 실행했다.
