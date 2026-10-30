# 공급 제한 형상 반복 결과 저장·조회 수용 — 2026-10-30

수용된 같은 family의 실제 Context6개·원 체크포인트33개를 불변 저장하고, 출현 전후를 포함한38시점을 별도 프로세스에서 재계산 없이 조회했다. 집중49검사·별도 전체 그래프 변조16사례·원 자료/GUI/WSL 보존을 확인해 이 소프트웨어 경계를 수용한다. 새 결과의 웹 연결·전체 작기·실제 품종·수확·구매·마진·추천 검증은 후속이다.

[계약](../contracts/crop-supply-morphology-artifact-v1.md), [기계 판독 증거](artifacts/crop-supply-morphology-artifact-20261030.json), [선행 반복 수용](crop-supply-morphology-repeat-20261030.md), [계획](../tasks/plan.md), [TODO](../tasks/todo.md).

## 저장된 범위

원 저장 시작305181/1024초→원512초의 합성 경로다. 시작 전의 누락된 시점을 채우지 않았다. 구간 budget1의 실제 실행으로 각 확정 endpoint의 genuine CP 바이트를 수집했고, 최종 Context/CP는 선행 전체/분할 결과와 같다. 모델99source·계수·격자·허용 budget을 변경하지 않았다. 기존 타입을 가장하지 않고 공개 복원 API로 실제 Context/CP를 복원했다.

저장소62파일/10,363,971bytes에 원 source CAS·프로필·라이선스 고지·요청/프로그램/초기 상태·선행 Context·원 Context/CP·조달 증거를 보관했다. root는45,785bytes이며 마지막에 게시한다. 최종 root는 `a5d9d516d2cf5d2a2bc3cca2e91156bfe82301a932521e1e3df5994009c6a220`다. 같은 입력·코드의 재시도에서 root와 모든 파일 메타데이터가 같다. 게시 전 최종 검사 실패는 완성 root를 남기지 않으며, 같은 재시도로 완료할 수 있다.

38시점은 원 CP33개와 CP가 없는 조달 전 dense5개다. 같은 조달 시각에서 before가 after보다 앞선다. 같은 UTC 원점·분수 초·기관 ID·부모·event/cursor/prefix와 A/L/C·출현 기준 시계·형상/유입 원점·부족분·전역 장부를 보존한다. 원 벡터6,208scalar·잎358행·절간356행이며 없는 폭·pose·과실 성장·수확을 계산하지 않았다.

## 통과한 검증

- [생산자](../backend/app/crop_supply_morphology_artifact_producer.py)는 genuine Context/CP를 검증한 뒤 기존 POSIX 저장소로 원 바이트를 쓴다. root-last·동일 재시도·부분 저장 후 복구와 입력/현재 코드/권리 조건을 확인했다.
- [조회기](../backend/app/crop_supply_morphology_artifact_reader.py)와 [좌표·시계 변환](../backend/app/crop_supply_morphology_artifact_projection.py)은 생장 모듈을 import하지 않는다. 별도 프로세스에서38시점 전체와 출현 기준 시계714개를 원 증거에 대사했다. 생장 import/RHS·DB·CLI·네트워크·쓰기0, 원 source/store 바이트·메타데이터 보존을 확인했다. before 원 증거5개도 선행 수용 packet의 지문으로 검증했다.
- 집중49검사는 실제 보류 prefix 저장·원 CP 바이트·재시도/부분 실패·재해시 scope/관문/순서/완료/권리/단위/상태/장부/시계/부족분·현재 코드/접근권/늦은 파일 교체와 표현/시계 단위를 검사했다. 파일과 이미 불러온 QC 코드가 다른 반례2개는 실패를 보존하고 수정한 뒤 전체49검사를 통과했다. 현재 파일은 매번 새로 읽으며 입력·권리·프로필을 캐시하지 않는다.
- 실제 전체38시점 그래프의 별도16변조 사례에서 구간 역순/누락/중복·Context/원 CP·형상 원점/부모·일정·조달 증거/권리/추가 필드·선행 바이트/프로필·frame/byte cap 위반을 거부했다. 기존 코드 판본의 root도 현재 코드에서는 hold한다. 부정 사례 복사본은 정리했다.
- 기존242source/1output closure·원 자료·private:false132blob·봉인 GUI4,865파일·기존 export 두 출력9,464파일/경계·보호 프로세스를 보존했다. 보존 단계에서 기존5175 HTTP200을 확인했다. 새 API/DB/worker/UI를 기동한 증거는 아니다.

