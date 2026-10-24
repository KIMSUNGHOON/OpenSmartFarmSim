# 잎 제거 후 실제 생장 구간과 분할 재개 — 2026-10-24

상태: **합성 첫 사건→다음 구간의 계산·재개 소프트웨어 수용**.
[계약](../contracts/growing-geometry-removal-next-interval-v1.md),
[구현](../backend/app/crop_growing_geometry_removal_next_interval.py),
[시험](../backend/tests/test_growing_geometry_removal_next_interval.py),
[독립 RK4 산술](growing-geometry-removal-rk4-reference.py),
[기계 증거](artifacts/growing-geometry-removal-next-interval-20261024.json),
[24조건 장부](artifacts/growing-geometry-removal-next-interval-20261024.csv).
새 불변 저장/같은 상태3D·전체 작기/생산·제품 관문 승인은 후속이다.
[현재 화면](http://localhost:5176/growing-geometry-replay.html)은 기존 합성32초 저장 재생을 유지한다.

## 실제 전진과 수지

제거 후 문맥의 현재 a/A·C/N·기후에서 원 shared-stage RK4를 수행한다.
현재 RHS 검증1회 뒤 각 걸음의 k2/k3/k4·endpoint4회와 같은 stage21개 flux를 적분한다.
원 global 격자/Fraction 경과 시각·D0/초기 영수증을 유지하고 현재 A를 초기 curve에 다시 맞추지 않는다.
제거된 잎은 새 목록에 없으며 남은 잎 면적/나이와 작물·기후 상태가 실제로 전진한다.

원21장부·사건 C/표현된 용량/signed 현열·새 segment21장부를 분리했다.
사건 직후부터의 segment 수지와, 원 parent seed부터의 C/N·수관/공기 현열·증기·용량/reduced energy·각 남은 잎 시계를 함께 검사한다.
global budget은 원 budget+대응 point budget+segment budget+global 원 항 규모64ulp를 합친 수치 회계 경계다.
어느 재고·원 장부도 이 예산에 맞춰 보정하지 않는다. 이 예산은 생물학적 정확도나 신뢰 구간이 아니다.
과실 N·공기/증기·나이의 사건 항0은 이 명시 첫 제거 모델에서 해당 상태를 바꾸지 않는다는 뜻이다.
실제 수분/조직·엔탈피를 검증한 것이 아니다.

최종 checkpoint는 별도 모델/코드와 원 post-context/source를 결속한다.
원 전체 D0/초기 영수증·제거 마지막 상태는 불변 context에 보존하고 checkpoint에 각각 SHA를 실었다.
active D0/현재 상태는 직접 보관해 원512잎 범위에서 같은 CP256KiB를 유지했다.
hold는 실패 시각/단계/이유·실패 직전 상태와 유효 confirmed checkpoint를 남기며 실패한 endpoint를 반환하지 않는다.

## 통과한 검증

- 모듈 부재 RED를 확인했다. 최초64통과 뒤 payload의 반복 원 영수증을 source SHA 결속으로 바꾸고 검증을 확장했다.
  **최종93검사**가198.59초에 통과했다. 그 후 앱 코드는 바꾸지 않고 실패 경계3검사만 추가했다.
  새3+기존 post-context82/point71/parent continuation160의 **316검사**도140.09초에 통과했다.
  고유 수는 **96신규+313관련=409**이며 최초64와 반복 fixture는 합산하지 않는다.
- 여섯 zero-continuous-outflow 조건×초기/중간 사건×한 잎/동시 두 잎의 **24경로**를 검사했다.
  dt1⁄8초/전체2초의 원 horizon을 이어 actual area/age·C/N·기후를 전진했다.
  초기 사건15cut×12경로와 중간 사건8cut×12경로, 합 **276단일 cut** 및 예산1/3의 sample·누적량/최종 bytes가 같다.
- 원점 C/U/증기 수지를 별도120자리 Decimal로 대사했다. 사건 항을0/두 배로 넣는 반례는 global 수지에서 거부했다.
  코드/source/단위/시각/장부·현재 상태/수지/active D0/형상·예산·다른 모델/문맥과 크기 경계를 거부했다.
  k2/k3/k4/endpoint·segment/global 수지·checkpoint 실패에서도 마지막 유효 prefix bytes와 확인 상태를 보존했다.
  남은 horizon0은 재전진할 수 없다. 초기화/과거 replay/point 재적용을 차단한 상태에서 복원/재개가 통과했다.
- 원512잎→511잎의 실제 한 걸음도 통과했다. checkpoint **202,019bytes**, 응답의 typed handle을 SHA로 표현한 JSON은 **248,710bytes**다.
  각각256KiB/2MiB 안이며 한도를 늘리지 않았다. 실제 농장/전체 host 운영 용량 수용은 아니다.
- 별도 producer/fresh 프로세스의 **24context/324시점**, **35,964상태 성분·504누적량**을120자리 Decimal RK4 driver와 대사했다.
  driver 자체는 app을 import하지 않는다. callback에서 이미 검토한 공동 RHS를 재사용하고 flux packing/단계 이동·가중합은 독립 구현했다.
  따라서 새로운 독립 생물학 모델/농장 검증이 아니라 수치 조립 검증이다.
  최대 상대 차이는 **9.36636150548447e-16**, 기준은 `max(64ulp(reference),3e-13*abs(reference))`이며 참조0은 정확0이다.
- fresh의 **204개 global 수지**도 별도 Decimal 식으로 대사했다. 최대 roundoff budget 비율은 **0.014176074939200227**이다.
  원 전체 영수증/D0의 SHA·과거/사건 장부, producer CP 전 bytes와 전체 sample prefix SHA를 확인했다.
  source parent6개는 fence 전에 재구성했다. 그 후 post-context 준비의 point24/RHS48,
  현재 CP 복원 RHS24와 독립 reference RHS1,224회만 실행했다. fresh에서 engine advance/과거 전진·point replay0이다.
  DB/CLI/network/쓰기 시도0·원 bundle/FD 보존을 확인했다.

최종93 guard는199.735초·최대PID78,979,072bytes/합산446,734,336bytes,
경계/관련316은141.184초·78,979,072/455,888,896bytes,
fresh는26.555초·78,979,072/458,760,192bytes였다.
512MiB/PID·1GiB 소유+보호 합산·0.25초 표본/600초/로그4MiB를 유지했다.
각 phase의 원3,545항목·소스/보호4root·FD4→4/소유 잔류0을 확인했다.
새 서비스·의존성/DB/키 변경0이며 Windows/전체 host 메모리·성능 수용은 아니다.
전체 backend·hosted CI·브라우저/배포 검증은 이번 Python 자식에서 실행하지 않았다.

native Codex CLI `gpt-6.1-sol/xhigh`, turn_context2026-10-24T11:23:05.459Z,
원 LF SHA `c80da001e6ee7b5931b7b104127f7011f66b5e0e8f8b75237016a980511f263e`·재귀 CLI0으로 판단했다.
새 농업 계수/자료·관문 채택은 없으며 원32초/nonzero outflow6프로그램은 이 제거 모델로 바꾸지 않았다.

## 다음 사용자 산출물과 의존성

다음은 **사건 전/직후/다음 구간의 불변 저장과 계산 없는 reader**다.
원 request/profile/notice·point 입력/현재 C 분포·parent/post-context/engine 코드·각 CP/장부/ID/D0·정확 시각/phase를 결속한다.
같은 시각의 사건 전/후 상태를 다른 phase로 구분하고 완료 root를 마지막에 게시한다.
현재 권리/변조/부분 실패를 거부하며 별도 reader는 생장/point/재개 import·계산/DB/CLI/network/쓰기0으로 원 값을 투영한다.
그 뒤 strict export/SDK→기존 사실적 renderer의 원 ID에 따른 잎 제거/같은 상태3D·표/그래프를 수용한다.
계산하지 않은 과실·키/전체 작기나 과장한 애니메이션을 추가하지 않는다.

저장/reader 자식은 계약30–45분+writer/reader 재사용70–120분+변조·불변/fresh60–100분+기록20–35분으로
**180–300집중분**의 낮은 신뢰 추정이다. SDK/3D는 저장 계약 뒤 별도로 분해한다.
이전190–320분 예상은 이번 짧은 구간 수용 기록으로 대체하며 전체 완료일 약속으로 환산하지 않는다.
실제 cultivar/국내 원 측정·미사용 독립 작기0, 복수 사건/출현·공급·전체 작기/생산·자원·Decimal 경제·거시/수급·자율 비교와
현재 farm/권리 runtime·실제 CLI G1 종단 간·G0–G4/R2는 남는다. 자료 확보는 개발과 병행하며 전체 제품 완료일은 미정이다.
