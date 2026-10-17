# 독립 일사 작업자의 종료 사유 관찰 — 2026-10-17

[기계 증거](artifacts/crop-solar-worker-termination-diagnostics-20261017.json) ·
[진단 계약](../contracts/crop-solar-worker-progress-diagnostics-v1.md) ·
[선행 현재 참조 reader](farm-pinned-context-reader-implementation-20261017.md).

## 원 정상의 실제 실패

[trace-OFF CI39034668788](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/39034668788),
source8423263은 **121.021초·자식1**로 실패했다. worker exit1·최종 성공 단언 실패와 API-15만 확인했다.
잡힌 예외·실제 반환 outcome·완료 단계·정상/DB 정리 proof는 없다. 원360초/RSS 상한 종료는 아니다.
단일133,279,744/합369,881,088bytes·FD7→7·소유 비좀비/임시0이다.
artifact12101344383/2,086bytes·run/head/ZIP digest/안전 경로를 대사했다.
이를 정상 기능·전체 성능 개선·WSL 용량·S3/사용자 배포로 표시하지 않는다.

## 변경과 통과 검증

source65a609b는 명시 진단의 `detail=worker`를 추가한다. 기본은 기존 `phases`다.
작업자 메서드만 관찰해 잡힌 예외 종류/코드 위치, 실제 `_confirm`의 확정 단계와
`run_once` 반환의 허용 상태/attempt/고정 reason code를 기록한다.
농장·시장·모델 phase journal을 생략한다. locals/메시지/원 입력/환경을 내보내지 않는다.
기존64KiB/최근32·동시16·예외16·atomic 기록과 진단의 정상 수용 금지를 유지한다.
관찰 비용을 포함하며 trace-OFF 처리량을 추정하지 않는다.

- 97179:1은 시험 source 문자열 오류라 행동 RED가 아니다. 보완한59782:1은 detail 기능이 없어 신규1실패/기존6통과다.
- 17910:0은 실제 queued/busy 반환·원 checkpoint·비밀값 제외와 기존 bounded/실제 SIGTERM·반환 형태의 **7검사**를 통과했다.
- 36579:1은 backend venv의 yaml 미설치다. 의존성을 설치하지 않고 기존 system Python을 쓴98252:0에서
  YAML·기존 web/native 및 원 정상 steps/env 보존·원 prototype/현재 application 불변을 확인했다.
- 새5root·원2,148항목·frozen 소스/자산·두 화면·512MiB/PID/합1GiB,
  감독FD4→4·소유 비좀비/PG/임시/passfile0을 유지했다. 실패 단계도 증거에 보존했다.

## 다음 한 단계

[CI39035225593](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/39035225593),
source65a609b/detail worker는 **262.162초·API1/worker-15**로 실패했다.
실제 마지막 확정은 **8/64·yielded·2026-10-01T00:00:16.123456Z**다.
confirm에서 SolarCustodyPending2개 exception event(전파를 포함한 journal6건)를 확인했다.
하지만 worker 최종 outcome은 없으며, API의 응답 단언이 먼저 실패했다.
원 정상121초의 작업자 실패와 같은 원인으로 합치지 않는다.

단일132,972,544/합371,658,752bytes·FD7→7·소유 비좀비/임시0,
정상/DB 정리 proof 없음이다. artifact12102092295/15,365bytes의 actual run/head/ZIP digest·안전 경로와
worker/header/prototype hash를 대사했다. worker-only 모드는 advance를 관찰하지 않으므로 None을 추정으로 채우지 않는다.

2473:0에서 원 API 전체 source를 재구성해 실제 actor SHA256ab5a93a…와 일치시켰다.
**API line285는 prefix 응답 status∈{200,503}의 단언**이다. 실제 status/오류 코드와 API 예외는 아직 없다.
정상 원 worker SHA25614fe24d…/line114도 성공 사건1·state succeeded·attempt1 단언과 대사했다.
입력/소스·원5root·두 화면/자산·FD/소유/PG/임시/passfile을 보존했다.

## API와 작업자 관찰의 후속

`worker-api` 모드는 원 API 본문 앞에 선택 관찰 header를 넣는다.
실제 request_http의 status·고정 allowlist code·허용 prefix_status·호출 행만 최근32건,
prefix/projection/routes의 실제 서버 스레드 예외 종류·basename/행/함수만 최근16건/각16위치로 기록한다.
HTTP 본문·message·경로/쿼리/ID·locals/입력/환경/인증값은 내보내지 않는다.
스레드 직렬화·64KiB·atomic replace와 진단의 정상 수용 금지를 유지한다.

- 52413:1에서 관찰기 미구현3실패→3835:0에서 HTTP 상태/고정 코드·비밀값 제외·실제 새 스레드 예외·유한 기록3통과다.
- 62582:1에서 새 worker-api 선택1실패/기존10통과를 확인한 뒤77465:0의 **고유11검사**를 통과했다.
- 34453:0에서 YAML·기존 web/native/원 정상 계산 단계·기본False·원 prototype/application 불변,
  원 API 본문 그대로의 header 주입/실제 원 SHA와 AST를 확인했다. artifact 경로1개만 추가했다.
- 기존 원5root/두 UI/소스·자산·2,148원본·512MiB/PID/합1GiB·감독FD4→4·소유/PG/임시/passfile0을 유지했다.

[CI39036105645](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/39036105645),
sourceba87cb8/detail worker-api가 진행 중이다. application8423263과 원 API/worker 본문·입력·64걸음·chunk1·
조회 주기·현재 검사·시간/RSS 상한을 유지한다. 실제 HTTP 오류 코드/검증 위치를 근거로 다음 작은 수정을 정한다.
진단은 정상 수용이 아니며, 수정 후 별도 trace-OFF 원 정상 기준이 필요하다.

[독립 보류·취소 후속](../contracts/crop-solar-unpaused-hold-cancel-v1.md)은 정상→보류→취소→실제 계산 중 WebGL의
개별 수용이다. 기존 저장 결과 조회를 독립 실행 증거로 대체하지 않는다.
S3/S4·WSL 용량·새 Solar 배포·실제 품종/독립 농장 자료·권리/G0–G4와 전체 완료일은 미완료/미정이며 goal active다.

최신8/64·API/worker 관찰 진행 기록은15158:0에서5173/5174 HTTP200·no-store·원 HTML/source·5root/원본·FD/소유 정리를 확인해 게시했다. 브라우저/디자인 재검사는 하지 않았다.
