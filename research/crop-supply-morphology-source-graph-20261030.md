# 저장 형상 strict SDK의 원본 연결 검증 수용 — 2026-10-30

strict SDK의 원본 파일·Context/체크포인트·조달 전후 지문 연결 검증을 수용했다. 새93검사·전체 타입 검사·독립 번들/실행에서 실제101파일·6Context/33CP/5증거·38프레임과 원6,208scalar의 지문을 대사했다. **전체 SDK와 새3D 화면은 미완료**다. 상세 상태/기관/clock/형상·장부 수치 검증과 HTTP/취소/latest/방어 복사가 남는다.

[계약](../contracts/supply-morphology-source-graph-v1.md), [기계 판독 증거](artifacts/crop-supply-morphology-source-graph-20261030.json), [원 증거 복원](crop-supply-morphology-sdk-wire-20261030.md), [이전 native 증거 정정](crop-supply-morphology-sdk-wire-native-evidence-20261030.md), [구현](../web/src/supplyMorphologySourceGraph.ts), [계획](../tasks/plan.md), [TODO](../tasks/todo.md).

## 확인한 범위

기존 자체 public fixture의 원305181/1024초→512초·101파일/14,197,795bytes를 그대로 읽었다. 원 모델99/계산·저장102지문·입력/권리·프로필·시간 격자/결과는 바꾸지 않았다. 원 비공개 false 자료를 공개 자료로 바꾸거나 새 생장 계산을 실행하지 않았다.

호출자가 독립적으로 신뢰한 root/index anchor와 설치된102code/4profile/NOTICE·exporter/writer 지문을 대조한다. 다운로드한 index가 자기 승인을 제공하지 않는다. 닫힌 source/root/index/권리·초기 crop/stem 결속과 선택한 원 상태를 검사한다. 각 blob/DTO는 원 byte 길이·해시와 맞아야 하며 명세 밖 경로·중복·도달하지 않는 파일·누락/역순·개별/전체 용량 초과는 거부한다.

6개 Context의 원 root CP·99code·평면 receipt 참조와 genuine seed, 원 분수 시작/다음 격자·잔여 시간을 대사했다.33개 CP의 초기/연속 단계·원 sample과 seed/prefix/hash·event/cursor/정확 UTC/phase를 확인했다.5개 조달 증거는 바로 앞 Context/CP·unadopted 후보·입력/계산 지문·채택 후 metadata/기존 형상 원점·일정의 한 번 소비·before/after prefix와 연결된다. 원 binary64와 분수 시간을 유지하며 값의 JSON 재직렬화로 Python 지문을 재생성하지 않는다.

38개 DTO/프레임의 snapshot·metadata·frame/state 해시는 같은 CP 또는 조달 전 dense snapshot과 같다. 원 순서와 cursor가 연속이며 같은 조달 시각의 before가 after보다 앞선다. 원6,208scalar의 바이트를 대사한 것이며, 모든 기관/clock·형상/계정의 상세 산술 검증이나 생물학 검증을 완료한 뜻은 아니다. 반환은 `source_graph_only_quantities_pending`이고 승인된 UI replay를 반환하지 않는다.

## 검사와 독립 실행

- 93검사는 정확 수/원 binary64·문자열 한도21, 실제6Context/33CP 및 재해시 CP/카운터/순서22, 실제5개 material과 재해시 채택 metadata·stale CP10, 전체 파일/프레임·재해시 index/root/권리/코드·잘못된 wire/UTF8·원본 변조·유효 hold·경로/추가/용량/취소40으로 구성한다.
- 독립 새 Node 프로세스의79,325byte 번들에서101파일/62blob·38원 프레임과5개 receipt를 원 Python 기준에 대사했다. 같은 실제 파일을 한 번씩 읽었으며 원 file/DTO/NOTICE byte·hash와 public101파일 메타데이터를 보존했다. 거짓 공개 grant는 index1회 읽기 뒤 source 읽기 전에 거부됐다. 외부 import가 없는 번들에서 fetch 차단 계측0회였으며 생장식·DB·CLI 실행은 없다.
- 유효한 보류 결과도 원 사유를 보존한다. 최초 prototype은 hold prefix를 대문자/underscore로만 제한했으나 기존 Python 저장 규칙은 colon 앞 `_HOLD` suffix를 요구한다. 실제 전체 graph를 재해시한 유효 `clock2_HOLD` 사례의 RED 후 원 규칙으로 수정했다. 원 상태·관문을 승인으로 바꾸지 않았다.
- 원 격자 metadata5필드와 첫 compatible→repeat 정책 전환을 native 정의에 맞췄다. signed exact 문자열4096자 한도는 minus를 포함한다. 처음 거부/길이·타입 사례의 실패 기록과 prototype 결과를 보존했고 최종93검사는 skip 없이 통과했다. 최초 전체 타입 검사에서 발견한 테스트의 ArrayBufferLike 문제도 실제 복사로 수정했다.

