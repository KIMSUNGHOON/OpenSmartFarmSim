# Cycle 실제 서버 계산과 서명된 진행 상태 — 구현과 검증

상태: **로컬 소프트웨어 수용**, 2026-10-05 KST. `crop-cycle-server-custody`.
[계약](../contracts/crop-cycle-server-custody-v1.md),
[불변 영수증 v2](artifacts/crop-cycle-server-custody-reference-20261005-v2.json),
[독립 제어 흐름/별도 Python 참조 실행](crop-cycle-server-custody-reference.py)을 확인한다.
현재 Codex CLI `gpt-6.1-sol / xhigh`, 설계10:50:09.576Z와 수용12:12:17.766Z의 turn_context/원 line SHA를 기록했다.
재귀 CLI0회이며 제품 runtime CLI 실행/G0–G4 수용이 아니다.
v2는 첫 영수증의 pending 문서 검사만 완료한다. 이전 농장 영수증의 commit key를 잘못 읽은
검사 오류와 [원 v1](artifacts/crop-cycle-server-custody-reference-20261005.json)을 보존하며 계산/시험 증거를 바꾸지 않는다.

## 구현 범위

core5파일은 새 module/순수 파일 시험/실제 SCRAM 농장 시험/계약/참조 실행이다.
운영자가 고정한 CycleFarmBinding·private root·별도 key·판본/identity가 고정된 input resolver만 사용한다.
사용자 요청의 파일 경로나 외부 계산 파일을 가져와 인증하지 않는다.
기존 정확한 ArtifactWriter가 실제 frozen RHS/원 RK4 격자/사건/페이지를 계산하며 원46개 hash를 보존했다.

서명된 불변 intent가 tenant/요청/binding/원 입력/context/header/code/고지/한도를 묶는다.
새 HEAD SHA를 파일명으로 한 HMAC proof를 먼저 fsync하고 원 atomic HEAD를 게시한다.
복원 때 실제 선택 HEAD의 proof/parent/signature와 artifact chain을 확인한다.
orphan proof가 현재 상태를 바꾸지 않고 unsigned 새 계산 HEAD는 hold다.
최초0commit에도 같은 게시 순서를 적용한다. 알려진0step header만 복구하며 알 수 없는 계산 파일은 채택하지 않는다.

root/intent/writer의 nonblocking lock과 private directory/file의 소유권·mode·ACL·link·NOFOLLOW,
현재 원 입력 파일/고정 코드·프로필·현재 farm/source/input/scopes를 전후 대사한다.
임시/orphan 파일도 전체 예산에 포함하고 새 RHS 전에 유한 여유를 확인한다.
advance/inspect/page는 코드별로 닫힌 progress bytes와 원 페이지를 돌려준다.
읽기/완료 재시도는 RHS0회다. 같은 revision의 다른 선언은 conflict다.

## 실제 시험과 수정

최종 고유 **46개 분할 수용**: 순수29개 + restart7개 + global/code3개 + numeric hold2개 + SCRAM 고유5개.
단일46 GREEN/전체 backend 수용이 아니다. 일부 앞선 증거는 `bd1030b` 판본이며 final reader 정리 수정은
거부된 subclass의 Base InputPacket.close 한 분기다. 원 math/binding/API46개와 계산 격자는 그대로다.

| 실행 | 관측 |
| --- | --- |
| 첫 순수 | 18통과/14.01초; 다음 시험에서 권한/alias 변경 공백을 확인 |
| 실제 반례 | source mode/hardlink/directory와 열린 proof directory 교체4실패/5.79초 |
| 입력/디렉터리 재검사 수정 | 28통과/26.81초; 변조 proof의 controller HMAC 재서명도 포함 |
| 페이지 전후 권리 검사 | 29통과/28.11초; 중간 display 철회,6원 프로그램의 canonical 원량/UTC |
| 실제 종료/복원 | 7통과/14.49초; exit41/42/43/44와 selected1/1/1/2commit, known0step/FD, 별도 Python exec |
| 실제 SCRAM 첫 연결 | 3통과/261.65초; 현재 farm/root·서버 계산·동일 새 service/완료 retry·중간 input 철회/외국 tenant |
| reader resource 반례 | 1실패/19.81초; 거부한 subclass가 FD12→13으로 남았음; 실제 RHS0회 |
| Base close 수정 뒤 | 실제 정상+reader2통과/148.51초; 순수 관련10통과/16.29초 |
| global/code | 3통과/0.88초; root129intents·두512MiB sparse orphan의 전체1GiB 초과·code/고지 변경을 RHS 전 거부 |
| 실제 lock/conflict/source | 1통과/64.06초; root lock 중 빠른 pending·동일 revision 다른 선언·현재 실제 경제 source provider 철회 |
| 수치 hold | 2통과/2.02초; pre-onset/늦은 관리 실패의 hold/확인 과거·canonical 페이지와 읽기 RHS0회 |

