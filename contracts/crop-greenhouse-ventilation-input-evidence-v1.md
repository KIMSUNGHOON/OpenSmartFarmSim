# 환기 공동 계산의 원 입력 검증 증거 v1

선행은 [새 continuation](crop-greenhouse-ventilation-continuation-v1.md), [UTC](crop-greenhouse-ventilation-time-v1.md),
[페이지 저장](crop-greenhouse-ventilation-storage-v1.md)이다. 핵심3은 새 input_evidence 모듈·해당 tests·이 계약이다.
기존 [입력 증거](crop-climate-joint-input-evidence-v1.md)의 bounded 파일 helper/서명 절차를 재사용하며 새 source/증거/type/domain으로 구분한다.
농업 계수·수식·프로필·구 증거/원본·사용자 두 서버는 변경하지 않는다.

## 원 입력과 검토

소유0700 directory의 닫힌6파일 `source.json,growth.json,cohort.json,transport.json,exchange.json,notice.txt`를 받는다.
원본은0400·현재 euid·single-link regular file이고 모든 경로/파일은 nofollow다.
source1MiB·각 profile/notice128KiB·증거2MiB 상한과 strict canonical JSON·중복/nonfinite 거부를 유지한다.
4프로필과 notice는 이미 고정된 원 bytes/hash만 허용한다.

source는 `version=joint-ventilation-input-source-v1`, `scenario,ventilation,events,output_steps,step_seconds,step_count,time_origin`의 닫힌 객체다.
scenario는 원 다른 forcing을 포함하고 ventilation은 별도 실외 입력이다. 초기 합성 forcing을 source에 다시 넣지 않는다.
scenario/ventilation/time_origin/각 관리 사건의 origin은 synthetic이어야 한다.
108상태·25장부·최대4096걸음/600초·128사건/512출력·UTC microsecond 정책은 선행 계약을 따른다.

신뢰한 현재 `review_resolver(evidence_id)`는 닫힌 `evidence_id,reviewer_id,decision_id,source_sha256,status,scope`를 반환한다.
ID의 기존 ASCII/128문자 정책을 유지하고 status=`accepted_for_software_validation`,
scope=`synthetic_ventilation_input_math_validation_only`만 허용한다. 검토 원본/결정/검토자 변경·삭제/철회/오류는 hold다.
이 검토는 CLI 제안을 곧바로 승인하지 않으며 실제 자료 권리/G0·농장 현재 권한을 승인하지 않는다.

## 발급과 현재 검증

`VentilationInputEvidenceAuthority(integrity_key,issuer_id,key_id,review_resolver)`를 신뢰한 서버 caller가 만든다.
키32–4096bytes를 증거/원본/브라우저/공개 manifest에 넣지 않는다.
`issue(directory,expected_source_sha256,binding=...,review_id=...)`는 원6파일/검토를 읽고 source에서 새 context/UTC를 준비한다.
초기 공동 RHS2회/환기1회만 수행하며 진행 적분·관리·checkpoint 복원0이다.
원 program·초기108상태·초기 `rhs,boundary` 묶음·25장부 identity·원 context/UTC binding에 정확히 대사한다.
원 다른 forcing과 실외 입력은 별도로 보존한다. 코드/프로필/helper SHA·수치 환경·schema/QC/정규화 판본을 결속한다.

새 HMAC-SHA256 domain `ossf-joint-ventilation-input-evidence-v1\0`에 source6파일 SHA·검토/결정 ID·검사 UTC·issuer/key ID·record를 결속한다.
record의 `initial_calculation`은 닫힌 `rhs,boundary`다. 구 flat 초기 RHS와 상호 대체하지 않는다.
증거 version=`joint-ventilation-input-evidence-v1`, 정규화=`joint-current-ventilation-float64-grid-v1`,
QC=`joint-initial-rhs-ventilation-schedule-utc-v1`이다. 원본과 검토를 반환 전에 다시 확인한다.

`verify(directory,expected_source_sha256,evidence_raw,expected_context_sha256=...,expected_binding_sha256=...)`는
trusted3 SHA·현재 키/domain/코드/원 bytes/프로필/환경/검토·원 context/UTC/초기 묶음 hash를 검사한다.
원 달력 helper SHA와 새25장부 identity를 확인하고 현재 원본/검토를 반환 전에 다시 읽는다.
별도 Python에서도 context/UTC 생성·RHS/환기/적분/관리/start/복원0이다.
`VerifiedVentilationInputEvidence.record`는 JSON 복사본이며 `rights_or_gate_approval=False`다.
구/새 증거·키/issuer/코드/환경 혼용과 무서명 fallback을 허용하지 않는다.
현재 호출 시점의 사실이며 cache된 무기한 권한이 아니다. 후속 농장/서버 custody가 게시/표시 전후 현재 검증을 다시 수행한다.

## 수용

1. 수용된10program의 원 다른 forcing/실외 입력·초기 RHS/환기 진단·UTC/hash·고정 프로필/notice를 보존한다.
2. 발급 RHS2/환기1·진행/관리0, 조회와 fresh Python 전체 수치/복원0을 실제 호출 차단으로 확인한다.
3. 서명/닫힌 schema/단위/원 seed·실외 입력/코드/helper·환경·검토·키·UTC/판본 변조와 늦은 변경을 거부한다.
4.6파일/경로/FD·최대512출력/128사건·구 증거/UTC 회귀·원본/두 UI/WSL·소유 정리를 확인한다.

합성 수학/QC 검증이며 G0–G4=`not_assessed`다. 실제 자료 채택·농장/테넌트 권리·custody·API/worker/3D·생산/마진/추천은 후속이다.
