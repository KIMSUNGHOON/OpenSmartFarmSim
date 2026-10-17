# 독립 일사 계산의 대기 부모 시험 — 2026-10-17

[기계 기록](artifacts/crop-solar-unpaused-parent-resource-20261017.json) ·
[원 경계/수용](../contracts/crop-solar-unpaused-probe-parent-v1.md).

## 실제 관측

원 API/worker 생성 원문과 환경을 보존한 사설 시험기를 구현했다. 두 actor의 원 hash는
[이전 시도](crop-solar-current-unpaused-resource-20261017.md)와 같다.
고정 프로그램을 만든 뒤 Python 대기 부모를 Bash로 exec하고, 준비/접수 대기→원 독립 worker→
원 후검사/DB 정리를 실행한다. 원64걸음·chunk1·조회 주기·수식/권리/검증·worker unpaused를 유지했다.

환경은 봉인한 익명 memfd로만 전달하고 actor exec 전에 추가 FD를 닫는다.
프로그램 hash·PID/boot/start·소유 디렉터리 dev/inode를 검사하며 원 identity/pidfd 감독은 그대로다.
환경/키/접속 문자열이나 actor 원 로그를 공개하지 않았다. 제품이나 공개 prototype에 채택하지 않았다.

| 최고 합 표본의 주체 | RSS bytes |
| --- | ---: |
| 시험 대기 부모 Bash |3,538,944|
| configured API |117,608,448|
| 독립 worker |83,189,760|
| 자원 감독 |28,213,248|

이전 다른 시도의 최고 합 표본에서는 대기 Python22,401,024bytes였다.
이 두 관측은 이후 합 RSS 감소량이나 상한을 보장하지 않는다.
이번 실제 정상 시험은 **30.995744초·합1,096,474,624bytes RSS 중단·실행기 종료1**이다.
정상 완료 proof가 없으므로 **정상 실행·S3·부모 시험 수용은 미완료**다.
소유 PG 연결 프로세스들도 합 표본에 포함했으며, 현재 자료로 각 연결의 호출 주체/수명을 확정하지 않는다.
중단 이후 worker/후검사 단언은 그대로 남겼고 독립 수치 결함의 증거로 승격하지 않았다.

원2,148항목·현재 source/기존 자산·두 UI·원5root/동적 자식·한도를 보존했다.
FD4→4·소유 비좀비/PG/임시 PG/passfile0이며 자체 후정리도 PG 정지/소유 디렉터리 제거를 확인했다.
권리 승인False·실제 농장 Run0·G0–G4 미평가다.

## 시험기 자체 검증

초기 사전 검사3회는 실패로 보존했다. 실패 actor에 대해 아직 기다리지 않은 API 상태255와
이미 종료한 API 상태0을 혼동한 시험 oracle, EXIT trap에서 후검사 실패 코드가 가려질 수 있는
흐름을 확인했다. 정상 경로는 후검사로 직접 exec하게 수정했다.
통제된 실패 actor와 살아 있는 API의 검사는 별도 합성 지연으로 안정화했다.
이는 실제 worker의 pacing이나 입력을 바꾸지 않는다.

최종 사전 검사 `25378:0`은 정상 actor0/0·worker 실패7의 거부·실제 통제 환경 일치·
봉인 메모리 쓰기 거부·원 후검사 AST 연속 보존·Python/Bash 구문을 통과했다.
실제 정상 계산 `23047:1`의 RSS 실패와 구분한다.

## 다음 단계

같은 조건의 로컬 실행을 반복하지 않는다.
[호스팅 정상 기능 검사](../contracts/crop-solar-unpaused-hosted-v1.md)를 명시 수동 job으로 구현했다.
기존 웹/native 저장3D job 단계 보존·YAML/Python 구문과 실제 자식 종료7 거부/FD/소유 정리는
`47184:0`으로 확인했다. 첫 검사는 backend 가상환경의 PyYAML 부재로 실패했으며 의존성 추가 없이
시스템 Python의 기존 YAML 도구로 분리 검사했다.

[CI39027776829](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/39027776829)의
원 source는 `abd11834f12da7a530d82ad481db1a26e0a0edd3`다. 실제 실패로 종료했고 수용하지 않았다.
자식1/감독1·129.660855초·단일133,337,088/합367,562,752bytes·자원 중단 사유 없음이다.
FD7→7·소유 비좀비/임시 항목0이며 정상/DB 정리 proof는 없다.
artifact12099795312/658bytes의 ZIP digest·run/head·경로를 대사했다.
이 증거만으로 원 시험 내부의 실패 위치는 알 수 없다.

