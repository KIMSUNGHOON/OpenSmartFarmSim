# 검증 계산 결과 웹 SDK — 로컬 수용

2026-10-07 KST. [웹·3D 계약](../contracts/web-crop-cycle-calculation-replay-v1.md)의 SDK 자식만 수용했다.
[고정 영수증](artifacts/web-crop-cycle-calculation-client-reference-20261007.json)에 실제 native Codex CLI
`gpt-6.1-sol / xhigh`·재귀 CLI0회·명령/종료/source/로그 SHA와 사설 임시 정리를 보존한다.
새 화면/브라우저·3D, 전체166일 농장 경로·hosted·품종/관문은 별도다.

## 변경과 검토

[새 SDK](../web/src/calculationCycleCropReplay.ts)는 verified result ID·새 공개 schema/engine/artifact ref와
원 source/manifest·두 input_validation 객체를 그대로 보존한다.
reference의8개/manifest의7개 검증 필드,15개 입력 증거 dependency와 read-context/runtime-role SHA를 검사한다.
두 검증 객체의 대응과 원 validation code/입력 evidence dependency의 세 code SHA도 대사한다.
원 context와 validated context의 의미를 대체하거나 새 필드를 삭제해 원 응답으로 바꾸지 않는다.
이 SDK는 서버의 HMAC·원 manifest digest 재계산·현재 농장 권리 판단을 대체하지 않는다.

[공통 API](../web/src/api.ts)는 import/factory spread 두 줄만 추가했다.
기존 startup sample/coupled event/UTC validator와 현재 Bearer·AbortSignal·30초/2MiB transport를 재사용한다.
요청·참조·페이지/끝·확인 과거·수지와 취소/늦은 응답·권리 실패를 검사하고, 한 번에 한 요청만 진행한다.
iterator는 소비자가 진행할 때만 다음 page를 읽으며 원 sample/event 배열을 모으지 않는다.
정확성·가독성·구조·보안·비용을 검토했고 원 SDK/장면·backend·잠금 **101 source SHA는 전후 같다**.
프레임워크·서비스·계수·기존 SDK/페이지·CI/HTTP 한도 변경은 없다.

## 공개 fixture의 범위

[고정 공개 JSON](../web/e2e/calculation-cycle-crop-recorded-responses.json)은 소유 수치 artifact를
현재 실제 공개 projection으로 만든34개 JSON 항목·640,855bytes다.
SHA-256은 `a2d3e197b352bc51ab1dd66f520f38912032bb9a9e705733eb89919e47f4a80b`다.
원 [계산 projection 시험 helper](../backend/tests/test_api_crop_cycle_calculation_replay.py)와
[25시간 program](crop-cycle-stream-execution-reference.py)을 사용했으며 원량/UTC/manifest·순차/빈 마지막 page를 대사했다.
source provenance는 그 helper의 소유 합성 custody metadata다. 실제 DB/TLS wire/history나 실제 농장 자료가 아니다.

| 실제 계산 사례 | 걸음 | 시점 / 사건 |
| --- | ---: | ---: |
| 25시간 완료 | 11,400 | 27 / 5 |
| 짧은 관리 사건 완료 | 120 | 3 / 3 |
| 확인 과거 event hold | 60 | 1 / 1 |
| 빈 hold | 0 | 0 / 0 |
| 소수 초 진단 hold | 0 | 1 / 0 |
| 출력0 완료 | 120 | 0 / 0 |

여섯 사례를 준비한 뒤 parser/context/QC/RHS를 금지한 projection에서 원 배열/UTC를 확인했다.
fixture는 tenant/권리·checkpoint/키·private 경로를 포함하지 않고 제품 번들에서 import하지 않는다.
최초 exporter는 소유 case 부모 디렉터리 미생성으로 종료1이었다. 해당 디렉터리만 마련한 별도 exporter가
116.57초/종료0·FD4→4·원101 source/임시 tree 정리를 통과했다. 실패 이력도 보존했다.
형식용513개 byte-short page·최대 count/시간 변형은 소프트웨어 형식 시험이며 실제 작기 계산으로 보고하지 않는다.

## 실제 검증

| 실행 | 결과 |
| --- | --- |
| SDK 없는 상태의 RED | module import 실패·시험 실행0·종료1 |
| 구현 뒤 같은 원량/provenance 사례 | 1통과/174건너뜀 |
| 첫 집중 시험 | 175통과/1.36초 |
| 원 code/evidence 대응 누락 반례 | 1실패/2통과/175건너뜀 |
| 대응 보완 뒤 같은 반례 | 3통과/175건너뜀 |
| 최종 새 SDK 집중 | **178통과/1.31초** |
| 웹 전체 | **700통과/13.55초** |
| typecheck / build | 종료0 / 종료0 |

전체700개에 새178개와 원522개가 포함된다. 반복 RED/GREEN·집중 시험을 더해 고유 수를 부풀리지 않는다.
최종 집중/전체/typecheck/build의 SDK4 core SHA는 같다. 계약 수용 절은 시험 뒤 추가했다.
기존 공통 API가 새 factory를 import하므로 웹 전체로 원 소비자의 호환을 확인했다.
실제 새 GET/PG/브라우저/WebGL은 이번 SDK 단계에서0회다.
nice19·Vitest `--maxWorkers=1 --no-file-parallelism`으로 파일을 순차 실행했다.
전체 시험 주 프로세스의 표본 최대 RSS345,239,552bytes는 worker 합산/WSL 전체 peak가 아니다.
각 소유 임시 tree를 제거했다. 빌드는 큰 chunk 경고를 냈고 한도/분할 설정은 바꾸지 않았다.

10월8일 제출 전 원101 source와 최종4 core SHA·네 검증 로그 SHA·종료0/임시 정리를 다시 대사했다.
변경 문서10개의 상대 경로1,428개가 존재하고 `git diff --check`를 통과했다.
57개 anchor 표기의 대상 절까지 검사한 것은 아니다. 이미 종료한 시험을 다시 실행하지 않았다.

## 다음 한 단계와 보류

다음 [현재 범위 helper2 core파일](../contracts/web-crop-cycle-calculation-window-v1.md)은 원 `open`을 유지하며
새 typed source/`openCalculation`을 연결한다. 같은 원 ID/reference/validation·sample 인덱스/UTC,
64/8 범위·취소/권리/늦은 응답·단일 요청/settlement를 확인한 뒤 이 자식만 수용한다.
그 뒤 기존 연구 화면의 명시 판본 선택/현재 범위 3D → 실제 PG/TLS/WebGL을 검증한다.
남은 작은 웹 연결은 helper/화면2–4 + native3–5, **5–9집중시간 잠정**이다.
CI·전체166일 등록 prefix/복원 비용·생과/자원/Decimal 경제·자료 확보/최종 날짜는 포함하지 않는다.

SDK 수용 기록 시점의 remote `353bffb` Backend는4분할 성공/4·5진행이며 원 CI 취소·rerun/push는 하지 않았다.
C0/웹/작성 PG 성공, 앱 설정 필드 거부에 대한 로컬 수정과 이번 변경의 hosted 수용은 남아 있다.
10월8일00:04 KST의 같은 run 조회에서는 Backend5분할 성공/분할5 진행을 확인했다.
전체 CI 종료 전 push를 보류한다. 기존 수용 영수증의 당시 CI 관측은 덮어쓰지 않는다.
실제 품종 입력·국내 독립 검증 자료·측정 농장 작물 Run0건, G0–G4 `not_assessed`다.
생산 예측·미래 마진·작물 순위와 공개 운영·최종 완료일은 필요한 독립 증거 전 보류한다.
