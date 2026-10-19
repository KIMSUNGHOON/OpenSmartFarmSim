# 현재 인코딩 호출·소비 경계 검토 — 2026-10-20 KST

[기계 증거](artifacts/solar-current-encoding-boundary-review-20261020.json) · [선행 실제 늦은 묶음](solar-worker-late-quantum-observation-20261020.md).

## 실제 호출 위치

같은 app261 tree `d477b74bc0a7ad2258a5bfd7bb522ad559a704ea55fca3849fb2f46e7ce403db`에서 원 CASE6/64·출력 격자·chunk1의44→45 before/private advance/confirm을 관측했다. JSONEncoder.encode의 원 반환값을 전달하며 호출 경로/옵션/크기/시간·반복 횟수만 내보냈다. 비교용 digest는 메모리에서만 사용하고 원문/개별 digest는 기록하지 않았다. 권한·디코드 객체·인코딩 결과 cache는 없다.

직접3단계 경로238개·호출16,885회·처리 bytes104,203,471을 확인했다. 아래는 phase를 합친 동일 호출 위치다. 계측 비용이 포함됐으며 driver/loader/phase 시간과 겹친다. 과거 profiler의 exclusive iterencode 시간과 직접 비교하거나 전체 처리량으로 환산하지 않는다.

| 호출 위치 | 횟수 | 인코딩 bytes 합 | 계측 wall초 합 |
|---|---:|---:|---:|
| `app.crop_climate_joint_continuation._hash:32` | 1302 | 32647518 | 0.537639 |
| `app.crop_cycle_artifact._blob:54` | 517 | 21278405 | 0.328397 |
| `app.crop_greenhouse_solar_storage._load:192` | 456 | 7852936 | 0.134113 |
| `app.crop_greenhouse_solar_input_evidence.verify:273` | 31 | 5660197 | 0.086778 |
| `app.crop_greenhouse_solar_input_evidence.verify:248` | 31 | 5786460 | 0.084688 |
| `app.crop_greenhouse_solar_input_evidence._signature:222` | 31 | 5783577 | 0.084262 |
| `app.market_reference_bundle.fingerprint:27` | 2640 | 1742370 | 0.058490 |

## 소비와 오류 경계

- [storage._load](../backend/app/crop_greenhouse_solar_storage.py)는 fresh commit/page에서 원 source_chunk·bound result·checkpoint hash를 각각 확인하고 last_confirmed의 canonical bytes를 비교한다. 같은 값이 반복돼도 서로 다른 파일/HEAD/읽기 시점의 검증이다. 일반 Python equality로 대체하지 않는다.
- [artifact._blob](../backend/app/crop_cycle_artifact.py)은 매번 현재 파일의 보안/크기·원 hash·엄격 JSON·canonical 원문을 확인한다. 기존 transcript는 서로 다른 load 사이의 clone/의존성 비용 때문에 실제 묶음 기준을 못 넘었다. 이번 반복 통계로 그 검사를 생략하지 않는다.
- [input evidence verify](../backend/app/crop_greenhouse_solar_input_evidence.py)는 전체 envelope와 HMAC·현재 파일/검토·원 record를 소비한다. 이전 envelope 후보는 평균−1.1108%였고 오류 경계 전체 검증도 하지 않았다. 다시 적용하지 않았다.
- [market source](../backend/app/market_source_store.py)의 canonical model/input 비교는 현재 경제 참조·엄격 타입/원문에 연결된다. 이번 작은 인코딩 비용만으로 해당 검증을 없애지 않는다.
- [실행 조회](../backend/app/crop_greenhouse_solar_execution_query.py)는 unavailable checkpoint에도 보호된 job metadata를 반환하며 current 전후 검증을 수행한다. 임의 busy 캐시나 검사 생략을 도입하지 않았다. 현재 CI의 실제 HTTP 응답/동시 병목은 이 단일 worker 관측만으로 알 수 없다.

