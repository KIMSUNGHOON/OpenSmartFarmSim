# 기관 native 관측기 보완 — 2026-10-21 KST

[이전 진행 기록](organ-native-integration-progress-20261020.md) ·
[기계 증거](artifacts/organ-native-observer-recovery-20261021.json).
현재 native Codex CLI `gpt-6.1-sol` / `xhigh`에서 판단했으며 재귀 CLI/하위 agent 호출은0이다.

## 두 번째 실행에서 확인한 실패 범위

source `88d766e`의 [CI39441263299](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/39441263299)는
전체 웹36파일/1,886단위·Chromium256·타입/빌드/audit를 통과했다. native는 종료1이었다.
67.426522초·단일419,815,424/합761,106,432bytes·267표본/.25초·FD6→6,
source 보존과 소유 프로세스/임시/자격증명 잔여0을 확인했다. 자원/600초 한도에 의한 종료가 아니다.

단계 기록에는 원6시점, 모바일, 재접속, 권리 복원, 계정 복원의 총10개 실제 WebGL/표 관측이 있다.
numeric hold의 장면 제거와 계정 거부 단계도 지났다. 원17응답 본문은 모두200으로 기록됐으며,
마지막 응답 관측의 종료를30초 기다리다 실패했다. 브라우저를 닫을 때 미완료 관측2개가
`response.body: Target page, context or browser has been closed`로 끝났다.
최종 부모의 서버/브라우저 원 body 해시 및 DB row/쓰기0 대사는 실행되지 않아 전체 통합은 미수용이다.

`web/src/api.ts`는 `!response.ok`에서 status를 오류로 바꾸며 `body.getReader()`를 호출하지 않는다.
시험 관측기는 모든 응답에 `response.body()`를 기다렸고, SDK가 소비하지 않는 오류 경로까지
완료 본문으로 취급하려 했다. 두 번째 source는 헤더를 본문 대기 뒤에 기록했으므로 미완료2개의
실제 status/path는 이 영수증에 없다. 이 빈 증거를403/422 본문 해시로 채우지 않는다.

## 수정과 유지한 검증

제품 API/UI/계수/결과는 바꾸지 않았다. 세 번째 관측기는 다음을 구분한다.

- 모든 응답의 실제 status/헤더와30초·no-store를 먼저 기록한다.
- 성공 응답은 원 body 길이/SHA256을 실제 upstream과 대사하고 기존 SDK 관측기로
  끝까지 읽은 횟수/경로·30초를 추가 확인한다.
- SDK가 거부한403/422는 실제 헤더와 현재 수치/장면 제거·복구로 검증한다.
  오류 본문의 bytes/hash는 검증된 upstream proxy만 관측하며 브라우저 소비 증거로 보고하지 않는다.

[계약](../contracts/crop-organ-native-acceptance-v1.md)에 이 관측 범위를 명시했다.
원 성공 데이터 대사, 권리/계정·numeric hold, 원 row/선택 DB counts·조회 계산/쓰기0,
512MiB/PID·합1GiB/600초/.25초·소유 정리 조건은 유지한다.

source `92c6456`의 [CI39444301162](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/39444301162)를
한 번 접수했고 현재 실행 중이다. 실제 완료 자료를 확인하기 전 체크를 해제하지 않는다.
hosted synthetic 통합과 역사적 row 호환성·WSL5root 동시 용량/사용자 적용, 원 디자인/기관 family/U1,
생산/자원/경제·실제 자료/관문과 전체 goal 완료는 별도다. 전체 완료일은 미정이며 goal은 active다.

두 번째 artifact는 GitHub ZIP digest와 대사했다. 다운로드 guard는 종료0/3.481038초·합619,565,056bytes였다.
세 번째 검증 중이라는 진행 JSON도 두 주소에 게시했다. 실제5173/5174의200·같은 bytes/no-store와
원 두 HTML/환기2,173파일·5root/원본 보존을 확인했다. 게시 guard는 종료0/0.346051초·합586,440,704bytes다.
각 guard의 FD4→4·소유 프로세스/PG/임시/자격증명 잔여0을 확인했고 새 UI 활성화나 DOM 재검사는 하지 않았다.
