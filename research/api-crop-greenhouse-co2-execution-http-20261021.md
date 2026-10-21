# CO₂ 보호 실행 HTTP — 접수·진행·취소 제어 수용

[계약](../contracts/api-crop-greenhouse-co2-execution-http-v1.md) ·
[375검사/원 증거](artifacts/api-crop-greenhouse-co2-execution-http-base-20261021.json) ·
[선행 공개 응답110](api-crop-greenhouse-co2-prefix-20261021.md).

## 수용 범위

접수202·원16KiB 진행·소유자 취소3경로를 기존 modular FastAPI 앱에 연결했다.
원 CO₂ admission/query/ResultFarm/Read와 같은 jobs/farms/resolver/server를 요구하며
설정이 없으면 인증 뒤503이다. 닫힌64KiB 입력/엄격 UUID·hash/중복·잘못된 JSON·권리 선언,
AND scope/tenant·응답 뒤 계정과 정확한 graph, 고정 오류/no-store/전송·취소 뒤 thread identity 해제를 확인했다.
취소는 기존 immutable job/input version에 결속하며 과학 입력 권리 해제와 별개인 소유자 권한을 사용한다.
이 경로는 원 service의 intent 멱등성을 쓰며 새 큐/계산/모델을 추가하지 않는다.

missing-module RED(수집1오류) 뒤 새 제어114개와 기존 Solar 실행/CO₂ 결과·공통 OpenAPI의
집중375개를 통과했다. 기존65경로/477스키마의 지문을 고정하고 전부 그대로 보존했다.
새 기본 문서는68경로/483스키마이며 explicit prefix는 아직 설치하지 않는다.
기존 결과 조회 시험에는 추가된 정확한 실행3경로만 허용했고 이전 경로/스키마의 SHA 검사는 유지했다.
전체 backend 시험을 수행한 기록은 아니다. 실제 DB/TLS 연결 검증은 후속이다.

## 자원·남은 작업

최종231.099353438초·단일 PID241,168,384/합900,616,192bytes·FD4→4로
원600초/512MiB PID/합1GiB 안이다. 원2148항목/5root·두 서비스 source/assets·소유 process/PG/임시/passfile0을 확인했다.
OpenAPI 생성만 기존 schema guard가 허용하는 contracts/openapi-v1.json 한 파일의 의도된 변경이다.
나머지 source와 보호 자원은 보존했다.

다음은 같은 실행 graph를 명시한 prefix3경로→실제 SCRAM/검증 TLS·원 byte/UTC/계산·조회쓰기0 수용이다.
이후 runtime/독립 worker→typed web/같은 UTC3D→사용자 적용을 진행한다.
새 CO₂ 사용자 배포·공통 WSL 용량/전체 작기·자원/경제·최종 UI/실제 CLI 종단 간·실제 농장0/관문은 미완료다.