원 API/worker·계산 조건을 바꾸지 않고 후정리 전에 예외 종류·코드 위치/종료 코드·proof 존재만
수집하는 진단을 추가했다. 원 메시지/환경/로그는 게시하지 않으며 통제된 비밀 문자열 제거와
원 workflow 단계/원 prototype 보존·실제 종료7 거부를 `14413:0`으로 확인했다.
이 사전 검사의 첫 실패는 비교 기준을 바뀐 HEAD로 잡은 검사 오류였으며 고정1fc56d4 기준으로 수정했다.
[진단 CI39028201921](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/39028201921)는
`00772f68dbb5039db652c1ded9d9b9acfe135620`에서 실패했다. 91.909초·합357,433,344bytes·FD7→7·
소유/임시0이며 worker 완료 상태 단언(원 worker114행)에서 실패한 것을 확인했다. 정상 proof는 없다.
원 정상64걸음·두 전진 prefix/원 값/UTC·원 후검사·DB/자원 정리를 모두 통과해야 기능 한 사례를 수용한다.
이 선택은 웹 회귀를 실행하지 않으며, 기존 웹/저장3D 성공 기록은 해당 원 판본의 증거로 유지한다.

로컬 동시 용량·hold/취소·계산 중3D·S2/S3/S4 부모·새 Solar 배포와 외부 실측/권리는 남아 있다.
호스팅 기능과 로컬 연결 수명/주체의 계측을 분리해 진행한다. 실제 계측 없이 pool/dispatcher/모델을
재설계하지 않는다. 전체 goal active·전체 완료일 미정을 유지한다.
판단은 현재 native Codex `gpt-6.1-sol/xhigh` 문맥에서 수행했고 재귀 CLI를 실행하지 않았다.

## 잡힌 예외·제한 재시도와 다음 보류

명시 선택한 [진단 CI39028662821](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/39028662821),
source51cb971은 worker 모듈의 exception trace에서 `SolarCustodyPending`을 확인했다.
호출은 worker `run_once:139`→custody `advance:301`→`_open:294`다.
50.176초·합359,915,520bytes·FD7→7·소유/임시0이며 실패로 남겼다.
진단 header는 actor 원문을 바꾸므로 정상 수용으로 계산하지 않는다.
기존 worker는 이 일시 잠금 충돌에서 즉시 transient 시도를 종료했다.

[작업자 제한 재시도](../contracts/crop-solar-worker-custody-contention-v1.md)를 source63baae8에 구현했다.
첫 pending 이후5초의 재시도 시작 예산·최대50ms의 실제 충돌 대기만 허용한다.
각 재시도 전에 현재 입력/권리·취소/임대를 검사·갱신하고, 소진/다른 오류는 원 정책대로 전파한다.
잠금/거래를 기다리는 동안 보유하지 않으며 수식·물리 시간·입력·청크/API 조회 주기를 바꾸지 않았다.
이 변경은 앞선 대기 부모 시험과 별도이며 그 사설 부모를 채택하지 않았다.

원3491:1에서 새 helper/time 부재로5개 setup이 실패했고, 구현 후43348:0에서5개를 통과했다.
권리 검사 중 예산 소진 회귀를 추가한 **23759:0의 집중6개**가 통과했다.
일시/영구 충돌·취소/철회·다른 오류·예산 소진 뒤 추가 호출 금지를 검사했다.
원5root/원본/두 UI·FD4→4·소유/PG/임시/passfile0과 합931,528,704bytes를 확인했다.
이 검사는 통제된 시계이며 실제 종단 간 성공을 대신하지 않는다.

예외 관찰을 끈 [원 정상 CI39029133073](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/39029133073)은
source63baae84d7f1d4bec3e66f2a35e1f75106a2d936에서 **실패**했다.
원64걸음/start1/CLI0·attempt1·두 전진 prefix·원 값/UTC·후검사 조건을 그대로 유지했다.
379.784237초·자식/감독1·단일135,462,912/합371,167,232bytes·자원 중단 없음,
원 계산360초 상한에서 부모가 종료했고 API/worker는 각각-15로 정리됐다.
FD7→7·소유/임시0이며 정상/DB 정리 proof가 없다. 완료 걸음 수나 성공을 추정하지 않는다.
네 호스팅 archive 모두 실제 run/head·artifact digest·안전한 경로를 대사했다.

따라서 **제한 재시도 집중 검사만 통과했으며, 정상 실행/S3는 계속 미수용**이다.
다음은 [확정 단계·구간별 실제 시간 계측](../contracts/crop-solar-worker-progress-diagnostics-v1.md)이다.
시간/자원 상한이나 원64걸음/판정을 바꾸지 않고 병목 근거를 확보한다.
새 source는 사용자 서비스에 적용하지 않았다. 전체 CI/hold/취소/실행 중3D·외부 관문은 별도다.

마지막 개발 기록은 `2026-10-17T11:43:54.474272Z`에 게시했다.
47829:0에서 두 HTTP200/no-store/원문 일치·기존 HTML/환기2,173파일·원5root/원2,148항목·
FD4→4·소유 정리를 확인했다. 현재 browser DOM/WebGL·전체 회귀는 재실행하지 않았다.
