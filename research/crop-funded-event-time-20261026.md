# 저장된 공동 RK4 구간의 기준 통과 시각 — 2026-10-26 KST

**수용 범위는 수치 다항식의 근 구간입니다.** [계약](../contracts/crop-funded-event-time-v1.md),
[구현](../backend/app/crop_funded_event_time.py), [집중 검사](../backend/tests/test_crop_funded_event_time.py),
[검증 JSON](artifacts/crop-funded-event-time-20261026.json).
기존 저장 원본에서 찾은 출현 기준 통과 구간을 재구성하고 그 안의 근을 계산했습니다.
새 기관·출현 전후 상태·수치 재개 checkpoint와 3D는 아직 생성하지 않습니다.
G0–G4/R2는 미평가·미승인 상태입니다.

## 방법 선택과 출처

기존 함수·변수·격자·시계·장부의 [기계적 코드 조사](funded-event-rk4-code-facts-20261026.md)를 먼저 대조했습니다.
이 조사는 연구 스킬이 명시한 background agent의 읽기 작업이며, 방법 선택은 현재 native CLI에서 했습니다.
저장 checkpoint에는 내부 stage가 없지만, 원 program/profile과 왼쪽 상태에서 같은 순서로 다시 계산할 수 있습니다.
과거 전체 구간을 재적분할 필요는 없습니다.

