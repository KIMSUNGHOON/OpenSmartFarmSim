# 분리 API·환기 작업자 소프트웨어 수용 — 2026-10-13

[선행 저장·권한 분리](crop-model-namespace-20261013.md)에 이어 **새 API 접수→독립 자동 계산→저장/조회**를 로컬 수용했다. [기계 증거](artifacts/crop-isolated-ventilation-runtime-20261013.json)에 실제 도구 종료·로그/소스 해시·자원 기록을 담았다. 합성 시험의 소유 일시 조립이며 새 사용자 모델 배포·전체 제품/G1 수용은 아니다.

## 구현과 판단

- [별도 operator](crop-isolated-ventilation-operator.py)는 새 schema/NOLOGIN owner/네 로그인/authority DSN과 자체 artifact·custody·legacy 영역을 결속한다. 원 runtime/operator bytes와 현재 인증 기록을 고정하며 기존 설정·토큰·서명 키·입력 증거를 바꾸지 않는다.
- 원 API/공동 작업자는 원 frozen source에서 계속 실행한다. 새 영역은 현재 source를 사용하며 공동 모델 flag/factory를 비활성화했다. 새 계정의 공동 결과 표 SELECT도 실제 거부했다. 필요한 작기 binding의 typed factory만 유지하고 기존 입력 계산 resolver는 제공하지 않는다.
- 공식 설치/외래키 순서로 26개 표를 그대로 복제하고, 시장 원천 85건은 새 authority의 기존 adopt_job으로 별도 접수했다. 과거 admitted_by를 재작성하지 않는다. 자체 artifact 영역에는 원 bytes를 복사하고 신규 custody에서 새 study/revision의 요청을 계산했다. 모든 복제 기록이 새 계정에서 사용 가능하다는 뜻은 아니다.
- [재현 진입점](crop-model-namespace-probe.py)의 `--exercise-runtime --original-access`가 [실제 API/작업자 시험](crop-isolated-ventilation-runtime-probe.py)을 실행한다. `--runtime-cases`로 작은 사례를 선택하고 `--check-runtime-rights`로 별도 권리 철회/복원을 검사한다. 경로·인증·원천 파일은 비공개 디렉터리에서만 전달한다.
- 현재 native Codex CLI의 실제 turn_context에서 **gpt-6.1-sol / xhigh**를 확인했다. 재귀 CLI 호출은 0이다. 이 문서는 해당 세션의 설계 판단 출력이며 계산/게시 관문의 승인 자료를 대신하지 않는다.

## 통과한 검증

| 실제 실행 | 관측 결과 | 자원/종료 |
| --- | --- | --- |
| 원76131 — 기동 | 실제 Bearer HTTPS·독립 unpaused chunk8 작업자·분리된 저장 영역. | 17.350초, 합625,504,256bytes, 실제0 |
| 원44543 — 세 계산 | 새 요청 정상/보류/실행 중 취소 모두 attempt1. 정상9시점/3사건·보류8시점/2사건을 원 저장/HTTPS bytes·UTC와 대사. 취소 결과0. 실제 HTTP query9건과 직접 query의22 계산/쓰기 감시 모두0. | 592.047초, 단일149,663,744/합818,229,248bytes, 실제0 |
| 원63469 — 최종 경계 | 보류 재실행·진행/결과 조회/신규 접수의 권리 철회422 세 건·복원200. 읽을 수 있는26표 모든 행 불변. 기존 입력3건/저장9시점 HTTPS·950파일/모든 원 행·키/권리/토큰과 원 API/작업자 보존. | 326.103초, 단일150,757,376/합795,926,528bytes, 실제0 |
| 원62388 — 현재 두 화면 | 새 기록의 실제 HTTP/DOM·15초 재조회·320/390/768/1024/1440px·오류/API 쓰기/인증 전송0. | 35.601초, 합784,359,424bytes, 실제0 |

