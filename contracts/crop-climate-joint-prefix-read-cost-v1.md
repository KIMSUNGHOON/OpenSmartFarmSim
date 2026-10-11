# 확정 prefix 조회의 반복 농장 검증 — v1

상태: P6a2c2 소프트웨어 로컬 수용. 사용자 P6a/P6b 수용과 별도다.
[계측·최종267개 검증 기록](../research/crop-climate-joint-prefix-read-cost-implementation-20261011.md)과
[기계 증거](../research/artifacts/crop-climate-joint-prefix-read-cost-reference-20261011.json)를 따른다.

P6a2c1의 실제 API 스레드 프로파일에서 사건 페이지 한 요청에 농장 등록 조회34회,
DB 연결547회, 역할 감사615회를 관측했다. `_Session._guard`의 current callback이 매번
전체 농장·시장·경제 참조를 재검증하는 경로가 지배적이었다. 계측 시간은 일반 성능 보장이 아니다.

## 수정 범위

prefix reader1파일의 내부 session callback을 변경한다. 공유 custody/farm binding,
writer·수치·DB·공개 DTO는 유지한다. reader 내부 판본은 v5다.

`read`와 `_after_projection`의 기존 전체 `query._current` 검사는 모두 유지한다.
각 경로가 session을 열기 전과 닫은 뒤 전체 농장·자료·권리를 확인하고, HTTP는 직렬화 후에도 확인한다.
session 내부 파일/서명 검사 사이에서는 서명 intent에 결속된 같은 binding의 다음 항목을 매번 검증한다.

- 동일 server/binding 객체·코드·정책·tenant와 현재 농장 조회 scope.
- 현재 resolver가 반환한 입력 증거 및 그 normalized input 전체가 binding의 input과 일치하는지.
- 현재 표시권과 불변 권리 선언. 입력 검증·권리 검사의 전후 guard.
- 기존 custody의 intent/directory/usage 및 HEAD/proof/commit/page 서명·계보 검사.

전체 등록 검증 결과를 전역/시간 기반 캐시에 저장하지 않는다. callback은 외부 응답을 발행하지 않는다.
중간에 농장 등록/그 참조가 거부되면 다음 전체 경계 검사에서 응답을 거부한다.
현재 표시권이나 입력 변경은 내부 callback에서도 즉시 거부한다.

## 수용

1. 실제 SCRAM에서 같은 원 page/UTC, 현재 권리·입력 철회, 취소/종료, signed rollback/fork와 늦은 농장 조회 거부를 확인한다.
2. HTTP 직렬화 후 witness/권리 검사와 기존 schema·원 수치를 확인한다.
3. 같은 unpaused HTTP 프로파일에서 전체 등록 조회/DB 연결/감사 호출 감소를 측정하고 원 terminal bytes를 대사한다.
4. worker 지연0·조회 계산/쓰기0·원본·두 사용자 서버·WSL·소유 정리를 확인한다.
5. 이후 실제 브라우저/WebGL 전체 경로를 다시 수용한 뒤 사용자5174에 적용한다.
