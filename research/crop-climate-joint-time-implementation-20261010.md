# 작물·기후 원 격자의 UTC 연결 — 2026-10-10

## 수용 범위

core **a8c70282c94e804936212ad3bb9ba01c95c74b3b**의
[시간 모듈](../backend/app/crop_climate_joint_time.py), [시험](../backend/tests/test_crop_climate_joint_time.py),
[계약](../contracts/crop-climate-joint-time-binding-v1.md)을 로컬 수용했다.
[공개 검증 묶음](artifacts/crop-climate-joint-time-reference-20261010.json)에 actual exit·원 hash·환경/CLI·자원 결과를 기록했다.

명시 상수 forcing/RGR의 기존 짧은 합성9프로그램에 원 시작 시각과 정수 마이크로초 UTC 표시를 연결한다.
원108상태·연속22장부·사건6합계·전역7수지·동적 T24/Tsum/RK4 및 원 checkpoint/prefix를 변경하지 않았다.
start origin·offset provenance·시각 변환 판본/코드와 원 context를 별도의 binding identity로 고정한다.
실제 시작 시각을 원 물리 상태에서 추론하지 않는다. source SHA와 binding SHA는 신뢰한 producer/후속 custody가 공급해야 한다.

## 실제 검증

| 단계 | 원 실행/완료 도구 | 실제 결과 |
| --- | --- | --- |
| 최소 시간 연결 | 81736 / `01eaf2` | 2개 통과·원 종료0·0.562초 감독 |
| 집중 | 50718 / `863d00` | 확장 전120개 통과·15.389초 감독 |
| 최종 회귀 | 46128 / `7cbf83` | 새130/기존786=916개 통과·pytest79.83초·80.356초 감독 |
| 별도 root | 24702 / `aa0674` | 원 종료0·7.207초 감독·아래 독립 대사 |

root는 기존 수용 artifact의9개 context/final checkpoint·sample/event SHA와 이번 원 계산을 정확히 대사했다.
기존23 core 파일·16 oracle 입력과9개 구성 코드의 기존 판본을 보존한다.
27sample/10journal의 원 수치 상태5,076개와 전체 source canonical 값, 모든 원 prefix/checkpoint bytes가 그대로다.
여러 chunk의 sample/event/last_confirmed **91개 시간 기록**을 연결했다.
별도 정수 epoch/calendar oracle의 **272개 시각**이 일치했다. 1969/1970 epoch·2000 윤년·2100 평년·연말,
1µs/0.0625/0.1/2초 격자를 포함한다. 시험은 year1/9999 끝값, UTC/KST·초기/t0사건/중간/마지막도 검사했다.

실제 마지막 적엽 실패는 확정 step-end와 실패 경계의 같은 UTC를 유지하고 실패 사건/선택 출력은 만들지 않았다.
실제 온도 영역 실패와 주입한 전역 step/event 수지 실패도 원 확정 prefix만 보존했다.
naive/이름 시간대/unknown offset·잘못된 날짜/offset/윤초·정밀도 손실·bool/범위,
origin/context/코드/시간 정책/이전 checkpoint·커서/누락/순서/원 elapsed/prefix 혼합과 변조를 거부했다.

binding 단계의 **RHS/step/event/restore/advance 호출은 모두0회**다.
별도 Python PID1896473도 실제 종료0·같은 binding/result SHA를 냈다.
그 과정의 초기 context1회+현재 두 checkpoint 검증2회 RHS는 setup으로 따로 세었으며,
과거 구간/사건 재실행0·binding 수치 호출0을 확인했다. 복원을 UTC 변환의 일부로 숨기지 않았다.
기존 독립 Decimal5,973수치/60수렴 비율은 해당 predecessor의 증거다. 이번에 재실행했다고 주장하지 않는다.

## 표현·출처·권리

