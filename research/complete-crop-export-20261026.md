# 전체 합성 작물 저장 결과의 웹용 내보내기 — 2026-10-26

**새21집중 검사와 별도12경로/834시점의 두 번 동일 내보내기를 수용했습니다.**
[계약](../contracts/complete-crop-export-v1.md), [exporter](export-complete-crop-replay.py),
[시험](../backend/tests/test_complete_crop_export.py), [기계 증거](artifacts/complete-crop-export-20261026.json).
[기존 저장 결과](crop-complete-artifact-20261026.md)의 수치·원본/권리를 보존하는 합성 연구용 경로입니다.

## 사용과 형식

프로젝트 venv의 Python으로 `research/export-complete-crop-replay.py DIRECTORY TRUSTED_ROOT_SHA NEW_OUTPUT`을 실행합니다.
source/output은 서로 겹치지 않는 절대 경로이고 출력은 새 경로여야 합니다. 기존 결과를 덮어쓰지 않습니다.
leaf·stem 원본과 초기 링크의 ownership/access/store/use/transform/display/redistribute가 모두True여야 합니다.
출력 생성 전과 게시 직전에 다시 확인합니다. 비공개 권리를 승격하지 않으며 현재 외부 농장 권한/철회·서명 custody는 별도입니다.

기존 funded exporter의 FD 고정·exclusive/nofollow·경로/inode/소유/권한·단일 링크 검증과 pending index 게시를 재사용합니다.
원 root/packet/context/CP·수치 후보/기관 point영수증·NOTICE의 **연결된 원 bytes**만 내보내고 CAS의 무관한 orphan은 제외합니다.
각 frame의 닫힌 DTO는 schema/version·artifact SHA·index·원 frame이며 CP와 상태 벡터를 재작성하거나 보간하지 않습니다.
새 index는 원53code·exporter/writer 지문, source/권리·basis, 원 blob/DTO 해시·길이와 exact UTC/phase/cursor/기관을 결속합니다.
개별 파일/index2MiB와 기존하위 cap을 유지합니다. 더 큰 원 blob은 자르지 않고 export cap hold로 남깁니다.
실패 전 출력은 정리/덮어쓰지 않으며 게시 전 실패에서는 index가 없습니다. 게시 뒤 변경은 index를 지우지 않으므로
신뢰한 index SHA와 후속 현재성 검증이 필요합니다. 파일 복사나 자체 해시는 농업적 승인/진실을 증명하지 않습니다.

## 실제 검증

- **21pytest:** 원 raw/packet/notice·69frame DTO/CP 없는 후보, 두 출력 동일 bytes,
  실제 private:false 사전 거부/원본 보존, source·stem·초기 링크 권리의 첫/늦은 거부,
  unsafe/기존/symlink 경로, 출력 폴더 교체와 file/write/publish/source/code 실패의 index 미게시,
  계산·DB/CLI/network 호출 차단을 확인했습니다. 늦은 권리/source/code 검사의 실제2번째 진입도 대사했습니다.
- 기존 공개 선언을 가진12원본 **834frame**을 별도 프로세스에서 새 출력 두 곳씩으로 내보냈습니다.
  각 쌍의 파일명/내용/index SHA가 정확히 같고 합 **1,668 DTO·9,464파일**을 확인했습니다.
  원 packet bytes·source/NOTICE·CP380개/후보12개와 원 상태/시간/phase/ID가 각 출력에서 같습니다.
  잎 상태13,788값의 두 출력 보존(27,576값)을 확인했고 원3,886파일의 bytes/metadata를 보존했습니다.
- 별도 exporter의 생장 import·DB·CLI·network·새 출력 밖 write open은 각각0회였습니다.
  기존 reader/producer/모델·helper exporter의 파일은 수정하지 않았고 새 의존성/서비스/DB/키도 추가하지 않았습니다.
- WSL512MiB/PID·소유+보호1GiB·0.25초/600초/로그4MiB에서 집중 검사
  310.426초/합170,246,144bytes,
  별도 두 출력 105.276초/합126,226,432bytes였고
  원4500항목/source·보호 외형1root·소유 잔여0/FD4→4를 보존했습니다. 다른 작업/Windows RSS는 이 측정 범위 밖입니다.

첫 시험은 공개 성공 fixture에 private source를 사용해2fail/19pass였습니다. 이때 이른 권리 거부로 통과한
부정 시험은 수용 증거로 세지 않습니다. 공개 fixture를 새 소유 선언/새 입력·새 root로 재생성하고
목표 지점 진입을 확인한 최종21검사로 대체했습니다. 공개 입력 생성 시 상위 input_id만 변경해 원 program ID와 불일치했던 준비 오류도 별도 실패로 보존하고, 원 연결 ID를 유지한 새 권리 판본으로 바로잡았습니다. 중간 검증문 위치 오류를 확인해 두 번째 실행은
소유 pytest만 SIGTERM(-15)으로 조기에 중단했고, 마지막 단계는 새 namespace에서 완료했습니다.
원 실패/중단 로그·출력과 기존 비공개 결과를 덮어쓰지 않았습니다.
전체 backend/build/브라우저·전체 최소/최대 API 조합은 이번에 실행하지 않았습니다.
기존512잎528,002/524,288bytes hold는 유지하며 이번 경로로 전체 최대 지원을 주장하지 않습니다.

## 판단과 다음 단계

native **gpt-6.1-sol/xhigh**, turn_context 2026-10-26T13:42:16.670Z,
원 LF SHA `b298f703507cb4e2f149f84e7121e2fcaffb311521112a827960b0bd89547517`·재귀 CLI0에서 설계/검증했습니다.
기존 자체 합성 자료/계수와 명시 공개 선언만 재사용했습니다. 새 외부 농업·기상·시장 자료 채택0이며
G0–G4=not_assessed/R2=not_approved, 실제 품종/독립 국내 측정0건과 생산·수익 예측은 후속입니다.
현재5175 제작 외형은 유지하며 새 계산 데이터는 아직 화면에 연결하지 않았습니다.

다음은 **새 strict SDK → 같은 저장 상태의 실제 잎·줄기3D**입니다.
SDK는 새 닫힌 index/DTO/raw source/notice·code/권리·원 vector/단위/ID/부착/exact 시각과 점 전후 phase를
검증하고 부분·변조·오래된 요청/취소를 거부해야 합니다. 기존 SDK 통과를 새 판본 수용으로 세지 않습니다.
앞선 export0.75–1.5h 예상은 실제 수용으로 대체하며 SDK1–2h+독립0.5–1h, **1.5–3집중시간**을 잠정 남깁니다.
실제 3D/브라우저는 그 뒤2.5–4.5집중시간의 낮은 신뢰 작업량입니다. 이는 달력 완료일 약속이 아니며
새 계약/실제 표시 상태에 따라 갱신합니다. 한 작기/수확·자원/Decimal 경제·거시/수급·자율 비교·전체 제품 완료일은 미정입니다.
