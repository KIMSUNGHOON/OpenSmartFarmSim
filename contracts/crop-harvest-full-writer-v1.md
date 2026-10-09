# 전체 수확 정상 등록·대사·보존 실행 — v1

2026-10-09. 선행 [실제 두 페이지 비용](../research/crop-harvest-writer-prefix-cost-20261009.md).
native Codex CLI `gpt-6.1-sol`/`xhigh`, 재귀 CLI0. core3는 이 계약,
`research/crop-harvest-full-writer.py`, `backend/tests/test_crop_harvest_full_writer.py`다.

## 실행과 보존

고정 source에서 원 전체 부모 backup/key/input/artifact를 실제 별도 DB에 복원하고
수용한 새 합성 profile 판본으로 정상 `HarvestRegistry.put`을 호출한다. 중단 hook이나
임의 응답/수확 행을 주입하지 않는다. 원 crop RHS/게시/proof는 금지한다.
원 source·47,809sample/5event·완료 상태를 확인하고 다른 계보로 대체하지 않는다.

정상 수확 DB 등록 직후 원 record/key/프로필을 private로 보존하고, **독립 대사 전에**
수확을 포함한 인증 DB backup을 만든다. 이 중간 backup은 미수용 연구 결과다.
후속 실패 시 원 source·새 artifact/DB data/key/backup을 지우지 않고 보류한다.
재생성보다 정상 동일 재시도/검증 복구를 우선한다.

## 전체 독립 검증과 fresh 조회

현재 서명 DB와 원 source에 결속한 harvest reader의 하나의 기존 전후 guard 작업 안에서
모든 저장 blob bytes/SHA/count와 전체 원 행/순서를 읽는다. 별도의 구조 reader는
수용 영수증의 고정 SHA·원 artifact·모든 sample/event hash를 확인하며 DB 권위를 대신하지 않는다.
현재 부모와 구조 reader의 source가 같아야 한다. Decimal2200으로 모든 질량/정확 배분·
수지/전체 합계/합성 관측 비교를 독립 대사한다. 조회 중 질량/배정 생성·RHS·등록은 금지한다.

같은 DB의 현재 reader에서 대표 첫64/마지막1행·원 record/최초 시각을 대사한 뒤
보존 helper의 정상 manifest를 만든다. 원 DB 정지 뒤 별도 Python/fresh DB가 동일 현재 조회를 수행한다.
다른 tenant와 이 query 인스턴스의 표시 권리 거부/복원을 확인하며 공유 권리 파일은 변경하지 않는다.
소유 거부 hook과 실제 외부 권리 취득/변경을 구분한다.

## 수용과 감독

1. 실제 전체47,813행/원 UTC·질량·단위/목적·미배정/hold·두 원문/코드 판본을 보존한다.
2. 정상 writer/서명 DB/독립 전체 대사/인증 backup/원 DB 정지/fresh 현재 조회의 원 종료와
   FD·원본/source/미리보기·512MiB/1GiB·소유 PG 정리를 별도로 확인한다.
3. 준비부터 producer10,800초, 이후 fresh reader900초 상한이다. 부분 비용의 외삽은 완료 보장이 아니다.
   실행 중 시작 identity/실제 PID·원 도구 handle·page 진행과 마감을 보존하며 관측 실패만으로 재시작하지 않는다.
4. 완료/정리/원 종료·root 감사 전에는 전체 writer 자식을 체크하지 않는다. API/대표3D는 후속이다.
   실제 농장 생산·예측/추천·U3·G0–G4는 이번 합성 저장 수용으로 해제하지 않는다.
