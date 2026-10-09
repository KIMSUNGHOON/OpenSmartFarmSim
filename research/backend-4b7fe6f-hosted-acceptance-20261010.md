# 4b7fe6f의 hosted 회귀 수용 — 2026-10-10

정확한 commit `4b7fe6f058266e7032a97bd4064b28307db65fcf`의
[Backend37941890045](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/37941890045)는
2026-10-09T16:28:19Z(10월10일01:28:19 KST) `completed/success`로 종료했다.
native CLI `gpt-6.1-sol / xhigh`, [현재 turn-context와 재귀0](crop-climate-joint-boundary-implementation-20261010.md#실제-cli와-선행-근거)의 개발 검토다.
도구 `2a1da2`/`ca528c`의 실제 상태와 각 job 원 로그를 대사했다.
[기계 판독 영수증](artifacts/backend-4b7fe6f-hosted-acceptance-20261010.json)의 SHA-256은
`cea6f21dd40f5757d2ea1763626789a23c6489938f60dcbda1819e265e13e8a0`이다.

| 분할 / job | 통과 | 제외 | 결과 |
| --- | ---: | ---: | --- |
| 0 / 113858090124 | 1,052 | 5,016 | success |
| 1 / 113858090174 | 859 | 5,209 | success; Pydantic serializer 경고2 |
| 2 / 113858089908 | 865 | 5,203 | success |
| 3 / 113858090002 | 1,382 | 4,686 | success |
| 4 / 113858090032 | 939 | 5,129 | success |
| 5 / 113858090171 | 971 | 5,097 | success |

고유 **6,068개**를 분할했고 각 통과+제외는 같은6,068개다. 제외는 해당 분할 외 선택이며 skip으로 수용한 것이 아니다.
집계 job113917875470도 실제 success이고 여섯 complete inventory가 모두
`1376176733de7ed89ddf291461e79ed9bff3df8c7473be34d632dee52dbbfee5`로 같다는 원 출력이 있다.
분할0의 별도 UID service smoke4개와 content DAC도 성공했다. 가짜 CLI/시험 key의 소프트웨어 경로다.

같은 head의 [Web37941890018](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/37941890018),
[AuthoredPG37941890169](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/37941890169),
[runtime37941889972](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/37941889972),
[Compose37941889932](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/37941889932)도 success다.
현재 조회에서 같은 commit5개 workflow가 모두 completed/success였다.

`gh run view --log`의 이번 반환은 분할5와 집계만 포함했다. 이것을 전체 원 로그라고 사용하지 않았다.
여섯 job의 직접 logs API 응답을 각각 보존·해시하고 각 pytest 최종 통과/제외를 대사했다.
첫 파서는 분할1의 경고2 필드를 허용하지 않아 실패했고, 원 bytes를 보존한 채 경고 필드를 구분해 읽었다.
시험/CI를 재실행하거나 원 실패를 가리지 않았다.

## 수용 범위와 고정

선행 [pidfd 두 배포본](owned-research-pidfd-compatibility-20261009.md),
[실제 tracker/같은 controller 시험 격리](owned-research-shared-controller-20261009.md),
[endpoint 포트 표현 대사](crop-harvest-ci-endpoint-binding-20261009.md)의 로컬 증거와 이 hosted 회귀를 결합했다.
해당 pidfd/시험 격리·endpoint 부모의 대기를 해제한다. 원 source/AST·pidfd/FD·권리/서명 검사를 줄이지 않았다.
구형 role 정리의 교착 원인/수정은 이 성공만으로 입증하지 않았으므로 그 조사 항목은 미완료다.
운영 기반 완료 범위는 기존 `d19f7c0` 고정과 위 결함 수정이다. 새 기반 확장은 하지 않는다.

이번 성공은 **4b7fe6f까지**다. 뒤의 ec18ea6 이후 작물·기후 변경은 별도 hosted 회귀가 필요하다.
원 실행의 실제 종료를 확인했으므로 대기 중인 후속 commit을 한 번 push할 수 있다.
새 원 CI handle이 생기면 이를 유지하며 관측 timeout이나 후속 로컬 작업만으로 취소/재시작하지 않는다.
실제 제품 CLI·독립 검토/해제·품종/농장 자료·G0–G4, 실시간 U3나 production 수용은 아니다.