Root/Context/response2MiB·CP512KiB·source16MiB·store64MiB/4096파일·inventory/frame512·sample scalar32768 한도를 유지했다. Context 최대2,034,607bytes는 한도에 가까우며 전체 작기나 최대 inventory 지원을 뜻하지 않는다.

## WSL과 코드 판본

| 단계 | Guard wall | 관측 |
| --- | ---: | --- |
| genuine CP 수집1 | 370.288초 | 실제 후속3출현·중간 저장 |
| genuine CP 수집2 | 359.756초 | 원512초·총33CP·선행 최종 바이트 일치 |
| 현재 코드 집중49검사 | 211.870초 | pytest49 passed |
| 현재 코드 생산·재시도·첫/끝 조회 | 289.283초 | 생산35.109초·재시도33.631초 포함 |
| 별도 전체38시점 조회 | 65.019초 | 조회63.399초·재계산/쓰기0 |
| 별도 전체 그래프 부정16사례 | 6.772초 | 모두 hold |
| 원 자료/GUI 보존 | 2.247초 | 통과 |

이는 검증 공수이며 제품의 최초 대기 시간·전체 처리량·완료일이 아니다. 현재 조회기의 전체 순차38조회는 약63초로, 최종 제품의 조회 지연 수용과 별도다. 생산 검증 전 원 권한 준비의 기존 초기 RHS1회와 CP33개의 현재 RHS 검증33회를 별도 계측했다. 저장 생산·조회·재시도 중 RHS·과거 적분/조달/초기화는0회다.

각 단계는 원600초·PID512MiB/합산1GiB·로그4MiB 안에서 종료했고 controller FD4→4·소유 자식0을 확인했다. 현재 생산 단계 PID peak227,295,232bytes/합산265,682,944bytes다. 준비 스크립트의 최초 들여쓰기 오류는 계산 전 발생했으며, 당시 잘못 명명된 helper12검사 단계를 genuine 수집 증거로 세지 않았다. 보완 전 prototype root/검증은 역사 기록으로 남겼고 현재 수용은 보완 후 코드/root에 한정한다.

전체 backend/frontend suite와 새 브라우저 검사는 실행하지 않았다. 작업 전 HEAD `4ce97ca7bd70564ca3a3ea0e5cd74cb8057b730e`의 실제 CI API 조회는0runs였으며 로컬 검증을 CI green으로 보고하지 않는다.

## 다음 산출물과 남은 의존성

이 자료의 `redistribution_authorized`는 **false**다. 자체 합성 fixture여도 기존 판본의 권리를 바꾸어 public export하지 않는다. 다음 export/strict SDK 검증에는 새 권리 선언·판본에 따른 재배포 허용 자체 합성 입력에서 실제로 생산한 결과가 필요하다. 기존 false 자료는 접근 정책에 따른 내부 조회 범위로 유지한다. 이후 같은 저장 상태를 실제 잎·줄기 mesh/표/그래프·원 시각 재생에 연결해 브라우저로 검증한다. 새 결과는 아직 웹에 반영되지 않았다.

먼저 허용 fixture와 export/SDK 계약·실제 응답 크기를 확인한 뒤 브라우저 연결 공수를 재산정한다. 이전180–300분은 미수용 초안이다. 독립 국내 단일 품종 자료·계수 채택0, 자료별 접근/권리·단위/QC·판본/available_at·독립 미래 작기·후보 비교는 병행 외부 의존성이다. 실제 자료 확보일·전체 제품 완료일은 미정이다. 로컬 연구 복사본의 권리 검사와 외부 농장 권리 철회·서명/실행 custody·제품 farm 연결을 구분한다.

실제 native Codex CLI `gpt-6.1-sol/xhigh`에서 조사·설계 판단/출력 지문을 기록했고 재귀 CLI0회다. G0–G4 `not_assessed`, R2 `not_approved`, 전체 goal active/incomplete를 유지한다.
