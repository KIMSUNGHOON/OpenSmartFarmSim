# 임대 갱신 중 원 페이지 조회 — 2026-10-11

**P6a2a의 제한된 소프트웨어 검증을 수용했다. 계산 중 WebGL/P6a·사용자 활성화/P6b는 미수용이다.**
[기계 증거](artifacts/crop-climate-joint-prefix-lease-guard-reference-20261011.json)의 SHA-256은
`f246a37005e4424264db0f8edfb0094f68f3a221bb10a1e47ac779e4ed16141b`다.
판단은 실제 native Codex CLI `gpt-6.1-sol`/`xhigh`의2026-10-11T04:22:14.601Z context에서 수행했다. 재귀 CLI는0이다.
선행 [P6a1 분류](crop-climate-joint-prefix-page-diagnosis-20261011.md)와 [설계](../contracts/crop-climate-joint-prefix-progress-guard-v1.md)를 따른다.

## 변경

제품 core는 [reader](../backend/app/crop_climate_joint_prefix.py)와 [HTTP 후검사](../backend/app/api_crop_climate_joint_prefix_routes.py)2파일이다.
내부 reader 판본은 `joint-crop-climate-prefix-read-v3`다. 공개 DTO·writer·수치·입력 증거·기존 결과 형식은 변경하지 않았다.
같은 simulating 작업의 실제 token/input/attempt와 나머지 모든 row 필드·bundle을 고정하고,
유효한 `lease_until`/`updated_at`의 UTC 단조 전진만 구분한다. 새 컬럼도 비교 대상이다.
조회 응답의 job은 마지막 DB probe에서 검증한 실제 row이며 observed_at도 그 probe의 실제 시각이다.

reader가 만든 비공개 witness는 query/tenant/job·전체 bundle·원 payload hash를 결속한다.
HTTP는 직렬화 뒤 이를 재검사하고 원 응답을 그대로 반환한다. witness/실제 lease token은 payload·header·오류·repr에 넣지 않는다.
현재 입력/권리·계정·서명 검사를 생략하지 않았다. 최신 수용 이력과 HEAD가 전후에 바뀌면 기존 Pending 처리를 유지한다.

## 실제 검증

최종 **같은2 core SHA**에서 고유245개를 통과했다. public collection과 앞선 중복 실행은 더하지 않았다.

| 범위 | 통과 | 근거 |
| --- | ---: | --- |
| HTTP/row/witness |156 |실제 SCRAM/TLS의 갱신 후 원 wire·누락/오조립·외부 취소·늦은 권리·종료, timestamp 역행/비공개 필드/미래 컬럼·UTC offset/fold 거부 |
| reader의 독립 heartbeat |1 |실제 별도 프로세스의 renew·두 timestamp 증가, 같은 selector/원 페이지 canonical bytes와 hash·UTC·조회 계산/쓰기0 |
| 공개 투영/명시 runtime 계약 |85 |기존 값/단위·binary64 거부·closed schema·새 기본 연결 없음·기본 비활성 |
| 별도 자동 작업자 |3 |실제 정상/hold/cancel·pause0·원 terminal wire/작업자 취소 확인·현재 prefix 닫힘·조회 계산/쓰기0 |

자동 작업자3개는 기존 실제 runtime 검사의 함수와 fixture를 호출하는 별도 reference다.
정상은 API 스레드 예외를 추적했고 작업자에는 tracing을 적용하지 않았다. 실제 브라우저 검사는 아니다.
정상 accepted summary1회 뒤 samples503, hold accepted summary3회를 관측했다. 원 terminal 응답과 process exit0은 확인했다.
정상 trace에는 DB bundle·final HEAD·HTTP 후검사의 Pending이 남았고422는 재현되지 않았다.
request별 내부 예외 정렬을 기록하지 않아 그 samples503의 단일 원인을 사후 단정하지 않는다.

UTC 보완 전 reader의 기존12개도 분할 통과했다. 이는 다른 core SHA의 회귀로 따로 보존하며 최종245개에 더하지 않는다.
최종2 core에서 기존 reader12개 전체를 다시 실행하지 않았다. 최종 native heartbeat와 전체 HTTP·투영·runtime 범위를 구분했다.

