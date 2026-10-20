# 기관 큰 저장 결과의 hosted 용량 검사 — 2026-10-21 KST

[수용 계약](../contracts/crop-organ-catalog-capacity-v1.md) ·
[기계 증거](artifacts/organ-catalog-hosted-capacity-20261021.json) ·
[선행 WSL 보류](organ-catalog-capacity-preflight-20261021.md).

## 정상1개 사전 검사 수용

source `145624826c61e570339492d2fe5263ceef557526`의
[CI39451887348](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/39451887348)가 성공했다.
기존 hosted 소유 실행기/백엔드 잠금/Python3.12.13·PG16.15를 재사용했다.
이번 명시 용량 입력에서는 웹/Solar 작업을 실행하지 않았으며 해당 전체 CI 수용으로 주장하지 않는다.
실제 current Codex CLI `gpt-6.1-sol` / `xhigh`에서 판단했으며 재귀 CLI/하위 agent 호출은0이다.

정상 `CropResultStore.put`이 새 synthetic1시간/정수 초3601시점 결과를 생성했다.
실제 packet은 **4,474,409bytes**, 계산3600걸음/계획3600걸음,
정상 producer는3.439190초·전체 준비는3.515508초였다.
원 프로필/초기 상태·forcing/제거율/solver를 유지한 소프트웨어 부하 입력이며
기존5분6시점 원 결과를 덮어쓰거나 packet padding/재서명으로 대신하지 않았다.

실제 SCRAM·ApiRuntime/Bearer·검증 TLS에서 GET4개(200×3,422×1)를 확인했다.
목록1개728bytes/4.787275초→tail 빈 목록367bytes/1.386833초,
현재 권리 거부91bytes/1.053450초→복원 뒤 같은 원 목록728bytes/4.935101초였다.
각 전체 응답30초/metadata64KiB/no-store를 만족했다.
원 row/payload/hash/서명 fingerprint는 불변이며 DB 전후는
작물 결과1·jobs89·job_events89·thermal_g1_runs0으로 같았다.
조회 중 put/integrate/RHS/SQL 쓰기는 각각0이었다. 실제 독립 농장의 자료 이용권 승인은 아니다.

hosted guard는 **종료0/32.335402초**, 단일265,076,736/합541,847,552bytes,
128표본/.25초·FD6→6·source3파일 보존·소유 프로세스/임시/자격증명 잔여0을 확인했다.
원512MiB/PID·합1GiB/600초를 유지했다.
ZIP/GitHub digest·모든 추출 파일/실행 source hash와 실제 결과/자원/정리 항목을 독립 대사했다.
WSL artifact 다운로드도 종료0/3.477801초·합615,731,200bytes·FD4→4,
보호5root·원본2,148개·두 frozen source/자산·소유 PG/임시/자격증명 잔여0을 확인했다.

## 후속20개

위 실제 크기/시간·HTTPS/자원 사전 수용 뒤 같은 source의
[CI39452498070](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/39452498070)은 실패로 종료됐다.
정상 producer20개를 실제 생성했으며 각4,474,409bytes·합89,488,180bytes였다.
각3601시점/3600걸음이며 전체 생성 준비92.230607초,
첫 HTTPS 목록은 **30.010263초/TimeoutError**로 원30초를 통과하지 못했다.
완료 응답/원 정렬·페이지·거부/복원과 마지막 row/DB counts 불변 대사는 수행되지 않았다.
실제로 완료한20개 생성을 최종 목록 용량 수용으로 바꾸어 쓰지 않는다.

실패 실행에서도 조회 put/integrate/RHS/SQL 쓰기0과 HTTPS server 종료를 확인했다.
hosted guard는 child1/reason없음·148.433949초,
단일326,262,784/합603,910,144bytes·581표본/.25초·FD6→6,
source 보존·소유 프로세스/임시/자격증명 잔여0이었다.
실패 artifact도 ZIP/모든 파일/source hash와 원 상한·종료/정리를 대사했다.
WSL 다운로드는 종료0/2.955594초·합624,447,488bytes·FD4→4·보호5root/원본·소유 정리를 확인했다.

다음은 기존 `_registration`/`_rows`/`_item`의 시간/개수만 기록하는 한 번의 별도 계측이다.
SQL/현재 검사/producer·20개·원 요청/자원 상한을 유지한다. 이 관측으로 비용 구간을 좁힌 뒤
필요한 작은 수정과 집중 회귀→계측 OFF 정상20개를 별도 검증한다.
원 실패 source의 계측 OFF 반복은 하지 않는다.
`organ-catalog-20-large-HTTPS-capacity`는 미체크다.

WSL 동시 용량 보류·역사적 reader/CODE/다른 판본·원 디자인·사용자 적용/전체 U1,
생산/자원/경제·U2–U5·실제 CLI 종단 간/독립 자료/G0–G4는 별도다.
큰 packet의 실제 검증 크기를64MiB 전체 상한으로 확대하지 않는다.
새 목록 UI/Solar 미배포·실제 농장0·전체 완료일 미정·goal active를 유지한다.
