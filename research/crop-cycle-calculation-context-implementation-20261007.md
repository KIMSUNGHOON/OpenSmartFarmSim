# 원 입력 검증 증명을 사용하는 새 계산 문맥

2026-10-07 KST. [계약](../contracts/crop-cycle-calculation-context-v1.md)의4 core파일을 구현했다.
**작은 순수 계산 경로만 로컬 수용했다. 실제166일 전체 실행·등록 농장/custody·저장/API/3D 수용은 별도다.**

## 구현과 판본

[새 factory/module](../backend/app/crop_cycle_calculation_context.py)은 정확한 `InputEvidenceAuthority`가
발행한 원 전체 QC/context 증명과 현재 입력 bytes·프로필/코드·키/issuer를 검사한다.
전용 `CalculationContext`/`crop-cycle-verified-execution-research-v1`과
`crop-cycle-verified-checkpoint-v1`로 구분하며 원 private token·조회 타입의 계산 허용·동적 객체 구성을 쓰지 않는다.
원 input normalization과 과거 checkpoint/manifest/result bytes를 바꾸지 않았다.
manifest는 원19개 key와 닫힌7개 필드의 `input_validation`을 결속한다.

5개 실행 제어 함수와 private paged reader는 원 소스의 식별자 변경 후 AST와 정확히 같다.
물리 계산/clock·격자 helper5개와 직렬화/해시 helper2개를 명시적으로 재사용한다.
이 소스 대조는 수치 정확도나 현재 권리의 독립 검증을 대신하지 않는다.
checkpoint SHA는 정합성 검사이며 계산 출처의 인증은 다음 server custody의 이력/서명이 필요하다.
기존 artifact는 새 context를 거부하며 다음 작업에서 명시 새 writer/reader를 구현한다.

## 실제 집중 검증

[시험](../backend/tests/test_crop_cycle_calculation_context.py)의 최종 실행은
**새57개 + 기존 입력 증명33개 = 고유90통과/76.37초·종료0**, session75283이다.
서로 다른 판본의 반복32/36/51/89개 실행 수를 합산하지 않는다.

```bash
cd backend
nice -n 19 .venv/bin/python -m pytest tests/test_crop_cycle_calculation_context.py tests/test_crop_cycle_input_evidence.py -q
```

| 확인한 경계 | 실제 증거 |
| --- | --- |
| 원6프로그램 × 3예산 | 실제 물리 RHS·모든 원 sample/event·수지·steps/plan 동일 |
| 원/새 checkpoint | 같은1/1→7/13→10000/10000 예산에서121상태·seed/UTC/Fraction clock·counter·prefix 동일; version/root/parent/checkpoint SHA4개만 정체성 차이로 구분 |
| 원 numerical hold5개 | 원 hold·확정 과거·누적/출력/사건과 동일 |
| 별도 Python4개 | 초기·t0 commit·내부 걸음·pending event의 정확한 checkpoint와 남은 전체 chain/출력/사건 대사·FD 동일·실제 PID 종료 |
| 현재 원본/물리 경계 | root/blob/누락/여분/쓰기/디렉터리 교체·파일/디렉터리 symlink·다중 link·directory mode 거부/정리 |
| 소유/설정/판본 | 소유자 불일치는 EUID 검사 입력을 바꾼 합성 시험; 다른 OS 사용자 실험은 아님. key/issuer/code/notice·원/조회 타입·재해시한 불일치 checkpoint 거부 |
| 검사 비용/반환 | factory/각 public 계산 연산의 현재 bytes 검증2회; 원 parser/prepare 재호출 금지; 실제 RHS 중 변조 후 정상 반환 차단 |
| cache/FD | reader≤4개 stream·context≤2개 key; close/실패 후 cache 비움/FD 복원 |

디렉터리 mode·합성 owner mismatch의 첫 RED는2실패/1.34초·종료1이었다.
원 `CycleCustodyHold`가 새 경계에서 그대로 전파되어 전용 보류 타입 assertion이 실패했다.
새 모듈의 진입/반환·factory 경계에서 해당 오류를 `CalculationContextHold`로 변환했고 최종90개를 통과했다.
최초 root-cwd import 오류와 미구현 import 오류는 assertion body 실패와 구분해 receipt에 남겼다.

