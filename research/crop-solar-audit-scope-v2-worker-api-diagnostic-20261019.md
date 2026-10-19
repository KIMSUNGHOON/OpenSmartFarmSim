# 현재 Solar 작업자/API 진단 — 2026-10-19 KST

[선행 실제 청크/원22/64 미완료](crop-solar-audit-scope-v2-remaining-cost-20261019.md) ·
[진단 계약](../contracts/crop-solar-worker-progress-diagnostics-v1.md) ·
[기계 증거](artifacts/crop-solar-audit-scope-v2-worker-api-diagnostic-20261019.json).

## 실제 결과

[CI39191823795](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/39191823795),
head7901e0891f0ff0e051602a7a061b8efa062d1bb0는240.708초·worker1/API-15로 종료됐다.
기존 `worker-api` 선택 진단이며 정상 완료 수용이 아니다. backend/원 probe/계측 header는
원22/64 실행 sourceeb943d9와 같은 bytes다. ZIP21,747bytes와 제공 digest/path를 검증했다.
51691:0에서 원 actor 본문 보존/AST와 예상 계측 actor·header SHA를 계산했고 실제 artifact와 일치했다.

실제 worker 반환은 **attempt1/queued/solar_execution_busy**다. `_confirm`에서 custody
open Pending이 발생했고 기존 재시도 뒤 반환했다. 마지막 실제 확인은 **8/64·yielded·
UTC2026-10-01T00:00:16.123456Z**다. 종료 뒤 읽기 전용/repeatable read 메타데이터도
동일8/64·sequence9·queued/busy를 기록했다. 메타데이터만으로 현재 권리/원천 검증을 주장하지 않는다.

| 실제 worker phase | 호출 / 반환 | 포함 초 | 최대 초 |
| --- | ---: | ---: | ---: |
| `_adopt` |1 / 1|1.880930|1.880930|
| `_before` |13 / 13|19.558752|1.822138|
| `_confirm` |11 / 11|72.393668|8.054482|
| `_custody_call` |21 / 21|194.971678|14.739345|
| `run_once` |1 / 1|211.261648|211.261648|

시간은 중첩과 계측 overhead를 포함하므로 합산/기여율·원 실행의 속도 비교에 쓰지 않는다.
`_confirm` 예외 사건2개와 마지막 `_custody_call`6.752784초를 확인했다. 이는 기존5초 대기 동안
유효성 검사/재시도가 수행된 실제 전체 시간이며 상한을 늘린 결과가 아니다.
worker 전용 세부 모드에는 custody advance 계측이 없어 `last_advanced=None`을 추정으로 채우지 않는다.
최근32사건/활성16단계와 API 최근32응답/16예외·각64KiB 제한을 확인했다.

API는 수집된15응답에서202/200·none/accepted prefix와 accepted page를 반환했다.
응답은 모두 보존됐고 최근 예외16개는 StopIteration/StopAsyncIteration이었다. 이전 예외20개는
유한 journal에서 제외돼 전체 실행의 무오류를 주장하지 않는다. 이 기록에서 예상 밖 HTTP 오류는 관찰하지 않았다.
인증·원문 body/message·입력/SQL·개인 자료는 수집하지 않았다.

hosted 단일128,888,832/합361,889,792bytes·FD7→7·소유 비좀비/임시0,
resource reason null이다. 정상/DB 정리 proof는 없고 WSL의5root 동시 용량도 수용하지 않는다.
로컬 원 본문 preflight51691:0는5root/원본/frozen source/assets·두 UI·상한/FD/소유 정리를 보존했다.

## 다음 작은 구현

현재 checkpoint `_session`은 `server._open(..., False)`를 사용하지만 root/intent 잠금을
`_file(..., lock=True)`로 열어 모두 배타 잠금을 얻는다. 진행 조회의 짧은 capture/최종 대사도
같은 read session을 사용한다. 읽기끼리 같은 잠금에서 충돌할 수 있다는 **코드에 근거한 판단**이다.
현재 진단만으로 어떤 reader가 마지막 충돌을 소유했는지는 특정하지 않는다.

다음은 [Solar read session 공유 잠금 후보](../contracts/crop-solar-custody-shared-read-locks-v1.md)다.
원 쓰기 배타 잠금과 모든 실제 검증을 유지하고, 읽기끼리의 공존과 writer 배제를 실제로 검사한다.
읽기 세션의 prepare/advance/게시·파일 생성을 금지하는 검증을 함께 둔다.
API와 checkpoint 확인이 실제 같은 read lock에서 공존하는지, writer는 계속 차단되는지 먼저 RED/GREEN으로 입증한다.
원 재시도/360초/입력/청크/권리와 수식은 바꾸지 않는다. 후보는 현재 미구현/미수용이다.

이는 [Linux flock](https://man7.org/linux/man-pages/man2/flock.2.html)의 shared/exclusive
및 별도 open description 의미와 [Python3.12 fcntl](https://docs.python.org/3.12/library/fcntl.html)을
대조한 설계다. 문서 의미가 실제 WSL 파일시스템의 동시 실행 수용을 대신하지 않는다.
native `gpt-6.1-sol/xhigh`에서 진단·판단을 수행했으며 재귀 CLI/서브에이전트는 없다.
로컬116검사는 유지하되 원64 정상·새 Solar 배포/계산 중3D·실제 농장0/G0–G4·전체 완료일은
미수용/미평가/미정이다. 외부 자료/독립 검증 경로와 전체 goal active를 유지한다.
