# 잎 생애 SDK와 현재 잎 adapter — 2026-10-24

상태: **strict SDK/순수 active adapter를 소프트웨어 범위로 수용**.
[계약](../contracts/web-leaf-lifecycle-sdk-v1.md), [기계 증거](artifacts/leaf-lifecycle-sdk-20261024.json),
[복사한40파일 장부](artifacts/leaf-lifecycle-sdk-files-20261024.csv)를 제공한다.
구현 commit은 `157c159d16e52f78af9dfd9fcb7b662f6806b0be`이다.
[원 export](crop-leaf-lifecycle-export-20261024.md)의 자체 소유 두20파일을 bytes/SHA 그대로 복사했다.
appearance/관리/stem 각각의 명시 use/display/redistribute를 확인했다. 농장 wrapper/비공개 설정은 복사하지 않았다.

loader는 고정 index/root SHA·40code/모델/표시 정책, 원 두 program/준비/초기 state·stem 연결과 권리3종,
원 sample의 input/state chain을 검사한다. DTO는 같은 UTC stem·정확 현재/제거 마지막 시각,
declared/active/removed/pending 순서/ID·단위/개수/저장 면적을 검증한다.
JS 합산의 반올림 허용은 합계 검증에만 사용하며 원 면적/합계를 바꾸거나 생장을 계산하지 않는다.
원 bytes의 신뢰는 loader의 SHA 검증에서 온다. 순수 decoder는 구조/연결 검증기이며 호출 자체가 bytes 인증이나 G0 판정은 아니다.

adapter는 active leaf ID/부착/원 면적을 복사해 기존 MorphologyScene 입력 구조로 전달한다.
removed 마지막 상태와 pending 예약은 원 DTO에 남는다. 입력을 바꾸지 않고 빈 active 목록은 빈 목록으로 유지한다.
기존 도형의 최소1잎 전제는 다음3D 단계에서 수정·검증한다. 이번 빈 목록 시험은 adapter만의 수용이다.

## 통과한 검증

RED는 새 SDK 모듈 부재로 수집 실패/검사0이었다. 구현 뒤 **신규76검사**, 전체 web `tsc --noEmit`,
독립 SDK 라이브러리 번들이 통과했다. 원24 DTO/94추적 상태와 active 복사 투영, 현재/마지막/예정 구분을 확인했다.
단위/수치/ID/부착/curve/출현·나이/선언·시각/개수/합계/권리/코드/chain/확장 필드,
20파일 각각의 bytes 변조·다른 관리 원문 혼합·누락/2MiB·사전/중간/마지막 abort에서 대체 결과 없이 거부했다.
기존 SDK 시험 묶음·전체 웹 단위/전체 웹 빌드·브라우저는 반복하지 않았다. 기존 source는 수정하지 않았다.

35,010bytes 번들은 원 SDK/fixture·공유 file IO/형태 reader와 두 fixture의6모듈만 포함했다.
Three/React·작물 생장/준비/producer 모듈은 포함하지 않는다. 별도 native Node와 소유 loopback HTTP에서
**실제40 GET/POST0**으로 두20파일을 읽었다. 원24 DTO/94추적 상태와24 active 투영이 모두 같았다.
모든 숫자는 원 저장값이며 새 crop state를 만들지 않았다. 이 시험은 브라우저/WebGL 시험이 아니다.
임시 HTTP 서버/소켓을 종료했고 원 공개40파일·lifecycle62blob·appearance52blob/stem29blob,
총183파일의 bytes/metadata를 보존했다. 공개40파일 SHA는 앞선 export와 같다.

모든 phase에서 기존4root/2,793감시 항목·source·FD4→4·소유 잔류0을 확인했다.
전체 타입 검사의 최대는 PID497,074,176bytes/보호+소유 합957,689,856bytes였다.
.25초 표본·512MiB/PID·합1GiB/600초/로그4MiB 안이며 Windows Chrome/전체 host 수용은 아니다.
native CLI `gpt-6.1-sol/xhigh`, turn_context `2026-10-24T02:21:52.599Z` 원 LF SHA
`d0a12893226d67feb8e0f1be2ba5666809bfd50ae756b42b51fe364a06fe09c9`·재귀 CLI0이다.
새 의존성/백엔드·DB·키·사용자 runtime/화면 변경0이다. 새 hosted CI 결과는 수용하지 않았다.

기록 검증은 코드3개/graph code40개·Vitest76개·공개40파일의 원 export bytes/SHA와 번들35,010bytes/6모듈을 대사했다.
상대 링크3,350개와 새 파일 staging을 포함한 전체 변경의 공백/줄바꿈 검사도 통과했다.

## 다음 산출물과 외부 의존성

다음은 **기존 사실적3D·표/그래프/복구 연결과 실제 브라우저·사용자 적용**이다.
같은 원 UTC/24시점·ID/면적을 사용하고 active만 현재 형상으로 표시한다.
removed의 마지막 면적/나이·정확 시각과 pending 예약은 별도로 설명한다.
원 단면 삼각형 면적/표/그래프를 대사하고 빈 현재 목록을 고정 외형 잎으로 대체하지 않도록 도형 전제를 수정한다.
시나리오/frame·메뉴/새로고침 복구/키보드·모바일/유휴와 원 화면/자료를 실제 브라우저로 확인한다.
저장 시점 사이 가짜 생장이나 제거 동작을 만들지 않는다. 기존 서비스 정적 경로/제작 외형을 재사용하며 12ui/browser workflow를 적용한다.

SDK50–100집중분 예상은 위 실적으로 대체한다. 다음3D는 빈 geometry/계약10–20분+연결25–45분+
브라우저/기존 서비스 적용25–50분+기록10–20분으로 **70–135집중분**의 낮은 신뢰 추정이다.
실제 첫 렌더링/경로 장애가 있으면 원인별로 갱신한다. 농장/runtime·외부 자료 확보 시간은 포함하지 않는다.
현재 화면에는 새 제거를 적용하지 않았다. 농장/현재 SourceRecord·서명/실행과
[국내 독립 자료 획득](independent-domestic-cherry-tomato-data-20261024.md)은 병행한다.
원측정/미사용 독립 국내 작기0·국내 첫 품종 미확정, 생산/자원·Decimal 경제·시장/거시/수급·자율 비교,
R2/첫 cold shader·G0–G4와 전체 완료일 미정을 유지한다.
