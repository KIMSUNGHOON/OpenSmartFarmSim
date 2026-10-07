# 계산용 문맥과 저장 경계의 현재 코드 대조

2026-10-07 KST. native Codex CLI `gpt-6.1-sol / xhigh`에서 판단했다.
재귀 CLI는 실행하지 않았다. [실행한 AST 감사/소스 기록](artifacts/crop-cycle-calculation-context-inspection-20261007.json)은
현재 구현의 연결을 검사한다. 새 계산 모듈의 구현·성능 수용은 아니다.

## 확인한 연결

| 현재 소스 | 확인한 계약과 다음 작업의 영향 |
| --- | --- |
| [input stream](../backend/app/crop_cycle_input_stream.py) | 생성자가 원 preflight를 실행하고 normalization SHA에 자기 코드 SHA를 포함한다. 원 파일 변경은 기존 packet의 정체성에 영향을 준다. |
| [stream execution](../backend/app/crop_cycle_stream_execution.py) | `prepare_context`는 정확한 `InputPacket`, `_require_context`는 내부 token이 있는 정확한 `StreamContext`를 요구한다. context를 소비하는 공개 연산4개는 직접/간접으로 이 검사를 사용한다. |
| [input evidence](../backend/app/crop_cycle_input_evidence.py) | `issue`가 원 reader/QC/context를 실행한다. `verify`는 원 engine/code에 묶인 context·서명과 모든 현재 bytes를 대사하며 `StreamContext`를 발급하지 않는다. |
| [read context](../backend/app/crop_cycle_input_read_context.py) | 별도 조회용 타입과 bounded reader이며 계산 API를 제공하지 않는다. 이를 계산용 원 타입으로 위장할 수 없다. |
| [artifact](../backend/app/crop_cycle_artifact.py) | `_pins`가 원 engine의 context 검사를 호출하고 header/commit에 원 실행·checkpoint를 결속한다. 새 계산 타입의 저장은 별도 구현 의존성이다. |
| [farm binding](../backend/app/crop_cycle_farm_binding.py) | 원 exact reader 검사와 전체 preflight를 `_bind` 앞뒤에서 수행한다. 권리·등록의 전후 검사는 유지해야 한다. |
| [server custody](../backend/app/crop_cycle_server_custody.py) | exact reader를 열고 원 context를 준비한 뒤 journal/current 권리를 연결한다. 순수 새 context 수용만으로 이 경로가 연결되지 않는다. |

따라서 다음 첫 변경은 [계산 문맥 계약](../contracts/crop-cycle-calculation-context-v1.md)의
전용 factory/새 실행 판본이다. 원 source bytes·input normalization/manifest와 과거 결과를
보존하고, 새 판본의 수학값/clock·복원·변조/자원을 확인한다. 최초 원 QC의 증명을 소비하지만
원 private token을 외부에서 주입하지 않는다. 조회 타입은 계속 계산 인수가 아니다.

**새로 확인한 의존성:** 새 계산 타입 → 명시 새 artifact writer/reader → 현재 농장·권리/custody다.
기존 artifact는 새 context를 거부하므로 저장 경계를 건너뛴 농장 연결 수용은 불가능하다.
이를 `crop-cycle-calculation-artifact`로 분리했다. 기존 전체 RHS/조회·복원/부하 부모와
생과→자원→경제 순서는 유지한다. 신규 artifact의 정확한 파일/형식은 작은 계산 수용 후 확정한다.

## 검증 범위와 남은 일

AST 감사는 형 검사·발행/재검증 호출·원 preflight 두 호출 위치·artifact/custody 연결과
조회 타입의 public 계산 함수 부재를 확인했다. 원7개 소스 SHA와 실행 중55개 source 보존을 기록한다.
이는 미래 factory의 수치·권리·성능 검증이 아니며 새 프로그램 시험은 실행하지 않았다.
로컬 링크/anchor2,621개와 의존성 DAG109/89edge의 비순환을 확인했다.
기존103/89edge와 앞서 추가한 계산 연결4edge를 보존하고 artifact 의존성2edge만 추가했다.
기존 수용 checkbox는 그대로이며 세 계산 자식은 미완료다. 과거 시험 수치는 영수증 대사이고 재실행이 아니다.

구현 착수 전4개 이내 core파일·판본/과거 재생·수용 matrix를 계약에 분해했다.
현재 실행의 실제 종료/증거 보존 뒤 순수 factory/복원·변조/자원을 구현하고,
그 실측 뒤 artifact/등록 경로의 작업량·예상 일정을 갱신한다.
현재 전체166일 실험의 고정6시간 예산은 제품 완료일이 아니다.
실제 품종 입력·국내 독립 자료·실제 작물 Run은0건이고 예측·추천은 보류다.
