# 합성 면적·기후 계산의 불변 저장과 생장 계산 없는 조회 — 2026-10-24

수용 범위는 [연속 계산](crop-growing-geometry-continuation-20261024.md)의 원 상태를 저장하고 조회하는 연구용 소프트웨어다.
[계약](../contracts/crop-growing-geometry-artifact-v1.md), [기계 증거](artifacts/growing-geometry-artifact-20261024.json).
새 계산의 사용자 3D 연결은 다음 단계이며 현재5176의 기존 잎 생장·제거 화면은 그대로다.

## 산출물과 경계

- [producer](../backend/app/crop_growing_geometry_artifact_producer.py)는 기존 CAS/현재 POSIX 파일 정책을 재사용한다. 원 wrapper/request/정규 program/context/seed·초기 영수증/D0·4프로필/notice와 원102checkpoint bytes를 보관하고 완료 root를 마지막에 반환한다. 새 DB/queue/service·원 모델 변경은 없다.
- [reader](../backend/app/crop_growing_geometry_artifact_reader.py)는 저장된 leaf ID/a/A·114상태·7derived·21누적량/수지와 출처·코드 지문을 복사한다. curve/SLA/기후식으로 다시 계산하지 않는다. metadata normalization·단위/형상·해시/prefix·정확 grid와 기록된 QC만 검사한다.
- 자체 합성 epoch+원 float elapsed와 `index*Fraction.from_float(dt)`를 함께 보존한다. dt=1/3의3걸음은 exact<1초/원float=1.0을 구분하며 ISO microsecond로 반올림하지 않는다.
- own input 권리 선언·현재 파일 정책을 전후 확인한다. redistribute=False를 보존하며 공개 재배포 허가로 해석하지 않는다. 이는 실제 farm SourceRecord/현재 테넌트 권한 조회나 서명 custody가 아니다. 신뢰한 private root가 전제이며 자가 재해시한 임의 root의 진본/방정식을 증명하지 않는다.
- 4프로필은 기존 raw JSON과 출처/권리/검토 metadata를 그대로 보존한다. 기존 Clear BSD notice도 포함한다. 원 논문/학위논문 fulltext·그림·표를 새로 수집/재배포하거나 실제 품종 계수를 채택하지 않았다.

## 통과한 검증

[집중 시험](../backend/tests/test_crop_growing_geometry_artifact.py)은 최종 **89 passed**다. 이전80개는 중간 검사이므로 합산하지 않는다.
원6프로그램의17시점씩 모두 원 checkpoint bytes/sample/state·leaf IDs/나이/면적·21장부/단위/권리/원시각과 대사했다.
동일·별도 디렉터리의 같은 root, 분수 dt, caller copy, 초기 요청 면적과 canonical 영수증의 구별,512잎/1,132상태를 확인했다.
권리 거부6종은 생장 전에 거부했고, malformed/초과/비정규 JSON·단위/형상·root/원본/재해시 checkpoint 변조·현재/늦은 파일 정책·늦은 코드·부분 쓰기/수치 hold는 완료 반환을 막았다.

실제 별도 producer→독립 readonly reader에서 **6개 root/102 checkpoint·DTO·17,136 상태/장부 수량**의 원 bytes/값이 일치했다.
reader는 생장/초기화/재개 모듈을 import 금지하고 DB 연결·CLI/하위 프로세스·네트워크·모든 파일 쓰기를 차단했다. 시도0, FD 보존, bundle와 모든 blob의 bytes/metadata 보존을 확인했다.
이는 독립 생물학적 수치 검증을 새로 수행한 결과가 아니다. 기존 계산의 독립 Decimal 근거는 앞선 계산/재개 기록에 남아 있다.
소스 지문27개/문서 상대 링크3,367개와 새 Python3파일의 구문 검사도 통과했다.
private handoff bundle은937,126bytes, SHA256 `1bf228ff2056927ae5d87b64cb309f1db2ef6a0fde14a02b8800b667db7ca536`다.

최종 focused wall30.167초·최대PID111,771,648bytes/소유+보호 합산544,088,064bytes였고,
fresh producer16.960초/합산484,319,232bytes·reader4.826초/합산455,266,304bytes였다.
기존512MiB/PID·1GiB 합산·600초 상한을 바꾸지 않았다. 모든 phase에서 보호4root/원2,966항목/원 source·FD4→4/소유잔여0을 확인했다.
Windows browser 메모리는 이 측정에 없고 전체 WSL/host 용량이나 운영 SLA를 주장하지 않는다.

첫 RED는 새 모듈 미구현 import 실패였다. 첫 core는 시험에서 기존 CAS의 필수maximum 인자를 누락해6실패/7통과였고 시험 호출을 수정했다. 뒤80통과 후 context 합계/최종 코드 fence와 경계9개를 보완해 최종89통과했다.
초기 실패의 원 로그/terminal은 보존했다. 새 hosted CI/전체 backend/browser는 이 단계에서 실행하지 않았다. 기존 UI·수치 코드가 바뀌지 않아 앞선211검사를 중복 집계/재실행하지 않았다.

## 설계 판단과 다음 순서

기존 CAS를 사용하고 계산하는 writer/계산하지 않는 reader를 분리했다. 버전 고정 단위/shape는 reader의 plain schema로 검사하며 생장 구현을 import하지 않는다.
코드 closure25파일을 원Context의 R/Q/15component 지문에 대사한다. 원 component 목록 밖 transitive fruit_allocation도 별도로 pin한다.
고정 상한 안의 전체 graph 검사 비용을 수용하고 캐시/새 서비스는 추가하지 않았다. 신뢰 root·파일 정책의 범위를 계약에 명시했다.
정확 모델은 현재 native Codex CLI `gpt-6.1-sol/xhigh`, turn_context2026-10-24T07:21:50.723Z,
원 JSONL line LF 포함SHA `117932c945aeb6b090c682f1ec7416c52fed679ae6ffe3e0af1b5e2ee5162fdf`로 확인했다. 재귀 CLI0이다.

다음은 권리/지문/notice를 보존하는 strict export/SDK→기존 사실적 renderer의 stored leaf ID/현재A·동일시각3D/표/그래프다.
이번 private own fixture의 redistribute=False를 바꾸지 않고, 필요한 공개 전달 범위는 별도 자체 합성 선언으로 검토한다.
32초의 실제 변화량을 과장하거나 기존24시간 줄기와 같은 생장 과정이라고 결합하지 않는다. stem/pose/attachment는 별도 제작 asset임을 명시한다.
정확 제거/출현·공급/자원·생산/경제/자율 선정은 뒤따른다. 실제 원 측정·미사용 독립 국내 작기0/첫 국내 품종 미확정·R2/과학 관문과 전체 완료일 미정은 유지한다.
