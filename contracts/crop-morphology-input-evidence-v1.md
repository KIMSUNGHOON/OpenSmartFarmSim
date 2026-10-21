# 형태 입력의 출처·현재 검토 결속 — v1

상태: [595집중검사·실제 원 입력/fresh 검증 수용](../research/crop-morphology-input-evidence-20261022.md).

선행: [정확 출현 v2 계산/불변 저장](crop-rational-morphology-artifact-v2.md)과
[별도 저장3D](web-morphology-rational-stored-replay-v2.md). 제품의 현재 권리 조회에 필요한 첫 자식이다.
기존 v2 프로그램·producer/reader·공개15파일은 변경하지 않는다.

새 `MorphologyInputEvidenceAuthority`는 명시 trusted key/issuer/key ID와 현재 검토 resolver를 받는다.
`issue`/`verify`는 원 `program_raw`, 별도 `source_raw`, 신뢰한 두 SHA와 decision UTC를 받는다.
source는 `morphology-input-source-v1`, `program_sha256`, 기존 `provenance.SourceRecord`의 닫힌 canonical JSON이다.
program≤16MiB/source≤1MiB/evidence≤2MiB다. source 전체 SHA는 provenance/권리도 결속한다.
서명은 새 domain/version을 사용하며 키 bytes는 증거에 넣지 않는다. unsigned/fallback은 없다.

현재 reviewer/evidence/decision/source SHA/status/scope의6필드를 기존 명시 resolver 형태로 재사용한다.
scope는 합성 형태 입력의 **구조/출처 소프트웨어 검증만** 허용한다. 발급·검증 전후 현재 검토가 같아야 한다.
철회/unknown·범위/판본/원 bytes 변경은 hold다. SourceRecord의 raw SHA는 원 program bytes와 같다.
품목 ID=program ID, 판본=program schema, revision=원 권리 판본, synthetic author/method는 필수다.
권리 선언≤관측/생성≤발표≤가용≤수신≤decision UTC 순서다. 관측은 자체 입력의 생성/관찰이며
프로그램의 가상 작기 UTC를 실제 관측 시각으로 사용하지 않는다. 미래 가용 시각을 과거에 이용한 것으로 표시하지 않는다.
station/request/validity는 없는 자체 합성 자료다. SourceRecord의 content ID와 안전한 locator 검사를 재사용한다.

모든 원 수량/정확 분수·순번의 JSON 경로에 해당 원 단위가 하나씩 있어야 한다.
기온 구간은 원 UTC 경계의 mean, 나머지는 instant다. provider QC는 not_supplied이고
프로젝트 QC는 이 판본의 structural_software_contract다. 수치적 초기 상태/곡선 일치 검증으로 표시하지 않는다.
access/store/transform/display는 allowed, redistribute는 원 program의 명시 bool과 allowed/denied로 일치해야 한다.
private 재생의 재배포 금지를 허용하되 공개 export 권리를 만들지 않는다.

실제 코드 지문과 원 model/입력/초기 상태/forcing·출력 schedule, provenance/current review/decision을 결속한다.
검증 결과는 불변 bytes와 복사본 metadata, `rights_or_gate_approval=False`만 제공한다.
이는 농장 승인·생장 재실행/수치 검증·기존 artifact 신뢰 root/서명·G0–G4 해제가 아니다.
파일 운송/농장 결속·server custody·DB/API/UI는 이후 별도 자식이다. 키/DB/사용자 화면은 이번에 바꾸지 않는다.

수용: 기존 공개 원 프로그램의 units/UTC/숫자/권리·원15파일과6root 보존, 정상/재배포 금지·fresh 검증,
현재/늦은 철회·서명/ID/코드/원본/단위/QC/시각/권리 변조 거부와 경계 크기 검증이다.
발급·조회에서 성장 모듈 import/계산·DB/CLI0을 확인한다. 관련 집중 회귀만 수행하고 전체 작기/제품 완료로 세지 않는다.
