# 작물·기후의 불변 페이지 저장 v1

선행은 [분할 실행](crop-climate-joint-continuation-v1.md)과 [원 격자 UTC](crop-climate-joint-time-binding-v1.md)다.
원108상태·연속22/사건6장부·원 elapsed/UTC·context/checkpoint/prefix를 그대로 저장한다.
기존 [artifact 파일 제어](crop-cycle-artifact-v1.md)의 bounded regular-file 읽기·독점 lock·content-addressed put·
fsync/atomic HEAD 게시만 정적 메서드 참조로 재사용한다. 원 계산 writer/상태 형식으로 위장하지 않는다.
새 code/dependency/limits와 source context·4프로필 원 bytes·원 notice·UTC binding을 header에 고정한다.

## 파일과 실행 경계

공개 함수는 `create_writer(directory,binding,initial_checkpoint)`,
`open_writer(directory,expected_head_sha256,binding,checkpoint)`, `open_artifact(directory,expected_artifact_sha256)`다.
directory는 caller가 만든 소유 directory다. writer의 `append(chunk,expected_chunk_sha256=...)`/`finalize()`,
reader의 `summary`/`page(kind,start=0,limit=None)`를 사용한다. handle은 자신의 directory/lock FD만 소유한다.
writer 재개는 caller가 원 모델 계약으로 검증/복원한 정확한 현재 checkpoint를 받는다.
그 setup RHS와 순수 저장 호출0회를 구분한다. 독립 reader는 binding/context 생성이나 checkpoint 복원 자체를 하지 않는다.
page는 같은 artifact의 현재 선택 범위 원 source/time 쌍을 반환하며 samples64/events8·전체2MiB 이하를 검사한다.

writer는 이미 확정된 producer chunk를 전달받는다. 저장/읽기는 RHS·적분·관리 사건·checkpoint 복원을 실행하지 않는다.
원 producer SHA와 binding SHA는 신뢰 경로가 제공해야 하며 다시 만든 hash 자체가 진본/권리 승인은 아니다.
순서는 원 binding 검증→64sample/8event 이하·각2MiB 이하 페이지→완전 commit→atomic HEAD다.
같은 source/time 쌍을 분리해 새 값을 보간하거나 계산하지 않는다. source/bound result SHA는 원 페이지 재조립으로 대사한다.

HEAD는 현재 header·최신 commit/sequence·terminal root를 가리킨다. 각 commit은 원 이전 checkpoint·parent/sequence와
원 source metadata/hash·시간 metadata/result hash·두 종류 페이지를 가진다.
completed/hold에서만 전체 commit 목록/최종 상태의 불변 root를 게시한다. 실패한 사건/선택 출력은 추가하지 않는다.
HEAD 전의 orphan/temp는 미게시이며 삭제/덮어쓰지 않는다. 이미 게시된 root/hash를 변경하지 않는다.
예외/중단 시 handle을 닫고 실제 HEAD를 새 handle에서 검증해 재개한다. 오래된 HEAD·동시 writer·혼합/불완전 게시는 거부한다.

독립 reader는 신뢰한 terminal root SHA에서 닫힌 header/chain/page·원 profile/context/hash·UTC와 현재 코드 판본을 검사한다.
모델 context/checkpoint 객체를 만들어 수치 재검증하지 않고 저장된 값을 읽는다. reader에는 새 물리 입력을 전달하지 않는다.
외부 source/custody 승인과 현재 계정/권리·DB/API·3D·실시간 U3는 후속이다. 이 모듈이 관문을 승인하지 않는다.

내부 context blob3MiB·metadata128KiB·root2MiB·최대4,097commit/18page-per-commit,
directory512MiB/65,536파일(미게시 항목 포함)의 상한을 적용한다. 원128경계 chunk8MiB 상한도 유지한다.
HTTP 경로는 아직 없으며 후속 API는 응답 전체2MiB를 별도 검증한다.

## 수용

기존9프로그램/여러 chunk의 실제 writer→종료→fresh reader에서108상태/22/6/수지·원량/UTC·checkpoint/prefix/hash를
대사한다. 처음/중간/마지막 사건과 실제 hold, 최대128sample/128event 묶음·실제 페이지 byte를 포함한다.
중간 writer 재개·원 HEAD 전후 실제 child 중단·불완전 게시/변조·shape/시간/모델/코드 혼합,
symlink/FIFO/missing/oversize/동시 writer/닫힌 handle·budget을 검사한다. 원본/FD/소유 정리·원 종료/WSL 상한을 확인한다.
소프트웨어 합성 범위이며 실제 품종/독립 농장 입력과 G0–G4·생산/자원·경제 예측/추천은 보류다.
