# 자동 출현 입력과 현재 농장·완료 줄기 결과 — 2026-10-24

상태: [농장 결속 계약](../contracts/crop-leaf-appearance-farm-binding-v1.md)의 **합성 소프트웨어 수용**.
[원 입력 검토](crop-leaf-appearance-input-evidence-20261024.md) 뒤의 현재 농장/parent 결과 연결이다.
새 appearance 결과의 서명·자동 worker/API·사용자 화면 적용은 후속이다.
[저장 3D](http://localhost:5176/leaf-appearance-replay.html)는 기존 연구 재생을 유지한다.

## 구현과 시간 범위

`LeafAppearanceFarmBinding`은 기존 실제 MorphologyExecutionQuery/farm authority·JobStore와
같은 stem 입력 authority를 사용한다. 완료 parent의 publication·서명/result/root·최초 계산 시각,
등록 farm/crop/기간과 원 appearance program/source/evidence·정책/초기/프로필을 결속한다.
양쪽 자료의 현재 검토·계산/표시 권리와 범위를 전후 대사한다.
기존 고정 판본과 수치/권한 검증을 보존하며 새 표/역할·leaf 결과 row나 서비스를 추가하지 않았다.

새 source의 가용 시각을 이전 사용자 farm decision으로 소급하지 않았다.
별도 합성 농장을 **2026-10-23T16:00:00Z**의 decision으로 등록하고 원 stem 작업을 실제로 완료했다.
원10월1–2일 모델 구간의 retrospective replay이며 당시 전망이나 실제 재배 검증은 아니다.
parent_result_binding_verified=True는 해당 job/서명/root 연결이며 품종 적용·초기 수치 검증이나
권리/G0–G4 승인을 뜻하지 않는다. per_tracked_shoot를 유지하고 전체 온실 생산량으로 환산하지 않는다.

## 통과한 검사

- **순수33:** 닫힌 요청/크기·UUID/SHA·기존 population schema 혼합·원 정책/프로필/초기 지문,
  원 parent 증거/결정 시각과 기간·1µs 가용/점유 경계·비공개 사용 범위를 확인했다.
- **실제 SCRAM2:** 별도 farm 등록→실제 parent 계산/완료→새 prepare/read/write와
  미완료·취소/다른 result/root·crop/tenant, 현재/늦은 양쪽 검토·권리/범위 변경을 확인했다.
  표시만 허용되면 read는 가능하지만 parent 계산 권리가 없으면 write를 거부한다.
  시험 DB의 과도한 DELETE 권한과 rehash한 등록 row 변조를 거부하고 원 상태를 복구했다.
- **독립 fresh:** 같은 **29,174bytes binding**, 원 parent result/root/최초 시각·32변수/정책 지문,
  양쪽 검토 철회 거부·생장/worker import0·작업 쓰기6진입/지속 SQL쓰기0,
  seed/pytest/HTTP app import0·원 signed18파일·FD4→4를 확인했다.

정상 prepare/read/write와 **모든 변경 거부 current 호출**에서 작업 쓰기/지속 SQL을 직접 차단·계측했다.
실제 권한/등록 변조를 만드는 시험 전용 admin SQL은 그 호출 밖에서만 수행하고 복구했다.
최종 두 시험의 각 스키마 **25표 행 SHA**는 전후 같고 생장/CLI 진입도0이다.
이는 기존 사용자 DB 전체를 이번에 재대사했다는 주장이 아니며 별도 소유 DB만 사용했다.

모듈 부재 RED 뒤 순수33/첫 native2가 통과했다. 검토에서 변경 거부 호출의 쓰기 계측을 보완해
**같은 생산 코드의 최종 native2**를 다시 통과했다. 이전 native 시도를 합산하지 않는다.
입력 증거/기존 farm/parent를 포함한 순수 회귀는 **304개**이며 신규33을 포함한다.
최종 고유 수용 묶음은 **순수304+실제 DB2=306개**다. 전체 backend/새 hosted CI·HTTP/브라우저는 실행하지 않았다.
기존 웹/수치 코드를 바꾸지 않아 이전 UI 시험을 반복하지 않았다.

생산 코드 source는 `e8b49767cefd6cba7a229ffef672a2e458b1a841`이며 최종 native/순수 회귀와 같은 bytes다.
정확 native `gpt-6.1-sol`/`xhigh`의 실제 turn_context 시각/원 LF SHA·재귀 CLI0,
현재 코드/시험 지문·정상/변경/fresh 원 증거를 [기계 판독 기록](artifacts/crop-leaf-appearance-farm-binding-20261024.json)에 보존한다.
자료 검토/농장 등록은 자체 소프트웨어 fixture이며 실제 제품 CLI·현장 검증이나 실제 농장 Run 수용은 아니다.

## 자원과 다음 단계

최종 native2는254.08초(guard255.237초)/968표본, .25초 설정의 PID102,055,936/
합산517,980,160bytes로512MiB/1GiB·600초 안이었다.
단일 prepare/read/write current 관측은13.338/12.946/12.969초이며 처리량·HTTP30초/운영 용량 수용은 아니다.
각 phase의 보호3root·원2,504항목/현재 소스·소유 잔여0·FD4→4를 확인했다.
임시 PG/짧은 디렉터리와 passfile을 정리했고 최종 schema/role 잔여0이다.
원 물리 DB/키·사용자 작업/불변 자료·서버/5175·5176 UI는 변경하지 않았다.

다음은 **원 appearance 불변 수치 결과의 서버 서명·현재 무계산 조회**다.
현재 farm 결속 아래 producer1회→원 source/준비/생성·내부 population root를 포함한43blob/outer root,
12시점/47면적·정책/부착/UTC를 대사한다. 현재/늦은 철회·서명/원본/코드/참조 변조를 거부하고
fresh manifest/frame/replay의 생장 import/계산·CLI·DB/파일쓰기0, 원 parent/result/시각·행·정리를 확인한다.
조회에는 현재 farm 확인을 위한 DB 읽기가 허용된다. 이후 기존 jobs 표의 접수/worker/현재 조회→보호 API→같은 job3D다.

새 outer manifest 연결·producer/조회30–60분, 변조·철회/실제 DB·fresh20–45분,
검토/기록10–20분으로 **60–125집중분**을 낮은 신뢰로 추정한다.
기존 서명 경계와 앞선 native 정상269/변경165초를 재사용하되 새 manifest/sample_count와
원 준비·내부 root 연결을 추가 확인해야 한다. 이번 farm의 이전2.5–5h 예상은 실제 수용 기록으로 대체한다.
후속 worker/API/UI·관리/생산·자원/경제·자료 확보를 포함한 전체 완료 날짜는 미정이다.
실제 품종/국내 독립 작기0·거시/수급/자율 비교·R2/첫 cold 경고·G0–G4는 후속이며 goal active다.
