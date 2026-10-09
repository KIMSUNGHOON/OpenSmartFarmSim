# 선행 자식이 있는 pytest 실행기의 소유 프로세스 검사 수정

2026-10-09. native Codex CLI `gpt-6.1-sol / xhigh`, 재귀 CLI0회.
core `bba1167`, [3파일 계약](../contracts/owned-research-test-isolation-v1.md),
[로컬 원 실행·대사 기록](artifacts/owned-research-shared-controller-reference-20261009.json).

## 원인과 좁은 수정

기존 [Backend37918274666/921d0e7](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/37918274666)의
분할1은892통과/2실패였다. 두 strict sent-set 검사에 같은 선행 PID가 추가됐지만
그 과거 PID의 종류는 원 로그만으로 확정할 수 없다.

정확한 uv Python3.12.13에서 spawn-context semaphore로 실제 resource tracker를 만든 뒤
같은 Python에서 기존 pytest를 실행하자 같은 두 검사가 실패했다. 추가 identity는 이 알려진 tracker와 일치했다.
tracker는 SIGTERM을 무시해 살아 있었고 두 검사 모두 종료 대상에 포함됐다.
제품 helper는 자기 실행기 전체 자식을 소유한다고 규정한다. 시험이 만든 가족만 존재한다는 fixture 가정이 틀렸다.

fixture는 시험 가족 생성 전에 기존 자식 identity를 고정하고 scope 생성 때 명시 protected로 전달한다.
그 뒤 생성한 소유 가족은 보호하지 않는다. 선행 일반/thread 가족의 보존 회귀2개를 추가했다.
제품 helper 원문/hash와 기존16개 test 함수의 모든 assertion AST는 그대로다.
sent-set 허용 집합·pidfd/identity·보호 가지/FD 검사를 줄이거나 skip하지 않았다.

## 통과한 검증

| 원 실행 / 실제 종료 | 조건과 결과 |
| --- | --- |
| 95993 / 1 | 수정 전 uv3.12.13+실제 tracker. 기존2실패/28제외, 같은 tracker extra identity 재현. 수용 성공이 아니다 |
| 48295 / 0 | 수정 후 uv3.12.13+실제 tracker,32통과/0.92초 |
| 95789 / 0 | 기존3.12.3+실제 tracker,32통과/0.98초 |
| 15059 / 0 | uv3.12.13 일반 실행,32통과/0.90초 |
| 36281 / 0 | 기존3.12.3 일반 실행,32통과/0.95초 |

고유32개를 두 배포본/두 조건에서 확인했다. 각 controller는1.361–1.375초다.
tracker 조건은 원 identity 생존을 확인한 뒤 자기 semaphore를 해제하고 stdlib stop으로 정리했다.
각 실행의 controller FD4→4·소유 비좀비0·원본2,148항목·현재 source/미리보기/배포 파일·frontend200을 대사했다.
0.25초 관측 단일/명시 소유+보호 트리 합 RSS 최대147,255,296/359,534,592bytes로512MiB/1GiB 안이다.
별도 root `c281b9` 실제0은 현재1,663 source·원본·실제 종료/트래커 부재,
미리보기 서비스FD8→8/root4→4·원 controller/서비스/PG 생존을 확인했다.

## 후속과 남은 범위

로컬 재현/수정은 수용했다. **새 exact-commit hosted 분할1/전체 CI는 아직 미수용**이며 push 후 별도로 확인한다.
기존921d CI가 실제 completed/failure임을 다시 확인했다. 현재 실패3개 분할 중2/3의 과거 수확 관측은
선행 로컬 수정으로 보완됐고, 이번에는1의 시험 격리만 바꿨다. hosted 통과를 미리 주장하지 않는다.
현재 사용자5173의 완료 생장/수확과 실시간 U3 미구현 상태는 유지된다.
후속 작물 계산은 수관/온실 입력·시간격자·수지 대조→기후/물·양분/구매 에너지→사용자 실행/Decimal 경제다.
실제 품종·농장 Run·국내 독립 자료0건과 G0–G4/생산/미래 마진/추천 hold를 유지한다.
