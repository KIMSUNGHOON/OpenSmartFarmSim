# 새 기관 전후·재개 결과의 공개 저장 데이터

2026-10-31 KST. **합성 공개 데이터/조회 수용; 새 화면은 후속.**
[계약](../contracts/supply-material-public-replay-v1.md),
[producer](../backend/app/crop_supply_material_artifact_producer.py),
[reader](../backend/app/crop_supply_material_artifact_reader.py),
[exporter](export-material-replay.py),
[시험](../backend/tests/test_crop_supply_material_artifact.py),
[inventory](fixtures/supply-material-public-20261031.json),
[기계 증거](artifacts/supply-material-public-replay-20261031.json)를 연결한다.

## 산출물

원 공개 source의 허용 상태를 다시 검증하고 새 정의/입력 provenance로 실제 계산했다.
기존 private false branch의 결과를 승격하지 않았다. 새 root는
`b4640f0532420a0deaa0cf82f840a548517f075a46059687acbd5c88caf11cae`,
index는 `9ce159b5b23fc54294a0dbac337e66757b2ab9858af0f78d66dea0933e1dddad`다.
[새 공개 데이터](../web/public/supply-material-replay/own-public-v1/index.json)는
106파일·13,985,230bytes·4시점/722좌표이며 원 NOTICE를 보존한다.

출현 직전/직후는 같은 정확 시각이고 잎11→12·상태176→182다. 이후 실제528/536초 current를 잇는다.
각 ID·부모·원 면적/길이/C·정확 clock·수지/기원을 저장 원문과 대사했다.
G0–G4/R2는 미평가/미승인이고 긴 작기를 덮지 않는다. 현재 UI는 기존38시점이다.

새 계산의 실제 RHS는 base5 + forcing17 + 후보34 + point36 + 채택36 + 재개10 =138회다.
producer/조회/export는 RHS0이다. 별도 프로세스에서14개 모델/성장 진입 모듈을 차단하고
DB/network/CAS 쓰기0·같은4frame hash/같은 export index를 확인했다.
조회는 저장된 RK4/clock·수지의 대수 검증을 수행하며 실제 시간 전진이나 RHS를 재실행하지 않는다.

## 검증과 보존

최종 **39 passed**, pytest233.09초/guard234.62초다. PID최대204,353,536bytes/합계402,145,280bytes였다.
실제 public 계산/별도 프로세스 export 검증은90.58초·PID175,636,480bytes/합계357,330,944bytes였다.
RSS는0.25초 WSL 표본이며 Windows 전체 host 사용량은 포함하지 않는다.

- genuine handle/실제 source·원본/새 상태·phase/clock/기관별 좌표와 동일 producer/export 결과를 확인했다.
- 사용하지 않은 private 정의가 source 저장소에 있어도 선택 witness 외의 파일은 복사하지 않았다.
- 세 공개 권리·private false 계산·related/relative/symlink 경로·개별/전체 한도·결측 source를 거부했다.
- source/frame/claim/code/권리·추가 blob/시각 변경, 재해시한 state/phase/global budget을 차단했다.
- 게시 직전 source/output 변경은 index를 게시하지 않았으며 원본은 보존했다.
- 독립 프로세스의 import 차단·DB/network/CAS 쓰기0과 정확 clock/기관 좌표 대사를 확인했다.

첫 module 부재 RED를 보존했다. 초기 조회는 참조·해시를 함께 바꾼 세 반례를 허용했다.
저장 RK4 단계/끝 상태·누산/lifetime/clock과 phase 경계·원 global+branch 예산 검증으로 수정했다.
전후 RED/수정 core를 남겼으며 수식/수지 예산을 낮추지 않았다. 시험의 clock_exact 구조를 잘못 참조한
KeyError도 기록하고 고쳤다. 실패 실행을 통과 수에 합치지 않았다.

이전514source/1output pin·material-owner36개 private 증거와14/17/14 archive,
이전 point/state/root/forcing·원 CAS/입력·4500항목·세 preview HTTP/원 고정 수명을 보존했다.
새 source/base/forcing/material/artifact/두 export의7개 manifest와 공개106파일도 대사했다.
모든 guard는 소유 child0·FD4→4로 끝났다. 새 UI/브라우저·전체 backend/frontend suite·제품 전체 CI/배포는 실행하지 않았다.

실제 native Codex CLI gpt-6.1-sol/xhigh·CLI0.157.1의 session/turn LF hash와 설계·실행 결과를 기록했다.
재귀 CLI/새 subagent·외부 raw/농업 계수/요금 채택0이다. 자체 검토/합성 QA를 독립 농장 검증으로 표시하지 않는다.
저장 root는 trusted local producer 또는 고정 inventory로 선택하며 외부 Farm 권한/서명을 대신하지 않는다.

## 다음 단계

다음은 이 새 namespace의 **strict SDK**다. source graph/권리·코드·raw bytes와 모든 저장 수치·clock/phase/ID를
검증하고 HTTP/취소/latest·변조/한도·타입과 독립 데이터 대사를 통과시킨다. 잠정0.75–1.5집중시간이다.
그 뒤 기존 실제 잎/줄기 scene 연결1–2h + 실제 브라우저/보존/기록0.75–1.5h,
첫 새 기관3D까지 **남은2.5–5집중시간의 낮은 신뢰 추정**이다. 실제 통합 결과에 따라 갱신한다.
이번 데이터 단계의 이전1–2h 초안은 실제 수용 기록으로 대체하며 전체 제품 완료일 약속이 아니다.

긴 작기 완료를 첫3D의 선행으로 묶지 않는다. 이후 반복/paging·600초 초과·주야/응축/관리/기관 수명·긴 작기,
생산·자원 사용/구매량·Decimal 경제 → 거시/수급·대응 후보 자율 비교·최종 제품 UI를 진행한다.
독립 국내 raw0·실제 첫 품종/현장 forcing·관리/계수/권리는 병행 외부 의존성이다.
실제 생산/수확·구매 에너지·마진/추천·G0–G4/R2와 전체 goal은 미완료이며 전체 완료일은 미정이다.
