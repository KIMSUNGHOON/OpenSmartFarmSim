# 수확 후속 검증을 위한 작은 부모 DB·인증 자료 보존

2026-10-09 KST. native Codex CLI `gpt-6.1-sol / xhigh`에서 판단·구현했다.
재귀 CLI0회. [불변 영수증](artifacts/crop-harvest-parent-backup-reference-20261009.json)의 SHA는
`46d46a69428d956d1a31b580adddba91d0d73ce566b554e972586e93cb75f39f`다.
원90143 종료0·집중11개/실제 DB1개·원 DB 정리 후 fresh Python 복원을 로컬 수용했다.

## 구현과 필요한 이유

[core4 계약](../contracts/crop-harvest-parent-backup-v1.md),
[소유 시험용 보존·복원 도구](crop-harvest-parent-backup.py),
[집중 반례](../backend/tests/test_crop_harvest_parent_backup.py),
[실제 SCRAM 시험](../backend/tests/crop_harvest_parent_backup_smoke.py)을 추가했다.
제품 모듈·API·의존성 잠금은 변경하지 않았다. 수확 후속 시험이 같은 저장 부모를 다시 읽기 위한 작업이다.

기존 전체166일 실행의 DB/config/passfile과 무작위 custody key가 실제 삭제된 것을 확인했다.
[원 생성 코드](../backend/tests/crop_cycle_registered_full_path_smoke.py)와
[현재 조회의 서명 검사](../backend/app/crop_cycle_calculation_current_query.py)를 대조했다.
보존 archive나 새 결과 검증 증명만으로 원 intent/proof의 HMAC를 복원할 수 없다.
구형 서명 검사 우회·임의 게시 행 삽입·새 key로 구형 서명을 대체하지 않는다.
**원 전체 계산의 수용은 유지하되, 후속 현재 조회에는 인증 자료를 보존한 새 전체 계산 판본이 필요하다.**

기존 PostgreSQL16.15의 정상 dump/restore와 기존 runtime/current query를 재사용했다.
[pg_dumpall 공식 문서](https://www.postgresql.org/docs/16/app-pg-dumpall.html)는
DB dump가 역할을 보존하지 않는다고 설명한다. 직접 소유한 시험 cluster의 roles-only와 custom DB를
별도로 보존하고 [pg_restore](https://www.postgresql.org/docs/16/app-pgrestore.html)로 복원했다.
DB·역할/권한·SCRAM verifier와 원 payload/서명을 유지하며 transport port/passfile만 새 config 판본에 결속했다.
외부 DB import나 일반 운영 backup/G4 수용은 아니다.

## 통과한 검증

| 대상 | 관측 결과 |
| --- | --- |
| 실제 원 계산·게시 | 작은 합성120걸음/603 RHS 호출·완료3sample/0event. 무작위 custody/DB/result key를 보존 |
| 원량·계보 | 원 record ID/payload·기록 시각·입력/artifact/증명 hash, 모든3시점/UTC/수치 일치. 이벤트는 원0건 |
| 실제 복원 | 원 DB 생존 중 별도 cluster 복원, 별도 Python 조회. 이어 원 DB/schema/role/passfile 정리 후 다시 새 cluster 복원·조회 |
| 현재 검사 | 실제 host SCRAM, 현재 권리 철회/복원·읽기 scope 철회/복원·다른 tenant 거부 |
| 반례 | 잘못된 manifest SHA·누락 DB key·dump/runtime 변조 거부. remote/inline password/혼합 passfile·권한/용량/심볼릭 링크 거부 |
| 재계산 금지 | 복원·조회 중 parser/context/QC/RHS·새 게시/증명 발행을 금지,0회. 생성 때의603 RHS와 구분 |
| 보존 용량 | 보호 raw307,294bytes≤128MiB; DB dump286,788bytes·역할2,210bytes. 입력/artifact 원 inode/path 보존 |
| 시간·종료 | 집중11개0.74초, 실제 시험69.23초, 원 DB 정리 후 복원10.192초. 전체81.287초/원900초·세 명령/원 도구 종료0 |
| WSL2 | nice19·0.1초779표본. 단일129.76MiB≤512MiB, controller/소유 PG 포함 합388.52MiB≤1GiB |
| 정리 | FD13→13·1,480 source 보존·소유 PG3개 모두 종료·남은 자식0·원 임시 디렉터리 없음 |

첫 원38071에서는 기능 자식3개가 모두 종료0이었으나 기본 pytest 임시 디렉터리가 남아
controller 종료1이었다. 소유 잔여8항목을 확인·제거하고 unit의 임시 경로를 명시했다.
같은 core 판본을 원90143에서 다시 실행해 전체 정리와 종료0을 확인했다.
첫 기능 성공만으로 최종 정리 수용을 표시하지 않았다.

중복 첫 시도 자료와 정지된 DB clone/data·unit 임시 파일167,550,554bytes를 제거했다.
**수용된 비공개 backup/runtime/입력/artifact는 후속 복원을 위해 의도적으로 보존한다.**
키·passfile·역할 SQL·DB 원본은 저장소/공개 manifest/로그에 넣지 않았다.
일반 운영 동시 처리·표본 사이 최대 RSS나 WSL 전체 용량 수용은 아니다.

## 다음 순서와 남은 조건

`crop-harvest-parent-backup` 자식만 완료한다. 전체 부모·전체 수확 writer/API/3D·replay 부모는 미완료다.

1. 기존 정상 producer로 동일 모델/입력의 **새 전체166일 계산**을 만든다. 먼저 작은 구성에서 보존까지 확인한다.
   새 판본의 모든47,809sample/5event·121상태/수지·UTC를 원 결과와 대사하고, 인증 자료와 DB를 함께 보존한다.
   별도 Python의 현재 query·권리/계정 거부와 원 종료/자원 정리를 확인한다.
2. 새 부모 source를 명시한 합성 환산/배정 profile의 새 판본으로 전체 수확 writer/등록을 검증한다.
   기존 계수·배정·수량·UTC는 대사하되 구형 source/profile/hash를 새 계보로 덮어쓰지 않는다.
   새 페이지/root hash와 용량을 별도로 기록한다.
3. 같은 저장 결과의 실제 API/대표 WebGL → 기후 결합 → 물/양분·구매 에너지 → 사용자 실행/Decimal 경제로 진행한다.

첫 복원2–4시간 추정은 인증 자료 재사용 조건이 깨져 철회한다.
새 전체 producer는 이전 실제7시간15분을 기준으로 **준비 검증 후7–9시간**의 실행·대사를 잠정 잡는다.
수확 writer/API의 완료일은 새 부모와 실제 비용을 관측한 뒤 정한다. 전체 제품 출시일은 아직 산정할 수 없다.

새 전체 계산·writer/HTTP/WebGL, 전체 Backend/web/type/build, hosted CI/push는 이번에 수행하지 않았다.
원격 마지막 판본 `2a3e615`의5개 workflow를 재조회했다.4개 성공·[Backend 실패](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/37669114958)로 종료돼 있으며 해결 완료로 표시하지 않는다.
실제 품종 입력·농장 작물 Run·국내 독립 농장 자료0건, G0/G1/G2/G3a/G3b/G4는 `not_assessed`다.
생산·미래 마진·최적 작물 추천 hold와 독립 자료 확보 병행을 유지한다.
