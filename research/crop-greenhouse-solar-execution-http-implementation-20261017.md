# 일사 실행·확정 구간 보호 HTTP 로컬 수용 — 2026-10-17

[HTTP 계약](../contracts/api-crop-greenhouse-solar-execution-http-v1.md) · [기계 증거](artifacts/crop-greenhouse-solar-execution-http-implementation-20261017.json).

## 완료 범위

commit `0f013696b182a10291d2803a0782ab79c03192d5`는 접수202·현재 진행·소유자 취소와 확정 구간 summary/samples/events의 여섯 경로를 연결한다. 기존 진행 DTO·계산/저장/current/prefix facade·runtime의 핵심10파일은 기준52c66b5와 byte 동일하다. 접수/진행/취소 기본 경로는 미조립 상태에서 인증 뒤503이며 prefix는 같은 execution query를 명시한 조립에만 설치한다. 운영 설정이나 사용자 서버를 자동으로 활성화하지 않았다.

현재 source/농장 권리·코드·같은 jobs/admission/checkpoint/custody/result/current/prefix/resolver/principal 결속과 전후 계정/tenant를 검사한다. 취소는 조회·표시권 철회 뒤에도 소유자의 cancel scope로 가능하며 실제 임대 작업자의 ack와 구분한다. 요청64KiB·진행16KiB·prefix2MiB/64sample/8event, 닫힌 JSON/UUID/selector/query·body 거부·고정 오류/no-store·전송/취소 뒤 identity/thread 정리를 적용한다. route code drift는 dispatch 전에 거부하고, 원 facade의 직렬화 후 현재 권리/입력/선택 페이지 검사를 유지한다.

원108상태/41연속·6사건 장부/15수지·PAR/NIR/관리 전후 진단·단위/UTC/선택자/최초 기록 시각을 그대로 전달한다. none/closed에는 프레임이 없고 정상/수치 hold는 기존 저장 결과로 연결된다. 읽기의 계산·복원·확정·SQL 변경은0이다. 취소 응답도 literal False 승인과 G0–G4 not_assessed를 유지한다.

## 검증 증거

**고유355검사 = pytest353(전용274: 순수262+실제 DB/TLS12, 기존·공통79) + 독립 계약2**다. 초기 실패/중복 배치는 이 수에 포함하지 않았다.

| 배치 | 원 tool session | 수용 |
| --- | --- | --- |
| 실제 OpenAPI 재생성·I/O 차단 import·기존 계약 보존 | 72207 | 독립1 |
| 접수/retry/진행/취소·원 세 view·직렬화 뒤 rights/page/witness | 46585 | 실제6 |
| 직렬화 뒤 독립 heartbeat | 69025 | 실제1 |
| 독립 cancel·새 private HEAD/DB 확정 뒤 원 페이지 | 79717 | 실제3 |
| 정상 종료·기존 저장 GET·closed prefix, 원 import 순서 | 95116 | 실제1 |
| 수치 hold 종료·기존 저장 GET·closed prefix | 57929 | 실제1 |
| 순수 계약256·기존 OpenAPI78/환기 조립1 | 4086 | 335 |
| 여섯 경로 route code drift·dispatch0 | 30559 | 6 |
| 자격 없이 별도 Python의 실제 `app.api_openapi --check` | 36295 | 독립1 |

실제 SCRAM PostgreSQL16.15와 명시적으로 신뢰한 합성 인증서의 TLS를 사용했다. 접수의 같은 job·원 progress bytes/UTC/최초 시각·정상/hold 저장 응답 bytes, 취소 요청/ack·권리 철회 뒤 cancel-only와 조회/재접수 차단을 대사했다. prefix 세 view를 원 저장 값과 비교하고, 최종 직렬화 뒤 실제 페이지 변경·권리 철회·witness 누락 시 값이 전송되지 않음을 확인했다. 부모 조회의 수치/SQL 변경0과 DB digest 보존을 확인했다.

독립 actor의 의도된 metadata SQL과 제품 읽기 SQL0을 구분한다. actor는 실제 계산으로 미리 만든 signed HEAD/확인 packet을 공개한다. 선택된 이전 페이지/UTC/최초 시각 보존과 heartbeat 허용·취소 차단을 실제 HTTPS로 확인했지만 **독립 unpaused numerical worker와 API의 동시 실행 수용은 아니다.**

