# 같은 load의 두 commit 읽기 비교 — 2026-10-20 KST

[기계 증거](artifacts/solar-same-load-two-read-evaluation-20261020.json) · [선행 동시 진단](solar-current-worker-api-diagnostic-20261020.md).

## 범위·사전 기준

storage._Files._load의 첫 pass chain 검증 뒤 두 번째 pass가 같은 commit을 다시 파싱한다. 첫 pass의 값은 외부로 노출되지 않는 사설 후보에서만 보관했다. 두 번째 pass도 실제 파일 보안·전체 bytes/SHA를 새로 확인하고 원 _seen/참조 예산 처리를 실행했다. raw 한도1MiB, 같은 load 안 수명이며 load/prepare/current/resume 간 재사용은0이다. 기존 whole-load transcript/clone 후보와 다른 경계다. 제품 app은 d477b74b… 원261파일 그대로다.

사전 비용 기준은 실제 전체 quantum 평균2% 이상, 두 ABBA 짝 모두 개선이다. 원 CASE6/64/output0..64/8/chunk1을 유지하고41까지 준비한 뒤 worker before/private advance/독립 confirm의42..45를 baseline/candidate/candidate/baseline으로 한 번 비교했다. 사전 native CLI gpt-6.1-sol/xhigh·원행/후보/test SHA를 결속했다. 재귀 CLI/하위 에이전트는0이다.

## 결과·미채택

| 순서 | 모드 | 원 quantum | 실제 시간 |
|---|---|---|---|
| 1 | baseline | 42 | 8.280512258초 |
| 2 | candidate | 43 | 8.193023253초 |
| 3 | candidate | 44 | 8.162251599초 |
| 4 | baseline | 45 | 8.255593265초 |

평균 **1.093550539%**, 짝별1.056565129/1.130647586%로 **2% 기준 미달·미채택**이다. 1MiB 한도를 높이거나 같은 후보를 재실행하여 유리한 timing을 선택하지 않는다. 후보마다5 load·각25 hits, 약1,026,589–1,026,653bytes를 보관하고 동일 크기의 실제 파일을 재확인했다. 원 bytes/counts/UTC84/86/88/90.123456Z·current15와 순서·SQL9,929/role273/원천2,280 및 SQL map은 같다.

1 pytest 통과는 사설 비용 실현성만 확인했다. 모든 codec/global alias·가변 소유권·변경/오류·보안 경계는 미입증이다. 원82의 현재 source 검사를 재실행하거나 새 제품 후보를 수용한 것으로 세지 않는다. 큰 raw cap의 효과도 추론하지 않는다.

## 자원·잔여

guard148.587038초·단일130,912,256/합892,030,976bytes·중단 사유null·FD4→4·5root/원본2,148/두 frozen UI 보존·소유 PG/비좀비/임시/passfile 잔여0이다. log SHA c89b1637ca1b1335db9d00322909f1ea794f4cee751f480142176e25abde08e1이다. 원문·로그·후보는 비공개이며 원본/토큰/농장 자료를 게시하지 않았다.

원 정상64·계산 중WebGL·새 Solar 사용자 적용·실제 농장 자료/독립 검증·G0–G4는 남는다. 실제 농장 Run0·새 Solar 미배포·전체 완료일 미정·goal active다.
