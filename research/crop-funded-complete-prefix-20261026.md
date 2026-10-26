# 시작부터 분기 후까지의 전체 확정 이력 결속 — 2026-10-26 KST

**합성512초 계산의 시작·원 조달점·분수 출현 전/후·새 격자·끝을 한 이력으로 결속했습니다.**
[계약](../contracts/crop-funded-complete-prefix-v1.md),
[구현](../backend/app/crop_funded_complete_prefix.py),
[집중 검사](../backend/tests/test_crop_funded_complete_prefix.py),
[검증 JSON](artifacts/crop-funded-complete-prefix-20261026.json).
일반69시점과 추가점70시점의 소프트웨어 연구 이력이며 전체 작기/실제 작물·G0–G4/R2 승인이 아닙니다.

## 실제 자료 연결

원본의0번부터 선택한 왼쪽 frame까지만 사용합니다. 그 뒤의 원본 미래 상태는 새 branch에 이어 붙이지 않습니다.
원 CP의 canonical bytes/hash·원 state/단위/시각·phase/event/cursor/누적/장부와 원 부모 ID를 보존합니다.
분수 시각의 출현 직전 상태는 기존 검증된 dense candidate를 사용하며 **checkpoint는 없습니다**.
원 source 누적과 checked partial interval을 합친 누적/정확 잔차를 보존하고 가짜 구간 번호/CP를 만들지 않습니다.
이 시점에는 수치 출현한 새 절간이 존재하지만 새 잎의 재료점은 아직 반영되지 않았습니다.
이후 실제 after-point CP·각 원 격자 CP를 연결합니다. 같은 시각 추가점은 새 context/원 이력/직전 CP에 결속합니다.

기존/새 기관의 시계와 원 곡선/앵커·잎 ID/부착은 앞서 수용한 source binding을 재사용합니다.
원 기온 적분량을 각 시점의 계산에 사용하며 옛22도 forcing이나 임의 시각/위치를 추가하지 않습니다.
빠진 seed/격자, 역순·반복/다른 이력·변경 초기 링크·잘못된 prefix와 끝나지 않은 horizon을 거부합니다.
source prefix는 과거 ODE/초기화 없이 결속하고, 새로운 CP의 검증은 현재 RHS 각1회입니다.
이력 해시/시각 검사 자체가 과거 ODE 재적분이나 농장 서명/보관 권한을 뜻하지 않습니다.
외부에서 복원할 때의 expected SHA는 기존 계약대로 신뢰한 원본/생산자 증거에서 받아야 합니다.

## 크기 제한과 유일한 상태 원본

최초 표현은 원 CP 안의 상태/누적/장부를 각 frame에도 복제해2MiB를 넘었습니다.
누적/장부의 중복을 제거한 뒤에도 이른 추가 출현2경로가 한도를 넘는 것을 실제 검사로 확인했습니다.
원 snapshot/C_i/a/A도 CP에 한 번만 보관하고 frame의 leaf 행은 ID/부착/출현·curve SHA를 가리키도록 보완했습니다.
CP 없는 dense point만 원 snapshot/합성 누적·장부를 별도로 보관합니다.
원 숫자/ID/CP·계수와2MiB/512frame/32768scalar 및 하위 cap은 변경하지 않았습니다.
크기 때문에 프레임을 생략하거나 데이터를 압축해 수용한 결과가 아닙니다.

## 검증 결과

- **최종16검사:** 원 시작/조달점/왼쪽 frame·dense-before/after·원 격자/끝,
  같은 시각/중간/마지막 추가 context의70시점과 초기 링크/실제 CP chain,
  누락/역순/미완료/반복 이력·잘못된 hash/prefix·상한/코드와 외부 효과를 확인했습니다.
- **일반6경로414시점+추가6경로420시점=834시점**을 별도 프로세스에서 생성·결속했습니다.
  exact shoot/기관 나이 **3,790개**, Decimal110 길이 **2,956개**,
  프로그램/잎 순서와 원 vector의 잎 상태 **13,788개**의 형식/보존을 확인했습니다.
  원 CP **380개**의 실제 bytes/hash와 각 경로의 CP 없는 dense-before1개(합12개)를 대사했습니다.
- 각 경로의 마지막 CP12개는 기존 수용 결과와 바이트가 같았습니다.
  일반/추가 경로의 동일 확정 prefix는 각각37/28/32/37/37/37frame, 합208frame이 정확히 같았습니다.
  근 구간·첫 before/after의 원 시각/나이0·old/new 기관·잎 ID/부착과 모든 원 cursor를 보존했습니다.
