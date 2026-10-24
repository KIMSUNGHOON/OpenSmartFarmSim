# 제거 전·직후·다음 구간 저장과 계산 없는 조회 — 2026-10-24

상태: **불변 저장/원 상태 조회의 소프트웨어 수용**.
[계약](../contracts/growing-geometry-removal-artifact-v1.md),
[producer](../backend/app/crop_growing_geometry_removal_artifact_producer.py),
[reader](../backend/app/crop_growing_geometry_removal_artifact_reader.py),
[시험](../backend/tests/test_growing_geometry_removal_artifact.py),
[기계 증거](artifacts/growing-geometry-removal-artifact-20261024.json),
[12root 장부](artifacts/growing-geometry-removal-artifact-20261024.csv).
새 strict export/SDK·동일 상태3D와 현재 farm/관문 승인은 후속이다.
[현재 사용자 화면](http://localhost:5176/growing-geometry-replay.html)은 기존 합성32초 재생을 유지한다.

## 저장한 내용과 구분

원 program·명시 현재 C 분포/제거 C·용량/현열과 rights/epoch/격자를 받는다.
parent는 사건 시점까지만 전진하고, point/post-context와 새 engine의 각 CP를 저장한다.
원 parent의 미사용 사건 후 구간은 계산하지 않는다.
parent request/정규 program/context/seed, point 입력/결과와 post program/context/seed/snapshot,
원4profile raw bytes/metadata·Clear BSD notice와 각 CP를 기존 내용 주소 파일 저장소에 보존한다.
원 source/코드/권리/모든 bytes를 대사한 뒤 완료 root를 마지막에 저장한다.
새 서비스/DB/키·기존 모델/코드/산출물을 변경하지 않았다.

전체 count+2개의 시점을 `before_removal`→`after_removal_before_next_step`→`post_removal_interval`로 구분한다.
제거 직전/직후는 원 global index·정확 Fraction 시각이 같고 phase/CP·현재 목록이 다르다.
새 시각을 만들거나 면적/성장 변화량을 확대하지 않는다.
reader는 양쪽 prefix·원 source/context/point/CP·단위/형상·장부/기록 수지와 현재 파일 정책을 검사하고 원 값을 복사한다.
사건 전 point/segment 장부는 null이며 사건 후의 과거21/사건/새21장부를 분리한다.
원 ID에 맞는 초기 영수증과 curve SHA·현재 a/A/기후/상태·D0도 보존한다.

입력의 rights는 자체 합성 선언이며 실제 자료/과학 관문 승인이 아니다.
신뢰한 private root와 현재 파일 정책의 경계다. 임의로 전 graph를 재해시한 결과의 진본/방정식 정확성이나
실제 tenant/farm 현재 권리·서명 custody를 증명하지 않는다.
원4profile의 참고 출처/권리 metadata와 notice를 유지하며 원 논문/PDF·도표 전문을 복사하지 않는다.

## 통과한 검증과 실패 기록

- 모듈 부재 RED 뒤49통과/2실패가 있었다. 두 반례가 분수 시각의 분자를 이미 있던1로 바꿔 실질 변경이 없었다.
  이를2로 고치고 원 source/post CP·단위·사건 장부/코드·late policy와 데이터 대사를 보강했다.
- **신규80+기존 고정 목록 artifact89=169검사**가50.05초에 통과했다.
  이후 앱 코드는 바꾸지 않고512잎 저장/조회 검사1개를 추가해2.40초에 통과했다.
  고유 수는 **81신규+89관련=170**이며 중간78/51은 합산하지 않는다.
  여섯 조건의 원 CP bytes/DTO·전 수량/ID/초기 영수증·단위/각 장부/같은 시각의 두 phase,
  초기/완료 사건·동시 제거·분수 dt와 동일 입력/다른 디렉터리의 같은 root를 확인했다.
- 잘못된 wrapper/권리·단위·형상/phase/시각/목록/해시/현재 원본·코드·진단/수지·index·raw JSON을 거부했다.
  원 source나 post CP를 새 blob/root로 다시 해시해도 원 결속/형식이 달라지면 거부했다.
  현재/늦은 파일 정책 철회, producer/reader의 늦은 code 변경·부분 쓰기/domain hold는 완료 반환을 만들지 않는다.
  JSON view는 복사본이며 reader에서 모든 계산 진입점/put을 차단해도 조회가 통과했다.
- 원512잎→511잎의 실제 계산 결과를3시점으로 저장/조회했고 원 index에 맞는 영수증·ID/1130상태를 보존했다.
  CP256KiB/DTO2MiB와 기존 파일 수/디렉터리 한도를 바꾸지 않았다.
- 별도 producer/fresh reader의 **12root/216시점**에서 원 모델 CP bytes·DTO SHA와
  **24,264상태 수량·936잎 나이/면적 수량**, 모든 투영/장부·권리/영수증/시각을 대사했다.
  여섯 zero-outflow 조건×한 잎/동시 두 잎, dt1⁄8초/count16·사건7의 합성2초 범위다.
  각18시점 중8개는 사건 전이며 같은7⁄8초의 사건 후1개와 이어지는9개 구간을 보존한다.
- fresh는 reader import 전에 네 artifact reader/IO 외 모든 `app.crop_*` import를 금지했다.
  계산 모듈 import 시도/생장·point·재개 호출0, DB 접속/CLI/network/파일 쓰기 시도0이다.
  공유 파일 transport가 가져오는 DB 라이브러리 자체의 import0을 주장하지 않는다.
  원 **420파일 metadata/bytes·FD**를 보존했다. 원 redistribute=False도 그대로다.
- 첫 fresh 하네스는 출력 상위 폴더를 준비하지 않아 storage hold로 끝났다. blob/root/bundle은 생성되지 않았다.
  원 실패/log를 유지하고 소유한 private 상위 폴더를 만든 뒤 같은 코드의12root/216시점 검증을 통과했다.

최종169 guard는51.101초·최대PID109,502,464bytes/합산488,747,008bytes,
512 경계는3.564초·78,979,072/454,307,840bytes,
최종 fresh는53.187초·78,979,072/486,629,376bytes였다.
512MiB/PID·1GiB 소유+보호 합산·0.25초 표본/600초/로그4MiB를 유지했다.
모든 phase의 원3,545항목·소스/보호4root·FD4→4/소유 잔류0을 확인했다.
Windows/전체 host 용량은 위 관측 범위 밖이다. 전체 backend·hosted CI·브라우저/사용자 적용은 이번 자식에서 실행하지 않았다.

native Codex CLI `gpt-6.1-sol/xhigh`, turn_context2026-10-24T12:00:50.215Z,
원 LF SHA `2b1c3a28afad9b4d28df6a0cbe9748d7d632acc4f6b38dfcefe90d8dd4bb47d2`·재귀 CLI0으로 판단했다.
새 농업 계수/자료·관문을 채택하지 않았다. 원32초/nonzero outflow 결과도 변경하지 않았다.

## 다음 단계와 일정

다음은 **별도 자체 합성 공개 선언의 export/strict SDK**다.
기존 private redistribute=False를 바꾸지 않고 새 원 요청/graph를 만든다.
원16source/notice·root·모든 pre/event/post CP/DTO bytes·정확 phase/시각·고정 root/index 지문과 단위/권리를 보존한다.
부분 실패 때 완료 index를 만들지 않고 exporter/SDK에서 생장 재계산0·늦은 변경/권리/변조·취소를 검증한다.
SDK의 원 leaf ID/현재 A를 사실적 renderer에 연결할 때 제거 후에도 원 attachment를 ID로 선택한다.
같은 시각의 전/후를 timestamp만으로 합치지 않으며 원 phase/index·표/그래프·3D를 함께 이동한다.
제작 줄기/pose는 명시하고 임의 과실·키/수확이나 중간 성장 상태를 추가하지 않는다.

export/SDK 자식은 계약/선언20–35분+export/SDK 재사용45–75분+변조/fresh·타입40–70분+기록15–25분,
합계 **120–205집중분**의 낮은 신뢰 추정이다. 3D/브라우저/사용자 적용은 그 뒤 별도 분해한다.
공개 benchmark의 horizon을 늘리면 새 실제 계산/독립 수지 검증을 먼저 통과해야 한다.
전체 작기/복수 사건·출현/공급·생산/자원/Decimal 경제·거시/수급·자율 후보 비교와 current farm/CLI G1 종단 간은 남는다.
국내 원 측정/미사용 독립 작기0·첫 품종 미확정·R2/G0–G4와 전체 완료일 미정을 유지하며 자료 획득은 병행한다.
