# 환기 공동 계산의 원 UTC 결속 v1

선행은 [새 환기 continuation](crop-greenhouse-ventilation-continuation-v1.md) 수용이다.
핵심3은 `backend/app/crop_greenhouse_ventilation_time.py`, 해당 tests, 이 계약이다.
기존 [공동 UTC 계약](crop-climate-joint-time-binding-v1.md)의 순수 달력/격자 helper·typed error를 재사용하며
새 frozen Binding/모델 판본·helper code SHA와 새25장부 context identity로 구분한다.
기존 시간 모듈·22장부 context/checkpoint·계산 식/프로필·원 결과는 변경하지 않는다.

## 입력과 시간 규칙

`prepare_binding(context,origin=...)`는 수용된 새 context와 닫힌 origin
`input_id/origin/start_at/precision`을 받는다. origin은 source scope와 같고 precision은 microsecond다.
명시 RFC3339 offset·소수6자리 이하·UTC 연도1..9999, offset의 시/분 범위를 검사한다.
모호한 local 시간·`-00:00`·윤초·7자리 이상·범위 초과를 거부한다.
`str(step_seconds)`의 decimal rational이 정확한 양의 정수 microsecond일 때만 결속한다.
시점은 UTC 시작+원 정수 index×정수 microsecond다. 소수 격자를 반올림하거나 새 격자를 만들지 않는다.
원 binary64 elapsed는 그대로 둔다. 예:0.1초×3은 원 elapsed0.30000000000000004와 UTC0.300000초를 함께 보존한다.
manifest는 origin 원문·정규 UTC 시작/끝·시간 규칙/코드·calendar helper SHA·원 context hash를 결속한다.
같은 순간의 UTC/KST 표기는 같은 UTC를 만들지만 원문이 다른 origin identity는 구분한다.

공개 함수는 `at_index(binding,index)`, `bind_checkpoint(binding,checkpoint,expected_binding_sha256=...)`,
`source_chunk_sha256(context,chunk)`, `bind_chunk(binding,before_checkpoint,chunk,expected_chunk_sha256=...,expected_binding_sha256=...)`다.
binding manifest16KiB·source/result8MiB 상한과 JSON 복사 반환을 유지한다.
producer가 보관한 trusted binding/chunk SHA를 필수로 검사한다. 내용 재해시는 서버 custody/권한 승인이 아니다.

## 원 결과와 실패 시점

UTC 결속은 RHS/환기/적분/관리/restore를 호출하지 않는다. 원 source를 canonical 복사하고 SHA에 묶는다.
원108상태·25연속/6사건·10수지/환기 진단·journal 수치와 checkpoint bytes/prefix를 재작성하지 않는다.
before/after checkpoint의 원 position/cursor/prefix와 새 source의 닫힌 필드·모델/manifest/기간을 검사한다.
원 경계 예산128·sample/event 정렬/누락·elapsed·완료 위치·마지막 상태와 checkpoint 일치를 검사한다.
확인된 계산 호출은 joint6×완료 걸음+3×사건, 환기5×완료 걸음+사건이며 checkpoint 검사 각1회를 별도 확인한다.
구형2개 호출 필드를 새4개 필드로 임의 변환하지 않는다.

`yielded/completed/hold`를 유지한다. hold는 원 global index/elapsed/phase/reason/inner_failed_stage를 보존한다.
interval/global-step 실패의 마지막 확정 시점은 직전 원 경계이며 실패 시점과 구분한다.
event/event-after-ventilation/global-event 실패는 같은 시각 사건 전 확정 step-end를 보존한다.
실패 사건/선택 출력을 만들지 않는다. initial-ready와 경계0 완료는 UTC가 같아도 원 identity/position이 다르다.
source의 숫자가 과학적으로 옳다는 판정·현재 권리 검사는 이 순수 시간 모듈의 기능이 아니다.

## 수용 기준

1. 수용된10program×예산1/7/128에서 원 source/수치/장부/진단·checkpoint/prefix 불변과 모든 UTC를 확인한다.
2. 별도 Python에서 같은 원 checkpoint/transport를 결속해 같은 binding/result SHA를 만들고,
   결속 중 RHS/환기/적분/관리/restore0을 차단 함수로 확인한다.
3. 독립 integer epoch oracle로16격자의272시점을 대사한다. 소수/음의 epoch·윤년/비윤년·연말·연도 경계,
   UTC/KST·1microsecond/정밀도·offset/범위·판본/호출/hold/JSON·trusted digest 변조를 확인한다.
4. 초기/사건 전후/마지막·실제 domain/관리/전역 수지/관리 후 환기 hold의 원 시점을 보존한다.
   최대128 sample/event chunk·크기 상한, 구 UTC/새 continuation 회귀·원본/두 사용자 서버·원 종료/FD/소유·WSL 한도를 확인한다.

범위는 `software_research_only`, G0_G4=`not_assessed`다.
새 입력/QC·현재 권리/서버 custody·불변 저장/API→worker/같은 UTC3D/사용자 적용은 후속이다.
전체 작기·실제 생산/미래 마진/추천 관문 수용은 아니다.
