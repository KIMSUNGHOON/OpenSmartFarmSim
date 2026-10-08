# 전체 등록 작기의 같은 DB 실행 구성 — 작은 수용, 2026-10-08

[계약](../contracts/crop-cycle-calculation-full166-same-db-preparation-v1.md)의 실행 구성을
[원 명령/최종 감사](artifacts/crop-cycle-calculation-full166-same-db-preparation-reference-20261008.json)로 로컬 수용했다.
현재 native Codex CLI `gpt-6.1-sol / xhigh`, 재귀 CLI 0회다.
새 [실행 구성](crop-cycle-registered-full-path.py)은 기존 계산·감독·게시·보호 조회/3D를 재사용한다.
선행 **392 source를 모두 유지**했고 새 고정 집합은397개다. 수식·격자·제품 경로·의존성은 바꾸지 않았다.

## 이번에 확인한 것

| 범위 | 실제 증거 |
| --- | --- |
| 경계 시험 | 고유12개 종료0 / 1.393316초: 새11개·선행 import1개 |
| 실제 같은 DB 경로 | 고유1개 통과, 시험94.41초·준비 시작부터 정리102.476019초·원 종료0 |
| 계산 | 실제 SCRAM·fresh Python, 120걸음·원3시점/3관리 사건·121상태 |
| 게시 전 대사 | 별도 Python 종료0 / 8.723235초, 원 행·UTC·checkpoint의 전체 비계보 의미/수지 일치·RHS0·FD 보존 |
| 별도 DB 게시 | 별도 Python 종료0 / 18.246924초, 새 결과 row0→1·조회/게시 RHS0 |
| 실제 3D | 같은 DB의 보호 HTTPS8개·현재 App/WebGL, 원3시점/3사건·LAI/C/N/UTC·표/그래프 대사 |
| 현재 거부 | 입력 권리 철회422→장면 제거→복원, 다른 계정403→장면 제거·unmount |
| 자원 | primary ≤512MiB, PG/controller 포함 동시 소유 RSS 합 **1,050,714,112bytes ≤1GiB** |
| 정리 | 계산/비교/게시/브라우저/Nginx/PG/controller 원 종료, schema/role/passfile/임시 tree 0, source397 보존 |

고유 pytest 수는 **13개**다. 앞선 실패·core10개 중간 통과를 중복 합산하지 않는다.
RSS는0.1초 간격의 고유 PID별 동시 RSS 합이며 공유 페이지 중복 가능·PSS/WSL 전체/미관측 순간 최대가 아니다.
앞서 수용한 실제 빌드161파일·native Nginx·1024×768/390×844 viewport·Node heap64/2MiB·
nozygote·명시 CDP GC2회 설정을 유지했다. 일반 운영 브라우저나 전체 작기의 자원 수용은 별도다.

[실제 데스크톱](artifacts/registered-full-path-small-desktop.png) ·
[실제 모바일](artifacts/registered-full-path-small-mobile.png).
동일한 합성 원 계산값의 LAI·과실 구획 모식도여서 선행 작은 자원 검증 화면과 PNG hash가 같다.
실제 토마토 형상·생과 수확량을 표시한 화면으로 취급하지 않는다.

## 준비 마감과 bounded 대사

실제 준비 초기화 명령이 PG/등록 전에600초의 원 시작·단조 시계·boot ID·마감·source/도구·저장 여유를 불변 기록했다.
등록/키/runtime/farm/원 참조는 계산 전에 별도 실행 기록으로 결속했다.
기존 감독의 내부 마감은 원 준비 마감보다 이르게 제한하며 단계마다 같은 준비 기록을 검사한다.
새 단계에서 예산을 다시600초로 시작하지 않았다.

행은 samples64/events8 이하의 페이지로 대사하며 전체 행을 list에 누적하지 않는다.
first64 samples/최대8 events만 API/대표 브라우저용으로 보존하고 브라우저에는 첫14시점만 전달한다.
전체 대사 자식이 종료한 뒤 브라우저를 시작하므로 큰 원 참조 문맥은 브라우저와 함께 유지하지 않는다.
늦은 값 변조·누락/중복/잘못된 start/next/total·121번째 상태/clock/누적 수지 차이·
현재 source 변경·마감 만료·실제 자식 종료7 거부를 집중 시험했다.

실제 **기존166일 원 참조 branch**도 별도 Python에서 열었다.
원 첫64/마지막1시점·전체5사건, terminal121상태/1,816,704걸음·+273일 뒤 마지막 UTC
`2027-03-16T00:00:00Z`, 기존 사건 전체 hash·RHS0·문맥/캐시 정리를 확인했다.
이 관측까지 같은 준비 시작부터181.233564초였다. 앞선 native와 명령 사이 시간도 포함하므로
이 숫자를 원 참조 읽기 자체의 소요 시간으로 해석하지 않는다.
이는 새166일 등록 계산이나 새47,809행 전체 대사의 완료가 아니다.

## 실패 보존과 검토

첫 RED는 실행 구성 파일 부재로 원 종료1이었다. 첫 native는 원량 대사 자식0 뒤 게시 자식71,
원 시험 종료1이었다. 기본 DB fixture가 계산 결과용 schema/권한 flag를 설치하지 않은 원인이었다.
기존 전용 fixture와 결과 row 계수를 가져오도록 수정했고 실제 게시/3D까지 통과했다.
첫 실패의 source397 snapshot·원 로그/종료·PG/schema/role/passfile/임시 정리를 보존했다.
제품 schema·권한 검사나 게시 거부를 완화하지 않았다.

검토에서는 새 동작을 소유 실행 구성/수용 시험으로 한정하고, 기존392 source·현재 권리·조회 RHS0·
bounded 메모리·원 마감과 실제 자식 종료 보존을 확인했다. 전체 Backend/웹 시험과 CI는 반복하지 않았다.

## 다음 실제 실행

다음은 별도의 **전체166일 등록 실행**이다. 원 준비부터32,400초,8초 RK4/300초 출력,
primary512MiB/pipeline1GiB와 두 저장 공간2GiB를 유지한다.
완료된 새47,809행/5사건·121상태/수지를 원 참조와 전부 대사한 뒤 같은 DB 게시/API/대표3D까지 검증한다.
전체 실행의 실제 종료·자료/원량·자원 정리 전에는 부모 작업을 체크하지 않는다.

생과 수확량·물/양분·구매 에너지·Decimal 작물 손익 연결은 후속이다.
실제 품종 입력0·국내 독립 검증 자료0·실측 작물 Run0, G0–G4 `not_assessed`, 예측·추천 hold를 유지한다.
실제 제품 CLI/독립 G1·hosted Backend HBA 증거·push도 보류 상태다. 완료 날짜는 작은 측정에서 외삽하지 않는다.
