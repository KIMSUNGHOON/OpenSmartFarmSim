# 작물·기후 원 격자의 UTC 결속 v1

선행은 [분할 실행/복원](crop-climate-joint-continuation-v1.md)이다. 새 UTC 표시는 원 계산과 별도의
version/hash를 가진다. 원108상태·연속22장부·사건6합계·prefix·동적 T24/Tsum/RK4를 바꾸지 않는다.

## 시각 표현

`prepare_binding(context,origin=...)`에 닫힌 `{input_id,origin,start_at,precision}`을 전달한다.
ID는 공백 없는 가장자리의1–200문자, origin은 원 scenario와 같은 `synthetic|reference_calculation`,
precision은 `microsecond`다. 시작은 대문자T/Z 또는 명시 ±HH:MM의 RFC3339 부분집합이다.
소수초는0–6자리, 실제 Gregorian 날짜/00–59초만 허용한다. naive/이름 시간대/약어·소문자·24시·윤초·
7자리 이상 소수·`-00:00`은 거부한다. RFC3339의 unknown-offset 표기를 이 프로젝트는 지원하지 않는다.
표시는 항상 UTC·소수6자리·Z다. Python datetime의 UTC year1–9999 범위 전체 작기를 검사한다.

`str(normalized_step_seconds)`의 십진 값을 정수 마이크로초로 정확히 변환하고,
`start_utc + step_index * step_microseconds`로 표시한다. 비정수 마이크로초 격자는 precision hold이며
반올림/새 격자/누적 부동소수 시계를 만들지 않는다. 원 `elapsed_seconds=index*dt`는 그대로다.
예를 들어 dt0.1의3번 경계는 원0.30000000000000004초를 보존하며 UTC 간격은 정확히300000µs다.
이것은 표시 시각의 명시적 변환 정책이며 물리 적분·온도 이력의 시간 정책을 교체하지 않는다.

시간 manifest는 원 context hash·원 origin(입력 offset 포함)·정규화 시작/끝·step/count·시간 판본/코드 hash를
결속한다. 같은 UTC인 KST/UTC 입력도 원 provenance가 달라 별도 identity다. 원 계산만으로 실제 시작을
추론하지 않는다. `at_index(binding,index)`는0..count의 정수 원 격자만 표시한다.

## 원 체크포인트·chunk 연결

`bind_checkpoint(binding,checkpoint,expected_binding_sha256=...)`는 원 checkpoint hash/value와
별도 `time={step_index,at,next_index}`를 반환한다. initial-ready/t0 완료는 같은 시각이지만 next_index0/1을 유지한다.

producer의 `source_chunk_sha256(context,chunk)`는 원 JSON의 canonical SHA를 만든다.
원 내부 Checkpoint 객체만 `{sha256,value}`로 운반하고 다른 필드는 그대로다.
`bind_chunk(binding,before_checkpoint,chunk,expected_chunk_sha256=...,expected_binding_sha256=...)`는
신뢰 경로가 제공한 두 digest와 원 시작 checkpoint를 필수로 받는다. 원 context/manifest·닫힌 응답 shape·
상태/범위/커서·최대128경계의 누락 없는 sample/event 순서·원 elapsed·완료 prefix/cursor·마지막 상태와
확인된 호출 수를 검사한다. 각 원 상태/사건/last_confirmed/hold에 별도 `times`를 반환한다.
실패 사건은 추가하지 않고 실패한 경계의 시각과 마지막 확정 상태의 시각을 각각 보존한다.
호출 순서나 chunk grouping으로 원 prefix를 다시 정의하지 않는다.

시간 표시 자체의 RHS/적분/관리/복원 호출은0회다. 원108상태·수지·온도 이력을 재검증하기 위한 RHS를
이 모듈에서 실행하지 않는다. 입력은 이미 검증된 내부 context/checkpoint와 신뢰 digest의 원 producer 출력이다.
digest 재생성만으로 진본·권리를 승인하지 않는다. 후속 writer가 권한 있는 불변 저장/서명 custody를 제공해야 한다.
반환은 원 canonical source와 별도 시간/identity·payload SHA이며 원 checkpoint의 bytes/hash를 교체하지 않는다.
binding은 process 내부 frozen 객체이고 property/반환은 JSON 복사다. 내부 필드 재작성의 인증 경계가 아니다.

source/반환은 각각8MiB 이하의 **내부** 묶음이다. 이 상한은 HTTP 응답 허용량이 아니다.
후속 writer/reader는64sample/8event 등 페이지 단위로 나누고 실제2MiB transport를 별도 검증한다.

## 수용과 근거

기존9프로그램의 처음/중간/마지막·t0사건/hold·여러 chunk에서 UTC/KST와 원 state/장부/prefix/bytes를
대사한다. 소수 격자·윤년/세기/epoch/범위·모호한 offset/정밀도 손실·원 context/시간 판본/시작/커서 혼합을
검사하고 binding 중 수치 호출0·fresh Python·최대chunk bytes·원본/FD/원 종료/자원 보존을 확인한다.

표시 정밀도는 [PostgreSQL16의 timestamp](https://www.postgresql.org/docs/16/datatype-datetime.html)와
[Python3.12 datetime](https://docs.python.org/3.12/library/datetime.html)의 마이크로초 표현에 맞춘다.
정수 timedelta만 사용해 float 인자의 반올림을 피한다. [RFC3339](https://www.rfc-editor.org/rfc/rfc3339.txt)의
가변 길이 소수/윤초/unknown offset 전체를 지원한다는 주장은 하지 않는다.
문서 원문은 비공개 SHA/조회 시각으로 고정하며 코드·농업 데이터/계수의 채택은 없다.

이 모듈은 합성/참조 소프트웨어 계산 범위다. 권리·현재 계정·영속 저장/서명·API·3D·실시간 U3,
forcing 변경/온실/전체 작기·실제 생산 검증과 G0–G4 승인을 제공하지 않는다.