기준 OpenAPI는61 path/65 operation·389 schema였고 모두 보존됐다. 기본 문서는64 path/68 operation·395 schema이며 prefix3경로는 명시 조립에서만 문서화된다. 예전 기록의60/319를 현재 기준으로 사용하던 private probe assertion은 실제 기준으로 수정했다. schema import의 운영 module/연결0·FD 불변과 별도 실제 CLI check를 구분해 기록했다.

## 실패·자원과 남은 위험

초기 순수7실패는 추가 False 필드와 facade None→404의 계약 기대값을 수정한 뒤 통과했다. 실제 prefix 원문 대사의1실패는 시험용 서버 밖 reference read에 principal 문맥을 적용해 보완했다. 실제 HTTP의 인증/권한 검사를 우회하지 않았다.

초기 종료 합배치에서는 첫 완료조건 assertion이 실패했고 다음 fixture 준비 중 합 RSS1,076,117,504bytes로 감독기가 소유 시험을 종료했다. 이 배치는 미수용이다. 원 실패의 원인은 확정하지 않았으며, 기존 import 순서의 정상/hold 단독 검증에서 재현되지 않았다. 정상의 선행 단독 통과도 중복 제외했다. 원5root/두 서비스를 보존하고 실제 소유 PID/start/boot 종료를 확인한 뒤 알려진 시험 passfile4개만 제거했다. controller의 임시 PG 디렉터리 제거 뒤 잔여0도 별도 감사했다. **두 종료 사례의 합배치·전체 CI/동시 운영 용량은 수용하지 않았다.**

수용한9개 guard는512MiB/PID·합1GiB, 원5root/동적 자식·원본2,148항목·두 서비스 source/자산을 보존했다. 수용 관측 합 최대1,068,032,000bytes·단일 PID 최대196,952,064bytes, FD4→4·소유 process/PG/temp/passfile0이다. 명목0.25초/thread1/nice19 계측이며 guard 합1,174.971초는 설계/준비/실패/기록 시간을 제외한 실측이다. 이후 용량이나 전체 완료 시간으로 외삽하지 않는다.

## 사용자 산출물과 다음 한 단계

공개 코드·계약·355검사/기계 증거와 두 UI의 개발 기록이 이번 산출물이다. 기존 환기 사용자 실행과 두 주소는 유지하며 **새 일사 사용자 실행/3D는 미배포**다. 이번 변경은 로컬 commit이며 DOM/WebGL·전체 CI는 재실행하지 않았다.

두 UI(5173/5174)의 개발 기록을2026-10-17 09:05:37KST로 게시했다. 원 session8918 종료0에서 HTTP200/no-store·동일 bytes(SHA 25e74ff3c2a7770da6a8d1ef1fbbd1125d982c515316363a4d956e7ccdc3f234), 기존 두 HTML·환기 frozen2,173파일 보존을 확인했다. `new_model_deployed=True`는 기존 환기 적용을 뜻하며 새 일사 배포 완료를 의미하지 않는다.

다음은 **명시 Solar operator/runtime·독립 unpaused worker**다. 닫힌 기본False 설정/의존성·동일 jobs/farm/resolver/키/현재 reader 조립, 실제 SCRAM/TLS 정상·hold·취소/권리 철회와 계산 중 원 prefix/UTC·읽기 계산/SQL 변경0을 검증한다. 초기 합배치 실패는 보존하고, 모든 필수 소비자를 포함한 같은 자원 한도에서 독립 계산과 API가 실제로 함께 실행되는 증거가 있어야 완료한다. fixture 준비 프로세스를 먼저 종료하는 순차 준비와 가벼운 독립 실행을 우선 검토한다. 기존 API1738/worker1752·키/역할/원 자료는 재시작·대체하지 않는다. 이후 typed 웹/같은 UTC3D→사용자 정상/hold/취소·재접속/재시작을 각각 수용한다. 부모 작업은 미완료다.

실제 농장 Run0·G0–G4 not_assessed·rights_or_gate_approval=False다. [자료 기준선](../docs/RESEARCH_BASELINE.md)의 국내 품종/작기·독립 농장·시설/광학·시장 자료/권리/QC 확보는 병행 과제다. 실제 생산·자원 구매·경제/추천·최종 UI/운영과 전체 날짜·남은 집중 시간은 외부 자료와 후속 실측이 없어 미정이며 goal은 active다.