원 checkpoint bytes/counts/UTC00:01:30.123456Z·current15/SQL9,929/role273/원천2,280·수치 step1/start0/restore1/CLI0와 기존14 assertion AST를 유지했다.

## 작은 인코더 구성요소 비교: 제품 미채택

별도 소유 저장 artifact에서 실제 _blob 소비 순서103개·4,190,691bytes를 대사했다. 새로 엄격 파싱한 JSON tree에만 같은 encoder의 circular 옵션을 끈 사설 함수와 기존 함수를 ABBA로 비교했다. 각 pass는 원 순서를6회 사용했고 매 출력의 원 canonical bytes를 대조했다. JSON 경계6개와 cycle fallback 오류도 비교했으나 일반 호출/모든 코드 변조·권리/오류 경계의 수용 시험은 아니다.

구성요소 평균 감소는 **12.020737%**, 두 짝은13.757045%/10.232307%였다. 전체 worker/current/IO와 보수적 fallback의 비용은 포함하지 않았다. 이 숫자로 원64나 전체 묶음의2% 기준을 통과했다고 하지 않는다. 라이브러리·제품 옵션·cache·검증 변경은0이며 전체 후보 trial도 실행하지 않았다.

## 계측 실패와 최종 수용

첫 v1은 confirm의 hold로 실패했다. 초기 깊은 경로512개 assertion은 관측 코드 안에 있었다. 후속 같은 원 입력에서5단계 경로581개·첫513번째가 confirm임을 확인했다. 최초 내부 예외 원문은 회수하지 못했으므로 단일 원인을 확정하지 않는다. v2는 직접3단계만 집계하고 깊은 경로는 개수만 기록하며, 수집 오류가 원 반환/권리 연산을 바꾸지 않게 분리했다. 최종 수집 오류는0이다. 실패 source/log/종료·정리는 보존했고 통과 수에서 제외했다.

v2는1검사·자식0·guard126.697013초·단일/합 RSS124,174,336/951,193,600bytes·FD4→4·5root/원본2,148/두 frozen UI/source/자산·소유 PG/비좀비/임시/passfile0을 확인했다. 구성요소 probe도 자식0·guard2.394524초·합 RSS847,400,960bytes·FD4→4/같은 보존·정리였다. 이전82/늦은 profiler1을 재실행·합산하지 않았다. 실제 native CLI `gpt-6.1-sol` / `xhigh`의 문맥/원행 SHA와 모든 source/영수증/출력 SHA를 결속했다. 재귀 CLI/하위 에이전트는0이다.

## 다음 한 단계

로컬 인코딩을 더 줄이는 후보로 원 동시 실행의 실패를 설명하지 않는다. 다음은 [기존 worker-api 진단](../contracts/crop-solar-worker-progress-diagnostics-v1.md)을 현재 source에 한 번 적용해 원 actor 본문/입력64/chunk1/조회·retry360/RSS를 유지한 실제 worker 반환·HTTP 상태/허용 오류·원 source/header/종료/정리를 대사하는 것이다. 새 관찰 header나 기반 서비스를 추가하지 않는다. 진단은 정상 수용이 아니며 그 결과로만 다음 수정 경계를 정한다.

원 정상64→독립 hold→HTTP취소→계산 중WebGL→WSL 사용자 적용, 실제 농장/독립 자료·G0–G4는 남아 있다. 새 Solar 미배포·실제 농장 Run0·전체 완료일 미정·goal active다.

최종 게시 `focused-solar-encoding-boundary-final-status-v1`는 자식0·guard1.881477초였다. 새 관측/구성요소·같은 app82/늦은 관측1·원 CI artifact/actor·관련 링크2,782개·두 HTTP200/동일bytes/no-store·두 frozen HTML/환기2,173파일·5root/원본2,148/FD4→4/소유 정리를 대사했다. 기록 시각은2026-10-19T21:30:27.618672Z이며 새 DOM/WebGL 수용은 아니다.
