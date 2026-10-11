# 환기 계산의 확정 부분 결과 조회 v1

상태: [합성 소프트웨어 범위로 로컬 수용](../research/crop-greenhouse-ventilation-prefix-api-implementation-20261012.md). 새279/기존 호환105=고유384개·실제 SCRAM/TLS/독립 자동 정상·보류·취소·원 terminal 대사·기존 두 화면/결과/자원 보존을 통과했다. 새 모델의 실제 실행 중WebGL와 사용자 적용은 후속이다.

선행: [현재 실행 조회](crop-greenhouse-ventilation-execution-http-v1.md),
[서명 이력](crop-greenhouse-ventilation-server-custody-v1.md),
[불변 페이지](crop-greenhouse-ventilation-storage-v1.md),
[완료 결과 웹](../research/crop-greenhouse-ventilation-web-terminal-implementation-20261012.md).
기존 [전진 조회](crop-climate-joint-prefix-forward-read-v1.md)의 선택 사건·현재 권리·서명 계보 검증을
환기25장부/10수지 판본의 별도 reader·projection·HTTP에서 적용한다.

## 조회와 공개 형식

`VentilationExecutionPrefixQuery`는 실제 DB 수용 사건의 최초 시각/attempt와 서명 HEAD를 선택한다.
현재 입력·농장·권리·검토·계정과 원 custody를 검사하고 선택한 HEAD에서 원 sample/event를 읽는다.
새 private HEAD가 존재해도 DB 수용 이전 시점을 채택하지 않는다. 정상 append/임대 갱신은
원 선택 사건/이전 latest/관측 HEAD의 불변성과 현재 signed ancestry를 증명한 경우에만 허용한다.
취소·종료·attempt/token/input 변경은 응답을 다시 조회하게 하며 역행/fork/삭제·변조·권리 철회를 허용하지 않는다.
후검사 witness는 서버 내부 객체이며 공개 payload에서 복원하지 않는다.

새 응답 판본은 `joint-ventilation-prefix-replay-v1`, 원량 범위는
`synthetic_joint_ventilation_math_only`, 부분 결과 범위는
`synthetic_joint_ventilation_confirmed_prefix_only`다. G0–G4는 `not_assessed`다.
accepted는 원 selector/checkpoint·농장/입력/manifest/UTC 격자와 summary 또는 page를 제공한다.
samples는 원108상태/25장부/10수지·환기 진단, events는 원 관리 전후·제거량·ventilation_after를 보존한다.
none/closed는 reference/summary/page=null이며 수치/미래 프레임이 없다.
lease/token·원 입력/매개변수/forcing·권리/계정 원문·자격증명은 공개하지 않는다.

GET `/v1/jobs/{job_id}/crop-greenhouse-ventilation-execution/prefix`는 query/body 없이 최신 확정 요약을 읽는다.
`/samples`와 `/events`는 `publication_sequence`, `head_sha256`, `proof_sha256`를 필수로 받으며
`start=0`, `limit=64`/`8`이 기본이다. 끝 offset은 원 total과 빈 배열을 반환한다.
닫힌 query·중복/추가 query/body 거부·정확한 UUID/hash/숫자·UTF-8 전체2MiB·no-store·전후 인증을 적용한다.
401/403/404, 선택 충돌409, 잘못된 요청/현재 증거 거부422, 전후 변경/일시 불가503을 구분한다.
서명/권리 거부를 계산 전진의 일시 대기로 숨기지 않는다.

## 명시 조립

새 prefix 설정 판본/기본False와 execution=True 의존성을 검사한다.
같은 jobs/farms/principal·result store·실행 query의 reader만 설치하며 기존 설정은 prefix를 켜지 않는다.
읽기는 REPEATABLE READ READ ONLY와 현재 권리 후검사로 처리한다. 계산·checkpoint confirm·재서명·DB 쓰기는0이다.
같은 선택자의 원 수치를 페이지 사이에 혼합하지 않는다. 전체 이력 검증 비용은 별도로 관측한다.

## 수용 기준

1. 실제 SCRAM의 미시작/ready·running·sparse/dense·빈/끝·이전 선택자·fresh process를 원 값/UTC와 대사한다.
2. 실제 독립 heartbeat/private/DB-confirm 전진을 거쳐 같은 선택자의 원 페이지를 유지한다.
   signed rollback/fork·선택/이전 latest 사건 교체·취소·늦은 권리·proof/HEAD/page 변조를 거부한다.
3. 닫힌 DTO·25장부/10수지·원 관리/환기/격자/모델·2MiB·비공개 필드 경계를 검증한다.
4. 명시 runtime의 실제 검증 TLS/자동 unpaused worker 정상·보류·취소에서 공개 요약→같은 selector의
   사건/생장200과 원 terminal을 확인한다. 장벽/직접 DB discovery를 공개 running 성공으로 세지 않는다.
5. 구 모델/설정·두 사용자 화면/원본/키/권리·WSL 상한·원 도구 종료·FD/소유 정리를 확인한다.

계산 중 실제 제품 WebGL와 사용자 적용은 후속이며 이 API만으로 부모3D·실제 생산/예측/추천 관문을 수용하지 않는다.
