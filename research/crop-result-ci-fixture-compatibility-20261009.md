# 작물 저장·조회 CI fixture 호환 수정

2026-10-09 KST. [8dd386d의 실제 CI 실패](crop-result-ci-terminal-20261009.md) 중
게시 선언의 역사적 source 의존과 세 수확 시험의 fresh Python import 경로를 수정했다.
[5파일 계약](../contracts/crop-result-ci-fixture-compatibility-v1.md)과
[원 종료·로그/hash·source·정리 영수증](artifacts/crop-result-ci-fixture-compatibility-reference-20261009.json)에 근거해
**이 두 fixture 작업만 로컬 수용**한다. native Codex CLI `gpt-6.1-sol / xhigh`의 실제
turn/output 기록을 보존했고 재귀 CLI는0회다.

## 원 실패와 수정

`PYTHONPATH`를 제거한 별도 실행 원89537은 종료1로 선언8개 setup 오류와 TLS import1개 실패를 재현했다.
세 원 자식 import 문장을 별도 Python에서 실행한 추가 대조도 각각 종료1·정확한 모듈 부재를 확인했다.

선언의 합성 단위 fixture는 소유 source map을 명시한다. 원8개의 선언/거부 검사는 유지한다.
별도2개 검사에서는 실제 `publisher.sources()`에 소유 파일/참조를 주어 정상 hash를 확인한 뒤,
파일 bytes 또는 참조 hash가 달라지면 거부하고 참조를 다시 쓰지 않는 것을 검증했다.
제품 publisher/supervisor·과거 영수증·frozen producer는 수정하지 않았다.

current query, runtime factory, TLS fixture import의 별도 자식 환경에는 backend와 tests의 절대
`PYTHONPATH`를 명시한다. 상속 환경과 기존 권리/계정·FD·원량/UTC·조회 재계산0 단언을 보존한다.
기본 venv·의존성 lock·CI workflow와 제품 API/UI 코드는 변경하지 않았다.

## 실제 통과 범위

| 검사 | 실제 원 종료와 범위 |
| --- | --- |
| WSL Python3.12.3 집중 | 원30681 종료0,11개 통과. 선언8개+원 hash 거부2개+무연결 import1개 |
| CI와 같은 Python3.12.13 집중 | 원16391 종료0, 같은11개 통과. TLS import FD5→5·접속0 |
| 실제 current query | 원83707의 첫 자식 종료0/385.876초. 같은 소유 SCRAM DB의 원6행·분할 동일성·fresh 정상/권리 철회 두 자식0 |
| 실제 runtime factory | 원83707의 둘째 자식 종료0/16.978초. 별도 소유 SCRAM DB의 fresh 정상2회/보호 설정 거부1회·자식3개0 |

고유 pytest 조건은13개다. Python 두 환경에서 반복한11개를 서로 다른22개로 세지 않는다.
runtime factory 대조는 빈 결과의 같은 부모/계정/reader 연결과 거부 검사이며 원6행 대사는 current query의 범위다.
새 실제 HTTP/TLS·브라우저 검사는0회다.

current query의 부모 FD13→13, fresh 두 자식4→4, RHS/수확 생성/새 증명/등록 호출0을 확인했다.
runtime factory의 부모 FD12→12, fresh 세 자식4→4, 원 DB 개수 보존·새 작물/수확 행0과 보호 파일 보존을 확인했다.
세 정리 영수증의 schema/role/passfile은 각각0이다.

실제 DB 실행의 원83707은 **전체 종료0/443.008초**, 원600초 상한 안에 끝났다.
소유 PG16.15 두 개 모두 정지·남은 pidfile0·소유 비좀비0이며, 추가 강제 PG 정리는 없었다.
전체 계산/미리보기의 보호4 identity·기존 dist와1,558 source를 보존했다.
표본 단일 RSS128,991,232bytes·동시 합852,099,072bytes로512MiB/1GiB 안이다.
이 합은 실행기/소유 자식·두 시험 PG와 보호된 전체 계산/미리보기의 RSS이며 WSL 전체 메모리 측정은 아니다.

CI Python 첫 private 실행 원38631은 증거 디렉터리를 만들지 않아 기록 단계에서 실패했다.
제품 import/FD 검사는 이미 통과했으며 이 실패를 제품 FD 오류로 해석하지 않는다.
원 실패를 보존하고 새 private 디렉터리에서 원16391 종료0을 확인했다. 제품 코드 추가 수정은 없었다.

## 남은 의존성

분할5 `DROP OWNED` 교착, 분할1/5 잔여 감사의 원인은 별도 조사/회귀가 남았다.
이번 두 소유 PG의 정리 통과를 그 hosted 실패의 해결로 표시하지 않는다.
수정 후 hosted PostgreSQL18·전체 Backend/독립 Linux UID 수용과 push는 아직 없다.

진행 중 전체166일 복구의 대사/게시/인증 보존·fresh 복원과 UI 목록/브라우저·실시간 U3도 미완료다.
현재 사용자 UI는 별도 DB의 작은 합성3시점만 읽는다.
실제 품종/농장 작물 Run과 독립 자료0건, G0–G4 미평가·생산/마진 예측·추천 hold는 유지한다.
