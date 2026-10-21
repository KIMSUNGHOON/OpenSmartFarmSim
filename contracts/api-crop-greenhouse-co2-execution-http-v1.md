# CO₂ 접수·진행·취소·확정 구간 보호 HTTP — v1 계획

Status: planned; no execution/prefix HTTP code or acceptance.
선행은 [공개 응답110개 전체 수용](api-crop-greenhouse-co2-prefix-v1.md),
현재 CO₂ admission/checkpoint/worker/query와 [기존 결과 HTTP](api-crop-greenhouse-co2-route-v1.md) 기능이다.
[기존 Solar HTTP 경계](api-crop-greenhouse-solar-execution-http-v1.md)를 같은 modular FastAPI 앱에 결속한다.

## 경로와 자료형

| 경로 | 동작·고정 한도 |
| --- | --- |
| POST `/v1/crop-greenhouse-co2-executions` | 닫힌64KiB request → 현재 접수 서비스, 동일 intent 재요청은 같은 job/202 |
| GET `/v1/jobs/{job_id}/crop-greenhouse-co2-execution` | 기존 `Co2ExecutionRead`의 원16KiB 진행 응답 |
| POST 같은 경로의 `/cancel` | 현재 소유자의 cancel scope로 요청; worker ack와 구분 |
| GET 같은 경로의 `/prefix` | 현재 공개 prefix summary |
| GET 같은 경로의 `/prefix/samples`, `/prefix/events` | 명시 원 selector, start/limit·64/8개·2MiB 공개 페이지 |

request는 study/revision·farm/input 식별자·해시/증거·명시 권리 선언만 받는다.
입력 source/rights 판본은 기존 CO₂ wire 상수, 진행/결과 farm은 기존
`Co2ExecutionRead`/`Co2ExecutionResultFarm` 타입을 사용한다. 취소 응답 판본은
`joint-co2-solar-execution-cancel-v1`이며 현재 job/요청/수락/관측 UTC를 제공한다.
접수202는 계산 완료/관문 승인과 별개다. 과학 입력 권리 철회 뒤에도 소유자 취소는 가능해야 한다.

## 현재 서버·접근 경계

같은 jobs/farms/admission/checkpoint/custody/result/query/prefix/principal/resolver의 정확한 조립을 검사한다.
기본 실행3경로는 설정 누락 시 인증 뒤503이다. prefix는 같은 실행 graph를 명시한 경우만 설치한다.
기존 결과 읽기 graph를 실행 권한으로 확대하지 않는다. 실제 조립/worker 시작은 후속 runtime 단계다.

엄격한 UUID/소문자 hash·canonical 정수/중복·추가 query·GET/cancel body를 검사한다.
접수/진행/취소와 공개 prefix는 각각 기존 AND scope를 적용하고 tenant/권한을 응답 전 다시 확인한다.
인증/계정·의도/선택 충돌·요청 한도/형식·현재 증거 보류·일시 불가의 기존 HTTP 오류 구분을 유지한다.
no-store와 고정 오류를 사용하고 입력 원문/계수/권리·검토/서명·개인 경로/자격증명은 출력하지 않는다.
조회는 기존 facade의 직렬화 후 원 source/page·선택자/UTC/현재 권리 검사를 그대로 거친다.

## 구현·수용 단위

1. 현재 OpenAPI의 기존 path/operation/schema 지문을 캡처한다. 실행 parser/DTO·명시 조립·기본503과
   접수/진행/취소3경로를 구현하고 기존 경로/필드 보존 및 새 문서를 검증한다.
2. 명시 prefix3경로를 연결해 원 선택/단위/UTC·2MiB·현재/늦은 권리·계정/소유자·source/page 변경과
   callback/전송/해제 경계를 검사한다. 원량 계산/복원/CLI/확정·조회 SQL쓰기0을 확인한다.
3. 실제 SCRAM/검증 TLS에서 접수/동일 retry·미기동/계산 중/정상/수치 hold·취소 요청/ack와
   철회 뒤 cancel-only, prefix3 view/선택자·최초 UTC/byte를 대사한다. 독립 actor의 시험 SQL은 구분한다.
4. 현재/동결 source·자료·키/역할·기존5root와 기존 자원/소유 정리를 보존한다.

이후 명시 실행 runtime/독립 worker → typed web/같은 UTC3D → 사용자 적용/재접속·재시작을 수용한다.
생산·경제·예측/추천의 주장 범위는 [제품 명세](../docs/PROJECT_SPEC.md)를 따른다.
