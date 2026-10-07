# 검증 영수증을 소비하는 계산 문맥 — v1 구현 계약

2026-10-07 KST. 구현 계약이며 [로컬 수용 보고서](../research/crop-cycle-calculation-context-implementation-20261007.md)의
작은 순수 계산 범위까지 확인했다. 전체 작기·농장/저장/API/3D 수용은 아니다.
선행 [입력 증명](crop-cycle-input-evidence-v1.md), [원 실행 의미](crop-cycle-stream-execution-v1.md),
[현재 코드 대조](../research/crop-cycle-calculation-context-inspection-20261007.md)를 따른다.
작업은 `crop-cycle-calculation-input-context`다. 아래 새 파일만으로 구현하고 원55개 source SHA와
현재 입력/spec을 보존하는 순수 개발은 실행과 병행한다. 동결 소스 변경은 실제 종료·증거 보존 뒤다.
현재55개 source 동결과 기존 전체 작기 부모의 수용 조건은 [계획](../tasks/plan.md)에 있다.

## 첫 변경의 경계

첫 core는 아래4개다. 실제 구현·시험·별도 프로세스 참조를 수용 보고서에 결속한다.

1. `backend/app/crop_cycle_calculation_context.py`: 공식 factory·전용 context와 순수 실행.
2. `backend/tests/test_crop_cycle_calculation_context.py`: 연속/복원·거부·자원 검증.
3. 이 계약.
4. `research/crop-cycle-calculation-context-reference.py`: 기존 실행과 별도 프로세스 대사.

원 input stream·engine·영수증·조회·artifact·custody 파일 bytes는 보존한다.
새 코드는 원 physical/continuation 함수와 고정된 격자·평가 helper를 명시적으로 사용한다.
원 engine에서 사용하는 helper는 `_boundary`, `_evaluator`, `_clock_record`, `_seal`, `_confirmed`로 한정한다.
직렬화/해시 helper `_canonical`, `_hash`도 원 구현을 명시적으로 재사용한다.
새 계수나 수식·시간 격자를 만들지 않는다. 실행 제어와 checkpoint 검사는 새 context의
정확한 형/판본을 검사하는 경계에 둔다. 원 engine private token을 가져오거나
`object.__new__`/외부 cache 주입·런타임 monkeypatch로 원 타입을 만들지 않는다.
제어 흐름을 이식하는 부분은 원 AST/연산 순서와 독립 수치로 대사하고 변경 지점을 기록한다.

## 공식 인터페이스

module은 다음 public 연산을 제공한다. 서버 설정이 authority를 공급한다.

```python
open_calculation_context(directory, input_root_sha256, evidence_raw, *, authority)
start(context)
advance_chunk(context, checkpoint, budget)
checkpoint_bytes(context, checkpoint)
restore_checkpoint(context, raw_bytes)
```

factory는 정확한 `InputEvidenceAuthority`의 `verify`로 서명·원 전체 검사 증명·현재 참조
bytes와 고정 프로필을 대사한다. 사용자가 보낸 dict/context나 서명 없는 초기 상태로
새 계산 문맥을 만들지 않는다. 최초 영수증 `issue`의 실제 전체 QC는 계속 필요하다.
증명의 원 initial/121 seed·Fraction clock·격자 index/계획을 새 전용 context에 결속한다.
원 `StreamContext`나 조회용 `InputReadContext`를 계산 인수로 받지 않는다.

context manager가 no-follow 입력 디렉터리 FD와 bounded reader를 소유한다.
실제 읽는 block은 SHA·metadata·단위/형태를 검사하고 stream별 한 block,
격자 한 page·평가 한 forcing 구간만 cache한다. 반환값은 내부 상태와 별도 사본이다.
닫기/실패 시 FD/cache를 정리하며 닫힌 객체는 다시 사용할 수 없다.
`rights_or_gate_approval`은 false다. farm/tenant/등록·현재 권리는 다음 연결의 검사다.

## 현재 bytes와 연산 경계

factory는 검증한 원본과 자신이 연 FD의 root/inventory·디렉터리 inode를 결속한다.
public 계산/복원 연산은 진입·정상 반환 전에 현재 bytes/판본을 재검사한다.
private helper의 중첩 호출마다 전체 검사를 되풀이하지 않도록 호출 수를 계측한다.
검사 뒤 변조의 미래 불변성을 주장하지 않으며 각 block 접근의 검사도 유지한다.
불일치 시 정상 checkpoint/result를 반환하지 않는다.

재검사는 원 전체 parser/preflight·격자 index 생성 없이 영수증을 검증한다.
원 schema/QC를 생략한 서명 생성, metadata만으로 전체 bytes 검사를 대체하는 cache,
새 입력을 이전 proof에 연결하는 동작은 허용하지 않는다.
실제 재검사·block load·RHS 횟수와 wall/CPU·활성 RSS/FD를 구분해 측정한다.
원 내부 `_input`의44.28초 관측을 이 factory나 전체 농장 경로의 속도로 재명명하지 않는다.

## 판본과 과거 재생

