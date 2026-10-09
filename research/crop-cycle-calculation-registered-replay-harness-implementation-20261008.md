# 같은 등록 DB의 완료 계산→HTTPS→실제 App/3D

2026-10-08 KST. [같은 DB 검증 계약](../contracts/crop-cycle-calculation-registered-replay-harness-v1.md)의
**작은 기능 경로를 고유2개·원 명령 종료0·별도 최종 감사/정리로 로컬 수용**했다.
[불변 영수증](artifacts/crop-cycle-calculation-registered-replay-harness-reference-20261008.json)의 SHA는
`8c1796f99a7e9d596398f148c046f14c5d8387d764211c500f5d0438e43bf925`다.
현재 native Codex CLI `gpt-6.1-sol / xhigh`에서 판단했고 재귀 CLI는0회다.
**전체 실행의1GiB RSS 상한은 아래 실측으로 아직 보류**하며 전체166일은 시작하지 않았다.

## 같은 데이터와 실제 화면

소유한 관리 사건 프로그램을 실제 등록 농장/입력으로 고정하고 기존 감독자가 fresh Python에서 계산했다.
완료 결과는 별도 무작위 DB key와 원 감독/계획/마감 선언에 결속된 fresh 게시 프로세스로 저장했다.
같은 DB/schema·농장·result ID·payload·원 서버 artifact를 기존 결과 증명과 현재 query에 연결했다.
결과 증명 key는 서버/DB key와 다르며 계산 뒤 실제 TLS/시험 토큰을 발급했다.
보호 설정 loader가 구성한 기존 API와 현재 App/SDK/WebGL을 사용했다. 응답 routing/fixture 대체는0회다.

120걸음·원3시점/3사건 전체의 값·UTC를 대사했다. Chromium은 각 저장 시점의50개 탄소량 C/개수 N,
LAI 잎 면적·원 도형 높이/가시성·표·분포/시간 그래프와 같은 UTC를 확인했다.
관리 사건의 원 제거·전/후50개 C/N도 확인했다. 이는 명시적 제거이며 숙기나 생과 수확량이 아니다.

[실제 데스크톱](artifacts/registered-cycle-desktop.png)·[모바일](artifacts/registered-cycle-mobile.png)은
이 같은 DB/HTTPS 경로의 캡처다. 토큰 입력은 마스킹했고 화면의 수치 도형은 연구용 모식도다.
실제 식물의 키/과실 크기·외형 정확도를 입증하지 않는다. 모바일의 가로 넘침도 없었다.

## 현재 권리와 조회 경계

실제 HTTPS8개 응답은 `[200,200,200,200,422,200,200,403]`이다.
현재 입력 권리 철회 시422와 기존 장면 제거, 복원 뒤 원 저장 시점, 계정 read 권한 부재 시403과
장면 제거를 확인했다. SDK stream의 완료/취소와 실제 ASGI 전체 본문을 따로 관측했다.
현재 요청 최대 동시는 각각1, 전체 본문 최대2.147691초/35,816bytes이며 성공 응답은 no-store였다.
HTTP30초/2MiB를 유지했다. 이 작은 사례의 관측을 전체 작기 성능으로 외삽하지 않는다.

GET에서 parser/context/계산/RHS·artifact 원 QC·증명 발행·DB 게시를 금지했다.
원 입력/설정/artifact와 FD target/device/inode는 같았고 custody FD는0이었다.
DB 수는 `[89,89,0,0,0]`→`[89,89,0,0,1]`, 조회 이후에는 같은 row1을 유지했다.
실제 SCRAM 암호 사용과 보호 loader의 같은 jobs/store 연결을 확인했다.

## 검증·수정·정리

한 시험은 import 때 DB/프로세스/thread 시작을 금지한다. 다른 한 시험은 위 실제 관리 계산부터 화면까지다.
최종2개는85.35초, 원 명령/정리86.111초·종료0이다. 계산/게시/Node의 실제 종료도0이며,
선행294개를 포함한303 source SHA와 원 argv·로그·결과·worker identity를 보존했다.
별도 감사는 primary/controller/worker/PG/Vite/Chromium 종료, DB schema/role/passfile0·
네 host SCRAM·임시 경로 제거를 확인한 뒤 source freeze를 해제했다.
전체 Backend/웹 suite·새 hosted CI는 이번에 반복하지 않았다.

소비 모듈 부재 RED의 원 종료1을 보존했다. 첫 native는 조회 판본 전환 중 닫힌 폼에 입력해 실패했다.
계산/게시와 정리는 성공했지만 그 첫 브라우저 child의 종료 영수증이 없어 추정하지 않으며 수용하지 않는다.
두 번째는 수치/사건 장면 대사 뒤 CDP response.body가 SDK stream 응답을 관측하지 못해 실패했다.
원 pytest 종료1·parent가 정리한 Node 실제-9·원 로그/source snapshot/정리를 보존했다.
기존 native 경로의 실제 fetch reader 완료/취소 관측으로 수정한 세 번째가 위 최종 수용이다.
실패 실행은 완전히 종료·감사한 뒤 수정했으며 관측 만료 때문에 같은 계산을 재시작한 것은 아니다.
이전 부분 통과나 실패 시험을 최종 고유2개에 더하지 않는다.

브라우저 pageerror는0이다. SwiftShader ReadPixels GPU stall 경고4회와 예상422/403의 네트워크 콘솔
오류2회는 기록했다. 무경고 production 브라우저 검증으로 표시하지 않는다.

## 실측 자원 보류와 다음 단계

표본 primary RSS145,948,672bytes·동시 descendant RSS 합1,583,595,520bytes였다.
shared page 중복 가능 합이며 WSL 전체/PSS가 아니다. 그 합만으로도
[전체 실행의1GiB 상한](../contracts/crop-cycle-calculation-full-registered-run-v1.md)을 넘는다.
작은 기능 경로는 수용하지만 전체 통합 구성/자원 부모는 체크하지 않고 장시간 실행은 시작하지 않는다.

다음은 개발용 Vite 대신 고정 production 빌드의 같은 App을 서빙하는 시험 경로와 viewport 캡처를 검토하고,
같은 계산/DB/보호 HTTPS/원 수치·권리/정리를 유지한 실제 pipeline RSS를 PG와 함께 확인하는 단계다.
상한을 올리지 않는다. 원인과 개선량은 새 실측 전 확정하지 않는다.
자원 수용 뒤 전체166일의 원9시간 준비/spec·같은 DB/farm/artifact·streaming 전체 원 행/수지/명시+273일
대사·게시→API/대표3D→정리를 진행한다. 브라우저는 처음 두 범위와 최대8사건만 보관하고 전체 프레임 대사로
표시하지 않는다. 큰 결과의 직접 범위 이동은 실제 순차 탐색 제한을 근거로 후속 사용성 작업에 둔다.
9시간 상한이나 작은 시험으로 완료 날짜를 추정하지 않는다.

생과/자원/작물 Decimal 경제, 실제 제품 CLI/독립 G1과 G0–G4는 후속이다.
실제 품종 입력/국내 독립 자료/측정 농장 작물 Run0건·예측/미래 마진/추천 hold,
기존 최신 native 화면 원 명령 종료 누락과 hosted Backend HBA hold는 유지한다.
