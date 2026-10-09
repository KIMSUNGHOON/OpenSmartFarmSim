# profile/full runner의 hosted CI 종료 보류

2026-10-06 KST. `8fe7dce`의5개 workflow는 모두 종료했다.
**Backend는 실패이며 profile/full runner/연구용 witness의 hosted 수용은 보류한다.**
운영 기반은 기존 `d19f7c0` 고정과 [선행7a855a7 전체 CI](crop-cycle-route-runtime-ci-success-20261006.md)의
확인 범위를 유지한다.

| workflow | 실제 종료 |
| --- | --- |
| [Backend](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/37434297055) | 5분할 성공·분할2 실패·집계 실패 |
| [Web](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/37434297122) | 성공 |
| [C0 Compose](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/37434297080) | 성공 |
| [Application runtime](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/37434297052) | 성공 |
| [Authored path](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/37434297087) | 성공 |

backend는6분할 모두 동일4,193개 목록 SHA
`aef6f199b659f872fd9a1edac00c315f00a2e05d515363fa3e7a9b4b67332096`을 수집했다.
고유4,185통과·8실패·skip0과 별도 UID4통과를 구분한다. 분할1의 UserWarning2개도 기록했다.
분할2는8실패·519통과/927.08초이며 원 runner가 `PROCESS_RESIDENT_BUDGET`을 반환했다.
원256MiB 제한이 전체 suite pytest 부모의 메모리에 적용된 실패다. hosted의 정확한 RSS 수치는 없다.

별도 작업 트리의 `e310e27`은 원17개 node를 각각 새 pytest 프로세스에서 실행한다.
같은 실제 부모 RSS283,119,616bytes에서 기존 실패와 수정 통과를 재현했고,
decorator 제거 시 회귀 실패 → bytes 복원 후 최종18통과/23.69초를 확인했다.
원 assertions·marker와 제품 자원 제한·수식·CI workflow는 보존했다.
이 commit은 아직 main에 적용하거나 push하지 않았으며 hosted 수정 성공으로 표시하지 않는다.

원166일(session81574)의53 source는 실행 중 그대로 유지한다. 원 계산의 실제 종료와
고정 spec/deadline/원 source·첫 checkpoint/출력/수지·hold 증거를 확인한 뒤 수정 적용과
한 번의 정상 batch push를 진행한다. 현재 CI를 취소/재시작하거나 timeout을 변경하지 않았다.
새 입력 영수증/조회 문맥과 결과 primitive 계획은 이 remote SHA의 수용 범위 밖이다.

실제 terminal API·job/전체 로그 hash·분할 수집 목록/결과와 native CLI 문맥은
[불변 receipt](artifacts/crop-cycle-full-rhs-ci-hold-20261006.json)에 있다.
원 전체166일·실제 품종 작기·독립 농장0건과 G0–G4·생산 예측/추천 보류는 유지한다.
