# CO₂ 확정 구간의 닫힌 공개 응답 — v1

Status: pure87 (projection83 + private source4) and actual SCRAM core7 accepted.
[Evidence](../research/api-crop-greenhouse-co2-prefix-20261021.md). Late native10/fresh/affected-reader regression93 and user activation remain required.
2026-10-21. 선행은 [확정 원 조회31검사](crop-greenhouse-co2-prefix-v1.md)의 전체 수용,
[기존 CO₂ 공개 원량](api-crop-greenhouse-co2-replay-v1.md)과 현재 진행 응답이다.
기존 [Solar 공개 응답](api-crop-greenhouse-solar-prefix-v1.md)의 none/closed/accepted 구분과
선택자·현재성/직렬화 후검사를 사용하되 CO₂의 원 타입·basis·model identity를 따른다.

## 공개 경계

`joint-co2-solar-prefix-replay-v1`의 none/closed에는 reference/summary/page가 null이다.
accepted에는 원 선택자·최초 DB 확정 UTC/attempt·농장/입력 식별자·manifest/time grid와
summary 또는 page 하나를 제공한다. 기존 `Co2Sample`/`Co2Event`의109상태·44연속/6사건 장부·
17수지·관리 전후·PAR/NIR·CO₂ 진단의 원 quantity와 단위/UTC를 보존한다.
입력 명령·계수·권리/검토/provenance 원문·서명/개인 경로·자격증명은 공개하지 않는다.

원 범위 `synthetic_joint_co2_solar_math_only`와 claim 범위
`synthetic_joint_co2_solar_confirmed_prefix_only`, not_assessed/승인 False,
정규화·QC·입력 증거 판본과 해당 품종 미검증 표시는 기존 CO₂ 계약을 따른다.
64 sample/8 event·전체 UTF-8 응답2MiB·끝 빈 배열/원 offset·정수 microsecond UTC 격자는 유지한다.
정수/bool/문자열을 물리량 float로 바꾸거나 누락 수치를 만들지 않는다.

## wet/dry의 원 프로그램 결속

각 행의 `co2_basis`는 원 `forcing_step_index`에 해당하는 검증된 프로그램의 wet/dry다.
기존 CO₂ 공개 모듈의 `_basis_map(program, manifest)`, `_basis(value, bases)`와
`_event(row, identity, bases)`를 사용한다. manifest program hash·격자와 원 forcing index를
대사하며 CO₂ 수치에서 basis를 추정하지 않는다.

순수 `project_prefix(record, *, source_program)`은 프로그램을 명시적으로 요구한다.
순수 투영은 현재 권한/DB 수용을 승인하지 않는다. 서버의 `read_prefix`는 정확한
`Co2ExecutionPrefixQuery`가 읽은 context.program의 canonical bytes를 서버 내부 owner-bound
witness에 결속한다. 이 바이트는 immutable이고 원 payload/manifest/선택자에 묶인다.
호출자 프로그램·JSON으로 복구한 witness를 권한 있는 읽기의 fallback으로 받지 않는다.

원 조회 응답의 공개 전 내부 형식·원 selector/UTC는 바꾸지 않는다. 프로그램은 private witness에만
보존하고 공개 응답 필드로 추가하지 않는다. 직렬화 후에는 원 선택 context/page·manifest/program
바이트와 현재 입력/권리·DB 사건/서명 이력을 다시 대사한다. 정상 append/heartbeat가 원 선택을
보존하면 읽을 수 있고 취소/다른 시도·입력/철회·변조는 응답을 차단한다.

## 구현·수용 순서

1. 순수 schema/원 값·단위/UTC·basis 전환과 비공개 필드, 승인 False/provenance·코드/판본·2MiB를 검증한다.
   없거나 다른 프로그램·잘못된 hash/index/basis와 CO₂가 아닌 타입을 거부한다.
2. private witness에 저장 프로그램을 결속하고 실제 SCRAM의 none/ready/running/normal/hold/cancel,
   현재/직렬화 뒤 권리·농장·원 선택 page/context 변조·소유/witness 이동을 검증한다.
3. 독립 actor의 원 signed HEAD/확정 사건 append·heartbeat/cancel과 별도 producer/reader의
   이전 선택 공개 bytes(관측 시각 제외)/원 UTC·basis·최초 시각을 대사한다.
4. 추가 witness 경계에 영향받는 원 조회의 선택/후검사·기존 결과 투영을 회귀 검증하고,
   조회 수치/복원/확정·SQL쓰기0 및 기존 자원/정리·서비스/자료 보존을 확인한다.

위 수용은 새 HTTP 경로/역할·worker runtime이나 사용자3D 배포가 아니다.
후속은 보호 실행 HTTP/runtime → typed web/같은 UTC3D → WSL/사용자 정상·보류·취소/복구다.
전체 작기·자원/경제/최종 UI·실제 CLI 종단 간·외부 자료/관문/예측·추천의 기존 미완료 범위는 유지한다.

## 고정한 native 실행 범위

[전체110개 수집 증거](../research/artifacts/api-crop-greenhouse-co2-prefix-native-preflight-20261021.json)를
`co2-prefix-projection-core`7 → `co2-prefix-projection-fences`10 → `co2-prefix-projection-regression`93으로
나눈다. 마지막93은 공개83/private4·독립 fresh1·영향받은 raw5다. 원 Solar의 DB15/fresh1 의미를 유지하고
CO₂의 실제 basis 전환/늦은 program 변조2개를 추가한다. 전체110의 source·원량/UTC·source/권리·정리 수용 전
부모를 완료하지 않는다. witness 부재의 직렬화 전 거부와 다른 최종 직렬화 뒤 변경을 구분한다.
