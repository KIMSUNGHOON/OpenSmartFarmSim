# 작물 자동 소비자의 명시 모델 선택 v1

2026-10-12. 같은 native Codex CLI `gpt-6.1-sol / xhigh`에서 판단한다. 재귀 CLI0.
선행은 [두 모델 API 조립](../research/crop-joint-ventilation-runtime-20261012.md)이다.

`select_crop_execution_loop`는 운영자 factory에서 기존 `DeterministicWorkerLoop`를 선택한다.
`None`은 비활성이며 factory 호출/worker 시작이 없다. 명시 모델은 `crop-climate-joint` 또는
`crop-greenhouse-ventilation`이다. 선택한 factory만 호출하며 loop/worker의 정확한 타입·단일 입력 판본과
기존 binding을 검사한다. 잘못된 모델·factory·다른 모델/입력 판본·변경된 binding은 고정 사유로 거부한다.
선택 함수는 queue 조회/접수·수치 계산·작업자 시작을 하지 않는다. 실행은 기존 소비자 CLI가 담당한다.

수용은 실제 같은 SCRAM DB의 두 모델 대기 작업을 명시 선택한 독립 소비자가 각각 자동 발견/계산하고,
첫 소비 중 다른 모델의 작업/사건을 보존하는 것이다. 원 결과/publication/checkpoint·UTC·현재 권리 철회,
잘못된 모델/비호출 factory 인자의 factory 호출 전 거부와 잘못된 반환 loop의 실행 전 거부,
기존 소비자 호환·원 데이터/두 UI/WSL/원 도구 종료·소유 정리를 확인한다.
두 모델 소비자는 순서대로 시험한다. 사용자 서버 적용과 동시에 두 작업자를 상시 실행하는 구성은 후속이다.
새 합성 입력/제품 화면 및 실제 사용자 정상/보류/취소/재접속은 별도 수용한다.

[로컬 수용](../research/crop-execution-worker-selection-20261012.md): 고유42검사·실제 두 모델의 순차 독립
자동 소비/원 값·UTC·비선택 작업 보존·권리 철회 시 계산/게시0·두 UI/원 데이터/자원 보존.
권리 철회의 현재 반환은 queued 재시도이며 terminal hold 수용은 아니다.
