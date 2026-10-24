# 저장 잎 생애 결과의 SDK와 현재 잎 adapter — v1

상태: 계약/검증 중. [원 결과](crop-leaf-lifecycle-artifact-v1.md)와 [연구 export](crop-leaf-lifecycle-export-v1.md)를 사용한다.
`loadLeafLifecycleReplay(scenario,signal)`은 `no-removal`/`with-removal`의 자체 합성20파일씩만 읽는다.
공개 fixture의 원 bytes를 복사하고 index/root SHA·40code·모델/표시 정책·선언 ID/출현/제거 시각을 고정한다.
임의 URL/농장/API/생장 계산·CLI/POST는 없다. 원 scope/claim/gates는 미평가 연구 범위다.

loader는20파일 각각의 SHA/bytes·닫힌 index/root/source/frame schema와 연결을 검사한다.
source 권리3종은 별도로 확인하며 원 두 program/준비/초기 state/stem root/program을 대사한다.
원12시점/원 UTC의 입력/출력 state chain과 같은 UTC stem, active/removed/pending의 ID/순서/개수·정확 시각/단위,
개별 원 면적·저장 합계를 검사한다. 합계 검사만 유한 양수의 JS 합산 반올림 범위 `EPSILON × 항 수 × 합계`를 허용하며
저장된 면적·합계를 수정하거나 생장을 계산하지 않는다. 빈 현재 합계는 정확0이다.

`decodeLeafLifecycleFrame(value,descriptor,root,scenario)`는 선택 DTO의 구조/참조 검증기다.
원 bytes/hash의 신뢰는 loader가 제공한다. 순수 decoder 호출 자체가 bytes 인증·농장 권한·관문 승인은 아니다.
제거 잎의 나이/면적은 제거 시각의 마지막 값이며 현재 시각의 면적으로 합치지 않는다.
pending은 예약 ID/부착/출현만 제공하며 현재 형상/면적을 만들지 않는다.

`activeLifecycleLeafBinding(frame)`은 현재 active 잎만 기존 MorphologyScene의 구조적 입력으로 복사한다.
원 stem/UTC·artifact/result SHA와 leaf ID/부착/면적을 유지하며 입력을 수정하지 않는다.
removed/pending은 원 DTO에 별도로 남는다. 빈 active adapter는 빈 목록이며 고정 외형 잎으로 대체하지 않는다.
기존 도형 생성기의 빈 목록 거부 해소와 실제 삼각형/표/그래프·React/브라우저 검증은 다음3D 자식이다.

수용은 두 원 결과의24 DTO/94추적 상태·40파일 SHA 보존과 active 투영,
변조/혼합·권리/단위·선언/시각/개수/합계·확장 필드 거부, 부족/초과2MiB/중간 및 마지막 abort의 대체 결과0이다.
기존 SDK/타입/화면·WSL 보호를 확인한다. 실제 HTTP/fresh 검증은 UI/브라우저 또는 G1/G4 수용과 구분한다.
