# Cycle 서버 계산과 서명된 진행 상태 — v1 설계 후보

상태: **설계 후보/미구현**, `crop-cycle-server-custody`, 2026-10-05 KST.
선행은 [현재 농장/root 결합](crop-cycle-farm-binding-v1.md),
[실제 writer/복원](crop-cycle-artifact-v1.md), [명시 runtime 권한](crop-cycle-storage-v1.md)이다.
[저장 부모/의존성](../tasks/plan.md)을 따르며 DB custody/API/client/성장3D는 후속이다.
현재 Codex CLI `gpt-6.1-sol / xhigh`로 판단하며 CLI 재귀 실행은 하지 않는다.

## 해결할 실제 공백

artifact reader는 구조·hash·clock·누적 수지와 원 격자를 확인한다.
그 SHA 검사를 통과한 파일이 실제 서버 RHS로 만들어졌다는 인증은 서명된 계산 경로가 필요하다.
운영자가 고정한 private POSIX root와 원 입력 resolver만 사용하고 사용자 요청은 닫힌
farm/input root ID다. 서버가 검증한 원 입력을 실제 frozen writer로 실행한다.
외부 caller가 선택한 artifact 경로/root/계산값을 가져와 인증하는 API는 제공하지 않는다.
서명된 진행 상태를 별도 프로세스에서 검증하고 같은 원 상태/시계/수지를 복원하는 단계다.

## 최소 모듈 경계와 원량

3–5파일의 새 server custody module/test/이 계약으로 구현한다.
신뢰 constructor는 CycleFarmBinding, private root,32byte 이상 별도 integrity key,
root 전용 input resolver를 고정한다. tenant/study/revision에 domain을 넣어 private intent 경로를 만든다.
절대 POSIX 경로의 모든 parent/leaf·owner·0700·ACL·regular file/단일 link·NOFOLLOW를 검사하며
request filesystem path나 원본/비밀을 공개 응답으로 넘기지 않는다.
resolver의 명시 판본/identity·원 입력 root/profiles/code/env/고지와 farm/source/input 권리를 대사한다.
OS UID/키 소유권의 독립 운영 검증과 G4는 이번 로컬 계약에 포함하지 않는다.

시작은 입력 preflight/현재 binding → 서명된 불변 intent → 실제 writer 초기 header다.
advance는 기존 max_steps1..10,000/max_transitions1..128의 한 유한 호출과 동일 원 RK4 격자를 사용한다.
각 호출 전후 현재 binding·코드/권리/intent를 확인한다. caller의 변경된 budget이 원 적분 격자를 바꾸지 않는다.
completed/hold와 확인 과거, 불변 terminal root는 기존 writer/reader를 재사용한다.
새 계수/작물 산술·임의 sample interpolation·자동 착과/생과 환산은 이 단계에 넣지 않는다.
초기0-step은 원 입력 상태이며 crop 계산 완료로 표시하지 않는다.

## HEAD 게시와 서명의 순서