## 실패와 자원 범위

기존 v2의 실제 독립 heartbeat red는 reader Pending과 HTTP503으로 각각 재현했다.
초기 collection fixture 불일치와 시험의 UTC/+09:00 문자열 비교 오류를 수정했다.
후자는 실패 확인 후 identity-verified 소유 pytest만 SIGINT로 종료했고 사용자 서비스에는 신호를 보내지 않았다.
같은 tzinfo의 fold가 바뀌면 Python datetime 비교가 UTC 역행을 놓치는 unit red도 재현해 UTC 비교를 보완했다.
이 fold 사례는 실제 DB에서 관측한 장애가 아니다.

기본 scratch PG의 첫 unpaused 정상 실행은 **미수용**이다. guard 합산 RSS1,085,059,072bytes로1GiB를 넘었고,
로그에는 prefix422도 있었다. 신호/오류의 순서와 내부 원인은 기록하지 않았으므로 그422의 원인·해결을 주장하지 않는다.
상한을 올리지 않고 별도 소유 scratch PostgreSQL16.15만 `shared_buffers=16MB`, `max_connections=32`,
`work_mem=1MB`, `maintenance_work_mem=16MB`로 제한해 실제 설정을 기록했다. 사용자/제품 PG 설정은 변경하지 않았다.
이 환경의 정상/hold/cancel은 실제 exit0이었다. 기본 설정/운영 용량의 수용으로 확장하지 않는다.

최종245개 묶음의 관측 최고 RSS는 단일190,107,648/사용자 서비스를 포함한 합산1,041,739,776bytes였다.
모든 수용 실행은 .25초 표본·512MiB/1GiB 상한 안이다. 원본2,148항목·두 frozen source/자산·보호 root4를 보존했다.
FD4→4·소유 프로세스/PG/passfile 잔여0·실제 종료를 확인했다. 사용자 DB에 검증 작업을 접수하지 않았다.

[공개 reference](crop-climate-joint-prefix-lease-guard-reference.py)는 마지막 private 파일에서 ROOT 산출1곳만 바꿨다.
정상 실행의 원 source는 두 후속 test 정의를 추가하기 전 판본이며 fixture/정상 함수는 동일하다. 각각의 SHA를 보존했다.
공개 파일은 실제 collection3개/exit0만 확인했다. **공개 파일 자체의 native 실행은 재실행하지 않았다.**
원래의 권한·SCRAM·TLS·schema와 수치 코드는 유지했고 API mock/가짜 frame은0이다.

## 다음 단계와 사용자 확인

다음은 **P6a2b 필요 확인**이다. 최종 v3의 같은 accepted selector events/samples 조회를 request별 DB/HEAD/예외와 정렬해
정상 forward progress가 어디서 표시를 막는지 확인한다. 최초 기본 설정422는 미확정 기록으로 유지한다.
필요한 변경은 선택한 불변 판본·현재 서명 계보·DB 수용 사건을 전후에 증명하는 작은 별도 자식으로 설계한다.
현재 권리 검사를 줄이거나 worker를 늦추지 않는다. 실제 WebGL/normal·hold·cancel/재접속과 사용자 기동은 이후 P6에서 수용한다.

첫 정렬 진단0.5–1집중시간 잠정이다. 수정 범위/완료 날짜는 그 근거 뒤 산정하며,
전체 P6 재검증0.5–1.5시간·P6b0.5–1시간은 성공 관측 뒤의 잠정 범위다. 앞선 단기 완료 날짜를 확정하지 않는다.
두 화면은 중지/변경하지 않았다.5173은 완료166일 저장 재생,5174는 상태 자동 조회/종료 후3D를 유지한다.
[접속 안내](../web/README.md#joint-execution-user-preview)를 따른다.
전체 작기·자원/경제·최종 UI/독립 현장 자료 일정은 별도다. 실제 crop Run0/독립 자료0, G0–G4 `not_assessed`, 생산/미래 마진/추천 hold다.
