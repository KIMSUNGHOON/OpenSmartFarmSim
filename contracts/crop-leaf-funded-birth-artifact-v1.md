# 조달된 새 잎 전후/재개의 불변 저장과 무계산 조회 — 연구 v1

상태: **합성 저장/무계산 조회 수용** — [59검사·fresh6결과/42시점](../research/crop-leaf-funded-birth-artifact-20261026.md). [수용한 실제 재개](crop-leaf-funded-birth-continuation-v1.md)의 저장 자식이다.
기존 MorphologyBlobStore/ContentAccess와 순수 stock schema 검사를 재사용한다.
모델/DB/키/서비스를 새로 만들거나 기존 fixed-list artifact를 새 형식으로 위장하지 않는다.

`produce_funded_leaf_artifact(directory,access,*,inputs_raw,**profiles)`는 닫힌 canonical JSON을 받는다.
schema_version=`funded-leaf-artifact-input-v1`, input_id, origin=`synthetic`, rights,
time_origin_utc, step_seconds, step_count, program, births다. 원 root의 권리/합성 epoch/정책·단위와
4profile/notice는 기존 stock artifact 계약을 따른다. redistribute=False를 True로 바꾸지 않는다.
births는1개 이상이며 각 항목은 step_index와 **원 point_inputs**다. 같은 index의 여러 batch는
배열 순서를 보존한다. 원 context/현재 CP SHA·정확 시각·floor/새 초기 C/A/clock·사건/부착 ID와
조달 정책을 미리 명시해야 한다. producer는 누락된 hash/질량/부착을 채워 원 입력을 바꾸지 않는다.

root 원 요청/정규 program/manifest/seed·초기 영수증, 원 profile4/notice와 각 시점의 raw CP,
각 점의 원 calculation result/동결 funded context bytes를 CAS에 저장한다.
현재 CP 검증→수용한 공유 point 산술→수용한 context capture를 각각1회 사용하며
독립 public 모델 경로와 같은 결과임을 대사한다. 시간은 원 dt/전역 index로 계속 전진한다.
원/점/segment/lifetime 장부·이력/코드/profile/모든 source bytes를 재확인한 뒤 root를 마지막에 게시한다.
부분 쓰기/domain/권리/source hold에는 완료 root를 반환하지 않는다.

전체 frame은 count+1+len(births)개다. root CP는 phase=root_interval/사건번호0이고,
새 CP는 원 after_birth 또는 funded_birth_interval/원 사건번호를 그대로 보존한다.
각 descriptor는 별도 index/원 global index/phase/event_sequence, exact Fraction elapsed,
원 sample/state/raw CP SHA와 직전 **전체 frame**의 CP SHA를 결속한다.
같은 시각의 다른 point를 병합/보간하지 않는다. epoch는 합성 표시 기준이며 관측/available_at이 아니다.

입력/단일 source/root·funded context2MiB, CP1MiB, frame≤512,
전체 실제 frame별(115+5n) 합≤32,768scalar와 원600초·store64MiB/4096파일 한계를 유지한다.
새 root schema=`funded-leaf-research-artifact-v1`, DTO=`funded-leaf-replay-frame-v1`다.

`read_funded_leaf_manifest`/`read_funded_leaf_frame(...,index=...)`는 외부가 신뢰한 private root를 받는다.
reader는 생장/조달점/재개/producer를 import/실행하지 않는다. 닫힌 schema·원 source/hash/rights/code,
root와 각 사건의 context/CP·입력/영수증·단위/shape/QC·clock/phase/order/prefix/현재 장부를 검사한다.
원 file policy/source rights/code를 반환 직전에 재확인한다. 생장식·질량/열수지를 다시 계산하지 않는다.
DB/CLI/network/쓰기0이며 hash 재작성은 권한/자료/방정식 진본의 증명이 아니다.
실제 tenant/farm 현재 권리/서명 custody는 상위 계층의 후속 관문이다.

DTO는 원 sample/CP·current state/layout와 leaf ID/C_i/a/A, 초기 또는 새 구조 생성 영수증,
원 clock/birth basis/point input의 declared attachment ID·각 장부를 복사한다.
원 잎의 attachment는 별도 자산, 새 ID도 declared_not_bound로 표시한다.
초기 aged 잎을 이 시각에 생물학적으로 출현한 잎으로 바꾸거나 부착 위치/키/과실/수확/마진을 만들지 않는다.
권위는 저장 A와 원 상태이고 strict SDK/실제 새 잎3D는 다음 단계다.

수용: 원6조건·초기/중간/끝/같은 시각/복수 점, 모든 CP/sample/수량·ID/정확 시각/각 장부/영수증,
같은 입력/다른 directory의 같은 root·원1→2/512잎·fractional dt·rights/변조/상한/부분 실패,
현재/늦은 file/source/code 정책·index/copy/FD와 원 자료/WSL을 검사한다.
별도 producer 뒤 fresh reader에서 전체 raw/DTO를 대사하고 모델 import/생장·점 계산/DB/CLI/network/쓰기0을 계측한다.
software_research_only/G0_G4=not_assessed이며 실제 품종/독립 자료·빈 수관/제거·공급 제한 A·작기/생산/자원/경제/
거시·수급/자율 비교·제품 통합/R2를 승인하지 않는다. 자체 합성 저장과 원 farm/source-clock·부착 결속은 병행한다.
