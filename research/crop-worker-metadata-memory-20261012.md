# 작업자 metadata 로딩과 동시 3D 메모리 — 2026-10-12

## 변경과 계측

현재 native Codex CLI `gpt-6.1-sol` / `xhigh`에서 판단했다. 재귀 CLI 호출은0이다.
API를 만들지 않는 metadata 경로가 작물 공개 DTO를 통해 FastAPI를 불러오는 것을 import 추적으로 확인했다.
네 작물 조회 모듈의 `Path/Query/Request/Response` import를 실제 라우트 설치 함수로 옮겼다.
같은 cold import/load의 RSS는84,299,776→78,884,864bytes로5,414,912bytes 감소했다.
넓은 runtime import 이동의 추가 이득은 약0.55MB여서 해당 실험은 되돌렸다.
계산식·매개변수·공개 스키마·TLS/현재 권리 검사는 변경하지 않았다.

로컬 preview harness에 명시적 `--shared-buffers-mib 4|8|16` 선택을 추가했다. 기본16은 유지한다.
현재 후보는 실제 `SHOW`로4MB/연결32/work1MB/maintenance16MB를 확인했다.
native 시험용 DB도 선택한 예산을 `SHOW`로 확인하며, 환경변수가 없으면 종전 설정을 유지한다.
PostgreSQL은 이 값을 시작 시 정하며 작은 값은 성능을 낮출 수 있다
([공식 PostgreSQL 16 자원 설정](https://www.postgresql.org/docs/16/runtime-config-resource.html)).
4MB는 이번 소유 로컬 배치의 계측값이며 production 권장값으로 채택하지 않았다.

## 집중 검사

| 검증 | 실제 도구 종료 | 통과 | wall 초 | 합산 최고 RSS bytes |
| --- | --- | --- | --- | --- |
| 초기 생장 OpenAPI·SCRAM·HTTPS·권리/재계산0 |15802:0|3|48.260|453,300,224|
| 공동 생장 같은 검사 |67534:0|3|117.221|1,036,718,080|
| 작기 시작 같은 검사 |73677:0|3|143.309|1,060,548,608|
| 작기 경로·OpenAPI·fresh import·실제 TLS 재기동/철회 |86401:0|42|124.436|455,028,736|

합계51검사다. native 시험 DB 예산은16MB이며 실제 host SCRAM/TLS를 사용했다.
각 종료에서 source/원본2,148항목·기존5173과 자산·보호 roots, FD 반환·자식/PG/passfile 잔류0을 확인했다.
전체 CI는 실행하지 않았다.

네 모듈을 한 프로세스에 누적한 시도21847/74267/96703은 각각 RSS_limit로 미수용이다.
마지막 시도는93개 검사 뒤 startup HTTPS에서 실패했고 합1,079,103,488bytes였다.
그 부분 통과를 위51개 수용 수에 더하지 않는다. 모델별 집중 검사에는 같은 HTTPS·권한·원 수치 검사를 유지했다.

## 저장 재생과 남은 수용

같은 frozen source의 API·두 unpaused worker와 기존5173을 함께 기동했다.
두 worker는 chunk8이며 사용자 원 토큰·구5키/신3키·입력/검토를 유지한다.
같은 소유 감독기18733의 profile-v1은 실제 브라우저 종료0/권리 복원/자식 잔류0이다.
최고 합1,009,172,480bytes, 여유64,569,344bytes, 단일 PID322,686,976bytes였다.
0.25초 샘플링의512MiB/PID·합1GiB 한도를 유지했다.

원93463 종료0의 postflight에서 실제 HTTPS wire와 저장9시점의 원 값·UTC/geometry,
재접속·현재 권리 차단/복원, 조회 계산/쓰기0, 기존27표 행의 완전 일치·856파일 보존을 확인했다.
필수 두 worker는 생존/idle이며 해당 재생 동안 worker 로그도 그대로다.

## 동일 판본의 계산 중 3D

| 실제 브라우저 | 계산 중 원 시점 | terminal | wall 초 | 합산 최고 RSS bytes |
| --- | --- | --- | --- | --- |
| 정상 |6개의 서로 다른 원 UTC|완료9시점·재접속/권리|439.840|1,052,463,104|
| 보류 |6개의 원 시점|같은 원 hold 결과·재접속/권리|419.591|1,008,648,192|
| 취소 |1개의 원 시점|취소 수락→worker canceled·장면 제거·결과0|125.506|912,293,888|

모두 같은 감독기/API/두 unpaused worker/기존5173을 유지했고 브라우저 실제 종료0이다.
각 원11544/41184/67868 종료0의 postflight로 wire/DB/원 UTC·geometry·조회 계산/쓰기0을 대사했다.
정상 최고 합은1,004MiB이며1GiB 한도 여유는21,278,720bytes다. 이 좁은 여유를 production 용량 수용으로 쓰지 않는다.
원18733 감독기도 사용자 적용 보류 뒤 요청 종료0/FD4→4·owned/PG/passfile 잔류0을 확인했다.
소유 서비스의 API/두 worker 종료0과 PG fast stop을 별도로 기록했다.

## 기존 입력 증거와 판본 호환 보류

최종 활성화 전 기존 공동 계산의 원 결과 조회가 `JointInputEvidenceHold`로 거부됐다.
원74372/45903 검사는 실제1이며 새 모델 사용자 적용 성공으로 세지 않는다.
후속 원76886 종료0 진단에서 등록된 기존 입력3건의 version/issuer/key/code/schema/QC는 같고
`file_metadata` 의존성만 다름을 확인했다. 원10651은 시험 helper 경로 누락으로 실패했고 수정 후 진단했다.

기존 proof는 `operator_config.py` SHA d38a57ee…에 묶여 있다. 환기 저장의 명시 flag를 추가한 현재 판본은
cdc53b32…이다. 이번 네 API import 수정이 이 파일을 바꾼 것은 아니다.
서명된 입력을 현재 판본으로 읽을 때 검증기가 이를 차단하는 동작을 유지한다.
과거 증거 재작성·키 변경·해시 비교 우회는0이다. 다음 작업은 불변 요청 identity에 따른 명시 판본 조립과
기존9시점/새 환기 결과를 함께 읽는 실제 SCRAM/HTTPS·권리/재계산0·합1GiB 수용이다.

## 복구와 보존

기존5173 run-v21은 계속 유지했다. 새 후보와 임시 안내 서버를 실제0으로 종료하고,
원30704 종료0으로 새 SELECT/INSERT 권한을 회수해 원 policy를 복원했다. 결과표·모든 행은 유지했다.
기존5174는 원 frozen source의 serve-v24(소유 도구45406, 실행 중)로 복구했다.
원38302 종료0에서 기존 작업의 HTTPS/SCRAM 요약·원9시점 bytes/UTC와 현재 저장 값을 대사했고
조회 계산/쓰기0을 확인했다. 요약의 현재 관측 시각만 서로 다르며 유효한 UTC로 검증했다.

원94206/94347은 새 배치 종료 후 모든27표/950파일 보존과 활성 policy를 확인했다.
복구 뒤 원57704 종료0에서 원 policy·새 권한 회수·최종 모든 행/950파일의 완전 일치를 다시 확인했다.
기존89작업·생장47,809시점/수확47,813행/5사건·같은 두 토큰·구5/신3키·입력/검토/권리는 그대로다.
정상/hold/cancel은 각각attempt1·결과1/1/0이며 수용한 새 계산 결과도 삭제하지 않았다.
원 serve-v23의 이전 중단은 실제143이며 새 후보의 정상0과 구분해 보관한다.

[기계 증거](artifacts/crop-worker-metadata-memory-20261012.json)는 비공개 원문에서 공개 가능한 검증 결과만 추렸다.
개인 농장 자료·토큰·키·원 CLI 로그·원 요청/결과 식별자는 포함하지 않는다.

## CI·남은 작업

현재 변경의 전체 CI는 실행하지 않았다.10월12일 `gh run list`로 확인한 최신 원격 판본은10월9일 f06fb67이다.
[Backend](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/37995386543),
[API smoke](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/37995386531),
[application runtime](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/37995386528),
[Compose](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/37995386493)는 failure,
[Web](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/37995386488)은 success다.
이는 현재 source의 CI 통과를 뜻하지 않는다. 운영 기반 범위를 늘리지 않고 계산 연결의 집중 검사만 수행했다.

새 모델 사용자 적용은 보류다. 기존2–4시간 추정은 철회했고 v1 진행 기록에는 철회를 명시했다.
숫자 추정의 구조적 미정/판단 시각/사유 UI는 아직 후속이며 이 한계를 숨기지 않는다.
판본 호환→같은 판본 정상/hold/cancel 재수용→사용자 적용 순서를 따른다.
그 뒤 PAR/CO₂·물/양분/구매 에너지→생산량/Decimal 경제→최종 UI다.
실제 품종/독립 농장/시장 자료 확보는 병행하며 실제 농장 Run0·G0–G4 미평가·전체 제품 완료일 미정을 유지한다.

## 사용자가 확인하는 산출물

[실제 계산 중 원 수치3D 모식도](artifacts/crop-worker-metadata-running-3d-20261012.png)는 새 후보 검증 장면이다.
현재 사용자5174에 새 환기 모델을 배포했다는 뜻이 아니다.
원26077 종료0으로 복구한 두 화면의 최신5단계/HTTP no-store·무인증·실제15초 두 번째 조회·390px/오류0·API 쓰기0을 확인했다.
[5173 진행 패널](artifacts/crop-worker-metadata-progress-20261012-5173.png)과
[5174 진행 패널](artifacts/crop-worker-metadata-progress-20261012-5174.png)에 판본 호환 보류와 기존 예상 철회를 게시했다.
진행 JSON SHA와 원자 게시/handoff SHA가 같고 두 실제 계산 서비스는 실행 중이다.
현재 접속은 [web 안내](../web/README.md#joint-execution-user-preview)의run-v21/serve-v24다.