처음의 module 부재 수집 오류는 missing-module 관측이며 기능 실행 RED로 세지 않는다.
앞선4반례와 FD 누수는 실제 실행 RED다. 최종 원46개 source hash는 일치한다.
순수 파일 시험의 callback/key/등록 없는 binding은 소프트웨어 증거다.
실제 SCRAM도 합성 농장·fake rights/source이며 농장 측정/권리 승인/G1/G4의 증거가 아니다.

실제 local Python3.12.3/Psycopg3.3.6/Pytest9.1.1·native PostgreSQL16.15,
private loopback cluster 순차1개/32connections/16MB shared/1MB work/16MB maintenance/nice10이다.
네 DB 실행 뒤 roles/schemas/runtime password0·PG stop/status3·private cluster/admin 제거·소유 서버0이다.
최대 순차 자식RSS127.734375MiB는 WSL 전체/동시 process group 합계가 아니다.
첫 runner의 이전 binding용 `application_crop_custody_or_run_created=false` 항목은 잘못된 파일 설명이었다.
원 proof를 보존하고 **signed files 생성true/DB crop row와 actual Run0**으로 새 corrected proof를 기록했다.
측정/실행/정리 값은 수정하지 않았다.

## 25시간 실제 RHS와 pending event 재시작

별도 원식 제어 흐름은 frozen rates를 공유하되 새 driver/index/cursor를 사용하지 않는다.
독립 농장/독립 생물학적 모델 검증과 구분한다. 300forcing/90,000초의 **11,400실제 걸음**을 계산했다.
4,864step·`2026-01-01T10:40:00Z`의 step-end/active segment127, 관리 사건 직전 상태에서 중단하고
새 Python exec가121개 float64/전체 checkpoint bytes를 정확히 복원했다.
마지막 vector/prefix/counters와27sample/5event의 canonical payload가 제어 흐름과 같다.

원 artifact는93commit/755,868bytes/127files다. intent/proof를 포함한 전체는
**829,769bytes/223files**, 총238.459932초다. parent/child 최대RSS96.703125MiB다.
7페이지/조회8.376323초·최대61,591bytes이며 RHS/advance0회, temp/child/FD 정리를 확인했다.
이 참조 실행은 reader 정리 수정 전 `bd1030b` 판본을 고정한다. 수정은 invalid subtype 거부 경로뿐이며
수학/정상 writer 경로를 변경하지 않았다. 실제166일 부하나 실제 품종 작기 수용으로 표시하지 않는다.

수정 후 SCRAM fixture progress는976bytes, 계산39.879813초/조회16.592199초,
sample16.657031초/event16.631405초를 관측했다. HTTP/TLS30초 gate·동시 처리량의 측정이 아니다.
모든 DB 실행에서 crop row/actual Run0개다. 결과는 private files의 합성 생장 연구다.

## CI와 다음 한 단계

선행 `ff6eb3d`의 [전체 CI5개](artifacts/crop-cycle-artifact-schema-roles-ci-20261005.json)는
backend3,862개·별도UID4개·여섯 동일 목록/정리·집계와 Authored 첫 시도7job까지 성공했다.
이는 cycle artifact/schema/roles까지이며 farm binding/이번 server custody는 그 SHA 밖이다.
새 코드의 hosted 수용은 별도 CI에서 확인한다. 기존 CI 취소/시간 제한 변경/재시도는 없었다.

기존 server3–5시간 예상은10월5일 로컬 수용 실적으로 대체한다.
다음 `crop-cycle-db-custody`는 metadata/HMAC/commit 전후 현재 권리와 immutable retry를 연결하는
3–5파일이며 준비/폐쇄 참조1시간+실제 SCRAM 게시/철회/재시작·정리1–2시간의
**2–3집중시간/10월5–7일 KST 잠정**이다. 하루4시간/CI·외부 자료 대기를 제외한다.
DB custody 뒤 저장 부모 → API/client → 같은 ID/UTC 성장3D → 작기 부하 → 생과/자원/Decimal 경제 순서다.

실제 cultivar/forcing/초기/관리 채택·국내 독립 측정·actual crop Run0개,
실제 runtime CLI/G0–G4·생산량/미래 마진/순위 게시 보류를 유지한다.
G4의 실제 UID/key custody·파일시스템/동시 운영 proof는 미수용이다.
알 수 없는/부분 proof와 untrusted file은 hold이며 이번 종료 시험의 네 게시 경계를 넘어서는
모든 OS/disk 실패의 자동 복구를 주장하지 않는다. DB/API/성장3D 연결은 후속이다.
