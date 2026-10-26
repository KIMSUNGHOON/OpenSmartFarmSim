# 저장된 줄기 이력과 두 시간 원점 — 2026-10-26 KST

**수용: 실제 저장 초기 상태의 이력·나이/길이와 동적 기온 투영.**
[계약](../contracts/crop-funded-shoot-epochs-v1.md), [구현](../backend/app/crop_funded_shoot_epochs.py),
[검증 JSON](artifacts/crop-funded-shoot-epochs-20261026.json).
stem의 발달 원점과 이번 시뮬레이션 시작을 구별하고 실제 선택 상태의 나이/ID·출현/곡선/anchor를 보존한다.
기존 원점 시작용 시계/길이·reader/SDK와 원 자료는 변경하지 않았다.

선택은 원 program 초기 상태(-1) 또는 실제 저장 frame이다. root/program·선택 result/state SHA와 index를 결속하고,
선택 시각이 leaf 시뮬레이션 원점과 같아야 한다. 이후 원 Ta 수치 적분량만 초기 나이에 더한다.
과거 나이를0으로 바꾸거나 과거 기온을 다시 적분/중복 적용하지 않는다.
절간 출현 초는 발달 원점 기준을 유지하고 현재 development 초는 원점 차이+원 binary-rational elapsed다.
선택 이전 이력은 **원 고정기온 모델의 합성 초기 조건**이며 새 공동 기온이 그 과거까지 증명하는 것은 아니다.

## 검증

- **신규25검사:** 원 초기/실제 저장7시간·8시간 상태와6조건, 분수 경과/출현·같은 시각/phase,
  독립 Fraction/Decimal·원 source/anchor 보존과 기존 v1의 같은 원점 수치 동등성을 확인했다.
  초기기관1/512 경계·잘못된 index/다른 선택 시각/코드/용량,
  계산 중 권리/program/선택 result·code 변경과 외부 쓰기를 거부했다.
- [별도 자체 합성 선언](../fixtures/crop-funded-shoot-epoch-fixtures-v1.json)과
  [generator](generate-funded-shoot-epoch-fixtures.py)로 기존 자체 소프트웨어 매개변수에서 새9조건을 만들었다.
  원 기상/농장 자료나 기존 private False 패킷의 권리를 바꾸지 않았다.
  7시간·8시간은 시험 window이며 새 농업 계수/측정 채택0이다.
- 별도 cold 계산에서 **163frame/독립659나이·496길이·163축합**을 대사했다.
  나이/시간은 app-free 정수 cross-product와 Fraction, 길이/합은 Decimal200 기준이다.
  길이 최대 차이는 **1.588 ULP 미만**이고 축 합은 반환 binary64 길이들의 독립 합과 같았다.
  초기 정규화 포함 point552회와 endpoint 문턱 열거163회를 사용했다.
  **ODE/무관 생장 import0·과거 ODE/clock advance0·DB0·CLI0·network0·write open0**을 계측했다.
  private proof는 harness가 사전에 소유한 FD에만 썼다.

원 next threshold/phyllochron/순번으로 기준 통과 **구간1개**를 찾았다.
양쪽 원 frame/CP·시각과 threshold를 독립 나열로 대사했고, `within_step_time_unresolved`로 남겼다.
정확 사건 시각·새 마디/잎·조달점·공간 pose를 생성하지 않았다.
이력 나이/선택 축 길이를 실제 품종의 생장/키·수확/수익 예측으로 표시하지 않는다.

최종25검사82.214초/PID94,093,312/WSL 소유+보호 합계130,576,384bytes,
새 원본 생성59.999초/합계81,563,648bytes, cold14.866초/합계80,986,112bytes였다.
512MiB/PID·1GiB합계·0.25초/600초/로그4MiB·보호1root·원4500항목/source·소유 잔여0/FD4→4를 유지했다.
Windows 프로세스 RSS는 측정 밖이다. 변경되지 않은 전체 backend/기존 v1·SDK·웹 타입/build/브라우저·R2는 반복하지 않았다.

## 다음 수용 단위와 남은 범위

다음은 bracket 내부의 **공동 ODE stage 근거·사건 시각 오차/출현 전이**를 명세하고 검증하는 것이다.
endpoint 사이를 임의 직선으로 잇거나 옛22도 forcing의 사건 시각을 가져오지 않는다.
수치 방법/원 stage 계약을 확인해 작업을 분해한 뒤 집중 공수를 추정한다.
그 뒤 새 기관과 실제 stem/leaf attachment·floor/초기 C/조달·현재 source 검토/farm 서명,
불변 결합 결과/같은 상태 실제 잎3D로 연결한다. 현재 결과는 UI에 미연결이다.
5177은 예정된11:48KST에 종료됐고5175 제작 외형만 유지한다.

실제 품종/국내 독립 자료0·G0–G4/R2·빈 수관/제거·공급 제한 면적·한 작기/생산/자원·Decimal 경제,
거시/수급·자율 작물 비교/제품 통합·주앱 전체 build/실제 표시 창과 전체 완료일은 미완료·미정이다.
자체 합성 개발과 독립 자료 확보를 병행하며 이 투영을 전체 작기 재개나 관문 승인으로 바꾸지 않는다.

판단/구현은 현재 **Codex CLI gpt-6.1-sol / xhigh**, 재귀 CLI0이다.
turn_context2026-10-26T03:32:57.090Z, raw LF SHA
`3353d71e36b4baa2faa31ff8f378bced53ac9c1aa344e0e34599da171c68d8a9`,
관측2026-10-26T03:36:27.781419Z. 출력은 계약/계산·선언/재현 절차·검증이며 관문 결정이 아니다.