Thomas Izgin-Melnikov의 [원 논문 §4.2 식(28)](https://doi.org/10.1007/s42967-025-00480-8)은
고전 RK4 네 stage의 명시적 3차 연속식을 제공합니다. 이 식을 기존 Ta 적분에 적용했습니다.
논문의 별도 implicit MPRK 방법이나 그 양수 보장을 채택하지 않았습니다.
실제 stage 온도가 모두 기준 온도보다 높더라도 이 다항식은 내부에서 감소할 수 있으므로,
정확한 이차 도함수 최소값이 양수인 경우에만 하나의 증가 근을 인증합니다.
단순 endpoint 부호 변화의 한계는 [SciPy 공식 events 문서](https://docs.scipy.org/doc/scipy/reference/generated/scipy.integrate.solve_ivp.html)와도 대조했습니다.
SciPy 의존성을 추가하거나 해당 구현 코드를 복사하지 않았습니다.

원 논문은 2025-05-22 공개·CC BY 4.0이며 제3자 자료의 예외를 유지합니다.
저자/DOI·식 번호와 변경 내용을 계약에 표시했습니다. 회수한 원 HTML은 private에 보관하며 저장소에는 원문을 배포하지 않습니다.
원 URL/product ID·회수 시각/원 SHA·판본·권리/QC/검토자는 검증 JSON에 있습니다.
출판/available_at은 확인된 **일자 정밀도**만 사용하고, 관측 시각은 농업 관측 없음으로 구별했습니다.
SciPy 문서는 링크와 자체 요약만 사용하며 원문 재배포 권리를 채택하지 않았습니다.
새 농업 계수·농장 자료·농업 권리 승인 채택은 0건입니다.

## 구현과 검증

원 epoch 투영이 공급하는 threshold/순번과 양쪽 원 frame·checkpoint를 결속했습니다.
같은 context/개체 목록의 한 격자 구간에서 RHS 5회로 네 stage와 endpoint를 계산하고,
원 endpoint 전체 sample과 모든 segment/lifetime 적분량을 canonical binary64 bytes로 대사합니다.
그 뒤 stage Ta의 binary64 값을 정확한 유리수로 바꿔 연속식과 도함수 최소값을 계산하고
최대 128회 이분법으로 명시한 시간 폭을 만족하는 근 구간을 구합니다.
원 누적량 반올림과 이상적인 다항식 endpoint의 차이를 기록하고 임의 보정하지 않습니다.
반올림 때문에 다항식 자체가 기준을 넘지 않으면 hold입니다.

- **27개 집중 검사 통과:** 잎 추가 이전 root 구간과 두 차례 추가 이후 구간,
  네 차수 조건의 정확 산술·비선형 해석해의 국소 시간 축소 수렴,
  경계 근/도함수 내부 최소/양수 stage의 반례·정밀도/용량·RHS/적분량 변조,
  권리/늦은 코드·source/blob 변경·DB/CLI/network/쓰기·birth point 0을 확인했습니다.
- 첫 실행은 테스트 보존 검사가 디렉터리를 파일로 읽어 1실패/22통과였습니다.
  그 검사를 수정해 23통과했고, root 구간·반올림/적분량·늦은 blob 사례를 추가한 최종 27통과를 수용했습니다.
- 기존 [자체 공개용 선언](../fixtures/crop-funded-shoot-epoch-fixtures-v1.json)의 `crossing` 원본을
  **별도 프로세스**에서 읽었습니다. 네 stage 관계·endpoint **122상태/36적분량**을 app 수치 helper 없이 재현했습니다.
  독립 Decimal200 계산/256회 이분법으로 반환 구간과 양끝 residual을 대사했습니다.
  RHS는 해당 구간의 5회이며 과거 interval advance·DB/CLI/network/write·birth point는 모두 0입니다.
  원 leaf/stem 54파일의 bytes/metadata도 보존했습니다.

이 합성 사례에서 근은 원점 뒤 약 **252.4575892076초**입니다.
반환 구간은 `[252.45758914947509765625, 252.4575901031494140625]초`,
폭은 `0.00000095367431640625초`입니다. endpoint 직선 근과는 약 `0.00419128초` 다릅니다.
이 폭은 **그 3차 다항식의 근 고립 오차만** 제한합니다. ODE 이산화·과거 누적 오차·계수/측정·실제 출현 오차의 상한은 아닙니다.
실제 threshold 시각·생물학적 예측·새 출현 checkpoint로 게시하지 않습니다.

최종 집중 검사는 82.632초/PID 100,958,208/WSL 소유+보호 합계 137,531,392bytes,
cold 검증은 8.346초/합계 86,532,096bytes였습니다.
512MiB/PID·1GiB 합계·0.25초 표본/600초/로그4MiB·보호 1root·원4500항목/source 보존,
소유 잔여0/FD4→4를 유지했습니다. Windows 프로세스 RSS는 이 측정 밖입니다.
최종 증거 포장 첫 검사는 공개 요약에서 빠진 source_count 키를 전체 proof와 비교해 실패했습니다.
원 검증 결과를 보존하고 공개 phase를 원 proof 전체와 일치시켜 다시 확인합니다.
변경되지 않은 전체 backend·기존 모델/SDK·웹 타입/build/브라우저·R2는 반복하지 않았습니다.

## 다음 수용 단위와 일정

`funded-air-within-step-event-time` 전체를 완료로 체크하지 않았습니다.
그 하위의 다항식 근 계산만 수용했습니다. 다음은 같은 사건 시각의 **상태와 모든 연속 적분량**입니다.
수용 기준은 원 계수/ID/시계를 보존하고 각 상태 domain과 질량·현열/열용량·나이 장부,
단계 축소 오차와 부분 실패를 확인하는 것입니다. 이 결과도 새 버전의 격자 잔여 전진/
CP·cursor·prefix·분할 재개 계약을 통과하기 전에는 원 integrator의 checkpoint로 사용하지 않습니다.

코드 조사에서 드러난 경계에 따라 다음 상태/장부 검증은 집중 작업 **1–3시간**,
그 뒤 분수 사건과 원 격자 잔여·재개/점 전후 계약은 **3–6시간**을 잠정 공수로 잡았습니다.
이는 정해진 완료 시각이 아니며 첫 오차/domain 대조와 변경 파일·검사 분해 후 갱신합니다.
그 후 실제 줄기 ID/leaf attachment·공통 floor/명시 초기 C/조달·현재 권리/검토,
불변 결합 결과→strict SDK→같은 상태의 실제 잎3D 순서로 진행합니다.
독립 농장 자료 확보는 합성 개발과 병행합니다.

현재 이 결과는 UI에 연결하지 않았습니다. 5177은 예정된 11:48 KST에 종료했고
[5175 제작 외형](http://localhost:5175/crop-appearance.html)을 유지합니다.
실제 첫 품종 확정/국내 독립 자료 0건, 전체 작기/생산·자원/Decimal 경제·거시/수급·자율 비교,
제품 UI 통합·최종 사실감 R2/실제 표시 창·주앱 전체 build와 전체 완료 날짜는 남아 있습니다.

판단과 구현은 현재 **Codex CLI gpt-6.1-sol / xhigh**에서 수행했고 재귀 CLI는 0회입니다.
turn_context `2026-10-26T04:11:50.718Z`, raw LF SHA
`312043d3dca5626d693c9c2b0aa915f7fb60f3e1e263940c9f947c3da379222f`,
관측 `2026-10-26T04:13:19.020891Z`. 출력은 계약·코드·재현 검사·이 기록이며 관문 결정이 아닙니다.
