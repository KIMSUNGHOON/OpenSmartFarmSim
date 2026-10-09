# 질량·배정 불변 저장과 현재 원 결과 아래 읽기의 개발 수용

2026-10-08 20:48 KST. 현재 native Codex CLI `gpt-6.1-sol / xhigh`에서 구현·검토했다.
재귀 CLI 실행은0회다. [공개 영수증](artifacts/crop-harvest-artifact-implementation-reference-20261008.json)에
원 명령/종료·411 source·코드/입출력·실제 저장 bytes·독립 Decimal·현재 권리/정리를 결속했다.
선행 [배정 수용](crop-harvest-events-implementation-20261008.md)의 원량과 합성 주장을 보존한다.

## 구현과 사용자 산출물

[저장 모듈](../backend/app/crop_harvest_replay.py)은 검증된 현재 crop query에서 원 질량·배정 행을 순회해
별도0400 SHA blob과 atomic HEAD를 만든다. 원 result/source·query identity·모델/질량·배정 판본,
두 입력 원문과 원 UTC/단위·미배정/관측 비교·hold를 보존한다. 기존 원 artifact/DB/수식은 수정하지 않는다.
한 page64행/2MiB·root2MiB·전체512MiB/65,536파일이며 원 행 전체를 모으지 않는다.

운영자 Python writer/reader는 정확한 현재 query만 받으며 게시 직전과 읽기 반환 전 원 결과·권리를 검사한다.
읽기는 선택 page/root/HEAD를 다시 해시하고 원 질량·배정 행을 재생성하지 않는다.
원 source와 같은 저장물의 재시도는 같은 hash이며 다른 계수/배정으로 기존 HEAD를 교체하지 않는다.
무결성 hash는 외부 진본 인증·서버 등록·관문 승인이 아니다. 서버 소유 expected hash 등록과
사용자 결과 선택·공개 API/SDK/3D는 다음 자식이다. 출력은 합성 산술·승인false를 유지한다.

사용자는 영수증의 실제 저장4파일(HEAD/root/page/lock)·원6행·행 순서 hash·계수/배정 원문을 확인할 수 있다.
검증 임시 DB/서버 경로는 정리했으므로 사용자 계정의 저장 이력을 생성하지 않는다.

## 통과한 검증과 범위

| 대상 | 확인한 범위 |
| --- | --- |
| 집중 시험 | [시험 파일](../backend/tests/test_crop_harvest_replay.py)의19개·원 종료0·5.22초. 중간17/19개는 중복 합산하지 않음 |
| 행/페이지 | 소유6행과132행·3page 사례의 원 행/전체/분할/경계 조회·원문·행 순서 hash 동일·재시도 동일·FD 정리 |
| 별도 Python | 두 소유 읽기 fixture에서 저장 행 재생성 함수들을 금지하고 전체 행 순서 hash 대사. 실제 DB 권한을 새 프로세스에 재구성한 검증은 아님 |
| 실제 중단 | 별도 child에서 HEAD 전/후 SIGKILL-9 각각1회·미게시/완전 HEAD 구분·lock 해제/재개 일치. 별도 예외 전/후2사례도 통과 |
| 거부 | HEAD/root/page·디렉터리·현재 source 변경/철회·잘못된 범위·공유 lock·symlink·단일 행2MiB 초과·다른 배정의 기존 HEAD 교체 거부 |
| hold 보존 | 추가 소유 fixture2사례: 확정 과거6행과 한 확정 표본/0구간. 둘 다 원hold/미승인 유지. 실제 DB의 hold 사례 검증은 후속 |
| 실제 DB | PostgreSQL16.15/TCP SCRAM·원3표본/4사건→6배정 행·실제 저장/전체/분할 조회·현재 권리/scope/계정·열린 reader 철회 거부 |
| 독립 대사 | 저장4파일의 원 bytes/이름 SHA·root/page/원문·행 순서와 네 양의 배정/미배정·관측 차이를 root에서 별도2200자리 Decimal로 대사 |
| 보존/정리 | 조회 RHS0·새 증명0·FD13→13·원 입력/custody SHA/mode/inode·DB 행 수·411 source 보존·DB schema/role/passfile0·소유 PG/controller/temp 정리 |

실제 DB 시험은20:44:33→20:46:08 KST, 원 종료0/pytest94.83초·준비부터 정리까지95.366초였다.
원600초 상한에서0.1초 간격897개 표본의 primary RSS 최대124,674,048bytes≤512MiB,
PG/controller 포함 소유 PID RSS 합 최대264,183,808bytes≤1GiB다.
공유 page 중복 가능 RSS 합이며 PSS/WSL 전체/production 부하의 증거는 아니다.
20:46:58 KST root 감사 뒤 시험 당시 세 파일을 보존하고 source freeze를 해제했다.

추가 hold probe의 첫 호출은 시험 fixture import용 PYTHONPATH 누락으로 종료1/실행0사례였다.
경로를 명시한 원 종료0의 두 사례만 수용했다. 실제 DB 시험/코드 수정·재실행은 없었다.

## 남은 외부 의존성과 다음 한 단계

[계약](../contracts/crop-harvest-replay-v1.md)의 `crop-harvest-artifact` 자식만 체크한다.
다음은 서버 소유 등록→현재 query의 작은 작업 분해와 구현이며, 원 부모/농장·질량/배정 hash/판본·
권리를 서버 등록에 결속하고 고객이 선택한 hash/경로를 등록 증명으로 받아들이지 않는 것이 수용 기준이다.
그 뒤 HTTP/SDK→같은 UTC 표/3D로 연결한다. 기후/물·양분/구매 에너지·경제 연결은 후속이다.

전체166일 질량/배정 저장 비용·새 공개 API/3D·fresh Python 실제 DB 권한 재구성·전체 Backend/web suite·
hosted CI·실제 품종 검증은 실행하지 않았다. 전체166일 RHS도 반복하지 않았다.
실제 계수/품종 입력·국내 독립 자료·실측 농장 작물 Run0건, G0–G4 `not_assessed`,
생산량·미래 마진/추천·원격 Backend/push·구형 native25시간 원 종료 기록 hold는 유지한다.
이 개발 자식은10월8일20:48 KST 수용이며 실제 자료 확보 일정이 없어 최종 production 완료일은 확정하지 않는다.
