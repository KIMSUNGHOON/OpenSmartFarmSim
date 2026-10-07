# 등록 계산의 누적 저장·재열기 비용 — v1 개발 계약

2026-10-08 KST. native Codex CLI `gpt-6.1-sol / xhigh`; 재귀 CLI0회.
작업은 `crop-cycle-calculation-prefix-cost`이며 [현재 조회 계약](crop-cycle-calculation-query-v1.md)과
[전체 작기 부하 계약](crop-cycle-burden-v1.md)의 남은 계산 비용을 실제 측정한다.
새 native 시험과 독립적으로 설계할 수 있지만 PG/계산/브라우저 실험은 순차 실행한다.
이 계약의 작성이나 작은 비용 측정으로 전체 등록166일/부하 부모를 완료하지 않는다.

## 현재 근거와 변경 경계

[원166일 실행](../research/crop-cycle-full-rhs-durable-completed-20261007.md)은1,816,704걸음과
14,567commit을 실제 완료했다. 이는 등록 농장 서버의 처리량 증거가 아니다.
현재 `CalculationServerCustody.advance`는 호출마다 `_open`으로 계산 context/journal을 열고,
`_Journal._progress`는 선택한 전체 prefix의 수지 검사를 수행한다.
`CalculationFarmBinding.current`는 현재 농장 등록/권리도 반복 확인한다.
[새 native 시작 관측](../research/web-crop-cycle-calculation-native-started-20261008.md)의 실제 호출 시간은
수식·파일 검사·농장/DB 확인을 모두 포함하므로 그중 하나의 비용으로 표시하지 않는다.

core3파일은 `research/crop-cycle-calculation-prefix-cost.py`,
`backend/tests/crop_cycle_calculation_prefix_cost_smoke.py`, 이 계약이다.
기존 `crop-cycle-burden-profile.py`의 `Costs` 계측기를 재사용한다.
현재 모델/계수·공식 계산/저장/권리·schema·SDK/UI·잠금/CI는 보존한다.
실측 결과가 수정 필요성을 입증하면 해당 제품 변경은 별도 작은 계약/검증으로 진행한다.

## 측정 순서와 수용 기준

1. **계측기 대사:** 실제 함수 wrapper가 정상/예외 모두 원 함수를 복원하는지 검사한다.
   inclusive/exclusive 시간과 호출 수를 분리하며 중첩 시간을 더하지 않는다.
   작은 공식 계산의 계측 전후 원 sample/event·121상태/seed/clock/cursor/누적을 대사한다.
   boolean·음수·범위 밖 예산과 이미 사용한 실행 의도는 계산 전에 거부한다.
2. **실제 등록 작은 기준선:** 실제 SCRAM/현재 농장 권리의 원120걸음 정상·수치 hold를 사용한다.
   한 호출과 여러 bounded 호출/새 서비스 재열기의 최종 원량·UTC·수지를 동일하게 유지한다.
   완료 후 DB put/retry/read의 RHS0, 현재 계정/권리 철회와 원 행·파일 보존을 확인한다.
3. **누적 prefix 관측:** 고정25시간 입력에서 최대32개의 실제 bounded advance를 관측한다.
   각 commit의 steps/counts/bytes/files와 context factory·입력 증명 검증·수식·prefix QC·
   journal 검사/서명·farm 현재 검사·DB 게시 비용을 가능한 호출 경계에서 분리한다.
   의도적 관측 종료는 `yielded` 그대로 기록하며 전체25시간/작기 완료로 바꾸지 않는다.
   저장 상태를 재열어 같은 checkpoint를 확인하고 읽기 RHS0·현재 권리 거부를 검사한다.
4. **전체 입력의 실제 등록 관측:** 원166일 입력/출력 격자·사건을 보존하는 새 등록 농장·
   경제 가정/작기 범위를 먼저 실제 검증한다. 작은 농장의 기간 검사를 우회하지 않는다.
   같은 전체 입력에서 초기/증가한 prefix의 실측 비용과 원 한도·현재 권리/서명·복원 증거를 확보한다.
   원 순수 artifact를 등록 서버 이력으로 재분류하지 않는다. 필요한 개선과 실제 실행 비용 근거 뒤에만
   prefix-cost 부모를 체크하며, 전체 terminal/DB/API/3D·복원/부하는 각각 후속 증거를 요구한다.
5. **실행/정리:** nice19·계산1/PG1·기존 로컬 PG와 잠금 의존성을 사용한다.
   계측 overhead와 RSS 표본 범위를 기록하고 FD/cache/DB schema/역할/비밀번호/PG PID/data를 정리한다.
   실제 CLI 문맥·argv/종료/source/로그 SHA와 원 입력/결과 보존을 고정 영수증으로 남긴다.

작은 기준선/32호출 관측의 첫 wall 예산은20분이다. 기존 native의 부분 호출 시간과
현재128transition artifact 한도에 근거한 관측 예산이며 HTTP30초/2MiB나 완료 날짜를 바꾸지 않는다.
전체166일 등록 실행의 global budget/완료 추정은4번의 실측과 필요한 수정 뒤 별도로 고정한다.
계측/작은 대사1–2집중시간·실제 기준선/곡선/정리1–2시간·검토/기록0.5–1시간의
**작은 측정2.5–5집중시간 잠정**이며 전체 입력 등록·개선/전체 실행·CI·자료 확보는 제외한다.

이 측정 뒤 전체 등록 저장/복원·같은 UTC3D → 생과 수확 → 물/양분·구매 에너지 →
Decimal 경제 연결로 진행한다. 실제 품종 입력·국내 독립 자료·측정 작물 Run0건과
G0–G4 `not_assessed`를 유지하며 생산 예측·추천·전체 완료 날짜의 근거로 비용 표본을 사용하지 않는다.
