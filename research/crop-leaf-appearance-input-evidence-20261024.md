# 자동 출현 원 입력의 현재 검토 — 2026-10-24

상태: [입력 증거 계약](../contracts/crop-leaf-appearance-input-evidence-v1.md)의 **합성 구조 검증 수용**.
새 원 정책·초기 잎/부착·프로필과 검증된 stem 입력을 같은 decision UTC로 묶었다.
사용자 [저장 3D](http://localhost:5176/leaf-appearance-replay.html)는 유지한다.
새 농장/완료 parent·서명/worker/API 연결은 후속이며 이 모듈은 아직 사용자 runtime에 배포하지 않았다.

## 구현과 검증

`LeafAppearanceInputEvidenceAuthority`는 기존 원 program parser·population 초기 구조 검사와
저장 reader의 초기 부착 대사를 재사용한다. 원 stem의 UTC/초기 시점·shoot/schedule과
명시 정책의 영양 위치마다 원 순서의 잎 하나/같은 출현 초를 요구한다.
원 정책·초기·프로필/부착 지문과 양쪽 현재 검토·모델/37코드를 새 HMAC domain에 묶는다.
stem root는 식별자이며 `stem_artifact_root_verified=False`, 수치 초기조건/관문 승인은 False다.

기존 SourceRecord의 원 URL/제품 ID·판본·SHA·단위/시각/QC·합성 저자/방법과 권리를 대사한다.
원 입력의30개 unit 객체와 정책의 첫 생식 순번/영양 간격 두 개의 단위 `1`, **총32개 변수**를 확인했다.
재배포 False는 내부 검증과 구분해 거부 권리로 보존한다. 발급/검증 전후 양쪽 현재 검토를 재확인하며
마지막 parent 검토 도중 appearance 검토가 철회되는 반례도 차단했다.
서로 다른 resolver의 원자 snapshot이나 실제 농장 권리·G0 승인을 이 결과로 주장하지 않는다.

모듈 부재 RED 뒤 최초65집중 검사가 통과했다. 새로 검토된 유효 정책 변경과 이전 증거 재사용 거부,
resolver의 scope/source/예외/늦은 decision 변경 여섯 검사를 추가한 최종 묶음은
**신규71/관련319·총390검사(7파일)**다. 기존 입력 증거·준비·producer/reader/export도 포함한다.
rehash한 출처/단위/권리/가용 시각·초기 부착/정책 혼합과 현재/늦은 철회,
재서명 metadata/code/time 변경·상한·runtime/model/config drift와 metadata 복사본을 검사했다.

별도 fresh 프로세스는 공개 root가 참조하는 **같은 원 program SHA**
`64d9e1551f925e8766c6f658c0838793556be58ecefe0dd96a55fad7bca47ade`를 검증했다.
원 stem program은 `0c6ebe7ddbff19b64a6348c6ea003a2c78340006a81028977cbc35a7bbef1eb3`다.
초기 잎/마디3·32변수/37code와 철회 거부, 생장 import/계산·DB/CLI·파일쓰기0,
원43 appearance/14 stem/40 population blob 및 공개20/17파일의 **134개 metadata/bytes**와 FD4→4를 보존했다.
fresh v2는 원 code map/모델 버전을 증거에 추가해 현재 파일 SHA와 대사한 같은 검증이다.
source/review는 자체 소프트웨어 fixture이며 실제 외부 자료·제품 CLI 검토나 농장 승인이 아니다.

실행 source는 `c7f6038b6a9668a90330c1043aaa4a9d9eb6eae9`이며 생산 모듈은 최종390/fresh 사이 같았다.
전체 backend/새 hosted CI는 실행하지 않았다. 기존 웹 소스/공개 자료는 바꾸지 않아 이전 웹 CI를 반복하지 않았다.
현재 native CLI `gpt-6.1-sol`/`xhigh`의 실제 turn_context 시각·원 LF SHA와 재귀 CLI0은
[기계 판독 증거](artifacts/crop-leaf-appearance-input-evidence-20261024.json)에 보존했다.

## 보존과 다음 수용

최종390검사는66.65초(guard67.620초), fresh v2 guard는1.102초였다.
전체 소유 phase의 최대 PID RSS105,390,080bytes/합산442,351,616bytes로512MiB/1GiB 안이었다.
0.25초 표본·600초/4MiB 로그 상한, 보호3root·원2,504항목/현재 소스·잔여0·FD4→4를 확인했다.
기존 수치 모듈/원 지문·불변 결과·DB/키·서비스/UI는 바꾸지 않았다.

다음은 **같은 등록 농장·완료된 서명 stem 작업과의 결속**이다.
기존 MorphologyExecutionQuery/farm authority·JobStore를 재사용하고 새 표나 서비스를 추가하지 않는다.
원 program/source/evidence와 outer 정책 지문, tenant/farm·원 완료 job/result/root/최초 계산 시각을 대사한다.
다른 tenant/미완료·취소/다른 root, 현재/늦은 양쪽 권리/검토·등록/권한 변경을 거부하며
별도 실제 SCRAM/fresh 같은 binding bytes·조회 생장/CLI/SQL쓰기0·원 행/파일/FD·WSL/소유 정리를 확인한다.

새 source가 기존 farm decision 이후 가용이면 그 job에 소급 결속하지 않는다.
필요한 늦은 decision의 별도 자체 합성 farm/parent를 만들고 원 사용자 작업/25표·자료는 보존한다.
이후 서명 결과→자동 worker/API→같은 job3D로 이어간다. 입력 증거의 수용을 그 전체 경로의 수용으로 확장하지 않는다.

다음 farm 자식은 요청/결속 경계와 구현1–2h, 순수 반례/실제 SCRAM·fresh1–2h,
검토/보존·기록0.5–1h로 **2.5–5집중시간**의 낮은 신뢰 추정이다. 앞선 입력 증거 추정은 이번 실적으로 대체한다.
실제 품종/독립 국내 작기0과 관리·생산/자원/Decimal 경제·거시/수급·자율 비교,
R2/첫 cold 셰이더 경고·G0–G4는 남는다. 외부 자료 확보 일정이 없어 전체 완료 날짜는 미정이며 goal active다.
