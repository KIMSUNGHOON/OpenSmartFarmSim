# 연결 수명 통합 뒤 원 독립 정상 — 2026-10-19 KST

상태: **로컬 통합58 수용 유지, 독립 원64 정상 미완료**.
[로컬 통합](registration-connection-lifetime-integration-20261019.md) ·
[원 CI39249166964](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/39249166964) ·
[기계 증거](artifacts/registration-connection-lifetime-native-normal-20261019.json).

source `f403b546ec1cc4d6b3f061b60e0fe74a052d634d`는 본체52/관련58을 통과한 application
`c08d564`와 같다. 고정 PostgreSQL16.15/잠금 판본 설치 뒤 원 계측 OFF64를 실행했다.
원 API/worker body·입력64/chunk1·조회/retry360/RSS와 수식/현재 권한 검사를 변경하지 않았다.

## 실제 종료

원 부모의 `time.monotonic()+360` 조건 단언에서 종료했다. hosted guard382.004874초,
child1·자원 중단 사유 없음이다. 단일128,868,352/합368,951,296bytes·FD7→7,
소유 비좀비/임시0을 확인했다. 이것은 hosted 자원 관측이며 WSL5root 용량/G4 증거가 아니다.

API와 worker는 정리 과정에서 각각-15로 종료했다. 원 actor SHA는
API `ab5a93aed402874bb85f723f272feafd64a44b257f6351256fc84b01b4769cba`,
worker `14fe24de5cf95f3f43a955b0e5c042a39d802d3dc3e67c89f6458b33448fade6`다.
정상 완료·API/client/worker proof와 DB 역할/schema 정리 proof는 없다.
기록된 actor exception 목록이 비었다는 사실을 전체 무오류로 해석하지 않는다.
실제 HTTP 응답 status/code도 이번 계측 OFF 자료에서는 확인하지 못했다.

## 종료 뒤 저장 metadata

두 actor가 끝난 뒤 같은 소유 test cluster에서 Read Only/Repeatable Read로 읽은 metadata다.
원천·현재 권리·모델/결과를 다시 검증하거나 정상 완료를 수용한 자료가 아니다.

| 관측 | 값 |
| --- | --- |
| 상태 / attempt | simulating / 1 |
| 저장 steps / planned | 33 / 64 |
| 저장 status / publication sequence | yielded / 34 |
| computed through UTC | 2026-10-01T00:01:06.123456Z |
| checkpoint 기록 시각 | 2026-10-19T12:12:41.828693Z |
| 종료 뒤 관측 시각 | 2026-10-19T12:12:49.860087Z |

이33/64를 사용자에게 승인된 생산/자원/경제 예측이나 완료된 계산으로 게시하지 않는다.
이전 다른 source의24/64와 직접 비교해 일반 처리량 개선 비율을 산출하지 않는다.
같은 조건의 본체 paired19.81%/21.30% 관측과 로컬58의 수용 범위는 유지한다.

artifact12184778914/3,291bytes의 actual run/head/name과 ZIP digest·안전 경로/개수/크기를 검증했다.
SHA256은 `c1cfc4f7c29a8a70a1b3a02b4891a46cf06c84972a0681aa0a75deaa2347d6a3`이며,
허용된 resource/failure/actor-diagnostics/failure-checkpoint-diagnostics 네 파일만 있었다.
개인 farm 입력·DSN·인증값을 공개하지 않았다.

## 다음 한 단계

[기존 단계 진단 계약](../contracts/crop-solar-worker-progress-diagnostics-v1.md)의 `phases`를
같은 source에서1회 실행했다. [진단 CI39250605987](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/39250605987)는
접수 뒤 실제 `Solar worker progress diagnostic (no acceptance)` job의 in_progress/PG 빌드를 확인했다.
원 actor body/입력64/chunk1/조회·retry360/RSS를 유지하며, 이 진단 자체는 정상/처리량 수용이 아니다.

실제 current/등록/확정/advance 호출·시간과 원 반환 checkpoint/UTC·예외/종료·정리를 대사해
다음 최소 수정 범위를 정한다. 중첩된 포함 시간은 합산하지 않는다.
같은 정상 실행의 반복이나 상한/청크/권한 검사 변경으로 수용하지 않는다.
진단 결과 확인 뒤 변경 근거와 관련 회귀를 확보한 source에서 원 계측 OFF64를 별도로 통과해야 한다.

독립 hold/실제 HTTP 취소/계산 중 WebGL·WSL 사용자 적용·새 Solar 배포·실제 자료 권리와
독립 현장/미래/대응 비교·G0–G4는 미완료다. 실제 농장 Run0·전체 완료일 미정·goal active를 유지한다.

8966:0에서 원 run/head/네 파일/ZIP digest·metadata33/64의 한정 범위와 로컬58 유지,
원 actor/header·로컬 링크2,380개를 대사했다. 두 UI는 HTTP200·동일 no-store JSON,
원 HTML/환기2,173파일·5root·FD4→4·소유 프로세스/PG/임시/passfile0이었다.
게시 guard1.363206초·합 RSS898,834,432bytes이며 UI code/DOM/WebGL은 변경·재검사하지 않았다.
이후 진단 job이 같은 head에서 실제 실행 구간 in_progress로 진입한 것을 확인했다.
