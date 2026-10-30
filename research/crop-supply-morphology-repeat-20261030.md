# 공급 제한 형상 반복 수용 — 2026-10-30

실제 후속 Context와 체크포인트에서 같은 새 family로 후보 계산·명시 조달·일정 단일 소비를 반복했다. 동일 합성 fixture에서 후속5출현·27확정 구간·원512초 종료를 확인했고, 전체/분할/출현별 cold 복원의 최종 Context와 CP 바이트가 같다. 이 범위의 소프트웨어 구현을 수용한다. 실제 품종·한 작기·수확/자원 구매/마진·작물 추천의 검증은 아니다.

[계약](../contracts/crop-supply-morphology-repeat-v1.md), [기계 판독 증거](artifacts/crop-supply-morphology-repeat-20261030.json), [중간 기록](crop-supply-morphology-repeat-progress-20261030.md), [계획](../tasks/plan.md), [남은 작업](../tasks/todo.md).

## 계산과 저장복원

- 실제 공개 pytest fixture를 생성·저장하고 별도 프로세스의 공개 복원 API로 실제 권한 계보를 재구성했다. 과거 typed handle을 가장하지 않았다. 원 시작 체크포인트는 `305181/1024`초이며 원래 끝점은512초다. 전체512초를 새 모델로 처음부터 계산했다는 뜻은 아니다.
- 공개 전체 반복 검사 함수를 그대로 실행했다. 명시 optional leaf·0/0.01m 줄기 seed를 섞은 후속5조달, 일정/ID 단일 소비·기존 형상/탄소/열 원점 보존과 전역 수지를 확인했다. 새 seed를 자동 추정하지 않았다. 원 threshold 경계5곳에서는 먼저 hold하고 입력을 명시한 뒤 채택했다.
- 같은 시작 상태에서 구간 budget3으로12회 호출했다.6회 yield·5회 pending hold 후 종료했으며 전체 계산의6회 호출과 모든 확정 sample/interval·각 출현 직후 seed CP·최종 바이트가 같다. 실제 stage 호출312→318의 차이6회는 추가 현재 상태 검증이다.
- 출현마다5회 Context/CP를 저장·복원했다. Context RHS0·CP 현재 RHS1회이며 과거 적분·후보·조달·fund·초기화10종을 차단한 계측에서 모두0회다. 세 번째 출현에서 프로세스를 나누고 다음 프로세스가 같은 저장 바이트를 복원해 원 끝점까지 이어갔다. 별도 최종 전체 복원도 바이트가 같다.
- 앱 import/RHS0인 Fraction/Decimal200 검사로 상태46,752값·유량11,024값·전역 합1,248항목·형상342식·탄소120식·시계114식과 조달5점/정밀 분할35구간을 대사했다. 독립 작물 생리 측정이나 ODE 오차 인증은 아니다.

최종 Context2,034,607bytes/2,097,152bytes, CP121,961bytes/524,288bytes다. 손실 없는 receipt 참조는 직전 genuine seed/현재 코드 지문만 사용하고, 확장 전 크기와 원 canonical 지문을 검사한다. 원512 inventory/32768 scalar 한도를 유지한다. 이 입력은 Context 한도에 가까우므로 최대 inventory나 전체 작기 지원·처리량을 수용하지 않는다.

## 집중 검사와 보존

기존 집중19개와 새 실패 행렬69개를 별도 실행해88개를 통과했다. 새 행렬은 genuine fixture를 사용했다.

