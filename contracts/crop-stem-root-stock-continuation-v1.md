# 기관별 재고·면적·기후를 보존하는 분할 재개 — 연구 v1

상태: [신규148/관련201·349검사·별도6문맥/18CP 수용](../research/crop-stem-root-stock-continuation-20261027.md)의 합성 분할 재개. [새 공동 적분](crop-stem-root-stock-dynamics-v1.md)의 같은 식·격자·한계를 유지한다. 일반106+3n+m 상태와21+3n+3m 누적량, 현재 잎/줄기·뿌리 C_i·면적/나이·기후·초기 D0를 보존한다. aggregate leaf/stem_root를 따로 적분하거나 현재 재고/면적을 초기값으로 재맞추지 않는다. 농장 UTC/출현/관측·작기/예측/추천 승인은 없다.

`prepare_context(program=...,step_seconds=...,step_count=...,**profiles)`는 처음에만 초기 정규화/RHS를 수행한다. 원 요청·정규 program·seed(상태/첫 RHS/초기 면적 영수증/D0)·manifest는 각각 immutable canonical bytes다. 새 engine/schema·원 short/component code·4profile/float 환경·dt/count·상태/flux 단위·기관 ID/순서·명시 floor/정책을 결속하며 context 합2MiB/총600초/32768scalar를 유지한다. Context/Checkpoint는 각각 frozen typed handle이며 반환 dict는 복사본이다.

`start(context)`는 seed에서 최초 확정 sample/0장부/prefix CP를 만들며 추가 RHS0이다. `advance_chunk(context,checkpoint,step_budget)`는 정수1–128걸음이다. 현재 endpoint를1회 평가/검증한 뒤 걸음마다 새4stage를 수행한다. `checkpoint_bytes(context,checkpoint)`는 같은 context의 원 bytes를 준다. `restore_checkpoint(context,raw_bytes,expected_sha256=...)`는 **외부가 신뢰하는 원 bytes SHA**를 필수로 받는다. 다른 프로세스는 같은 원 요청/코드/profile/환경의 context를 만든 뒤 현재 CP를 복원한다.

CP는 새 version/context SHA·step_index·cursor=index+1·원 sample prefix SHA·현재 sample·모든 global/perleaf/perstem 누적량·원 seed 기준 잔차/예산을 닫힌 canonical JSON으로 보존한다. 상한512KiB다. 과거 sample을 다시 적분하지 않고 신뢰한 prefix를 보존한다. 자체 재해시가 진본을 증명하지 않으며 권한 있는 저장/서명 서버가 expected SHA를 공급하는 경로는 후속이다. Python 내부 필드 재작성의 보안 경계가 아니다.

비canonical/중복 key/잘못된 UTF8/비유한·누락/여분·다른 schema/context/격자·벡터 길이/float 타입·유량 단위/시각/현재 파생량/D−D0·장부/반올림 예산·코드/profile/environment 변경을 거부한다. 현재 검증은 새 short의 RHS1회/순수 sample·장부 helper만 사용하고 초기 정규화/과거 전진0이다. 원 요청/초기 영수증/seed와 현재 C_i/A/원 기관·분모를 보존하며 모든 수용한 분할에서 원 short와 sample/상태/누적량·잔차/예산 및 최종 CP bytes가 같아야 한다. 실행 시각·chunk 크기·복원 횟수는 payload identity에 포함하지 않는다.

입력/context/CP/budget 오류는 `ContinuationRejected`이고 전진0이다. 완료 CP는 복원 가능하나 재전진은 거부한다. 새 단계의 수치/domain/장부/부분 실패는 hold·실패 step/stage·마지막 확정 sample/장부와 checkpoint=None만 반환한다. 미확정 상태/CP 게시·clipping·재초기화0이며 cancel/crash/외부 예외를 수치 hold로 바꾸지 않는다. 하위512KiB와 기존512기관/원512잎 byte hold도 유지한다. DB/CLI/network/쓰기0, scope=software_research_only, claim=synthetic_stem_root_stock_continuation_only, G0_G4=not_assessed다.

수용: 원6조건의4step 모든 composition/대표32초의 모든 단일 cut·여러 chunk 예산·초기/중간/완료 trusted canonical roundtrip와 fresh 별도 프로세스 같은 context/raw SHA·이어 계산, 실제 개별 C/현재 A/D0·전체 누적량·동일 최종 bytes·호출 수/과거 replay 차단·반환 복사·malformed/current 변경/실패 prefix·최소/실제기관 cap/CP/context/step/scalar 상한·원 코드/자료/GUI/WSL 보존이다. 실제 품종/독립 농장·전체 작기/생산/자원·경제/3D 연결과 G0–G4는 별도다.
