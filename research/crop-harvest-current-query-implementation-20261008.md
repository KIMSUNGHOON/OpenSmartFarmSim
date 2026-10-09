# 등록 수확 산술의 현재 조회·별도 실제 DB 복원 개발 수용

2026-10-08 22:04 KST. 현재 native Codex CLI `gpt-6.1-sol / xhigh`에서 구현·검토했다.
재귀 CLI 실행은0회다. [공개 영수증](artifacts/crop-harvest-current-query-implementation-reference-20261008.json)에
원 명령/종료·426 source·실제 SCRAM reader·서명/파일·fresh Python·권리·정리를 결속했다.
선행 [서버 등록](crop-harvest-registration-implementation-20261008.md)과
[합성166일 DB/API/대표3D](crop-cycle-calculation-full166-same-db-completed-20261008.md)는 보존한다.

## 구현과 사용자 산출물

[현재 조회 제공자](../backend/app/crop_harvest_current_query.py)는 정확한 등록부와 별도 reader 로그인만 받는다.
현재 읽기 scope/계정 아래 등록 ID와 농장 참조로 signed metadata를 읽고 서버의 key/hash로 artifact를 연다.
DB/역할·HMAC·닫힌 metadata/열·원 부모/농장/source·두 계수 원문 hash·판본·HEAD/root/page를 검사한다.
summary/제한 page·최초 DB 시각·원 단위/UTC·합성 가정·미배정·hold·승인false를 보존한다.
조회 context 종료 때 같은 record/현재 표시 권리와 선택 page를 재검사한다.
계산 권리나 쓰기 scope가 없는 현재 표시 권리 소유자도 기존 등록 결과를 읽을 수 있다.

별도 Python exec는 [기존 보호 런타임 조립](crop-cycle-registered-runtime.py)을 재사용해 같은 실제 DB의
원 farm/input/server·result evidence·등록 reader를 새 객체로 구성한다. owned 권리 provider의 판본과
시험 factory 소스 hash, 고정 key/DSN/proof 파일 hash를 private bundle에 고정했다.
권리·principal은 현재 보호 파일에서 다시 읽는다. fork된 메모리나 소유 페이지 callback으로 대체하지 않았다.
이 factory/provider와 상수 key는 합성 시험용이며 제품 운영 설정·실제 CLI 작업자는 아니다.

사용자 산출물은 같은 저장6행의 summary/전체·분할 조회와 별도 프로세스 복원/거부 보고서다.
아직 HTTP/SDK/새 화면에는 연결하지 않았다. 임시 시험 DB를 정리했으므로 사용자 데모 이력은 생성하지 않는다.

## 통과한 검증

| 대상 | 실제 확인 범위 |
| --- | --- |
| 집중 시험 | [시험 파일](../backend/tests/test_crop_harvest_current_query.py) 전체24개·원 종료0·323.53초. 순수23개/실제 SCRAM1개이며 선행 순수 실행을 중복 합산하지 않음 |
| 순수 검사 | 잘못된 타입/ID/농장·bool/범위·명시 설정·코드/정책 변경·전체 응답2MiB 거부 |
| 실제 reader | 별도 SCRAM reader·원 등록1건/최초 시각·6행/4파일·summary/전체/3+3행 페이지 동일·없는 등록None |
| 권리 | 쓰기 scope 제거와 계산 권리false/표시true에서 조회 성공. 현재 읽기 scope·계정·표시 권리·다른 농장·범위 거부 |
| 서명/파일 | 서명 오류 주입·실제 HEAD/root/page bytes 변조 거부, 원 bytes/mode/inode 복원. 새 판본 채택 아님 |
| 종료 시 검사 | 표시 권리 철회·등록 row 소실 오류 주입·실제 선택 page 변조 뒤 context 종료 거부. row 소실은 불변 DB 수정이 아닌 조회 오류 주입 |
| fresh Python | 같은 실제 DB 정상 전체/분할 조회와 표시 권리 철회 거부의 자식2개, 각각 실제 종료0·73.924/1.628초·FD4→4 |
| 재계산 금지 | parser/context/QC/RHS·수확 행 생성·등록·새 proof 함수를 금지한 조회, RHS/행 재생성/등록/새 proof0 |
| 독립 감사 | metadata/key/HMAC/원 source·두 원문·파일 bytes/SHA·6행 순서·fresh 결과/summary hash·원 명령/마감·426 source 대사 |
| 보존/정리 | 원 parent query/DB 수·input/custody/harvest SHA/mode/inode 보존·FD13→13·보호 파일19개 명시 제거·새/기존 schema/role/passfile0·PG/child/temp 종료 |

실제 시험은21:59:18→22:04:42 KST, 준비부터 정리까지324.090초였다.
600초 원 상한·0.1초 감시3048개 표본에서 primary RSS 최대133,095,424bytes≤512MiB,
PG/controller 포함 소유 PID RSS 합 최대375,414,784bytes≤1GiB였다.
공유 page 중복 가능 RSS 합이며 PSS/WSL 전체/production 동시 부하 수용은 아니다.
22:04:56 KST root 감사 뒤 시험 당시3파일 snapshot을 보존하고 source freeze를 해제했다.

작은 사례의 summary는13.808초, 전체/분할 page는22.950/23.019/23.011초였다.
전체 내부 응답의 정규화 JSON은70,444bytes였다.
이는 내부 현재 query 측정이며 HTTPS30초 수용은 아니다. 후속 투영·route/runtime에서 같은 권리 검사를
유지한 실제 지연/응답 크기를 다시 확인한다. 전체166일 질량/배정 조회 부하는 아직 측정하지 않았다.

## 다음 한 단계와 외부 의존성

[조회 계약](../contracts/crop-harvest-registered-query-v1.md)의 자식과 세 자식을 충족한 작은
`crop-harvest-current-query` 부모만 추가 체크한다. `crop-harvest-replay` 부모는 HTTP/SDK·같은 UTC3D가 남아 있다.

다음 `crop-harvest-http-sdk`는 먼저 공개 투영 계약/module/집중 시험3 core파일로 나눈다.
수용은 원 ID/부모·UTC/단위·계수/배정 판본·정확 수량/미배정/hold·승인false의 닫힌 DTO,
unknown/mixed/비정상 수량 거부·summary/선택 page 전체2MiB·원 저장6행/분할 동일·투영 중 재계산0이다.
HMAC·비밀·private 경로·권리 원문은 공개 DTO에 넣지 않는다. 그 뒤 명시 runtime/인증 route·실제 TLS→SDK→
같은 UTC 표/3D→기후/물·양분/구매 에너지·기존 Decimal 경제 연결을 진행한다.

현재 query의 수용 시각은 위 실측으로 확정했다. 후속 투영·runtime/TLS·SDK·3D를 각각 검증한 뒤
실제 완료 시각과 남은 작업 추정을 갱신한다. 독립 자료 확보 일정이 없어 최종 production 완료일은 확정하지 않는다.
전체166일 새 질량/배정 조회·새 HTTP/SDK/3D·전체 Backend/web suite·hosted CI·실제 제품 CLI/품종 검증은 실행하지 않았다.
실제 계수/품종 입력·국내 독립 자료·실측 농장 작물 Run0건, G0–G4 `not_assessed`,
생산/미래 마진/추천·원격 Backend/push·구형 native25시간 원 종료 기록 보류는 유지한다.
