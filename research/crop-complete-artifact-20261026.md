# 전체 합성 작물 이력의 불변 저장·계산 없는 조회 — 2026-10-26

**25개 집중 검사와 별도12저장/834시점의 cold 조회를 수용했습니다.**
[계약](../contracts/crop-complete-artifact-v1.md), [producer](../backend/app/crop_complete_artifact_producer.py),
[reader](../backend/app/crop_complete_artifact_reader.py), [시험](../backend/tests/test_crop_complete_artifact.py),
[별도 조회 검증기](verify-complete-crop-artifact.py), [기계 증거](artifacts/crop-complete-artifact-20261026.json).
기존 전체 prefix의 합성512초를 저장한 연구 결과이며 UI 연결·실제 농작물 예측 승인은 후속입니다.

## 저장과 조회의 범위

실제 context/CP handle로 수용된 complete-prefix packet을 생성하고 원 leaf/stem source·notice,
context와 각 절간 point request/실제 response를 기존 불변 CAS에 보관합니다. 현재 코드53개와
원본 source·권리·초기 링크·프로필·clock/기관·출현/CP·phase/cursor/prefix를 검사한 뒤 root를 마지막에 게시합니다.
같은 입력/코드 재시도는 같은 root입니다. 게시 전 실패는 완료 root를 남기지 않습니다.
게시 후 현재 파일/코드가 바뀌면 최종 fence·후속 조회가 hold하며 불변 root 자체를 지우지는 않습니다.

원 CP에 C_i/a/A·누적/장부를 한 번만 보관하고, CP 없는 dense 후보는 별도 snapshot을 유지합니다.
조회는 전체 packet 또는 선택 frame을 반환하며, 선택한 잎의 상태는 저장 벡터107+3n에서 그대로 읽습니다.
원 줄기의 ID/곡선/앵커·수치 출현 기관과 원점 차이, 원 source 이후의 잎 부착/사건 이력을 대사합니다.
점 길이 수식·RHS·출현 초기화·과거 시계/ODE는 조회에서 실행하지 않습니다. 저장 값 간 해시/합계·수지 QC만 수행합니다.
이 복사본의 현재 로컬 파일 정책과 포함된 grant를 검사하며 외부 farm 권리/철회·서명 custody·런타임 접수는 별도입니다.
호출자가 신뢰한 원본에서 받은 root SHA가 필요합니다. 자체 해시는 농업적 진실이나 자료 승인을 증명하지 않습니다.

## 검증

- 최종 **25pytest**: 실제 producer/전체 원 packet·일부 decoded frame, 동일 재시도/root,
  초기 링크의 redistribute:false 유지, 잘못된 epoch/시각·phase/prefix/상태 원본 종류,
  부모/사건/원 기관/곡선 앵커 출처·길이/단위, 초기 권리/코드·프로필/누락 receipt·부분 저장,
  방어 복사·bool index 거부와 현재/늦은 파일 정책을 확인했습니다.
- 일반6경로414시점+추가6경로420시점, 합 **834시점**을 새 namespace에 저장했습니다.
  원 packet canonical bytes 전체가 그대로이고 원 CP380개·CP 없는 후보12개·잎 상태13,788값을 보존했습니다.
  마지막/점 전후/첫 상태의 decoded48frame도 같은 원 벡터와 일치했습니다.
  원 길이/정확 나이의 수치 검증은 [앞선 complete-prefix 증거](crop-funded-complete-prefix-20261026.md)를 유지합니다.
- 별도12개 cold 프로세스에서 생장 모듈 import·DB·CLI·network·write open은 각각0회였습니다.
  이 검사는 위 공개 검증기를 실제 실행했습니다. 저장 3886파일의 bytes/metadata와 기존 source/결과529파일을 보존했습니다.
- 생산은 기존 원 context/CP를 복원해 현재 CP 검증·binding을 수행했습니다. 실제 RHS 합884회이며
  과거 prepare/advance/출현점·DB/CLI/network와 출력 밖 write open은0회였습니다.
  저장 최대 packet 1,867,742/2,097,152bytes, 기존512frame/32768scalar 및 모든 하위 cap을 유지했습니다.
- WSL은512MiB/PID·소유+보호1GiB·0.25초/phase600초/로그4MiB를 유지했습니다.
  최종 집중/두 생산/cold phase의 합산 peak는 각각
  152,178,688/
  128,077,824/
  130,887,680/
  127,590,400bytes입니다. 소유 잔여0·FD4→4·보호 외형1root/원4500항목을 보존했습니다.
  Windows/다른 사용자의 프로세스는 이 합산 범위 밖입니다.

초기 prototype은 point curve SHA의 version envelope 누락, 다음 source-link QC는 영수증 대신 program에서
잎 ID를 찾아야 하는 오류로 실패했습니다. 첫 시험의19pass/1fail은 실패 주입기가 원 license text도 JSON으로 읽은
시험 오류였으며 수정 후21pass, 원 기관/epoch 검사를 보완한 최종25pass를 구별해 보존했습니다.
최초/실패 namespace와 로그를 덮어쓰지 않았습니다.
기존 private:false132blob·GUI1502파일과 공개324/경계100/목록424파일·기존 최대 요청 hold는 최종 보존 점검에서 별도로 대사합니다.

## 판단·한계와 다음 수용

실제 native CLI의 모델은 **gpt-6.1-sol/xhigh**, turn_context 2026-10-26T13:02:23.797Z이고
원 LF SHA는 `a4584e4204cc8457886a56871a68ed594bcb0e3816319029d53908e517d6e2eb`입니다. 재귀 CLI 호출0으로 설계 판단·시험을 수행했습니다.
기존 자체 합성 QA/매개변수만 재사용했으며 새로운 품종·현장 측정·농업 계수를 채택하지 않았습니다.
G0–G4는 not_assessed, R2는 not_approved입니다. 전체 backend/build/브라우저·전체 최대 API 조합은 이번에 실행하지 않았습니다.
기존512잎 요청의528,002/524,288byte hold는 유지하며 이번 정상 경로 수용으로 전체 최대 지원을 주장하지 않습니다.

다음은 **새 artifact export → 새 strict SDK → 같은 저장 상태의 실제 잎·줄기3D**입니다.
원 source/초기 링크 중 하나라도 재배포가 false면 export를 보류하고, 현재 notice/코드/프레임·CP 없는 후보를 보존해야 합니다.
SDK는 새 판본의 닫힌 schema·ID/clock/phase/부착·벡터/단위·출처/권리와 부분 실패를 거부해야 합니다.
3D는 원 길이·면적/ID/UTC를 mesh/표/그래프·재생/URL 복원과 대사하고 제작 배치와 계산 상태를 구별해야 합니다.
기존5175 제작 외형은 유지하며 이번 새 결과는 아직 UI에 연결하지 않았습니다.

저장 단계의 앞선2.75–5.5집중시간 예상은 이번 실제 수용으로 대체합니다.
기존 export/SDK 재사용 경계를 검토해 다음 export0.75–1.5h+SDK1–2h+독립 검증0.5–1h,
합 **2.25–4.5집중시간**을 잠정 배정합니다. UI/실제 브라우저는 그 뒤2.5–4.5집중시간의 낮은 신뢰 작업량입니다.
이는 완료 날짜 약속이 아니며 새 schema/UI 결속에서 확인한 의존성에 따라 재산정합니다.
실제 품종/독립 국내 측정0건·새 기관 C/초기 생물학·한 작기/수확·자원/경제·거시/수급·자율 비교와
제품 전체 UI·예측/추천 관문 및 전체 완료 날짜는 미완료/미정입니다.
