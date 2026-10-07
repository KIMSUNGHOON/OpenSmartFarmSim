# 전체 등록 작기의 원 격자·참조 용량 — v1 관측 계약

2026-10-08 KST. 작업 `crop-cycle-calculation-full-capacity`.
선행은 [등록 두 묶음 수용](../research/crop-cycle-calculation-registered-chunk-cost-observed-20261008.md)이다.
현재 native Codex CLI `gpt-6.1-sol / xhigh`에서 판단하며 재귀 CLI는0회다.

## 범위

고정된 소유 합성166일 입력의 모든 원 경계를 RHS0으로 읽는다.
원 경계 i의 처리 완료 전이는 `steps + i + 1`이다. 요청4,096전이/10,000걸음,
실효128경계 정책으로 끝까지 나누고 출력/사건/걸음·처음 두 실제 checkpoint의 cursor를 대사한다.
이 정수 계획은 상태 벡터·생장 checkpoint·새 계산 결과가 아니며 writer에 전달하지 않는다.
조밀한 경계·경계 직전/직후·긴 간격·출력 없는 forcing·잘못된 계획의 작은 반례를 먼저 확인한다.

불변 원 artifact의 모든 commit/page를 bounded canonical/SHA reader로 한 번씩 읽고
원 전체 행 hash·순서·개수와 명시 +273일 달력의 행 크기를 대사한다.
참조 행을 새 묶음별로 재포장했을 때의 page bytes/count와 최대 단일 행을 계산하되 새 artifact는 쓰지 않는다.
원 합성 행 크기를 신규 실행의 실제 저장량이나 실제 품종 예측으로 채택하지 않는다.

## 수용 기준

1. 원/새 각750입력·원29,141 artifact·선행276 source와 실제 native model/effort를 보존한다.
2. RHS와 advance를 실제로 금지하고 전체 경계/걸음/출력/사건을 한 번씩 계획한다.
   첫 두 계획 cursor/count가 실제4,096/8,192전이 증거와 같아야 한다.
3. 원 모든 row hash·commit 순서/부모·전체 출력/사건 개수와 최대 page/record를 대사한다.
   참조 재포장의 page2MiB/128행·delta8MiB/16page 경계를 확인한다.
4. 참조 page bytes와 commit당 metadata128KiB·header128KiB·root2MiB·HEAD8KiB 상계를 사용해
   artifact512MiB/65,536file/16,384commit를 대조한다. 최대 advance/finalize/publish 예약을 더한다.
   proof당8KiB·전체 proof128MiB/32,770file, intent640MiB·root1GiB와 해당 file 한도도 대조한다.
   이는 같은 참조 행·깨끗한 단일 intent의 조건부 용량이며 실제 writer 제한/hold를 대체하지 않는다.
5. 원 명령 예산240초·nice19·주 프로세스 RSS384MiB 한도를 적용하고 actual exit/log SHA·PID 시작 identity·
   FD/cache/임시 경로 정리·원 파일 전후 bytes/hash/mode/identity·소스 감사를 기록한다.
   DB·브라우저·컨테이너·새 생장 계산은 기동하지 않는다. 관측 만료로 재시작하지 않는다.

## 다음 장시간 실행 계약

용량 근거와 선행 전체 순수 계산20,518.836초, 현재 이력 bytes/HMAC 증가 구조를 함께 검토한다.
새 등록 전체166일 실행의 고정 예산·지속 감독자·원 명령 종료 기록·source freeze·현재 권리·중단/재개·정리와
terminal 전체 QC/원량 대사 기준을 별도 계약으로 정한 뒤 실행한다. 두 초기 구간의 선형 외삽은 완료 날짜가 아니다.
이번 관측만으로 장시간 실행·worker lease/HTTP30초 변경이나 DB/API/3D 부모를 수용하지 않는다.
용량 자식의 실제 증거와 후속 감독/예산 계약이 모두 있어야 이 작업을 체크한다.

생과/물·양분/구매 에너지·작물 Decimal 손익과 실제 제품 CLI·독립 G1은 후속이다.
실제 품종 입력·국내 독립 자료·측정 농장 작물 Run0건, G0–G4 `not_assessed`, 예측·추천 hold를 유지한다.
