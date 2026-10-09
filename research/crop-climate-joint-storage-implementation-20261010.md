# 작물·기후 불변 페이지 저장·독립 조회 — 2026-10-10

## 수용 범위와 산출물

core **5547f5e20e9f78ab332cad1aa83cb481a9435092**의
[저장 모듈](../backend/app/crop_climate_joint_storage.py), [시험](../backend/tests/test_crop_climate_joint_storage.py),
[계약](../contracts/crop-climate-joint-storage-v1.md)을 로컬 수용했다.
[검증 묶음](artifacts/crop-climate-joint-storage-reference-20261010.json)에 실제 종료·원 hash·중단·페이지 크기·자원을 기록했다.
원108상태/연속22/사건6/전역 수지·원 elapsed/UTC·context/checkpoint/prefix를 유지한 순수 저장/조회 자식이다.
writer는 확정 producer chunk와 신뢰한 source SHA를 받는다. 새 coefficient나 농업 자료를 채택하지 않았다.

기존 [artifact 파일 제어](../backend/app/crop_cycle_artifact.py)의 directory FD·bounded regular read·lock·
immutable put/fsync·atomic HEAD만 재사용한다. 이전121상태 계산 writer/authority로 위장하지 않는다.
새 context/4프로필 원 bytes·notice·UTC binding/코드/수치 환경을 불변 header에 고정하고,
완전한 페이지/commit 뒤 HEAD를 게시한다. terminal completed/hold에서만 전체 root를 게시한다.
reader는 Context/Binding 생성이나 checkpoint 복원 없이 저장 데이터/해시를 읽는다.
프로필의 기존 metadata/hash validator는 사용하며 물리 RHS를 평가하지 않는다.

## 실제 검증과 발견한 오류

| 단계 | 원 세션/완료 도구 | 결과 |
| --- | --- | --- |
| 페이지 최소 경로 | 60717 / `59f96e` | 1개 통과·종료0·1.087초 감독 |
| writer/fresh reader 최소 경로 | 41934 / `13ef5c` | 3개 통과·종료0·2.364초 감독 |
| 정상/실패/중단 확장 | 25702 / `1c09ee` | 당시75개 통과·종료0·40.212초 감독 |
| 열린 writer 혼합 반례 | 20822 / `4b157f` | 의도한2개 실패·종료1·원 실패/원 source SHA 보존 |
| 수정 후 전체 저장 검사 | 80146 / `d4dabe` | 새77개 통과·종료0·pytest46.58초/감독46.906초 |
| 기존 회귀 | 5003 / `e57c56` | 기존916개 통과·종료0·pytest79.80초/감독80.379초 |
| 별도 root | 57103 / `da146d` | 종료0·15.409초 감독·아래 독립 파일 대사 |

열린 writer의 public binding/checkpoint를 다른 정상 객체로 교체하면 원 HEAD와 다른 시간을 게시할 수 있었다.
먼저 두 반례를 실제 실패로 확인하고 매 게시 전/최종 root 직전에 **실제 HEAD/header/commit의 원 binding·checkpoint**를
대조하도록 수정했다. 실패 당시 source bytes를 관측 SHA와 정확히 대사해 private에 보존했다.
실패 결과를 숨기거나 검사 조건을 완화하지 않았다. 최종 새77/기존916=**고유993개**는 두 순차 실행의 합이다.
WSL 감독120초를 늘리지 않고 각 실행을 그 안에 유지했다.

root는 원 수용 시간 artifact의9개 binding/context/final checkpoint·sample/event/prefix SHA와 실제 저장값을 대사했다.
원27sample/10journal의 수치 상태5,076개와 전체 source canonical 값·46개 원 시각(행37+최종9)을 보존했다.
초기/t0사건/중간/마지막·여러 chunk의 정확한 값·순서와 writer 종료/재개를 확인했다.
현재26선행 core·9구성 코드·16oracle 입력을 보존했다. predecessor의 Decimal/시간 oracle 증거를 새로 생성했다고 주장하지 않는다.

별도 fresh PID1903213은9개 실제 저장 root를 입력받아 종료0·같은 모든 값/시간/최종 checkpoint hash를 냈다.
**Context/Binding 생성·start/restore/advance·RHS/step/event가 모두0회**다. 조회 setup에 물리 계산을 숨기지 않았다.
부모의 순수 저장/조회도 같은8개 호출0회를 강제했다.

원 HEAD 게시 전 PID1903215·게시 후 PID1903216을 실제 SIGKILL해 둘 다 -9로 종료시켰다.
남은 commit_count0/1과 실제 HEAD SHA를 확인해 같은 prefix에서 재개하고 원 최종 checkpoint와 정확히 대사했다.
각 child의 context/현재 endpoint setup RHS2회와 순수 저장0회·과거 step/event0회를 구분했다.
시험에서도 같은 두 중단 경계를 통과했다. 미게시 blob은 기존 파일을 삭제/덮어쓰는 방식으로 복구하지 않았다.

