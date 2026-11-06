# 같은 Farm 소유 입력과 원 초기 seed의 첫 선행 수용 — 2026-11-06

[계약](../contracts/supply-material-farm-input-v1.md)과 [집중 시험](../backend/tests/test_supply_material_farm_inputs.py)의 좁은 입력/초기 seed 선행을 수용했다.
[기계 증거](artifacts/farm-owned-input-and-seed-20261106.json)는 실제 원 입력/현재 witness·원 artifact/proof와 독립 검토/보존을 연결한다.
**전체 material custody, 완전 material 결과 게시/현재 조회, 같은 Farm schema4 비용, HTTP/SDK/같은 선택3D는 미완료다.**

실제 기존 FarmAuthoringService/소유 SCRAM authority로 정확 tenant/Farm/등록 판본/crop/zone을 다시 읽는다.
새로 명시한 합성 Farm floor/cultivable/crop area1과 원 model floor1을 정확 Decimal/Fraction으로 대사하며 옛100m² fixture나 탄소·형상·기관 counter를 바꾸거나 비례 조정하지 않는다.
닫힌 전체 구조 요청은 실제29261bytes, server content witness를 포함한 실제 불변 입력은38790bytes로 각각 기존65536byte 한도 안이다.
입력 내부에는 자기 전체 SHA/미래 root가 없으며 첫 review와 DB UUID/SHA/created_at은 별도 현재 resolved witness에서 보존한다.
명시 원 epoch/UTC+Fraction/작물 점유·Farm 달력, source/rights availability·retrieval·review·actual recording을 구분하고 supplemental ex-post/비확립 ex-ante를 유지한다.

메타 접수와 읽기는 원 Context/RHS/producer/CAS를 실행하지 않는다. 실제 produce는 기존 write+simulation_create 권한을 요구하고 각 제어 numerical/CAS 경계 전후 현재 입력/권한/코드/파일 정책을 검사한다.
새 producer 자체의 원 serialization loop가 진짜 carbon/stem/individual Context와 원 초기 binder를 실행하며 같은 원 입력의 기존 bulk producer와 모든 원 blob bytes/root를 대사했다.
원 schema/dependency map은 format 호환성을 뜻하고, 실제 새 실행 주체/version/code는 별도 seed witness에 기록한다. 새 계수·농도·요금·비용 계산은 없다.
원 initial inventory/상태/area receipt/정확 잔차와 추적 한 shoot를 보존하며 density·per-plant/Farm 전체 생산·품종 적합성을 만들지 않는다.
이는 queued owned-input registry와 초기 seed이며 succeeded simulation이나 DB material publication이 아니다. 현재 proof의 DB simulation publication은null이다.

- **현재 고유163 = 새 모듈 전체53 + 직접 legacy110**. 실제 전체 collection/node union과 단계별 argv·module counts를 대사했다.
  실행 모드는 no-PG 순수25와 소유 PG runner로 실행한 통합/회귀138다. 순수 runner의 계측 psycopg/outbound/process 시도는0이며 PG/DSN 환경을 사용하지 않았다.
  소유 PG 단계는 실제 host SCRAM/16MiB cluster를 종료했다. 필요한 기존 cold-reader 프로세스와 PG transport는 허용하며 전체 network/process0으로 표시하지 않는다.
- 입력의 fixed Farm dispatch·late 취소/claimed 상태·동시 동일 intent, Context numerical grid·file-policy/실패 경로 변경은 실제 RED와 수정/최종 현재-source 검증을 보존했다.
  초기 fixture 실패·옛 구현 부분/반복 GREEN·collection은 이번 고유 passed 수에 더하지 않았다. 선행145/235/13/308/114/425 등은 보존 이력이다.
- 모든 수용 단계는600초/PID512MiB/합1GiB/로그4MiB guard 안에서 실제 종료0·FD4→4·owned0·원본/source/보호 root 보존을 확인했다.
  아래 값은 각 실제 raw pytest/runner/guard 관측이며 합산 완료시간이나 성능 보장이 아니다.
- 원 rational cold-reader의 첫 legacy 단계31통과/1실패는 자식 Python의 app import 경로 누락이며 수용 합계에서 제외했다.
  같은 원 source/04db runner/e370 guard의 새 전체32단계는 guard가 지운 PYTHONPATH를 기존 command mode의 고정 `/usr/bin/env PYTHONPATH=.../backend`로 한 단계에만 설정했다.
  실제 argv/cwd/환경 override와 원 실패를 보존했다. 테스트/모델/guard/runner나 사용자 환경을 고치지 않았으며 다른 probe 단계의 설정은 유지했다.

