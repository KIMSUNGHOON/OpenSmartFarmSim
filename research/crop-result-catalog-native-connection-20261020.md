# 저장 결과 목록의 실제 연결 진행 — 2026-10-20

[기계 증거](artifacts/crop-result-catalog-native-connection-20261020.json) ·
[이전 준비](crop-result-catalog-native-readiness-20261020.md) ·
[TLS 수명 수정](legacy-preview-TLS-lifetime-repair-20261020.md).

## 수용 범위

**저장 판본의 목록 API와 현재 화면 개발 빌드를 확인했다. 목록→3D 브라우저/U1은 미수용이다.**
현재 backend에서 과거 결과를 읽는 지원과 기존 판본의 검증을 구분한다.

과거 작은21건 seed는 수확 reader3파일의 판본이 달라 현재 checker가 거부했다.
전체166일 manifest도 원 절대 dependency namespace를 현재 checker에 바로 넘길 수 없었다.
기존 exact-source validator로 원 manifest를 확인한 뒤 reader 파일의 같은 bytes를 대사했다.
원 manifest·서명/코드 판본을 새 값으로 바꾸지 않았다.

현재 backend의 실제 farm/등록 작물3응답은200이었다. 결과 목록은422였다.
진단은 `_row`→`_decode`의 CODE 검사로 거부됨을 확인했다. 저장된 `runtime_roles` SHA는
be1dc602…이고 현재 것은12a47d70…다. 이 차이를 허용하도록 검사를 풀지 않았다.
현재 frontend와 연결할 때는 저장 당시 코드가 고정된 기존 읽기 서버임을 명시하며,
그 성공을 최신 backend의 구판 읽기 지원으로 합산하지 않는다.

## 실제 API와 빌드

기존 배포 판본의 별도 복원 SCRAM DB/HTTPS에서 **10응답**을 대사했다.
farm 목록→등록→작물→생장1건/47,809시점·5사건→수확1건/47,813행과 원 ID/부모를 확인했다.
부족한 scope403·다른 계정422·투영 뒤 display 철회422/보류·복원200을 확인했다.
metadata 조회의 수치/값 읽기·게시·증명0, 원 record와 DB counts 불변·DB 종료를 확인했다.
guard28.469569초·단일137,560,064/합671,309,824bytes다. 합성 fixture이며 실제 농장 생산량이 아니다.

현재 frontend 개발 빌드는 원 소스/lock을 고정하고 unminified/CSS unminified로 만들었다.
첫 전체 설정 로딩은 파일 생성 뒤 단일 RSS543,940,608bytes로 중단돼 수용하지 않았다.
프로덕션에서 비활성인 serve/test/demo 설정 import를 제외한 사설 build 설정과128MiB heap/
한 CPU로 같은 제품 소스를 빌드했다. 종료0/guard1.897005초·단일483,971,072/
합901,263,360bytes였다. 정상 minified production build·전체 웹 회귀의 새 수용은 아니다.

## 브라우저 진단과 실제 장애

첫 두 브라우저 시도는48–50초 뒤 RSS로 중단됐다. 두 번째 제한 journal은
`farm_list_started`까지이고 요청/장면 대사 증거가 없었다. 별도 짧은 실제 DOM 검사는
초기 버튼 활성/계정 연결을 확인했다. 후속 응답 관측이 **502/HTML과 expired TLS 오류10**을
확인해 보호 조회가 실패한 이유를 밝혔다. 메모리 중단만으로 제품의3D 비용을 추정하지 않는다.
이 인증서는 [실제 유지보수로 복구](legacy-preview-TLS-lifetime-repair-20261020.md)했고
원 생장/수확8·환기8응답을 새 TLS로 대사했다.

TLS 복구 뒤 같은 현재 화면·저장 판본 서버의 전체 브라우저 시도는 **3.209003초**에
전체 RSS1,083,510,784bytes로 원1GiB 한도를 넘었다. 단일 최고270,643,200bytes였고
`browser_started` 뒤 app-loaded/요청/장면 증거는 없다. 이 결과는 초기 결합 용량 보류다.
새 목록→3D/수확·새로고침·계정 변경·좁은 화면을 통과했다고 표시하지 않는다.

모든 시험 guard는 원512MiB/PID·합1GiB·600초·0.25초를 유지했다. 실패 후 시험 소유
프로세스를 정리했고 기존5역할/원본/두 frozen UI는 보존했다. 실제 만료 유지보수 때만
정상 절차로 legacy/의존 환기를 교체했으며 joint2root는 그대로 유지했다.
시험에서 정지된 복원 DB4개·복사된 passfile/키를 정리해167,873,614bytes를 해제했다.
원본/활성 서비스의 키는 건드리지 않았다. 원 증거·hash·실패 기록은 보존했다.

## 다음 한 단계

기존 `product-ui-result-catalog-native`는 계속 미완료다. 다음은 실제 측정된
브라우저 실행기/감독의 메모리를 분리하고 필요한 할당을 줄이는 것이다. 제품 소스·원 저장
값/UTC·읽기 권리·원 브라우저 조건/자원 한도를 유지한다. 건강한 보호 root를 정지하지 않는다.
코드·조건이 바뀌지 않은 실패 실행을 반복하지 않는다.

그 뒤 실제 목록→같은 결과/UTC의 C/N·수확, 재접속/API 재시작·계정/철회/늦은 응답·
키보드/좁은 화면·기존3상태 디자인 대조를 수용한다. 최신 backend의 구판 CODE 거부는
별도 의존성으로 남으며 지원하는 reader 판본을 명시해야 한다. 강제 재서명·코드 해시 허용 목록
확대나 이 API10응답으로 전체 U1을 대신하지 않는다.

native CLI gpt-6.1-sol/xhigh·원 문맥/출력 SHA를 사용했고 재귀 CLI/하위 agent0이다.
전체 backend/browser CI·새 Solar 정상64/hold/취소/계산 중WebGL·WSL 배포·실제 자료/독립
작물/경제/시장 검증은 별도다. 새 목록 UI/새 Solar 미배포·전체 날짜 미정·goal active를 유지한다.
