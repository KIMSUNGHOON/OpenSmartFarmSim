# 원 출현/줄기와 관리 선언의 생애 입력 결속 — 2026-10-24

상태: **원 자동 출현 준비/줄기·관리 입력 결속 수용**.
[계약](../contracts/crop-leaf-lifecycle-preparation-v1.md), [기계 증거](artifacts/crop-leaf-lifecycle-preparation-20261024.json),
[13지문 결속 장부](artifacts/crop-leaf-lifecycle-preparation-ledger-20261024.csv)를 제공한다.
현재 웹은 [이전 정책 잎 생장](leaf-appearance-execution-web-20261024.md)이다. 새 생애 결과의 저장/조회·runtime/3D는 후속이다.

## 구현과 통과한 검증

별도 관리 프로그램을 원 appearance bytes SHA에 결속하고 권리를 별도로 보존한다.
parser는 닫힌 schema·고유 leaf/event ID·원 UTC/정확 초·명시 whole-leaf 제거와 display policy를 검사한다.
원 초기 잎 또는 실제 자동 출현 선언만 제거 대상으로 받으며 출현 전/원점 차이·준비 forcing 밖의 시각은 거부한다.
기존 appearance preparation의 source/generated/initial/derivation SHA·초기 부착/자동 출현·정확 forcing은 그대로다.
초기 population/lifecycle 상태의 검증·초기화는 허용한다. 새 lifecycle 전진/결과 producer는 호출하지 않는다.

같은 최종 코드의 **새63/관련568·고유631검사**가 통과했다. 초기12를 더하지 않는다.
원 준비 결과/입력·초기 state/hash·forcing/단위/ID와 source 권리3종을 대사했다.
원점/시각·다른 stem/shoot/schedule·초기 부착/기준온도·권리/잘못된 선언/512·513/bytes를 확인했다.
새 코드·반환 전 원 준비 결과·중간 blob bytes/권한·디렉터리 교체의 늦은 변경은 보류됐다.
별도 parser 프로세스의 생장 import0, 준비의 전진/producer·DB/CLI·파일쓰기0과 입출력 alias 방지를 확인했다.
파일 custodian owner 차이도 거부했다. 이것이 농장 SourceRecord/계정 권한·G0 승인 검사는 아니다.

첫 전체 회귀에서 기존 appearance parser/preparation의 보류 예외13개가 새 형식 밖으로 빠졌다.
거부 자체는 발생했으며, 두 기존 예외 클래스를 명시적으로 받아 새 preparation hold로 전달하도록 수정했다.
첫 실패/수정과 최종631을 구분해 보존했다. 기존 모듈/판본은 수정하지 않았다.

## 실제 저장 원 준비 결과의 별도 프로세스 대조

기존 원 appearance/줄기 자료와 실제 ContentAccess를 사용했다. 새 준비 결과에 담긴 원 준비가 저장된
`a09cd9f32a7c9ef69191eb26c6fa8a0a4353027bb3811a1cca514d07d0e490aa`와 **bytes/SHA 모두 같았다**.
원32code pin과 새38code pin, 자동 출현2개·명시 제거2개·같은 원 forcing/초기 population SHA를 대사했다.

새 준비3회(같은 입력 반복·관리 redistribute=False 변형)에서 원 준비6회 모두 같은 저장 SHA였다.
이번에는 원 자동 정책의 준비도 실제로 다시 수행했다. 이전 수치 커널의 선언 재사용 검사와 구분한다.
반환32,640bytes와 실제 관리 원문/준비 반환문을 비공개 불변 파일로 보관했다.
재배포False는 보존됐고 원 준비/초기 생애 state SHA는 같았으며 관리/input SHA는 달라졌다.
관찰자의 입력/반환 증거 저장을 제품 preparation의 파일쓰기0과 구분한다.
초기화3회는 active2/removed1/pending2였다. 생장 전진/producer·DB/CLI 금지 호출·소유 밖 쓰기는0이었다.

원 appearance52blob과 stem29blob의 bytes/metadata·33legacy code는 그대로다.
자체 소유 합성 source이며 실제 농장 측정·생물학 검증은 아니다. 원 권리/관리 권리/stem 권리를 합쳐 승인하지 않았다.
fresh v1은 비교만 통과한 pilot이고 v2는 정확 원문/반환 지문까지 보관한다. 두 버전의 횟수를 합산하지 않는다.
전체 backend·새 hosted CI/브라우저·사용자 배포는 실행하지 않았다. 새 의존성/API/SDK/DB·키·화면 변경0이다.
초기 실패 phase를 포함한 관측 최대는 PID105,652,224bytes/보호+소유 합599,642,112bytes였다.
.25초 표본·기존4root/2,793감시 항목·source·FD4→4·소유 잔류0,512MiB/PID·합1GiB/600초/로그4MiB를 유지했다.
전체 host/Windows Chrome 용량 수용은 아니다. native CLI gpt-6.1-sol/xhigh,
turn_context2026-10-24T00:53:28.313Z 원 LF SHA
`760e7bb7e8872189697658158dafa774186fad7643f6800ec08f5a952c70e7d0`·재귀 CLI0을 기록했다.

기록 검증은 코드 지문3개/준비 source38개·JUnit631개·결속 장부13행·원문/반환 SHA4개와 상대 링크3,344개를 대사했다.
새 파일 staging을 포함한 전체 변경의 줄바꿈/공백 검사도 통과했다.

## 다음 한 단계와 외부 의존성

다음은 **별도 불변 생애 결과/계산 없는 frame 조회**다. 이 준비의 두 원문/원 준비/초기 state·code 지문과
원 stem sample UTC/기관 ID를 결속해 lifecycle을 producer에서만 계산한다. active/removed/pending과 전체/마지막 정확 시각을 저장한다.
무제거의 원12시점/47상태 및 제거의 독립 나이/면적/합계를 대사하고 별도 fresh 조회는 생장 import/계산·DB/CLI·쓰기0이어야 한다.
현재/늦은 권리·원본/코드/서명 전 원 custody·용량·기존 판본/원 자료 보존을 검증한다. 새 기반 서비스는 추가하지 않는다.

그 뒤 기존 실행 흐름을 재사용해 농장/현재 SourceRecord·서명·HTTP/SDK와 같은 UTC3D로 연결한다.
새 DTO는 전체 시각과 제거 마지막 시각을 분리하고 active만 표시·pending 제외, 표/면적 합계/그래프와 일치해야 한다.
기존 준비의 전 구간 초기 잎 저온 보류와 기존 reader의 모든 잎 시각=현재 시각 계약은 유지한다.
별도 질량 변환/수지 뒤 생산/자원·Decimal 경제·시장/거시/수급·자율 비교로 간다.

이전85–170집중분 예상은 위 구현/631검사·fresh 실적으로 대체한다. 다음 저장/조회는 계약/그래프25–45분,
producer/원본 결속35–70분, 무계산 reader/독립·변경 검증35–75분, 기록15–30분으로 **110–220집중분**의 낮은 신뢰 추정이다.
농장/HTTP/SDK/3D·실제 자료 획득 시간은 포함하지 않는다. [국내 자료 획득](independent-domestic-cherry-tomato-data-20261024.md)은
병행 외부 의존성이며 이번에 원측정을 새로 받지 않았다. 원측정/미사용 독립 국내 작기0·국내 첫 품종 미확정,
생산/자원/경제/추천·R2/첫 cold·G0–G4와 전체 완료일 미정을 유지한다.
