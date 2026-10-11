# 실제 중간 결과 조회 뒤 취소 요청 진단 — 2026-10-11

**API 내부 추적을 끈 실제 실행에서 같은 공개 선택자의 사건·생장200 → 취소 수락 → 독립 worker canceled·결과 미게시를 확인했다. 실제 브라우저 취소와 사용자 적용은 남아 있어 P6a/P6b는 미완료다.**

[기계 증거](artifacts/crop-climate-joint-cancel-request-reference-20261011.json)의 SHA-256은
`50269892854a09201a915918d422a09b554e26503c2b4a6703d95ed5fea8cb45`이다.
[진단 helper](crop-climate-joint-cancel-request-diagnosis.py)는 실패 경로도 기록하는 관측 도구다. 종료0만으로 취소 수용을 판단하지 않고 아래 실제 응답·작업자·보존 증거를 함께 확인했다.
native Codex CLI `gpt-6.1-sol`/`xhigh`의 실제 context SHA는
`d9a178621abe19627a6eda120e9ef6a80efeb0adef03d7fa520ae9a2540a02bb`이고 재귀 CLI 실행은0이다.
제품 core `69e420936aaf628a802cbb4ebf76fed98c8fb43a`의 backend/app203·web/src115파일은5회와 현재 checkout에서 같다. 제품 코드 변경은0이다.

## 최종 비추적 API 검증

원 tool55047의 실제 종료0, 최종 helper의 `untraced`1개 통과/`traced`1개 deselect를 확인했다.
소유 scratch PostgreSQL·실제 SCRAM/TLS API와 별도 자동 worker(chunk8)를 사용했다. API mock·worker 정지/지연·worker 추적은 없다.
진행→공개 요약→같은 선택자 사건/생장→취소 순서다. GET에만 계산·작업 변경 금지 검사를 적용하며 취소 POST는 그 검사 밖에서 실행한다.

| 실제 확인 | 결과 |
| --- | --- |
| 공개 선택자 사건·생장 | 둘 다200, 같은 selector |
| 취소 POST | 200, `cancel_accepted=true` |
| 독립 worker | `canceled`, exit0, busy outcome0 |
| 결과 | 등록 결과·publication 없음 |
| 종료 뒤 prefix | `closed`, reference/page 모두 null |
| GET 계산·변경 / observer 오류 | 모두0 |
| API 내부 trace | 비활성, trace0 |
| guard FD / 소유 process·PG·임시 PG·passfile 잔여 | 4→4 / 모두0 |

취소 요청 관측 시간은0.072967초, 전체 guard85.004초다. 단일/합산 peak RSS154,632,192/1,023,586,304bytes로
0.25초 관측512MiB/1GiB 이내다. 일반 성능 보장이나 전체 브라우저 polling 성능을 뜻하지 않는다.
진행/요약에는 일시503도 있었으며 모든 요청 상태·시간·wire 해시를 기계 증거에 남겼다.
이번 API 진단은 새 WebGL·원 수치 독립 대사 시험이 아니다. 선행 [reader v5 고유267개](crop-climate-joint-prefix-read-cost-implementation-20261011.md)와
[정상/hold 실제 WebGL](crop-climate-joint-prefix-browser-v5-20261011.md)의 수용 범위는 그대로 유지한다.

## 추적의 영향과 실패 보존

앞선 traced tool86285는 진단 종료0이지만 작업은 busy3회→`attempts_exhausted`/failed, 취소 미수락이었다.
API reader의 파일 잠금이 유지된 최소 확인 구간은6.860708초이며 세 번째 worker busy 종료가 그 구간 안에 있다.
처음 두 busy 종료까지 같은 구간 안에 있었다고 주장하지 않는다. PG row-lock 대기는 관측되지 않았다.
API tracing 자체가 실행 시간을 바꾸므로 이 관측을 비추적 일반 동작이나 앞선 실제 브라우저503의 확정 원인으로 확대하지 않는다.
최종 비추적 실행의 busy는0이다. 이 진단만으로 제품 query/worker 변경이나 기반 작업을 추가하지 않는다.

첫 tool87062/37732의 실패는 진단기의 GET 읽기 전용 patch를 취소에도 적용한 문제다.
37732 trace의 `JobStore.cancel`/pytest `Failed`는 주입된500임을 확인했다. 제품500 증거로 세지 않는다.
비추적 tool95985에서는 실제 취소 수락/worker canceled를 확인했으나 monitor의 일시 eventpoll FD가 HTTP FD 기준선과 경합해 전체 수용에 실패했다.
monitor를 HTTP 서비스 기준선 이후 시작하고 종료 검사 전에 닫도록 수명만 수정한 뒤55047에서 통과했다. FD 기준을 완화하지 않았다.
read-only monitor는 소유 setup admin socket이며 SCRAM 검증 대상으로 주장하지 않는다. API/worker의 SCRAM 증거와 구분한다.
각 실행의 helper SHA와 실패를 보존했다. 최종 helper의 traced 분기는 재실행하지 않았다.

## 사용자 화면과 다음 한 단계

사용자 서비스 중지0이다. 원본2,148항목·두 frozen source/자산·보호 root4·현재 키/권리를 보존했다.
최종 확인에서 기존274파일과5173/5174의 HTTP200·원 HTML 해시·root4 생존을 재확인했다.
[접속 안내](../web/README.md#joint-execution-user-preview)는 계속 `run-v8`/`serve-v8`다.
5173은 완료166일 재생,5174는 같은 사용자 DB의 진행/확정 checkpoint polling·종료 후3D이며 계산 중3D는 비활성이다.

다음 **P6a2d2**는 실제 브라우저에서 running WebGL을 확인한 직후 취소하는 경로다.
취소 전에 수행하던 고비용 screenshot 관측만 해당 경로에서 제외할 계획이며 정상/hold의 기존 PNG 증거는 유지한다.
수용 기준은 실제 같은 selector/원 값·UTC/WebGL → 서버 취소 수락 → worker canceled·장면 제거·결과 미생성,
실제 종료/소유 정리·WSL/원본 보존·두 사용자 화면 복구다. worker를 늦추거나 메모리 한도를 올리지 않는다.
P6a 전체 통과 뒤 P6b에서 사용자5174 적용·현재 인증/자동 worker·원 결과/두 주소·접속 안내를 확인한다.

5회 진단 guard 합384.267초이며 준비·분석·문서/commit은 별도다.
다음 실제 브라우저 취소와 유지보수/복구0.5–1.5집중시간, P6a 통과 뒤 P6b0.5–1시간을 조건부 배정한다.
실제 응답/자원·복구 수용 전에는 완료 날짜를 확정하지 않는다. 최종 UI·전체 작기·독립 자료 일정은 별도다.
전체 CI·remote·새 제품 UI build·새 실제 브라우저 취소·전체 작기 재계산은 실행하지 않았다.
실제 농장 Run/국내 독립 자료0, G0–G4 `not_assessed`이며 실제 생산·미래 마진·추천은 계속 보류다.
