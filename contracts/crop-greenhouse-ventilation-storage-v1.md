# 환기 공동 계산의 불변 페이지 저장 v1

선행은 [새 continuation](crop-greenhouse-ventilation-continuation-v1.md)과 [원 UTC](crop-greenhouse-ventilation-time-v1.md)다.
핵심3은 `backend/app/crop_greenhouse_ventilation_storage.py`, 해당 tests, 이 계약이다.
기존 [저장 계약](crop-climate-joint-storage-v1.md)의 파일 helper·페이지/HEAD 정책을 재사용하고 새 모델/저장 판본으로 구분한다.
기존 storage·22장부 결과/프로필·코드·frozen 사용자 서버는 변경하지 않는다.

## 원 입력·결과와 파일 경계

원108상태·25연속/6사건 장부·10수지/환기 진단·source의 다른 forcing/실외 입력·원 elapsed/UTC,
context/checkpoint/prefix를 canonical source 그대로 저장한다. 새 초기 RHS/환기 묶음과4프로필 원 bytes·notice를 고정한다.
header는 source context/UTC binding·코드/정책/한도와 현재 파일 의존 SHA를 결속한다.
새 stage/program/순수 환기·구 driver/kernel·continuation helper·calendar helper도 의존 코드에 포함한다.
새 context의25장부 판본·초기 묶음과 UTC calendar helper SHA를 확인한다.

공개 함수는 `create_writer(directory,binding,initial_checkpoint)`,
`open_writer(directory,expected_head_sha256,binding,checkpoint)`, `open_artifact(directory,expected_artifact_sha256)`다.
caller가 만든 소유 directory를 받고 handle은 자기 directory/독점 lock FD만 소유한다.
writer는 확정 producer chunk를 `append(chunk,expected_chunk_sha256=...)`로 받고 terminal에서 `finalize()`한다.
reader는 `summary`와 `page(kind,start=0,limit=None)`로 원 source/time 쌍을 읽는다.
writer 재개는 원 계약으로 검증/복원한 현재 checkpoint를 받으며, 그 setup과 저장/조회 계산0을 구분한다.
독립 reader는 context/binding 생성·checkpoint 복원·RHS/환기/적분/관리를 실행하지 않는다.

파일 제어는 기존 bounded regular-file 읽기·content-addressed put·fsync·독점 writer lock·atomic HEAD helper를 재사용한다.
64sample/8event 이하·각 페이지/응답2MiB 이하이며 같은 원 source/UTC 쌍을 보존한다.
context3MiB·metadata128KiB·root2MiB·4,097commit/18page-per-commit,
directory512MiB/65,536파일(미게시 항목 포함)의 상한을 유지한다. 원128경계 내부 chunk는8MiB 이하이다.
HTTP 허용량·DB 등록/현재 권리 검사는 후속이다.

## 게시·재개·조회

원 UTC binding 검증→페이지→완전 commit→atomic HEAD 순서로 게시한다.
각 commit은 header/parent/sequence·이전 checkpoint·원 source/time metadata/hash·페이지를 가진다.
source/bound result SHA를 원 페이지 재조립으로 대사하고 같은 artifact의 cursor/prefix/UTC와 상태를 확인한다.
completed/hold에서만 전체 commit 목록·최종 상태/root를 게시한다. 실패 사건/선택 출력을 추가하지 않는다.
관리 후 환기 실패는 같은 UTC의 사건 전 마지막 확정 상태와 원 hold phase/inner stage를 저장한다.

HEAD 전 orphan/temp는 미게시이며 덮어쓰거나 삭제하지 않는다. 이미 게시된 bytes/hash를 바꾸지 않는다.
예외/중단은 handle을 닫고 새 handle이 실제 HEAD를 검증해 재개한다.
오래된 HEAD·동시 writer·혼합/불완전 게시·변조/파일 형식·원 한도 초과를 거부한다.
reader는 trusted terminal root SHA로 header/chain/page·원 프로필/context/시간/현재 코드 판본을 검사한다.
내용 재해시는 진본/권리 승인이 아니다. 이후 서버 custody가 trusted digest와 현재 농장/자료 권리를 제공해야 한다.

## 수용 기준

1. 수용된10program×예산1/7/128의 실제 writer→종료→reader에서 원 숫자/UTC·25연속/6사건/10수지/진단·checkpoint/prefix/hash를 대사한다.
2. 별도 Python reader에서 context/binding/restore·RHS/환기/적분/관리0과 원 summary/page 동일을 확인한다.
3. initial/사건 전후/완료 writer 재개·HEAD 교체 전후 실제 child SIGKILL과 남은 원 prefix의 재개를 확인한다.
   실제 interval/초기·마지막 관리/전역 수지·관리 후 환기 hold의 원 시점/확정 결과를 유지한다.
4. 구/새 artifact 혼용·새 의존 코드/프로필·trusted root/HEAD·source/prefix/hash·동시 writer/닫힌 handle·예산·symlink/FIFO/missing/oversize/늦은 변조를 거부한다.
5. 최대128sample/event chunk의 실제2MiB 페이지/응답·구 storage/새 UTC 회귀·원본/두 서버·원 종료/FD/소유 정리·WSL 한도를 확인한다.

범위는 `software_research_only`, G0_G4=`not_assessed`다.
새 입력/QC·현재 농장/자료 권리·서버 custody→결과 등록/현재 API→worker/같은 UTC3D/사용자 기동은 후속이다.
실제 품종/전체 작기 생산·구매 자원·미래 마진/추천 관문 수용은 아니다.
