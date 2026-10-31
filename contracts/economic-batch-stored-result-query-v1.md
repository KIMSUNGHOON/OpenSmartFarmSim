# 소유 생산 batch 저장 결과의 현재 조회 v1

상태: [실제 조회/별도 프로세스 수용](../research/economic-batch-stored-result-query-20261031.md).
[구현](../backend/app/economic_batch_query.py)은 [실제 worker/게시](economic-batch-execution-worker-v1.md)를 따른다.
실제 EconomicBatchAuthority·같은 JobStore/저장 root·현재 source/서명 hold/context를 결속한다.
metadata/artifact와 원 참조 읽기 scope가 필요하며 simulation_execute는 필요하지 않다.

소유 tenant/job의 지원 input_version·실제 succeeded/attempt·원 입력 bytes/SHA,
publication/manifest·2MiB 이내 원 파일 bytes/SHA를 대사한다.
canonical envelope/닫힌 결과 형식·입력 pin·모델/성분 판본·batch/입력/문맥 결속을 검증한다.
게시 당시 전체 worker 코드/잠금 환경 지문과 최초 시각은 원 이력으로 보존한다.
현재 다른 backend 코드가 바뀌었다고 원 이력을 새 지문으로 덮어쓰지 않는다.
현재 지원하는 고정 v10 모델과 현재 입력/근거의 호환성은 확인한다.

현재 원 입력/근거 SHA를 계산 전 검증 경로로 다시 검사한다. 금액/수량을 재계산하지 않는다.
현재/늦은 scope·객체/root·원 메타데이터/입력/근거·물리 파일 변경 때 반환을 차단한다.
원 bytes와 최초 publication ID/시각 및 독립 typed 결과를 반환하며 cache로 권한을 대체하지 않는다.
알 수 없는/다른 종류·미완료 작업은 결과 없음이고, 변조/손실/결속 불일치는 고정 hold다.
다른 tenant/읽기 scope 부재는 거부한다. 일부/미확인 금액과 hold는 원 null/문자열을 유지한다.

조회는 READ ONLY metadata 거래·원 파일 읽기와 현재 근거 검증만 수행한다.
금액/작물 계산·작업/자료/결과 생성·SQL 쓰기·CLI 실행·관문 승격을 하지 않는다.
수용은 실제 SCRAM/fresh reader·원 bytes/최초 이력, 계산 진입 차단/SQL 쓰기0,
부분 결과·재조회 복사 독립성과 현재/late 권한/metadata/파일/참조 반례·원 자료/GUI/만료 보존이다.
보호 HTTP/runtime/자동 소비·SDK/화면과 실제 농장/추천/G0–G4/R2는 후속이다.
