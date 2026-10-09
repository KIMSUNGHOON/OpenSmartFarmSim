# 공동 작물·기후 결과의 API 투영 v1

`project_joint_result(record, terminal, view='summary', page=None, limit=None)`은
[현재 결과 저장소](crop-climate-joint-result-store-v1.md)가 검증한 원 값을 닫힌
`joint-crop-climate-replay-v1` 응답으로 투영한다. 함수 자체는 HMAC·자료 권리·현재 계정을 승인하지 않는다.
후속 current reader는 같은 custody 세션에서 원 artifact의 페이지 소속을 확인하고 투영/직렬화 전후 권리를 검사한다.
단독 투영 검사를 인증된 HTTP·실제 생산 관문의 수용으로 해석하지 않는다.

## 공개 응답

새 result ID/tag·최초 recorded_at·study/revision·농장 scenario/crop/batch/zone·등록 SHA,
원 source/context/UTC/evidence·intent/HEAD/proof/header/root와 code/profile/QC 참조를 보존한다.
claim_scope는 synthetic_joint_crop_climate_math_only, G0_G4는 not_assessed다.
summary는 원 manifest의 모델/수치 판본, UTC 격자, 마지막 확정 상태/시각, checkpoint SHA와 hold를 제공한다.
모든 view는 마지막 확정 시각과 실패 경계를 참조한다. hold는 실패 격자 경계의 시각·단계·reason code를 제공한다.
대문자 code 형식이 아닌 원 오류문은 CALCULATION_HOLD로 매핑하며 자유 형식 원 오류문을 공개하지 않는다.

samples는 원 `{value,time}`의108상태·6파생량·22연속 장부·6사건 합계·7수지/허용오차·순서/단위를 보존한다.
events는 원 시각/격자 번호와 관리 전후108상태·6파생량·제거량·합계·수지/허용오차·계산 SHA를 제공한다.
원 event 입력값·forcing/RGR/매개변수·프로필 원문·원 농장 기록·tenant·내부 등록 job·review/reviewer/권리 선언·자격증명은 공개하지 않는다.
원 계산을 바꾸거나 새 성장/기후/수확 값을 만들지 않는다. 기존121상태 API의 판본을 사용하지 않는다.

## 경계

모든 객체는 닫힌 타입이며 원 quantity는 정확한 유한 float와 단위, 과실 배열은50개다.
원 양수/음수의 부호를 유지하며 sensible energy·온도·순 장부를 일괄 비음수로 제한하지 않는다.
기록 SHA·원 metadata ID·terminal/progress·manifest/context·UTC binding·모델/code/profile/QC를 대사한다.
페이지 root/tag·총수·offset/limit·순서·격자 UTC/elapsed·hold의 실패 경계 이전 행만 허용한다.
페이지 소속/원 숫자의 인증은 trusted reader가 담당하며 단순 page의 root 문자열로 인증됐다고 주장하지 않는다.
summary와 page는 한 응답에서 동시에 제공하지 않는다. samples64/events8, 직렬화된 UTF-8 응답2MiB 이하이다.
UTC는 원 마이크로초 문자열이다. 페이지를 보간하거나 새 UTC binding/Context/RHS/관리/적분을 실행하지 않는다.
serialize 직전에 타입/경계와 bytes 상한을 다시 검사한다. 변조/잘못된 형식은 일반 ProjectionHold다.

## 수용

소유 원 producer/파일의 전체 숫자·시각/단위와 whitelist 원 event를 대사하고 fresh exec에서도 같은 응답 SHA를 확인한다.
실제 SCRAM의 정상/hold 등록 결과에 투영을 연결하고 조회 계산0·원본/FD/자원·소유 종료/정리를 확인한다.
닫힌/추가 필드·잘못된 숫자/단위/50배열·SHA/모델/UTC/terminal 혼합·페이지/용량·공개 정보 경계를 검증한다.
새 HTTP/runtime·WebGL/실시간 U3·실제 품종/작기/현장/미래/비교/배포 관문은 후속이다.
