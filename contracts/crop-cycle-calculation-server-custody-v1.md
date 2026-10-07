# 검증 계산 판본의 서버 실행·서명 이력

상태: 2026-10-07 KST [로컬 소프트웨어 수용](../research/crop-cycle-calculation-server-custody-implementation-20261007.md).
작업은 `crop-cycle-calculation-server-custody`다. 아래 본문은 실행 전 고정했고 수용 기록만 추가했다.
선행은 [현재 농장 권한](crop-cycle-calculation-farm-binding-v1.md)과
[새 불변 artifact](crop-cycle-calculation-artifact-v1.md)의 로컬 수용이다.
[원 서버 custody](crop-cycle-server-custody-v1.md)의 파일·서명·예산 정책을 유지하되
exact 새 타입/판본을 사용한다. 이 자식 수용만으로 DB 게시·농장 연결 부모·전체166일/3D를 완료하지 않는다.

## 구현 경계

core는 다음4파일 이내다.

1. `backend/app/crop_cycle_calculation_server_custody.py`
2. `backend/tests/test_crop_cycle_calculation_server_custody.py` — 순수 journal/실제 프로세스.
3. `backend/tests/test_crop_cycle_calculation_server_custody_farms.py` — 실제 SCRAM/현재 농장.
4. 이 계약.

원475줄의 파일/서명 알고리즘을 명시 새 판본에 이식하고 함수별 AST/변경 이유를 검토한다.
원 exact binding/reader/engine을 사칭하거나 module global·token을 교체하지 않는다.
새 module은 `CalculationFarmBinding`/`CalculationContext`/검증 artifact만 받는다.
기존55 source SHA·실행 중 입력/spec/마감과 원 결과를 보존한다. 새로운 queue/service/DB schema는 없다.

```python
CalculationServerCustody(binding, directory, *, input_resolver, integrity_key)
service.advance(tenant, request_raw, *, budget)
service.inspect(tenant, request_raw)
service.page(tenant, request_raw, expected_progress_raw, kind, start=0, limit=None)
```

운영자가 고정한 resolver는 `(root_sha256, *, authority)`로 공식 factory가 연
exact `CalculationContext`를 반환하고 그 소유권을 호출에 넘긴다. 원 root의 사설 bytes와
서버 발행 입력 증명을 resolver 내부에서 읽으며 요청은 filesystem path/계산 결과/서명을 지정할 수 없다.
authority는 현재 binding에 설치된 동일 객체여야 한다. resolver identity/version·키·root inode·
binding/service/코드/의존성/고지·현재 입력을 고정한다. 정확한 계산 문맥은 모든 종료 경로에서 닫는다.
잘못 반환한 알려진 context/reader 형도 소유한 FD를 정리한다. 조회 문맥·원 reader를 계산에 허용하지 않는다.

## 판본과 게시 순서

서버/intent/HEAD proof 판본은 각각 `crop-cycle-verified-server-custody-v1`,
`crop-cycle-verified-server-intent-v1`, `crop-cycle-verified-server-head-v1`이다.
identity/intent/proof HMAC domain은 각각 `ossf-crop-cycle-verified-server-identity-v1`,
`ossf-crop-cycle-verified-server-intent-v1`, `ossf-crop-cycle-verified-server-head-v1`의 NUL 종료 bytes다.
HEAD는 새 artifact의5필드, checkpoint/engine은 새 공식 계산 판본을 유지한다.
원 closed envelope/intent/proof/progress 필드와 content-addressed parent chain을 유지한다.
intent의 binding과 context SHA에는 현재 입력 검증 provenance가 들어간다.
공개 SHA 일치는 실행 인증·자료 권리/G0 승인 자체가 아니다.

서버는 현재 권한/등록/원천과 입력을 확인한 뒤 불변 intent와 초기 header를 쓴다.
실제 새 writer가 만든 초기/advance/finalize HEAD마다 **현재 권리 확인 → proof fsync →
현재 권리 재확인 → 기존 atomic HEAD replace** 순서로 게시한다.
계산 전후·반환 전에도 현재 권리·입력/코드·intent와 디렉터리 identity를 대사한다.
proof 기록 뒤 철회되면 그 proof는 orphan으로 남고 이전 signed HEAD를 유지한다.
여러 외부 정책을 하나의 원자 snapshot으로 잠근다는 주장은 하지 않는다.

