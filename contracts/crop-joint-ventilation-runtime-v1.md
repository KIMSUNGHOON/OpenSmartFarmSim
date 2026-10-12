# 기존 공동 계산·환기 계산의 명시 API 조립 v1

2026-10-12. 같은 native Codex CLI `gpt-6.1-sol / xhigh`에서 판단한다.
선행은 [수정본 실제3D 수용](../research/crop-greenhouse-ventilation-post-fix-live-20261012.md)이다.

## 명시 설정

기존 환기 loader에 `operator-joint-ventilation-prefix-api-config-v1` 판본을 추가한다.
기존 보호 파일·factory/조립 후 재검사를 재사용하고, 기존 환기 판본의 필드와 동작을 유지한다.
새 판본은 다음 네 exact boolean 필드를 모두 명시한다:

- `crop_climate_joint_execution`, `crop_climate_joint_prefix`
- `crop_greenhouse_ventilation_execution`, `crop_greenhouse_ventilation_prefix`

모델별 prefix=True는 같은 모델 execution=True를, execution=True는 같은 모델의 result storage=True를 요구한다.
두 모델의 결과 저장 policy 필드는 필수이며 기존 cycle authority 의존성을 유지한다.
새 판본의 False는 명시 비활성이다. 누락·추가 필드·형 강제 변환·구 판본에 새 필드를 넣는 요청은 거부한다.
기존 original/calculation/joint loader는 새 설정 판본을 채택하지 않는다.

## 조립과 수용

기존 ApiRuntime의 두 typed store/query·각 모델 실행/prefix 객체를 같은 jobs/farms/current_principal에 결속한다.
각 모델의 현재 입력·권리·서명 키와 원 불변 결과를 유지한다. factory는 provisioned 역할·현재 검토·resolver·키·custody root를 명시한다.
모델별 key 구분을 검사하며 다른 모델의 객체·권리·결과를 대신 채택하지 않는다.

수용은 실제 같은 SCRAM DB와 검증 HTTPS에서 두 모델의 정상/보류 원 summary/sample/event bytes·UTC,
실행/prefix의 명시 결속·현재 권리/계정/늦은 변경 거부, 잘못된 factory/키/flag·기존 loader 호환 확인까지다.
조립/조회의 수치 재계산·결과 등록·작업 쓰기는0이며 원 데이터/두 UI·원 도구 종료·WSL/소유 정리를 확인한다.
작업자 시작·사용자 서버 적용은 후속 작업이며 이 조립의 수용으로 승인하지 않는다.

[로컬 수용 기록](../research/crop-joint-ventilation-runtime-20261012.md): 고유198검사·실제 두 모델
SCRAM/TLS 정상/보류·22거부 조건·두 현재 UI/자동 조회·원 데이터/WSL 보존. 새 모델 사용자 적용은 후속이다.