실제 SCRAM 로그인4·양방향 영역 접근 거부20·DDL/owner 거부8과 두 정책 감사를 확인했다. 원 ACL/행을 보존했고 시험 schema/다섯 역할/passfile과 소유 프로세스 잔여는0이다. 보호 root4·원 source2,148항목과 두 서비스를 유지했다. 감독기는 .25초 간격으로512MiB/PID·필수 기존 서비스를 포함한 합1GiB를 검사했다. 한도를 올리거나 기존 소비자를 중단하지 않았다.

최종 보류 사례의 실제 HTTP query8건은 계산·쓰기0이다. API는 고정 Uvicorn이 graceful shutdown 뒤 SIGTERM을 다시 전달하여 **-15**, 작업자는 **0**으로 종료했다. 두 종료 모두 pidfd를 사용했고 강제 kill은 없었다. 세 사례 배치와 추가 권리 배치는 서로 다른 시험 영역/요청이며 동일 operator와 제품 API/worker 코드를 사용했다. 최종 같은 배치의 브라우저3D 수용은 후속이다.

## 실패/수정 기록

- 원61592(2.222초/실제1): 공동 모델이 비활성인 새 authority에 기존 공동 표를 읽으려던 시험 가정을 수정했다. 접근 거부를 유지한다.
- 원74177/89194/76941/37500은 실제1이었다. 과거 원 runtime 해시/인증 유효시간과 무인증 readiness 가정을 찾아 **새** 설정에서 현재 원 bytes/인증을 명시했다. 원 설정·proof는 보존했다. 첫 preflight에서 남은 소유 credential 복사본1개를 제거하고 이후 생성/정리 범위를 수정했다.
- 원51582(292.960초/실제1): 권리 검증 뒤 API의 native SIGTERM 종료를0으로 기대한 시험 오류다. 설치된 Uvicorn capture_signals 구현을 확인해 실제[worker0, API-15]를 검사하도록 고쳤다. 최종 원63469에서 권리·종료·정리를 다시 통과했다. 실패 실행을 성공으로 세지 않는다.

## 사용자가 확인할 산출물과 다음 한 단계

현재 `http://localhost:5173/`와 `http://localhost:5174/#crop-execution`의 개발 현황을 갱신했다.
[5173 실제 화면](artifacts/crop-isolated-ventilation-progress-20261013-5173.png)과 [5174 실제 화면](artifacts/crop-isolated-ventilation-progress-20261013-5174.png)을 남겼다. 새 환기 모델은 아직 미배포다. 시험 API/작업자는 정리됐으며 기존 두 사용자 서비스를 유지했다.

**다음: 같은 모델별 조립 판본의 계산 중→저장 결과3D 재수용.**

1. 현재 operator/API/worker source와 각 모델의 DSN·접수/권리 기록을 고정한 검증 배치를 만들고, 모델별 HTTP 경로를 연결한다.
2. unpaused 정상/보류/취소의 확정 prefix와 terminal을 실제 Chromium/WebGL에서 같은 원 수치·UTC·표/장면과 대조한다. 재접속/권리 철회 시 장면 제거·복원과 기존 저장9시점도 확인한다.
3. 기존 필수 서비스·추가 API/worker·브라우저 전체를 포함한 같은 시각 자원과 원본/정리를 통과한 뒤 사용자 적용을 평가한다. 임의 애니메이션이나 다른 배치의 과거3D 증거를 수용 근거로 삼지 않는다.

관측 검사 시간은 남은 구현 시간 추정이 아니다. 이전2–4시간 추정은 계속 철회 상태이고 완료 시각은 미정이다. 실제 한 품종/한 작기 입력·독립 농장/시장 자료와 권리는 미확보다. PAR/CO₂/시설 유량→물·양분/구매 에너지→생산량/Decimal 경제·시장/거시→최종 UI·전체 경로가 남는다. 이번 변경의 전체 CI는 미실행이다. 실제 농장 Run0·G0–G4 not_assessed·생산/미래 마진/추천 보류를 유지한다.

자동 goal은 기존 usageLimited 상태다. 새 활성화를 주장하지 않으며 사용자의 “순서대로 시작/계속” 지시에 따라 수동으로 이 단계를 진행했다.
