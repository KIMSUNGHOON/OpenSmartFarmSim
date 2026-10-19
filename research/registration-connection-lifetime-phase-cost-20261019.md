# 등록 연결 수명 이후의 실제 단계 비용 — 2026-10-19

[기계 증거](artifacts/registration-connection-lifetime-phase-cost-20261019.json).
현재 native Codex CLI `gpt-6.1-sol` / `xhigh`에서 판단했고 실제 turn_context의 시각/해시를 기록했다. 재귀 CLI는 실행하지 않았다.

## 독립 진단의 종료

[CI39250605987](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/39250605987)은 source `f403b546ec1cc4d6b3f061b60e0fe74a052d634d`에서 원 body/입력64/chunk1/조회/retry360/RSS를 유지하고 기존 bounded `phases` observer만 켰다. 원360초 조건으로 failure, guard383.177251초, 자식1이었다. artifact12186191379의 SHA-256/digest·크기16,646bytes·5개 허용 경로/파일과 run/head/header/actor를 대사했다.

마지막 advance/confirm은17/64·`2026-10-01T00:00:34.123456Z`다. 종료 뒤 같은 소유 DB의 Read Only/Repeatable Read metadata도 attempt1/simulating·sequence18을 확인했다. 이는 현재 권리/정상 완료 수용 증거가 아니다. normal/DB cleanup/actor proof는 없고 API/worker의 정리 종료는 각각-15다. 기록된 phase 예외0과 빈 actor journal을 전체 무오류로 해석하지 않는다. 최근 사건57,003개는 유한 journal에서 탈락했다.

등록 조회734회·재구성113회와 binding.current366회가 관측됐다. current 포함324.332초, registration 포함273.818초, confirm 포함132.518초, advance 포함189.173초이며 수학 advance18회의 포함 시간은1.393초다. **중첩 포함 시간은 합산하지 않는다.** 종료 시 advance가 활성 상태였으며 완료되지 않은 구간 시간은 반환 합계가 아니다. observer 비용이 포함되므로 무계측33/64와 진단17/64를 처리량 개선/퇴행으로 비교하지 않는다.

호스팅 단일 PID127,197,184bytes/합368,865,280bytes·FD7→7·잔류 non-zombie/임시0을 확인했다. WSL의 보호5root 동시 용량 수용으로 세지 않는다.

## 실제 로컬 한 묶음 분리 관측

`focused-registration-worker-quantum-cost-v1`의 실제 SCRAM 작업에서 before→advance→confirm을 한 번 실행했다. SQL의 실제 반환을 대체하지 않았고 선택 함수 profiler/SQL observer만 추가했다. 원 step2/UTC04.123456Z를 확인했다.

| 구간 | 관측 wall(초) | 등록 재구성 | 역할 감사 | 원천 읽기 |
|---|---:|---:|---:|---:|
| before | 1.730133 | 2 | 46 | 152 |
| advance | 11.548158 | 1 | 183 | 1,824 |
| confirm | 7.746714 | 3 | 144 | 1,064 |

관측 wall은 profiler 비용을 포함하며 서비스 처리량이 아니다. 함수별 포함 시간과 SQL 실행 시간도 중첩된다. 로컬 guard55.651653초·자식0·합1,002,332,160bytes·FD4→4·5root/원본2,148/두 frozen UI 보존·소유 PG/역할/schema/임시/passfile 정리를 확인했다.

## 다음 최소 변경

checkpoint의 `_current`가 기존 server 등록 범위 밖에서 호출되면 등록 두 회를 각각 재구성한다. **이 한 함수 안에서 기존 등록 읽기/연결 범위를 사용**하는 작은 변경을 검증한다. 이미 server 범위 안이면 기존 witness를 그대로 유지한다. 새 범용 pool/캐시/프레임워크는 필요하지 않다. 현재 권리·원천의 실제 재검사, 원 트랜잭션/잠금 해제, 수명/복제 문맥 거부를 보존하고 원 작업자/ABBA 비용으로 평가한다.

이 진단은 [이전 로컬58](registration-connection-lifetime-integration-20261019.md)에 추가 기능 통과 수로 합산하지 않는다. [원 독립64 미완료](registration-connection-lifetime-native-normal-20261019.md), 새 Solar 배포/계산 중3D, 실제 농장/독립 자료 및 G0–G4/전체 완료일은 미수용/미정이며 goal은 active다.
