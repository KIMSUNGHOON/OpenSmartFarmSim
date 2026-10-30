# strict SDK의 원 조달 증거 복원 수용 — 2026-10-30

저장된 공급 제한 형상 결과를 브라우저에서 읽을 strict SDK 중, 원 조달 증거의 바이트 복원부를 수용했다. 새43검사/기존 wire8검사=고유51검사·전체 타입 검사·별도 빌드/독립 실행을 통과했다. **전체 strict SDK와 새 저장 상태의 사용자3D 연결은 아직 미완료**다.

[계약](../contracts/supply-morphology-sdk-wire-v1.md), [기계 판독 증거](artifacts/crop-supply-morphology-sdk-wire-20261030.json), [Python 기준](fixtures/supply-morphology-receipt-wire-20261030.json), [선행 export](crop-supply-morphology-export-20261030.md), [구현](../web/src/supplyMorphologyReceiptWire.ts), [계획](../tasks/plan.md), [TODO](../tasks/todo.md).

## 복원한 범위

선행 수용의 자체 public fixture38시점/101파일·6Context/33CP를 그대로 사용했다. 앞선 genuine seed 또는 모델99지문을 참조하는 기존 압축 형식을 실제5개 후속 출현 증거에서 해제했다. 원 Context/CP/모델102지문·계수·입력/권리·시간 범위와 원 export는 변경하지 않았다. 새 생장 계산/과거 전진·조달을 실행하지 않았다.

기존 Python encoding 구현으로 실제5개 증거의 원 receipt/calculation/candidate·before/after 상태·program 지문과 길이를 별도로 기록했다. 복원된 크기는388,384/414,337/440,293/466,613/492,549bytes다. 브라우저용 함수와 별도 번들의 실행 결과가 모두 같은 원 지문과 일치했다. Python 기준 생성은 허용 encoding 이외의 생장 import를 차단하고 원 source/output closure와 공개101파일의 보존을 확인했다.

원 `2.0`·`-0.0`·지수 표기와 참조 부분 문자열을 그대로 보존한다. 숫자 값을 JSON으로 다시 직렬화하지 않는다. 닫힌 형식·version/코드집합/receipt hash, 정수 tag/selector/index·실제 own key/배열 경로·Unicode codepoint 키 순서를 검사한다. 중복 키·비유한 수·상속 경로·없는/잘못된 참조·깊이/입력·UTF8/확장 byte cap 위반은 거부한다. 입력과 확장은 원2MiB, 깊이/경로는64이며 반환 문자열을 무제한으로 만든 뒤 크기를 검사하지 않는다.

43개 새 검사는 실제5개 전 증거 대사, 원 float/Unicode/배열·코드 참조와35개 부정/용량 사례를 포함한다. 기존 wire8검사를 함께 통과했다. 독립 새 Node 프로세스에서도5개 receipt의 정확한 원 길이/전체 해시를 확인했고, 같은 부모를 JavaScript JSON으로 재직렬화한5개 변형은 모두 거부했다. 별도7,440byte 번들에는 외부 import가 없고 fetch 차단 계측0회였다. 생장식·DB·CLI를 포함하지 않는 바이트 검증 경계다.

## 측정한 성능과 WSL

초기 별도 실행의 동일5정상+5변형 묶음은10.117초였다. CPU profile9,446샘플 중 parser의 value/string/space·공백 정규식이8,749샘플로 약92.6%였다. 같은 불변 원 문자열의 컨테이너 파싱을 호출 내부에서 최대4,096항목까지 재사용하게 해 같은 묶음이1.573초가 됐다. 원 지문·길이·변형 거부 결과는 전후에 모두 같았다. 공유/영속 입력·권리 캐시는 없다. 이 한 번의 비교는 전체 SDK/브라우저 응답 지연이나 최종 성능 수용이 아니다.

| 최종 단계 | Guard wall | 결과 |
| --- | ---: | --- |
| 독립 Python 기준 | 1.835초 | 실제5개 원 지문/길이 |
| 최종 고유51검사 | 3.506초 | 두 test file 통과 |
| 전체 타입 검사 | 4.742초 | 같은 전체 tsconfig/최종 코드 |
| 별도 번들 | 1.243초 | 원 source의 독립7,440bytes |
| 별도 원/변형 실행 | 2.812초 | 5정상+5변형, 내부1.573초 |
| 원 자료/GUI 보존 | 1.989초 | 선행361source/1output·원 출력/권리/GUI |

전체 타입 검사 재실행 한 번은 PID564,224,000bytes에서 원512MiB guard가 보류했다. child exit0이어도 그 시도를 수용하지 않았다. 설치된 TypeScript7.0.2의 wrapper가 Go 네이티브 실행 파일을 쓰는 것을 직접 확인했다. Node heap flag와 별도로 해당 검사 프로세스에 `GOMEMLIMIT=320MiB GOGC=50 GOMAXPROCS=2`를 적용했다. Go memory limit은 soft limit이므로 기존 외부 RSS guard를 유지한다([공식 설명](https://go.dev/doc/gc-guide#Memory_limit)). 최종 전체 타입 검사는 PID522,526,720bytes/합산561,041,408bytes로 원 PID536,870,912bytes/합산1GiB 상한 안에서 통과했다. 여유가 작다는 관측을 남기며 향후 검사도 같은 guard를 선행한다. 패키지·lock·tsconfig·CI·원 guard 상한은 바꾸지 않았다.

수용 단계는 원600초·로그4MiB 안에서 종료했고 controller FD4→4·소유 자식0, 보호5175 프로세스를 보존했다. 원 private:false132blob·봉인 GUI4,865파일·기존 두 공개 출력9,464파일/경계와5175 HTTP200도 확인했다. 새 HTTP/브라우저/API/DB/worker를 기동한 증거는 아니다. 전체 frontend/backend suite는 실행하지 않았으며 작업 시작 HEAD `922ce312d99d4063b2958284dca6ded45d025c77`의 CI API는0runs였다.

## 다음 수용 기준

다음은 독립 root/index/102code anchor와 닫힌 파일/Context/CP 연결 검증이다. 그 뒤 원106+3n+m+2h 상태와38프레임/6,208scalar·A/L/C/부착/clock/정확 UTC/phase·형상 원점/부족분/장부를 대사하고, HTTP/개별·전체 cap·취소/latest/반환 복사·원 자료/GUI/WSL을 독립 검증한다. 이들이 통과해야 전체 strict SDK를 수용한다. 현재 복원 함수가 crop replay를 승인하거나 UI에 수치/geometry를 제공하지 않는다.

전체 SDK 조회를 실측한 뒤 같은 상태의 실제 잎·줄기3D 공수를 갱신한다. 이번1.573초를 전체38시점 로딩이나 제품 일정으로 바꾸지 않는다. 이후 생산·자원·Decimal 경제/거시/수급·지역·제품 farm/worker·자율 비교가 남는다. 독립 국내 단일 품종 자료0·자료/권리/독립 미래 작기·대응 후보 비교는 병행 외부 의존성이며 확보일·전체 완료일은 미정이다.

실제 native Codex CLI `gpt-6.1-sol/xhigh`의 문맥과 출력 지문을 기록했으며 재귀 CLI0회다. G0–G4 `not_assessed`, R2 `not_approved`, 전체 goal active/incomplete를 유지한다.
