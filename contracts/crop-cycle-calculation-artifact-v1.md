# 새 계산 판본의 불변 결과 파일과 재개·조회 — v1

2026-10-07 KST. 구현 전 고정한 계약이며 [로컬 소프트웨어 수용](../research/crop-cycle-calculation-artifact-implementation-20261007.md)을 완료했다.
선행 [계산 문맥 수용](../research/crop-cycle-calculation-context-implementation-20261007.md),
[원 artifact 계약](crop-cycle-artifact-v1.md)과 [소스 대조](../research/artifacts/crop-cycle-calculation-artifact-inspection-20261007.json)를 따른다.
작업은 `crop-cycle-calculation-artifact`이며 현재 farm/권리·server custody·DB/API/3D 연결은 다음 작업이다.
원166일 실험/55 source SHA·입력/spec과 과거 결과를 보존한 신규 파일 개발을 병행한다.

## 변경 범위와 판본

구현 core는 다음4개다.

1. `backend/app/crop_cycle_calculation_artifact.py`: 새 writer/reader와 불변 파일·현재 입력 검사 경계.
2. `backend/tests/test_crop_cycle_calculation_artifact.py`: 원량/원자 게시·재시작/조회·거부/정리 검증.
3. 이 계약.
4. `research/crop-cycle-calculation-artifact-reference.py`: 소유한 긴 합성 사례·별도 Python/실제 중단 대사.

artifact ID/HEAD/header/commit/root 판본은 `crop-cycle-verified-artifact-v1`이다.
계산/checkpoint는 수용한 `crop-cycle-verified-execution-research-v1`/
`crop-cycle-verified-checkpoint-v1`만 받는다. 원 artifact/checkpoint를 재해시하거나 판본만 바꿔 수용하지 않는다.
원 writer에 engine globals/token을 주입하거나 원/조회 타입으로 위장하지 않는다.
동일 범위의 저장 제어를 정적으로 이식하는 부분은 원 AST/연산 순서와 변경 지점을 대사한다.
원 파일을 수정하거나 실행 중 동적으로 소스를 생성/교체하지 않는다.

## 공개 인터페이스와 소유

```python
create_writer(directory, context, *, notice_raw)
open_writer(directory, expected_head_sha256, context, *, notice_raw)
open_artifact(directory, expected_artifact_sha256, context, *, notice_raw)
writer.advance(budget)
writer.finalize()
reader.summary
reader.page(kind, start=0, limit=None)
```

context는 정확한 새 `CalculationContext`이며 factory의 현재 원 bytes/증명·코드/프로필/고지를 대사한다.
writer/reader는 자신이 연 결과 directory FD·lock/cache를 소유하고 caller의 context는 빌린다.
정상 close는 빌린 context를 닫지 않는다. 입력 불일치 시 context 자체의 실패 정리와 결과 handle 정리를 모두 확인한다.
결과 없음·빈 hold·확정 과거 hold를 구분하고 실패한 미래를 만들지 않는다.
원 전체 QC 발행은 계속 필요하며 권리/G0/농장 계산 출처 승인은 false다.

## 현재 입력 검사와 내부 검증 호출

create/open·writer advance/finalize·reader summary/page의 진입과 정상 반환 전에
현재 증명과 모든 입력 bytes를 다시 확인한다. 쓰기에는 HEAD 게시 직전 검사도 둔다.
실제 계산은 writer.advance의 새 `advance_chunk`만 호출하며 이 함수의 기존 진입/반환 검사2회는 유지한다.
따라서 advance의 정상 경로는 artifact3회+계산2회, create/finalize는3회,
open/summary/page는2회를 기준으로 계측한다.
초기화 안에서 같은 논리 연산을 중첩 호출해 검사를 추가 반복하지 않는다.
오류 시 정상 객체/응답을 반환하지 않으며 열린 결과 handle을 닫는다.

전체 commit prefix 대사에서 public `start/checkpoint_bytes`를 매 commit마다 부르면
현재 큰 입력 전체의 검사를 반복한다. 내부 검증은 아래 새 module의 고정 private helper를 명시적으로 사용한다.

- 정체성/초기·checkpoint: `_require_context`, `_start`, `_checkpoint_bytes`.
- 원 grid/clock/event/확정 과거: `_boundary`, `_evaluator`, `_clock_record`, `_seal`, `_confirmed`.
- canonical JSON/SHA: `_canonical`, `_hash`; prefix는 원 `short._prefix`의 연산 순서를 유지한다.

이 helper는 위 공개 연산의 전후 검사를 통과한 경계 안에서만 사용한다.
초기 증명의 schema/QC·현재 bytes·각 입력 block SHA/metadata·checkpoint/수지 검사를 생략하는 fast path가 아니다.
읽기/QC·복원은 RHS0이며 실제 과거 결과를 재적분하지 않는다.
선택 결과 blob도 각 조회에서 재해시하고, code/profile/notice·closed key·현재 입력 변경은 반환을 거부한다.

## 파일과 원자 게시

