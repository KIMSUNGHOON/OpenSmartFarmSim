# 수확 후속 작업을 위한 소유 부모 문맥 보존 v1

선행: [전체 수량·용량 대사](../research/crop-harvest-full-capacity-implementation-20261009.md).
core4: 이 계약, `research/crop-harvest-parent-backup.py`,
`backend/tests/test_crop_harvest_parent_backup.py`, `backend/tests/crop_harvest_parent_backup_smoke.py`.

## 실제 확인으로 변경된 의존성

기존 전체 작기의 DB/runtime/무작위 custody key는 정리됐다. archive와 과거 종료0 기록만으로
현재 query가 요구하는 HMAC/등록 농장을 복원할 수 없다. 구형 서명 우회나 새 key로 구형 서명을
대체하지 않는다. 기존 모델/입력의 새 전체 계산 판본이 필요하며 원 수량/UTC/hash와 별도로 대사한다.
현재 자식은 작은 실제 계산 부모에서 인증 문맥 보존/정상 복원을 먼저 검증한다.
전체 부모와 전체 writer/API/3D 수용을 대신하지 않는다.

## 경계

- 이미 설치한 PostgreSQL16.15와 기존 소유 runtime/current query를 재사용한다.
  새 제품 복구 API나 일반 외부 DB import 기능을 추가하지 않는다.
- 직접 만든 로컬 시험 cluster만 허용한다. 원 data_directory/현재 UID·PID·binary를 확인한다.
  `pg_dump` custom DB와 `pg_dumpall --roles-only`를 사용해 데이터·권한/역할을 보존한다.
  원 서비스의 쓰기를 완료한 뒤 순차 실행하며 row·원 payload·서명·권한을 임의 생성/수정하지 않는다.
- DB dump·역할 암호 verifier·passfile·HMAC key/runtime는 저장소 밖700 디렉터리에400/600으로 보존한다.
  공개 기록은 원 hash/개수·종료·권리 거부·자원/정리만 포함한다. 명령 오류의 원 stderr도 사설 파일이다.
- 입력/artifact/농장 객체 파일은 원 inode/path를 유지한다. 모델/입력·과거 증명의 raw/hash를 바꾸지 않는다.
  복원 transport의 port/passfile만 새 명시적 runtime 판본으로 변경한다.

## 수용

1. 기존 실제 SCRAM 경로에서 작은 부모를 계산·정상 게시한다. 원 record/source/UTC/값을 고정하고
   보호 runtime와 모든 필요한 인증 자료를 보존한다. 새 계산과 이후 RHS0 읽기의 계측을 구분한다.
2. 별도 소유 cluster에 roles/DB를 정상 도구로 복원한다. 실제 SCRAM/current query와 별도 Python에서
   같은 record/payload·원 sample/event·입력/artifact/proof hash를 읽는다. 복원 중 새 계산/게시/증명은0회다.
3. 현재 권리 철회/복원과 계정 거부, 잘못된 manifest/dump hash·누락 key를 거부한다.
   원 DB/파일·불변 원값을 보존한다. backup raw 합128MiB 초과는 hold다.
4. nice19·단일 RSS512MiB/소유 합1GiB·원900초 예산, 원 명령 종료·FD/PID/임시 비밀 정리를 확인한다.
   원 시험 cluster/schema/role은 정리하고, 복원 cluster는 정지한다.
   **명시적으로 보존한 비공개 backup/runtime/입력/artifact는 후속 전체 실행의 의도된 산출물**이다.
   이를 삭제한 비밀이나 일반 운영/G4 backup 수용으로 보고하지 않는다.

## 다음

작은 복원 수용 뒤 같은 보존 절차를 새 전체 작기 계산에 적용한다.
전체 원 수량/UTC·모델/입력 판본의 대사와 새 부모 source/식별자·합성 profile의 새 판본 결속을 기록한다.
그 뒤 전체 수확 writer/등록→fresh 현재권리/API·대표3D→기후/자원·경제를 진행한다.
자료 확보와 G0–G4·생산/미래 마진/추천 hold는 유지한다.
