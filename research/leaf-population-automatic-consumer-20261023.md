# 기존 consumer의 명시 leaf 자동 실행 — 2026-10-23

상태: [leaf 실행 계약](../contracts/crop-leaf-population-execution-v1.md)의 **합성 소프트웨어 수용**.
[E3 현재 조회](crop-leaf-population-execution-query-20261023.md) 다음이며 보호 HTTP/runtime·사용자3D는 후속이다.

기존 foreground loop의 WORKERS에 정확 LeafPopulationExecutionWorker/Outcome·leaf v1을,
기존 discovery의 INPUT_VERSIONS에 leaf-population-execution-input-v1을 명시 등록했다.
생산 코드 변경은 import/worker mapping/discovery 판본의3줄이다. 새 큐·표·역할이나 기본 자동 실행은 추가하지 않는다.
정확 worker와 해당 판본으로 만든 operator factory가 기존 bounded discovery/임대/시도/완료 규약을 사용한다.

## 검증

- **새10/관련 기존23=33 제어 검사:** 구성 시 계산하지 않고 빈/미래/다른/혼합 판본을 거부한다.
  정확한 leaf outcome의 안전한 attempt metadata만 내보내고 다른 계열/작업·unclosed는 거부한다.
  기존 morphology와 generic loop의 cursor/대기/stop·범위/tenant·잘못된 outcome 검사를 통과했다.
- **실제 SCRAM1:** 기존 작업 뒤의 leaf 접수를 discovery로 찾아 실제 producer1회·원자 완료했다.
  원12frame/52면적의 전체 bytes/SHA와 parent·최초 시각/서명 결과를 같은 현재 query로 대사했다.
  다른 queued 모델은 그대로이고 완료 뒤 선택0, 조회/후속 discovery의48생장·CLI 진입0이었다.
  새 두 job과 관련 행을 제외한 **25표 모든 원 행 SHA**와 부모18파일을 보존했다.
- 현재 native 정상223.699초/856표본, 실제 loop 단일139.288초, 완료 뒤 scan50+36행/선택0이었다.
  PID108,843,008bytes/보호+소유 합394,375,168bytes로 .25초·512MiB/합1GiB·600초 안이었다.
  원2root/2,148항목·관련 artifact/배포 파일·소유 schema/role/PG/temp/passfile0과 FD4→4를 확인했다.

먼저 미등록 RED를 확인했다. worker mapping만 추가한 뒤의 제어5실패/28통과와 실제 native 실패는
discovery 허용 판본의 누락이었다. 두 등록점을 맞춘 최종33+1=**34개 고유 검사**를 수용했다.
앞선 실패/정리를 보존하고 통과 수에 더하지 않았다.
코드/로그 SHA·원 frame/행 지문·정확 native gpt-6.1-sol/xhigh와 재귀0은
[기계 증거](artifacts/leaf-population-automatic-consumer-20261023.json)에 기록했다.
기존 E3 source와 생장 모델은 변경하지 않았다. 전체 backend/consumer 회귀·hosted CI·공개 운영 capacity/G4는 미실행이다.

## 다음 단계

다음 [보호 HTTP 계약](../contracts/api-crop-leaf-population-execution-v1.md)은 새6경로/typed 입력·응답,
같은 jobs/farm/parent/provider graph·현재 인증/권리·멱등/취소와 실제 SCRAM/TLS를 수용 기준으로 고정했다.
기존 OpenAPI/Scope 지문을 기록하고 기존 경로를 보존한 뒤 새 경로를 검증한다.
내부26–29초에 대한 실제30초 요청 예산·늦은 만료/전송 검사는 통과 전까지 미수용이다.
API/Scope·OpenAPI 조립60–120분 + 제어/실제 SCRAM·TLS90–180분 + 기록30–60분 =
**3–6집중시간**의 낮은 신뢰 작업량이다. 전송/현재성 비용을 실제 측정한 뒤 갱신한다.
이번 consumer의 이전1.25–2.5h 계획은 실제 수용으로 대체한다. 이후 명시 runtime→strict SDK/같은 job3D를 잇는다.

[사용자 화면](http://localhost:5176/leaf-population-replay.html)은 기존 저장 합성3→6잎 재생이다.
이번 자동 소비는 소유 scratch에서 검증했고 사용자 runtime에 아직 적용하지 않았다.
일반 입력 목록/운영 조립·실제 Axiany 계수/초기관측·독립 현장 작기0, 생산/자원·경제/자율 선정·
최종 사실감/첫 셰이더 경고·G0–G4와 전체 제품 완료 날짜 미정을 유지한다.