[PostgreSQL16 timestamp](https://www.postgresql.org/docs/16/datatype-datetime.html)와
[Python3.12 datetime](https://docs.python.org/3.12/library/datetime.html)의 마이크로초 표현에 맞춰
정수 timedelta를 사용했다. [RFC3339](https://www.rfc-editor.org/rfc/rfc3339.txt)의 더 넓은 표현 중
unknown-offset/윤초·6자리 초과는 이 모듈에서 지원하지 않는다. RFC 자체의 제한으로 설명하지 않는다.
dt0.1의 index3은 원 elapsed0.30000000000000004를 유지하며 표시 UTC 간격은300000µs다.
그 변환 규칙을 새 identity에 명시했고 physical temperature clock을 바꾸지 않았다.

3개 공식 문서의 URL/product ID·조회 시각·raw SHA·revision/QC·reference use/display/redistribution 판단은
공개 묶음의 `technical_sources`에 있다. 발행/관측 시각이 확인되지 않은 곳은 null이며 available_at을 과거로 만들지 않았다.
원 HTML/TXT는 private에만 보존하고 원문·농업 데이터/계수의 채택/재배포는 없다.
판단은 native Codex CLI **gpt-6.1-sol / xhigh**, turn2026-10-09T17:30:31.711Z에서 수행했다.
완전 원 JSONL 줄(LF 포함)의 SHA는
`fe0a7ad9239dc3abc9cb414e60da4e66f76dbd059759a50b0fbc7d74e2cfb9d3`이며 recursive CLI0회다.

## 원본·자원·현재 화면

모든 감독 단계는 source1,719·원본2,148항목과 고정 미리보기 source/assets·실제3개 PID identity를 보존했다.
FD4→4·소유 non-zombie 잔류0·frontend200을 확인했다. 이번 관측 최대 단일 RSS147,255,296bytes,
소유+보호 합407,535,616bytes로512MiB/1GiB 안이다. 원 전체166일 계산·수확 writer/API/WebGL을 다시 실행하지 않았다.

최대 첫 chunk128sample/128event/127걸음의 source4,996,376bytes·시간 포함5,010,569bytes,
시간 manifest631/checkpoint10,578bytes다. 내부8MiB 상한에는 맞지만 **HTTP2MiB 응답에는 맞지 않는다**.
다음 페이지 저장/읽기와 현재 권리 API를 건너뛰어 전체 chunk를 웹에 보내지 않는다.

현재 `localhost:5173`은 기존 완료 합성166일의 저장 생장/수확과 같은 UTC3D를 읽는다.
이번 새 공동 모델/시간 연결은 UI에 미연결이며 진행률·새 checkpoint 자동 반영 U3도 미구현이다.
hosted exact703e49c Backend37962183498은 partition0 success·1/2 in_progress·3/4/5 queued로 관측했다.
기존 실행을 취소/재시작/새 push로 대체하지 않았다. 이번 core의 hosted 수용은 별도다.

## 다음 구현·외부 의존성

다음 core3은 `crop-climate-joint-page-storage`다. 계약/기존 atomic 저장 재사용 검토→
불변 manifest와64sample/8event 페이지 writer·fresh reader→변조/실패 prefix/권리 연결 경계 검증→증거 기록으로 나눈다.
원 context/binding/checkpoint/출력 hash·108상태/22/6장부·UTC를 그대로 복원하고 읽기 RHS0,
페이지의 실제2MiB 이하·원본/FD/원 종료/자원을 수용 기준으로 삼는다.
이후 현재 권리 등록/API→같은 UTC3D→사용자 실행/U3 순서다.

이번 child는 최종 회귀80.356초·root7.207초로 검증했다. 다음 저장 child의 잠정 예산은
계약/재사용0.5–1시간, writer/reader0.5–1.5시간, fresh/변조/자원0.5–1시간, 기록0.5시간의 **2–4집중시간**이다.
계속 작업·새 I/O/복원 장애 없음 조건의10월10일 검토 목표이며 전체 제품 완료일은 아니다.
온실/forcing 변경·물/양분·구매 에너지·Decimal 경제 연결은 미완료다.
실제 품종 입력/농장 Run/국내 독립 자료0건·권리/자료 확보와 G0–G4/생산·미래 마진·추천 hold를 유지한다.
