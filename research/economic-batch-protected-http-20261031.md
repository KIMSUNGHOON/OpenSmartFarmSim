# 소유 생산 batch의 보호 HTTP — 2026-10-31

[HTTP 구현](../backend/app/api_economic_batch.py)과 [닫힌 응답 형식](../backend/app/economic_batch_wire.py)을
[계약](../contracts/economic-batch-protected-http-v1.md)대로 실제 소유 SCRAM DB와 검증된 TLS에서 수용했다.
[기계 증거](artifacts/economic-batch-protected-http-20261031.json)와
[실제 HTTPS 사례](artifacts/economic-batch-http-case-20261031.json)를 남겼다.
**입력8종/schema4의 등록·목록·조회, 계산 접수와 원문 결과 조회를 연결했다.
자동 계산 소비자·일반 runtime 조립·SDK/비용 UI는 아직 연결하지 않았다.**

## 구현 범위

create_app에 같은 실제 EconomicBatchAuthority를 명시 주입한 경우에만 새5경로를 설치한다.
서버가 인증 tenant를 결정하고 client body의 tenant_id를 거부한다.
같은 provider/정책/JobStore/source/서명 hold/context의 원 identity를 전후 검사한다.
기존 source intake의 등록 거래와 재시도·원문/최초 시각 보존을 공유하며 새8종/schema4와 scope를 선택한다.
기존7종/schema3 서비스와 기본 OpenAPI는 유지한다. 새 런타임 설정이나 사용자 DB는 변경하지 않았다.

source 전체 요청64KiB, 계산 요청4KiB, 결과2MiB 한도를 명시했다.
중복 JSON key·비유한 값·tenant/추가 필드·잘못된 schema/cursor/query를 거부한다.
참조만 접수하고 HTTP 안에서 worker를 실행하거나 금액을 계산하지 않는다.
결과는 현재 읽기 권한/입력/근거와 게시 이력을 검증한 원 JSON bytes를 반환한다.
Decimal 문자열·null·재고 행은 닫힌 OpenAPI 형식이며 최초 publication ID/시각과 no-store를 유지한다.

## 통과한 검증

- **최종 신규20 + 기존129 = 고유149검사**를 같은 production 코드에서 통과했다.
  기존 사용자 source 등록/조회·인증 middleware·ApiRuntime을 포함한다. 앞선11/148/반복 사례는 다시 합산하지 않았다.
- 실제8종 source의 HTTP 등록/재시도/목록/조회와 원 collection job bytes/SHA, 최초 시각을 대사했다.
  schema3 거부/schema4·닫힌 스키마, 한글/슬래시 ID, cursor/중복 query/JSON, 큰 body와 content type을 확인했다.
- 기존 source와 다른 값의 같은 버전은409이고 새 작업/행이 남지 않는다.
  쓰기 권한의 늦은 철회는403이며 원 거래가 rollback된다.
- 저장 거래 중 authority의 source를 교체하면503 응답 뒤 행이 남는 **실제1fail RED**를 재현했다.
  같은 authority의 결속 검사를 등록 서비스의 거래 guard까지 연결해 두 행0으로 수정했다.
  늦은 읽기 권한 철회와 객체 교체에도 본문을 반환하지 않는다.
- 실제 HttpsApiService·검증된 인증서/HTTPSConnection과 BearerRegistry/current_principal을 사용했다.
  실제 source 접수→계산 접수202/동일 재시도→queued404→**명시 worker** 완료→fresh request-bound 결과 조회200을 대사했다.
  자동 소비자를 실행한 증거는 아니다. 초기 서명 context/일부 source는 소유 fixture에서 준비했다.
- 결과10,460bytes가 자기 작업의 원 bytes와 일치한다. 최초 publication headers, 실행 scope 없이 읽기,
  인증401/부족 scope403/다른 tenant404/tenant query422/만료401을 확인했다.
  금액 진입을 차단하고 실제 SQL을 계측한 결과 조회 재계산/SQL쓰기0을 확인했다.
