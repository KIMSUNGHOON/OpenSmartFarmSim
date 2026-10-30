# 공급 제한 형상 결과의 공개 export 수용 — 2026-10-30

새 자체 합성 입력에서 실제 계산한 결과를 공개 fixture로 내보내는 경계를 수용했다. 집중31검사, 별도 실제 source bridge1검사, 같은 두 출력과 전체 실패8종을 확인했다. strict SDK와 새 결과의 사용자3D 연결은 다음 단계다. 기존 비공개 자료의 권리·입력·계산 코드와 전체 goal은 변경하지 않았다.

[계약](../contracts/supply-morphology-export-v1.md), [기계 판독 증거](artifacts/crop-supply-morphology-export-20261030.json), [공개 파일 목록](fixtures/supply-morphology-public-20261030.json), [선행 저장/조회](crop-supply-morphology-artifact-20261030.md), [계획](../tasks/plan.md), [TODO](../tasks/todo.md).

## 실제 계산한 새 입력

기존 crop/초기 선언의 `redistribute:false`를 바꾸지 않았다. 새 `own-public-supply-morphology-20261030/public-software-QA-v1` 선언을 계산 전에 만들고 정상 source/authority/model/storage 경로를 실행했다. 수치 템플릿을 깊은 복사한 테스트 입력 제공자만 범위를 한정해 교체했다. 애플리케이션 검증기·계수·모델99source·격자·시간 범위는 바꾸지 않았다. 새 crop/stem/초기 선언의7개 권리와 최종 redistribution은 모두 true다. 원 private CAS와 false 권리는 그대로다.

원305181/1024초→512초의 합성 경로를 실제 분할 전진하고5후속 출현을 채택했다. genuine Context6개·CP33개와 CP가 없는 조달 전5시점, 총38시점을 저장했다. 공개 복원 API로 경계를 cold restore했으며 기존 typed handle을 가장하지 않았다. 서로 다른 새 source/context/prefix 지문은 유지하면서 원 기준과 상태·유량·장부·시계·형상 수치를 대사했다. 새 자료가 실제 품종 관측이나 전체 작기는 아니다.

## 공개 파일과 검사

새 저장소는62파일/10,364,683bytes다. 같은 입력의 재시도에서 root와 파일 메타데이터가 같았다. 최종 root는 `84daf00c44a964f904aa0b78e2c64f44c2753ec97641f23566fdfcc349bf4476`다. 저장 계산 코드102지문은 선행 수용 판본 그대로다.

[exporter](export-supply-morphology-replay.py)는 계산 없는 조회기와 기존 FD 고정 writer를 사용한다. 독립 두 출력이 각각101파일/14,197,795bytes로 완전히 같았다. 원 raw62개·NOTICE와 원 DTO38개/상태6,208scalar를 모두 대사했다. A/L/C·기관 ID/부착·출현 clock·원 UTC/phase/prefix·형상 원점/부족분/장부를 보존했다. 최종 index SHA는 `94aaced1aff85a349a88ee03cb6dc64dbc653561f674ff371104db2bf407d8fc`다. 공개 파일은 [자체 fixture 디렉터리](../web/public/supply-morphology-replay/own-public-v1/index.json)에 보관했다.

- 집중31검사는21개 개별 source 권리, 최종 false 보류/비변경,5개 잘못된 경로, 새 입력의 원본 비변경, 공개101파일의 독립 지문과 원본 범위, 전체 용량 실패를 검사한다. 별도 실제 bridge1검사도 통과했다.
- 실제 원 private:false 자료는 출력 폴더 생성 전에 거부됐다. 두 export에서 생장 import/RHS·DB·CLI·네트워크·출력 밖 쓰기는0회다. 출력 쓰기816회는 두 출력의 파일 생성/메타데이터/게시 동작이다.
- 현재 코드의 실제 실패8종은 부분 쓰기, 게시 실패, 늦은 권리·코드·출력·원 source 변경, 디렉터리 교체, 개별 크기 초과다. 모두 완성 index를 남기지 않았으며 검사 복사본은 정리했다. 크기 초과는 정상 접근 권한의 실제 해시/메타데이터를 가진 복사본에서 `CAPACITY_HOLD`를 확인했다.
- 검토 중 전체 export 용량 제한의 누락을 발견했다. 정상 source를 더 작은 검사 상한으로 export하는 RED에서 가짜 완료를 재현한 뒤, 원64MiB 상한이 원 blob/DTO/마지막 index 전체에 적용되게 수정했다. 수정 후 최종 두 export·8실패·31검사를 다시 확인했다. 이전 두 검사 스크립트의 가짜 경로/잘못된 파일 mode 실패와 이전 출력은 private 역사로 보존하며 최종 수용과 구분한다.
- 원251source/1output closure·private:false132blob·봉인 GUI4,865파일·기존 두 출력9,464파일/경계를 보존했고 기존5175 HTTP200을 확인했다. 새 공개 파일에서 private 경로/credential 패턴 일치0을 확인했다. 새 DB/API/worker/브라우저를 기동한 증거는 아니다.

