# 수확 후속 부모의 정상 producer·인증 보존 구성 v1

선행: [작은 DB·인증 복원 수용](../research/crop-harvest-parent-backup-implementation-20261009.md).
core3: 이 계약, `research/crop-harvest-parent-production.py`,
`backend/tests/crop_harvest_parent_production_smoke.py`.

1. 기존 supervisor/정상 계산·별도 Python 전체 행/121상태 대사·정상 DB publisher를 재사용한다.
   먼저 작은 관리 사건 작기로 검증한다. 새 제품 API나 수식·격자/계수를 바꾸지 않는다.
   후속 수확 API/웹6파일 변경으로 구형 source guard가 현재 checkout을 거부하므로,
   정상 producer는 `dc7b852`의 별도 고정 worktree에서 이 core3와 선행 backup core를 복사해 실행한다.
   원392 source hash를 전부 확인한다. 기존 guard/서명 검사를 변경하거나 monkeypatch하지 않는다.
   실행한 baseline/복사 파일 hash와 현재 제품 코드의 판본을 구분해 기록한다.
2. 기존 producer가 시작 전에 export한 private runtime와 무작위 server/DB/result key를 보존한다.
   완료 결과 증명은 그 정상 결과에 한 번 발행하고 실제 DB·roles를 함께 backup한다.
3. source DB 정리 전 현재 query의 원 ID/payload/hash/UTC와 처음/마지막 sample·전체 event를 확인한다.
   현재 권리/scope 철회·다른 tenant를 거부하고 복원한다. 읽기의 RHS/게시/증명 발행은0회다.
4. source DB 정리 뒤 fresh Python에서 backup을 실제 복원해 같은 현재 query/원 행을 읽는다.
   모든 행 대사는 게시 전 비교, 대표 조회는 게시/복원 뒤 검사로 구분한다.
5. 작은 구성은 원600초, 전체는 원32,400초(9시간) 준비부터의 고정 마감이다.
   nice19·단일512MiB/소유 합1GiB, source/원 입력 보존·원 종료/정지·비공개 비밀의 명시 보존을 확인한다.
   관측 timeout은 원 실패로 간주하거나 같은 계산의 재시작 근거로 사용하지 않는다.
6. 작은 수용 뒤에만 전체를 시작한다. 새 전체는 동일 원 입력/모델의47,809sample/5event·1,816,704걸음이며,
   기존 전체 수용의 후보 행 hash/수량/UTC와 대사한다. 새 농장/payload/source 판본을 별도로 기록한다.
   구형 서명 검사 우회·임의 DB 게시 행 삽입·구형 profile/계보 덮어쓰기는 금지한다.

작은 수용은 전체 수용이 아니다. 전체도 수확 writer/API/3D나 품종 검증·G0–G4를 대신하지 않는다.
사용자 산출물은 작은 실행 증거, 이후 전체 실행의 실제 시작/마감/진행·원 종료와 보존 자료 목록이다.
