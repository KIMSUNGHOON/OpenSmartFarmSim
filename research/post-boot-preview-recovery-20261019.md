# WSL 재기동 뒤 기존 UI 복구 — 2026-10-19 KST

[기계 증거](artifacts/post-boot-preview-recovery-20261019.json).
재개 시 boot ID가 바뀌었고 기존5root 모두 실제 프로세스가 없었으며 인증도 만료됐다.
기존 불변 원본2,148항목을 먼저 대사하고 legacy→joint→환기 순으로 복원했다.
수식·원 모델·자료·토큰은 보존하고 인증 시각/TLS와 실행 경로를 갱신했다. 새 Solar 배포가 아니다.

| 실제 검사 | 도구 | guard 초 | 합 RSS 최고 bytes |
| --- | --- | ---: | ---: |
| 기존 생장/수확·권한8응답 |65384:0|51.545|918,827,008|
| joint 원 입력3/저장9시점·HTTPS/SCRAM |73912:0|28.689|957,353,984|
| 환기 정상/보류8응답·HTTPS/UI proxy |79208:0|45.056|885,567,488|

legacy의47,809생장시점·47,813수확행과 기존 DB counts를 유지했다. 이미 저장된 합성 자료다.
joint의 원 값/UTC를 대사했으며 관측 시각만 다르다. 환기8응답은 원 bytes와 같다.
조회 계산/쓰기 후크0·동일 bearer·검증 TLS·FD/원본/frozen source·현재5root·
512MiB/PID/합1GiB·감독FD4→4와 시험 소유 비좀비/PG/임시/passfile0을 확인했다.
서비스와 서비스 PG는 계속 실행 중이다. 복구 동안 작업 트리2,429파일도 그대로였다.

joint 시작 감독은 이전 boot의 postmaster PID를 관찰하다 FileNotFoundError로 종료됐다.
새 API/작업자/PG는 실제로 살아 있음을 boot/start/PID·부모·binary/data 경로로 검증해 재시작 없이 유지했다.
현재 보호 root는 legacy 감독/PG, joint API(그 작업자·NGINX 자식 포함)/PG, 환기 감독이다.
현재 resource 감독에 이 실제 가지를 모두 포함한다. **독립 joint 감독 복구/G4 수용은 남아 있다.**
이 초기 실패를 숨기거나 서비스 중단으로 메모리 검사를 통과시키지 않았다.

사용자 경로는 `http://localhost:5173/`, `http://localhost:5174/#ventilation-execution`이다.
사설 안내는 legacy `run-v28/service/OPEN-UI.private.txt`, 환기
`20261013-ventilation-user-activation/user-service-v3/OPEN-UI-ISOLATED-20261019.private.txt`다.
공통/환기 인증 종료는2026-10-19T23:01:39.008992Z이며 다음 갱신 준비는22:01UTC 이전이다.
토큰은 게시하지 않는다. 현재 browser DOM/WebGL·새 계산·전체 회귀는 재검사하지 않았다.

복구 직후의 다음은 중단 전 후보인 요청 내 등록 조회의 변경/권한/수명 회귀 검사였다.
그 시점 후보는 미커밋이었고 이전 happy-path1검사만 통과한 상태였다. 후속 수용은 별도 기록한다.
원 독립 Solar16/64 미완료·계산 중3D·실제 농장
자료/권리/독립 검증·G0–G4와 전체 완료일 보류를 유지한다. goal은 active다.
판단은 기록된 native `gpt-6.1-sol/xhigh` 세션에서 수행했고 CLI를 재귀 실행하지 않았다.
