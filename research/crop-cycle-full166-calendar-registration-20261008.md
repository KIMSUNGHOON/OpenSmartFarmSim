# 전체 합성166일 달력 판본과 실제 농장 등록 수용

2026-10-08 KST. [등록 계약](../contracts/crop-cycle-calendar-registration-v1.md)의 범위를 실제 검증했다.
[불변 관측 영수증](artifacts/crop-cycle-full166-calendar-registration-reference-20261008.json)에
원/새 root·기간·전체 stream 대사·실제 명령 종료와 source/로그 SHA·자원 정리를 기록했다.
native Codex CLI `gpt-6.1-sol / xhigh` 문맥을 확인했고 재귀 CLI0회다.

## 원본과 다른 새 합성 판본

원 root `ab24eda4d763d7fe3faff1ae3c7c2f84fbec030af71a494bf284fef1f2cdcd98`의
2026-01-01~06-16 UTC 입력을 보존했다. 별도 program ID
`owned-full166-calendar-20261001-v1`과 새 root
`05a58cc9092682f663bb3e2f827003f51ec8a778f746bb429126a663e841fc04`로
시각만 **+273일**,2026-10-01T00:00:00Z~2027-03-16T00:00:00Z로 옮겼다.

네 stream의 모든 시각을 되돌려 원 record chain과 대사했다.
47,808 forcing구간·47,809 output/anchor·5관리 사건과 input ID, 초기값/프로필/계수·solver,
정확한 temperature clock prefix와1,816,704걸음 계획을 보존했다.
원본750파일의 SHA/mode/device/inode를 확인했다. 새 입력도750파일이다.
새 판본은 원 순수166일 실행의 등록 서버 이력이나 새 계절의 실제 기후 자료가 아니다.

변환 자체121.657초, 새 입력 증명30.214초, 검증 context 열기0.363초다.
준비 원 명령은 **종료0/153.498초**, FD4→4·RHS0·cache/임시 자원 정리를 확인했다.
표본 primary RSS 최대101,310,464bytes이며 WSL 전체 메모리나 작기 계산 부하는 아니다.

## 실제 농장·경제 달력 결속

경제 baseline과 숫자 권리·공급/수요/매크로 적용 기간, 정산 원문/참조 hash와 shock pin을
**저장 전에** 새 자기 작성 시험 입력으로 결속했다. 실제 `JobStore`/`MarketSourceStore` 접수와
후보 검증, 고정 소유 조사 원천과 `FarmAuthoringService`를 사용했다.
제품 validator나 기간/권리 검사를 우회하지 않았다.

`owned-full166-farm/r1`의 짧은 점유 기간을 먼저 등록·보존했다.
새 `r2`는 전체 입력을 포함하는 점유/해제와2026-10-01~2027-03-16 평가 기간,
경제 batch/grade/channel·수확/판매/수금 참조를 결속했다.
등록 상태는 `registered_unpublished_inputs`이고 작업은 queued/attempt0이다.
같은 요청 재시도와 새 서비스 `read_registration`, 현재 `CalculationFarmBinding.prepare/current`가
같은 불변 등록 job/hash를 반환했다. prepare2.587초·current2.621초는 이 등록 검사의 실측이다.

짧은 `r1` 점유·원1~6월 입력은 거부했다. 현재 입력 권리 철회와 계정 읽기 범위 손실도 거부했고,
복원 뒤 같은 binding을 확인했다. 기존 `r1`과 원/새750파일의 SHA/mode/device/inode를 보존했다.
FD12→12·context/cache 정리, 등록 검사 중 DB 쓰기0·RHS/실제 계산 걸음/작물 Run0을 확인했다.

첫 실제 명령은 시험 코드에서 tuple 권한 목록을 합치는 오류로 **1실패/종료1**이었다.
그 실행의 source/정리를 보존한 뒤 명시적 set 병합 한 줄만 수정했다.
같은 준비 입력을 재사용한 수정 실행은 **1통과·1미선택/35.16초**, 원 명령 **종료0/35.918초**다.
원127 source pin과 실제 SCRAM, schema/role/passfile0·PG PID 종료/data 제거·소유 임시/프로세스 정리를 확인했다.
표본 primary RSS 최대129,028,096bytes다. 작은 변환/원 input stream 회귀 **73개/4.48초**도 통과했다.
전체 backend/브라우저 회귀나 새 whole-cycle 계산을 실행한 결과는 아니다.

## 다음 단계와 남은 범위

`crop-cycle-calculation-full-registration`의 **별도 합성 달력 등록** 범위만 수용한다.
다음은 같은 새 전체 입력의 실제 등록 서버에서 초기/증가 prefix 비용과 checkpoint 복원을 측정하는 단계다.
필요한 개선 뒤 전체 등록 계산 완료·DB 저장/복원·API/같은 UTC3D로 진행한다.

경제 거래량/거래일과 비용은10월의 명시 가정이며 전체166일의 모델 수확량이나 원가가 아니다.
짧은 열 fixture도 전체166일 온실 환경을 입증하지 않는다. 등록 프로필 적용성은
`unvalidated_for_registered_crop`이고 생과 수확·물/양분·구매 에너지·Decimal 경제 연결은 남았다.
새 native 화면의 원 종료 기록 누락 보류도 유지한다.
실제 품종 입력·국내 독립 자료·측정 작물 Run0건과 G0–G4 `not_assessed`를 유지한다.
전체 실행 비용·자료 확보 전 전체 완료 날짜를 추정하지 않는다.
