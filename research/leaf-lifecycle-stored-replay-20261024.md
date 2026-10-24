# 저장 잎 생장·제거의 사실적3D — 2026-10-24

상태: **자체 합성 저장 결과의 사실적3D/사용자 화면 기능 수용**.
[화면 열기](http://localhost:5176/leaf-lifecycle-replay.html), [계약](../contracts/web-leaf-lifecycle-replay-v1.md),
[데스크톱](artifacts/leaf-lifecycle-stored-last-20261024.png), [모바일](artifacts/leaf-lifecycle-stored-mobile-20261024.png),
[실제24시점 장부](artifacts/leaf-lifecycle-stored-frames-20261024.csv), [기계 증거](artifacts/leaf-lifecycle-stored-replay-20261024.json)를 제공한다.
관리 시나리오를 고른 뒤 `저장 결과 재생`으로 원12시점을 확인한다. 새 계산이나 중간 생장을 만들지 않는다.

기존 실제 WebGL/제작 토마토 외형을 재사용했다. active만 현재3D·표·그래프에 표시하며,
제거 마지막 면적/나이·정확 제거 초와 pending 예약을 별도로 보여준다.
다른 잎을 제거해도 현재 잎의 제작 방향을 유지하고 명시 빈 목록은 줄기만 만든다.
scenario/artifact/frame URL로 메뉴/reload/뒤로 가기·키보드 탐색을 복구한다.
권리/hash hold 때 결과를 제거하고 WebGL2 불가 때 원 표/탐색을 유지한다.
빈 WebGL 시험은 명시 빈 geometry binding의 검사이며 새로운 빈 작물 Run을 뜻하지 않는다.

로컬 **신규22/관련84·106단위**, 전체 web 타입과 **새7/기존3·10브라우저**가 통과했다.
실제 기존 전용 Chrome/gateway의24 UTC/94추적 상태·73현재 잎 삼각형 면적을 원 저장값과 대사했다.
최대 상대 면적차는6.723195640234054e-15, 원 파일80GET/POST0·콘솔 오류/경고0,
폰트/레이아웃 준비 뒤 유휴 draw 변화0과 모바일 넘침0이었다. Chrome은 마지막 시점에 열어 뒀다.
초기 관찰자는 비활성 처음 버튼 클릭과 준비 전 idle 측정으로 중단됐고, 제품 코드 변경 없이 관찰자를 교정한 v3만 수용했다.

[집중 CI40057808874](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/40057808874)는183단위/42브라우저가 통과했다.
[전체 CI40057807134](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/40057807134)는2248단위/318브라우저가 통과했다. 두 CI의 source는f7d01b2이며 검사 수는 서로 합산하지 않는다.
이전 두 CI의 긴 통합 시험30초 실패를 보존했다. 원 검증을 시나리오/복구/재생으로 나누고 각 시험30초를 유지했다.
제품 코드3dfdfdb와 시험 수정f7d01b2를 구분한다.

새 정적 버전/entry와40원 파일을 기존 서버에 추가했고 이전 HTML을 덮어쓰거나 backend/DB·키를 재시작하지 않았다.
현재 미리보기의4entry 빌드270파일은 현재 소스에서 재생한 결과와 bytes/SHA가 같다.
더 넓은 crop 빌드294파일도 로컬/CI의 SHA가 모두 같다. 실제 미리보기270파일과는 entry 구성이 달라 별도로 대사했다.
12ui는 기존 변경 없는 승인 LayerDoc과 실제 캡처를 대조했다. 새 구매0·반복 CSS 수정0이다.
이미지 kit의 unanchored/DOM coverage0이며 픽셀 정밀 일치나 R2 수용은 아니다.
사용자 요구대로 래스터 식물/차트와 예시 숫자·없는 기능은 도입하지 않았다.

현재 자료는 자체 합성 per-tracked-shoot 연구 결과다. 원측정/미사용 독립 국내 작기0·국내 첫 품종 미확정이다.
실제 품종·한 작기/생산·자원·경제·시장/거시/수급·자율 선정, 농장 현재 권리/실행 연결·G0–G4와 전체 완료일은 남아 있다.
다음 핵심 연결은 잎 면적m2/추적 shoot와 기존 탄수화물mg_CH2O/m2_floor 모델의 단위·범위를 먼저 대조해야 한다.
면적을 임의 밀도/SLA로 LAI·질량/수확으로 변환하지 않는다. 관리 SourceRecord/농장 결속과 독립 자료 획득은 병행한다.

.25초 표본의 최대 PID533,692,416bytes/보호+소유 합992,825,344bytes로512MiB/1GiB·600초/로그4MiB 안이었다.
기존4root/원 파일·source/FD4→4·소유 잔류0을 확인했다. Windows Chrome/전체 host 수용은 아니다.
12ui 메타데이터 키 오류로 같은 kit를 무료 replay한 phase는 빌드로 세지 않았고 실제 재생은reproduce-v2다.
native CLI gpt-6.1-sol/xhigh, turn_context2026-10-24T02:38:42.380Z 원 LF SHA `57a54e2ef64c9843cff277231cdc50bdb59c98741cf9d7100e91ff835c102fe0`·재귀 CLI0이다.

기록 검증은 원 코드14개·로컬106단위/10브라우저·CI2248/318와183/42·실제24시점/94상태/73면적,
장부24행/화면2개 SHA·미리보기270파일과 로컬/CI294파일·상대 링크3,346개를 대사했다.
새 파일 staging을 포함한 공백/줄바꿈 검사도 통과했다.