- 재해시 Context/CP의 상태·시각·일정·장부·prefix·scope/관문/추가 필드 변경을 거부했다. Context/CP wire 한도와 endpoint budget도 확인했다.
- 조달 자금 부족은 `FUNDING_HOLD`, 표현에서 사라진 작은 debit은 `NUMERIC_HOLD`로 거부했다. 부적합 seed/ID/기하/온도/권리·외부 CP/허용오차·복사한 후보 capability와 issued 객체 재해시 변조도 거부했다. 정상 prepared 재사용의 RHS는0회다.
- 현재 프로필/접근권 변경은 재사용을 막았다. 두 번째 구간의 domain 실패는 첫 확정 endpoint만 보존했다. 늦은 코드/프로필/접근권·caller CP/stage 입력 변경은 공개할 수 없는 prefix를 모두 제거했다. 입력 capture 뒤 caller 변경과 재해시 receipt의 funding/state/원점/부모/budget/초기화 변조도 거부했다.
- 기존225source/1output closure와 원 자료·private:false132blob·봉인 GUI4,865파일·기존 public/export/경계 파일을 대사했다. 보존 단계에서 기존5175 HTTP200을 확인했다. 새 반복 UI/DB/API/worker를 띄운 결과는 아니다.

전체 backend/frontend suite와 새 브라우저 수용은 실행하지 않았다. CI는 로컬 증거와 별도이며, 작업 전 HEAD `7ad59ac5dd6a3fd0ba1b70941abdae0e0b1a4ece`의 실제 GitHub API 조회는0runs였다.

## WSL 실측과 실패 기록

| 단계 | Guard wall | 결과 |
| --- | ---: | --- |
| 실제 초기 fixture 생성/저장 | 179.007초 | 통과 |
| 전체 원512초 경로 | 490.337초 | 통과 |
| 분할/cold 1: 후속3출현까지 저장 | 321.780초 | 통과·중간 종료 |
| 분할/cold 2: 저장 복원→원512초 | 305.462초 | 통과·전체와 최종 바이트 일치 |
| 새 실패 행렬69검사 | 529.960초 | pytest69 passed |
| 원 자료/화면 보존 | 2.277초 | 통과 |

모든 단계는 원600초·PID512MiB/합산1GiB·로그4MiB 한도 안에서 종료했다. 원 서비스·자료와 controller FD4→4를 보존했고 소유 자식은0개다. 이 표는 검증 공수이며 제품의 최초 대기 시간이나 처리량 보장이 아니다. 초기 생성179초와 계산490초는 별도 비용이다. 초기 생성과 계산을 합친 이전3회600초 미완료, 검사기의 유량 순서 오류와 수정 기록은 [중간 기록](crop-supply-morphology-repeat-progress-20261030.md)에 남겼다. 모델·계수·허용 budget을 바꾸어 통과시키지 않았다.

## 다음 산출물과 외부 의존성

다음은 이 계산의 불변 결과와 계산 없는 reader다. 같은 A/L/C/clock/ID/UTC/phase·원점/장부·권리를 보관하고 별도 프로세스의 조회에서 생장 import/RHS·CLI·DB/network/write0을 확인한다. 이어 export/strict SDK를 수용한 뒤 같은 저장 상태를 실제 잎·줄기 mesh/표/그래프에 연결한다. 새 반복 결과는 아직 기존 웹에 반영되지 않았다. 과실 상태가 없는 구간에서 과실 성장이나 수확을 만들지 않는다.

저장 schema·실제 packet 크기·조회 경계를 확인한 뒤 export/SDK와 브라우저 검증 공수를 다시 추정한다. 이전 저장3D180–300분은 미수용 초안이며 완료 날짜가 아니다. 전체 작기에는 현재 Context 크기와 계산량 제약의 검증도 필요하다. 독립 국내 단일 품종 자료·계수 채택0, 접근/자료별 권리·단위/QC·판본/available_at·독립 미래 작기·후보 비교는 병행 외부 의존성이다. 확보일과 전체 제품 완료일은 미정이다.

실제 native Codex CLI `gpt-6.1-sol/xhigh` turn의 invocation metadata/출력 지문을 기록했고 재귀 CLI0회다. G0–G4 `not_assessed`, R2 `not_approved`와 전체 goal active/incomplete를 유지한다.
