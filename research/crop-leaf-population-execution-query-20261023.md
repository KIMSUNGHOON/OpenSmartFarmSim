# 잎 작업의 현재 조회와 원자적 DB 스냅샷 — 2026-10-23

상태: [실행 계약 E3](../contracts/crop-leaf-population-execution-v1.md)의 **합성 소프트웨어 수용**.
[E2 worker](crop-leaf-population-execution-worker-20261023.md) 다음이며 자동 consumer·보호 HTTP/runtime·제품3D는 후속이다.

## 구현과 현재성 경계

`LeafPopulationExecutionQuery.read(tenant,job_id,view=...,index=...)`가
status/manifest/frame/replay의 닫힌 응답을 반환한다. 원 job/input/publication/outcome/events와
opaque 참조·worker 코드/시도·시작 출력 수와 실제 완료 증거를 대사한다. 가짜 CLI invocation은 거부한다.
원 result/root/calculated_at·parent job/result/root/계산 시각, farm·program/source/evidence/binding SHA를 유지한다.

완료 조회는 기존 signed authority의 원 `_load`를 전후 호출한다.
그 사이 원 manifest/frame reader와 원 program 결속을 검증하고 같은 payload/binding/packet을 대사한다.
양쪽 현재 farm/자료 권리·검토와 서명 검증을 유지하면서 동일한 전체 public 조회를 중첩 호출하지 않는다.
현재 resolver 원 bytes·닫힌 request/intent HMAC은 양 끝에서 다시 확인한다. 요청 간 권리 cache는 없다.
미완료 status는 현재 입력 결속을 전후 확인하며 결과 참조를 반환하지 않는다.
frame만0이상 정수 index를 받으며 최종 응답은2MiB 이내다.

job/publications/events/outcomes/invocations는 **한 SQL statement의 동일 스냅샷**으로 읽고,
조회 양 끝의 묶음이 다르면 Pending으로 재조회한다. 반영 중인 완료를 확정 결과로 섞지 않는다.
원본/권리·검토 실패는 과거 정상 결과로 대체하지 않는다. 조회는 입력·수치·서명을 새로 만들지 않는다.

## 동시 완료 문제와 수정

첫 구현의 정상·현재/늦은 변경·fresh는 통과했지만 최종 검토에서 분리된5개 SELECT를 확인했다.
실제 worker를 첫 job SELECT 직후 별도 연결로 완료시키자 이전 queued와 새 publication이 섞여
Pending 대신 **hold**가 되는 반례를 재현했다. worker의 succeeded를 별도로 확인하고 실패 로그/정리를 보존했다.

수정은 `_bundle`의 단일 SQL 스냅샷으로 한정했다. 나머지 메서드/모듈의 AST는 같고
기존 생장/서명·E1/E2 source는 변경하지 않았다. 같은 실제 동시 완료 조건에서 Pending을 확인한 뒤
**모든 실제 DB/fresh 검사를 최종 동일 소스로 다시 실행**했다. 앞선 통과/실패를 최종 개수에 합산하지 않는다.

## 통과한 검사

- **집중16:** 게시·시도/시작·완료·종료 사유, opaque 참조/원 input,
  claim/원 binding과 parent job/result/root 불일치, fake CLI·누락/변조를 거부했다.
  처음 새 모듈 부재 RED와 최종 통과를 보존했다.
- **실제 SCRAM 정상1:** queued와 완료의 모든 모드, 첫/마지막 개별 frame·전체 replay,
  원12frame/52면적의 bytes/SHA와 UTC/ID/최초 시각·부모 정보를 대사했다.
- **현재 변경1:** foreign tenant·양쪽 권리/검토·원 packet3종·read scope 거부,
  복원 뒤 같은 원 결과를 확인했다.
- **늦은 변경1:** 마지막12번째 frame 직후 leaf/parent 권리·leaf 검토·resolver source를 바꾼4경우
  전체 응답이 거부됐다. 일부 프레임 응답은 없었다.
