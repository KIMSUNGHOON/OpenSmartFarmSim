# 조건부 항목별 비용의 별도 자동 소비 v1

상태: 수용. [신규21·기존214=고유235검사/실제 SCRAM·별도 소비자·검증 TLS](../research/economic-cost-automatic-consumer-20261106.md)로 [명시 비용 runtime](economic-cost-runtime-assembly-v1.md)과 수용된 비용 worker/현재 조회를 기존 foreground loop에 연결했다.

deterministic_job_discovery의 simulation 허용 집합에 economic-cost-line-calculation-input-v1만 추가한다.
deterministic_work에는 정확한 EconomicCostWorker/CostCalculationOutcome과 그 입력 판본만 등록하고,
정확한 기존 batch worker 또는 cost worker에 기존 _access를 호출한다.
다른 worker/판본/outcome·미등록 subclass를 허용하지 않으며 기존 family의 설정·분기·이벤트·CLI를 유지한다.
unclosed 결과는 정상 attempt 이벤트가 아니며 기존 고정 LoopHold/CLI 오류로 종료한다.

발견은 선택 tenant의 simulation stage와 현재 due/만료 lease·불변 입력의 정확 판본을 사용한다.
페이지 상한·keyset 순서·읽기 전용 SQL과 기존 권한은 그대로다.
발견 직후 현재 scope 또는 source/root/provider가 바뀌면 claim·계산·게시 전에 중단한다.
취소/현재 evidence hold·만료 lease 재임대/옛 token 거부·원자 게시의 판단은 기존 비용 worker가 담당한다.
완료 작업을 다시 선택하거나 최초 입력·생성 시각·publication을 바꾸지 않는다.

HTTP의 request-bound current_principal과 별도로 소유 operator authority를 조립한다.
기존 python -m app.deterministic_work --factory를 별도 소유 Python 프로세스에서 실행하고 작업 UUID를 직접 전달하지 않는다.
시험용 factory는 실제 SCRAM authority와 원 source/서명 context/hold를 사용한다.
원 version1 started/attempt/stopped 형식을 유지한다. attempt의 작업 정보는 job_id·attempt·state·reason_code뿐이며 금액/trace ID·비밀 설정을 출력하지 않는다.
새 runtime factory/flag·queue/daemon·DB/schema/역할/정책·금액 계산이나 worker 구현은 추가하지 않는다.

수용 경로는 검증 TLS의 참조 접수/동일 재시도→별도 foreground 프로세스의 자동 발견→trace/원 v10 각1회·게시1회→완료 후 전체 scan의 재선택0이다.
페이지 크기2와 다른 family/미래 판본/다른 tenant·live/future-due 작업의 보존을 확인한다.
원 입력·최초 생성 시각·첫 publication과 재시도 뒤 원 bytes/게시 불변을 대사한다.
새 ApiRuntime/두 번째 검증 TLS 리스너의 read-only/no-execute 조회는 원 bytes·최초 publication header·no-store를 반환한다.
그 조회의 금액/worker/runtime digest 호출·SQL 쓰기는0이며 현재 signed scope/근거 hold와 복원·미인증 거부를 확인한다.
새 API 조립은 같은 시험 OS 프로세스이며 cold API 프로세스/PG 재기동 증거로 보고하지 않는다.

소유 소비자의 SIGTERM·stopped/exit0·리스너 thread 종료와 private 설정/fixture TLS 제거·소유 PG 정지/FD/source 보존을 실제 증거로 확인한다.
설정은 소유0700 디렉터리의0600 파일에 두고 정상/실패 경로에서 제거한다.
최종 고유 검사 수는 실제 collection과 서로 겹치지 않는 terminal 묶음으로 확정한다.
기존16 batch consumer와 영향받는 generic discovery/loop·기존 family의 닫힌 등록/선택 경계를 회귀한다.
부모 runtime13/HTTP308/조회114/worker425는 보존 증거이며 새 실행 합계에 자동으로 더하지 않는다.

두 변경 경로는 mutable integration pin이다. 원 bytes는 수용된 runtime Git801396642b306d56e8a2e4dd9a2f8e5a734d49a9로 보존하고 현재 통합 지문·회귀를 별도로 결속한다.
strict source750의 기존 worker/query Git 예외 두 개만 유지하며 새 예외나 과거 manifest/receipt·숫자 판본의 수정은 없다.

원 자원 창/독립 비용·구매/청구 기간 결속·strict SDK/같은 선택 UI와 실제 사용자 배포는 후속이다.
자체 소유 합성 QA이며 실제 농장 Runs0·독립 국내 raw0·G0–G4 미평가/R2 미승인·전체 제품 목표 미완료를 유지한다.