원 header의 닫힌8개 필드 `schema_version/scope/manifest/initial_checkpoint/notice_raw_utf8/`
`artifact_code_sha256/dependency_sha256/limits`를 유지하며 새 판본/실제 source/dependency를 고정한다.
manifest는 새 계산 문맥의20개 key와 provenance7개를 그대로 받는다.
HEAD/commit/root의 key와 parent/checkpoint/ordered prefix 규칙은 원 계약을 유지한다.
sample/event·원량/UTC·121상태·16누적·단위/수지/clock·hold/last_confirmed를 변환하지 않는다.
원/새 artifact SHA·실행/checkpoint root/parent SHA는 판본 차이로 기록한다.

SHA 이름의 canonical blob을 overwrite 없이 작성/fsync한 뒤 완전한 commit만 HEAD로 atomic 게시한다.
root는 terminal completed/hold에서만 게시한다. HEAD 이전 orphan/temp와 이후의 불확실한 게시를 구분한다.
게시 예외는 writer를 닫고 실제 HEAD/prefix를 새 handle로 검증한 뒤 재개한다.
동시 writer·오래된 HEAD·미게시 root·partial/혼합 판본을 거부하고 기존 다른 directory를 삭제하지 않는다.
이 파일 hash/수지 대사는 외부 진본 인증이 아니며 원자적 farm/DB 게시와 server signature는 후속이다.

원 한도는 유지하고 canonical limits pin도 검사한다. 저장 page128records/2MiB·delta8MiB/16pages·
metadata128KiB·checkpoint64KiB·root2MiB/16,384commits·directory512MiB/65,536files,
artifact chunk10,000steps/128transitions, 조회 samples64/events8·응답2MiB다.
orphan/temp까지 directory budget에 포함하고 다음 RHS 전에 검사한다.
경계 시험을 위해 production 한도를 낮추거나 새로운 일시한도를 승인하지 않는다.
한도 전체 부하나 HTTP30초 수용 주장은 해당 별도 실험 전까지 보류한다.

## 수용 기준

1. 원6프로그램과 원 hold/빈 과거 사례의 실제 writer→reader를 순수 새 계산 결과와 대사한다.
   전체 원량/UTC·121상태·누적/수지·사건/출력 prefix·clock·counter를 확인한다.
2. 초기/commit 뒤·pending forcing/event/output에서 닫고 별도 Python으로 재개한다.
   원 순서/중복 없음·checkpoint/남은 chain과 terminal root를 대사하며 reader의 RHS/advance0을 강제한다.
3. 실제25시간·11,400걸음/300forcing 자작 사례를 저장하고 전체27시점/5사건·선택 페이지·
   별도 Python 재개/조회·활성 RSS/FD/cache·저장 bytes/files와 원55 source/입력/spec을 대사한다.
   이 사례로166일/farm/DB/API/3D 부모를 완료하지 않는다.
4. HEAD 전후 실제 child 강제 종료2개와 다시 열린 HEAD/prefix를 대사한다.
   현재 입력·proof/code/profile/notice/limits·root/commit/page·순서/수지/clock/삭제량의 변조,
   symlink/FIFO/oversize/missing/닫힌 handle·잘못된 형/판본·동시 writer와 자원 초과를 거부한다.
5. 공개 연산의 입력 검증 횟수와 내부 prefix의 반복 전체 검사0을 계측한다.
   실제 RHS 중/페이지 투영 중·HEAD 전후 변경을 시험하고 정상 반환/잘못된 과거 재발급을 차단한다.
6. 집중 검증·실제 process/중단·자원 정리·불변 receipt/source/CLI·검토/링크가 모두 존재한 뒤 이 자식만 체크한다.

산출물은 원/새 결과 대사·복원/실제 중단 기록·reader RHS0·비용/자원 보고서와 불변 receipt다.
G0–G4·실제 품종 입력/국내 독립 자료0건·생과/자원/경제 후속과 예측/추천 보류는 유지한다.

## 잠정 작업 분해와 시간

착수 당시 계약/정적 이식·현재 검사 경계 검토1–2집중시간, 집중/별도 Python·실제25시간 사례/중단·수정1–2집중시간으로
**총2–4집중시간,10월7–8일 KST 잠정**이다. 원 artifact475줄·기존58개 분할 검증(55.36초+0.20초)과25시간 참조236.264초,
새 계산 경로90사례/76.37초가 분해의 근거다. 오류·실제 저장 비용을 관측하면 갱신한다.
hosted CI 대기·원166일 종료/전체 farm/API/3D·독립 자료 확보의 완료일을 포함하지 않는다.

10월7일에 이 자식의 최종68개/선행90개·총158통과와 별도 Python7개·실제25시간/11,400걸음·
HEAD 전후 child 즉시 종료2개를 로컬 수용했다. 실제 참조 실행249.435초·저장758,946bytes/127파일은
이 작은 합성 사례의 관측이다. 원166일/farm·DB/API/3D 및 생산 예측의 수용은 별도다.
