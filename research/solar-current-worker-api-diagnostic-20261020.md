# 현재 원 API·worker 동시 진단 — 2026-10-20 KST

[기계 증거](artifacts/solar-current-worker-api-diagnostic-20261020.json) · [계약](../contracts/crop-solar-worker-progress-diagnostics-v1.md) · [선행 인코딩 검토](solar-current-encoding-boundary-review-20261020.md).

## 같은 실행의 최종 결과

[CI39328214424](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/39328214424) / job118319433913·source `0a06b3913c7444ad0e308e2ed10af64cc473a0d7`는 `completed/failure`다. 기존 `worker-api` header만 선택했고 원 actor 본문/단언·입력64·chunk1·조회/retry360·RSS를 유지했다. 원 계산 step은21:34:32Z–21:40:57Z다. 진단은 정상 수용이 아니며, 원 계측 OFF44/64와 이번 단계 수를 처리량 비율로 비교하지 않는다.

worker가 실제로 반환한 마지막 confirm은 **27/64·yielded·UTC00:00:54.123456Z**다. confirm29진입/28반환·기록된 worker 예외0, 완료한 confirm 누적145.362200초/최대5.800220초였다. before30회·누적31.389100초, custody_call59진입/58반환·누적323.182465초다. 이 시간은 observer 비용과 중첩 confirm을 포함하므로 더하지 않는다. 종료 시 run_once/custody_call/다음 confirm이 열려 있었고 원 terminal/outcome proof는 없다. private advance는 `None`이며 이 모드는 custody advance를 관찰하지 않으므로 last_advanced의null을 실패나 새 진척으로 바꾸지 않는다.

## 실제 HTTP와 관측 한계

관측 응답27건은202 1건·200 20건·503 6건이다. 고정 코드는 prefix_unavailable 1건·execution_unavailable 5건이며 accepted prefix 응답은16건이다. 응답 dropped는0이다. accepted라는 상태만으로 원64·독립 수치/UTC/클라이언트 완료를 수용하지 않는다.

최근 예외16개는 StopIteration/StopAsyncIteration 제어 흐름이고55개가 창 밖으로 제외됐다. 이를 서버 실패나 모든 시점의 예외 부재로 해석하지 않는다. 이 API header에는 요청별 latency/CPU/SQL 시각이 없어 worker와의 정확한 시간 상관이나 API 병목 비중을 확정하지 않는다. 실제 worker 예외 기록이 없는 이번 사례를 과거 Pending 실패와 같은 원인으로 합치지 않는다.

종료 뒤 READ ONLY/REPEATABLE READ로 회수한 저장 metadata도27/64·sequence28·attempt1/simulating·같은 UTC다. 현재 권리·공개 prefix·전체 숫자·정상 완료 proof가 아니다. API/worker 종료는 정리의−15/−15이며 normal/API/client/worker·DB role/schema0 count proof는 없다.

## 무결성·자원

artifact12223162857·16,237bytes·ZIP SHA `9ada3a768d0e7658232becb2c862bba9547ffb150ee024b305a4ba9026281a9b`를 한 번 수신했다. 허용 파일/경로/압축 해제 한도와 run/head/prototype/header·실제 actor SHA를 대사했다. API의 관측 포함 SHA는4c589b25…·worker는d1a1aac5…다. header를 제거하면 원 APIab5a93…/worker14fe24… 본문과 단언이 byte 단위로 복원된다.

hosted guard385.312731초·단일/합 RSS132,669,440/367,112,192bytes·자원 중단 사유null·FD7→7·소유 비좀비/임시 잔여0이다. WSL5root 동시 용량 수용은 아니다. raw artifact는 비공개이며 메시지/locals/접속 정보/응답 원문을 공개 기록에 복사하지 않았다. 최초 actor 해시 생성은 시스템 Python에 psycopg가 없어 import 전에 종료됐고, 잠긴 backend venv로 실행했다. 의존성/제품 변경이나 fixture 실행은 없었다.

실제 native CLI `gpt-6.1-sol` / `xhigh` 문맥과 원행 SHA·source/원 수신/출력 해시를 결속했다. 재귀 CLI/하위 에이전트·새 header/서비스·제품 코드 변경은0이다.

## 후속 후보의 실제 결과

같은 load의 두 traversal 사이에서만 commit 값을 재사용하는 [별도 실제 비용 시험](solar-same-load-two-read-evaluation-20261020.md)을 마쳤다. 원 current15/SQL9,929/role273/원천2,280·원 bytes/counts/UTC와 보존/정리는 같았으나 평균 **1.093551%**, 두 짝1.056565/1.130648%로 사전2% 기준 미달이다. 후보를 미채택하고 app을 유지한다. 1MiB 한도를 높이거나 좋은 timing을 고르는 재실행은 하지 않는다. codec/alias·소유권·오류 closure는 미입증이며 이 시험을 기존82검사에 합산하지 않는다.

다음은 이미 잠긴 pydantic-core decoder를 원 canonical roundtrip·원 parser fallback과 결합할 수 있는지 source/오류 경계를 검토하는 작은 작업이다. 검토만으로 새 parser나 검사 생략을 승인하지 않는다. 원 파일 보안/원문/SHA·duplicate key·숫자·Unicode·원 오류/현재 권리는 유지해야 한다. 해당 전제가 불성립하면 후보를 제외한다.

원 정상64→독립 hold→HTTP취소→계산 중WebGL→WSL 사용자 적용, 실제 농장/자료·G0–G4는 남아 있다. 새 Solar 미배포·실제 농장 Run0·전체 완료일 미정·goal active를 유지한다.

## 사용자 상태 게시

[게시/원본 보존 증거](artifacts/solar-current-worker-api-status-publication-20261020.json): 두5173/5174 상태 feed HTTP200·원 bytes 일치/no-store, frozen HTML/환기2,173/5root/원본2,148·FD4→4·소유 PG/비좀비/임시0을 확인했다. guard2.398255초·합631,590,912bytes다. 상태 데이터만 갱신했으며 browser DOM/WebGL과 전체 회귀는 재실행하지 않았다.
