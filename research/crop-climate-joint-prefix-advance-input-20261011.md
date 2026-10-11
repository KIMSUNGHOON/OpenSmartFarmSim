# 연속 저장 시점 관측의 새 입력 재현 — 2026-10-11

**A1 입력/관측 계약을 수용했다. 실제 계산 중 두 시점 이상 갱신되는 A2는 미수용이다.**
현재 사용자5174의 [P6b 단일 running 시점→terminal 연결](crop-climate-joint-prefix-user-activation-20261011.md)은 유지한다.
새 [관측 계약](../contracts/crop-climate-joint-prefix-advance-observation-v1.md)을 정의하고
[기계 증거](artifacts/crop-climate-joint-prefix-advance-input-reference-20261011.json)에 실제 입력 재현을 기록했다.
증거 SHA-256은 `3026fd88b60872a0af6023181c87aa4ba6a79273cf5b68775bc3424fc4f96256`이다.

native Codex CLI `gpt-6.1-sol`/`xhigh` context SHA는
`874b8d476241c89afe78d5fede0fe6a72963e60d15c42c27a082a64bf15b009e`이며 재귀 실행0이다.
농업 계수나 새 방정식을 제안/채택하지 않았다. 원 normal의 scenario·4개 profile/notice·2초 격자·
관리 사건0/8/16·원 UTC를 유지하고 종료16→64걸음/출력3→9시점만 확장한 새 소유 합성 판본이다.
기간은32→128초다. 새 source/context/time-binding/evidence와 소프트웨어 검토·결정 ID를 생성했으며
기존 사용자 입력/키·권리·runtime은 변경하지 않았다. 새 입력은 아직 사용자 서버에 접수하지 않았다.

## 실제 계산/복원 대사

원 tool88508의 child/guard/tool exit0,2.705초를 확인했다.
일괄 budget128의1chunk와 budget8의9chunk/매번 checkpoint bytes 복원에서
모든9sample/3event·마지막 상태와 최종 checkpoint bytes가 정확히 일치했다.
수지/범위 검사를 유지하며 수치 hold는 없었다.
원 출력 UTC는 `2026-10-01T00:00:00.123456Z`부터16초 간격으로
`2026-10-01T00:02:08.123456Z`까지다. 최초/최종 원 수치가 달라짐도 확인했다.
현재 자료·품종의 현장 정확도나 독립 수치 oracle을 검증한 것은 아니다.

단일/합산 peak RSS136,712,192/707,489,792bytes,0.25초 관측으로512MiB/1GiB 이내다.
main1915파일·원본2,148항목·두 frozen source/자산·FD4→4·소유 잔여0과 보호 root4를 보존했다.
20:55 KST에5173/5174 HTTP200을 확인했다.

## 새 관측 모드와 다음 수용

기존 reference MJS의 `live-advance` 모드는 서로 다른 원 UTC2개 이상,
전진한 publication sequence와 바뀐 원 수치를 요구한다. 동일 UTC의 다른 selector는 갱신 횟수로 세지 않는다.
각 장면의 실제 관측 벽시계 UTC와 두 번째 시점의 원 screenshot을 기록하도록 준비했다.
기존 원 응답/표·그래프·50구획·온도/WebGL 대사와 terminal 원값/binary64·UTC/재접속 검사는 유지한다.
`node --check`는 exit0이다. **새 모드의 실제 브라우저 실행은 아직 하지 않았다.**

현재 operator는 시작할 때 input resolver를 고정한다. A2는 새 입력의 farm/권리/서명 접수를 확인하고
versioned runtime/review/rights를 연결한 정상 재기동 뒤 실제 자동 worker/브라우저를 사용한다.
원 DB/결과·키/기존 권리 항목/입력과 원 두 주소를 보존·복구하고, actual DB 종료 시각과
장면 관측 시각을 대조한 뒤 두 시점 이상 계산 중 갱신을 판단한다.
관측을 위한 worker 정지/sleep·저예산 전환·가짜 프레임은 사용하지 않는다.
P6b browser의1GiB 근접 관측 때문에 필요한 유지보수/복구를 먼저 준비한다.

A2의 실제 검증/보존0.5–1.5집중시간은 잠정이며 실행 비용·자료 접수·자원 관측 뒤 갱신한다.
현재 실제 농장 Run/국내 독립 자료0·G0–G4 `not_assessed`와 최종 UI/전체 작기·
생산/자원·Decimal 경제/미래 마진/추천의 보류는 유지한다.
새 build·전체 CI/remote·서비스 재기동/새 사용자 작업은 실행하지 않았다.
