# 작물·기후 원 입력 검증 증거 v1

선행은 [공동 분할 실행](crop-climate-joint-continuation-v1.md), [UTC 결속](crop-climate-joint-time-binding-v1.md),
[불변 저장](crop-climate-joint-storage-v1.md)이다. 이전121상태의 입력 authority/context로 위장하지 않는다.
이 증거는 합성 입력의 초기 수학/QC 검사를 인증한다. 실제 출처 권리·G0 채택·현장 G2·미래 생산/마진/추천이나
농장/테넌트의 현재 계산·표시 권한을 승인하지 않는다. 실제 자료의 권리·vintage·시각 검토는 별도 경로다.

## 원본과 검토

caller가 만든0700 소유 directory의 닫힌 파일 집합을 받는다. `source.json`,
`growth.json`, `cohort.json`, `transport.json`, `exchange.json`, `notice.txt`만 허용한다.
원본은0400·현재 euid·단일 hard link인 regular file이며, directory의 모든 경로와 파일은 nofollow로 연다.
기존 bounded secure-file/metadata/strict-JSON 함수만 재사용하며 이전 모델 입력 parser/context는 사용하지 않는다.
원본 JSON1MiB·각 profile/notice128KiB·증거 전체2MiB 상한이며 중복 키/nonfinite/비정규 JSON은 거부한다.

`source.json`은 `version=joint-crop-climate-input-source-v1`, `scenario`, `events`, `output_steps`,
`step_seconds`, `step_count`, `time_origin`의 닫힌 canonical JSON이다. 모두 `synthetic`이며
원 단위·108상태·최대4096걸음/600초·128사건/512출력·UTC 정밀도는 선행 계약을 따른다.
4프로필은 이미 고정된 reference 원 bytes이며 notice도 정확한 원 bytes다. 임의 계수를 채택하지 않는다.

신뢰한 caller의 `review_resolver(evidence_id)`는 현재 검토 저장소에서 닫힌
`evidence_id, reviewer_id, decision_id, source_sha256, status, scope`를 반환한다.
ID는 ASCII `[A-Za-z0-9][A-Za-z0-9._:-]{0,127}`, status는 `accepted_for_software_validation`,
scope는 `synthetic_input_math_validation_only`다. 검토는 자유 형식 CLI 제안 자체의 승인이 아니다.
현재 resolver의 결정·검토자·원본·범위 변경, 삭제/철회/오류는 hold다. DB나 새 검토 서비스를 추가하지 않는다.

## 발급과 현재 조회

`JointInputEvidenceAuthority(integrity_key=..., issuer_id=..., key_id=..., review_resolver=...)`를 만든다.
키32–4096bytes는 신뢰한 서버 caller가 제공하며 원본·증거·브라우저·공개 manifest에 넣지 않는다.
`issue(directory, expected_source_sha256, binding=original_binding, review_id=...)`는 현재 원 bytes/검토를 확인하고
원 입력에서 새 context를 한 번 준비해 원 program/초기108상태·초기 RHS/manifest와 원 UTC binding에 정확히 대사한다.
초기 RHS1회이며 시간 결속0회·진행 적분/관리 사건0회다. 원본과 검토를 반환 전에 다시 검사한다.

HMAC-SHA256의 별도 domain/version에 issuer/key ID·검사 UTC·schema/QC/정규화/현재 코드·의존성·Python/수치 환경,
6파일 SHA·검토/결정 ID·초기 상태 hash·원 context/initial RHS·UTC binding을 결속한다.
`verify(directory, expected_source_sha256, evidence_raw, expected_context_sha256=..., expected_binding_sha256=...)`는
신뢰 경로의3개 expected SHA와 HMAC·현재 코드/파일/검토를 검사한다. 전체 초기 수학/QC를 다시 실행하지 않는다.
새 Python에서도 context/binding 생성·RHS·걸음·사건·복원0회다. 검증된 record는 복사본이며 `rights_or_gate_approval=False`다.

같은 키/issuer/key ID·현재 원 bytes/검토/코드/환경에서만 재기동 검증을 허용한다. 키 교체/유실의 무서명 fallback은 없다.
검증 결과는 검증 호출 시점의 사실이며 무기한 권한 cache가 아니다. 후속 농장/서버 custody는 게시/표시 직전과 직후에
현재 검증을 다시 호출해야 한다. 서버 키나 신뢰한 resolver가 손상된 공격까지 증명하는 형식은 아니다.

## 수용

9개 수용 프로그램의 원 context/seed·profile/notice·UTC 보존, 발급 초기 RHS1회/조회0회·별도 Python0회를 확인한다.
변조/서명/비정규·bounds·다른 입력/seed/time/model/code/profile/검토·키/설정·철회와 발급/검증 중 변경을 거부한다.
파일 누락/추가/symlink/hardlink/FIFO/mode·경로/FD·원본/원 종료/WSL 자원 보존을 확인한다.
현재 농장/자료 권리→서버 custody/등록→API→같은 UTC3D→사용자 실행/U3는 후속이며 이 자식으로 완료 처리하지 않는다.
