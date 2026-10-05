# 시작 유보 계산의 불변 저장 선행 artifact — v1

상태: **다음 두 파일 계약; artifact/DB/API/새 3D 미수용**.
선행: [새 짧은 적분의 로컬 수용](../research/crop-startup-integration-implementation.md).
파일: `backend/app/crop_startup_artifact.py`, `backend/tests/test_crop_startup_artifact.py`.
기존 artifact/model/코드/불변 bytes는 보존한다.

## 경계와 판본

`calculate_startup_artifact(program_raw, *, growth_profile, cohort_profile,
transport_profile, notice_raw)`는 canonical UTF-8 JSON의 명시 합성 프로그램을
고정 새 적분기로 계산해 immutable bytes를 반환한다.
`read_startup_artifact(raw, *, expected_sha256, growth_profile, cohort_profile,
transport_profile, notice_raw)`는 신뢰 참조의 bytes hash와 프로그램/결과를 검증하고
새 사본을 반환한다. 조회에서 재적분하지 않는다.
외부 작성 결과/계수/테넌트/승인/예측을 입력으로 받지 않는다.

새 `schema_version=crop-startup-artifact-v1`, `claim_scope=synthetic_crop_math_only`다.
닫힌 packet은 schema/claim, 원 canonical 프로그램과 hash, 고정 세 profile/notice bytes,
artifact code hash, 새 원 적분 result, ID를 보존한다.
`artifact_id=crop-startup-artifact-v1:<sha256>`는 ID를 제외한 canonical bytes hash다.
기존 [artifact 계약](crop-coupled-artifact-v1.md)의 1 MiB 입력/16 MiB 결과 상한,
단위/shape·중복 키·비유한/비canonical 거부·동일 ID의 서로 다른 block 거부를 재사용한다.
입력 origins는 모두 synthetic이어야 하며 실제 source/rights/QC 채택 인터페이스가 아니다.

## 결과 검증

새 program/integrator/RHS와 현재 아홉 원 코드 hash·고정 profile·기존 배분/새 시작 정책·
notice·정규화 input/result hash·Python/time/solver/연구 가정을 대사한다.
필요한 변경 없는 순수 parser/단위/상태/사건 helper만 재사용한다.
원 v1/v2 모델을 새 형식으로 바꾸거나 전역 모델/validator를 치환하지 않는다.

각 sample/last_confirmed의 UTC·닫힌 5개 기관/온도 상태·50 N/C·16 누적 필드·LAI/fruit C와
원 외부 탄소/개수 수지 및 새 요청/생장 호흡 진단 4필드를 검사한다.
잔차를 재계산하고 공급 budget이 코드의 허용 예산을 초과하지 않게 한다.
관리 journal의 같은 N/C 비율·전후 상태/제거량·원 사건 ID/시각을 대사한다.
완료는 모든 출력/사건/계획 step이 있어야 하며 hold는 확인된 과거의 순서 있는 prefix만
허용한다. trial 시각은 소수 초 UTC를, 저장 출력은 정수 초 UTC를 유지한다.

tail 전환/미세 구획 오차와 수렴 미평가의 연구 고지를 유지한다.
reader나 packet이 관측한 수렴/생물학적 검증/actual Run/추천을 승인하지 않는다.
hash는 권리 서명이 아니다. 후속 DB가 HMAC·현재 farm/program 권리·등록 연결을 먼저 검사한다.

## 수용 기준과 사용자 산출물

1. 새 독립 6프로그램 중 빈 초기/무진입/전량 제거·기존 양의 tail의 실제 bytes와
   코드/profile/정책/원 입력·결과 hash, caller 불변/사본 격리·재현을 확인한다.
2. 실제 runtime hold의 UTC/phase/마지막 확인 상태·과거 prefix를 보존한다.
3. 별도 Python reader와 재적분 금지 검증, 실제 24시간/512출력 파일의 크기/읽기 시간을 기록한다.
4. 비합성/동일 ID 충돌·과대/비canonical·추가/중복/비유한·단위/길이/시각/수지/budget/
   journal/manifest/모델·코드/정책 혼합·변조와 신뢰 hash 불일치를 거부한다.
5. 새 집중 시험과 기존 작물/artifact 회귀, 변경 파일/링크/hash를 통과한 뒤 수용한다.
   사용자는 immutable 파일 ID/hash·UTC별 원 상태/누적 요청/실현/유보/호흡·hold를 확인한다.

이 단계에는 DB custody/현재 권리·새 API·실제 브라우저 장면이 없다.
후속은 각각 새 저장 판본의 실제 SCRAM/원자성/철회/재시작·조회 페이지/TLS/30초 본문·
동일 UTC 원 수치/mesh/권리·취소 정리의 별도 계약/수용이다.
전체 작기·수확/자원/경제와 국내 독립 자료 확보는 기존 의존성을 유지한다.
