# 등록 수확 산술의 현재 권리 조회 — v1

2026-10-08 구현 전 계약. [서버 등록](crop-harvest-registration-v1.md) 뒤 current query·집중/native 시험·
이 계약3 core파일로 구현한다. 현재 native Codex CLI `gpt-6.1-sol / xhigh`에서 판단하며 재귀 CLI는0회다.

## 인터페이스

`HarvestCurrentQuery(registry)`는 정확한 `HarvestRegistry`와 별도 reader 로그인만 받는다.
`read(tenant, result_id, farm_ref, *, start=0, limit=None)`는 현재 읽기 scope/표시 권리 아래 등록 record·
summary·선택 page·조회 identity를 반환한다. limit=None은 start0의 summary이며 page는 정수1~64행이다.
`open(...)`은 같은 검사를 수행하는 context manager이며 context 종료 직전에도 재검사한다.
유효한 현재 계정의 없는 등록은 None이다. 잘못된 ID/농장/범위는 hold이며 다른 계정/scope는 PermissionError다.

등록 ID와 농장 참조만 받으며 metadata의 서버 key/hash로 파일을 연다. 고객 경로/hash·미등록 HEAD를 권위로 받지 않는다.
원 record의 metadata 원문/SHA·첫 시각, 원 UTC/단위·가정/미배정·source hold·승인false를 보존한다.
내부 결과를 metadata UTF8/ISO 시각으로 정규화한 JSON 전체는2MiB 이하이며 별도 API DTO/SDK는 후속이다.

## 검사와 복원

현재 읽기 scope→실제 reader DB/역할 감사→metadata HMAC/닫힌 형식/열/판본→원 농장·source→
artifact HEAD/root/page·원문/행 수/순서→반환 전 같은 DB record/현재 원 권리/파일을 확인한다.
기존 표시 권리가 있으면 계산 권리·쓰기 scope가 없는 저장 결과도 읽을 수 있다.
계산·수확 행 생성·등록·새 증명은 수행하지 않는다. publisher 쓰기는 별도 선행 단계다.

별도 Python exec에서는 기존 보호 runtime 조립을 재사용해 같은 실제 DB·농장/원 입력·원서명·
result evidence·registry reader/key 파일을 복원한다. 소유한 표시/계산 권리 provider는 판본과 시험 소스 hash를
보호 bundle에 고정하고 실제 현재 권리 파일을 읽는다. 소유 페이지 callback이나 fork된 메모리로 복원을 대체하지 않는다.
bundle/고정 파일 hash·private mode/경로를 확인하고 key/DSN 원문·비밀/실농장 원자료는 출력하지 않는다.

## 수용

1. 잘못된 제공자/역할·ID/농장/범위·코드/응답 용량을 거부하는 순수 검사를 통과한다.
2. 실제 SCRAM reader의 summary/전체·분할 page가 같은 저장6행·등록 record/원문/UTC와 일치한다.
3. 표시 권리만 남긴 읽기와 현재 write scope 없는 읽기는 성공하고 표시 철회·계정/scope·
   혼합 농장·변조·페이지 뒤 권리/등록 변경은 거부한다. 원 raw bytes를 복원하고 새 판본으로 덮어쓰지 않는다.
4. fresh Python이 같은 실제 DB authority를 재구성해 정상 전체/분할과 현재 권리 거부를 확인한다.
   crop RHS/수확 행 재생성/등록/새 proof를 금지하고 실제 child 종료·FD·부모/원 파일·자원을 보존한다.
5. 실제 조회 시간/페이지·2MiB/WSL cap·DB schema/role/passfile·보호 key 파일·PG/child/temp 정리를 확인한다.

증거 뒤 query 자식과 충족한 작은 등록/현재 조회 부모만 체크한다. 전체166일 새 질량/배정 조회 부하·
HTTP/SDK/3D·실제 품종/자료·G0–G4 수용은 별도다. 기후/물·양분/구매 에너지·Decimal 경제 연결은 후속이다.
실제 품종/계수·국내 독립 자료·실측 농장 작물 Run0건, 생산/미래 마진/추천·원격 Backend/push·
구형 native25시간 원 종료 hold를 유지한다. 최종 production 완료일은 외부 자료 확보 상태에 따라 갱신한다.

## 로컬 수용과 다음 공개 투영

2026-10-08 22:04 KST [실제 검증](../research/crop-harvest-current-query-implementation-20261008.md)으로
순수23개/실제 SCRAM1개·집중24개·원 종료0·6저장 행/4파일·summary/전체/분할·표시 권리만 남긴 읽기·
fresh Python 실제 DB 정상/표시 철회2개·현재 scope/계정/서명/파일·종료 시 권리/row 오류 주입/page 변조 거부·
FD13→13/자식4→4·426 source/보호 파일19개/DB·PG 정리를 확인했다.
원 마감600초 안의324.090초이며 시험 당시3 core파일 snapshot/hash는 영수증에 보존했다.
query 자식과 작은 현재 조회 부모만 수용한다. 전체 harvest replay·품종/관문은 미수용이다.

전체 내부 정상 응답은 정규화 JSON70,444bytes다. 작은 page는22.950~23.019초, summary13.808초이며
HTTP30초/2MiB와 전체166일 새 질량 조회 비용을 대신하지 않는다.
다음 공개 투영은 계약·`backend/app/api_crop_harvest_replay.py`·집중 시험3 core파일로 착수한다.
닫힌 DTO·원 ID/부모/source·UTC/단위/정확 수량·계수/배정 판본·미배정/hold·승인false·2MiB를 유지하고
비밀/HMAC/private 경로·권리 원문은 내보내지 않는다. 원6행/전체·분할을 대사하고 재계산0을 확인한다.
그 뒤 인증 route/runtime·실제 TLS→SDK→같은 UTC 표/3D로 진행한다.
