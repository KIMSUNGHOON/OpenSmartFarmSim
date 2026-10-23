# Leaf 입력 확인·접수 범위 검증 — 2026-10-23

상태: **소프트웨어160검사·새 frozen 판본의 기존 결과/입력 확인 HTTPS 수용, 사용자 적용 전**.
[계약](../contracts/leaf-admission-registration-scope-v1.md),
[기계 증거](artifacts/leaf-admission-registration-scope-20261023.json)와
[기존 저장 job의 실제3D](leaf-population-query-registration-scope-20261023.md)를 함께 확인한다.

## 변경과 근거

기존 첫 POST는30초를 넘겼다. [원 접수 한 번의 비용 관측](artifacts/leaf-admission-cost-observation-20261023.json)은
등록 재구성64회·SQL33,022회와 profiler가 있는 서버 작업38.854초/queued를 기록했다.
클라이언트는 원30초에 종료했고 재요청하지 않았다. 계측 시간을 정상 성능 수용으로 세지 않는다.
첫 private 진단의 pytest 파일명 수집 오류는 HTTP/DB fixture 시작 전에 종료했고 이름만 수정했다.

HTTP 접수 callback과 owned 입력 확인 callback에서 기존 농장 등록 읽기 범위를 사용한다.
실제 작업 thread 안에서 검증된 원 요청/config의 farm 참조와 서버 tenant를 같은 기존 farm graph에 전달한다.
이전 scope가 있으면 helper가 actor/ref·문맥을 검증하며 다른 범위로 우회하지 않는다.
원 submit·prepare/current·resolver·권한/원천/서명·멱등성/commit_guard와 응답 후 인증을 보존했다.
등록 재구성만 요청 내 재사용하며 현재 등록64회·원천4,864회는 그대로다.

수치 모델·worker·서명 authority·query는 바꾸지 않았다. 접수 core 지문은
`9a2132f2309ee73f5b272baf01d25c280944b2f4845f7058f1af4ff1c0a8632b` 그대로다.
기존 intent/result를 새 코드에 맞춰 다시 쓰거나 키를 바꾸지 않는다. 새 라이브러리는 없다.

## 통과한 범위

| 범위 | 고유 검사 | 확인 |
| --- | ---: | --- |
| HTTP/owned 제어 | 57 | 신규6과 기존51, Scope·body·오류·전송/문맥 정리·선택적 구성 |
| 실제 SCRAM/검증 TLS 신규 | 2 | 첫/retry의 각1재구성·4,864원천, 동일 job/원 input·새1행/이벤트1·생장/worker/CLI0, 늦은 커밋 롤백 |
| 기존 실제 HTTP | 3 | 신규/동일202·409·worker 완료12frame/52면적·권리/취소·늦은 만료/원본/parent 철회 |
| 실제 실행 파일 | 3 | 자동 소비1계산/attempt1·같은 DB/키 cold restart/POST0, 파일 철회/취소/기본 모드·SIGTERM/SIGINT |
| OpenAPI/Scope | 95 | 원 경로/스키마·operation/Scope·기본 비활성·공개 계약 지문 |
| 합계 | **160** | 반복 실행과 진단은 합산하지 않음 |

신규 실제 HTTPS 첫202는13.323초, 동일 retry는13.419초였고 같은 원 job/input bytes를 반환했다.
각 요청의 witness/소유 연결은 별개이며 종료 뒤 닫혔다. current source trace76개를64회 모두 대사했다.
커밋 검증 직전의 실제 원천 bytes/초과 UPDATE 권한/인증 만료는422/422/401로 거부됐다.
각 원복 뒤25표 전체 행 SHA가 같았고 새 job/events는 롤백됐다.
원 작업의 정상 GET/retry와 원 입력/파일 보존을 재확인했다. 새 불변 binding의 미게시 준비는 구분한다.

별도 실제 실행 파일의 입력 확인200은13.533초, 접수202는13.638초였다.
실제 consumer가 완료 attempt1·원12frame/52면적을 게시했고 같은 DB/키 재시작 뒤 같은 최초 시각/결과를 읽었다.
재시작 중 새 POST는0이다. 이 시험을 사용자 환경에서의 동시 retry나 전체 자동 UI 수용으로 대신하지 않는다.

## 새 판본과 남은 단계

새 frozen snapshot은 기존 query 판본의820파일 중 HTTP/owned callback 두 소스만 다르다.
기존 실제 저장 작업을 별도 실제 SCRAM/검증 TLS로 읽고 원 result/parent/root/최초 시각·12frame/52면적을 대사했다.
입력 확인의 request도 원 config와 같다.7개 기존 응답+입력 확인의8응답, POST0이며 정상 요청은13.243–13.614초다.
원25표 SHA `586fa1a1fe090e84997ab2a9b93ae059d618bdd52aa7f8f3f232193a48203797`와 서명 파일66개를 보존했다.

모든 단계에서 원3root·감시2,481항목과 소스를 보존했다. 소유 잔류0·감독 FD4→4,
PID 최대182,538,240bytes·합산 최대651,300,864bytes를 확인했다.
512MiB/PID·합1GiB·600초/로그4MiB와 HTTP30초/2MiB를 유지했다.
전체 backend/새 hosted CI/새 사용자 browser는 아직 실행하지 않았다. 웹 코드는 바꾸지 않았다.
판단은 현재 native CLI gpt-6.1-sol/xhigh의 turn_context 기록이며 재귀 CLI0이다.

다음은 같은 원 DB/키·원 결과를 보존한 새 판본 적용→실제 worker 계산 중 동일 POST30초/같은 job·attempt1→
현재 SDK의 입력 확인/한 접수/자동 저장3D·메뉴/reload/실제 권리 제거/원복이다.
이 사용자 적용/동시 요청/새 자동 UI가 통과하기 전 부모 runtime 체크를 완료하지 않는다.
실제 품종/독립 작기0·생산/자원/경제·자율 선정·R2/첫 cold 경고·G0–G4와 전체 완료일은 미완료/미정이다.
