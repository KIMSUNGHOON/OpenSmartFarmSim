# 전체 합성 작기의 별도 달력 판본과 농장 등록 — v1

2026-10-08 KST. native Codex CLI `gpt-6.1-sol / xhigh`, 재귀 CLI0회.
`crop-cycle-calculation-full-registration`의 개발 계약이며 원 입력 검사는
[별도 증거](../research/crop-cycle-calculation-full-input-preflight-20261008.md)에 있다.

## 판본과 보존

원166일 입력은2026-01-01~06-16 UTC, root
`ab24eda4d763d7fe3faff1ae3c7c2f84fbec030af71a494bf284fef1f2cdcd98`이다.
고정 소유 원천 fixture는10월이다. 원 입력/기존 등록을 덮어쓰지 않고 **+273일의 새 합성 판본**을
새 디렉터리와 `owned-full166-calendar-20261001-v1` program ID로 만든다.
새 기간은2026-10-01T00:00:00Z~2027-03-16T00:00:00Z다.

`research/crop-cycle-calendar-translation.py`는 검증된 synthetic input packet만 읽고
기존 packet writer로 새 root를 만든다. 전체 네 stream의 시각만 같은 정수 일수만큼 옮긴다.
초기121상태/seed의 근거, 모든 forcing/배분/관리 값과 input ID, 프로필/계수·solver,
300초 출력/anchor 간격과8초 RK4 한도를 보존한다. 원/새 root·계산 hash·기간·전체 개수,
시각을 되돌린 네 stream hash와 정확한 temperature clock prefix 대사를 영수증에 기록한다.

이 변환은 현행 수식이 명시 forcing과 상대 UTC 간격을 사용하는 합성 소프트웨어 검증에만 해당한다.
검토 근거는 `crop_cycle_continuation._Evaluator.clock/rhs`,
`crop_cycle_stream_execution.prepare_context`, `crop_cycle_input_stream._slope/segment`다.
새 날짜에 맞는 실제 기후·계절·작물 생리를 생성하거나 품종 적용성을 검증하지 않는다.
원 순수166일 계산 이력을 새 등록 서버 이력으로 재분류하지 않는다.

## 실제 등록과 다음 수용 기준

1. 변환의 작은 시험은 모든 값·원 파일/FD 보존, 전체 stream 시각/간격,
   작은 실제 RHS 전후 같은 상태/수지와 시간 변환, 잘못된 요청·hash·기존 목적지 거부를 확인한다.
2. 경제 baseline의 평가 종료일을2027-03-16로 바꾼 **별도 자기 작성 시험 입력**을 저장 전에 만든다.
   정산 원문/참조 hash, 경제 입력 권리, 공급·수요·매크로 가정의 적용 기간과 shock pin도 저장 전에
   다시 결속한다. 기존 숫자/거래일은10월의 명시 가정으로 유지하며 전체166일 생산·원가로 주장하지 않는다.
3. 실제 SCRAM `JobStore`/`MarketSourceStore` 접수와 후보 검증, 고정 소유 조사 원천을 사용하는
   `FarmAuthoringService`를 거친다. 새 농장 ID/권리 판본·전체 평가 기간과 작물 점유/해제,
   경제 batch/grade/channel·수확/판매/수금을 검증한다. 짧은 열 fixture는 전체166일 온실 환경 증거가 아니다.
4. 불변 job/input/registration hash와 현재 `read_registration`, 같은 검증 context의
   `CalculationFarmBinding.prepare/current`를 실제 대사한다. 이 단계의 RHS/작물 계산/Run 게시는0이다.
   원 기간 입력·잘린 점유 기간·권리 철회·계정 범위 손실을 거부하고 원 이력을 보존한다.
5. 원/새 파일 hash·mode·inode, FD/cache·schema/role/passfile·PG PID/data 정리와 원 명령 종료를 보존한다.
   nice19, 소유 PG1개이며 실행 중 source를 고정한다. 전체 입력 등록 첫 관측은20분 예산이다.

등록 수용 뒤 같은 새 전체 입력으로 초기/증가 prefix 비용을 측정하고 필요한 개선을 검증한다.
그다음 전체 등록 계산 완료·저장/복원·API/같은 UTC3D, 생과 수확·자원·Decimal 경제 연결로 진행한다.
작은 등록/변환 시험으로 전체 작기 실행·실제 생산 예측·추천·G0–G4를 수용하지 않는다.
