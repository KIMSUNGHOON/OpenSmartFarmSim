# 경제 이력 새로고침 뒤 키보드 시험의 대기 조건

상태: **집중 로컬 수용·수정 판본 hosted CI 미수용**, 2026-10-07 KST.
운영 기반의 완료 범위는 기존 `d19f7c0` 고정을 유지한다.

`4b0d559`의 [Web CI37587498493/job112680935707](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/37587498493/job/112680935707)는
단위522개·타입·빌드·감사0을 통과한 뒤 Chromium97개 통과/1개 실패로 종료했다.
경제 이력 새로고침 뒤 정확한 조건부 매출 문자열을 찾지 못한 실패다.
같은 SHA의 C0·Application·Authored PostgreSQL은 성공했으며 Backend는 이 기록 시점에 실행 중이다.

원 시험은 경제 요청 버튼의 비활성만 확인하고 이력 버튼에 Enter를 보냈다.
새로고침 중에도 경제 요청 버튼은 비활성이므로 완료를 구별할 수 없다.
제품은 이력 버튼도 비활성화해 조회 중 중복 행동을 막는다.
소유 합성 이력 응답을500ms 지연한 별도 Chromium 재현은 같은 문자열 assertion에서
1실패/본문6.8초·실제 종료1이었다. 관측 DOM에는 이력이 있지만 선택된 금액은 없었다.
이 결과와 제품의 `busy`/`inFlight` 경계를 근거로 시험의 비활성 버튼 키 입력이 원인이라고 판단했다.

수정은 이력 버튼의 **활성 확인 후 Enter**를 보내도록 시험에 대기 조건을 추가한다.
기존 키보드·정확한 소수 금액·미확인과0원 구별·POST 본문·현재 권리 거부 검증을 유지한다.
첫 시험의 합성 이력에500ms 응답 지연도 남겨 같은 조건을 검증한다.
이 지연은 서버 응답 fixture이며 assertion/service timeout 증가는 아니다.

| 실제 로컬 검증 | 결과 |
| --- | --- |
| 수정 시험 파일의 Chromium7개 | 7통과/13.7초·종료0 |
| 정확한 금액·현금 페이지·평가 보류·응답 유실·계정/권리 철회 | 기존 assertion 통과 |
| `npm run typecheck` | 종료0 |
| 제품 컴포넌트·Playwright 설정·의존성/잠금·workflow·기존 화면2개 | HEAD bytes 동일 |
| 원166일 동결55개 source | 모두 SHA 동일 |
| 임시 probe·기록한 실행 PID·포트5187 | probe 제거·PID 종료·포트 해제 |

시험한 사본은 수정 source와 화면2개 출력 경로만 다르며, 화면은 사설 디렉터리에 보존했다.
원 화면 파일은 덮어쓰지 않았다. 단일 browser worker/nice19로 실행했으며 원 nice15 계산은 계속 실행 중이다.
실제 DB나 외부 농장 자료를 사용한 시험이 아니며 전체98개 브라우저 재실행은 하지 않았다.
현재 native `gpt-6.1-sol / xhigh` 기록·원 실패/재현/수정 로그 hash·source 대사·정리는
[불변 receipt](artifacts/web-financial-history-keyboard-reference-20261007.json)에 있다.
재귀 CLI0회이며 실제 품종 입력·국내 독립 자료0건, G0–G4 `not_assessed`를 유지한다.
수정 판본의 hosted CI와 전체 Backend 수용은 별도다.