선택 HEAD의 proof와 부모를 genesis까지 확인한다. unsigned delta/다른 key·판본·binding·
source/code/고지/경로·canonical bytes 불일치에는 hold다. 알려진 초기0-step header만 복구하며
HEAD를 지운 computed blob을 초기값으로 추정하지 않는다. 같은 요청 재시도/완료 조회는 RHS0이다.
`page`는 expected progress와 현재 권리를 전후 확인하고 원 UTC/값만 반환한다.
수치 hold는 원 확인 과거/진단을 보존하며 완료·수확/생산량으로 승격하지 않는다.

## 자원과 기존 자료

원 budget `max_steps <= 10,000`, `max_transitions <= 128`, RK4 격자/계수/clock을 유지한다.
artifact의512MiB/65,536파일/16,384commit과 원 custody의 고정 LIMITS를 그대로 사용한다.
원 root1GiB/131,072파일/128intent·intent640MiB/98,310파일·proof128MiB/32,770파일,
intent192KiB/proof8KiB/progress128KiB다. orphan/temp도 사용량과 사전 reserve에 포함한다.
root/intent의 nonblocking exclusive flock·owner0700/noACL/NOFOLLOW와 regular 단일 link
불변0400/lock-temp0600·fsync를 유지한다. 같은 root의 원 이력도 합산 예산에 포함한다.
새 identity domain은 원 intent를 새 실행으로 재발급하지 않는다. DB/HMAC metadata 공존은 다음 자식이다.

## 수용 기준

1. 첫 signed0-step/실제 bounded 계산/terminal finalize·완료 재시도와 sample/event 원량/UTC를 대사한다.
   새 순수 계산·원 적분의 같은121상태/clock/counter·confirmed past를 확인한다.
2. selected proof의 서명/parent/sequence/schema·unsigned 계산·다른 key/domain/version·
   root/파일/입력/고지/코드/예산·동시 lock/같은 revision 충돌을 거부한다.
3. 실제 child를 proof 전후·HEAD 전후에서 즉시 종료해 선택된 signed checkpoint만 복원한다.
   `os._exit` 시험은 외부 SIGKILL/전원 장애와 구분한다. 별도 fresh Python exec의
   정확한 checkpoint 복원·실제 계산/완료 조회 RHS0·FD/cache/child 정리를 확인한다.
4. 실제 SCRAM 등록 농장에서 연속/작은 중단 재개와 새 서비스 재접속·현재 권한/원천/등록을 확인한다.
   계산 중·proof 기록 뒤·페이지 투영 중 철회를 거부하고 권리/입력 검사를 우회하지 않는다.
   이 단계는 새 작물 DB row/Run0이며 등록 jobs/events를 보존한다.
5. 조회·새 문맥 재열기·농장 권리·journal/서명·실제 RHS 비용과 저장 크기를 나누어 실측한다.
   소유 PG/schema/role/passfile·FD/lock/temp/child 정리, 원55 source/입력/spec와 과거 bytes 보존을 확인한다.
6. 실제 시험/소스 판본·native CLI `gpt-6.1-sol / xhigh`/재귀 CLI0·불변 영수증/검토·문서 링크 뒤
   이 자식만 체크한다. 전체 backend/hosted CI·DB/API/3D와 G0–G4 수용으로 확대하지 않는다.

산출물은 새 서버 실행 이력과 실제 계산·중단 복원/권리 철회·비용/정리 보고서다.
원475줄 이식/함수 검토1–2시간, 원376줄 순수·143줄 실제 DB 시험의 새 타입 적용/반례/검증1–2시간으로
**2–4집중시간/10월7–8일 KST 잠정**이다. 선행 artifact158개/151.23초·실제25시간 참조249.435초와
현재 권한의12개/242.84초·prepare/current2.711/2.713초가 근거다.
CI 대기·전체166일/실제 DB 게시·품종/독립 자료 확보 시간은 포함하지 않는다.
실제 품종 입력·국내 독립 자료·actual crop Run0, G0–G4 `not_assessed`와 생산 예측/추천 hold를 유지한다.

10월7일에 순수49개와 원 signed 이력 공존 추가1개·실제 SCRAM12개, 고유62개를 분할 수용했다.
제품 module은 동일하며 DB 게시·farm 연결 부모·전체 작기/API/3D는 미수용이다. 실제 정리와 원55 source/입력/spec을 보존했다.