## 같은166일 입력의 factory-only 비용

원 입력 root·113,920,841bytes/750파일, 계획1,816,704걸음/47,811경계/374index page를 유지했다.
첫/마지막 실제 grid page와 원 initial/121 seed·clock도 대사했다.
아래는 같은 입력의 **새 nice19 프로세스에서 최초 QC와 입력 경로만** 측정한 값이다.
원 nice15 장시간 계산은 계속 실행 중이며 OS cache는 통제하지 않았다.

| 실제 호출 | wall초 | CPU초 | 원 전체 검사 / 현재 proof 검증 |
| --- | ---: | ---: | --- |
| 최초 전체 QC·원 context 생성·발행 | 31.882307 | 32.114515 | preflight1·prepare1 / 0 |
| 새 factory | 0.386465 | 0.387795 | 0 / 2 |
| 현재 재검사 | 0.185526 | 0.185961 | 0 / 1 |
| 초기 checkpoint 시작 | 0.389763 | 0.390997 | 0 / 2 |
| 초기 checkpoint 직렬화 | 0.390243 | 0.391540 | 0 / 2 |
| 초기 checkpoint 복원 | 0.383002 | 0.384078 | 0 / 2 |

RHS guard0회·전체 FD4→4·cache 정리·원55 source SHA/입력 metadata+bytes/spec 보존을 확인했다.
50ms 활성 RSS 표본 최대89,038,848bytes, 최종 kernel VmHWM88,760,320bytes다.
두 지표는 별도 관측이며 순간 peak의 완전 포착을 보장하지 않는다.
CPU에는 메모리 표본 thread가 포함된다. 단계별 FD 표본에는 그 thread의 `/proc` 읽기가 섞일 수 있어
종료 후 FD4→4를 누수 대사로 사용한다. secure helper I/O 수는 parser/direct page 읽기를 포함한 총 I/O가 아니다.
이0.39초를 실제 농장/DB/HTTPS 지연이나 전체 작기 처리량으로 외삽하지 않는다.

별도 작은 실제 계산은 [동일 참조 CLI](crop-cycle-calculation-context-reference.py)로
120걸음·603RHS·3시점/3관리 사건을2.366838초에 완료했다.
원 전체 parser를 금지한 상태에서 재개했고, 앞선89개 실행의 초기 복원 사례와 정확한 checkpoint/남은 결과를 대사했다.
50ms/47표본의 활성 RSS 최대78,700,544bytes·FD4→4·child 종료를 확인했다.
이 관측과 최종90개의4개 별도 Python 결과는 구분해 각각 불변 보존했다.

실제 native CLI `gpt-6.1-sol / xhigh`, source/로그·AST 대조·복원4개·큰 입력/작은 RHS 관측은
[불변 receipt](artifacts/crop-cycle-calculation-context-reference-20261007.json)에 결속한다. 재귀 CLI0회다.
검사 도구/키/원 결과는 재부팅 후 유지되는 사설0700 경로에0400으로 보존하고 키는 공개하지 않는다.

## 다음 단계와 남은 의존성

`crop-cycle-calculation-input-context`만 완료 처리한다. 다음은 별도 `crop-cycle-calculation-artifact`의
작은 writer/reader 계약·원량/UTC/순서·강제 종료/복원·현재 bytes/QC·조회 RHS0·자원 검증이다.
그 뒤 현재 farm/Scope·계산/표시 권리·등록/custody·DB/API/같은 UTC3D를 연결한다.
실행 중 원55 source 변경은 실제 종료·증거 보존 뒤에 한다.
순수 개발에 실제166일 성공이나 국내 독립 자료 확보를 추가 착수 조건으로 만들지 않는다.
전체 작기/저장·3D·부하 부모는 실제 전체 증거를 모두 요구한다.
생과 → 자원 → Decimal 경제 순서, 실제 품종 입력/국내 독립 자료0건·G0–G4 `not_assessed`와 생산 예측/추천 보류를 유지한다.
후속 완료 날짜는 artifact/farm 작업 분해와 실제 전체 실행·저장/API 비용을 확인한 뒤 갱신한다.
