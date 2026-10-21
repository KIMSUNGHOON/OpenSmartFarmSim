# CO₂ 중간 확정 기록 기능 수용 — 2026-10-21 KST

[CI39524881613](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/39524881613)의
source `a8cc095303f3fabadac0da6ceb11cf1470f8c488`에서26검사(제어13/실제 SCRAM13)가 통과했다.
[기계 증거](artifacts/crop-greenhouse-co2-checkpoint-20261021.json)의17개 산출물/308개 현재 source 지문을 대사했다.
전체 backend/새 브라우저는 실행하지 않았다. 합성32초 소프트웨어의 checkpoint 기능 수용이다.

## 확인한 기능

[실행 핵심 계약](../contracts/crop-greenhouse-co2-execution-core-v1.md)의 exact Co2 admission/custody·같은
jobs/resolver, 원 signed HEAD/provenance·8KiB metadata·임대/현재 입력/취소와 마지막 실행 권한을 연결했다.
마지막 실행 권한 검사는 private reader 종료 뒤 거래 commit 전에 있다.

| 검증 | 결과 |
| --- | --- |
| 원 상태 | ready/yielded/completed/수치 hold4종의 원 HEAD/metadata·UTC/파일 SHA 유지 |
| 중복 확인/전진 | 같은 event/최초 recorded_at, 새 객체/lease 갱신 뒤 동일, 다음 signed HEAD의 ancestry/순서·최초 사건 유지 |
| 현재 접근/빈 상태 | tenant/자료 권리/실행 scope3개 거부, 없는 HEAD는 초기화·새 계산/게시 없이 거부 |
| 불변성/잘못된 metadata | owner의 이력 UPDATE를 DB가 거부; 잘못된 새 snapshot2종의 실제 INSERT를 관측하고 checkpoint 거래 rollback·정상 다음 기록 수용 |
| 늦은 변경 | 두 번째 현재 검사 뒤 cancel/expiry/input/execute scope4종에서 checkpoint rollback |
| 입력 변조 범위 | 실제 immutable input UPDATE 거부 + 최종 locked-row 읽기의 별도 fault injection; 실제 입력 bytes 유지 |
| 계산/정리 | 확인 중17개 수치/context/restore/새 UTC/CLI 진입점0, source 파일 유지·게시/결과0 |
| 자원 | 350.345596초, 단일115,847,168/합203,440,128bytes·.25초 표본1,360개·FD6→6; schema/role/소유 process/passfile/임시 DB 항목0 |

준비·advance의 실제 계산은 계측 전 수행했다. 의도한 checkpoint SQL쓰기는 있으며 모든 산술0을 주장하지 않는다.
ready의 중단은 fixture stop이고 새 객체는 같은 프로세스다. 실제 SIGKILL/독립 fresh worker는 아직 미수용이다.
원600초·512MiB/PID·합1GiB·4MiB log 한도를 유지했다.

[첫 CI 실패/시험 준비 수정](artifacts/crop-greenhouse-co2-checkpoint-immutable-test-fix-20261021.json)은 보존했다.
DB가 금지한 이력 UPDATE를 시험에서 시도한 원인을 실제 소유자 PG16 probe로 재현했다. DB trigger/권한·제품 코드를
유지하고 같은26개를 재검증했다. fault injection과 실제 DB 변경을 구분해 기록했다.

개발 기록을 localhost5173/5174의 같은 JSON/HTTP200/no-store로 게시했다. 원 HTML·환기 frozen2,173파일,
원 자료2,148항목/보호5root·FD4→4와 소유 정리를 보존했다. 새 DOM/WebGL 검증은 실행하지 않았다.

## 다음 단계

worker core에서 원 구간 계산/독립 confirm과 result/link/outcome/terminal 원자 저장을 검증한다.
그 뒤 기존 discovery/loop에 명시 판본을 연결하고 독립 정상/hold·fresh 읽기·실제 SIGKILL 뒤 남은 구간만 계산을 수용한다.
worker 부모는 두 단계와 원 수치/UTC·현재 권리·소유 정리가 모두 통과하기 전 미완료다.
[공통 WSL 용량](api-crop-greenhouse-co2-replay-20261021.md)·새 CO₂ 사용자 적용/전체 작기·자원/경제·실제 CLI 종단 간·
독립 농장 자료와 G0–G4는 남으며 전체 완료일은 미정·goal active다.
