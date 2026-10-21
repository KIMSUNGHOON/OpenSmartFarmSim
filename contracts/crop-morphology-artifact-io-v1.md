# 형태 연구의 내용 주소 파일 보관 — v1

상태: 파일 운송 새14/기존272검사 수용. [기존 POSIX/JobStore 선택](../docs/TECH_STACK.md#최소-운영-구성-결정표)을 재사용한다.
이 저장소는 **내부 합성 연구 artifact의 파일 운송**이며 농장/테넌트 ACL·등록/권리·Run 승인이 아니다.

`MorphologyBlobStore(directory, access, *, write=False)`는 절대 경로/명시 ContentAccess를 받는다.
디렉터리750/파일640·명시 owner/group과 ACL 없음 정책을 기존 JobStore/ContentAccess로 적용한다.
writer는 디렉터리의 비차단 배타 flock을 보유한다. reader는 쓰기 없이 같은 디렉터리를 연다.
경로 각 요소의 symlink, 디렉터리 교체, 파일 symlink/비정규/hardlink·권한/소유/ACL 변경은 hold다.
reader의 파일 크기/metadata를 읽기 전후 대사하고 SHA-256과 원 bytes를 검사한다.

`put(raw, *, maximum)`는 최대16MiB 안에서 원 JobStore의 동기화·원자 no-clobber 내용 주소 파일 저장을 쓴다.
같은 bytes 재보관은 같은 digest를 반환하고 기존 bytes/mtime를 덮어쓰지 않는다.
`get(digest, *, maximum)`는 해시 이름의 원 bytes만 읽는다. bool/범위 밖 상한·잘못된 SHA·파일은 거부한다.
최대4096파일/64MiB의 디렉터리 예산을 유지하며 새 저장의 임시 파일 여유를 보수적으로 확보한다.
같은 OS owner의 악의적 전체 재작성까지 인증하는 서명/권한 체계는 아니며 trusted root는 상위 계약이 공급한다.

DB/API·큐·일반 농장 저장 권한은 사용하지 않는다. 연결 호출0, 별도 프로세스 읽기·원 bytes,
동일 재보관/동시 writer 거부, 파일/경로 변조·권한/크기·FD 정리와 기존272수치검사를 확인한다.
형태 producer/typed reader·불변 root와3D 연결은 다음이며 농장 현재 권리는 기존 제품의 별도 관문이다.

[원 수용/실행 범위](../research/crop-morphology-artifact-io-20261022.md).
