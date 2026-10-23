# 정책 기반 잎의 실행 SDK — 2026-10-24

상태: **현재 API를 읽는 strict SDK 수용**. 새 UI/같은 job3D는 후속이다.
[계약](../contracts/web-leaf-appearance-execution-v1.md)과
[기계 증거](artifacts/leaf-appearance-execution-sdk-20261024.json)에 실제 native Codex CLI
**gpt-6.1-sol / xhigh**의 turn_context 지문·재귀0, 검사·source/자원 관측을 기록했다.
선행 [사용자 API](leaf-appearance-execution-live-20261024.md)와 [유효기간 갱신](preview-finite-lifetime-renewal-20261024.md)을 유지했다.

## 구현과 신뢰 경계

새 client는 preview/submit/status/observe/manifest/frame/replay/cancel의 appearance 경로만 사용한다.
닫힌 요청/상태·결과/서명 metadata, 같은 job/result/parent·farm/source/binding/최초 시각을 확인한다.
manifest의 정수/문자열/boolean 원 root SHA와 원 sample_count/source/preparation/population/stem 참조를 대사한다.
원 프레임의 UTC/ID·정확 출현/나이·부착/단위/합계·안정된 기관 목록/정책·프로필 참조를 검사한다.
다른 모델/순서/누락·늦게 나타나는 기관과 바뀐 ID·미완료 결과를 거부한다.

프레임 원 bytes/입력 정책·프로필·수치/서명의 현재 검증은 원 서버 authority/reader가 수행한다.
SDK는 인증된 현재 응답의 형식과 참조 관계를 검증하며 독립 수치 검증이나 과학 관문으로 승격하지 않는다.
Python float frame JSON을 JS로 재해시하지 않는다. 실제 서버의 frame_sha256과 원 값은 보존한다.
현재 API에 없는 정책 수치를 만들어 반환하지 않으며 고정 연구 root/기관 수를 실행 결과로 대체하지 않는다.
다른 root/비재배포 입력의 형식 결속도 집중 반례로 확인했다.

각 요청30초·2MiB/UTF-8·no-store/redirect=error/credentials=omit와 caller abort를 적용한다.
POST 자동 retry/fixture fallback은 없고503/504 등의 HTTP status를 보존한다.
observe는 매번 현재 status→같은 완료 summary의 replay를 읽는다. 새 현재422/503 거부 때 이전 replay를 반환하지 않는다.
frame은 현재 manifest→같은 summary의 서명 frame/index를 확인한다.

## 통과한 검증

| 범위 | 결과 |
| --- | --- |
| 신규 단위 제어 | **65** |
| 기존 실행 client/저장 appearance/common stem 관련 제어 | **99** |
| 최종 고유 단위/관련 합계 | **164** |
| 전체 웹 타입 검사 | 통과 |
| SDK 별도 번들 | **26,765bytes**, public assets 복사0 |
| 실제 현재 API SDK probe | **1**, GET10/POST0 |

부재 RED의 module 수집 오류1 뒤 최초54검사를 통과했다. 기관 drift/현재 거부/범위 반례를 보강했다.
다른 family 반례의 job ID도 같은 값으로 맞춰 오직 다른 모델을 거부하는지 검토한 뒤 최종164개를 통과했다.
반복한 검사/초기54개/RED 실패는 최종 합계에 추가하지 않았다.

실제 번들에서 `localhost:5176`의 원 작업 `1b4cd63a-d6b1-4924-90c4-22be4b50c7d3`를 읽었다.
preview/status/manifest·첫/마지막 frame·observe 전체 replay와 원 canceled probe의 null 결과를 확인했다.
원 **12시점/47면적의 모든 JSON 값·원 UTC/ID·parent/result/root·최초 calculated_at**이 같았다.
첫/마지막의 원 server frame SHA도 저장된 Python canonical 원 SHA와 같았다. static 응답 대체나 POST는0이었다.

실제10개 GET의 body 완료까지 최장은 **12.291077초**였다.
status→replay의 observe는 두 HTTP 요청 합계 **24.173746초**이며 요청별 기존30초 예산을 유지한다.
세 DB의25표 원 행과 입력/source/서명·저장 **2,673파일**의 bytes/metadata를 보존했다.
현재 데이터 읽기 수용이며 계산 중 같은 POST retry/동시 U1 수용과 구분한다.

.25초 표본의 PID 최대는 **417,492,992bytes**, 보호+소유 합은 **924,069,888bytes**였다.
모든 phase는 PID512MiB/합1GiB·600초 안이며 원4root/2,504감시 항목/source·deployed UI를 유지했다.
일시 자손0·controller FD4→4였다. Windows Chrome을 WSL 용량 증거에 포함하지 않았다.
기존5개 web source는 byte/hash가 같다. backend/원 수치 모델·DB/키/사용자 UI는 바꾸지 않았다.

전체 웹 단위 suite/전체 UI build·이번 hosted CI·브라우저와 사용자 배포는 미실행이다.
이번 번들은 SDK만 검증하며 현재5176의 표시 화면을 갱신하지 않았다.

## 다음 사용자 확인점

다음은 새 진입/실행 페이지에서 **같은 실제 작업을 사실적인 잎3D·표·그래프에 연결**하는 단계다.
기존 실행 페이지128행과 공통 재생83행을 재사용하며 별도 저장 키·URL의 job/frame을 유지한다.
provided replay를 새 appearance source로 전달하고 API에 없는 정책 값을 표시하지 않는다.
기존 화면과 토큰/DB·입력을 보존하며 메뉴/reload/재연결의 같은 ID·추가 POST0,
실제 leaf 삼각형 면적/UTC·현재 권리 철회 때 수치/장면 제거와 실제 Chrome/모바일을 대사해야 한다.
새 계산의 실제 queued/simulating/succeeded·동일 pending request 유지도 확인한다. 임의 완료율은 만들지 않는다.

분해는 페이지/상태·entry 연결20–35분 + CI/실제 Chrome·원 값/철회·보존40–65분 + 불변 배포/기록10–20분 =
**70–120집중분**의 낮은 신뢰 추정이다. 전체 작기·자료 확보와 최종 R2 시간은 제외한다.
실제 품종/초기 기관·독립 국내 작기0/승인 farm Run0, 관리·생산·자원/Decimal 경제·시장 거시/수급·자율 비교,
최종 사실감 R2/첫 cold 셰이더 경고·G0–G4와 전체 완료 날짜 미정을 유지한다.