원 root/Context/DTO/index2MiB·CP512KiB·source16MiB·store64MiB/4096파일·frame/기관512·sample scalar32768을 유지했다. 개별 공개 blob2MiB와 전체 공개 결과64MiB(마지막 index 포함)를 초과하면 잘라내거나 보정하지 않고 보류한다. 새 Context 최대 크기는 원 한도에 가까우므로 전체 작기 지원·최대 inventory 성능 수용이 아니다.

## 실제 공수와 확인하지 않은 범위

| 단계 | Guard wall | 결과 |
| --- | ---: | --- |
| 새 public source bridge | 157.995초 | 실제1검사 |
| genuine 전진 수집1/2 | 371.799/358.520초 | 원512초·6Context/33CP |
| 현재 생산/재시도 | 288.523초 | 같은 root/파일 metadata |
| 최종 두 export | 13.060초 | 원101파일씩 동일 |
| 최종 전체 실패8종 | 23.817초 | 실패 index0 |
| 최종 집중31검사 | 4.013초 | pytest31 passed |
| 원 자료/GUI 보존 | 1.971초 | 보존/5175 HTTP200 |

이 값은 소프트웨어 검증 시간이며 제품 응답 지연·전체 완료일이 아니다. 생산 준비의 기존 초기 RHS1회와 CP33개 현재 RHS 검증을 별도로 세었다. 생산/조회/export 과정의 과거 전진·조달·초기화 재실행은0회다. 각 guard는 원600초·PID512MiB/합산1GiB·로그4MiB 안에서 종료했고 보호5175·controller FD4→4/소유 자식0을 확인했다. 최대 관측은 생산 단계 PID226,652,160bytes/합산265,076,736bytes다.

전체 backend/frontend suite·새 브라우저·strict SDK·실제 농장 실행은 수행하지 않았다. 작업 전 HEAD `ce64d2166c894e5c6c0fce20aef552d2b9125f49`의 실제 CI API 조회는0runs였으며 로컬 검증을 CI green으로 표시하지 않는다. 새로운 프레임워크·의존성·운영 기반 변경은 없다.

## 다음 단계와 외부 의존성

다음 수용 단위는 strict SDK다. (1) 독립 root/index/code anchor와 닫힌 원 JSON wire 검증, (2) 원6Context/33CP/조달 전후의 ID·clock·단위·계보·원점·장부/관문 대사, (3) 부정 사례와 HTTP/취소/latest/복사·용량 검증 순서다. 현재14.2MB/101파일·38시점의 실제 경계로 분해하며, 첫 decode와 독립 조회 실측 뒤 브라우저 공수를 갱신한다. 아직 SDK나 새 화면 완료 날짜를 수용하지 않았다.

SDK 다음은 같은 저장 A/L/C/clock/ID/UTC/phase의 실제 잎·줄기 mesh/표/그래프·재생과 실제 브라우저 확인이다. 제작 폭/pose·없는 과실·수확은 계산 결과로 제시하지 않는다. 이후 생산량·자원·경제/거시/수급·지역·제품 farm/worker 연결·자율 비교가 남는다. 독립 국내 단일 품종 자료0·계수/권리 채택과 미래 작기/대응 후보 비교 자료 확보는 병행 외부 의존성이며 확보일·전체 완료일은 미정이다.

실제 native Codex CLI `gpt-6.1-sol/xhigh`의 실행 문맥과 출력 지문을 기록했고 재귀 CLI0회다. 사용자 clear 완료 회신 뒤에도 goal 도구는 기존 전체 active를 반환하고 새 등록을 거부했다. 교체 완료나 기존 전체 목표 완료로 표시하지 않고 재입력을 반복 요청하지 않는다. 과거10월22일 오전9시 초안을 새 미래 기한으로 재사용하지 않는다. G0–G4 `not_assessed`, R2 `not_approved`, 전체 goal active/incomplete다.
