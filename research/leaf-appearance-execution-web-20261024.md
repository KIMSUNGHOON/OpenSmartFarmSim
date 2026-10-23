# 정책 기반 잎의 실제 계산과 3D 연결 — 2026-10-24

상태: **자체 합성 owned preview의 실행 화면 기능 수용**.
[실제 화면](http://localhost:5176/leaf-appearance-execution.html?job_id=9dbcca83-3b81-4171-862d-2953a0698eb6&frame=11)을 전용 Chrome에 마지막 시점으로 열어 뒀다.
[계약](../contracts/web-leaf-appearance-execution-ui-v1.md)과 [기계 증거](artifacts/leaf-appearance-execution-web-20261024.json)를 함께 확인한다.
[공개 이미지](artifacts/leaf-appearance-execution-fixture-20261024.png)는 공개 합성 fixture 캡처이며 실제 인증 API의 캡처·토큰·원 요청은 공개하지 않았다.
최종 제품 UI·실제 품종/농장 작기·R2·생산량/경제/추천 수용은 별도다.

## 현재 동작과 검증

입력 확인 → 명시 새 접수 → 실제 queued/simulating/succeeded 또는 보류/취소 → 같은 작업의 저장 잎·줄기3D다.
원 **12시점/47면적·3→5잎**의 UTC/ID·실제 삼각형 면적·표/그래프를 대사했다. 저장 시점만 재생하며 임의 완료율이나 중간 생장값은 만들지 않는다.
별도 token/job/pending/frame 키와 job_id/frame URL을 쓴다. 메뉴/reload·재연결은 같은 작업과 선택 시점을 유지하고 접수 응답이 없으면 같은 body를 명시 재확인한다.
현재 권리·무결성/연결 거부 때 3D·표·그래프를 제거한다. API에 없는 정책 숫자나 static fixture를 현재 실행 결과로 표시하지 않는다.

| 최종 범위 | 결과 |
| --- | --- |
| 로컬 타입 / 집중 단위 | 통과 / **175개·6파일**, SDK68 포함 |
| 로컬 Windows Chrome | **25개**, 새 UI12 포함 |
| [전체 웹 CI](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/40037515156) | **2150단위 / 311브라우저**, 타입/build/high audit 통과 |
| [분리 3D CI](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/40037517078) | **85단위 / 35브라우저**, 타입/별도 build/high audit 통과 |
| 최종 실제 Chrome | 원12시점·47면적/18회 재방문 대사, 메뉴/reload/모바일·재생/유휴, GET4/POST0 |
| 실제 새 계산 / 취소 / 현재 권리 | 자동 완료 / 실제 취소·게시0 / 철회 제거·같은 결과 복원 |

두 최종 CI의 코드 판본은 `7418842b1e5ef9c0beee641e7e5b40b4ec8b81e7`이다. 분리 CI와 로컬 빌드247파일은 SHA까지 같았다.
최종 삼각형 면적 상대차 최대는 **6.723195640234054e-15**, 실제 현재 조회4개 중 본문 완료 최장은 **20.471126초**였다.
요청별30초를 유지했다. 두 요청을 쓰는 observe 전체가30초 이내라는 주장은 하지 않는다.
최종 warm 재생의 pageerror/console은0이었다. 새 계산 중에는 snapshot503이2회 있었고 제한 GET 재조회로 같은 작업이 자동 복구됐다.
새 작업의 전체 probe265.499초는 입력 확인·대기·저장 재생/reload를 포함하며 순수 계산 시간이 아니다. 실제 계산 접수1회·자동 POST retry0이었다.
실제 권리 철회422 때 표시 제거, 복원 뒤 같은 result/root·마지막 시점과 POST0을 확인했다.
기존 첫 cold 셰이더 경고·넓은 동시성/U1·R2는 별도 보류다. high audit는 통과했으나 기존 moderate2건과811kB chunk 경고를 없앤 작업은 아니다.

## 발견한 오류와 화면 대조

실제 대기 작업 취소는 `canceled / cancel_accepted=true / cancel_requested=false`였다. 최초 SDK가 이를 거부해 화면만 queued로 남았으며 서버의 취소는 완료됐다.
실패와 RED1/66pass를 보존한 뒤 terminal canceled 또는 pending request를 수용하도록 교정했다. 최종 SDK68·브라우저25와 새 작업의 실제 취소가 통과했다.
최초 취소 작업도 canceled/게시0이며 이력을 지우지 않았다. 초기 optional policy 타입 오류도 수정/기록했다. 이전 CI2147/310 통과는 이 교정의 최종 CI와 구분한다.

12ui는 기존 승인 Branch a/b/c의 변경하지 않은 LayerDoc과 실제 Chrome의 계산/완료/권리 보류 캡처를 대조했다. 세 로컬 이미지 kit는 settled/새 구매0이다.
URL 캡처는 Linux sharp를 win32-x64에서 읽지 못해 kit 전에 실패했다. 이미지 경로는 unanchored/DOM coverage0이며 selector·픽셀 정밀 일치 증거가 아니다.
토큰 패치에 반복 CSS 변경이 없어 기존 CSS를 유지했다. 사용자 요구의 실제 WebGL/원 숫자·현재 거부를 우선해 raster 식물/차트·예시 관리 입력/숫자·잔상 장면과 없는 배경 자산은 도입하지 않았다.
이 화면 구성 검토는 최종 사실감 R2 수용이 아니다.

## 보존과 다음 한 단계

기존 두 DB의25표 전체와 appearance DB 원25표 행을 보존했다. 새 작업3개와 정상 결과1/사건·시도만 추가됐다. 두 취소 작업의 게시는0이다.
현재 권리 정책은 같은 bytes/권한으로 복원했고 그 외 **2,672파일**의 bytes/metadata와 원 배포262파일을 보존했다.
새 버전 자산을 추가하고 새 entry HTML 포인터만 한 번 교체했다. 기존 root/다른 화면·backend/DB/키 재시작0이다.
현재 인증 종료는 **2026-10-25 06:17 KST** 설정이며 미래 가동률/G4 증거가 아니다.

.25초 표본의 최대 PID **520,998,912bytes**, 보호+소유 합 **1,058,295,808bytes**였다. 기존 PID512MiB/합1GiB·600초 범위와4root/source·감시 항목/FD4→4·소유 잔류0을 확인했다.
Windows Chrome은 WSL 합에 넣지 않았고 전체 host 용량을 수용하지 않는다. backend 전체/독립 농장·실제 품종·공개 운영 검증은 실행하지 않았다.
추가로 로컬 링크3,376개(중복 포함)·선택 런타임9개 SHA·소유 Chrome PID/profile/port·실제 자격증명 비노출을 대사했다.
현재 CLI **gpt-6.1-sol/xhigh**, 실제 turn_context2026-10-23T22:28:13.142Z의 원 LF SHA `15037c4755193a0db45d6e87a2a3bef697b55f4cd7995b8ab70351c506b3dfb2`·재귀 CLI0을 기록했다.

다음은 [명시 잎 제거의 원문 경계](crop-declared-leaf-removal-primary-sources-20261024.md)에 근거한 **같은 정확 시점의 전체 잎 제거 순수 커널**이다.
원 anchor·출현/제거 이력과 남은 면적/개수·마지막 잎 제거의 빈 현재 목록을 대사한다. forcing/출현 결속 → 새 저장/같은 UTC3D → 별도 질량 수지·생산/자원·Decimal 경제·시장/거시/수급·자율 비교 순서를 유지한다.
면적 감소를 곧바로 탄소/수확량으로 바꾸지 않는다. 이전 UI70–120집중분 예상은 이 실제 구현/CI·교정 기록으로 대체한다.
다음 순수 커널은 계약/새 state20–40분 + 구현30–60분 + 독립 면적/경계·기존 회귀30–60분 + 기록10–20분 = **90–180집중분**의 낮은 신뢰 추정이다.
forcing·새 저장/UI와 실제 자료 수신은 제외한다. 실제 품종/독립 국내 작기0·예측/마진/추천 게시 관문·전체 완료 날짜는 미정이다.
기존 native goal은 도구상 active이며 교체 완료/전체 완료로 표시하지 않는다.