HEAD와 별도 서명 pointer를 각각 덮어쓰는 두 파일만으로 crash atomicity를 보장할 수 없다.
실제 writer가 산출한 **새 HEAD의 canonical SHA를 키로 한 불변 HMAC proof를 먼저 fsync**하고,
그 후 기존 artifact의 atomic HEAD replace를 수행하는 후보를 채택한다.
private adapter가 writer의 publish 경계를 감싸며 frozen artifact module은 변경하지 않는다.
proof는 tenant/intent/request/binding/input/context/header/code/고지·previous HEAD/proof·새 HEAD를 domain HMAC에 묶는다.
원 상태/벡터 전체를 서명 metadata에 복제하지 않고, HEAD→commit→checkpoint/page의 hash 체인을 대사한다.
proof body의 canonical schema/세부 byte 상한과 domain 문자열은 구현 전에 고정하고 실제 크기로 검증한다.
Python의 [HMAC와 compare_digest](https://docs.python.org/3.12/library/hmac.html)를 사용해
공개 SHA와 비밀 키를 쓰는 인증 서명을 구분한다.
[fsync/replace](https://docs.python.org/3.12/library/os.html#os.fsync)의 파일/디렉터리 동기화 순서는
기존 writer의 실제 강제 종료 시험과 새 proof 경계의 강제 종료로 검증한다.
공식3.12 문서의 표시 patch 판본을 현재 로컬3.12.3/hosted3.12.13 채택으로 해석하지 않는다.

복원은 실제 atomically selected HEAD의 hash로 대응 proof를 읽는다.
서명/parent/binding/code/manifest 불일치나 unsigned 계산 HEAD에는 hold다.
새 proof만 남고 HEAD는 이전이면 이전 signed HEAD를 복원한다. 새 HEAD가 보이면 fsync한 대응 proof가 있어야 한다.
finalize도 terminal root를 참조하는 prospective HEAD proof 뒤 atomic 게시로 같은 순서를 따른다.
초기 header 생성 중 proof가 없던0-commit 상태는 원 입력/정확한 초기 header를 대사하는 별도 복원 조건으로 검증한다.
기존 파일을 추정해서 인증하거나 unsigned 새 계산 delta를 자동 채택하지 않는다.

intent/서명들은 내용 주소 파일과 no-overwrite를 사용하고 동시 호출에는 기존 exclusive writer와
명시 intent lock을 사용한다. 같은 intent/요청의 재시도는 실제 선택 HEAD에서 복원한다.
다른 farm/input/권리/요청의 같은 study/revision은 conflict다. 정정은 새 revision이다.
orphan proof/blob도 파일 수/bytes budget에 포함하고 새 RHS 실행 전에 한도를 검사한다.
global proof/directory budget은 실제 metadata 크기와 artifact512MiB/16,384commit 한도를 근거로 시험 후 고정한다.
별도 새 queue·대몬·서비스·DB migration은 필요하지 않다.

## 다음 한 단계의 수용 기준

1. 6개 원 프로그램의 canonical sample/event/UTC·checkpoint/누적 수지와 실제 서버 RHS 실행을 대사한다.
   읽기/동일 완료 retry는 RHS/advance0회다.
2. 25시간/원 한도 초과 실제 입력의 bounded advance/서명·별도 Python 재시작으로 정확한 원 상태를 보존한다.
3. 실제 process 강제 종료를 proof 게시 전/후와 HEAD 교체 전/후에 주입한다.
   실제 선택 signed HEAD의0/1 delta와 pending event를 한 번만 복원한다.
4. HMAC/signature/HEAD/parent·cross tenant/farm/intent/root/context/code/고지·symlink/FIFO/hardlink와
   외부 fabricated artifact/미서명 delta·orphan/부분 proof를 거부한다.
5. 현재 farm/source/input/scopes의 advance 전후 철회와 stale memory handle·동시 호출/conflict를 확인한다.
6. artifact/proof의 실제 byte/file/step 상한·전체 budget/WSL RSS·FD/lock/temp/child 정리를 기록한다.
7. DB crop row/Run/새 gate0개와 원44개/binding 판본의 hash를 보존한다.
   실제 farm provider 시험은 SCRAM을 사용하고 signed file만의 parser 시험은 pure focused로 수행한다.

계약/adapter/proof1–2시간+actual writer/현재 권리/복원1–2시간+강제 종료/변조/정리1시간의
잠정 **3–5집중시간**이다. 시작 날짜는 선행 binding 수용 뒤 갱신한다.
이후 DB HMAC/commit 전후 권리·immutable retry는 별도2–3시간 잠정이며 실제 구현에서 갱신한다.
권리 predicate·fixture key는 소프트웨어 증거이며 actual data/독립 국내 자료0개와 G0–G4 hold를 유지한다.