새 실행 ID는 `crop-cycle-verified-execution-research-v1`, checkpoint ID는
`crop-cycle-verified-checkpoint-v1`로 구분한다. 원 input packet/normalization은 바꾸지 않는다.
새 실행 manifest는 원의 물리·profile·정책·solver·UTC/clock 필드를 보존하고,
새 실행 code SHA와 입력 검증 provenance를 명시적으로 포함한다.
닫힌 key 집합은 원 `prepare_context` manifest의19개 key에 `input_validation` 하나를 더한 것이다.
`engine_version`은 위 새 실행 ID, `code_sha256.stream_execution`은 새 module SHA다.
나머지 원 manifest 필드는 같은 입력의 원 증명과 정확히 같아야 한다.
`input_validation`은 다음7개 key만 받는다.

| key | 고정하는 값 |
| --- | --- |
| `version` | 원 input evidence VERSION |
| `evidence_sha256` | 실제 검증한 영수증 bytes의 SHA |
| `validated_context_sha256` | 원 증명의 context SHA |
| `validation_engine_version` | 원 context manifest의 engine ID |
| `validation_code_sha256` | 원 context의 닫힌 input/engine/continuation code SHA map |
| `input_evidence_code_sha256` | 실제 authority module SHA |
| `input_evidence_dependency_sha256` | 실제 authority의 닫힌 dependency SHA map |

위 원 engine SHA가 다섯 helper의 출처를 고정한다. 실제 module/프로필/정책/Python과
현재 값을 대사하고 알 수 없는 key·fallback origin을 거부한다. 원 증명의 context SHA와
새 실행 root는 별개다. 증명을 새 계산 결과·현재 농장 승인으로 재발급하지 않는다.
원 결과/manifest/checkpoint bytes는 변환하지 않고 기존 조회 경로로 재생한다.
원 checkpoint의 root/version만 바꾸는 복원·묵시 migration은 거부한다.
여기서 checkpoint SHA는 정합성 검사이며 계산 출처의 인증이 아니다. 임의로 일관된 JSON을
재작성할 수 있는 호출자를 신뢰하는 경계가 아니며, 실제 farm 게시에는 후속 server custody의
계산 이력·서명이 필요하다. 이 순수 API는 원 server trace의 판본 변환을 제공하지 않는다.
새 checkpoint는 새 판본에서 시작한 실행의 별도 프로세스 복원에만 사용한다.
사용자에게 계산 engine 선택 옵션을 추가하지 않는다.

원/새 판본 대사에서는 UTC·121상태/seed·16누적·clock·counter·sample/event·수지·hold가
같아야 한다. engine/checkpoint version·실행 root·checkpoint/parent SHA는 판본 차이로
구분해 기록한다. 이 정체성 필드가 다른 사실을 숨겨 전체 byte-identical이라고 주장하지 않는다.
같은 새 판본의 연속/분할/별도 Python 복원에는 해당 checkpoint/chain 규칙을 모두 검사한다.

## 저장 연결은 다음 작은 작업

원 artifact의 `_pins`는 원 engine context를 요구하므로 새 context를 받지 않는다.
`crop-cycle-calculation-artifact`에서 명시 새 artifact 판본·writer/reader를 검증한 뒤
`crop-cycle-calculation-farm-binding`으로 현재 농장·권리/custody를 연결한다.
첫 순수 계산 수용으로 원 writer/DB/API/3D 호환이나 전체 작기 부하를 체크하지 않는다.
후속도 원 schema·공개 응답을 조용히 바꾸지 않고 작은 계약으로 나눈다.

## 첫 단계의 수용 기준

1. 원6프로그램의 연속·복수 예산 분할·사건/출력 충돌·hold를 원 실행과 대사한다.
   모든 원 물리량·온도 clock·전역 counter와 수지를 확인하며 임의 보정은 없다.
2. 새 checkpoint의 초기·내부 걸음·pending event·commit 경계를 별도 Python에서 복원한다.
   같은 새 판본의 상태/UTC·중복 없는 사건/출력·seed/누적/hold를 대사한다.
3. 잘못된 key/issuer·서명·code/profile/environment·root/blob·누락/여분·symlink/소유/권한·
   디렉터리 교체, 읽기 전후 변조, 원/조회 타입과 판본 혼합을 거부한다.
4. 최초 proof 발행에는 실제 원 QC를 사용한다. 이후 factory/복원/계산 경계에서는
   원 전체 preflight/prepare_context를 다시 부르지 않음을 계측한다. 실제 RHS는 계산 시 실행된다.
5. 유효한 큰 합성 입력의 factory/recheck만 별도 측정한다. RHS0인 이 관측을 전체 작기 실행으로
   보고하지 않는다. 실제 작은 계산의 활성 RSS/FD/cache와 종료 정리도 별도로 측정한다.
6. 기존 원 계산/조회 소스와 과거 영수증·원 입력을 보존하고 해시/집중 시험·검토를 기록한다.
   예상 새 파일·닫힌 manifest/실제 helper 목록을 구현과 대조한 뒤 자식 작업만 체크한다.

사용자 산출물은 원/새 물리값 비교·새 판본 복원·검사 비용/자원 보고서와 불변 receipt다.
전체166일 성공은 이 작은 개발의 추가 착수 조건이 아니다. 동결 소스 변경에는 현재 실행의 실제 종료·증거 보존이 필요하다.
실제 품종/수확·독립 현장 검증·예측/추천과 관문은 [제품 명세](../docs/PROJECT_SPEC.md)를 따른다.
