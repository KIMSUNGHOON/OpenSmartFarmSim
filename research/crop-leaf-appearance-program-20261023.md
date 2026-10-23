# 초기 잎/정책을 묶는 자동 출현 program 수용 — 2026-10-23

상태: [입력 계약](../contracts/crop-leaf-appearance-program-v1.md)의 **신규46/관련269·총315검사 수용**.
[기계 증거/계산 참조](artifacts/crop-leaf-appearance-program-20261023.json),
[원 source program](../fixtures/crop-leaf-appearance-software-program-v1.json),
[생성된 계산 입력](../fixtures/crop-leaf-appearance-generated-population-v1.json)을 제공한다.
현재 [사용자 잎3D](leaf-admission-live-automatic-20261023.md)는 기존 작업을 유지한다.

## 구현과 수용 범위

원 줄기 root·초기 잎 목록·명시 분류 정책/프로필·권리를 하나의 program으로 묶었다.
초기 줄기의 영양 위치마다 잎 한 개를 같은 순서/부착 ID·출현 정확 초에 요구하고 누락/중복·생식 위치의 잎을 보류한다.
초기 잎의 열적 나이는 명시 값이며 줄기 나이를 복사하지 않는다. 별도 기준온도/나이의 정상 사례와
각 clock은 유효하지만 부모와 출현이 다른 사례를 구분했다.
새 선언은 기존 [저장 줄기→잎 입력](crop-stored-shoot-leaf-birth-inputs-20261023.md)을 사용한다.
초기+새 ID/512개 상한과 이후 기온 정의역도 검사했다.

얇은 parser와 준비 모듈을 분리했다. parser는 기존 reader의 형식/권리/단위 검사만 사용하며
분류/생장/준비 모듈을 import하거나 면적·출현을 계산하지 않는다. 새 float/Decimal 수식·품종 계수·라이브러리 추가는0이다.
준비는 초기 면적/곡선을 대사하고 기존 계산용 v1 program과 파생/초기 결속 증거를 반환한다.
원 source SHA/크기, 생성 입력·초기 state/결속·파생 SHA와32개 code를 기록한다.
원17code 일치와 모든 원 sample bytes를 확인하고 계산 전·반환 전 code/원본도 다시 검사했다.
원본의 거부/변경은 조용히 다른 입력으로 대체하지 않는다.

이 판단은 native CLI gpt-6.1-sol/xhigh의 실제 context2026-10-23T13:49:28.973Z,
원 LF 포함 SHA `8c52bf91e854f8a31cd54e41868a05c1458a34f81ae17f91cb8c36f0e07638ca`다.
보고서/fixtures/JSON이 해당 CLI의 실제 출력이며 재귀 CLI0·새 독립 자료 승인 reviewer0이다.
농업적 근거는 [기존 분류 조사](crop-phytomer-kind-20261023.md)를 유지하며 새 실제 자료·계수 채택은0이다.

## 검증과 실제 원본 산출물

실제 모듈 부재 RED 뒤 신규46검사3.58초·관련9파일269검사43.53초를 통과했다.
최초36통과와 별도 probe는315에 중복 합산하지 않았다.
형식/권리·초기 누락/중복/순서/생식 위치/출현·원 clock/ID·초기/새 ID 충돌·다른 source 참조,
정의역·코드 drift·도중 중간 blob 변경을 확인했다. 실제512잎(초기3+새509) program과2MiB 출력도 검사했다.
별도 fresh parser에서 생장/분류/준비 import0·DB/CLI/파일쓰기0을 확인했다.

보관 중인 원14blob으로 같은 source bytes를 두 번 준비해 결과가 정확히 같았다.
초기3/새2선언·32code와 원17code 일치, 원본 metadata/bytes 보존·생장 advance/producer/DB/CLI/쓰기12진입0을 대사했다.
원 source와 생성 v1 program은 위 fixtures에 **동일 canonical bytes**로 보관했다.
서로 다른 권리 선언 시각/내용은 새 source SHA가 되며 함수 내부에서 날짜나 매개변수를 고르지 않는다.

같은 준비 입력을 기존 실제 v1 producer에 전달한 별도 합성 호환 계산도 저장했다.
root는 `94224ddcac4cdbb46eb2ba4cd1318fdaf71c14550128e570ce90fc60e3334285`이며
40blob·12시점/47면적·마지막5잎이다. 원 초기 state SHA와 생성 program SHA가 준비 결과와 같았다.
독립 Decimal100의47개 면적/나이와 실제 stored reader를 대사했고 조회의 생장 advance는0이었다.
이는 source→생성 입력→기존 계산의 호환 증거이며 새 자동 출현 outer manifest/무계산 조회·3D 수용은 후속이다.

첫 보관 실행은 출력 부모 디렉터리가 없어 계산 저장 전에 종료했다. 해당 실패/원본 보존을 기록하고
소유700 부모를 만든 뒤 같은 입력으로 정상 계산을 완료했다. 제품 코드는 이 준비 오류로 수정하지 않았다.
원3root·감시2,481항목/소스·자료와 WSL512MiB/PID·합1GiB·600초/4MiB 한도를 유지했다.
최종 신규/회귀/원본/호환 guard는4.705/44.444/1.153/2.553초이며 .25초 관측 합산 최대 RSS478,470,144bytes다.
소유 잔류0·FD4→4를 확인했다. 전체 backend/새 hosted CI·브라우저/사용자 배포는 실행하지 않았다.

## 다음 한 단계

다음은 **원 source program·준비/생성 증거와 계산 root를 한 별도 불변 manifest로 묶는 producer**다.
같은 입력/코드의 같은 root·기존14/새40blob 보존, 실제 원 수치/UTC/47면적의 결속과
늦은 권리/원본/코드 변경·부분 저장 때 completed root0이 첫 수용 기준이다.
기존 완료 job/result를 다시 쓰지 않으며 기존 v1 계산기/reader를 재사용한다.
계약/결속0.5–1시간 + 저장 조립1–2시간 + 실제/거부·재실행/기록1–2시간 = **2.5–5집중시간** 잠정 작업량이다.
실제40blob/12시점·이미 생성된 두 fixture와32고정 소스 재사용이 전제이며 완료 날짜를 보장하지 않는다.
그 뒤 source/파생/계산의 무계산 reader·fresh 검증→strict SDK/같은 UTC3D를 잇는다.

실제 Axiany 계수·forcing/초기 기관·독립 작기 확보0은 병행 외부 의존성이다.
관리/노화·생산/자원/Decimal 경제·수급/거시/자율 선정·R2/첫 cold 경고·제품 UI/G0–G4와 전체 완료일은 미완료/미정이다.