- prefix 결속12회의 RHS는0회였고 새 CP 검증은 각각 현재 RHS1회, 합442회입니다.
  실제 새 격자 전진의 stage/현재 검증을 포함한 전체 RHS는 일반1,278+추가1,284=2,562회였습니다.
  과거 prepare/advance/점·초기화·DB/CLI/network와 출력 밖 write open은 모두0회였습니다.
- 일반 packet은 최대 **1,771,355bytes**, 추가 packet은 최대 **1,867,742bytes**로2,097,152bytes 안입니다.
  최초 입력 source497+이전 결과43=540파일과 이후 일반 결과13을 더한553파일의 bytes/metadata를 보존했습니다.
  새 출력은 일반13/추가19, 합32파일이며 각자 별도 namespace에만 생성·동결했습니다.
- 주 검사341.335초/WSL 소유+보호 합142,557,184bytes,
  일반 별도381.763초/121,675,776bytes, 추가 별도390.014초/124,882,944bytes였습니다.
  512MiB/PID·합1GiB·0.25초/600초/로그4MiB, 보호1root·원4500항목/source·소유 잔여0/FD4→4를 유지했습니다.
  Windows RSS는 측정 밖입니다. 최대 길이 상대차는 3.7475708930459498e-16이며 물리 오차 보증이 아닙니다.

[자체 QA 선언](../fixtures/crop-funded-complete-prefix-fixtures-v1.json)과
[재현·독립 대조](verify-funded-complete-prefix.py)를 추가했습니다.
기존 자체 공개 source/context/선언만 재사용했고 새 품종/측정/계수를 채택하지 않았습니다.
독립 대조는 Fraction 시계와 Decimal110 길이, 원 bytes/실제 CPP와 프로그램·잎 순서/값의 보존을 검사합니다.
RHS는 기존 검토 코드를 공유하므로 독립 농업 모델/현장 검증으로 승격하지 않습니다.

## 다음 수용 기준과 일정

다음은 이 이력의 **불변 producer/계산 없는 reader**입니다. 원 source/notice·raw context/CP/candidate,
초기 링크/권리/현재 코드·profile과 각 frame의 같은 시각/ID/기관·누적/장부를 묶어 root를 마지막에 게시해야 합니다.
조회는 source/권리/단위·순서/phase·현재 파일/코드/해시를 재검사하고 생장 모듈 import/ODE·DB/CLI/network/쓰기 없이
원 값을 반환해야 합니다. 부분 실패/변조·현재·늦은 권리·읽기 범위/상한·별도 프로세스를 검증합니다.
그 뒤 export/strict SDK→같은 저장 시각·상태의 실제 잎3D/표·그래프·사용자 브라우저로 연결합니다.

기존3.5–7집중시간 계획 중 prefix/점 전후 결속은 이번 증거로 대체합니다.
저장 계약0.5–1시간+producer/reader1.5–3시간+집중/별도 검증0.75–1.5시간, 합 **2.75–5.5집중시간**의 잠정 작업량입니다.
기존 fixed-grid59검사·새 실제414/420frame 구조를 근거로 하며 UI/브라우저·외부 자료 확보는 별도입니다.
새 의존성이 확인되면 갱신하며 전체 완료 날짜는 아직 산정하지 않습니다.

이번 결과는 UI미연결이며 [5175 제작 외형](http://localhost:5175/crop-appearance.html)을 유지합니다.
전체 backend/build·새 브라우저/R2와 최대512 API 행렬은 이번에 실행하지 않았습니다.
동일512잎 요청의528,002/524,288bytes hold, 새 절간의 독립 C 배분·초기 잎 과거 출현/생물학적 배치,
후속 자동 출현/빈 수관/제거·실제 첫 품종/독립 국내 자료0건·한 작기/수확/자원/경제·거시/수급/자율 비교·제품 통합과
G0–G4/R2·전체 완료일은 미완료·미정입니다. 전체 goal은 active입니다.

판단/구현: **native Codex CLI gpt-6.1-sol / xhigh**, 재귀 CLI0회.
turn_context `2026-10-26T11:36:06.715Z`, raw LF SHA
`01106a9e6fa28cf79dcca6721e7339d0721bd3bd8e523f372c64ca7d7e19a387`, 관측 `2026-10-26T11:36:52.578990+00:00`.
출력은 계약/구현/시험 증거이며 관문 결정이 아닙니다.
