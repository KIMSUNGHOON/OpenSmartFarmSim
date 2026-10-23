# 출현 잎의 서버 계산·서명과 현재 조회 — v1

상태: [집중36/실제 SCRAM2·fresh 수용](../research/crop-leaf-population-signed-artifact-20261023.md).
선행은 [현재 farm/완료 parent 결속](crop-leaf-population-farm-binding-v1.md)과
[원 population 수치 저장](crop-leaf-population-artifact-v1.md)이다.

`LeafPopulationArtifactAuthority`는 정확한 leaf farm binding·서버 소유 별도 directory/
ContentAccess·key/issuer/key ID를 받는다. parent directory와 분리하고 기존 POSIX 저장의
0700/0400·nofollow/single-link·SHA·원자 쓰기와64MiB/파일 수 상한을 사용한다.
leaf program2MiB/source1MiB/evidence2MiB/binding2MiB·서명128KiB/응답2MiB다.

producer는 현재 prepare→기존 population producer1회→원 manifest/전 frame 검증→현재 write 재검사→
원 packet/binding과 새 domain의 signed 증거 저장→마지막 현재 재검사 순서다.
원40blob/28코드·초기/출현·parent stem root/12시점은 변경하지 않는다.
서명은 tenant/study·farm binding/입력·원 population root, parent job/result/root와 calculated_at UTC·현재 코드를 묶는다.
실패는 결과 ID를 반환하지 않으며 남은 private 객체를 게시 Run으로 세지 않는다.
unsigned 결과를 임의로 attach/import하는 발급 경로는 제공하지 않는다.

read_manifest/read_frame/read_replay는 원 서명·파일과 현재 farm/양쪽 source 검토·표시 권리를 전후 확인한다.
replay는 원 manifest/전체 frame을 한 현재성 경계와2MiB 안에 반환한다. 일부만 승인된 것으로 반환하지 않는다.
원 program SHA·초기/출현 입력 지문·모델/28코드·정확 시간 원점/부착/면적과 parent 참조가 같아야 한다.
최초 calculated_at/result/root와 원 DTO bytes 의미를 유지하며 조회에서 producer/생장 import·계산/CLI·DB/파일쓰기0이다.
철회·원본/서명/모델/코드·잘못된 tenant/index/용량·마지막 frame 뒤 변경은 hold이고 fallback은 없다.

서명은 합성 소프트웨어 계산과 lineage 증거다. 실제 품종 적용/초기 관측·생물학적 검증,
G0–G4와 leaf DB 게시/접수 멱등·취소/worker·HTTP/제품3D의 수용은 별도다.
서로 다른 파일/DB/resolver의 원자 snapshot은 주장하지 않으며 후속 게시기가 현재 검사를 다시 수행한다.

수용: 실제1회 producer·원 root/12frame/52면적·40blob 재현과 parent 보존,
잘못된 초기 면적·현재/늦은 철회·서명/파일·링크/원본/코드/참조 변조·범위/한도 거부,
실제 SCRAM/fresh manifest/frame/replay의 import/계산·CLI·DB쓰기/파일쓰기0·원 시각/ID·FD·원 행/2서비스/WSL 상한·소유 정리다.
