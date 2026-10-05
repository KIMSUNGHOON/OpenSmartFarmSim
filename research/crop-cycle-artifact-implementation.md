# 긴 생장 계산의 불변 저장과 재계산 없는 읽기

2026-10-05 KST. [구현](../backend/app/crop_cycle_artifact.py),
[집중 시험](../backend/tests/test_crop_cycle_artifact.py),
[계약](../contracts/crop-cycle-artifact-v1.md),
[실제 실행 증거](artifacts/crop-cycle-artifact-reference-20261005.json),
[CLI·파일/초안·검토 영수증](artifacts/crop-cycle-artifact-implementation-reference-20261005.json).
**원 cycle 계산 결과의 유한 파일 저장과 reader를 로컬 수용**했다.

## 사용자가 확인할 수 있는 산출물

새 writer가 수용된 실제 stream driver를 호출해 sample/event/checkpoint를 SHA-256 이름의
canonical UTF-8 JSON으로 저장한다. header와 연속 commit이 원 입력/계수/정책/코드·seed/
Fraction clock·전역 counter/수지·확인 과거를 연결한다. 모든 파일을 작성한 뒤 HEAD를 atomic
replace하며, 마지막 completed/hold의 불변 root를 게시한다. 게시되지 않은 orphan은 결과가 아니다.

같은 root의 reader가 원 UTC/단위/121상태·16누적·수지/진단·관리 사건을 순서대로 반환한다.
읽기마다 선택 blob hash를 확인하고 한 page만 cache하며, 조회에서 적분하지 않는다.
samples 최대64/events 최대8·결합2MiB, 저장 page128record/2MiB·delta8MiB,
checkpoint64KiB·metadata128KiB·root2MiB/16,384commit·directory512MiB/65,536파일을 고정했다.
상한 전체의 부하를 통과했다는 뜻은 아니다. 기존 short/continuation/입력 reader/driver·
fixture/profile·저장/API의40개 hash를 보존했다.

이 단계의 확인 대상은 코드·불변 root/hash와 검증 기록이다. 긴 결과의 농장 저장 목록/API/
웹3D 연결은 후속이다. 기존 짧은 startup 성장 연구 3D의 수용 범위는 유지한다.

## 통과한 검증

- **58개 고유 집중 검증의 분할 수용:** 기존57개/55.36초와 추가 orphan 파일 수
  budget1개/0.20초, skip0. 추가한 검증 전후 제품 코드/기존57개 시험은 같다.
- 원6프로그램의 실제 writer→reader가 canonical 상태/누적·진단/수지·sample/event와 같다.
  초기/t0 commit/내부 걸음/forcing·event·output pending 경계에서 저장·재시작했다.
- 원7종 hold의 확인 과거/빈 과거·fractional trial을 보존하고 실패 시점의 미래 sample을 만들지 않는다.
  root/commit/page를 다시 hash한 counter type/parent/prefix/clock/수지/예산/순서/LAI/제거량/
  status/shape 변조, hash·symlink/FIFO/oversize/missing/UTF-8/중복 key와 닫힌 handle을 거부한다.
- 배타 writer·오래된 HEAD·고지/context/code pin·deep copy·선택 page 재hash·유한 cursor,
  HEAD 전후 예외/미게시 root·orphan byte/file 수와 commit budget의 RHS 시작 전 거부를 확인했다.
  기존 directory는 보존하며 FD·소유 임시 파일·자식을 정리했다.
- **별도 Python7개/847 float64** 복원과 terminal root 읽기에서 canonical 결과가 같다.
  실제 child에서 RHS/advance/원 integrator를 금지해 세 호출 모두0회를 확인했다.
- 긴 입력은 이전 실행 증거와 같은 **자작25시간·300forcing 구간·11,400실제 RK4걸음**이다.
  4,864걸음/forcing index127·`2026-01-01T10:40:00Z step-end`에서 실제 파일을 닫고,
  다른 Python이 복원해 pending forcing 변경/전량 과실 제거/output을 한 번만 처리했다.
  93commit·27sample/5event의 canonical 전체 물리 payload와 최종 y/seed `.hex()`·두 prefix가
  원 rates를 사용하는 독립 전체 제어 루프와 같다. 합성20°C/PAR400/CO₂800은 실제 온실 자료가 아니다.
- **실제 강제 종료2개:** child의 HEAD 게시 전 `os._exit(73)`과 게시 후 `os._exit(74)`를 실행했다.
  실제 HEAD의0/1commit에서 새 writer로 복원해 원 결과와 대사했다. 파일 lock은 프로세스 종료로
  해제됐다. 예외 mock만으로 이 증거를 대신하지 않았다. 호스트 전원 장애 시험은 아니다.

```bash
cd backend
nice -n 10 .venv/bin/python -m pytest -q tests/test_crop_cycle_artifact.py
```

```bash
nice -n 10 backend/.venv/bin/python research/crop-cycle-artifact-reference.py \
  --output /tmp/ossf-cycle-artifact-recheck.json
```

실제 reference 전체 **236.264초**, parent 최대RSS **54.05MiB**·child **53.68MiB**다.
독립 전체 계산106.676초, writer parent+child111.137초다. 긴 결과의 소유 저장은
**755,868bytes/127파일**, 임시 파일 잔여0개다. 읽기/검증은 **0.388759초**,
samples3/event2 단위 관측 응답 최대 **32,918bytes**다. reader의 `referenced_bytes=763,748`은
HEAD의 보수적8,192bytes 예약을 포함한 검사용 값이며 실제 저장량과 구별한다.
`max_selected_checkpoint_bytes=2,970`은 짧은6개에서 선택한 checkpoint의 최대치다.
전체/긴 checkpoint 최대치로 표시하지 않는다. WSL 전체 메모리나 HTTP 응답시간 측정은 아니다.
자작 입력/결과/응답 tempfiles·FD·자식을 정리했고 DB/서버는 시작하지 않았다.