## 실제 시간과 자원

| 최종 단계 | Guard wall | 관측 |
| --- | ---: | --- |
| 고유93검사 |26.481초 |4파일/93 passed |
| 전체 타입 검사 |8.753초 |최종 source/전체 tsconfig |
| 별도 build |1.488초 |79,325bytes |
| 독립101파일 읽기 |3.544초 |내부 정상 처리 약2.344초 |
| 원 source/GUI 보존 |2.256초 |선행368source/1output·정정 포함 |
| 원 CAS/입력 보존 |1.227초 |124 CAS/32입력 metadata |

독립 읽기는 파일 callback을 사용한 로컬 코드 실행이다. HTTP/실제 브라우저·제품 응답 지연 수용이나 전체 작기 성능이 아니다. 전체 frontend/backend suite와 새 HTTP/API/DB/worker/브라우저를 실행하지 않았다. 작업 시작 HEAD `e8c17c8872fab48af594c5c0d8fc43a36f2960ba`의 실제 CI API는0runs였다. 로컬 검증을 hosted CI green으로 표시하지 않는다.

원600초·PID512MiB/합산1GiB·로그4MiB guard를 유지했고 각 수용 단계의 source 보존·controller FD4→4/소유 자식0과 보호5175를 확인했다. 네이티브 TypeScript의 검사 프로세스만 `GOMEMLIMIT=256MiB GOGC=30 GOMAXPROCS=1`로 실행했다. 최종 타입 검사의 PID531,111,936bytes/합산569,716,736bytes는 원 상한 안이며 여유가 작다. 상한·패키지/lock·tsconfig/CI·원 운영 기반은 바꾸지 않았다.

원 private/public CAS 두 저장소124파일과 원 입력32항목의 byte/hash·identity/mode/owner/group/mtime/ctime을 대사했다. 원 private:false/public:true는 그대로다. 기존 private:false132blob·봉인 GUI4,865파일·이전 두 공개 출력9,464파일/경계·5175 HTTP200도 확인했다. 새 화면을 기동한 증거는 아니다.

## 다음 한 단계

다음 `stored-quantities`는 원106+3n+m+2h 배치·프로그램/기관/ID/부착·면적/길이/탄수화물·birth/정확 clock·형상 원점/부족분과 전체 계정의 단위·잔차/예산을38프레임 전체에서 대사한다. source graph가 읽은 CP/조달 전후와 원 wire/hash를 사용하며 새 생장 계산이나 계수를 넣지 않는다. 그 뒤 실제 HTTP/취소/latest/방어 복사와 full SDK 수용을 거쳐 같은 저장 상태의 실제 잎·줄기3D를 연결한다.

전체 SDK 조회 실측 뒤 UI 공수를 갱신한다. 이번2.344초를 브라우저 처리 시간·화면 완료 날짜로 바꾸지 않는다. 지역/실제 단일 품종·한 작기·생산/자원·Decimal 경제/거시/수급·자율 비교/제품 farm/worker 연결과 독립 국내 품종 자료0·권리/미래 작기·대응 후보 비교의 외부 의존성은 남는다. 자료 확보일·전체 완료일은 미정이다.

이번 native 증거는 `CODEX_THREAD_ID`와 일치하는 session metadata/실제 workspace 및2026-10-30T12:05:07.656Z 문맥의 `gpt-6.1-sol/xhigh`를 직접 대조했다. 재귀 CLI0회이며 원 source/검증/출력 지문을 기록했다. G0–G4 `not_assessed`, R2 `not_approved`, 전체 goal active/incomplete다.
