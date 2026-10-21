# 형태 계산의 접수·완료 참조와 현재 조회 — v1

상태: [E1 제어11/실제 SCRAM2](../research/crop-morphology-execution-admission-20261022.md),
[E2 참조9/실제 SCRAM5](../research/crop-morphology-execution-worker-20261022.md) 수용. E3와 HTTP/UI는 후속이다.

선행: [완료 수치 서명/현재 조회](crop-morphology-signed-artifact-v1.md).
기존 JobStore의 deterministic simulation·jobs/job_attempts/job_events/job_publications/attempt_outcomes를 사용한다.
근거: 기존 [작업 계약](../docs/ARCHITECTURE.md#http작업-계약)과
Joint 실행의 admission/worker·JobStore publish/lease/취소 규약이다. 새 결과 표/Role 판본은 이 경로에 필요하지 않다.
기존 JobStore/runtime_roles·수치/입력/농장 source는 보존한다.

## E1 접수

`MorphologyExecutionService(authority,input_resolver=...)`는 trusted authority와 판본 고정 resolver를 받는다.
resolver는 tenant/닫힌 input 참조에서 원 program/source/evidence bytes만 반환한다. 사용자 경로/키는 받지 않는다.
simulation_create·현재 farm write/current source를 확인하고 현재 binding을 기존 blob store에 보관한다.
Job input은 morphology-execution-input-v1/request/binding SHA/resolver 판본·authority issuer/key ID/실행 코드 지문이다.
64KiB 안에 원본/키 없이 참조만 저장하고 별도 intent HMAC domain으로 admission key/version도 결속한다.
study/revision의 versioned intent key와 기존 submit commit_guard로 같은 요청의1행/같은 job·충돌 거부를 보장한다.
접수는 계산/서명 결과나 G0 승인으로 표시하지 않는다.

## E2 worker·완료 참조

새 worker는 해당 tenant/input_version의 simulation만 claim한다. 기존 임대/시도/취소 규약을 사용한다.
현재 원 입력/binding·intent를 검증한 뒤 실제 완료 producer를 실행한다. 중간 미검증 프레임은 내보내지 않는다.
시작/완료 단계와 실제 원 output 수를 사건에 기록하며 임의 퍼센트/성장 애니메이션으로 진행을 대신하지 않는다.
현재 권리/등록·원 job input/lease/cancel을 publication transaction 전후에 재검사하고 기존 private artifact writer로
작은 **opaque result reference**를 저장한다. 같은 transaction에 publication/outcome/events·terminal state를 기록한다.
다른 모델/시도·만료 임대/취소·현재 철회는 게시하지 않는다. 완료 job 재조회/동일 접수는 수치 재실행0이다.
중단된 시도는 기존 attempts 정책을 따르며 새 시도의 계산 시각/증거를 보존한다. completed artifact 자체를 승인 Run으로 승격하지 않는다.
계산은 job 행 잠금 밖에서 수행한다. 실제 deterministic 계산 시작 사건과 code/input SHA·원 output 수를 기록하고
AI 전용 attempt_invocations에 가짜 CLI 호출을 넣지 않는다. 완료 전 취소·임대 만료/권리 철회 때 private artifact가
남을 수 있으나 publication/완료 참조는 없으며 제품 query로 조회할 수 없다. 이 v1은 계산 중 프레임이나 checkpoint 재개를 약속하지 않는다.

## E3 현재 조회와 다음 API

같은 job의 닫힌 input·publication/ref/hash를 검증하고 현재 표시 권리를 확인한 뒤 status/manifest/frame을 조회한다.
원 서명 결과 ID/calculated_at·numerical root/원 DTO를 보존하고 조회 계산/쓰기/CLI0을 요구한다.
generic job artifact에는 원 crop 값/농장 문서 없이 opaque 참조만 넣는다. 수치는 현재 검사를 통과하는 전용 query로 읽는다.
프로젝트 UI의 접수/재접속과 보호 HTTP는 이 core 수용 뒤 연결한다. 전체 CLI 지역 조사/선정·G0–G4는 별도다.

수용은 접수(권한·commit fence·멱등/충돌/0계산) → worker(정상/hold/취소/lease·원 서명과 원자 게시) →
현재 query(원 bytes/UTC·현재 철회·fresh·0계산/쓰기)로 나눈다.
각 단계 실제 SCRAM/원 행·기존 모델의 queued job 보존·6root/WSL 상한·소유 정리를 확인한 뒤 체크한다.
