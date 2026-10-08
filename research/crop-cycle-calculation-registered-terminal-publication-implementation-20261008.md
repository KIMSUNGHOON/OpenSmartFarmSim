# 등록 계산 완료 결과의 별도 프로세스 DB 게시

2026-10-08 KST. [개발 계약](../contracts/crop-cycle-calculation-registered-terminal-publication-v1.md)의
**고유9개·원 명령 종료0·별도 최종 감사/정리로 작은 게시 연결을 로컬 수용**했다.
[불변 영수증](artifacts/crop-cycle-calculation-registered-terminal-publication-reference-20261008.json)의 SHA는
`c508d68e7431aaa28df3da9f50f6950cdfa737cf1953134fc632a2755fdb9910`다.
현재 native Codex CLI `gpt-6.1-sol / xhigh`에서 판단했고 재귀 CLI는0회다.

## 구현과 실제 연결

연구 harness의 게시 선언은 첫 계산 전에 원 supervisor spec SHA·고정 입력 계획의 걸음/출력/사건 수와
현재 source를 결속한다. 별도 무작위32byte DB key는 사설0400 파일에만 두며 서버 key와의 재사용을 거부한다.
선언/키의 형식·SHA·mode·현재 코드/source·원 config/DB 참조·원 마감을 서비스 구성 전에 확인한다.
설정 schema나 제품 API/worker lease를 변경하지 않았다.

새 Python 게시 프로세스는 실제 이전 명령/로그/종료/결과를 재확인한다. 마지막 원 감독 영수증의
종료0·recorded·completed·고정 전체 계획 일치가 필요하다. 기존 DB store의 현재 입력/등록 농장/계정 권리와
bytes/HMAC 검사를 거쳐 put/get하고, 마지막 선언/설정/마감을 검사한 뒤 사설 결과를 fsync한다.
게시와 재조회에서 RHS는 금지한다. 마지막 검사 실패 때 이미 저장된 비공개 row가 있어도 성공으로 표시하지 않는다.

실제 PostgreSQL16.15/SCRAM·같은 농장/입력의 작은 계산을40→120걸음으로 이어 완료했다.
두 fresh 계산 worker는 복원 RHS0·추가 RHS201/402회였다. 최종3출력/0사건의 전체 값·UTC는
fixture의 원 계산과 정확히 같았다. 다음6개의 게시 명령은 각각 fresh Python이다.

| 실제 게시 명령 | 원 종료 | 확인한 결과 |
| --- | ---: | --- |
| 계산 전 | 71 | 결과 파일·DB row 없음 |
| 40걸음 yielded | 71 | 결과 파일·DB row 없음 |
| 120걸음 완료 | 0 | 실제 같은 DB put/get·row1 |
| 완료 결과 재시도 | 0 | 같은 result ID/payload SHA/recorded_at·row1 |
| 입력 이용권 철회 | 71 | 게시·기존 결과 조회 거부·원 row 보존 |
| 계정 read 권한 철회 | 71 | 게시·기존 결과 조회 거부·원 row 보존 |

완료 게시/재조회와 재시도의 RHS는0이며 실제 암호 사용·`require_auth=scram-sha-256`을 확인했다.
두 성공 프로세스 FD는 각각4→4, parent는13→13이다. DB 수는 `[89,89,0,0,0]`→`[89,89,0,0,1]`이다.
선택 이력·현재 입력·원 설정/게시 선언/원 마감은 보존됐다. 게시+재조회19.365초, 재시도+재조회19.317초는
이 작은 내부 사례의 관측이며 전체 작기나 HTTP 성능 수용이 아니다.

## 검증·검토·정리

8개 형식/키/mode/source/마감 사례와 실제 SCRAM1개의 최종 고유9개를122.56초에 통과했다.
원 명령/정리123.575초·종료0이며 모듈 부재 RED의 원 종료1과 초기8개 통과도 보존했다.
초기8개를 최종9개에 더하지 않는다. 선행289개를 포함한294 source SHA는 모두 같았다.
표본 primary RSS124,702,720bytes·동시 descendant RSS 합223,293,440bytes다.
shared page 중복 가능 표본이며 WSL 전체/PSS 또는 production 성능 수용이 아니다.

별도 최종 감사는 여섯 게시 프로세스·두 계산 worker·primary/controller/PG의 실제 종료,
원 명령/로그/결과 SHA, DB schema/role/passfile0·네 host SCRAM·임시 경로 제거를 대사했다.
그 뒤 source freeze를 해제했다. 전체 Backend·웹/API/3D 시험은 이번에 반복하지 않았다.
검토는 닫힌 선언→현재 원 감독 증거→기존 store→최종 현재 검사 흐름, 비공개 키,
재시도의 원량/중복 방지와 실패 시 성공 미표시를 확인했다. 새 의존성·생장식·gate 변경은 없다.

## 다음 통합 실행과 남은 의존성

[전체166일 실행](../contracts/crop-cycle-calculation-full-registered-run-v1.md)은 아직 시작하지 않았다.
기존 임시 fixture는 teardown 시 DB·역할·자격증명을 지운다. 따라서 전체 계산/게시만 끝내고 지우면
후속 API/3D에 같은 DB를 쓸 수 없다. **같은 DB/farm/artifact를 유지하는 통합 실행 구성을 먼저 준비**한다.
작은 실제 계산→게시→현재 API/HTTPS→동일 UTC3D를 대사한 뒤 전체166일 실행을 시작한다.
전체 실행에서는 계산→전체 원 행/수지·명시+273일 이동 대사→DB 게시→API/3D→최종 정리 순서를 유지한다.
원9시간 상한에 준비/검증/게시/후속 연결/정리가 포함되며, 단계별 수용 범위는 각 실제 증거로 판단한다.
9시간이나 작은 시험 시간으로 전체 완료 날짜를 예측하지 않는다.

생과 수확·물/양분·구매 에너지·작물 Decimal 손익, 실제 제품 CLI/독립 G1과 G0–G4는 후속이다.
실제 품종 입력/국내 독립 자료/측정 농장 작물 Run0건·예측/미래 마진/추천 hold,
최신 native 화면 원 명령 종료 누락과 hosted Backend HBA hold를 유지한다.
