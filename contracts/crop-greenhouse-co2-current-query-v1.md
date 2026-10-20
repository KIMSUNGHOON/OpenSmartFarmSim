# CO₂·일사 저장 결과의 현재 권리 조회 v1

Status: implemented; actual SCRAM/fresh/late-change acceptance pending.
[사전 증거](../research/artifacts/crop-greenhouse-co2-current-query-preflight-20261021.json)는
잘못된 저장소5개 거부와 전체11개 수집·원5root/자료/자원·정리를 확인했다.
실제 DB 정상/보류·fresh 현재 권한·철회/변조/경계 검증은 격리 CI에서 후속한다.
개발 선행은 [공개 투영의 기능 수용](api-crop-greenhouse-co2-replay-v1.md)과
[기존 서명 결과 저장소](crop-greenhouse-co2-result-store-v1.md)다.
projection 부모의 WSL 동시 용량과 새 사용자 적용 조건은 그대로 남는다.
[기존 Solar 현재 조회](crop-greenhouse-solar-current-query-v1.md)의 같은 세션/직렬화 뒤 확인을 대조한다.

## 경계

`Co2CurrentQuery`는 exact `Co2ResultStore` 인스턴스만 받고 store/pointers·현재 코드/의존성을 고정한다.
`read(tenant, result_id, farm_ref, *, view='summary', offset=0, limit=None)`은 검증된 원 UTF-8 bytes 또는
권한 있는 현재 조회에서 존재하지 않는 결과의 None을 반환한다. 별도 HTTP/worker 활성화는 하지 않는다.

view는 summary/samples/events다. summary의 offset0/limitNone, samples64/events8과 원 총량/페이지 끝,
exact 정수(bool 거부)·farm selector·2MiB를 지킨다. 다른 가족/테넌트/농장·서명/소스/판본 혼합은 보류다.
권한/런타임 역할·busy/pending의 기존 예외 의미를 유지하고 내부 오류문은 공개하지 않는다.

## 같은 세션의 원문과 재확인

store의 현재 `_read` 세션에서 원 row/metadata/progress/recorded_at을 얻고 같은 ArtifactReader로
summary/manifest/UTC와 원 page를 읽는다. `source_program`은 그 reader의 검증된 context에서만 가져온다.
사용자 입력·현재 시각·새 forcing 선택으로 program/basis를 대신하지 않는다.

투영 전과 직렬화 뒤의 DB row/HMAC·원 progress/컬럼·최초 기록 시각, 현재 계정/권리와 farm selector,
원 artifact/선택 HEAD/페이지를 재확인한다. `_read` 종료의 현재 검사와 마지막 권한 검사를 마친 뒤 bytes를 반환한다.
늦은 철회/변조는 이미 생성한 bytes도 반환하지 못하게 해야 한다. 같은 세션/현재 등록 witness를 유지한다.
캐시로 현재 검사를 건너뛰거나 Context/restore/RHS/적분·관리/새 UTC binding/CLI를 실행하지 않는다.
조회에 DB 쓰기나 최초 recorded_at 갱신이 있어서는 안 된다.

## 수용 기준

실제 SCRAM 정상/보류의 원3응답과 값/단위/UTC·checkpoint/마지막 확정·forcing basis를 대사한다.
별도 fresh 프로세스는 현재 DB/입력 권리와 서명을 다시 확인해야 하며 투영 전용 fresh 검사를 대신 쓸 수 없다.
초기/투영 중/직렬화 뒤의 입력 권리·검토·농장 원천·계정/범위 철회, DB 서명/컬럼/progress/기록 시각·
선택 HEAD와 실제 원 페이지 변조가 응답을 차단하는지 확인한다.
닫힌 인자·빈 마지막 페이지·외부 테넌트/농장·바뀐 store/코드와2MiB를 확인한다.
조회17수치 진입점/CLI/SQL쓰기0, 원 행/최초 시각·원 자료·FD/소유 PG/schema/role/passfile 정리를 대사한다.
집중 검증의 원600초·512MiB/PID/합1GiB를 유지하고 hosted 결과로 기존5root 포함 WSL 용량을 해제하지 않는다.

수용 뒤 보호 HTTP/명시 runtime→worker/prefix→같은 UTC3D로 진행한다.
실제 품종/작기·자원/경제 예측과 G0–G4는 [제품 명세](../docs/PROJECT_SPEC.md)의 별도 조건이다.
