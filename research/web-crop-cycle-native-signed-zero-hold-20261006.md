# 실제 긴 결과 화면 시험의 signed zero 기대값 실패

상태: **실제 연결 시험1실패·정리 확인·전체 수용 보류**, 2026-10-06 KST.
`348b162`의 두 native 시험 파일과 장면 정리는 현재 scope의 구현 후보다.
[불변 실패 receipt](artifacts/web-crop-cycle-native-signed-zero-hold-20261006.json)에
실제 CLI·source/로그 hash와 계산/정리 결과를 기록했다.

실제 새 PostgreSQL 16.15/SCRAM 계산은 원 입력 root/49개 코드 pin을 확인한 뒤
25시간·92회 advance·11,400걸음으로 완료됐다. 이어 표준 HTTPS/Bearer/실제 WebGL을
읽는 시험은 과거 보류 사례의 축 비교에서 실패했다. 시험 전체는 **1실패/1,666.57초**다.
원 27시점/5사건을 검증하는 흐름을 거쳤지만 최종 성공 receipt가 없어 전체 native 수용으로 표시하지 않는다.

실제 실패는 `{lower: -2, upper: -0}` 기대값과 canvas JSON의 `{lower: -2, upper: 0}` 차이다.
`Math.ceil`이 만드는 signed zero를 `JSON.stringify`는 숫자 `0`으로 표현한다.
독립 Node 재현에서 이 차이를 확인했고, 시험의 축 기대값만 정확히 `-0`일 때 `0`으로 정규화한다.
다른 축·원량/단위·C/N/LAI·페이지·HTTP 예산 검사는 유지한다. 제품 식·49개 pin·장면 코드 변경은 없다.
재시험은 기록된 실제 과거 보류 원값도 사용하는 화면 사전 검사 뒤 진행한다.

실패 실행에서도 시험 role/schema/비밀번호 파일은0, PG status3·private cluster/admin 비밀번호 파일 제거와
서버 정리를 확인했다. Linux `RUSAGE_CHILDREN`의 peak는 **533.13671875MiB**였다.
WSL 전체 메모리나 실제 GPU driver 메모리 수치가 아니다. 실패 diagnostic/screenshot은
첫 private runner가 임시 디렉터리와 함께 삭제했으므로 보존됐다고 보고하지 않는다.
원 로그·완료 progress·PG 정리 JSON은 별도 파일로 보존했다.
다음 runner는 실패 diagnostic도 임시 디렉터리 제거 전에 보존한다.

원 `d61bcb3` CI는 p0/p1/p3/p5 성공, p4 실행 중, p2의
[권한 기대값 불일치](market-candidate-read-authority-assertion-20261006.md) 실패다.
후속 수정의 hosted 성공은 아직 확인하지 않았다. 실행 중인 원 CI를 취소할 push는 기다린다.
남은 native 재검증은 이 실행의 약28분 실적을 기준으로 **추가 약30분**을 예상하며 실제 결과로 갱신한다.
replay/browser/result-pages 부모의 체크는 계속 열어 둔다. 실제166일 부하와 생산량·자원/경제는 후속이다.
실제 품종/작기 입력·국내 독립 검증 자료·crop Run은0건이며 G0–G4 `not_assessed`를 유지한다.
