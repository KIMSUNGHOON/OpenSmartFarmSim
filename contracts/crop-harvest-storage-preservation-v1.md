# 새 부모 수확 저장·인증 보존 v1

선행: [작은 정상 producer](../research/crop-harvest-parent-production-small-implementation-20261009.md),
[수확 registry](crop-harvest-registration-v1.md), [현재 조회](crop-harvest-registered-query-v1.md).
현재 native Codex CLI `gpt-6.1-sol / xhigh`에서 판단하며 재귀 CLI는 실행하지 않는다.
core4: 이 계약, `research/crop-harvest-storage-preservation.py`,
`backend/tests/test_crop_harvest_storage_preservation.py`,
`backend/tests/crop_harvest_storage_preservation_smoke.py`.

## 범위와 순서

1. 이미 수용한 작은 부모의 보호 backup을 실제 별도 PostgreSQL16.15에 복원한다.
   현재 `CalculationCurrentCycleQuery`가 주는 새 source/첫·마지막 UTC/원 위치에
   기존 합성 질량 계수·배정 규칙의 명시 새 profile 판본을 결속한다.
2. 기존 `HarvestRegistry.put`만 writer/전체 행 검사·서명 DB 등록을 수행한다.
   원 crop RHS/새 crop 게시·증명 발행은 금지한다. 새 수확 행 생성은 이 저장 단계에만 허용한다.
3. 별도 수확 publisher/reader·무작위 서명 key·원 profile과 metadata를 비공개로 보존한다.
   수확 등록을 포함한 DB/roles를 기존 부모 backup 형식의 새 디렉터리에 다시 보존한다.
   초기 부모 backup/서명/이력은 덮어쓰지 않는다.
4. 원 복원 DB를 정지한 뒤 fresh Python이 새 DB backup과 수확 reader를 복원한다.
   재보존된 roles에는 첫 복원의 bootstrap 계정도 있으므로 두 번째 복원은
   별도 고정 bootstrap 계정을 사용한다. 역할 삭제/SQL 변조·서명 우회를 하지 않는다.
5. 원 수확 ID/payload/최초 시각·원문 hash·summary·대표 page/UTC를 대사한다.
   작은 경우에는 모든 행이 대표 page에 포함된다. 현재 권리/scope 철회·다른 tenant를
   거부하고 원 권리 bytes를 복원한다. 조회에서는 RHS/수확 행 생성/등록/증명 발행을 금지한다.

## 수용과 한도

- 닫힌 manifest·각 보호 파일/코드/DB backup hash·private mode·혼합 source/credential 거부.
- 실제 SCRAM의 정상 writer/DB 등록 후 정지·fresh 복원·동일 record/원 행과 철회/복원.
- 원 작은 부모 입력/artifact/backup의 bytes/mode/inode, 원 종료0·FD·소유 PG/임시 정리.
- 작은 준비부터900초·nice19·단일512MiB/소유 합1GiB. raw DB backup128MiB,
  수확 artifact512MiB/registry1GiB와 기존64행·2MiB page를 유지한다.
- 보호 key/passfile/DB dump는 작업 전용0700 디렉터리에 보존한다.
  공개 증거에는 원문/비밀/private 경로를 내보내지 않는다.

이 수용은 작은 새 source 저장/보존 자식만 완료한다. 진행 중인 전체166일 부모의
원 종료/최종 감사가 끝나기 전에는 전체 writer를 실행하지 않는다. 전체 행 수량 대사와
실제 API/대표3D는 각각 후속이다. 계수는 기존 합성 fixture이며 실제 생산/수확 예측이 아니다.
기후·물/양분·구매 에너지·Decimal 경제와 실제 품종/농장 자료·G0–G4/추천 hold는 유지한다.
