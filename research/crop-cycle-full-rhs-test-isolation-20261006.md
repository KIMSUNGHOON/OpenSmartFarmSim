# 전체 작기 참조 시험의 실제 메모리 제한과 프로세스 분리

2026-10-06 KST. **집중 로컬 수용이며 수정 판본의 hosted CI는 미실행이다.**
운영 기반은 `d19f7c0`으로 고정한다. 이 수정은 작물 계산의 기존 자원 제한을
그대로 검증하기 위한 시험 실행 변경이다.

## 보존한 실패와 원인

`8fe7dce`의 [Backend 분할2](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/37434297055/job/112172214121)는
8실패·519통과·3,666deselected/927.08초로 종료했다. 전체 수집 목록은4,193개였다.
실제 참조 runner가 `PROCESS_RESIDENT_BUDGET`을 반환해 중단/완료/저장 제한을
기대한8개 시험이 실패했다. 전체 workflow는 이 기록 시각에 아직 종료되지 않았다.

runner는 실행 프로세스의 **현재 RSS 256MiB**를 검사한다. 전체 suite를 수집·실행하는
pytest 프로세스 안에서 이 runner를 호출하면 suite의 메모리도 제한 대상에 들어간다.
remote 로그는 정확한 RSS 숫자를 남기지 않았으므로 그 값을 추정해 기록하지 않았다.
실제 독립 계산 프로세스의 제한과 산식을 바꾸지 않는다.

동일한 로컬 부모 프로세스에 실제 메모리 페이지를 할당한 재현에서 시작 RSS는
283,119,616bytes였다. 기존 실행은1실패/1.60초·같은 메모리 보류로 끝났다.
첫 수정은 같은 시작 RSS에서1통과/3.76초였다. RSS를 가짜 값으로 바꾸지 않았다.
이 재현의 첫 수정 hash와 최종 회귀 시험을 추가한 hash는 영수증에서 구분한다.

## 수정과 최종 검증

[시험 파일](../backend/tests/test_crop_cycle_full_rhs_reference.py)의17개 원 node는
각각 새 `python -m pytest` 프로세스에서 같은 node와 fixture를 실행한다.
자식의 종료 코드를 검사하고 실패 출력을 부모 assertion에 전달한다.
실행은 직렬이며60초는 시험 자식의 timeout이다. 제품의6시간 global deadline,
256MiB RSS·저장 한도·격자·출력·CI 분할/workflow는 변경하지 않았다.
Codex CLI를 재귀 실행하지 않는다.

원10개 함수 본문의 AST·매개변수 marker를 대사했다. `request` 인자와 실행 decorator만
추가했고 원 assertions와17개 node를 유지했다. 부모 RSS가 실제 제한을 넘는 상태에서
독립 자식의 원 재시작 시험을 실행하는 회귀1개를 추가했다.
decorator만 제거하면 이 회귀는 `PROCESS_RESIDENT_BUDGET`으로1실패/1.97초다.
원 후보 bytes를 정확히 복원한 뒤 **최종18통과/23.69초**를 확인했다.
앞선18통과/23.29초와17통과/20.03초는 고유 검증 수에 합산하지 않는다.

```bash
cd backend
nice -n 15 /home/sunghoonk/Workspaces/OpenSmartFarmSim/backend/.venv/bin/python \
  -m pytest tests/test_crop_cycle_full_rhs_reference.py -q
```

검증은 `/tmp/ossf-crop-full-rhs-test-isolation-20261006`의 별도 작업 트리에서 했다.
실행 중인 원166일(session81574)의 main 소스53개는 여전히 byte/hash가 같았다.
원 계산의 실제 종료 전에는 이 수정 파일을 main에 적용하지 않는다.
새 의존성 설치·PG/API/browser 서버 기동·전체 backend 로컬 실행은 없었다.

실제 `gpt-6.1-sol / xhigh` CLI 문맥·hosted 실패 로그·실제 압력 재현·회귀 RED/GREEN·
소스와 로그 hash는 [불변 영수증](artifacts/crop-cycle-full-rhs-test-isolation-reference-20261006.json)에 있다.
영수증 SHA256은 `09810b2051f5e3f7ce48ff3a7c44456ae318440581949252a02b14cc613a334a`다.

## 다음 수용

원166일 계산과 현재 remote8fe CI의 실제 종료를 먼저 확인한다. 원 계산의 종료/보류 사유,
고정 spec·deadline·53 source·첫 checkpoint 재개·원 출력/사건/수지를 보존한 뒤
이 수정의 main 적용과 한 번의 정상 push를 진행한다. 수정 SHA의 hosted CI 성공은 별도로 확인한다.
`crop-cycle-burden-full-rhs`와 `crop-cycle-burden-replay-restore`는 아직 미수용이다.
다음 핵심 경로는 전체 생장 계산 → 저장 결과와 같은 ID/UTC의3D → 생과·자원·Decimal 경제다.
실제 품종 작기 입력·국내 독립 자료0건과 G0–G4 `not_assessed`·생산 예측/추천 보류를 유지한다.
