# 일사 결과 등록·현재 조회 로컬 수용 — 2026-10-17

[기계 증거](artifacts/crop-greenhouse-solar-result-store-implementation-20261017.json) · [계약](../contracts/crop-greenhouse-solar-result-store-v1.md).

## 구현과 수용

정확한 SolarServerCustody·등록 농장·현재 source/review/rights와 두 원문(metadata/progress)의 SHA/HMAC/선택 root를 결속했다. 각각128KiB 한도이며 원 UTC·108상태/41연속·6사건 장부/15수지·checkpoint/hold를 재계산 없이 읽는다. 새 계산식·계수·요금은 도입하지 않았다.

같은 transaction advisory lock 안에서 기존 행을 먼저 대사하므로 동일 재시도는 INSERT를 다시 시도하지 않고 원 result ID/bytes/최초 recorded_at을 유지한다. 새 행은 기존 INSERT/고유키 검사 뒤 현재 권리를 다시 검사한다. 내부 savepoint hook은 호출자 기록 이후 권리·scope·resolver 변경과 호출자 오류를 결과/작업 기록과 함께 rollback한다. 커밋 뒤 철회는 저장된 private 감사 행을 유지하고 응답·후속 조회를 차단한다. 모든 시점의 권리를 하나의 전역 snapshot으로 주장하지 않는다.

실제 소유 SCRAM에서 **새18/기존17=고유35검사**를 통과했다. 정상/fresh·권한/철회/변조4·보류/충돌/원자 저장4·rollback5·호출자 권리/연결4, 기존 schema/roles16·custody current rights1을 분할 실행했다. 아래 원 tool session은 모두 실제 종료0이다.

| 배치 | session | 통과 |
| --- | --- | --- |
| 정상·별도 프로세스 | 26174 | 1 |
| 권한·철회·변조 | 3038 | 4 |
| 보류·충돌·원자 저장 | 35506 | 4 |
| 철회·호출자 rollback | 31278 | 5 |
| 늦은 권리·연결 identity | 78008 | 4 |
| 기존 schema/roles | 25127 | 16 |
| 기존 custody current rights | 33415 | 1 |

정상 metadata73,066bytes와 별도 progress 원문, 원 페이지/UTC/시각을 확인했다. fresh의13수치/복원/CLI 감시 및 SQL 변경 카운터는 모두0이다. 등록 재시도까지 포함한다. 기존4표의 SQL 형식 fixture 행을 각각1개 보존했고 구 producer 타입/ID/HMAC domain 혼합을 거부했다. 과거 signed 데이터 이관/재서명 검증은 하지 않았다. 기존 사용자 frozen 판본·키·서명 이력은 보존했다.

## WSL 자원과 실패 기록

512MiB/PID·합1GiB·명목0.25초·단일 numeric thread/nice19를 유지했다. 수용 배치의 합 최대1,069,801,472bytes, 단일 PID 최대137,015,296bytes이며 필수5root/동적 자식·원본2,148항목·기존 소스/자산·FD4→4·소유 프로세스/PG/임시 PG/자격 파일/시험 schema·role 정리를 확인했다. 이 관측값은 production 용량 증거가 아니다.

앞선 정상 시도11건은 실패 증거로 보존했고 통과 수에 넣지 않았다. 메모리 초과와 시험용 `/proc` 종료 확인의 ProcessLookupError를 구분했다. 종료한 프로세스의 사라짐 오류를 처리하고 소유 시험 PG의 명시1MiB 버퍼 선택을 추가했다. 기본/기존 버퍼 선택과 사용자 DB는 바꾸지 않았다. 동일 INSERT 재시도의 불필요한 제약 재평가를 제거했다. 최종 정상 검사는 가벼운 감독 아래 모델 프로세스 A가 검증/원문 fsync 후 종료하고, 같은 DB/역할/키/파일에서 독립 프로세스 B가 조회/재시도/철회를 검증한다. 부모가 실제 schema/role 정리와 PG 종료를 확인한다. 원 검사 조건을 모두 유지했고, 준비 단계만으로 수용하지 않았다. private 계측 동기화는 관측 RSS나 필수 root를 제외하지 않는다.

## 사용자 진행 기록

원 session74668 실제0: 두 주소의 개발 기록이 HTTP200/no-store·원 bytes와 일치하고 기존 두 HTML·환기 frozen2,173파일을 보존했다. 게시 시각은2026-10-17 02:00:25KST이며 기록 SHA는451c693d307687807f785814c6deab929f6245df3cc9abd1c2d2c74563d11ce2다. 이 probe는 DOM/WebGL 재검증이 아니다. 기존 환기의 사용자 적용 표시를 유지하고 새 일사 미배포·공개 API 후속을 명시했다.

## 범위와 후속

합성32초 소프트웨어 결과이며 rights_or_gate_approval=False·G0–G4 not_assessed·실제 농장 Run0이다. 새 일사 모델의 API/worker/사용자3D 배포, 실제 한 품종/한 작기 생산·구매 자원·경제·추천 정확도는 미수용이다. 이번에 사용자 서비스·키·배포 역할은 변경하지 않았다. 전체 CI와 현재 브라우저 DOM/WebGL은 재실행하지 않았다.

다음 한 단계는 **공개 응답 투영·현재 조회**다. 정확한 새 current store의 같은 선택자를 사용해 정상/hold summary와 samples/events를 원 값·단위·UTC로 공개하며 현재 권리를 반환 전후 검사한다. 독립 프로세스/늦은 철회·구 판본/변조·재계산/SQL 변경0·원 사용자 결과/5root/자원 보존을 통과해야 한다. 이어 보호 HTTP/명시 runtime→자동 worker/확정 prefix→같은 UTC3D→사용자 정상/보류/취소·재접속/재시작으로 진행한다.

실제 시설/광학·국내 한 품종/독립 농장·미래 작기·시장 자료의 권리/QC/가용성 확보는 병행 의존성이다. 단계별 소프트웨어 수용과 예측·추천 게시 관문을 분리한다. 전체 goal은 active이며 완료일·남은 집중 시간은 미정이다.
