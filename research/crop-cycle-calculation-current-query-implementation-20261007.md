# 검증 계산 결과의 현재 농장 조회 — 로컬 수용

2026-10-07 KST. `crop-cycle-calculation-current-query`의 작은 등록 합성 농장 소프트웨어 범위를 수용했다.
[고정 영수증](artifacts/crop-cycle-calculation-current-query-reference-20261007.json)에 실제 명령/출력 SHA,
판본별 시험·source·native Codex CLI `gpt-6.1-sol / xhigh` 문맥을 기록했다. 재귀 CLI·새 agent0회다.
새 API/runtime·전체166일 등록 경로/3D와 실제 농업 정확도는 이번 수용에 없다.

## 변경과 검토

[별도 query](../backend/app/crop_cycle_calculation_current_query.py)는 exact 새 store/evidence authority와
새 read context를 결속한다. 원 query의 이름을 정규화한11함수 중9개 AST가 같으며,
`_pins`와 `open`의 변경을 검토했다. 원 input proof bytes와 공식 계산 manifest·root metadata에서
input9/validation8필드를 재구성해 DB binding과 대사한다. 서로 다른 validated/calculation/input proof SHA를 유지한다.
계산 context·private token을 만들지 않고 server의 순수 서명 해석으로 선택한 HEAD의 전체 부모를 확인한다.
query version/code/dependency·resolver/notice/profile·현재 계정/Scope·등록/원천·입력 권리와 DB를 전후 재검사한다.
DB/server/input/result 네 key는 별개다. 실패와 yield 이후 철회도 반환을 차단하고 모든 조회 FD를 닫는다.

정확성·가독성·경계·보안·비용을 검토했고 원55 source와 선행 proof/reader·원 query/test를 합한
**63 source SHA를 전후 보존**했다. 새 서비스·schema는 없다. 구형 signed row 공존의 실제 시험은
[선행 게시 수용](crop-cycle-calculation-result-publication-implementation-20261007.md)에 남기며 이번 재시험으로 표시하지 않는다.

## 실제 시험

| 실행 | 결과 |
| --- | --- |
| 새 validation 연결 전 같은 정상 DB 조회 | 1실패/64.35초·종료1 |
| validation9/8 보완 뒤 같은 정상 조회 | 1통과/78.95초·종료0 |
| 실행 중 query VERSION 변경 반례 | 1실패/63.74초·종료1 |
| 고정 선언 보완 후 최종 새 query 전체 | **12통과/1,079.43초·종료0** |

반복한 사례를 합산하지 않는다. 최종은 단일 집중12개이며 전체 backend가 아니다.
실제 소유 PostgreSQL16.15의 네 host 인증 규칙 모두 SCRAM이고 정상 연결의 `used_password`도 확인했다.
조회 중 parser/context/terminal QC/RHS·server `_open`·`_Journal` 생성을 금지한 정상/사건/hold를 대사했다.
없는 ID/다른 tenant/farm·구형 타입·key 중복·resolver packet 변경과 version/code/dependency 변경을 거부했다.
실제 Scope/계정/등록/원천/입력 권리 철회, DB HMAC/column·intent/HEAD/선택·중간 부모 proof·input/result 변조,
symlink/누락과 page 준비 후/yield 뒤 철회를 확인했다. 형식과 HMAC가 유효한 잘못된 validation도 거부한다.
같은 원 context를 갖되 raw SHA가 다른 유효 input proof로의 대체도 거부했다.

## 원 결과와 조회 비용

| 실제 등록 합성 사례 | 걸음 | 원 시점/사건 | 요약 | samples | events |
| --- | ---: | ---: | ---: | ---: | ---: |
| 정상 | 120 | 3/0 | 5.010523초 | 5.096964초 | 5.021792초 |
| 관리 사건 포함 정상 | 120 | 3/3 | 5.798102초 | 5.872510초 | 5.931896초 |
| 수치 hold·확인 과거 | 60 | 1/1 | 5.813566초 | 6.023316초 | 6.059781초 |

모든 원 sample/event·UTC·manifest/검증 SHA와 terminal checkpoint/clock/cursor를 보존했다.
hold 이유/확인 과거는 독립 원 적분 결과와 같다. 조회 전후 DB 행 수는 같고 세 사례 모두 FD13→13이다.
정상 사례에서는 custody/input의 파일 SHA·mode·inode도 전후 동일하다.
새 서비스/fork 재접속의 같은 페이지와 child 종료0을 확인했다. **farm query의 fresh Python exec는 수행하지 않았다.**
선행 reader의 별도 Python 시험과 이번 fork를 구분한다.

최종 주 시험은 nice19·표본 최대 RSS133,636,096bytes다. PG나 fork child와 합친 peak가 아니다.
OS cache는 통제하지 않았으며 위 시간은 내부 작은 조회 관측이다. 실제 HTTPS 요청·브라우저 실행은0회다.
원 내부 get7.898755초/39.668745초를 보존하고 HTTP30초 수용으로 바꾸지 않는다.
네 실행 모두 실제 DB/schema/역할/비밀번호0개·PG PID/data 부재·소유 temp tree 제거를 확인했다.
원 명령/로그/정리·proof SHA·source는0700 사설 경로의0400 증거에 남겼다.
계약은 실제 실행 뒤 수용 기록으로 갱신했다. 영수증의 계약 SHA는 시험 당시 판본이며 제품/test SHA는 그대로다.

## 후속 순서와 보류

query 자식만 체크한다. [다음 순수 공개 투영 계약](../contracts/api-crop-cycle-calculation-projection-v1.md)은
새 manifest/validation과 ID를 보존하는3 core파일이다. 순수 투영 → 명시적 설정/factory →
인증 route/실제 SCRAM·HTTPS30초/2MiB 순서로 API/runtime 부모를 검증한다.
원 `operator_config.py`가 server 서명의 file helper dependency인 근거로 그 파일을 보존하는 별도 loader를 계획했다.
이어 새 client/같은 UTC3D와 별도 등록 prefix 비용·전체166일 저장/복원 수용을 확인한다.
순수 투영1–2시간+설정/factory2–4시간+route/TLS1–2시간의 총4–8집중시간 잠정이며 실측 뒤 갱신한다.
query의3–6시간 잠정은 위 실제 수용으로 대체한다. CI/전체 작기/외부 자료 완료일은 이 추정에 포함하지 않는다.

[기존 원격 CI 종료 증거](artifacts/crop-cycle-calculation-current-query-ci-prepush-20261007.json)는
`8d111f1`의 다른4workflow 성공·Backend5분할 성공/분할0와 집계 실패다.
[권한 시험 정리의 로컬 수정](application-authority-passfile-cleanup-20261007.md)은 `25b92a0`에 있으며
새 query/수정 판본의 hosted 성공은 별도다. 기존 실행을 취소/재시도하거나 CI 한도를 변경하지 않았다.

실제 품종 입력·국내 독립 검증 자료·실제 작물 Run0건, G0–G4 `not_assessed`다.
전체 연결 뒤 생과/수확 → 물/양분·구매 에너지 → Decimal 경제를 연결한다.
생산 예측·미래 마진·추천과 최종 제품 완료일은 해당 실제 자료와 검증 전까지 보류한다.
