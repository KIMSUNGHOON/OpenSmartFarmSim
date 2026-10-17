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
원 source는 `abd11834f12da7a530d82ad481db1a26e0a0edd3`다. 이 문서 작성 시 실행 중이며 수용하지 않았다.
원 정상64걸음·두 전진 prefix/원 값/UTC·원 후검사·DB/자원 정리를 모두 통과해야 기능 한 사례를 수용한다.
이 선택은 웹 회귀를 실행하지 않으며, 기존 웹/저장3D 성공 기록은 해당 원 판본의 증거로 유지한다.

로컬 동시 용량·hold/취소·계산 중3D·S2/S3/S4 부모·새 Solar 배포와 외부 실측/권리는 남아 있다.
호스팅 기능과 로컬 연결 수명/주체의 계측을 분리해 진행한다. 실제 계측 없이 pool/dispatcher/모델을
재설계하지 않는다. 전체 goal active·전체 완료일 미정을 유지한다.
판단은 현재 native Codex `gpt-6.1-sol/xhigh` 문맥에서 수행했고 재귀 CLI를 실행하지 않았다.
