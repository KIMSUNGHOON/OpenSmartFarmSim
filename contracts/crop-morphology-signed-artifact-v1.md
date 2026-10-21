# 등록 형태 계산의 완료 artifact·현재 조회 — v1

상태: 제어30/관련653검사 통과. 실제 SCRAM/fresh 검증은 진행 전이며 부모는 아직 미수용이다.

선행: [현재 농장/입력 결속](crop-morphology-farm-binding-v1.md)과
[v2 수치 producer/불변 저장](crop-rational-morphology-artifact-v2.md).
이 자식은 완료 계산의 서버 증거를 만든다. DB 결과 등록·접수/재시도/worker·제품 UI는 뒤따르는 자식이다.

`MorphologyArtifactAuthority`는 정확한 farm binding·서버 소유 blob directory/ContentAccess·명시 key/issuer/key ID를 받는다.
조회 모듈과 계산 producer 모듈을 분리한다. 새 서명 domain/version을 사용하고 기존 수치 root/17코드·프로그램은 보존한다.
기존 MorphologyBlobStore의0700/0400·nofollow/single-link·SHA/원자 기록/64MiB/파일 수 상한을 사용한다.
원 program16MiB/source1MiB/evidence2MiB/binding2MiB/root128KiB·서명 증거128KiB 한도다.

계산 호출은 현재 prepare → 원 v2 producer → 전 프레임의 기존 readonly 검증 → 현재 write 결속 재검사 →
새 signed 완료 증거 저장/마지막 재검사 순서다. 원 program/source/evidence/binding bytes와 수치 root를 내용 주소로 연결한다.
원 numerical root의 program/초기 상태·9모델/17코드는 검증된 binding과 같아야 한다.
서명에는 tenant/study/farm binding·입력 지문/수치 root·실제 calculated_at UTC·새 코드/issuer/key ID를 묶는다.
calculated_at은 모델 구간/판단 시각과 분리한다. 새 계산 호출은 새 계산 시각을 갖고 원 수치 root는 재현 가능하다.
입력/계산/현재성 실패는 결과 ID를 반환하지 않으며 남은 private 객체를 게시된 Run으로 세지 않는다.

`read_manifest(tenant,result_sha256)`와 `read_frame(...,index)`는 원 서명/파일과 현재 농장·입력 검토/표시 권리를
전후 검사하고 같은 원 수치 root/UTC·기관별 원 길이/정확 출현 초를 조회한다.
조회에서 producer/생장 모듈 실행·CLI/DB쓰기0, 원 calculated_at·결과 ID/해시는 그대로다.
원 DTO는 wrapper 안에 보존하며 원 frame canonical SHA와 result/manifest lineage를 제공한다.
현재 철회·변조·미지원 code/version/tenant·잘못된 index/크기·서명은 hold이고 이전 결과로 fallback하지 않는다.

범위는 synthetic morphology software calculation이다. 원 source/farm 구조 검토의 수치 검증=False는 보존하고,
수치 producer가 실제 실행한 사실과 계산된 원 root를 별도로 증명한다. 등록 품종 적용/실제 키·잎/과실/생산·경제,
G0–G4·독립 농장 검증을 승격하지 않는다. 서명 증거는 실제 Run/DB 게시 이력이나 중단 재개/접수 멱등성을 대신하지 않는다.

수용: 실제 정상 producer/12원 프레임·전체 원 bytes/UTC/정확 초·코드/원 수치 root 재현,
실제 SCRAM/fresh 현재 조회의 계산/쓰기0·원 시각/ID, 잘못된 초기 길이·현재/늦은 철회/서명·파일·경로/원본 변조 거부,
예외 뒤 공개 결과 없음·원15파일/DB 행/6root·WSL 상한/소유 정리다.
같은 수치 root를 임의로 서명하는 별도 attach/import 경로는 제공하지 않는다.
