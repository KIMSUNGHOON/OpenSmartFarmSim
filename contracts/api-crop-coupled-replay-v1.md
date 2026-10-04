# 저장 기관/50과실 구획의 페이지 조회 API — v1

상태: **로컬 합성 연구 API 수용; 새 hosted/브라우저·실제 작기 미수용**.
[실제 수용](../research/api-crop-coupled-replay-implementation.md): 고유 207개 분할 검증,
HTTPS 19개·최대 11.508339초/649,718 bytes·재시작/현재 권리·정리.
선행은 [farm 결합 연구 저장](crop-result-v2.md)이다. 현재 CLI
`gpt-6.1-sol / xhigh`에서 판단하며 재귀 CLI를 실행하지 않는다.

## 한 읽기 경로와 범위

`GET /v1/crop-coupled-research-results/{result_id}`는 정확한
`crop-result-v2:<64 lowercase hex>`와 v1 조회의 네 필수 farm query
`scenario_id/scenario_revision/registration_sha256/crop_id`를 받는다.
추가 query는 `sample_offset`(기본 0, 0–512), `sample_limit`(기본 64, 1–64),
`event_offset`(기본 0, 0–128), `event_limit`(기본 8, 1–8)뿐이다.
각 query는 한 번만 허용하며 정수는 canonical ASCII decimal이다. total을 넘는
offset은 422, total과 같은 offset은 빈 마지막 페이지다.
본문/새 입력·계수/tenant 교체·실행/재계산·관문 게시를 받지 않는다.

페이지의 직렬화된 전체 본문은 **2 MiB 이하**다. 계산의 512출력과 API의 한
응답 64출력을 분리한다. 전체 결과를 축약하거나 미래 시점을 생성하지 않는다.
검증된 원본의 같은 순서를 페이지로 읽으며 각 페이지는 같은 result ID/등록/
payload·result·artifact/input hash를 유지한다. 조회는 저장 값을 바꾸지 않는다.

인증 tenant·기존 farm READ와 `crop_result_read`, 현재 farm/source/program
display 권리·HMAC/custody가 필요하다. 기본 store 없음은 503이다. 새 optional
store/factory와 명시적인 `crop_coupled_result_storage=true`는 함께 필요하고,
같은 실제 farm service/JobStore/현재 principal에 묶는다.
operator loader는 생략/정확한 bool만 읽는다. 명시 true에는 표준 runtime의 exact
store/factory 조립이 필요하며 flag/factory 불일치·다른 service/store는 거부한다.

## 공개 타입과 보류

닫힌 typed 응답은 불변 result/최초 DB UTC·study/revision,
farm/crop/batch/zone·등록/farm/source hash, 기간/status/step count와
model/profile 3개/policy/code 6개·artifact/storage/binding 코드/solver·raw/normalized
input/result/artifact/payload/notice hash를 제공한다. 원 입력 ID·권리 선언·forcing/
RGR/S/W1 원문·profile 원문·tenant·key/HMAC/비공개 source는 공개하지 않는다.
연구 가정은 고정된 설명 목록만 제공한다.

`stored_unpublished_research`, `synthetic_crop_math_only`, `software_research_only`,
`unvalidated_for_registered_crop`, `per_m2_floor`, `synthetic_research_program`,
`gates=not_assessed`를 유지한다. 승인 Run/실제 품종 예측으로 바꾸지 않는다.

sample은 UTC·buffer/leaf/stem_root/T24/Tsum와 정확한 50개 N/C,
LAI·과실 C 합계·12개 누적 외부 유량·두 잔차/계산 예산이다.
CH2O는 mg_CH2O/m2_floor, N은 fruits_equivalent/m2_floor이며 실제 생과 kg/과실 개수/
수확·판매량으로 환산하지 않는다. 온도와 온도 적산·LAI 단위는 원 계산 그대로다.
각 sample은 요구한 output_times 중 하나이고 관리 후 상태다.

사건 페이지는 정확한 UTC·전/후 상태·기관 및 같은 구획 N/C 제거를 제공한다.
사건 input ID는 반환하지 않는다. 이 제거는 품종별 수확 기록이 아니다.

hold는 고정 reason code·UTC solver 시각/phase와 마지막 확인 상태의 진단이다.
소수 초 실패 시각과 정수 초 sample을 실제 UTC datetime으로 비교한다.
확인된 과거 sample/event는 페이지로 읽되 실패 이후 시점은 없다.
last-confirmed는 별도 진단이며 정상 관리 후 output sample로 추가하지 않는다.
원 reason 문자열·실패 trial을 정상 장면에 넣지 않는다.

sample/event의 각 페이지는 offset/limit/total/next_offset을 가진다.
완료의 총 sample/event 수는 원 프로그램과 정확히 같고, hold는 확인된 앞부분이다.
페이지의 선택된 UTC/수지/단위와 raw result hash를 함께 읽는다.

## 오류·조립과 수용

기존 ErrorEnvelope와 Bearer/보안 헤더/no-store 정책을 사용한다.
401 인증, 403 scope, 404 미저장/다른 tenant, 422 무효 query·farm/rights/custody/
형식 hold, 503 서비스 실패다. 예외 원문이나 credentials를 응답/로그에 넣지 않는다.
큰 응답은 부분 JSON을 보내지 않고 hold로 끝낸다.

구현은 새 API/시험 각 한 파일과 기존 `api.py`, `api_runtime.py`의 선택
store/factory, operator loader·고정 OpenAPI/권한 시험의 연결이다.
실제 TLS/SCRAM 시험 영수증을 기록했고 existing v1 조회는 유지한다.

1. OpenAPI/typed 닫힌 계약·단위/50구획·UTC/페이지와 stored exact quantities를 대사한다.
2. 512개 output을 모든 페이지에서 누락/중복 없이 같은 ID/hash/순서로 읽는다.
   management events와 hold/빈 과거의 경계도 확인한다. GET에 재적분이 없음을 확인한다.
3. 다른 farm/tenant·잘못된 query/중복/body·행/모델/프로필/단위/수지 변조와
   현재 scope/source/program 권리 철회를 거부한다. 기본/다른 factory 조립 회귀를 확인한다.
4. 실제 표준 HTTPS/Bearer·SCRAM에서 최대 sample/event 페이지의 **전체 본문을
   30초 안에 수신**하고 재조회/현재 권리·재시작/DB·password 파일 정리를 확인한다.
   로컬 artifact 읽기 0.3055초를 이 HTTP 검증으로 대신하지 않는다.
5. 실제 검증·파일/hash와 남은 브라우저/전체 작기·실제 자료/G0–G4 의존성을 보고한다.

이후 같은 저장 result ID·UTC의 표/그래프·50구획 연구 3D를 [별도 장면 계약](web-crop-coupled-replay-v1.md)으로
연결한다. 키/실제 잎 수·과실 색/숙기·수확은 그 근거/모델이 생기기 전까지 만들지 않는다.
