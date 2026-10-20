# 기존 기관 v1 목록 서버·보호 API — 2026-10-20

[계약](../contracts/crop-organ-result-catalog-v1.md) ·
[기계 증거](artifacts/organ-catalog-server-api-20261020.json)

## 변경과 범위

현재 native Codex CLI `gpt-6.1-sol` / `xhigh` 세션에서 설계·구현했다. 재귀 CLI는 실행하지 않았다.
서버 자식 source `9e4baea`, 보호 API source `78b86fa`다.
기존 기관 `crop-result-v1`을 읽는 `OrganCropResultCatalog`와 명시 kind `organ_v1`을 추가했다.
기존 저장소의 HMAC·프로필/모델·현재 등록/display 권리를 사용하며 store 파일과 저장 형식은 바꾸지 않았다.
목록은 식별자를 먼저 읽고 각 원 record를 순차 검사한다. 새 표·role·결과 재생성·재서명·요청 간 캐시는 없다.

같은 기존 목록 URL과 농장/작물 선택 URL을 사용한다. 기관만 구성된 표준 runtime도 작동한다.
닫힌 응답에는 원 ID·저장 시각·study/revision·명시 입력 기간·상태·시점/사건 개수만 제공한다.
수치 원문·서명·credential은 노출하지 않으며 선택 시 원 결과를 다시 검증해야 한다.
기존 URL과 Growth/Harvest 목록·항목 및 FarmSelection의 5개 스키마는 보존했다.

## 검증

- 서버 단위/실제 SCRAM의 30검사를 통과한 뒤 API를 연결했다. 현재 API 23검사를 포함한
  **7파일·고유 295검사**를 같은 최종 backend source로 통과했다. 새 검사 53개와 기존 242개다.
  이 중 기존 HTTPS 검사 1개를 새 목록까지 확장해 별도로 재확인했다. 296개로 중복 가산하지 않는다.
- 회귀 guard: 실제 종료 0·319.777966초, 단일/합산 최대 RSS 225,116,160 / 898,187,264bytes.
  표본 1,187개·0.25초·FD 4→4, 보호 5root·원본 2,148개·두 frozen UI/환기 source와 소유 정리를 확인했다.
- 실제 소유 SCRAM DB의 정상 합성 producer 3결과로 2+1 keyset 페이지·원 ID/UTC·기간·시점/사건 개수,
  현재/늦은 프로그램 권리·조회 scope 철회와 복구, row/payload/DB 불변을 확인했다.
  기관 단독 ASGI 조립의 목록·작물 선택·기존 수치 조회도 대사했다. ASGI scheme은 TLS 증거로 쓰지 않는다.
- 별도 표준 runtime의 **실제 TLS+SCRAM+Bearer**에서 전체 17응답 중 새 목록/작물 선택 7응답을
  `401,403,422,200,200,422,200`으로 확인했다. 실제 원 response bytes/길이/hash는 비공개 증거에 보존했다.
  미인증·scope 부족·foreign 농장·정상·display 철회/복구와 원 row 불변, 읽는 동안 put/integrate/RHS 0을 확인했다.
- 확장 HTTPS guard: 실제 종료 0·31.298956초, 단일/합산 최대 RSS 147,226,624 / 790,327,296bytes,
  표본 115개·0.25초·FD 4→4·보호/원본/소유 PG·프로세스·passfile·임시 정리 통과.
  회귀와 이 검사의 모든 `backend/app/` source 핀은 같으며 기존 store 파일은 원 bytes다.

기존 512MiB/PID·합1GiB·600초 한도를 유지했고 건강한 서비스를 중단하거나 제한을 늘리지 않았다.
이 변경의 전체 호스팅 backend CI·웹 CI/브라우저는 실행하지 않았다.

두 사용자 주소의 진행 JSON도 갱신했다. 실제 5173/5174의 200·동일 bytes·no-store,
두 frozen HTML과 기존 환기 source 2,173파일 보존을 확인했다.
게시 guard는 실제 종료 0·0.597485초·합산 최대 RSS 609,509,376bytes와 소유 정리로 통과했다.
새 backend/UI 코드 적용과 사용자 두 주소의 DOM 재검증은 하지 않았다.

## 실패 기록과 제한

새 module/API가 없을 때 RED 실패를 먼저 확인했다. 첫 실제 DB 비교는 기대값이 KST인 채 UTC 문자열과
비교해 실패했으며, 시각을 바꾸지 않고 테스트 기대값을 UTC로 정규화했다.
API의 wrong-kind 반례 첫 시도는 테스트가 요청 kind까지 바꿔 미구성 503을 받았다.
요청은 기관으로 고정하고 응답 kind를 바꿔 422 거부를 검증했다. 이 실패들은 통과 건수에 넣지 않았다.

HTTPS의 정상 목록에는 원 결과 **1개**가 있었다. 전체 응답 최대 4.210470초는 이 사례의 관측이며,
기존 30초 요청 제한 아래 20건/대용량 payload의 운영 용량 증거가 아니다.
서버는 기존 limit 1–20과 packet 64MiB/응답 64KiB 계약을 유지한다. 최대 범위의 실제 검증은 사용자 적용 전 남는다.
이번 데이터는 새 소유 시험 DB의 합성 연구 결과이며 기존 보존 판본의 최신 CODE 호환성 증거가 아니다.

## 다음 산출물과 수용 기준

1. 같은 원 HTTPS metadata에 근거한 닫힌 `organ_v1` SDK를 추가한다. 원 ID prefix·farm·UTC/cursor·
   count/hold·오류와 취소를 확인하고 기존 두 kind의 byte/해석을 보존한다.
2. picker/선택 전달에서 원 ID/farm을 기존 기관 재생에 연결한다. 종류/페이지/농장 변경·계정 교체·
   권리 실패·취소와 늦은 응답은 이전 장면을 제거한다. 재계산·추정 보간은 추가하지 않는다.
3. 같은 minified App의 실제 API/원 UTC·수치/표/3D·키보드/좁은 화면, 보존 판본 CODE·다수/큰 packet,
   기존 서비스/WSL과 원 디자인 대조를 확인한다. 구획 v2/startup v3의 목록 연결도 별도로 이어간다.

서버/보호 API 자식만 수용한다. 기관 family 전체·U1·사용자 적용과 새 목록 UI/버튼·Solar는 미완료/미배포다.
기존 원 디자인 변환 서비스의 동시 한도, API/브라우저 동시 재시작/권리 RSS hold,
생산/물·양분·구매 에너지/경제 통합과 독립 농장/시장 자료·G0–G4는 남는다.
실제 농장 Run 0·전체 완료일 미정·goal active를 유지한다.
