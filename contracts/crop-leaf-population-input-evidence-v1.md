# 출현 잎 입력의 출처·현재 검토 — v1

상태: [52집중/fresh 수용](../research/crop-leaf-population-input-evidence-20261023.md). 선행은 [저장 재생](web-leaf-population-replay-v1.md)과
[원 stem 입력 증거](crop-morphology-input-evidence-v1.md)다.

`LeafPopulationInputEvidenceAuthority`는 명시 key/issuer/key ID·현재 leaf review resolver와
기존 `MorphologyInputEvidenceAuthority`를 받는다. issue/verify는 원 leaf program/source bytes·
신뢰한 SHA·review ID/decision UTC 및 parent stem issue의 원 arguments/evidence bytes를 받는다.
클라이언트 경로·키·승인 문장을 받는 HTTP 인터페이스는 추가하지 않는다.

leaf program≤2MiB/source≤1MiB/evidence≤2MiB, parent는 기존 상한을 따른다.
source는 `leaf-population-input-source-v1`의 닫힌 program SHA/기존 SourceRecord다.
모든 원 unit 객체의 JSON 경로·단위/instant/QC와 raw SHA·품목/판본·합성 저자/방법,
발표/가용/수신·권리 선언 순서를 대사한다. forcing/출력 시각의 근거는 검증된 parent source에 보존한다.
권리·QC·검토는 leaf와 parent 각각 현재 검사한다. leaf 재배포 False는 거부 권리로 보존한다.

parent evidence는 같은 decision UTC로 검증하고 원 stem program SHA가 leaf 참조와 같아야 한다.
원 reader의 구조 검사로 같은 시간 원점·초기 시각/범위·중복 없는 명시 출현과 단위/곡선 형식을 확인한다.
**stem artifact root는 아직 식별자다.** 해당 농장/완료 job의 서명 결과와의 일치는 후속 farm binding에서 검증한다.
초기 면적/곡선의 수치 일치·생장 계산, 실제 계수/자료·농장/G0–G4 승인을 이 증거가 만들지 않는다.

새 domain/version의 HMAC은 원 bytes SHA, 두 입력 증거/검토·모델/코드 지문과 metadata를 결속한다.
leaf/parent의 현재 검토를 발급·검증 전후 재검사한다. metadata는 복사본이며 키 bytes를 반환하지 않는다.
마지막 parent 검증 후 leaf 검토를 재확인한다. 서로 다른 resolver의 원자 snapshot은 증명하지 않으며
후속 farm binding/서명 게시기는 게시 전후 현재 검사를 별도로 수행해야 한다.
기존 root/producer/reader·공개17파일·서버/DB/사용자 화면은 변경하지 않는다.

수용: 정상 원 metadata/bytes와 두 판본·재배포 False, rehash 뒤 출처/단위/권리/시각·parent 불일치,
서명/코드/모델·현재/늦은 철회 거부, 별도 fresh의 생장 import/계산·DB/CLI/쓰기0과 원 파일/FD 보존이다.
자료의 권리/품질 검토와 모델 수치 검증은 구분하며 fixture 통과를 실제 농장 검증으로 세지 않는다.