- 기존 source7종/default API·runtime·보호 middleware 회귀를 통과했다.
  전체 backend/frontend suite와 새 브라우저/사용자 배포는 실행하지 않았다. CI 상태는 커밋 뒤 exact head로 별도 기록한다.

증거 기록용 설정이 읽기 전용이어서 기존 phase 이름을 재사용한1회는 검사19개가 통과했어도
기록 파일 충돌로 exit1이었다. 그 실행은 수용에서 제외했고 기존 기록을 덮어쓰지 않았다.
별도 최종 phase/실제 클러스터에서149개와 정상 종료·정리를 확인했다.

## 보존과 자원

PG16.15 별도 소유 클러스터·16MiB shared_buffers·host SCRAM과 기존 Python 환경을 사용했다.
기존 사용자 DSN/비밀번호를 읽지 않았다. WSL PID512MiB/합1GiB·600초 한도로 감독했고
최종 계측/FD/소유 잔여0과 원4,500항목 보존은 기계 증거에 기록했다.
수용된 부모733원본/2출력·private15/external12와 기존 UI의 원 자료/빌드를 확인했다.
5184의238파일/21,012,689bytes는 실제 HTTP·원 identity/첫 만료17:03 KST를 대사했다.
만료된5181은 종료와233고정 파일/정책·과거 증거 지문으로 확인했고 재시작/만료 연장을 하지 않았다.
이전 모든 raw archive를 이번에 새로 재실행하지는 않았다.

공유 API/형식/시험 파일은 수용 커밋의 Git snapshot으로 남긴다.
수치/모델의 고정 지문은 유지하고 이후 명시 runtime 연결은 snapshot과 관련 회귀로 검토한다.
native gpt-6.1-sol/xhigh·CLI0.157.1 turn 2026-10-31T05:16:27.169Z와 판단/출력을 기록했고 재귀 CLI/새 agent0이다.
실제 농장 자료/요금/계수 채택0·독립 국내 raw0·G0–G4 미평가·R2 미승인을 유지한다.

## 다음 수용과 일정 근거

1. `economic-batch-runtime-assembly`: 기존 ApiRuntime의 명시 optional factory로 같은 실제 provider/정책/login/source/hold/context/authority를 조립한다.
   default/기존7종·schema3·운영 설정을 보존하고 flag/factory 불일치·다른 저장소/늦은 교체를 거부한다.
   실제 보호 HTTPS에서 접수·원 결과/현재 권한과 기존 runtime 회귀를 수용한다. 현재 경계 확인 기준1–2집중시간 초안이다.
2. `economic-batch-automatic-consumer`: 기존 discovery/loop의 닫힌 version/worker/outcome 목록에 정확한 새 입력을 연결한다.
   새 worker는 기존 loop의 _binding 대신 _access를 사용하므로 명시 adapter 분기를 검사한다.
   다른 작업 배제·취소/lease/reclaim·현재 권한·실제 접수→자동 완료→fresh HTTP 원 bytes를 검증한다.2–3집중시간 초안이다.
3. 위 둘 수용 뒤 원 저장 창과 독립 사용자 가정 비용의 기간/포함·누락을 결속한다(1–2시간 초안).
   그 뒤 strict SDK/같은 선택 UI를 연결하고 실제 메뉴/reload/현재 권한/원 수치·3D를 검증한다(2–4시간 초안).

이는 제한된 합성 경제 연결에 남은6–11집중시간의 조건부 작업량이고 달력 완료일/전체 제품 약속이 아니다.
실제 품종/긴 작기·설비/계량/구매/청구·다회 수확/정산·거시/수급·자율 비교와 독립 농장 검증,
최종 제품/G4·R2의 전체 완료일은 필요한 자료와 외부 검증 일정이 없어 미정이다. 전체 goal active/incomplete다.
