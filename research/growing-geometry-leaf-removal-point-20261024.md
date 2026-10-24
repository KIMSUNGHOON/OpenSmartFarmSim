# 독립 면적의 명시 잎 제거 point — 2026-10-24

상태: **순간 연구 계산의 소프트웨어 수용**. [계약](../contracts/growing-geometry-leaf-removal-point-v1.md),
[구현](../backend/app/crop_growing_geometry_leaf_removal_point.py), [시험](../backend/tests/test_growing_geometry_leaf_removal_point.py),
[기계 증거](artifacts/growing-geometry-leaf-removal-point-20261024.json),
[독립288수량](artifacts/growing-geometry-leaf-removal-point-20261024.csv).
시간 전진/적분·새 저장3D·farm 게시/관문 승인과 전체 goal 완료가 아니다.
사용자 화면은 앞서 수용한 [32초 저장3D](http://localhost:5176/growing-geometry-replay.html)를 유지한다.

## 계산 범위

원 continuation context/checkpoint bytes·신뢰한 SHA/코드/profile/수지와 정확 경과 시각을 검증한다.
모든 현재 잎에 별도로 선언한 CH2O/floor가 원 leaf C 재고와 같아야 한다.
한 잎 또는 동시 batch가 명시한 탄소·표현된 용량·signed 현열을 같은 시점에서 한 번 차감한다.
SLA로 면적/질량을 역산하거나 기존 SLA 제거 함수를 호출하지 않는다.
고정 면적당 k와 실제 현재 A에 대한 별도 용량 선언, `Tout=Tc`의 명시 사건과 현열 선언을 대사한다.
실제 물질/엔탈피·수분/조직 물성을 검증한 것이 아니며 [선행 근거와 회계의 한계](explicit-area-canopy-energy-primary-sources-20261024.md)를 유지한다.

남은 잎의 a/A·원 D0와 초기 영수증, 다른 C/N·필터/공기·증기와21개 과거 누적량은 보존한다.
Uref에서 명시 현열을 빼고, 남은 용량으로 복원한 Tc는 기존2e-13K 안에서 같다.
사건 장부를 과거 구간 장부에 몰래 섞지 않으며 새 출력은 기존 continuation checkpoint로 수용되지 않는다.
원 현재 상태에 대한 동일 입력 재실행은 동일 bytes다. 영속 exactly-once·농장 권한은 후속이다.

현재 모델의 연속 leaf C 제거나 capacity_outflow가0이 아니면 기관 귀속을 확인할 수 없어 hold한다.
기존 여섯 저장 프로그램의 capacity_outflow=0.0001도 이 첫 point에서는 거부한다.
원 프로그램/32초 결과를 바꾸지 않았다. 수용 사례는 **새로 명시한 zero-continuous-outflow 조건**이다.
완전 제거/빈 수관·비혼합 유출·k 변경·출현/공급과 다음 구간은 별도다.

## 실제 검증

- 모듈 부재 RED를 확인했다. 초기58검사 뒤 경계를 확장한 검사에서69통과/1fixture 실패가 있었다.
  512잎 시험 helper가3잎 질량 목록만 만들던 IndexError를 고쳤고 수용 기준/구현은 바꾸지 않았다.
- 신규70+관련356의 **426검사**가135.60초에 통과했다. 이후 정확0 Uref/현열 검사를 추가해 신규 **71**을5.10초에 다시 통과했다.
  고유 수는 **427=71+356**이며 중복 배치를 합산하지 않는다. 관련356은 continuation160·short integration51·면적 현열145다.
  최종 추가는 시험1개뿐이고 수치 구현은426검사 때와 같다.
- 여섯 조건의 초기/중간7/완료16,1⁄8초 dt·한 잎/동시 두 잎 제거, 음/양/정확0 현열,
  512잎·남은 ID/면적/나이/D0와 다른 상태 불변·동일 재실행을 확인했다.
  코드/profile·context/원 CP SHA·bytes·시간/질량 분포/단위/중복·missing/비유한/subnormal·2MiB·완전 제거와 연속 유출을 거부했다.
- 별도 fresh 프로세스에서 같은6조건의 **36point/288수량**을120자리 Decimal/Fraction 참조와 대사했다.
  새 조건은 dt1⁄8초×16, 즉2초 범위이며 실제 작기 자료가 아니다.
  C_leaf/LAI/용량/Uref/Tc·제거 C/용량/현열의 최대 상대차는 **2.91037369412283e-16**이다.
  기준은 `max(32ulp(reference),3e-13*abs(reference))`, 참조0은 정확0이다.
  동일 계산을 두 번 수행해 bytes를 대사했고 현재 checkpoint 복원 RHS72회만 실행했다.
  새 초기 정규화/과거 replay·시간 전진/적분0·DB/CLI/network/파일 쓰기 시도0, 입력/CP/D0·과거 누적량/FD 보존을 확인했다.

관련 배치 guard는136.491초·최대PID81,469,440bytes/합산457,719,808bytes,
마지막71은6.139초·81,469,440/422,600,704bytes,
fresh는5.090초·81,469,440/403,709,952bytes였다.
512MiB/PID·1GiB 소유+보호 합산·0.25초 표본/600초/로그4MiB를 유지했다.
각 phase의 원3,545항목·소스/보호4root와 FD4→4/소유 잔류0을 확인했다.
Windows 메모리/전체 host 운영 용량은 위 관측 범위 밖이다.
전체 backend·hosted CI/브라우저 회귀·제품 배포는 이번 Python 자식에서 실행하지 않았다.

native Codex CLI `gpt-6.1-sol/xhigh`, turn_context2026-10-24T10:34:59.052Z,
원 LF SHA `f02201e2ad36461178006cadca8377c38bad67aeed99fc150343044477f2a0dd`·재귀 CLI0으로 판단했다.
새 농업 계수/원 자료·권리/관문 채택은 없으며 제어체적 원리를 실제 잎 열역학 검증으로 확대하지 않는다.

## 다음 단계·외부 의존성

다음은 **제거 후 상태를 보존하는 별도 continuation 문맥**이다.
원 parent/context·사건 SHA/선언·정확 시각/footprint/k와 남은 ID/a/A/D0·초기 영수증·21누적량/별도 사건 장부를 고정한다.
현재 A를 초기 curve로 다시 맞추거나 기존 context의 고정 길이 checkpoint를 위조하지 않는다.
초기화/전진 없이 새 문맥/복원까지 먼저 수용한 뒤 사건→다음 연속 구간·분할 재개/독립 C·열·물 수지를 검증한다.
그 후 새 사건 결과의 불변 저장/같은 상태3D→출현·공급/전체 작기→자원·생산/경제·거시/수급·후보 비교 순서를 유지한다.

다음 문맥 자식의 경계 대조30–50분, 최소 구현50–90분, 반례/fresh40–70분, 기록15–30분으로
**135–240집중분**을 낮은 신뢰로 추정한다. 다음 구간/3D·작기 전체의 완료 약속은 아니다.
현재 farm/서명 custody·실제 CLI G1 종단 간과 국내 원 측정/미사용 독립 작기0·첫 품종 미확정은 병행 과제다.
실제 G0–G4/R2·예측/미래 수익·자율 추천과 전체 제품 완료 날짜는 계속 미평가/보류·미정이다.
