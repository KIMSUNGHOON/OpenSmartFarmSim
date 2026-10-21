# CO₂ 자동 계산 worker core 기능 수용 — 2026-10-21

source `0bca8cd6ed0855efbb5dcd4fd0a613c662eeadfe`의
[CI39527128812](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/39527128812)는 성공했다.
[원 증거](artifacts/crop-greenhouse-co2-worker-core-20261021.json)의15개 curated JSON과 현재311개 source 지문을 대사했다.
Codex CLI `gpt-6.1-sol` / `xhigh`의 실제 native turn/hash와 판단을 기록했으며 재귀 CLI/하위 agent는 사용하지 않았다.

## 확인한 범위

20검사 = 제어9 + 실제 SCRAM11, skip0이다.

| 경로 | 수용 증거 |
| --- | --- |
| 정상·수치 hold2 | 원32초 프로그램의 samples/events·109상태/44연속·6사건 장부·17수지와 checkpoint/last-confirmed·UTC를 직접 producer에 대사. registry/link/outcome 각1, 정상 publication1/hold0. |
| 취소2 | chunk/terminal 경계의 cancel ACK·원 사유와 결과/게시 없음. private HEAD를 사용자 확정 결과로 바꾸지 않음. |
| 임대 만료1 | 첫7걸음 뒤 만료, 같은 프로세스의 새 시도2가 원 HEAD 채택 시17계측0·start0/남은9걸음만 계산. 독립 프로세스/SIGKILL 증거는 아님. |
| 저장 실패2 | terminal event/최종 UPDATE fault에서 결과·link·publication·terminal rollback, 원 확정 prefix 유지·queued closure1. |
| 늦은 변경4 | outcome 뒤 실행 범위/권리/resolver 변경3과 성공 terminal UPDATE 뒤 실행 범위 철회1에서 결과 쓰기 전부 rollback·hold closure1. |

계산 중 정상/hold는 각각16걸음·3 chunk와97/96 RHS를 실제 실행했다. 원 결과 조회·중복 실행,
prefix 채택·미리 계산된 terminal의 rollback 검증 구간에서만17계측0이다. SQL 결과/사건 쓰기는 의도된 동작이다.
worker 시간31.22/31.08초는 이 합성32초 입력의 hosted 관측이며 전체 작기/WSL 처리량 추정이 아니다.

## 자원과 보존

hosted guard402.675218117초, 단일 PID116,584,448/합267,436,032bytes,
.25초 간격1,567 samples, FD6→6이다. 원600초·512MiB/PID·합1GiB 안이다.
source 지문 보존, 소유 non-zombie/임시 경로/passfile0, schema/role0을 확인했다.
이 검증은 hosted이며 기존 WSL 동시 용량 보류를 해제하지 않는다.
로컬 사전 제어/수집 및 두 UI의 pending 기록 게시에서 원2,148자료/5root·frozen source/HTML을 보존했다.

## 다음과 미완료

`co2-worker-core` 자식만 수용한다. 다음 `co2-worker-consumer-restart`는 기존 discovery/loop에 exact
CO₂ 입력/결과 쌍을 추가하고 독립 normal/hold 자동 발견·원 결과 fresh 읽기/현재 권리와 실제 pidfd SIGKILL
뒤 남은 구간만 재개를 검증한다. 두 자식 수용 전 worker 부모는 완료하지 않는다.
이후 진행 query/HTTP/runtime→typed web/같은 UTC3D→공통 WSL/사용자 적용 순서다.

새 CO₂ 배포·전체 작기/물·양분/구매 에너지·경제·최종 UI/실제 CLI 종단 간·독립 농장 자료/G0–G4는
미완료다. 실제 농장 Run0·전체 완료일 미정/goal active, 기존161–308집중시간의 낮은 신뢰 계획을 유지한다.
