# 불변 cycle 계산 결과와 재적분 없는 reader — v1

상태: **불변 파일/reader의 로컬 소프트웨어 수용**, 2026-10-05 KST.
작업 `crop-cycle-result-artifact`; [실제 수용/제한](../research/crop-cycle-artifact-implementation.md),
[실제 RHS·별도 Python·강제 종료 증거](../research/artifacts/crop-cycle-artifact-reference-20261005.json)를 확인한다.
[수용된 실제 stream 실행](crop-cycle-stream-execution-v1.md),
[제품 관문](../docs/PROJECT_SPEC.md), [저장/worker 경계](../docs/ARCHITECTURE.md)를 따른다.
현재 Codex CLI `gpt-6.1-sol / xhigh`로 설계/검토하며 CLI를 재귀 실행하지 않는다.
기존 short/continuation/입력 reader/긴 driver와 fixture/profile/API의 수용 hash를 보존한다.

## 산출물과 범위

구현3파일은 `backend/app/crop_cycle_artifact.py`,
`backend/tests/test_crop_cycle_artifact.py`, 이 계약이다.
새 합성 연구 artifact의 sample/event/checkpoint commit·불변 index/root와 reader를 구현한다.
writer만 HTTP 밖에서 실제 driver를 실행하며 reader는 RHS/적분을 실행하지 않는다.
scope는 `software_research_only`; 문헌 참조/합성 고지를 고정된 기존 bytes/hash로 보존한다.
실제 입력/품종·전체 작기/생과/구매 자원·경제·G0–G4를 승인하지 않는다.
독립 농장 자료 확보는 개발과 병행한다. 새 queue/service/dependency는 선행이 아니다.

후속은 cycle schema → 명시 role/config → 현재 farm/source 권리/HMAC custody → API → client → 같은 UTC3D →
166일 실제 RHS 부하 → 생과/자원/경제다. 이 파일 저장은 DB 거래/현재 권리/worker lease·cancel의
배포 수용을 대신하지 않는다. 취소/crash/파일 오류를 numeric hold로 위장하지 않는다.

## 유한 저장 계약

| 항목 | 연구 v1 상한 |
| --- | --- |
| 원 실행 chunk | max_steps 정수1..10,000; max_transitions 정수1..128 |
| sample/event page | canonical UTF-8 JSON array, 각≤128record·≤2MiB; record를 자르거나 보간하지 않음 |
| 한 commit의 모든 delta page bytes | 합계≤8MiB·page 목록≤16개 |
| checkpoint | 기존 새 stream schema≤64KiB,121 float64/원 seed/clock·전역 counters/phase |
| header/commit | 각≤128KiB; closed JSON/hash·code/profile/notice/input context pin |
| 최종 root |≤2MiB·최대16,384 ordered commit hashes |
| 소유 저장 directory | canonical blob/commit/header/root와 pointer 합계≤512MiB; 파일 수≤65,536 |
| 조회 | samples 최대64·events 최대8; 원 순서/UTC·결합 본문≤2MiB |

이 수치는 유한 소프트웨어 resource 계약이며 해당 전체 규모의 production 부하 수용이 아니다.
너무 큰 단일 record/전체 byte/commit 한도는 typed artifact rejection이다. 입력·수치/격자를
변경해 조용히 맞추지 않으며 마지막으로 commit된 prefix를 보존한다.

## header·commit·최종 root

모든 blob은 SHA-256 이름의 immutable canonical JSON이다. header는 판본/scope, 실행 manifest,
원 input/context root, 초기 checkpoint, 새 artifact/읽기 검증 dependency hashes, 고지 bytes,
고정 resource limits를 연결한다. profile/code/policy/Python/seed/clock의 pin은 원 context와 대사한다.

commit은1부터 연속 순서다. header hash·직전 commit hash·입력 checkpoint hash, 원 driver의
status/steps/planned/output_start/event_start, 이번 delta page descriptors, 다음 checkpoint 또는
hold/last_confirmed를 보존한다. yielded/completed의 checkpoint.parent는 입력 checkpoint hash다.
sample/event prefix는 원 전역 sequence와 canonical record chain으로 대사한다.
failed trial/hold에는 정상 다음 checkpoint가 없다. t0 hold는 확인된 과거가 없다.

최종 root는 header hash/ordered commit hash 목록/terminal status만 포함한다. 마지막 commit만
completed 또는 hold일 수 있고 그 이전은 모두 yielded다. root/hash/commit/index/수치의
검사는 진본·현재 권리·G0/게시 권한을 증명하지 않는다; HMAC/custody는 후속이다.

## writer·atomic 게시·재시작

`create_writer(directory, context, notice_raw=…)`는 새 소유 directory만 만들고 header/initial HEAD를
고정한다. `open_writer(directory, expected_head_sha256, context, notice_raw=…)`는 현재 HEAD와
모든 commit prefix를 사전 검증한 뒤 복원한다. writer는 directory의 nonblocking 배타 file lock을
유지한다. 다른 writer/잘못된 root·판본/오래된 HEAD·닫힌 handle은 typed rejection이다.

