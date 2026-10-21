# CO₂ 실행 진행 조회 기능 수용 — 2026-10-21

[계약](../contracts/crop-greenhouse-co2-execution-query-v1.md) ·
[전체 증거](artifacts/crop-greenhouse-co2-execution-query-20261021.json).
첫 [CI39533373500](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/39533373500)의24개와
후속 [CI39534107848](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/39534107848)의11개를 수용했다.
겹치지 않는35개 = 제어15 + 실제 SCRAM18 + 독립 SCRAM2, skip0이다.
source2f8b5e9/3eb99bd의 선택324파일 SHA가 서로 같고 수용 시 현재 파일과도 일치했다.
실제 native Codex CLI `gpt-6.1-sol / xhigh` 판단과 turn/hash를 기록했으며 재귀 CLI/하위 agent는 사용하지 않았다.

## 원 진행/현재성

정확한 Co2 checkpoint/result/server와 닫힌16KiB 응답을 연결했다. 읽기 전용 repeatable-read·
별도 DB probe와 직렬화 뒤 현재 권리/입력 검사를 유지한다. 계산·복원·확인/접수/임대·결과 쓰기를 실행하지 않는다.
queued/canceled·none/current/unavailable, 원 HEAD/건수·계산 UTC와 최초 확정 UTC의 heartbeat/시도2 유지,
정상/수치 hold 결과 연결·publication1/0을 확인했다. 미확정 HEAD나 busy 상태에 추정 진행률을 만들지 않는다.

늦은 권리 철회·잘못 추가된 불변 checkpoint 사건, 반환 bundle 오류5종, 별도 actor의 job 변경,
잠금 해제/유지, 유효한 signed HEAD 전진·손상과 동일 byte의 directory 교체에서 원 Hold/Pending을 확인했다.
반환 bundle fault를 실제 불변 DB 행 UPDATE라고 주장하지 않는다.
조회 측31계측(수치/CLI·SQL쓰기·job/result 변경)은 모두0이다. job-drift의 별도 actor UPDATE1건은
조회 SQL0 계측 밖의 명시된 시험 변경이며, 다른 DB 불변 검사와 구분한다.

정상/수치 hold는 같은 소유 DB·원 파일에서 준비→자동 worker→fresh reader를 별도 프로세스로 실행했다.
create/execute/write 범위 없이 읽고, 두 조회의 DB 관측 시각을 제외한 DTO SHA·원 계산/최초 확인 UTC가 같았다.
현재 review 철회는 거부했고 fresh31계측0·원 상태/결과를 유지했다.

## 자원·첫 실패

| 배치 | hosted guard 초 | 단일 PID bytes | 합 bytes | FD |
| --- | --- | --- | --- | --- |
| 첫24 | 237.513439328 | 144,347,136 | 302,821,376 | 6→6 |
| 후속11 | 343.498660632 | 140,853,248 | 344,109,056 | 6→6 |

각600초·512MiB/PID·합1GiB, .25초 샘플링 기준을 유지했다. 모두 schema/role·소유 프로세스·passfile·
임시 경로0과 source 보존을 확인했다. 로컬 제어/수집/기록 게시에서 원2,148자료/5root·두 UI/frozen source를 보존했다.
hosted 기능 수용으로 WSL 동시 용량을 해제하지 않는다.

[첫 실패/기록 필드 수정](artifacts/crop-greenhouse-co2-execution-query-evidence-fix-20261021.json)은
pytest24 종료0 뒤 권리 기록의 필수 DB 불변 표지가 빠져 엄격 후검사에서 거부된 것을 보존한다.
원 DB 비교·31계측0/엄격 후검사를 유지하고 표지 기록만 수정한 뒤 같은24를 재검증했다.
기존 수식/프로필·공유 schema/역할·worker·HTTP/runtime/OpenAPI·사용자 배포는 변경하지 않았다.

## 다음

`co2-execution-query` 기능을 수용한다. 다음은 원109상태/44연속·6사건/17수지·UTC를
DB 확정 selector에 연결하는 CO₂ prefix 원 조회다. 서명했어도 미확정인 HEAD는 채택하지 않고
이전 확정 페이지의 정상 append/heartbeat·현재/직렬화 뒤 권리/페이지·독립 fresh/정리를 검증한다.
이후 공개 투영→보호 실행 HTTP/runtime→typed web/같은 UTC3D→WSL/사용자 적용이다.

합성32초 소프트웨어 조회이며 새 CO₂ 배포·전체 작기/자원/경제·최종 UI/실제 CLI 종단 간·독립 농장
자료/G0–G4/실제 예측·추천은 미완료다. 전체 완료일 미정과 기존 낮은 신뢰 공수 계획을 유지하며 goal active다.
