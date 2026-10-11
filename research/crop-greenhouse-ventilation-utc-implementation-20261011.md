# 환기 공동 계산의 UTC 결속 — 2026-10-11

**2026-10-11 23:08 KST 로컬 수용.** [핵심3파일 계약](../contracts/crop-greenhouse-ventilation-time-v1.md)과
[기계 증거](artifacts/crop-greenhouse-ventilation-utc-reference-20261011.json)를 기록한다.
새25장부 continuation의 원 index에 정확한 UTC를 붙인다. 원 상태/장부/환기 진단/사건·계산 격자는 그대로다.

## 구현과 확인한 증거

기존 순수 origin/달력/격자 helper와 typed error를 재사용하고 새 frozen Binding·모델 판본과 helper SHA를 결속했다.
명시 offset·microsecond/범위·원 decimal step의 정수 microsecond를 검사한다.
원 binary64 elapsed와 정수 UTC를 각각 보존하며, 같은 순간의 UTC/KST도 원 provenance identity는 구분한다.
새 source의4개 호출 필드와 관리 후 환기 실패 phase/inner stage를 확인한다.
초기-ready/경계0 완료의 같은 시각·다른 identity, 실패 시각과 마지막 확정 시각을 보존한다.
UTC 결속은 RHS/환기/적분/관리/restore를 호출하지 않는다. producer의 trusted digest는 필요하며 서버 custody/권한 승인은 후속이다.

| 실제 검사 | 결과 |
| --- | --- |
| 새 UTC |147통과:10program×예산1/7/128=30구성·원 source/수치/25장부/6사건/10수지·checkpoint/prefix 불변 |
| 독립 시각 기준 |integer epoch oracle·16구성×17index=272UTC,1µs/소수·음의 epoch/윤년/세기/연말 대사 |
| fresh·계산0 |별도 Python에서 원 checkpoint/transport의 binding/result SHA 동일·결속 중 RHS/환기/적분/관리/restore 차단 |
| 실제 hold |interval·관리·전역 step/event 수지·관리 후 환기 실패의 원 시점/확정 prefix 보존·실패 사건/출력 생성0 |
| 변조/판본 |origin/offset·microsecond/범위·코드/helper/구 타입·4개 호출·closed hold/source·trusted digest·prefix/cursor 거부 |
| 최대 chunk |128samples/128events·binding16KiB/source/result8MiB 상한 확인; 내부 묶음이며 HTTP 허용량은 별도 |
| 관련 회귀 |기존 UTC130 + 새 continuation175 =305통과 |
| 최종 실행 |고유452통과/pytest100.31초; 원73808 child/tool exit0·guard100.909653334초 |
| 첫 smoke |원29101 child/tool exit0·3통과/guard0.870513575초 |
| guard 보존/정리 |원본2,148·두 frozen source/기존 자산·protected roots4 live·FD4→4·소유 잔존/PG/passfile0 |
| 관측 WSL RSS |.25초 표본, 단일145,842,176/보호 포함 합759,226,368bytes;512MiB/1GiB 이내 |

이번 원2guard 합101.780167초이며 준비/설계·분석·기록은 별도다. 실패 실행0이다.
원 수치/독립 Decimal fixture의 이전 수용은 보존하며 이번에는 새 농업 계수나 수치 oracle을 추가하지 않았다.
새 package/build/API/Chromium/전체 CI·remote는 실행하지 않았다. 사용자 서버 중단/전환0이다.

최종 보존 원50756 child/tool exit0·0.605598066초로 기존235계산 파일 SHA·accepted source1,911/자산171,
두 HTTP200/index hash·현재 runtime/권리·검토/접속 권한·로컬 링크2,002·diff check를 확인했다.

실제 native CLI는 `gpt-6.1-sol / xhigh`, turn timestamp `2026-10-11T13:56:46.299Z`,
context SHA `65a61221b7300697de4daff06c55fee4fa0172a292c30db6b9f618b8b0650630`, CLI 재귀 실행0이다.
농업 근거/자료 권리는 [기존 원문 검토](crop-greenhouse-boundary-source-review-20261011.md)를 따른다.

## 다음 한 단계·외부 의존성

다음은 **새 판본의 불변 페이지 저장/fresh reader**다.
[기존 저장기](../backend/app/crop_climate_joint_storage.py)는 driver.short/management/joint와 구 claim/schema를 전제로 한다.
새 program/stage 구조·25장부/초기 RHS+환기 묶음·UTC helper 판본을 식별하는 새 저장 판본이 필요하다.
기존 파일 저장 helper·페이지 제한/HEAD 원자 교체를 재사용하고 원 bytes/수치/UTC·구 결과를 보존한다.
수용은 새 writer의 initial/yielded/completed/hold·원 prefix와25연속/6사건/10수지·UTC,
독립 reader의 수치/RHS/환기/관리/복원0·fresh 동일,HEAD 전후 강제 종료/재개와 원 결과/FD/소유/WSL이다.
페이지/writer/reader0.5–1 + fresh/강제 종료·범위0.5–1 + 보존/기록0.25–0.5로 잠정1.25–2.5집중시간이다.
이후 새 입력/QC·현재 농장/자료 권리·서버 custody→결과 등록/현재 API→자동 worker/typed web/같은 UTC3D→사용자 적용을 별도 수용한다.
이번 UTC의 이전0.75–1.5시간 잠정 추정은 native22:56 KST→실제 수용 시각/guard 관측으로 대체한다.
[계획](../tasks/plan.md)/[작업 목록](../tasks/todo.md)에 다음 저장 자식을 분리했다.

현재5173은 완료166일 저장 재생,5174는 기존 [A2](crop-climate-joint-prefix-advance-browser-20261011.md)의
합성128초 접수/진행·확정 부분 결과 자동 조회다. 새 환기 모델은 UI 미배포다.
실제 품종/농장 Run·국내 독립 자료0, G0–G4 `not_assessed`, 실제 생산/미래 마진/추천 hold를 유지한다.
다른 온실 경계/물·양분/구매 에너지/경제·최종 UI와 독립 자료가 남아 전체 제품 완료 날짜는 미정이다.
