# 기존 기관 v1 결과 목록 연결

`product-ui-result-catalog-legacy-families`의 첫 판본이다. 기관 v1의 서버 목록→보호 API→닫힌 SDK→
기존 재생→실제 통합을 순서대로 연결하며, 각 자식의 검증을 전체 U1이나 배포 수용으로 확대하지 않는다.
구획 v2/startup v3는 후속이다. 조사·설계는 현재 native Codex CLI `gpt-6.1-sol` / `xhigh`에서 수행한다.

## 서버 목록 자식

`OrganCropResultCatalog(store)`는 기존 실제 `CropResultStore`와 그 저장소의 farm/principal/현재 권리
검사를 재사용한다. 계산-cycle query나 수확 reader가 없어도 이 자식은 구성할 수 있다.
새 표·role·결과·서명·계수·계산은 만들지 않는다. 기존 store 파일도 변경하지 않는다.

`open(tenant, 'organ_v1', farm_ref, limit=10, before=None)`의 농장 참조·UTC keyset·닫힌 응답은
기존 목록 계약과 같다. ID는 `crop-result-v1:<sha256>`만 허용하며 limit은 정수 1–20이다.
기존 `crop_research_results`에서 tenant·농장/판본/등록 hash·원 request의 crop_id로
`(recorded_at,result_id)` 내림차순 limit+1개의 식별자와 저장 시각만 읽는다.

각 항목은 기존 `store.get`으로 HMAC/원 bytes·모델/프로필·현재 등록/display 권리를 검증한 후
원 ID/저장 시각·study/revision·원 입력 기간·completed/hold·시점/사건 개수를 투영한다.
수치·원 payload·서명·credential은 응답에 넣지 않는다. 목록 선택은 관문 승인 증거가 아니다.
응답은 기존 `crop-research-result-catalog-v1`/`stored_research_metadata_only`, kind `organ_v1`,
`selection_validation_required=true`, `rights_or_gate_approval=false`와 64KiB 한도를 유지한다.

다수 원 payload를 한 번에 가져오거나 보유하지 않는다. 후보 식별자만 보유하고 각 원 record를
순차 검사한다. 각 원 payload에는 기존 store의 packet 한도 64MiB를 적용한다.
수치 재생은 선택 후 기존 API가 별도로 검사한다. 입력은 원 program의 명시 기간이며 관측 작기가 아니다.

빈 목록에서도 현재 농장/작물을 확인한다. 초기 투영·yield 전·yield 뒤마다 현재 등록과 각 항목의
원 metadata/payload hash를 대사한다. 권리·계정·등록·record 변경은 페이지 전체 보류/거부이며
조용히 항목을 빼거나 이전 승인을 재사용하지 않는다. 뒤에 추가된 새 row는 기존 항목을 바꾸지 않는다.

## 수용 순서

1. 서버 자식: 닫힌 필터/cursor·동률·빈/hold·bytes·늦은 변경·오류 비공개 단위 검사,
   실제 SCRAM의 정상 producer가 만든 원 결과와 목록의 일치·권리 철회·재조회/원 bytes·DB 불변,
   조회 중 RHS/put 0·FD/소유 프로세스/PG/임시 정리·고정 WSL 한도를 확인한다.
2. 보호 API 자식: 기존 목록 URL의 명시 kind와 원 ID cursor·typed 응답을 추가하고,
   legacy만 구성된 조립의 농장/작물 선택과 인증·현재/늦은 철회·원 byte 불변을 확인한다.
3. SDK/화면 자식: 명시 kind·원 ID/farm을 기존 기관 재생에 전달한다. 페이지/종류 변경·취소·
   계정 교체/권리 실패는 이전 재생을 제거하며 늦은 응답은 무시한다. 다른 두 kind를 보존한다.
4. 통합: 실제 저장 reader/보호 API/같은 minified App에서 목록→같은 원 UTC·3D/표,
   재접속/권리·페이지·좁은 폭/키보드·원 디자인 대조·기존 서비스/자료/자원을 확인한다.

합성 fixture/새로운 소유 시험 결과는 소프트웨어 검증이다. 기존 보존 판본의 최신 CODE 호환성과
실제 독립 농장 자료·생산/경제·G0–G4·원 디자인·사용자 적용의 남은 조건은 별도다.

## 보호 API 자식

기존 `GET /v1/crop-research-result-catalog`에 kind `organ_v1`과 원 ID cursor를 추가한다.
다른 두 kind의 응답과 미구성/인증/오류 의미는 유지한다. 기관 store는 기존 `create_app`의
`crop_result_store`에서 명시적으로 전달하며 jobs·farms·principal이 다른 조립은 거부한다.
기관만 구성된 조립도 기존 `/farm-crops`의 동일한 등록 작물 응답을 제공한다.
단위 없는 metadata와 전체 typed JSON 직렬화는 현재 검증 context 안에서 끝낸다.
권리/계정의 늦은 변경은 준비된 bytes를 내보내지 않는다. 현재 kind의 reader가 없으면 인증 후 503이다.
OpenAPI snapshot·기존 두 kind·기관의 닫힌 cursor/응답·개인 오류 비공개·ASGI/실제 SCRAM의
원 결과 대사를 검증한다. 실제 HTTPS/브라우저·최신 CODE의 기존 보존 판본과 사용자 적용은 후속이다.
