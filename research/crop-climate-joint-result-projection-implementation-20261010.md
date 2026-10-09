# 공동 작물·기후 결과의 닫힌 API 투영 수용

2026-10-10 06:14 KST. native Codex CLI `gpt-6.1-sol / xhigh`, 재귀 CLI0회.
core `d6313faf8ae8af4ce15d26b2f2194eea64ab582b`의 projection447줄·tests252줄·계약39줄을 로컬 수용했다.
[검사 기록](artifacts/crop-climate-joint-result-projection-reference-20261010.json)은93,382bytes,
SHA256 `8b9df86ff989ea6e6a0dfee09713c2a630d150633c4e47c793f44b521873c35c`다.
실제 metadata 도구86ed30에서21:09:16.330Z의 모델/강도와 원 LF SHA
`e0f79ac0f9cb74ebe0520ab69b77415d14e1d9d83d607e55e07f363eb90d0299`를 확인했다.
개발 세션의 증거이며 새 제품 runtime CLI 실행/관문 승인은 아니다.

## 구현 범위

[새 계약](../contracts/api-crop-climate-joint-replay-v1.md)은 새108상태 모델의 독립 tag/DTO를 사용한다.
원 source/context/root·농장/crop/batch/zone·code/profile/QC·마이크로초 UTC와
108상태/6파생량/22연속 장부/6사건 합계/7수지·허용오차를 보존한다.
summary에는 원 manifest·마지막 확정값·checkpoint SHA·hold의 실패 경계가 있고,
페이지에는 원 관리 전후 상태/제거량/합계·순서와64sample/8event 한도가 있다.
공개 응답에는 원 forcing/RGR/매개변수·raw event/프로필·tenant/등록 job·권리/review·서명 key를 넣지 않는다.
오류 자유문은 공개하지 않으며 정형 code가 없으면 CALCULATION_HOLD로 표시한다.

소유32초/16걸음의 원3sample/3event를 대사했다. 순수 fixture는 선행 저장 검사의 공개 소유 packet과
같은 원 root/context를 재구성하며 **현재 HMAC 인증 조회를 대신하지 않는다.**
별도의 실제 SCRAM 검사는 정상/hold 결과를 새 store에 등록해 현재 조회한 값을 투영했다.
투영 함수는 HMAC·현재 자료 권리·페이지 소속을 승인하지 않는다.
HTTP 후속은 같은 custody 세션에서 원 페이지를 읽고 투영/직렬화 전후 현재 권리를 검사해야 한다.

## 통과한 검사와 원 실패

최종 같은 core3/source1,758에서 순수38개와 실제 SCRAM2개, **고유40개**를 순차 통과했다.
중간36개 통과는 다른 초기 bytes이므로 최종 수에 더하지 않는다.

| 그룹 | 실제 검사 | 원 exec → terminal | 실제0 / guard초 |
| --- | ---: | --- | ---: |
| 원 수치/단위/UTC·privacy·닫힌 schema·숫자/혼합·페이지/2MiB·fresh exec | 38 | 43890 → 140044 | 4.150 |
| 현재 store의 completed/hold·마지막 확정값/실패 prefix·조회 계산0·DB 정리 | 2 | 15699 → 8c45d1 | 117.071 |

최종 guard 합121.221초이며 pytest는3.43/112.98초다.
별도 exec PID1997396의 summary/samples/events 응답 SHA는 원 응답과 같고 종료 뒤 PID는 없었다.
순수 응답18,904/35,046/73,566bytes의 모든 원 행/시각과 whitelist 사건 값을 대사했다.
조회 구간의 Context/start/restore/advance/RHS/step/event/UTC binding8종 호출은0이다.
fixture의 최초 계산/자료 검증까지0이라는 뜻은 아니다.
유한 음수 sensible energy/온도 타입을 허용하고 잘못된 숫자8종과 혼합/추가 필드24종을 거부했다.
2MiB 검사는 유효 JSON에 공백을 붙인 serializer fault injection으로 실제 UTF-8 bytes 경계를 검사했다.
최대 숫자 페이지의 부하/성능 수용은 아니다. private reason fallback의 변경 packet은 schema-only이며 HMAC 인증 결과가 아니다.

첫 실제 guard60566→4b6b6f는 transient `/proc/.../comm`의 ESRCH를 처리하지 못해 도구1로 종료했다.
임시 root finalizer가 실행 중 시험 socket을 제거했고 원 로그는1실패/1통과/1teardown error였다.
원 child 종료 코드를 직접 관측하지 못했으므로 수용하지 않았다. 실패 로그/관측과 controller 원 SHA를 보존했다.
정확한 시험 경로의 프로세스·PG·passfile·임시 root 부재, source/기존 UI 생존을 확인한 뒤
private 감시 스크립트에 ProcessLookupError 처리를 추가해 같은 제품 core3를 재검증했다.
제품 계산/저장 코드 변경으로 고친 실패라고 보고하지 않는다.

최종 두 guard는 원본2,148항목·기존 UI source/assets/보호3PID·frontend200을 보존했다.
FD4→4·소유 PG/schema/role/passfile/임시 경로·프로세스 정리를 확인했다.
0.25초 관측의 최대 단일PID/소유+명시 보호 트리 RSS 합137,621,504/524,496,896bytes는512MiB/1GiB 안이다.
기존233/82/993 전체 회귀·전체166일 계산/writer·새 HTTP/WebGL/hosted를 재실행하지 않았다.
최종 core pin/AST2개·민감 필드 검사와 관련 문서의 로컬 링크1,702개를 확인했고 diff whitespace 오류는 없었다.

## 사용자 화면과 다음 수용

**http://localhost:5173/** 은 기존 완료 합성166일 생장·수확과 같은 UTC 수치3D를 계속 읽는다.
최근 공동32초 모델은 이 화면에 연결하지 않았다. 재생은 저장 시간의 이동이며 **실시간 진행/U3는 미구현**이다.
이번 수용은 API 투영 자식까지다. 전체 joint replay/기후 결합 부모는 미완료다.

다음은 기존 store `_read`/artifact reader를 재사용하는 같은 세션의 current reader(core3)다.
원 DB/서명/페이지 소속·현재 농장/자료/계정을 유지한 채 투영/직렬화하고 늦은 철회를 반환 전에 거부한다.
그 뒤 route/API 연결→명시 runtime 조립→같은 UTC 수치3D→사용자 실행/U3 순서다.
기존 reader/route의201/95줄과 이번 실제 DB guard117초를 근거로 current reader1–2집중시간,
HTTP2–3집중시간을 잠정 잡는다. 연속 작업·새 계약 오류 없음 조건이며 CI/전체 작기/자료 확보는 제외한다.
이번 투영의 초기2–4시간 추정은 실제 native 최초 설계 기록20:50Z부터 약24분의 개발/검토·실패 재검증 관측으로 대체한다.
실제 품종 입력/농장 crop Run/국내 독립 자료0건이며 자료 확보는 개발과 병행한다.
G0–G4·실제 생산/미래 마진/추천 hold, 운영 기반 d19f7c0 고정을 유지한다.
원900288b Backend37981057415는 이번 actual 조회에서0–4 성공·5 진행 중이었다.
원 실행을 취소/재시작하거나 push/merge하지 않았으며 이번 로컬 core의 hosted 수용과 구분한다.
