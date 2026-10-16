# 일사 확정 구간 공개 응답 로컬 수용 — 2026-10-17

[공개 계약](../contracts/api-crop-greenhouse-solar-prefix-v1.md) · [기계 증거](artifacts/crop-greenhouse-solar-prefix-projection-implementation-20261017.json).

## 구현과 검증

닫힌 joint-solar-prefix-replay-v1 응답과 현재 read_prefix facade를 구현했다. none/closed에는 프레임이 없으며 accepted는 원 selector·최초 기록 UTC/attempt·farm/input/manifest/time grid와 summary 또는 page를 제공한다. 원108상태/41연속·6사건 장부/15수지·PAR/NIR·관리 전후 진단/원량/단위/UTC를 기존 Solar 타입으로 보존한다. top/reference/checkpoint의 literal False 승인·checkpoint/input provenance 동일성·per_m2_floor/unvalidated_for_registered_crop·정규화/QC/증거 판본을 고정한다. 순수 투영은 현재 권리 승인이나 DB 수용의 증거가 아니다.

현재 facade는 정확한 reader의 원 조회→투영→UTF-8 직렬화→owner-bound witness/현재 권리·입력·DB 사건/signed ancestry·원 snapshot/page 후검사를 거쳐 bytes를 반환한다. [후검사 페이지 재검사 보완](crop-greenhouse-solar-prefix-post-serialization-fix-20261017.md)에서 실제 변조 RED를 재현하고 수정했다. 토큰/권리·review/provenance 원문·params/forcing/event 명령·서명/개인 경로는 출력하지 않는다. 샘플64/사건8·전체2MiB·유한 binary64/50기관 배열·정확한 범위/끝/next_offset·코드/정책/UTC 격자를 검사한다. 계산/복원/확정/SQL 변경은0이다.

**전용 고유91검사 = 순수75 + 실제 DB15 + 독립 fresh1**이다. 단독 초기 정상 투영1은 최종75와 중복이므로 제외했다. RED/초기 실패 배치와 그 통과 부분도 수용 수에서 제외했다.

| 배치 | 원 tool session | 통과 |
| --- | --- | --- |
| 직렬화 뒤 실제 선택 페이지 변조 RED→GREEN | 35940 | 1 |
| 닫힌 원량/단위/UTC·float/범위/승인/코드·2MiB/비공개 | 6367 | 75 |
| 실제 none/현재 세 view·읽기 scopes·취소 | 70067 | 1 |
| 최종 직렬화 뒤 rights/review/farm/page/witness 변경 | 31009 | 5 |
| 직렬화 뒤 독립 heartbeat/취소 | 67986 | 2 |
| 새 sample/event·private HEAD/DB 확인 뒤 원 공개 페이지 유지 | 17331 | 2 |
| 실제 ready0·dense64+1 원량/UTC 공개 | 71394 | 2 |
| 정상/수치 hold closed·기존 결과 연결 | 22059 | 2 |
| 실제 추가 저장 뒤 별도 readonly 원 공개 응답 | 57282 | 1 |

독립 metadata actor의 의도된 SQL과 제품 조회 SQL0을 구분했다. actor는 실제 계산으로 미리 만든 원 signed HEAD/검증된 checkpoint packet을 공개한다. 동시에 새 numerical worker가 계산했다고 주장하지 않는다. 별도 실제 producer가 sample/event1/1→2/2를 계산·저장한 뒤 종료하고, 독립 reader가 같은 DB/키/파일의 이전 선택자 세 공개 응답을 원 값/UTC/최초 시각·해시(관측 시각 제외)와 대사했다. 권리 철회/후검사·읽기 scopes·DB/수치 변경0을 확인했다. unpaused worker/HTTP·브라우저 동시성은 후속이다.

처음 재현한 페이지 후검사 누락은 선택 원문 재로드·대사로 수정했다. 초기 정책 참조 오류는 실제 startup.POLICY_SHA256으로 고쳤다. NaN/Inf 시험 helper가 투영 전에 엄격 인코딩에서 실패하던3건은 malformed JSON을 투영에 전달하도록 수정했고 최종75검사에서 모두 거부됐다. 오류/RED를 통과로 계산하지 않았다.

## 자원·보존과 사용자 산출물

필수5root/동적 자식·원본2,148항목·두 서비스 source/HTML/자산·키/역할, 기존 과학/입력/custody/store/worker/현재 진행/HTTP/runtime/OpenAPI 코드를 보존했다. 원 reader 후검사만 명시적으로 보완했다. 감독 FD4→4·소유 프로세스/PG/임시 PG/passfile/schema·roles0,512MiB/PID·합1GiB·명목0.25초/thread1/nice19를 유지했다. 성공 관측 합 최대1051541504bytes·단일 PID 최대172838912bytes,9개 guard 합1423.896초다(준비/설계/기록 별도). 기본 합성32초와64걸음/128초 페이지 경계 시험이며 전체 작기·브라우저 동시 용량/실제 농장 검증은 아니다.

공개 코드·계약·91검사/기계 증거를 확인할 수 있다. 두 UI(5173/5174)의 개발 기록을2026-10-17 08:01:10KST로 갱신했다. 원 session35401 종료0에서 HTTP200/no-store·기록 원 bytes(SHA 9297f77dcbcd16d132759513edd2914fdb5663f76d024156d33e5c02f03f0977), 기존 두 HTML·환기 frozen2,173파일 보존을 확인했다. 새 HTTP 경로는 아직 설치하지 않았으며 새 일사 사용자 실행/3D는 미배포다. 기존 환기 사용자 실행은 유지한다. DOM/WebGL·전체 CI는 재실행하지 않았고 변경은 로컬 commit이다.

## 다음 단계와 남은 의존성

다음 한 단계는 **일사 접수/진행/취소·확정 구간 보호 HTTP**다. 닫힌 요청/selector/UUID/query·현재 계정/farm/자료 권리·같은 jobs/admission/checkpoint/custody/result/current/public facade 조립·취소 경합·오류/no-store·최종 전후 인증·실제 SCRAM/검증 TLS·원 bytes/UTC·직렬화 뒤 변경·조회 계산/SQL 변경0·기존 경로/스키마/5root/원본/자원을 수용해야 한다. 이어 명시 operator/runtime/독립 unpaused worker→typed 웹/같은 UTC3D→사용자 정상/hold/취소·재접속/재시작을 각각 검증한다. 부모는 미완료다.

실제 농장 Run0·G0–G4 not_assessed·rights_or_gate_approval=False다. 국내 한 품종/작기·독립 농장/시설/광학·시장 자료와 권리/QC 확보는 병행 과제로 남아 있다. 실제 생산·자원 구매·경제/추천·최종 UI/운영·전체 완료 날짜는 외부 자료와 후속 실측이 없어 미정이다. 전체 goal은 active다.
