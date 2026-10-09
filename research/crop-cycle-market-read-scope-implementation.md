# 작기 조회에 필요한 시장 원천 읽기 범위

상태: **로컬 소프트웨어 수용, 2026-10-06 KST**. 운영 기반 `d19f7c0` 이후의
이 수정은 [실제 작기 조회 비용](artifacts/crop-cycle-api-read-profile-20261006.json)을
근거로 [좁은 계약](../contracts/crop-cycle-market-read-scope-v1.md)에 한정했다.
구현 `505e498`, 긴 HTTP 부분 계측 후보 `dfa1c2f`와
[불변 검증 영수증](artifacts/crop-cycle-market-read-scope-reference-20261006.json)을 구분한다.

`validate_pinned` 한 호출에서 실제 원천 저장소의 SCRAM 연결 하나를 읽기 전용으로
유지한다. 각 원천/권리/숫자와 원 job 입력을 다시 조회·검증하며 연결 종료 전 현재
tenant/scope·effective grants를 재검사한다. Candidate·hold 연결과 모든 쓰기 거래는
기존 경로를 따른다. 원 pinned 검증과 원천 row/job 검증 본문의 AST가 같고 산식은
변경하지 않았다. 실제 CLI `gpt-6.1-sol / xhigh`와 원 line/소스 해시를 기록했다.

## 통과한 검증

새 실제 SCRAM14개는22.67초, 기존 원천·경제 등록·실제 짧은 TLS42개는455.35초에
통과했다. **고유56개 분할 검증**이며 단일 전체 backend 실행이 아니다.
별도 앞선 순수84개/123.03초는 최종 nonempty tenant 선검사 전의 보조 증거다.
첫 red1개/1.17초, 초기11개/21.52초, 새 선검사의 module parametrize fixture 누락
collect error1개/0.89초도 보존했다. 후속 fixture 연결 수정 뒤 최종14개가 통과했다.

- scoped/unscoped typed request·파생 scenario·전체 pin과 Decimal 원장/ID가 같다.
  원천 row/job 검사 횟수(20회 초과)는 같고 source 연결은1회다.
- 현재 scope/tenant/authenticated 철회, 이전 조회 뒤 원 job의 commit된 변조,
  권리 누락, 시작/종료 시 grant drift를 거부한다.
- Read Committed/읽기 전용, write 거부, 중첩 거부, 오류 후 새 조회, 같은 store의
  동시 context별 별도 연결과 정상/오류 연결 종료를 확인했다.
- 기존 경제 등록의 철회·재바인딩·insert 충돌·원자 rollback을 보존했다.
  짧은 실제 HTTPS는 현재 권리·파일/DB HMAC 변조·live grant·재시작/RHS0회를 확인했다.

| 동일 짧은 TLS 시험의 전체 응답 | 이전 수용 | 원천 읽기 범위 적용 후 |
| --- | ---: | ---: |
| 응답 수 | 21 | 21 |
| 최대 경과 시간 | 27.871882초 | 12.764535초 |
| 최대 bytes | 18,718 | 18,718 |

두 실행의 실제 시점 측정이며 모든 환경/부하에서의 속도 보장은 아니다.
동일30초/2MiB를 유지했다. Source120걸음/원3시점/사건0개이며 nonempty event나
긴 결과 HTTP의 수용은 아니다. 앞선 raw 응답 근거는 별도 보존 후 원 경로에
동일 bytes로 복원했고 새 측정은 다른 private 파일에 남겼다.
각 실제 native 실행의 역할/schema/test password/server0, PostgreSQL 중지와
private cluster/admin password 삭제를 확인했다. nice10/PG16.15이며 hosted lock의
실행 증거로 재분류하지 않는다.

## 다음 한 단계와 외부 의존성

같은 등록25시간/11,400걸음 실제 계산과 검증 HTTPS에서 원27시점/5사건 전부·빈
종단 페이지·서버 재시작을 대사한다. 각 전체 응답30초/2MiB·RHS0·FD/lock과
DB/비밀/서버 정리가 수용 조건이다. 실패 시 view/restart/offset/limit·진행 단계와
시간/status/bytes를 private 부분 계측에 남기는 후보는 syntax/collection만 확인했고
실제 긴 호출의 계측은 아직 실행 전이다. 앞선 긴 실패 영수증은 보존한다.

그 수용 뒤 client → 같은 저장 ID/UTC 성장 연구3D → 실제 작기 부하 → 근거 있는
생과·자원·경제로 진행한다. 실제 품종 입력/독립 국내 농장 자료0건과 crop Run0건,
생산 예측/추천·전체 제품 CLI·G0–G4는 미수용이다. 독립 농장 자료 확보는 병행한다.