## 발견·수정과 검토

반례에서 닫힌 context의 예외 타입, bool/float delta counter 허용, HEAD 교체 뒤 예외 시 writer가
열려 있는 문제를 발견했다. typed rejection/정수 counter와 게시 예외 시 writer close로 고쳤다.
orphan bytes가 이미 전체 상한을 넘었어도 다음 RHS를 시작하는 반례도 발견해 `advance` 앞에서
전체 directory budget을 검사하도록 고쳤다. RED log hash를 영수증에 보존했고 최종 검증은 통과했다.
단일 writer의 직렬 API이며 thread-safe 공유나 외부 진본 인증으로 표시하지 않는다.

현재 Codex CLI turn_context **2026-10-05T07:46:25.992Z**, **gpt-6.1-sol / xhigh**에서
설계/구현/검토했다. 실제 metadata line SHA·입력/source/output/log hash를 기록한다.
재귀 Codex CLI0회다. 별도 Python 시험은 제품 runtime Codex 호출 증거가 아니다.

검토는 finite byte/file/record·closed JSON·원 sequence/checkpoint/seed/clock/수지·event 제거
fSum 순서·hold/확인 과거·atomic 게시·불확실한 HEAD/재시작·배타 lock·재계산 없는 읽기와
FD/소유 파일 정리를 확인했다. SHA/수지는 현재 권리/HMAC·독립 승인/G0–G4를 증명하지 않는다.
소유 directory의 fsync/rename을 실제 프로세스에서 시험했으며 배포 스토리지의 전원 장애/
백업 복원·DB 게시/custody·worker lease/cancel 수용은 후속이다.

첫 reference는 Git`130ede3`의 구현 중 계약/57개 시험 파일 hash에 고정돼 있다.
추가 파일 수 budget 시험과 최종 계약 hash는 수용 영수증에서 Git 초안과 대사한다.
첫 reference를 덮어쓰지 않았다. 기존 hosted 수용 SHA`1555610`의5CI/3,456backend+UID4는
별도 [terminal 기록](artifacts/crop-startup-replay-ci-20261005.json)이다.
후속 SHA`fe41e22`는 artifact 코드 이전이며 CI 상태는 별도 exact-SHA 기록을 따른다.
그 authored-browser 첫 시도는7passed/정리 성공 후25분 job deadline으로 취소돼 미수용이며,
같은 SHA의 해당 작업만 재실행했다. 이 파일의 로컬 수용으로 원격 상태를 승격하지 않는다.

## 다음 한 단계와 외부 의존성

다음 **`crop-cycle-storage-schema`**는3파일(new installer module/test/contract)에 한정한다.
512MiB 결과를 기존20MiB startup row에 넣지 않고, [고정 stack](../docs/TECH_STACK.md)의
private POSIX 결과와 DB의 불변 metadata/root 참조를 연결한다. 공개/요청 본문에 경로나 원본을
넣지 않는다. schema는 tenant/study/revision/result ID·현재 farm 등록 참조·input/artifact root/
metadata hash·정수 step/record/commit/storage 예산을 대사할 수 있는 제약을 둔다.
HMAC 확인과 파일 실재/현재 권리 검사는 다음 custody의 서버 책임이다.

수용 기준은 실제 PostgreSQL/SCRAM의 새 표·등록 외래키/bytes/판본/범위/정수 counter·중복/
잘못된 root·metadata 혼합 거부, owner UPDATE/DELETE 거부, 기본 runtime 네 role의 새 권한0,
다시 provision할 때 기존 표/bytes를 자동 수정하지 않는 명시 migration 경계와 DB/password 정리다.
기존 startup v3 schema/store/API의 의미/hash를 보존한다. schema 단독으로 부모 저장을 체크하지 않는다.
그다음 **`crop-cycle-storage-roles`**의5파일에서 기본 false의 명시 flag/role/config와 실제
authority SELECT/INSERT만 허용·다른 role/과다 grant·누락/false 호환/정리를 별도 수용한다.
두 단계 이후 현재 farm/source 권리/HMAC custody → API → client → 같은 UTC3D로 진행한다.

schema 계획은 참조/metadata 계약0.5–1시간+installer/불변 제약1시간+
실제 SCRAM/잘못된 행·회귀/정리1–2시간의 **2.5–4집중시간**,
하루4시간/CI 대기 제외 **10월5–6일 KST 잠정**이다. 관측 근거는 이번58개·236초 파일 시험과
앞선 v3 schema의184개 실제 SCRAM 수용이며, 아직 다음 schema를 실행했다는 뜻은 아니다.
최초 artifact5–8시간/10월5–7일 예상은10월5일 로컬 완료 실적으로 대체한다.

166일 실제 RHS 부하·전체 작기 결과/3D, 실제 forcing/초기/관리·품종 채택,
자동 착과/pre-onset/RGR·생과kg·구매 자원/경제·G0–G4는 미수용이다.
실제 채택0개·국내 독립 자료0건·actual crop Run0개다. 농장 자료 확보는 모델 개발과 병행하며
미래 생산 예측·추천/production 완료 날짜는 자료 확보 전에 산정하지 않는다.
