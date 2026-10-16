# 일사 공개 응답·현재 조회 로컬 수용 — 2026-10-17

[기계 증거](artifacts/crop-greenhouse-solar-public-query-implementation-20261017.json) · [공개 응답 계약](../contracts/api-crop-greenhouse-solar-replay-v1.md) · [현재 조회 계약](../contracts/crop-greenhouse-solar-current-query-v1.md).

## 구현과 증거

`joint-solar-replay-v1`의 닫힌 타입은 원108상태·41연속/6사건 장부·15수지/허용오차·단위/마이크로초 UTC를 보존한다. snapshot과 관리 전후 solar_before/solar_after의 환기·열·PAR·가상 NIR 진단을 같은 원 값으로 제공한다. 출처/progress SHA, 원 모델 component code/policy/source/notice 지도와 `rights_or_gate_approval=False`를 유지한다. 원 event·combined forcing/매개변수·프로필/출처 본문·tenant/내부 job·review/rights·자격 정보는 제외한다. 자유 형식 hold 오류는 CALCULATION_HOLD로 제한한다. 새 계산식/계수·보간·생장/경제 출력은 도입하지 않았다.

정확한 SolarResultStore의 같은 `_read` 세션·원 artifact에서 페이지를 선택하고, 투영 전과 직렬화 후 DB row/HMAC/컬럼·두 원문과 현재 권리를 다시 확인한다. 반환 전 HEAD/root/progress·계정·농장·입력 검토/권리를 대사한다. 단독 projection은 HMAC·권리·관문 승인이 아니다. 공개 bytes는 samples64/events8·2MiB 이하이며 caller가 page/terminal을 current query에 주입할 수 없다.

**새89/기존17=고유106검사**를 수용했다. 아래 원 tool session은 모두 실제 종료0이다.

| 배치 | session | 통과 |
| --- | --- | --- |
| 원 producer 공개 타입·값/진단/프라이버시·hold | 76565 | 79 |
| 실제 current hold·정확한 초기화 타입 | 88002 | 5 |
| 같은 DB의 독립 순차 fresh 2회 | 1976 | 1 |
| 투영/직렬화 도중 현재·늦은 철회 | 74657 | 2 |
| 직렬화 후 DB/원 파일 변조·조회 경계 | 10603 | 2 |
| 기존 schema/roles·store transaction identity | 97367 | 17 |

정상/보류 summary·samples·events를 원 응답과 대사했다. 실제 SCRAM·동일 DB/역할/키/파일에서 독립 프로세스 B/C의 응답 SHA가 같고13수치/복원/CLI 및 SQL 변경 카운터가 모두0이다. 5종 철회×3view를 투영/직렬화 두 시점의 전/후에 적용해60건을 차단했다. 계정 비활성·자료 검토·read scope·자료 권리·농장 원천을 포함한다. 직렬화 후8종 DB 조회 fault injection과 실제 소유 페이지 파일 변경을 차단했다. 이 fault injection을 실제 DB UPDATE 실행으로 주장하지 않는다. 잘못된 view/농장/범위·다른 계정·없는 결과·빈 페이지·2MiB 상한·변경된 조립도 확인했다.

## 자원·시험 환경

512MiB/PID·합1GiB·명목0.25초·numeric thread1/nice19와 필수5root/동적 자식을 유지했다. 수용 합 최대1,039,024,128bytes·단일 PID 최대137,015,296bytes, 원본2,148항목/원 소스·자산·FD4→4·소유 PG/프로세스/임시 PG/자격 파일/시험 schema·roles 정리를 확인했다. production 운영 용량 증거가 아니다.

초기 독립 조회 시도2건은 시험 증거 출력의 os import 누락과 준비 중 RSS 초과로 실패했으며 통과 수에서 제외했다. 수정 후 같은 통합 시험 함수를 가벼운 stdlib 부모에서 직접 실행했다(모든 assertion 활성). pytest도 같은 함수 본문을 사용한다. 부모의 불필요한 pytest/psycopg 로딩을 제거했고 같은 DB/키/원문에서 준비 A→조회 B→독립 재조회 C를 순차 실행한다. 원 검사를 생략하거나 가짜 subprocess 결과로 대체하지 않았다. 소유 시험 PG만 명시1MiB/JIT off 예산을 사용했다. 기존 사용자 서비스/키/배포 역할은 변경하지 않았다.

순수 projection fixture는 자기 작성 합성 자료와 새 원 producer를 사용한다. 축소한 휴대용 metadata 형태는 등록 농장·서명 custody/HMAC·G0 승인을 입증하지 않는다. 실제 current 조회 수용은 별도 SCRAM/farm/source 검증 증거다.

## 사용자 진행 기록

원 session94719 실제0: 두 주소의 최신 개발 기록이 HTTP200/no-store·원 bytes와 일치하고 기존 두 HTML·환기 frozen2,173파일을 보존했다. 기록 시각2026-10-17 03:00:02KST·SHA a72d98d046d0ac041e0aa4bf6ead191163b81859f1035e4be442855ee6099457이다. 현재 DOM/WebGL 재검증은 아니며 기존 환기 사용자 적용을 유지하고 새 일사 HTTP/3D 미배포를 명시했다.

## 범위와 다음 한 단계

합성32초/G0–G4 not_assessed·실제 농장 Run0·새 일사 미배포다. 실제 지역/품종/한 작기 생산·구매 자원·경제/추천·최종 UI·완료일은 미정이다. 전체 CI와 현재 브라우저 DOM/WebGL은 재실행하지 않았다. 전체 goal은 active다.

다음은 **보호 HTTP·명시 runtime** 연결이다. 먼저 실제 인증 HTTP route의 별도 일사 ID/닫힌 query/GET body 거부/no-store·오류/전후 계정 검사와 같은 trusted query/store/jobs/farm 결속을 검증한다. 실제 SCRAM·검증된 loopback TLS에서 정상/hold 원 summary/samples/events bytes·UTC/단위와 늦은 철회·연결 종료·계산/SQL 변경0을 확인한다. OpenAPI의 기존 경로/스키마·원 결과/키/두 UI/5root/WSL/정리를 보존한다. 이어 전용 operator/runtime의 명시 flag→독립 자동 worker/확정 prefix→같은 UTC3D→사용자 정상/hold/취소·재접속/재시작 순으로 수용한다. 독립 농장/미래/광학·시설·시장 자료의 권리/QC 확보는 병행하며 실제 예측·추천 관문을 유지한다.
