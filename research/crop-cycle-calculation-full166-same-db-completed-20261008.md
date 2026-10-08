# 합성 166일의 계산·같은 DB·보호 API·대표 3D 완료

2026-10-08 KST. 현재 native Codex CLI `gpt-6.1-sol / xhigh`에서 검토했다. 재귀 CLI 실행은0회다.
[원 시작 기록](crop-cycle-calculation-full166-same-db-started-20261008.md)의 같은 실행을 관측했고,
재시작·마감 초기화 없이 종료했다. [공개 영수증](artifacts/crop-cycle-calculation-full166-same-db-completed-reference-20261008.json)에
원 명령·로그/감사 hash·398개 source·결과 비교·API/브라우저·정리 증거를 결속했다.

## 실제 종료와 수용 범위

원 도구 세션15007의 실제 종료 코드는0이다. pytest는 **1 passed in 26102.92s**이며,
준비부터 정리까지26,127.555초(7시간15분27.555초)였다. 시작은10월8일11:41:29 KST,
종료는같은 날18:56:57 KST다. 원9시간/20:41:29 KST 상한을 유지했다.
최종 root 감사는19:04 KST에 통과한 뒤 source freeze를 해제했다.

| 확인 대상 | 실제 증거 |
| --- | --- |
| 소유 합성 달력 | 2026-10-01→2027-03-16, 원 참조에 명시적으로+273일. 미래 날씨나 실제 농장 입력이 아님 |
| 실제 계산 | fresh Python/nice19·1,816,704걸음·456commit·47,809표본/5사건·완료·원 worker 종료0 |
| 별도 전체 비교 | fresh 자식 종료0/2,420.258초·samples64/events8 이하·748/1page·전체 원 행/UTC hash 일치 |
| 전체 checkpoint | 계보6필드만 제외한121상태·clock/counter/누적 수지 의미 일치·조회 RHS0·FD4→4 |
| 같은 DB 게시 | 비교 뒤 fresh 게시 종료0/38.397초·현재 SCRAM/권리·작물 결과 row0→1·재조회 RHS0 |
| 실제 보호 웹 | 같은 DB/farm/artifact의 실제 빌드/Nginx/HTTPS/App/Chromium WebGL·원 UTC/수치 일치 |
| 대표 범위 | 첫 두7표본 창의14시점과 전체5사건. 전체47,809프레임 검사는 아님 |
| 거부/복원 | 현재 권리 철회422→복원, 실제 계정 권한403·동시 읽기 최대1·장면 unmount |
| HTTP | 10응답 전체 완료·최대8.329273초/67,188bytes·기존30초/2MiB 이하·정상 응답 no-store |
| 원본 보존/정리 | 398 source·입력/config/artifact 보존·FD/context/cache 정리·DB schema/role/passfile0·PG/API/Nginx/Node/Chromium/controller/임시 경로 종료 |

최종 artifact root는`f1bf669180fa3b07f39c4b582fedc5c7edcf28b5e35497cde9947dcdd5eb6a8c`,
HEAD hash는`dbdac5625094bd1f5372831b0aef38054a81a586095698273986e8082ca17ab3`다.
두 hash는 서로 다른 객체다. 지속 artifact919파일/404,673,556bytes와 증명458파일/571,038bytes를 보존했다.
root 감사에서 artifact 내용 hash·HEAD/root/최종 checkpoint와458개 증명의 HEAD 이름/부모 hash 연결,
입력750파일을 다시 확인했다. HMAC은 실제 실행에서 비밀 정리 전에 검증했으며 root 목록 검사에서 재발행하지 않았다.

## 사용자가 확인할 화면

[데스크톱1024×768](artifacts/registered-full166-desktop.png)과
[모바일390×844](artifacts/registered-full166-mobile.png)는 이번 실제 App의 원 캡처다. root가 두 화면을 직접 확인했다.
현재 화면은 LAI와 과실50구획의 C/N 상당량을 표시하는 **저장 수치 모식도**다.
실제 줄기 높이·잎 수·열매 크기·숙기·생과 수확량을 검증한 식물 형상이 아니다.
임시 검증 DB/서버는 종료 후 정리했으므로 이 시험이 사용자 계정의 저장 이력을 생성하지는 않는다.

## 자원과 감사 한계

0.1초 간격 감시의233,854개 표본에서 primary 최대164,487,168bytes≤512MiB,
PG/controller를 포함한 소유 고유 PID RSS 합 최대1,070,809,088bytes≤1GiB였다.
한도 여유는**2,932,736bytes(약2.8MiB)**뿐이다. 공유 page 중복 가능 RSS 합이며 PSS/WSL 전체가 아니다.
지정 viewport·Node heap64/2MiB·SwiftShader·명시 CDP GC2회의 시험 수용이다.
표본 사이 최대치나 일반 사용자 브라우저/production 동시 실행 성능을 증명하지 않는다.

원 수식·8초RK4/300초 출력·권리/bytes·메모리·원9시간 한도를 바꾸지 않았다.
감사 v1은 증명 파일 이름을 내용 hash로, v2는 입력`root.json`을 hash 이름으로 잘못 가정해 각각 종료1이었다.
원 저장 계약을 확인해 별도 v3에서 수정했고 실제 종료0을 보존했다. 원 계산을 반복하거나 자료를 고치지 않았다.
처음 두 감사 소스·실제 실패 영수증과 최종 감사 hash도 공개 영수증에 연결했다.

전체 Backend/web suite·hosted CI 재실행·전체47,809 WebGL frame·실제 품종 형상 검증은 수행하지 않았다.
마지막 확인 원격`2a3e615`의 Backend HBA 실패/push hold와 구형 native25시간 원 종료 유실 hold는 별도다.
이번 종료0을 구형 명령의 종료 코드로 소급하지 않는다.

## 다음 단계와 외부 의존성

이번 수용은 합성 연구 계산/저장/대표 재생 범위다. 실제 품종 입력·국내 독립 자료·실측 농장 작물 Run은0건,
G0–G4는`not_assessed`다. 실제 제품 CLI·독립 전체 G1·생과/자원/경제 연결과 예측·추천은 아직 미수용이다.
전체 목표는 계속 활성 상태다.

다음 작은 구현은 [제거 원장 계약](../contracts/crop-harvest-v1.md#첫-구현-한-단계의-수용-기준)의
`crop-removal-ledger`다. terminal 누적 차이와 관리 사건의 과실 C/N을 분리하고 원 result/UTC/위치에 결속한다.
잎·줄기 제거를 과실에 더하지 않는 독립 대조와 경계/중복·혼합 거부, 작은 실제 저장 조회·권리/RHS0/정리가 다음 수용 근거다.
그 뒤 명시 계수 환산→수확 의미→기후/물·양분/구매 에너지→사용자 실행·경제 연결 순서로 진행한다.

완료일을 확인한 범위는 위166일 연구 경로다. 다음 원장의 착수 조건은 충족했으며
실제 생과·경제·최종 제품 완료일은 DMC/수확/면적·밀도/계약·정산과 독립 국내 자료 확보 상태를 반영해 갱신한다.
[DMC 후속 조사](crop-harvest-reference303-dmc-followup-20261008.md)와
[국내 부록 구조 확인](crop-domestic-supplement-schema-20261008.md)은 해당 자료 공백을 해소하지 못했다.