`writer.advance({max_steps,max_transitions})`만 실제 driver를 호출한다. page/header/commit은
같은 directory의 독점 임시 파일에 쓰고 fsync, 내용 주소로 overwrite 없이 게시하고 directory를
fsync한다. 전체 delta/checkpoint commit blob이 완성된 뒤 HEAD를 atomic replace한다.
성공 반환에는 HEAD hash/commit count/상태/전역 steps가 있다.
`writer.finalize()`는 마지막 completed/hold에서 불변 root를 만들고 HEAD의 artifact hash를
atomic 게시한다. 같은 terminal prefix의 재시도는 같은 root다. 완료 후 advance는 거부한다.

HEAD 교체 이전의 장애는 이전 prefix에서 재시작한다. 페이지/commit만 생긴 orphan은 정상 결과가
아니며 reader가 그로부터 임의 복원하지 않는다. orphan/temp bytes도 소유 directory의 유한 budget에
포함한다. 파일 정리는 생성한 임시 파일과 실패한 새 directory에 한정하며 기존 다른 directory를
삭제하지 않는다. 하나의 filesystem에서 관측하는 atomic 게시와 fsync를 시험하며 실제 호스트
전원 장애/배포 스토리지 durability·동시 DB 거래/lease는 별도다.
HEAD 게시 과정의 예외는 writer를 닫는다. 교체 전후의 실제 HEAD를 새 handle로 검사한 뒤
다시 시작해야 하며, 불확실한 게시를 오래된 메모리 상태로 재시도하지 않는다.

## reader 검증과 페이지

`open_artifact(directory, expected_artifact_sha256, context, notice_raw=…)`는 HEAD에 게시된 해당
root만 받는다. 파일은 directory FD 기준 O_NOFOLLOW/O_NONBLOCK의 유한 regular file로 읽고
hash/closed canonical schema를 검사한다. header/commit 목록·연속 parent/checkpoint/position·
원 grid/출력·관리 prefix/seed/clock와 terminal status를 bounded 읽기로 preflight한다.

sample은 원 출력 시각 prefix·형식/단위·정확한 clock·전역 operations=steps+event_count의
원 seed 수지/diagnostics·LAI/과실 탄수화물 합계와 동일해야 한다. event는 원 event 시각/input ID,
제거 before/after/원 removal 원량과 일치하고 sample/last_confirmed의 사건 누적과 대사한다.
yielded/complete checkpoint는 기존 driver의 reader 검증을 사용하며 RHS를 실행하지 않는다.
hold의 last_confirmed는 원 grid/phase/counters·원 clock/ledger의 확인된 과거이고, hold.at는
해당 시도/확인 과거 이후의 canonical UTC(필요하면 fractional RK4 trial)다.

`reader.summary`는 deep copy의 원 manifest/고지/상태/steps/planned/기록 수·최종 checkpoint 또는
hold/last_confirmed다. `reader.page(kind,start,limit)`는 같은 불변 root의 순서 있는 원량 record와
다음 offset/전체 개수를 반환한다. 읽기마다 선택 blob의 hash를 확인하며 한 page만 cache한다.
잘못된 cursor/bool/oversize/닫힌 handle·순서/중복/혼합 root/부분/변조는 거부한다.
과거 hold/빈 hold에서 없는 미래를 만들지 않는다. 보간/임의 3D 프레임·생과kg를 추가하지 않는다.

## 수용 절차

1. 기존6프로그램의 canonical 원 상태/16누적·수지/diagnostics·사건/걸음,7종 hold와 확인 과거가
   실제 writer→reader에서도 같아야 한다. read path에서 RHS/적분0회를 강제한다.
2. pending forcing/event/output 경계와 초기/commit 뒤를 저장하고 별도 Python process에서
   writer 재시작 및 terminal root의 reader 조회를 대사한다. checkpoint/JSON float64 원량을 보존한다.
3. 실제25시간/10,000step 초과 자작 합성 RHS를 저장하고 전체/선택 UTC·순차 페이지·별도 Python
   읽기를 비교한다. 원 계산 driver/seed/clock/입력 hash를 바꾸지 않는다.
4. closed/schema/profile/code/policy/notice/context/hash/root·page offset/count/time/chain/수치
   변조·partial commit·HEAD 이전/이후 장애·동시 writer·오래된 HEAD·byte/file/record budget,
   symlink/FIFO/oversize/missing file/닫힌 reader와 tempfile/FD/자식 정리를 검증한다.
5. 집중 회귀/실제 process·RHS 증거, frozen source/input hashes, CLI metadata·검토/자원·영수증과
   local links 뒤 checkbox를 갱신한다. 이 과정에서 기존 진행 중 CI를 후속 push로 취소하지 않는다.

최초5–8집중시간/10월5–7일 KST 예상은 **10월5일 로컬 수용**으로 대체한다.
58개 고유 집중 검증의 분할 수용(57개/55.36초+파일 수 budget1개/0.20초),
실제25시간/11,400걸음·27sample/5event·755,868bytes/127파일,
별도 Python7개/847float64와 실제 강제 종료2개/게시 전후 복구를 확인했다.
읽기/검증0.388759초·RHS/advance/원 적분0회, 관측 페이지 최대32,918bytes다.
첫 실행 증거는 Git130ede3의 구현 중 계약/57개 시험 파일 hash를 고정한다.
최종 계약/58개 시험 hash와 초안 대사는 별도 수용 영수증에 기록하며 첫 증거를 덮어쓰지 않는다.
다음 schema는 아래 보고서의3파일/실제 SCRAM 수용 기준으로 진행한다.
실제 품종/예측·추천 날짜는 독립 농장 자료0건인 현재 산정하지 않는다.
