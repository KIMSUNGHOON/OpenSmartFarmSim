# Cycle 서버 계산과 서명된 진행 상태 — v1

상태: **로컬 소프트웨어 수용**, `crop-cycle-server-custody`, 2026-10-05 KST.
[구현/수정과 검증](../research/crop-cycle-server-custody-implementation.md),
[불변 영수증 v2](../research/artifacts/crop-cycle-server-custody-reference-20261005-v2.json)을 확인한다.
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
절대 POSIX 경로의 모든 parent/leaf를 NOFOLLOW로 열고 private root/intent의 owner·0700·ACL,
private 파일의 regular type/단일 link·정확한 mode를 검사하며
request filesystem path나 원본/비밀을 공개 응답으로 넘기지 않는다.
resolver의 명시 판본/identity·원 입력 root/profiles/code/env/고지와 farm/source/input 권리를 대사한다.
OS UID/키 소유권의 독립 운영 검증과 G4는 이번 로컬 계약에 포함하지 않는다.

시작은 입력 preflight/현재 binding → 서명된 불변 intent → 실제 writer 초기 header다.
기존 create_writer는 초기 HEAD를 instance 반환 전에 게시하므로 새 adapter는 정확한
ArtifactWriter를 만들고 원 `_header`/`_put`/초기 checkpoint를 그대로 사용하되 최초 HEAD도
proof-before-HEAD 경계로 게시한다. 실제 RHS/페이지/commit/finalize는 원 writer의 메서드다.
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
아래 닫힌 schema/상한을 구현 기준으로 고정하며 실제 크기/반례를 검증하기 전에는 수용하지 않는다.
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
root의 exclusive nonblocking flock으로 서로 다른 intent의 합산 예산도 직렬화한다.
이는 [Linux flock의 열린 파일 description과 해제 규칙](https://man7.org/linux/man-pages/man2/flock.2.html)을 따른다.
고정 writer에 전달하는 내부 경로는 이미 검증한 intent FD의 `/proc/self/fd/{fd}/artifact`다.
[Linux descriptor 경로](https://man7.org/linux/man-pages/man5/proc_pid_fd.5.html)를 사용하며,
요청/운영자 경로의 symlink 검사를 생략하지 않는다. Linux 로컬 파일시스템의 소프트웨어 경계다.
별도 새 queue·대몬·서비스·DB migration은 필요하지 않다.

## 닫힌 파일과 호출 계약

`CycleServerCustody(binding,directory,*,input_resolver,integrity_key)`는 exact CycleFarmBinding,
절대 private root와 최소32byte key·판본/identity가 고정된 resolver를 요구한다.
resolver는 `(root_sha256,**profiles)`에서 실제 열린 exact InputPacket을 반환한다.
입력 directory는 같은 EUID/0700/noACL, 원 files는 regular/단일 link/noACL이며
기존 reader가 작성하는0400/0600/0644 mode만 허용한다. 서버 결과의 불변 files는0400,
lock/temp는0600, directory는0700이다. 디스크 판본을 고정한 code/dependency hash도 대사한다.

- `advance(tenant,request_raw,*,budget)`는 한 bounded 호출과 필요한 terminal finalize를 실행한다.
  같은 완료 재시도는 계산하지 않는다. 충돌/잠금은 별도 오류이며 수정은 새 revision이다.
- `inspect(tenant,request_raw)`는 서명과 현재 권리/원량을 읽는다. 신규 intent를 만들거나 RHS를 실행하지 않는다.
- `page(tenant,request_raw,expected_progress_raw,kind,start=0,limit=None)`는 같은 완료/hold
  progress의 원 sample/event 페이지를 반환한다. current rights와 expected bytes를 전후 대사한다.
  미완료 결과를 완료로 만들지 않는다. DB/API의 공개 계약은 후속이다.

canonical UTF-8 envelope는 `payload/signature`만 가지며 HMAC-SHA256을 compare_digest로 대사한다.
intent domain은 `ossf-crop-cycle-server-intent-v1\\0`, HEAD proof는
`ossf-crop-cycle-server-head-v1\\0`의 실제 NUL 종료 bytes다.
intent 파일은 version/scope/tenant_id/intent_id/request_sha256/binding/context_sha256/
header_sha256/notice_sha256/resolver_version/custody_code_sha256/dependency_sha256/limits의 닫힌 payload다.
tenant/study/revision의 canonical hash로 intent_id를 만들고 경로에는 그64hex만 사용한다.
binding이 원 request/root/farm/profile/권리를 포함하며 context/header가 실제 원 계산을 묶는다.
intent envelope 자체의 SHA가 proof의 intent_sha256이다.

proof payload는 version/intent_sha256/binding_sha256/head/parent/sequence/action만 가진다.
head는 원 writer의5필드 HEAD다. parent는 null 또는 head_sha256/proof_sha256의 닫힌 쌍이다.
action은 initialize/advance/finalize이고 sequence0은0commit/root-null/parent-null이다.
advance는 commit_count+1/root-null, finalize는 같은 commit_count와 최초 terminal root를 묶는다.
각 parent의 HEAD SHA/서명 bytes SHA와 sequence 감소1을 검증해 genesis까지 유한하게 확인한다.
proof 파일명은 원 HEAD canonical SHA다. 선택하지 않은 orphan proof는 현재 상태를 바꾸지 않는다.
초기 HEAD가 없으면 알려진 초기 header/HEAD와 그 temp만 있는 경우에만 같은0step을 복구하며
알 수 없는 computed blob/proof가 있으면 hold다.

progress bytes는 version/scope/intent_sha256/binding_sha256/input_root_sha256/context_sha256/
custody_code_sha256/head_sha256/proof_sha256/header_sha256/artifact_sha256/status/commit_count/
steps/planned_steps/counts/storage_bytes/file_count의 닫힌 metadata다.
시계열 원량은 기존 artifact에서 읽으며 임의 시간/공개 filesystem path/비밀을 넣지 않는다.

| 고정 한도 | 구현 기준 |
| --- | --- |
| intent envelope / proof envelope / progress | 192KiB / 8KiB / 128KiB |
| proof directory | 128MiB, 32,770 files |
| 한 intent 전체 | 640MiB, 98,310 files |
| root 전체 | 1GiB, 131,072 files, 128 intents |
| artifact / commit / 원 호출 | 원512MiB/65,536 files/16,384 commits, 10,000 steps/128 transitions |

orphan/temp도 합산한다. advance 전에는 원 최대8MiB delta의2배+metadata4개+proof2개+HEAD16KiB와
40file의 여유를 검사한다. finalize 전에는 최대2MiB root의2배+proof2개+HEAD16KiB/8file을 검사한다.
예산 부족이면 새 RHS 전 hold이며 이 한도가 실제166일/동시 운영 처리량을 증명하지 않는다.

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
기존 **3–5집중시간** 예상은10월5일 로컬 수용으로 대체한다.
고유46개 분할·6원 프로그램·25시간/11,400실제 걸음·121float64/pending event의 별도 Python exec,
네 실제 강제 종료/selected signed HEAD 복원·현재 권리/타입/예산/FD 정리를 확인했다.
참조25h는 reader subtype 정리 수정 전 판본이며 원46개/수학/정상 writer 경로를 보존했다.
이후 DB HMAC/commit 전후 권리·immutable retry는 별도2–3시간 잠정이며 실제 구현에서 갱신한다.
권리 predicate·fixture key는 소프트웨어 증거이며 actual data/독립 국내 자료0개와 G0–G4 hold를 유지한다.
