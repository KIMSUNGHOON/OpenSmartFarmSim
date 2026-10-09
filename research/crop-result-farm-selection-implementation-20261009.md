# 저장 결과 선택을 위한 등록 작물 조회 — 2026-10-09

상태: `crop-result-farm-selection` 서버 자식만 **로컬 수용**.
[계약](../contracts/crop-result-farm-selection-v1.md)과
[원 종료·CLI·응답·자원 증거](artifacts/crop-result-farm-selection-reference-20261009.json)를 따른다.
판단은 현재 native Codex CLI `gpt-6.1-sol / xhigh`에서 수행했으며 재귀 CLI 호출은0이다.

## 구현과 사용자에게 남은 연결

기존 농장 요약에는 작물 ID·이름이 없는데 결과 목록에는 crop_id가 필수였다.
`GET /v1/crop-research-result-catalog/farm-crops`를 같은 인증/현재 farm graph에 추가해
농장 판본·등록 hash로 원 등록의 작물 ID/이름·품종·기간을 찾는다.
Unicode 이름과 원 사용자 가정·미검증 profile을 보존하며 최대32항목/64KiB를 적용한다.
닫힌 query/DTO와 no-store, 투영 전후 현재 등록/권리·응답 직전 인증 주체 재검사를 연결했다.
새 DB/role/작업 큐·작물 계수나 계산은 추가하지 않았다.

이 조회는 등록 입력 선택용 metadata다. 결과 존재나 품종/자료·관문 승인을 뜻하지 않는다.
후속 결과 목록과 선택 결과의 기존 현재 검사는 계속 필요하다.
실행 중인 localhost API/제품 빌드에는 이 새 조회·선택 화면을 아직 배포하지 않았다.
현재 화면은 별도 DB의 저장된 작은 합성3시점을 읽으며, 진행 중인166일 계산의 상태/새 결과와 자동 연결되지 않는다.

## 통과한 검증

- 최종 집중 시험은 원77334 종료0, **348 passed /230.57초**다.
  새 metadata16개/API34개와 기존 목록·OpenAPI·생장/수확 API를 확인했다.
  빈/32항목·Unicode·고유/순서·닫힌 query·bytes·현재 주체/등록 변경과 철회를 검사했다.
  초기 RED와 초과 bytes fixture의 수정 이력도 보존했다. 응답 한도는 늘리지 않았다.
- 실제 별도 복원 SCRAM DB/보호 HTTPS는 원10756 종료0, **1 passed /48.96초**다.
  준비/정리 포함49.556초/상한1,200초이며 완료 응답22개 중 새 선택 조회는8개다.
  원 등록의1작물을 대사한 성공2개는 각각 **1.349140/1.351118초, 604bytes**, 원 응답 SHA가 같다.
  무인증401/권한403·타 계정/잘못된 hash422와 투영 뒤 현재 등록 scope 철회/지속 철회422를 확인했다.
- 기존 생장21건/수확1건과 원 hash·서명·최초 시각을 보존했다.
  조회 단계의 값/파일 조회·RHS·증명/게시 호출0, 입력/artifact370 entries 동일,
  FD12→11·새 FD identity0이다. 정상 준비된 추가20건은 기존 보존 dump를 재사용했다.
- 최종 native의 backend/contracts690 source pins와 다섯 핵심 파일을 확인했다.
  집중 시험 뒤 변경은 수동 harness의 소유 복원 설정 경로 보완뿐이며 핵심/API/OpenAPI는 같다.
  0.1초/472표본의 동시 원 계산/미리보기 포함 RSS 합827,895,808bytes·단일150,212,608bytes다.
  시험 소유 PG/HTTPS 종료 후 해당 복원 DB data와 passfile만 삭제했다.
  원 계산/미리보기의 네 프로세스 identity, 고정 producer3파일과 기존 web/dist는 유지했다.

## 실패와 남은 범위

첫 native/원11745는3.837초·종료1이며 HTTPS 전에 runtime 검사가 거부했다.
소유 market_scope 파일을 복제하면서 static hash 사전의 경로를 원 경로에 남긴 것이 원인이다.
원 bytes/hash 동일성을 확인하고 소유 사전의 경로만 새 위치로 옮겼다. 원 validator/producer를 완화하지 않았다.
실패·성공 양쪽의 정지와 소유 정리 증거를 남겼다.

32항목/빈 목록은 집중 시험 범위이며 실제 DB에서는1작물만 검증했다.
웹 SDK·결과 선택 화면·브라우저/재시작·상위 U1, 실시간 상태/완료 연결 U3는 미완료다.
실제 품종/농장 작물 Run/국내 독립 자료0건과 G0–G4·생산/미래 마진/추천 보류를 유지한다.
다음은 등록 작물 SDK와 기존 목록 SDK의 남은 빌드 수용 → 저장 결과 선택 화면 → 실제 DB/API/브라우저다.
