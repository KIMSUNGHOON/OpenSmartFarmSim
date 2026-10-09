# 등록 수확 결과 웹 SDK — 로컬 수용

2026-10-09 00:32 KST. native Codex CLI `gpt-6.1-sol / xhigh`, 재귀 CLI0회.
[고정 영수증](artifacts/web-crop-harvest-client-v2-reference-20261009.json)에 원 도구55282 종료0·458 source·집중/전체·타입/빌드·자원/정리를 결속했다.
선행 [실제 SCRAM/HTTPS](crop-harvest-runtime-tls-implementation-20261009.md)는 유지한다.

## 구현과 사용자 확인 산출물

[계약](../contracts/web-crop-harvest-client-v1.md)의5 core파일을 구현했다.
[SDK](../web/src/harvestReplay.ts)는 닫힌 summary/records·모든 중첩 형식·source/판본/단위/UTC·합성/미평가/승인false를 검사한다.
정확 분자/분모 문자열과 원 수량·배정 목적·미배정·관측 비교 상태를 보존한다.
BigInt는 제공된 정확값의 정규형/Float64 짝수 반올림과 배분 관계를 검사하며 수확/경제 모델을 실행하거나 값을 대체하지 않는다.
HMAC·파일 hash·현재 권리는 서버가 검사한다.

[공통 API](../web/src/api.ts)는 import/factory spread 두 줄만 추가했다.
기존 Bearer·AbortSignal·30초/2MiB transport를 재사용한다. 한 번에 한 요청을 진행하고,
summary/page의 공통 provenance·배정 선언/목적, offset/next/total과 end UTC·terminal→event 순서를 대사한다.
iterator는 다음 요청 전/늦은 응답/소비자 재개 시 선택 변경과 취소를 검사하며 자동 prefetch나 전체 배열 수집을 하지 않는다.
실패/소비자 종료 뒤 추가 요청이나 완료 판정을 내지 않는다.

[공개 fixture](../web/e2e/harvest-recorded-responses.json)는 원 실제 소유 HTTPS summary/전체6행 body와
그 원 body를 현재 DTO로 직렬화한 두 분할/빈 끝5개·152,060bytes다.
모두 선행 실제 응답의 SHA/길이와 일치한다. source receipt와 body SHA를 보존했고 새 DB/HTTP/RHS 실행은0회다.
최초 Python 기본 JSON serializer의 분할 body SHA 불일치/종료1 뒤 원 DTO serializer를 사용해 일치시켰다.
기대 SHA/원 수량은 바꾸지 않았다. 별도 반올림/zero/hold 변형은 형식 시험이며 실제 농장 자료가 아니다.

## 통과한 검증

| 대상 | 실제 결과 |
| --- | --- |
| 처음 RED/GREEN | module 미구현으로 import 실패/시험0·종료1 → 원5응답 보존1통과 |
| 최종 집중 | **97통과**. 원6행/summary/분할·중첩/단위/참조/권리 주장/계수·비율/정확값 거부·취소/동시/settlement |
| 반올림 | 최근접 짝수 두 경계·최소 subnormal/최대 유한·400자리 비율·zero·음수 비교·underflow/잘못된 반올림 거부 |
| 웹 전체 | **817통과/15.23초**, 새97개+기존720개 포함. Vitest 한 worker/파일 순차 실행 |
| 타입/빌드 | 종료0/종료0. 첫 시험의 iterator 완료 타입 좁히기 오류를 수정한 뒤 최종 source로 통과 |
| source/정리 | 최종5 core snapshot·458 source 불변·현재 실제 프로세스/소유 임시 tree0·원 도구 종료0 |

전체+빌드 준비부터17.896초·nice19·Node heap256MiB·0.1초 감시168표본에서
소유 단일 프로세스 RSS 최대437,075,968bytes≤512MiB,
controller/자식 포함 동시 RSS 합566,980,608bytes≤1GiB였다.
공유 page 중복 가능 RSS 합이며 WSL 전체/production 용량 수용은 아니다. 원600초 마감은 유지했다.
기존 큰 chunk 빌드 경고는 남아 있으며 설정/한도를 바꾸지 않았다.

## 검토 반례와 최종 판본

첫94/814 candidate의 [불변 영수증](artifacts/web-crop-harvest-client-reference-20261009.json)은 보존하고 최종 수용에서 대체했다.
추가 검토에서 같은 parameter hash 아래 행/페이지의 revision 이름을 바꾼 두 경우가 거부되지 않았고,
소비자가 반환된 마지막 행의 시각을 바꾸면 다음 정상 페이지가 거부됐다. 세 새 시험을 실제 RED로 확인했다.
전역 parameter/근거·코드/dependency와 배정 선언 identity를 행/페이지 사이에 고정하고,
이전 행의 primitive 시각/종류와 identity 문자열 snapshot을 보존하도록 수정했다.
실제 segment 구간 차이는 유지하며 반환된 행 객체를 다음 검사의 기준으로 보관하지 않는다.
최종97개·전체817개·현재 typecheck/build·458 source/정리는 별도 원 도구55282 종료0으로 확인했다.
과거 시험 수를 최종 고유 수에 더하지 않는다. 원 소유 HTTPS fixture/서버 수식/계수/관문은 바꾸지 않았다.

## 다음 한 단계와 보류

`crop-harvest-client`와 선행 자식의 `crop-harvest-http-sdk` 부모만 추가 체크했다.
다음은 같은 parent/result/UTC의 수확 목적·미배정/관측 비교 표를 기존 C/N·잎 면적 수치3D와 연결하는 작은 view다.
필요한 현재 범위/취소 helper와 화면을3~5파일 자식으로 분해하고, 원 값/단위/시각·선택 변경/권리 실패 시
기존 결과 제거·HTML 대안·대표 WebGL/소유 자원을 검증한다. 실제 형상/숙기/등급/판매를 추정하지 않는다.
그 뒤 같은 DB/API/WebGL의 작은 실제 연결→전체166일 질량 부하→기후/물·양분/구매 에너지→Decimal 경제로 진행한다.

이번 새 UI/브라우저/WebGL·실제 DB/HTTP·작물 RHS·제품 CLI·전체 backend/hosted CI/push는0회다.
실제 품종/환산 계수·국내 독립 자료·실측 작물 Run0건, G0–G4 `not_assessed`다.
생산/미래 마진/추천·원격 Backend 실패·구형25시간 원 종료 유실 hold와 전체 goal은 유지한다.
다음 view의 파일/검증 분해와 자료 확보 일정에 따라 완료 추정을 갱신하며 최종 production 완료일은 확정하지 않는다.
