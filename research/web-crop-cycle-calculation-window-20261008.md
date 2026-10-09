# 검증 계산 결과의 현재 범위 선택 — 로컬 수용

2026-10-08 KST. [범위 선택 계약](../contracts/web-crop-cycle-calculation-window-v1.md)의
`crop-cycle-calculation-window` 자식만 수용했다.
[고정 영수증](artifacts/web-crop-cycle-calculation-window-reference-20261008.json)에 실제 native Codex CLI
`gpt-6.1-sol / xhigh`·재귀 CLI0회·명령/종료/source/로그 SHA와 임시 정리를 기록했다.

## 변경과 확인한 동작

[기존 helper](../web/src/cycleCropWindow.ts)에 원/검증 계산 source의 닫힌 구분과
summary/page의 원 형식을 유지하는 union, 명시 `openCalculation`을 추가했다.
원 `open`과 현재 범위·이전/다음·선택·취소/settlement 알고리즘을 공유한다.
각 source의 schema를 확인한 뒤 해당 typed SDK를 호출한다. DTO 변환·필드 삭제·구형 cast·`any`는 없다.
정확성·가독성·구조·보안·비용을 검토했고, 승인된 기존 helper 하나 외 **104 source SHA를 보존**했다.

[새 집중 시험](../web/src/calculationCycleCropWindow.test.ts)은 SDK의 소유 공개 fixture를 재사용했다.
25시간·짧은 완료·확인 과거/빈/소수 초 hold·출력0 완료의 원량/UTC·전체 reference/manifest·검증 정보를 대사했다.
선택 index는 전체 저장 배열의 원 offset을 유지하며 보류 진단을 새 frame으로 만들지 않는다.
sample64/event8 한도, byte-short/마지막 범위·방문한 이전 offset·종류 전환과 현재 배열만 보존함을 확인했다.

일부 시험은 요청 limit만64/8로 echo한 **형식용 metadata 변경**이다. 원 수치 배열·UTC는 같다.
계정/ID 변경 시험의 ID 교체도 형식 시험이며 실제 새 농장 승인/서명 증거가 아니다.
원/새 source 전환 세 경우, 재진입 callback·대기 선택 대체, 취소/dispose 때 pending settlement와
최대 동시 원 요청1개·늦은 응답 비게시를 확인했다. 권리403/서버503·원 검증 정보/저장 시각 불일치 때
이전 summary/배열/선택/범위를 비우고 원점에서 다시 조회한다.

## 실제 검증과 자원

| 실행 | 결과 |
| --- | --- |
| 구현 전 같은 provenance 사례 | `openCalculation` 누락·1실패·종료1 |
| 구현 후 같은 사례 | 1통과 |
| 최종 새 범위 선택 집중 | **19통과 / 426ms** |
| 웹 전체 | **719통과 / 13.70초 / 21파일** |
| typecheck / build | 종료0 / 종료0 |

전체719개에 이번19개와 기존700개가 포함된다. 기존700개에는 원 window19개와 새 SDK178개가 포함된다.
반복 실행을 더해 고유 시험 수를 부풀리지 않는다. 최종 집중/typecheck/전체/build의2 core SHA가 같고,
각 실행에서 원104 source·로그 SHA·소유 임시 tree 정리를 확인했다. 계약 수용 절은 시험 뒤 추가했다.
nice19·Vitest 한 worker/파일 순차 실행을 유지했다. 표본 주 프로세스 최대 RSS349,556,736bytes는
worker 합산이나 WSL 전체 peak가 아니다. 빌드의500kB 초과 chunk 경고와 원 설정을 기록했다.
두 로컬 실행 handle은 종료 결과까지 소비했으며 소유 PG/API/브라우저 서버를 만들지 않았다.
제출 전 변경 문서11개의 상대 경로1,440개와 `git diff --check`를 확인했다.
57개 anchor 표기의 대상 절까지 검사한 것은 아니다. 종료한 시험은 반복 실행하지 않았다.

## 다음 단계와 보류

다음 [기존 화면3 core파일 계약](../contracts/web-crop-cycle-calculation-view-v1.md)은 원 네 판본과
명시 새 판본을 제공하고94자 결과 ID·원 검증 정보를 같은 UTC 표/그래프/3D에 연결한다.
`12ui-design`·브라우저 skill을 읽었고12ui CLI가 있음을 확인했다. Chrome DevTools MCP는 없어
기존 격리 Playwright/Chromium으로 실제 DOM·network·console·장면·접근성을 검사한다.
기존 승인 시안/자산과 close를 재사용하며 pixel fidelity를 자동 수용하지 않는다.

helper1–2시간 추정은 위 실적으로 대체한다. 남은 작은 화면/집중 browser1–2 + native3–5,
**4–7집중시간 잠정**이며 CI·전체166일 등록 prefix/복원·생과/자원/Decimal 경제·자료 확보는 제외한다.
이번 단계의 새 HTTP/PG/브라우저/WebGL·RHS 계산은0회다. 새로운 3D 수용으로 보고하지 않는다.
00:12 KST 같은 `353bffb` CI는 C0/웹/작성 PG 성공·Backend5분할 성공/분할5 진행,
앱 config 실패의 로컬 수정 hosted 수용은 후속이다. 원 run을 취소/rerun하거나 push하지 않았다.
실제 품종 입력·국내 독립 검증 자료·측정 농장 작물 Run0건, G0–G4 `not_assessed`와
생산 예측·미래 마진·작물 추천·공개 운영·최종 완료일의 보류를 유지한다.