- **독립 연결 cancel1:** 두 DB 묶음 조회 사이 실제 cancel이 반영되면 Pending,
  다음 조회에서 실제 canceled/result 없음·cancel_requested False를 확인했다.
- **원자 스냅샷1:** 첫 job statement 직후 실제 worker 완료·서명/DB 게시가 진행돼도
  원 상태와 새 게시를 섞지 않고 Pending으로 끝났다.
- **별도 fresh1:** 실제 SCRAM과 모든4모드·첫/마지막 frame/원12frame SHA,
  같은 result/root/최초 시각·parent와 양쪽 검토 철회를 확인했다.

최종 수용은16+6=**22개 고유 검사**다.
정상/변경 조회의 **48생장/CLI 진입·7작업/artifact 쓰기·지속 SQL쓰기0**과25표 원 행 SHA를 대사했다.
취소/동시 완료 시험의 독립 actor 쓰기는 의도적으로 분리했다.
fresh는 관련 생장/producer/worker import 시도0·파일/작업/프로세스 쓰기13진입0·지속 SQL쓰기0,
FD4→4·원 parent18/leaf44파일 bytes/metadata와 기존 건수4종 보존을 확인했다.
seed/pytest/HTTP app import도0이었다. 모든 scratch schema/role·짧은 임시 디렉터리와 소유 child를 정리했다.
전체 backend 회귀/hosted CI·HTTP/TLS/브라우저는 이번 범위에 없다.

## 시간·자원과 다음 수용

최종 단일 내부 관측은 queued29.15초, 완료 status28.37초/manifest28.46초,
frame0 26.49초/frame11 26.44초/replay27.58초였다. replay는67,660bytes였다.
원자 snapshot213.436초/정상359.713초/현재232.956초/늦은273.067초/
취소116.656초/fresh332.852초로 각 단계600초 이내였다.
최종 수용 단계의 최대 PID113,127,424bytes/보호+소유 합436,154,368bytes, .25초 표본·FD4→4·소유 child0이었다.
원2root/2,148항목·관련 artifact/배포 파일을 보존했다. Windows Chrome/공통 WSL 용량 수용은 포함하지 않는다.
코드 SHA·원 실패/각 단계 로그 해시·정리·정확 native gpt-6.1-sol/xhigh와 재귀0은
[기계 증거](artifacts/crop-leaf-population-execution-query-20261023.json)에 기록했다.

클라이언트 기본30초에 가까운 내부 관측이므로 **실제 HTTP/TLS·전송/취소·U1 성능은 미수용**이다.
보호 HTTP 단계에서 전송 경계와 실제 요청 예산을 검증한다. 현재성 검사를 건너뛰거나 timeout을 임의로 늘려 통과시키지 않는다.
다음은 기존 foreground consumer에 정확 leaf worker/outcome·판본 등록이다.
실제 discovery→1계산, 다른 queued 모델 보존·완료 재선택0·현재 scope/같은 graph·정리를 검증한다.
등록/계약30–60분 + 집중/실제 DB30–60분 + 기록15–30분 = **1.25–2.5집중시간**의 낮은 신뢰 작업량이다.
E3의 이전2–4h 계획은 이번 수용으로 대체하며 실제 consumer 검사 뒤 다음 범위를 갱신한다.
이후 보호 API/runtime→strict SDK/같은 job의 제품3D·메뉴/재접속 복원 순서다.

[사용자 화면](http://localhost:5176/leaf-population-replay.html)은 기존 저장 합성3→6잎 재생이다.
새 leaf core는 사용자 runtime에 미배포이며 자동 leaf 실행/제품 통합 완료로 표시하지 않는다.
실제 Axiany 계수/초기관측·독립 현장 작기0, 생산·자원/경제·자율 선정·최종 사실감/첫 셰이더 경고,
G0–G4 및 전체 제품 완료 날짜 미정을 유지한다.
