# 검증 계산 결과의 현재 범위 선택 — v1 개발 계약

2026-10-07 KST. native Codex CLI `gpt-6.1-sol / xhigh`; 재귀 CLI0회.
선행은 [새 SDK 수용](../research/web-crop-cycle-calculation-client-20261007.md)이며,
[웹·3D 부모 계약](web-crop-cycle-calculation-replay-v1.md)의 window/view를 두 자식으로 나눈다.
이 문서는 다음 window helper의 착수 계약이며 새 화면·브라우저·3D 수용은 아니다.

## 현재 코드와 변경 경계

기존 `cycleCropWindow.ts`는 원 SDK의 summary/page 타입과 두 조회 메서드를 직접 사용한다.
새 SDK는 sample/event 형식과 페이지 의미가 같지만 ID/manifest/validation을 별도로 보존한다.
응답에서 새 필드를 삭제하거나 구형 DTO로 변환하는 adapter를 만들지 않는다.
기존 현재 범위·취소/settlement 알고리즘에 닫힌 두 source 종류를 연결한다.

다음 작업 `crop-cycle-calculation-window`의 core파일은 **2개**다.
기존 `web/src/cycleCropWindow.ts`와 새 `web/src/calculationCycleCropWindow.test.ts`다.
이전 SDK 수용 때 보존한101 source 중 window helper 하나만 이 단계의 명시 변경 대상이다.
원 window 시험·SDK/공개 fixture·backend·장면/그래프/컴포넌트·잠금은 보존한다.

source는 원/검증 계산의 discriminator, 각 typed SDK와 lookup을 함께 묶는다.
원 `open(api, lookup)` 의미를 유지하고 새 `openCalculation(api, lookup)` 진입점을 추가한다.
공통 상태는 두 summary/page의 닫힌 union을 보존한다. source 종류와 schema를 확인한 뒤
각 SDK의 summary/page를 호출하고, 원 참조·validation/manifest·양·UTC를 그대로 보관한다.
새 응답을 원 응답으로 cast하거나 `any`·필드 삭제로 타입을 통과시키지 않는다.

## 다음 한 단계의 수용 기준

1. 실제 소유 공개 fixture의 정상/25시간·과거/빈/소수 초 hold·출력0 완료를
   새 SDK로 읽고 원 summary/reference/manifest와 선택된 sample·전체 index/UTC를 대사한다.
2. 현재 sample64/event8 이하와 실제 next_offset·이전 조회 offset만 사용한다.
   byte-short·종류 전환·끝/빈 범위·이전/다음 선택에서 배열을 모으거나 미래 frame을 만들지 않는다.
3. source/ID/계정 변경·취소·dispose·권리/검증 실패 시 이전 summary/배열/선택을 비운다.
   실제 pending 요청 settlement 뒤에 다음 요청을 시작하고, 지연/늦은 응답과 세대 변경을 거부한다.
   최대 동시 원 요청1개·dispose 뒤 요청0개와 실패 뒤 stale sample 비표시를 확인한다.
4. 원 `open`/window19개 의미와 새 SDK178개·공통 API 회귀, focused unit/typecheck/build를 확인한다.
   시험 횟수를 더해 고유 수를 부풀리지 않고 동일 최종 source의 근거를 기록한다.
5. 실제 명령/종료·source/로그 SHA와 사설 임시 정리 뒤 window 자식만 체크한다.
   UI/3D·native browser 부모, 전체166일/실제 품종/관문은 체크하지 않는다.

사용자가 확인할 산출물은 새 원 ID/UTC·검증 정보를 유지한 현재 범위 상태와 대사 기록이다.
SDK가 확인하는 공개 형식/대응 관계와 서버의 현재 권리·서명 검증 책임을 보존한다.

## 후속 화면과 실제 경로

window 수용 후 `crop-cycle-calculation-view`는 기존 `CycleCropReplay.tsx`/`CropReplay.tsx`와
집중 브라우저 시험의 작은 계약으로 고정한다. 원 네 판본 선택을 유지하고 명시 새 판본/94자 ID,
현재 범위의 동일 원 sample·C/N/LAI·표/그래프/장면·전체 validation 표시와 계정/권리 실패 때
renderer/timer 정리를 검증한다. UI 착수 때 `12ui-design`/브라우저 skill을 적용한다.
그 다음 실제 소유 등록 계산→보호 loader/TLS→WebGL과 자원 정리로 native/웹 부모를 수용한다.

기존 window/view2–4집중시간을 helper1–2시간 + 화면/집중 브라우저1–2시간으로 분해한다.
SDK 수용 후 작은 웹 연결의 남은 예상은 위2–4 + native3–5, **5–9집중시간 잠정**이다.
실제 실패/통과로 갱신하며 CI·전체166일 등록 prefix/복원·생과/자원/Decimal 경제와 자료 확보는 제외한다.
실제 품종 입력·국내 독립 검증 자료·실제 농장 작물 Run0건, G0–G4/예측·추천·최종 날짜 보류는 유지한다.

## 2026-10-08 window 자식 수용

[실제 검증 기록](../research/web-crop-cycle-calculation-window-20261008.md): 새19개 포함 웹 전체719개·타입/빌드,
원량/UTC·전체 검증 정보·닫힌 source/union·순차/취소/settlement와 원104 source/임시 정리로 수용했다.
원 `open`을 유지했고 새 `openCalculation`을 추가했다. 새 HTTP/PG/브라우저·3D 실행은0이다.
다음 [화면3파일](web-crop-cycle-calculation-view-v1.md) 뒤 실제 PG/TLS/WebGL을 검증한다.
위 helper 추정은 실제 실적으로 대체하며 남은 작은 화면/native는4–7집중시간 잠정이다.
