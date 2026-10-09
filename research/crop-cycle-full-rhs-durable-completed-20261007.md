# 자작 166일 전체 RHS 계산 완료

2026-10-07 KST. `crop-cycle-burden-full-rhs`의 **소유 합성 입력 전체 수치 실행**을 로컬 수용했다.
[고정 영수증](artifacts/crop-cycle-full-rhs-durable-completed-reference-20261007.json)에 실제 종료 코드,
원 spec·입력·결과·55 source SHA, 전체 파일/행 대사와 자원 관측을 기록했다.
현재 native Codex CLI `gpt-6.1-sol / xhigh`에서 판단했으며 재귀 CLI 실행은0회다.
새 실험은 [지속 저장 감독자](crop-cycle-full-rhs-durable-implementation-20261007.md)를 사용했다.
유실된 원81574 실험의 최종 상태는 계속 확인 불가이며 이 성공으로 바꾸지 않는다.

## 실제 종료와 복원

준비 시작은14:07:36.678777 KST, 원 고정 마감은20:07:36.678777 KST다.
첫 child는 원123걸음·620RHS 뒤 명시 중단하고 종료0을 기록했다.
두 번째 별도 Python child가 **같은 spec·deadline과 체크포인트 전체**를 복원해 계산을 끝냈다.
복원한121개 state와121개 seed, clock·누적·cursor·sequence를 첫 결과와 모두 대사했다.
전체 RHS 실험에서 별도 강제 종료를 추가한 것은 아니며, SIGKILL 복원은 선행 작은 감독자 시험의 증거다.

최종 계산 결과는19:49:35.515178 KST, 감독자의 실제 종료0 영수증은19:49:35.772718 KST다.
준비·첫 중단·재개를 포함한 결과 기록까지의 실제 경과는 **20,518.836401초**로 원21,600초 안이다.
재개 호출만의20,311.080433초와 구분한다. 이 시간은 해당 로컬 순수 실험의 관측이며 제품 완료일이 아니다.

| 항목 | 실제 최종 값 |
| --- | ---: |
| 입력 구간 / 출력 시점 | 47,808 / 47,809 |
| 실제 적분 걸음 / 계획 | 1,816,704 / 1,816,704 |
| 관리 사건 | 5 |
| 재개 호출의 실제 RHS | 9,130,711 |
| 완료 원 reader의 RHS | 0 |
| 불변 commit | 14,567 / 한도16,384 |
| artifact bytes | 466,898,203 / 한도536,870,912 |
| artifact 파일 | 29,141 / 한도65,536 |
| 최대 조회 page bytes | 562,065 / 한도2,097,152 |
| 관측 active RSS / 한도 | 48,201,728 / 268,435,456 bytes |
| 프로세스 과거 peak RSS | 57,257,984 bytes |
| worker FD 전후 | 5 → 5 |

원8초 RK4,300초 출력,chunk10,000steps/128transitions와 저장·메모리 한도를 유지했다.
출력 복제·출력 축소·solver 간격 변경은 없다. 실제 farm/서버 전체 경로의 처리량은 아직 측정하지 않았다.

## 원 결과·수지·파일 대사

원 runner는 완료 전에 원 `open_artifact`의 `_load_prefix`와 `_validate_delta`로
**모든 commit·원 시점·사건의 수지/누적·checkpoint 연속성**을 검사한다.
이 원 reader 전체 검사와 bounded page 읽기를 마친 뒤에만 결과가 기록됐으며 조회 RHS는0이다.
최종 행 개수는 원 input plan의 전체 출력/사건과 같다.

종료 후 별도35.092748초 감사에서 입력750파일/113,920,841bytes와 artifact29,141파일 전체의
regular file·소유권·mode·canonical bytes·이름 SHA를 확인했다. 원55 source도 모두 그대로다.
HEAD/root/14,567commit의 parent·sequence·입력 checkpoint와 모든 출력/사건을 다시 순서대로 읽어
기록된 두 전체 행 SHA와 최종 체크포인트를 재현했다. 이 별도 감사는 RHS 재계산이나 독립 농장 검증이 아니다.

- 원 spec SHA: `d4e7de05249b55a2db3218c3e47c09ac1819ab15415b4021a44399ea76bcc310`
- 입력 root SHA: `ab24eda4d763d7fe3faff1ae3c7c2f84fbec030af71a494bf284fef1f2cdcd98`
- 완료 artifact SHA: `15b609576243c73b67a4947b5affc2db14047787e4851064b3aabeafd3d0286d`
- 전체 출력 SHA: `b00e63d96debcbfc2c80eb5c17b71a9a9bd7bd0634acdb1d6ffe47655ae53dbd`
- 전체 사건 SHA: `0900f8ff0753d3d7746a2ea32b75ed579ba0c07a7789d99e4b4cee01850e1eb8`

실제 worker/controller PID 부재와 배타 lock의 재획득·해제를 확인했다.
원 입력·artifact·로그·request/result/receipt는 소유0700 지속 저장 경로에 보존한다.
worker 영수증의 request/spec/supervision/log/result SHA와0400 원 bytes를 대사했다.

## 수용 범위와 다음 단계

이 증거로 full-rhs 자식만 체크한다. 전체 `crop-cycle-burden`, 등록 농장 전체 저장·복원,
HTTPS30초/2MiB와 동일 ID/UTC3D 부모는 미수용이다. 순수 참조 artifact를 농장 DB 실행 이력으로 재분류하지 않는다.
다음은 새 signed 결과 게시·현재 조회 수용 뒤 전체 등록 계산의 누적 prefix 비용을 측정하고,
원 출력/수지/철회 검사를 유지하며 저장/API/3D의 실제 경로를 검증하는 것이다.
그 뒤 수확 제거·생과 환산 → 물/양분·구매 에너지 → Decimal 경제 연결로 진행한다.

두 번째 전체166일 독립 제어 계산, 실제 등록166일 DB/API/브라우저, 실제 재부팅·감독자 SIGKILL,
전체 backend/browser 회귀는 이번 감사에서 실행하지 않았다.
품종·UTC/QC·초기·관리를 승인한 실제 입력은0건, 국내 독립 검증 자료와 실제 작물 Run도0건이다.
G0–G4는 `not_assessed`이며 실제 수확 예측·미래 마진·작물 순위 게시를 보류한다.
전체 등록 경로와 외부 자료 확보 실측 전에는 최종 제품 완료 날짜를 확정하지 않는다.
