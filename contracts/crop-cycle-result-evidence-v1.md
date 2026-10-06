# 원 terminal 결과 검증의 서버 영수증 — v1 후보

2026-10-06 KST. [확정 과거 결과 비용](../research/crop-cycle-result-prefix-read-cost-observation-20261006.md)을
근거로 전체 결과 조회의 반복 검증을 분리한다. 원 [artifact 계약](crop-cycle-artifact-v1.md),
[입력 영수증](crop-cycle-input-evidence-v1.md), [조회 문맥](crop-cycle-input-read-context-v1.md)을 따른다.
원 계산 판본·artifact·53개 실행 소스는 유지한다.

3 core파일: `backend/app/crop_cycle_result_evidence.py`,
`backend/tests/test_crop_cycle_result_evidence.py`, 이 계약.
기존 terminal artifact와 입력 조회의 로컬 수용 뒤 자작 작은 완료/hold 사례로 개발할 수 있다.
원 전체166일 실행과 병행하되 실제 전체 결과/부모 수용은 그 종료와 후속 실제 경로 증거를 기다린다.

## 인터페이스와 발행

`ResultEvidenceAuthority(input_authority, *, integrity_key, issuer_id, key_id)`는 정확한
`InputEvidenceAuthority`와 서버 제공 영수증 전용 키/ID를 고정한다. 새 키 서비스·DB 표는 만들지 않는다.
별도 판본/코드 hash와 HMAC domain을 사용하며 키를 JSON/로그/브라우저에 넣지 않는다.

`issue(result_directory, artifact_sha256, input_directory, input_root_sha256, input_evidence_raw)`는
현재 입력 증명을 대사하고, 실제 원 `InputPacket`/`prepare_context`와 원 `open_artifact`를 호출한다.
원 initial·clock·step/cursor·출력/사건 prefix·수지·모든 commit의 검증을 통과한 terminal root만 받는다.
원 객체의 private token/캐시를 구성하거나 새 코드가 원 계산을 수행했다고 재표시하지 않는다.
원 `completed`/`hold`와 확인된 과거·보류 사유를 그대로 보존한다. RHS는 실행하지 않는다.

발행 전후에 같은 result HEAD/terminal root·입력/context·참조 파일/전체 bytes와 디렉터리 inode를 대사한다.
결과 영수증에는 원 math manifest와 code/profile/notice/Python, HEAD/header/root hash,
원 summary·page index/counts, 정확한 참조 inventory/byte 합, 검증 시각·issuer/key ID를 서명한다.
검증되지 않은 부가 파일이나 바뀐 HEAD를 승인하지 않는다. 제어 파일은 기존 artifact의
HEAD 및 소유한0byte writer-lock만 별도 파일 계약으로 허용한다.

증명은 **최대8MiB인 새 사설 canonical JSON 후보**다. 관측 prefix의 index/inventory 합은
2,875,101bytes이며 전체 작기 proof 크기는 실제 종료 결과로 검증해야 한다.
초과하면 발행/조회 hold이며 index나 원 출력을 자르지 않는다. 기존 artifact512MiB/파일·commit 한도와
공개30초/2MiB·sample64/event8을 바꾸는 수용이 아니다. 영수증은 bytes로 반환하며 원 결과 디렉터리에 쓰지 않는다.

## 재조회와 신뢰 경계

`verify(result_directory, artifact_sha256, input_directory, input_root_sha256, input_evidence_raw, evidence_raw)`는
닫힌 canonical schema·판본/서명/issuer/key ID를 먼저 검사한다. 현재 source/profile/notice/Python·
입력 authority/context, result 디렉터리 inode·HEAD/root·모든 참조 파일의 현재 bytes/SHA·정확한 inventory와
원 bytes/files 한도를 대사한다. 원 전체 parser/`prepare_context`/artifact 수지 검증을 다시 실행하지 않는다.
성공 시 불변 `VerifiedResultEvidence`를 반환한다. summary/index/identity/context는 독립 JSON 사본이다.

파일은 기존 서버 소유 no-follow/0700·0400 regular/단일 링크·ACL/읽기 전후 metadata 규칙을 따른다.
미래 변조나 키/프로세스 침해의 증명은 아니다. 후속 typed reader는 실제 page를 읽을 때 다시 SHA와
보안 조건을 확인하고, 공개 반환 전 입력/결과 증명을 재대사해야 한다.
새 증명의 판본/source가 달라지면 원 증명을 묵시 전이하지 않는다. 같은 서버 키/ID를 보존한
별도 Python에서도 재조회되며 키/ID 분실·교체는 fallback 없이 거부한다.

`rights_or_gate_approval`은 false다. primitive는 농장/current Scope·등록·권리·DB row·서버 custody trace를
승인하지 않는다. 순수 참조 결과의 증명으로 농장 계산 이력을 만들어 내거나 기존 서버 progress로
바꾸지 않는다. 원 현재 권리와 실제 서버 계산 이력을 연결한 후속 단계에서만 제품 경로로 사용할 수 있다.

## 수용과 다음 단계

1. 자작 작은 정상/hold terminal에서 원 summary/index/counts·원 계산 manifest/clock/121상태·prefix를
   원 reader와 대사한다. 비terminal·입력/결과 불일치·원 수지/shape 실패는 발행 거부한다.
2. 서명/판본/키/code/profile·비정규/중복/NaN·한도·root/blob 변조/누락·파일 보안/교체·
   발행 중 HEAD 변경을 거부한다. 실패/재시작/close의 FD 정리와 원 parser/RHS 재실행 없는 검증을 확인한다.
3. 별도 Python의 같은 키 재시작과 actual issue/verify wall/CPU/RSS/bytes/FD를 기록한다.
   원166일 종료 뒤 같은 원 전체 result의 발행/크기/모든 bytes를 대사해야 전체 결과 범위를 수용한다.

사용자 산출물은3 core파일, 집중 검증·실제 비용/비밀 없는 receipt다.
다음은 증명을 소비하는 별도 typed result reader → 현재 farm/Scope/등록/권리·원 custody/API 연결 →
전체 저장의 같은 ID/UTC3D·정리다. 전체 [복원/부하](crop-cycle-burden-v1.md) 수용 전에는 부모를 체크하지 않는다.
