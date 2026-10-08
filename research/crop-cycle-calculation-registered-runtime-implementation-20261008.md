# 같은 등록 농장의 fresh Python 복원 수용

2026-10-08 KST. [작은 등록 런타임 계약](../contracts/crop-cycle-calculation-registered-runtime-v1.md)을
**고유7개·원 명령 종료0·정리/최종 감사로 로컬 수용**했다.
[불변 영수증](artifacts/crop-cycle-calculation-registered-runtime-reference-20261008.json)의 SHA는
`6a492b14f4841211705433e9aaeeedb514bf9e7b3e464c4152b8c0cfc6fd6ece`다.
현재 native Codex CLI `gpt-6.1-sol / xhigh`에서 판단했으며 재귀 CLI는0회다.

## 구현과 실제 복원

새 연구 harness는 소유 합성 시험의 DB 역할·농장/연구/시장 참조·입력 proof·서버v3를
사설 설정과 명시 SHA에서 다시 구성한다. 기존 intent를 다른 권리 정책으로 변환하지 않으며
새 설정은 첫 계산 전에 발급한다. 고정 파일의 SHA와0400/0700·소유/ACL·닫힌 형식을 검사한다.
DB 비밀·key·raw proof는 사설 파일만 사용하고 원 argv/로그는 비공개 영수증으로 보존했다.
현재 principal/입력 허용은 매번 소유 시험 파일에서 읽는다. 제품 계정 서비스나 현장 권리 서비스가 아니다.
닫힌 입력 context는 마지막 하나만 보관하고 다음 열기 전 FD/cache 정리를 확인한다.

| 항목 | 첫 계산 | 별도 Python 재개 뒤 |
| --- | ---: | ---: |
| 적분 걸음 / 전체 계획 | 40 / 120 | 80 / 120 |
| 출력 / 관리 사건 | 1 / 0 | 2 / 0 |
| 확정 commit / 상태 | 1 / yielded | 2 / yielded |

서로 다른 실제 Python 자식4개의 argv·PID/start tick·로그 SHA·원 종료를 기록했다.
첫 자식은 같은 DB/농장과 첫 checkpoint 전체를 RHS0/delta QC0으로 복원해 fsync한 뒤 SIGSTOP했다.
그 지점에 SIGKILL을 보내 실제 종료 **-9**, 선택 HEAD/서명 이력 보존을 확인했다.
두 번째 자식이 같은 checkpoint를 다시 RHS0으로 복원하고 실제201 RHS 호출로80걸음까지 계산해 종료0이었다.
전체 checkpoint와 두 출력의 값/UTC/순서가 같은 예산으로 연속 실행한 별도 제어 artifact와 정확히 같다.

이는 **복원 직후·새 계산 전**의 강제 종료다. 계산 도중 crash·전체 작기·관리 사건 사례의 추가 수용으로 넓히지 않는다.
나머지 두 자식은 현재 입력 허용/`crop_result_read` 철회를 각각 hold/PermissionError·종료71로 거부했다.
고정 server key의 변조도 서비스 구성 전에 거부했다. 원 input·선택 HEAD·config를 보존했고
yielded 결과의 DB 완료 게시를 거부해 DB 수는 `[89,89,0,0,0]`으로 같으며 새 작물 Run/게시 row는0이다.

## 검증·실패 수정·정리

최종7개는 정상 설정 대조가 포함된 SHA/판본/필드/mode/고정 파일6개와 실제 SCRAM 등록1개다.
79.77초·원 명령/정리80.481초, primary 표본 RSS126,914,560bytes·동시 descendant RSS 합225,763,328bytes다.
표본 RSS 합은 shared page를 중복 셀 수 있으며 WSL 전체/PSS·production 성능 수용이 아니다.
nice19·소유 PG/계산 하나씩, FD13→13·마지막 context 닫힘·schema/role/passfile0을 확인했다.
네 host 규칙 모두SCRAM·실제 비밀번호 연결을 검증했다.
실제 child/primary/controller/PG 종료와 PG/임시/비밀 경로 제거, 선행279개를 포함한284 source 보존을
별도 최종 감사에서 확인한 뒤 source freeze를 해제했다.

최초 RED는 연구 모듈 부재였다. 초기 설정 시험에는 잘못된 cwd와0400 시험 파일 재작성의 준비 오류가 있었고 수정했다.
정상 설정 대조를 강화한 native v1은0600 전용 운영 설정 reader로0400 불변 파일을 읽으려 해 실제 종료1이었다.
DB는 시작하지 않았고 종료/정리·실패 source/로그를 보존한 뒤 기존 custody의 불변 reader로 수정했다.
수정 v2가 위7개를 통과했다. 실패나 초기5개 GREEN을 최종 고유7개에 더하지 않으며 관측 만료 재시작은0회다.

## 다음 단계와 hold

[전체 지속 실행 계약](../contracts/crop-cycle-calculation-full-registered-run-v1.md)의 작은 runtime 자식만 수용했다.
다음은 동일 config/입력/DB 참조를 고정하는 지속 spec·원 시작/deadline·배타 실행·실제 종료/로그·
취소/벽시계/RSS 감독의 구현과 반례 검증이다. 그 부모가 통과하기 전9시간 전체 등록 실험은 시작하지 않는다.
기존 HTTP30초/제품 worker lease는 그대로이며 이 harness는 제품 CLI 작업자가 아니다.

전체 Backend·새 전체166일 등록 계산/DB/API/TLS/WebGL·실제 제품 CLI/독립 G1은 실행하지 않았다.
최신 native 화면 원 명령 종료 누락과 hosted Backend HBA hold는 별도다.
생과/물·양분/구매 에너지·작물 Decimal 손익, 실제 품종/국내 독립 자료/측정 농장 작물 Run0건,
G0–G4 `not_assessed`, 생산 예측·미래 마진·추천 hold를 유지한다.