| 단계 | 고유 | 모드 | pytest초 | runner초 | guard초 | PID peakB | combined peakB |
|---|---:|---|---:|---:|---:|---:|---:|
| seed-unwind-green-v1 | 1 | owned_PG | 70.72 | 72.17080269102007 | 73.62011504010297 | 157700096 | 222625792 |
| pure-v2 | 25 | pure | 0.99 | 1.1209633110556751 | 2.572711273096502 | 107626496 | 140562432 |
| integration-flow-v2 | 1 | owned_PG | 39.32 | 41.15399688691832 | 43.41464809398167 | 116146176 | 209547264 |
| seed-faults-green-v2 | 4 | owned_PG | 166.57 | 168.27284053899348 | 170.43823309079744 | 115814400 | 222027776 |
| integration-metadata-v2 | 6 | owned_PG | 87.04 | 88.99659182108007 | 91.12677439581603 | 113938432 | 220385280 |
| integration-current-v2 | 6 | owned_PG | 86.15 | 88.0648857629858 | 90.15446324483491 | 134848512 | 223305728 |
| integration-transactions-v2 | 6 | owned_PG | 94.7 | 96.56785356579348 | 98.45594467991032 | 119062528 | 253800448 |
| integration-late-producer-v2 | 3 | owned_PG | 64.46 | 66.21524509298615 | 67.67313316604123 | 114311168 | 218988544 |
| integration-linkage-v2 | 1 | owned_PG | 95.33 | 96.85057575488463 | 98.41454878193326 | 115884032 | 213512192 |
| legacy-authoring-v1 | 3 | owned_PG | 39.05 | 40.66902319691144 | 42.186455118935555 | 156090368 | 253198336 |
| legacy-read-scope-v1 | 13 | owned_PG | 163.22 | 165.66325049800798 | 167.4655322509352 | 148959232 | 295231488 |
| legacy-initial-binding-v1 | 46 | owned_PG | 7.32 | 8.680510067148134 | 10.193401347845793 | 101179392 | 165449728 |
| legacy-rational-v2 | 32 | owned_PG | 4.65 | 6.060266966931522 | 7.6521011490840465 | 108318720 | 171642880 |
| legacy-carbon-v1 | 16 | owned_PG | 54.25 | 55.65258125285618 | 57.194835289148614 | 102920192 | 167636992 |

부모38 integration과 추가 관련 원 source의 실제 union81은 current/Git62와 같고 새 입력/seed/test3을 더한84를 보존했다.
kernel750 중748 current와 worker Git8f/query Git4edef의 기존 두 예외만 유지하며 새 strict 예외는0이다. 과거 manifest/receipt/script/원 수치 입력·출력은 바꾸지 않았다.
저장3D687source/4output/745private/46external, 만료5184의238/5181의233파일·원 소유/첫 만료/과거 HTTP 증거와 원2148/감시4500·원5175를 보존했다.
이번 preview HTTP는0이고 재시작/수명 연장은 없다. 실패 후 이미 쓴 보호 CAS blob은 남을 수 있으며 SQL rollback이 파일을 지웠다고 주장하지 않는다.

실제 native CLI0.166.0/gpt-6.1-sol/xhigh author/test/doc와 생산 작성자와 다른 다섯 축 검토/owner 수용을 SHA로 연결했다.
부모 orchestration은 실제 ultra이며 xhigh 판단으로 표시하지 않는다. 재귀/새 Codex CLI는 없다.
전체 backend/frontend/browser·새 HTTP/SDK/UI·사용자 배포는 실행하지 않았다. 독립 국내 raw0·G0–G4 미평가/R2 미승인·전체 goal active/incomplete를 유지한다.

다음 수치 작업은 **Add a genuine material.Handle successor/repeated-event numerical owner/point/proof capability before another material admission/worker/query stack.**
기존 첫 material adoption 뒤의 실제 material.Handle 다음 pending을 옛 forcing-only point API가 소비하지 못하는 능력 공백을 먼저 닫는다.
새 admission/worker/query stack을 먼저 더하지 않고, 같은 원 모델/장부를 재사용하는 additive successor의 실제 반복 사건/성장을 검증한다.
정적 material parameter/event-parent plan과 owned seed compiler 검토는 병행할 수 있다. 다음 수용 조건은 다음과 같다.

- genuine first-adoption result reaches real second pending event
- new version consumes actual second and third events exactly once and reaches explicit bounded horizon
- full/split/cold proofs preserve original grid/state/all ledgers and independently show real organ/state growth
- piecewise forcing order/rights/code/cancel/bounds reject without partial current
- Keep every old model/input/output version unchanged; use explicit owned synthetic declarations without new coefficients or handle casts.
- Do not claim full season: separately review/prove longer horizon/capacity/restart and complete forcing/material coverage; retain independent crop/economic/data/gate requirements.

이 제한2–3사건 증명은 한 작기 완료가 아니다. 긴 horizon/capacity/restart·완전 forcing/material 입력을 별도 증명해야 한다. 이후 genuine full lineage/lease-CAS terminal publication/current no-replay query와 별도 같은 Farm schema4 비용 association, HTTP/runtime/strict SDK/같은 선택 현실적3D·표·그래프/실제 브라우저가 계속 필요하다. 다음 집중 공수와 전체 완료일은 검토된 값이 없어 미정이다.
