# Leaf 현재 조회의 농장 등록 읽기 범위 — 후보 v1

상태: **조회 소프트웨어65검사·별도 실제 HTTPS 수용, 사용자 적용/UI와 접수30초는 후속**.
[검증·실패·보류](../research/leaf-population-query-registration-scope-20261023.md)를 확인한다.
[실제 지연·연구 비교](../research/leaf-population-execution-web-20261023.md)의 다음 작은 수정이다.
[기존 E3](crop-leaf-population-execution-v1.md)와 [보호 HTTP](api-crop-leaf-population-execution-v1.md)의
출력·Scope·현재성/취소·불변 결과와30초 계약을 따른다. 새 HTTP 경로나 계산 모델을 만들지 않는다.

## 선택과 범위

1. 기존 query의 UUID/view/권한 검사와 원 job 조회·intent HMAC/현재 resolver 검증을 먼저 수행한다.
2. 검증된 원 job 요청의 farm `scenario_id/scenario_revision/registration_sha256`을 사용한다.
   URL 인수·브라우저 저장 상태나 다른 작업의 결과에서 farm 참조를 선택하지 않는다.
3. leaf authority → 완료 parent authority → 그 farm binding의 동일 `FarmAuthoringService`를 사용한다.
   기존 객체/코드/provider 결속 검사를 유지한다.
4. 해당 서비스에 등록 읽기 범위가 없으면 기존 `registration_read_scope`를 열어 현재 조회를 감싼다.
   기존 범위가 있으면 중첩 범위를 열지 않고, 기존 helper가 같은 actor/ref·실행 문맥을 검증하도록 한다.
   다른 ref나 손상된 witness를 캐시 미스로 취급해 별도 원 경로로 우회하지 않는다.
5. 정상 반환·거부·예외 모두 범위와 소유 연결을 정리한다. 요청·thread/task 사이에 범위를 재사용하지 않는다.

helper는 첫 등록 입력 재구성을 보관하되 매 조회의 현재 원천·원 행/권한을 다시 대사한다.
기존 helper의 동작과 검증을 변경하지 않는다. 도입부에서 농장 등록·권리·서명 검사를 새로 대체하지 않는다.
scope 안에서도 원 query의 전후 `_guard/_intent/_bundle`, 두 signed `_load`, leaf/parent 권리·원본 대사를 유지한다.
원 SQL snapshot/worker 완료 Pending과 오류 처리 순서를 대조한다.

## 변경하지 않는 결과 경계

미완료 작업은 status만 제공한다. 완료 manifest/frame/replay는 원 publication과 같은 signed result를 대사한다.
원 값·기관/UTC·result/root/parent·최초 calculated_at과 정규화를 유지한다.
조회는 새 생장 계산·서명 결과 작성·CLI·지속 SQL/파일쓰기를 수행하지 않는다.
등록 재구성의 내부 비용 개선은 권리 승인·품종 검증이나 G0–G4 수용이 아니다.

기존 source4f1f523/DB/키·결과를 보존한 별도 source 판본으로 검증한다.
기존 intent/publication의 코드 결속과 새 query의 호환성을 실제 조회로 확인한다.
기존 파일을 고쳐 과거 실행의 source로 표시하지 않는다.

## 수용 증거

- 같은 원 요청의 queued/simulating/canceled와 완료 status/manifest/frame0·11/replay를 대사한다.
  observed_at 외 원 결과와 최초 계산 시각·12frame/52면적, 원 application 행/불변 파일이 같아야 한다.
- 원 등록의 재구성 횟수와 현재 권한·원천 재확인 횟수를 구분한다.
  첫 재구성 뒤의 source/rights/등록/parent 변경, 읽기 Scope/actor 변화는 원 경로와 함께 거부해야 한다.
- 마지막 frame 뒤 철회/원본 변경, 독립 취소·worker 완료 경합과 one-snapshot Pending을 검증한다.
  원 결과가 이전 값이라는 이유로 현재 거부를 정상 응답으로 바꾸지 않는다.
- 중첩·다른 ref/thread의 범위, 예외 뒤 scope/connection/FD 잔류와 readonly/growth/CLI fence를 검사한다.
  기존 E3·HTTP의 정상/오류 회귀와 독립 새 프로세스의 무계산 조회를 수행한다.
- 실제 SCRAM/검증 TLS에서 동일 actor/입력·관측 예산으로 status/replay와 동시 동일 POST를 검사한다.
  제품 요청30초 내 정상 응답·같은 job/attempt1/원 결과, 늦은 거부/취소·소유 정리를 각각 확인한다.
  별도 프로세스의 함수 시간이나 프로파일 수치는 실제 HTTP 통과로 대체하지 않는다.
- 그 뒤 현재 SDK의 새 job3D·메뉴/reload·실제 권리 거부 제거/복원과 원 화면/자료 보존을 수용한다.

연구 비교에서 status 값/25표·scope 종료와 시간 개선을 확인했다.
별도 shadow leaf 권리 파일의 첫 확인 뒤·마지막 frame 뒤 철회4경우도 원/후보가 함께 거부했다.
현재 변경11종/다른 등록3종·기존 경합/fresh와 별도 실제 HTTPS의 원 결과 조회를 확인했다.
제품 query 소스는 최소 수정했고 frozen source의 나머지819파일은 원 판본과 같다.
기존 native HTTPS 정상 시험은 leaf GET 전에 첫 접수 POST30초 초과로 실패했다.
사용자 적용·현재 SDK UI와 접수/동일 retry30초는 남아 있으며 부모 runtime 수용을 유지 보류한다.
