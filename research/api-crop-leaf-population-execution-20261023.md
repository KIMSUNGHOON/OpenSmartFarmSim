# 새 잎 계산 보호 HTTP 검증 — 2026-10-23

범위는 자체 합성 입력의 소프트웨어 검증이다. [계약](../contracts/api-crop-leaf-population-execution-v1.md)과
[기계 증거](artifacts/api-crop-leaf-population-execution-20261023.json)를 함께 확인한다.
현재 Codex CLI의 실제 모델은 **gpt-6.1-sol / xhigh**이며 기록한 turn_context 지문과 재귀 실행0을 증거에 보관했다.

## 구현과 수용

표준 create_app에 선택적 leaf service/query와 보호6경로를 추가했다.
접수·상태·manifest·frame·replay·취소는 같은 jobs/provider와 farm/완료 parent graph를 요구한다.
기본 비활성503, 부분/다른 graph 거부, 기존 인증/현재 Scope·tenant와 입력 검증을 유지한다.
입력은 필수 parent job/result/root 참조를 포함하며 비밀·원 자료·임의 경로를 받지 않는다.
응답은 no-store/2MiB, per_tracked_shoot·unvalidated_for_registered_crop와 합성 연구 표시를 유지한다.

| 확인 범위 | 통과한 고유 검사 | 확인한 내용 |
| --- | ---: | --- |
| HTTP/ASGI 제어 | 39 | 닫힌 요청/응답, 권한·상한·오류, 동일 객체 조립, 전송 실패/연결 종료의 인증 문맥 정리 |
| OpenAPI/Scope | 95 | 기존 계약 불변, 새6경로·operation ID/권한, 공개 schema 연결 |
| 실제 PostgreSQL SCRAM·검증 TLS | 3 | 접수/멱등·409/worker/현재 원 결과, 권리 철회 후 취소·만료, 늦은 원본/parent 검토 철회 |
| **합계** | **137** | 앞선 반복 실행·실패는 합산하지 않음 |

OpenAPI는 **74경로/78연산/488스키마 → 80경로/84연산/492스키마**다.
기존74경로와488스키마의 객체 값이 모두 같음을 대사했다. 앞선 consumer의4개 source 지문도 그대로다.

실제 HTTPS에서 인증 없는401, 신규202, 같은 요청의 같은 job, 변경409와 실제 worker 완료를 확인했다.
완료 replay의 **12시점/52면적 원 bytes·UTC/ID**, frame11·manifest·결과/parent root와 최초 계산 시각을 대사했다.
현재 자료 권리 철회에는422, 철회 후 취소에는200과 결과 미게시를 확인했다.
읽기 뒤 인증 만료는401, resolver 원본 변경과 parent 검토 철회는 각각422였다.
조회의48생장·CLI 진입은 모두0이며 정상/늦은 변경 시험에서25표 전체 행 SHA가 전후 같았다.

소유 시험의 전체 요청 시간을 실제 측정했고 모두 기존30초 안이었다.
최장 요청은 접수 **28.758496초**, replay **26.891894초/67,660bytes**였다.
이는 이 시험의 단일 요청 증거이며 공통 U1 용량·동시 사용자 지연·G4 수용이 아니다.
현재성 검사를 생략하거나 timeout을 늘리지 않았다.

## 실패와 자원 보존

첫 미등록 RED와, 완료 parent의 SQL 상태를 바꾸려다 terminal 불변 trigger에 막힌 시험을 보존했다.
후자는 유효한 변경 시나리오가 아니므로 현재 parent 검토 철회로 시험을 수정했다.
제품 코드/DB guard를 바꾸지 않고 실제 철회 거부를 최종 통과했다.

각 단계에서 repo source를 동결하고 .25초 표본으로 PID512MiB/보호+소유 합1GiB·600초를 감시했다.
최대 PID RSS **187,023,360bytes**, 합산 **498,040,832bytes**였다.
기존2root와2,148원 항목·관련 artifact/배포 파일을 포함한2,469감시 항목을 보존했다.
실패 단계까지 소유 PG/schema/role/temp/passfile·프로세스 잔여0, controller FD4→4를 확인했다.
Windows Chrome 메모리를 WSL 용량 증거에 포함하지 않았다.

전체 backend suite·이번 hosted CI·브라우저 검증·사용자 runtime 배포는 실행하지 않았다.
기존 [5176 화면](http://localhost:5176/leaf-population-replay.html)은 저장 합성3→6잎 연구 재생이며,
이번 HTTP의 새 job을 표시하는 화면은 아직 아니다.

## 다음 단계와 외부 의존성

다음은 기존 보호 runtime의 leaf resolver/현재 검토·권리·서명 authority/service/query와 정확 consumer 조립이다.
실제 사용자 HTTP 접수→자동 계산→같은 저장 결과 조회·취소/철회와 기존25표 원 행 보존을 먼저 수용한다.
기존 farm의 판단 시각은 새 leaf 자료 가용 시각보다 이르므로 원 job에 소급 부착하지 않는다.
별도 더 늦은 판단의 retrospective 합성 farm과 그 farm의 실제 완료 parent를 사용하고 원 농장/결과를 보존한다.
이후 strict SDK→같은 job의 기존 사실적 잎3D·UTC/표/그래프, 메뉴/reload 복원·철회 제거를 검증한다.
구체적 분해/수용과 낮은 신뢰 작업량은 [현재 계획](../tasks/plan.md#leaf-보호-http-수용과-runtime-연결--2026-10-23)에 기록했다.

실제 Axiany 계수/초기관측·독립 현장 작기0, 실제 승인 farm Run0을 유지한다.
전체 작기/생산·자원/경제/자율 선정·최종 사실감 R2/첫 셰이더 경고와 G0–G4는 후속이며 전체 완료일은 미정이다.
