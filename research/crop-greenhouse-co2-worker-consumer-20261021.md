# CO₂ 독립 자동 worker·강제 종료 재개 기능 수용 — 2026-10-21

[실행 계약](../contracts/crop-greenhouse-co2-execution-core-v1.md) ·
[원 증거9개/318지문](artifacts/crop-greenhouse-co2-worker-consumer-20261021.json) ·
[CI39530741390](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/39530741390).
source `314bc26bf7da7383c1d4e802b653cbc0c35b352c`의37검사/skip0을 수용했다.
새 소비자 제어17·기존 Solar14·실제 독립 SCRAM3·기존 libc pidfd 회귀3이다.
실제 native Codex CLI `gpt-6.1-sol / xhigh` 판단과 turn/hash를 기록했고 재귀 CLI/하위 agent는 사용하지 않았다.

## 실제 실행과 원 결과

정상·수치 hold는 준비 프로세스가 종료된 뒤 별도 worker가 ID 수동 전달 없이 CO₂ 작업을 발견했다.
다른 Solar v1 작업은 queued로 남았다. 같은 DB/서명 원 파일의 원 progress와 결과/link·provenance,
정상 publication1/수치 hold0을 대사했다. 별도 fresh reader는 원 payload·progress·페이지/UTC·최초 recorded_at을
재발급 없이 읽고 현재 review 철회를 거부했다. reader의17수치/CLI 계측과 SQL쓰기 모두0이다.

실제 crash 경로는 다음을 확인했다.

1. 첫 worker가7걸음의 signed HEAD를 저장한 뒤 DB checkpoint 확인 전 대기했다.
2. 열린 pidfd에 SIGKILL을 보내 종료 코드−9와 원 프로세스 소멸을 확인했다.
   이때 결과/publication/DB checkpoint0이며 시험 제어가 임대만 만료시켰다.
3. 별도 자동 소비자가 시도2에서 같은 HEAD를 채택했다. 채택 시17계측0, start0/남은9걸음만 계산해
   전체16걸음과 원 UTC·서명 결과를 보존했다. 별도 fresh reader도 원 결과와 현재 권리를 대사했다.

호스트의 Python pidfd open/send API는 모두 없었고 기존 canonical libc pidfd 헬퍼를 사용했다.
[첫 실패/증거 환경변수 수정](artifacts/crop-greenhouse-co2-consumer-diagnostic-20261021.json)과
[정확한 AttributeError 위치·호환 헬퍼 수정](artifacts/crop-greenhouse-co2-consumer-pidfd-fix-20261021.json)을 보존했다.
제품 `backend/app`·수식/프로필·기존 공유 헬퍼는 수정하지 않았으며 기존34개에 회귀3개를 추가했다.

## 자원·범위

hosted137.907263627초, 단일 PID101,625,856/합287,178,752bytes,
.25초 간격546samples, FD6→6이다. 원600초·512MiB/PID·합1GiB 안이며
세 경우 모두 schema/role0, 소유 프로세스/passfile/임시 경로0과 source 보존을 확인했다.
로컬 호환성/수집·게시에서 기존5root/원 자료2,148항목·두 UI/frozen source를 유지했다.
hosted 수용으로 공통 WSL 동시 용량/사용자 적용 조건을 해제하지 않는다.

[worker core20](crop-greenhouse-co2-worker-core-20261021.md)의 실제 원 계산·취소/만료·원자 저장/늦은 fence와
이번 독립 소비자/재개를 합쳐 `co2-execution-worker`의 기능 범위를 수용한다.
합성32초 소프트웨어 증거이며 전체 backend CI나 실제 농장 검증이 아니다.

다음은 [진행 조회](../contracts/crop-greenhouse-co2-execution-query-v1.md)→확정 prefix 선택/보호 실행 HTTP·runtime→
typed web/같은 UTC3D다. 새 CO₂ 배포·전체 작기/자원/경제·최종 UI/실제 CLI 종단 간·실제 자료/G0–G4는
미완료다. 전체 완료일 미정과161–308집중시간의 낮은 신뢰 계획을 유지하며 goal active다.
