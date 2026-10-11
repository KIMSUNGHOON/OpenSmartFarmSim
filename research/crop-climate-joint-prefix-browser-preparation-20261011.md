# 계산 중 3D의 실제 브라우저 연결 준비 — 2026-10-11

상태: **P6a/P6b 미수용·사용자 prefix 미활성화**.
[기계 기록](artifacts/crop-climate-joint-prefix-browser-preparation-reference-20261011.json)의 SHA-256은
`40fc598bc5d39a050fa2a117dca2912f2944fb2c2cd4d7cf4a49ca7d43d9f93f`다.
현재 native Codex CLI의 실제 `gpt-6.1-sol`/`xhigh` turn context를 확인·기록했다. 재귀 CLI 실행은0이다.

## 사용자가 보는 화면과 백엔드의 관계

| 주소 | 현재 연결 범위 | 계산 중 성장3D |
| --- | --- | --- |
| localhost:5173 | 완료된 합성166일의 저장 생장·수확 결과를 실제 API에서 조회/재생 | 없음 |
| localhost:5174 | 같은 DB에 접수한 지정 작업의 상태·확정 checkpoint 자동 조회, 종료 후 저장 결과3D | 아직 비활성 |
| 분리된 개발·검증 서버 | 해당 시험의 별도 저장소·작업 | 사용자 화면에 자동 노출되지 않음 |

5174의 자동 조회는 응답 완료 뒤10초를 기다리는 polling이다. 모든 개발 계산을 한 화면으로 중계하는 기능이 아니다.
P5의 부분 결과 화면 코드는 로컬 수용됐지만 사용자5174의 frozen 빌드에는 아직 적용하지 않았다.
두 사용자 HTTP 주소가200을 반환하고 현재 보호 프로세스가 살아 있음을 다시 확인했다.
접속 방법은 [web README](../web/README.md#joint-execution-user-preview)를 따른다.

## 관측한 자원 제약

두 사용자 서비스를 유지하고 추가 prefix API/Chromium에서 기존 완료 결과만 읽는 profile을 실행했다.
새 계산 접수는0이며 실제 running prefix 시험이 아니다.
기준 합산 RSS578,494,464bytes에서 최고1,105,895,424bytes로 증가해1GiB 상한에서 시험 프로세스를 종료했다.
단일 최고273,575,936bytes, 실제 자식 exit1, wall4.4864초다. 브라우저 통과로 세지 않는다.
원본2,148항목·두 frozen source/자산·보호 프로세스와 FD4→4를 보존했고 소유 프로세스/PG/passfile 잔여는0이다.

[계획](../tasks/plan.md#joint-prefix-view-20261010)에5173 유지→5174 활성 계산 확인/정상 종료→같은 영속 DB/키의 별도 후보 검증→수용 후 활성화 또는 원 서버 복구를 추가했다.
**이 기록 시점에는 유지보수를 시작하지 않았고5174도 계속 실행 중이다.**

## 이번에 준비한 코드와 확인 범위

- `crop-climate-joint-live-preview.py`: 명시적 `--enable-prefix`에서만 prefix 판본/API를 선택한다. 원 private factory를 보존하고 새 이름의 같은 저장소 factory를 사용한다.
- `crop-climate-joint-live-operator.py`: 검증된 worker 생성자에 명시한 chunk budget을 전달한다. 기본값16을 유지하며 시험 후보는8을 선택할 수 있다. 별도의 정지 장벽·계산 지연·농업 계수 변경은 없다.
- 두 reference 파일: 실제 제품 App/Playwright core/HTTPS와 원 응답을 대사하는 완료 결과 resource profile이다. running prefix 검증으로 확장하는 작업이 남아 있다.

Python3파일 AST·JavaScript 구문·CLI 도움말의 두 옵션과, prefix 옵션 없는 사용자 지정 budget의 **파일 변경 전 거부**를 확인했다.
검사 자식 exit0, 단일/합산 최고 RSS136,769,536/687,132,672bytes, FD4→4였다.
원본2,148항목과 두 사용자 source/자산·프로세스 보존, 소유 프로세스/PG/passfile 정리를 확인했다.
새 runtime 기동·실제 prefix 응답·실제 running WebGL은 **이번 검사를 통해 수용하지 않았다**. 기존 P5 시험 수도 늘리지 않는다.

## 다음 수용과 일정

다음은 P6a의 실제 unpaused 자동 worker와 제품 브라우저에서 samples/events200을 관측하는 일이다.
동일한 원 UTC·LAI·50구획 C/N·온도를 표/차트/WebGL과 terminal 저장 결과에 대사하고 정상/hold/cancel·현재 권리/재접속을 확인해야 한다.
특히 P4에서 event-prefix200을 관측하지 못한 항목은 남겨 둔다.
메모리 상한 안에서5173과 원본을 보존하고5174를 최종 복구하거나 수용된 후보로 활성화해야 한다.

유지보수·복구 검증0.5–1시간을 기존 P6a1–2시간/P6b0.5–1시간에 더해 **남은2–4집중시간**을 잠정 범위로 둔다.
실제 event 응답/자원 관측 뒤 재산정하며 완료 날짜를 확정하지 않는다. 전체 U3·실제 작기·독립 농장 자료의 일정과 별개다.
G0–G4 `not_assessed`, 실제 생산·미래 마진·추천 hold와 remote 작업0을 유지한다.
