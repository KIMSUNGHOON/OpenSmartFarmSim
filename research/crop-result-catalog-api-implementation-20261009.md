# 저장 작물 연구 결과 목록 API — 2026-10-09

상태: `crop-result-catalog-api`와 필요한 등록 조회 비용 보완만 **로컬 수용**.
상위 U1·웹 목록/선택·진행 중인 전체 계산의 실시간 UI 연동은 미완료다.
[HTTP 계약](../contracts/api-crop-result-catalog-v1.md),
[metadata 계약](../contracts/crop-result-catalog-v1.md),
[종료·응답·자원·CLI 증거](artifacts/crop-result-catalog-api-reference-20261009.json)를 따른다.
판단은 현재 native CLI `gpt-6.1-sol / xhigh`에서 수행했고 CLI를 재귀 실행하지 않았다.

## 구현과 사용자에게 남은 연결

`GET /v1/crop-research-result-catalog`는 기존 인증/현재 query/runtime graph에서
같은 계정·농장/판본·등록 hash·crop의 verified 생장 또는 등록 수확 metadata를 찾는다.
닫힌 query·paired UTC cursor·1–20 limit, typed union·64KiB·no-store와
context 안의 직렬화 후 등록/권리/서명 및 현재 인증 주체 재검사를 연결했다.
새 DB/role·factory·queue를 추가하지 않았다. OpenAPI와 기존 endpoint 조립을 대사했다.

목록은 `stored_research_metadata_only`, `selection_validation_required=true`,
`rights_or_gate_approval=false`다. 선택할 때 기존 query/API가 원 파일/수치·현재 권리를 다시 검사한다.
목록 조회를 품종·생산/자원·미래 마진/추천 또는 관문 승인으로 표시하지 않는다.
현재 localhost 앱에는 이 목록 SDK/선택 화면을 아직 연결하지 않았다.
기존 앱은 별도 DB의 저장된 작은 합성 3시점을 읽으며 전체166일 producer와 자동 연동하지 않는다.

## 실제 다수 목록에서 확인한 비용과 수정

원84015/실제 시험 v2는 정상 producer가 준비한 생장21건의 기본10건을
**19.062664초/4,397bytes**에 읽었다. 최대20건은 **30.101151초에 client timeout**으로 실패했다.
제한을 늘리지 않고 각 검사 단계 안에서 동일한 등록 검사를 한 번만 수행하도록 보완했다.

묶는 키는 tenant·farm 참조·권리 available_at·원 period 전체다.
기존 등록 함수의 구현 파일 SHA를 명시적으로 고정하고 다른 구현은 새 검토 전 거부한다.
초기·직렬화 전·직렬화 후 검사마다 별도 묶음을 사용한다. 서로 다른 인자는 합치지 않으며
각 행의 HMAC/column·부모 대사와 각 선언/root의 현재 display 권리는 매번 확인한다.
원 함수·저장 payload/서명·시각·입력/솔버를 수정하지 않았다.
추가 반례9개는 수정 전 실패했고 수정 후 기존 항목과 함께 통과했다.

## 통과한 검증

- 최종 집중5파일은 원19559 종료0, **296 passed /114.69초**다.
  metadata39개·새 API56개와 기존 OpenAPI/생장/수확 경로를 확인했다.
  `python -m app.api_openapi --check` 원74719도 종료0이다.
- 수동 [실제 DB/HTTPS 시험](../backend/tests/crop_result_catalog_api_preserved_smoke.py)은
  원7187 종료0, **1 passed**, 준비/정리 포함 **45.660520초/원1,200초 상한**이다.
  별도 SCRAM 복원 DB와 실제 TLS/Bearer의 완료 응답14개를 끝까지 읽었다.
  성공7개·인증401/권한403/등록·작물·foreign422·투영 뒤 display 철회422를 대사했다.
- 실제 생장21건에서 **20+1 페이지**와 전체 ID의 중복/누락0을 확인했다.
  기본10건 **5.101307초/4,397bytes**, 최대20건 **6.482368초/8,237bytes**다.
  수정 전후 기본10건 응답 SHA가 같아 원 metadata 보존도 확인했다.
  수확은 실제 **1건/원5행 metadata**, **4.244461초/764bytes**다.
- 원 생장/수확 ID·최초 저장 시각·부모를 보존했다. 동률은 새 소유 합성20행의 시각만
  DB owner로 동일하게 만든 별도 fixture이며 원 보존 행의 시각은 바꾸지 않았다.
  동률10+10+원1 페이지와 ID 내림차순을 대사했다.
- 추가20건은 첫 시험의 정상 producer가 만든 별도 소유 연구 결과다.
  첫 시험 종료 후 같은 DB를 소유 범위에서 잠깐 재기동해 dump로 보존했다.
  재시험은 그 dump의 원 payload hash/최초 시각21건을 대사하며 **재계산/재서명하지 않았다**.
  추가 결과의 선택/3D용 result evidence를 발행한 것으로 표시하지 않는다.
- 조회 단계에서는 값/파일 조회·RHS·결과 생성/게시·증명 발행을 금지해 **0호출**을 확인했다.
  준비 단계의 정상20회 계산/게시와 이 0호출 범위를 구분한다.
- 보존 입력/원 artifact/추가 준비 자료 **370 entries 동일**, 새 FD identity **0**,
  FD **12→11**과 시험 소유 PG/HTTPS 종료를 확인했다. 기존 full producer/preview·두 DB는 같은 프로세스로 유지됐다.
  원1,516 source pins도 같았다. 0.1초/435표본의 동시 소유 RSS 최대
  **841,277,440bytes**, 단일 **148,512,768bytes**로 지정1GiB/512MiB 안이다.

## 실패와 수용 한계

첫 v1/원42667은 기록 파일의 중복 생성 거부로 종료1이었다. 정상20건 준비는 완료됐으므로 보존해 재사용했다.
보존 export의 첫 기동은 너무 긴 Unix socket 경로로 실패했고, 짧은 소유 `/tmp` 경로로 수정해 종료/보존했다.
v2는 위 실제30초 초과다. 수정 후 v3/원20063은 API/원본 대사까지 통과했으나
FD 개수 완전 일치 assertion이12→11 감소를 거부했다. 최종 v4는 FD identity/multiplicity로
새 descriptor가 없음을 검사한다. FD 누출 검사를 제거하지 않았다. 각 실패의 종료/소유 정리 기록을 보존했다.
초기 조립 회귀의4실패도 schema-only 경로의 지연 import와 forwarding-only 시험 격리를 보완해 최종296개에서 해소했다.

같은 period/권리 시각의 생장20건만 실제 용량으로 검증했다.
서로 다른20개 조건 또는 수확20건·동시 사용자·브라우저·일반 운영 용량은 미수용이다.
새 hosted 전체 CI·실제 제품 CLI·웹 목록/3D 선택·실시간 진행과 G0–G4도 이 시험으로 완료하지 않는다.
실제 품종/농장 작물 Run/국내 독립 자료0건은 유지한다.

다음 사용자 산출물은 **기존 농장 선택 → 저장 결과 목록 → 같은 결과의 기존3D/수확 조회**다.
그 뒤 같은 실제 DB/API/빌드 App의 새로고침/재시작·권리 실패를 확인한다.
실시간 상태/완료 결과 연결은 U3의 별도 수용 기준을 따른다.
