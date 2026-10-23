# 자동 잎 출현 결과의 무계산 조회 — 2026-10-24 KST

[계약](../contracts/crop-leaf-appearance-reader-v1.md)의 manifest/frame reader를 소프트웨어 연구 범위에서 수용했다.
[검사·원본/fresh·자원 증거](artifacts/crop-leaf-appearance-reader-20261024.json).
현재 사용자 화면은 기존 job이며 이 새 appearance root의3D/제품 실행 연결은 후속이다.

## 산출물과 검증

- [reader](../backend/app/crop_leaf_appearance_artifact_reader.py)는 원 source/준비/생성 program과 내부 population·원 stem의
  닫힌 형식·모델/33코드/권리·초기/최종 state/UTC를 대사한다. 초기 상태는 첫 저장 결과의 clock/area anchor 영수증으로 확인한다.
  원 줄기에 저장된 ID·정확 출현 초/열적 나이와 정책의 정수 위치를 대사하며 출현 시각·기온 적분·면적식을 계산하지 않는다.
- 신규87/관련349=고유436검사 통과. 재해시한 outer/준비·초기/정책/프로필/파생·생성/계산 혼합과 누락/후기 변경을 거부했다.
  새 reader는 반환 전 전체43blob을 재확인한다. 중간에 선택하지 않은 결과가 바뀌는 경우도 거부한다.
- mixed 초기 정책/redistributeFalse·새 영양 잎0·정수 수량 표현·중간7200초에서의 독립 초기 잎 시계
  (base10°C/나이1°Cday)·512잎/2MiB 이내 frame을 확인했다. 새 관측/품종 기본값은 도입하지 않았다.
- 실제 root `77c3ffcab5f02b0dab132530a3f4c278db07dd18a258633bb4b148c18f5e423a`와43파일 metadata를 보존했다.
  실제 새 DTO12개·3→5잎/47면적과 나이가 원 manifest/결과/binding/UTC 및 앞 단계의 독립 Decimal100 원47개와 같다.
  내부 root `94224ddcac4cdbb46eb2ba4cd1318fdaf71c14550128e570ce90fc60e3334285`도 보존했다.

## 별도 프로세스와 수정

새 프로세스는 허용된7개 crop reader/IO 모듈 외 모든 crop 모듈 import를 차단했다.
기존19개 수치 모듈을 포함해 생장/준비/producer·출현/기온/면적 import0을 확인했다.
DB 연결·외부 명령과 open/network/process audit를 차단한 상태에서12frame을 조회했다.
DB/CLI/파일쓰기0·FD 보존·43파일 metadata 불변이다. Python 검증 자식의 실행은 Codex CLI 재귀 호출이 아니다.

최초 모듈 부재 RED 뒤82검사/fresh가 통과했다. 검토 중 manifest 권리의 숫자1이 bool과 같게 처리되는 반례와
원 stem17코드/outer33코드 대사 누락을 각각 RED로 재현했다. canonical 권리 대사와 원 stem 지문 대사로 수정했다.
최종87에는 두 반례가 포함되며 과거82/86·중간 단계를436에 합산하지 않는다.

최종 신규/관련/실제 fresh 단계는 각각21.922/94.306/2.072초였다. 최대 WSL 합산 RSS는475,914,240bytes로
PID512MiB/합산1GiB·600초·0.25초 표본·4MiB 로그 안이다. 원2,481항목/현재 소스·보호3root를 보존했고
소유 잔여0·FD4→4였다. 전체 backend/new hosted CI/new browser·새 export/SDK/사용자 적용은 실행하지 않았다.

판단은 실제 현재 CLI `gpt-6.1-sol`/`xhigh`의2026-10-23 15:04:16.751Z turn_context를 확인한 상태에서 수행했다.
원 LF 포함 SHA는 위 증거에 보존했으며 recursive CLI 호출은0이다. 기존 UI/runtime·DB/키는 변경하지 않았다.

## 다음 단계와 외부 의존성

다음은 **이 새 root의 명시 재배포 권리를 검사한 public export → strict SDK/같은 UTC3D**다.
기존 geometry/재생 화면과 원 stem DTO를 재사용하며 새 root/source/준비/정책·생성 선언의 의미를 보존한다.
검증된 원 면적·잎 수/ID·UTC만 표시하고 기존3→6잎 예제의 상수/표식을 새 계산에 재사용하지 않는다.

첫 export는 계약/권리·해시0.25–0.5h + 원20파일 작성/보존0.25–0.5h + fresh/거부·기록0.5–1h의
**1–2집중시간** 낮은 신뢰 작업량이다. 기존17파일 export와 새436검사/실제43blob 재사용이 전제다.
그 뒤 SDK/화면1–2h, 실제 browser/사용자 URL·검증1–2.5h의 잠정 범위이며 분해 후 갱신한다.
이 시간은 전체 제품 완료일이 아니다.

실제 품종·독립 국내 작기 확보는0이다. 자료 확보는 개발과 병행하며 G0–G4/예측·미래 마진·추천을 보류한다.
새 program의 farm/현재 권리·서명/worker 적용과 관리/생산/자원/Decimal 경제·거시/수급·자율 비교,
R2/첫 cold 경고가 남는다. 전체 완료 날짜는 자료 확보 일정이 없어 미정이다.