실제 초기/마지막 적엽 실패·온도 영역 실패는 terminal hold와 원 확정 prefix만 저장했다.
실패 사건/선택 출력은 만들지 않았다. HEAD/root/header/context/commit/sample/event 변조·
current code/limits·시간/모델/체크포인트/커서 혼합·오래된 HEAD/동시 writer/미게시 root·닫힌 handle,
symlink/FIFO/missing/oversize·잘못된 조회 범위·sparse orphan을 포함한 directory budget 거부와 FD 정리를 확인했다.

## 용량·원본·자원

정상9프로그램은 합2,862,175bytes/136파일, 최대 저장 페이지30,482/조회 응답87,750bytes다.
최대 첫128경계 source4,996,759bytes를 sample64/event8 이하 페이지로 나눴다.
마지막129번째 sample까지 완료한 전체는 sample3/event16=**19페이지**,5,347,572bytes/26파일이다.
가장 큰 저장 페이지657,049bytes·조회 응답657,237bytes로 각2MiB 이하를 실제 확인했다.
18pages-per-commit 상한은 첫 commit에 적용하며 마지막1page는 별도 commit이다.
HTTP 서비스·30초 전송 수용은 아직 아니다.

감독은 source1,724·원본2,148항목, 기존 미리보기 source/assets·실제3개 PID를 보존했다.
모든 단계의 FD4→4·소유 non-zombie 잔류0·frontend200을 확인했다.
이번 최대 단일 RSS147,255,296bytes·소유+보호 합406,417,408bytes로512MiB/1GiB 안이다.
원 전체166일 RHS/writer/API/WebGL은 다시 실행하지 않았다.
현재 `localhost:5173`은 기존 완료 합성 생장/수확을 읽으며 새 공동 모델/API/3D·실시간 U3는 미연결이다.

판단/검토는 native Codex CLI **gpt-6.1-sol / xhigh**,2026-10-09T17:49:09.257Z에서 수행했다.
완전 원 turn_context JSONL 줄(LF 포함)의 SHA는
`8e818e29ea0f910bc59e36cab51ed060e893ba8c967cd3b995426b2aab73fef2`이며 recursive CLI0회다.
exact703e49c Backend37962183498은0/1/2 success·3/4 in_progress·5 queued로 관측했다.
기존 run을 취소/재시작/새 push로 대체하지 않았다. 이번 core의 hosted 수용은 별도다.

## 다음 의존성·수용 기준·시간

[기존 입력 증거](../backend/app/crop_cycle_input_evidence.py)는 이전 input packet/clock/context를 전제로 하고,
[농장 결속](../backend/app/crop_cycle_calculation_farm_binding.py)은 그 정확한 authority와 CalculationContext를 요구한다.
새108상태 공동 context를 그 타입으로 취급할 수 없다. 현재 파일 hash는 외부 진본/현재 권리 승인이 아니므로
다음은 **새 입력 검증 증거→현재 농장/자료 권리 결속→서버 custody/등록→API→같은 UTC3D→사용자 실행/U3**다.
이는 새 운영 기반 확장이 아니라 해당 계산을 기존 권한 경로로 연결하기 위한 직접 의존성이다.

다음 `crop-climate-joint-input-evidence` core3은 원 context/seed·4프로필/notice/UTC·source bytes/정규화/QC 판본과
검토/증거 ID를 새 authority에 결속한다. 기존 authority 유형을 재사용한 승인으로 표시하지 않는다.
권한 있는 evidence/현재 원 bytes를 재검사하고 변조·다른 seed/profile/time/code·철회/혼합·fresh/FD/원 종료/자원을 확인한다.
합성 input math 증거·실제 G0 채택과 현재 farm/display 권리의 게시 조건을 구분하며 G0–G4를 열지 않는다.

잠정 분해는 원 authority232줄/농장 결속140줄 재사용 검토·새 계약0.5–1시간,
검증/불변 evidence 구현0.5–1시간, fresh/변조/현재 bytes·자원0.5–1.5시간, 기록0.5시간의 **2–4집중시간**이다.
이번 저장은 최종46.906초/기존80.379초/root15.409초로 검증했다.
계속 작업·새 source/authority 장애 없음 조건의10월10일 검토 목표이며 전체 API/UI·제품 완료 날짜는 아니다.
실제 품종 입력/농장 Run/국내 독립 자료0건·온실/물·양분/구매 에너지/Decimal 경제 후속,
독립 자료/권리 확보와 G0–G4·생산/미래 마진/추천 hold를 유지한다.
