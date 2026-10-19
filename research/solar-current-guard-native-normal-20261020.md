# 현재 검증 정리 source의 독립 정상 미완료 — 2026-10-20 KST

[기계 증거](artifacts/solar-current-guard-native-normal-20261020.json) · [선행 로컬64](solar-current-guard-ownership-20261020.md) · [앞선 큐 관측](solar-current-guard-independent-queue-20261020.md).

## 실제 독립 실행 결과

[CI39280701330](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/39280701330), source `8b5afe5ffc056c60474a72fca57c19d6328aba65`, 작업 `118154056615` / `independent normal Solar execution`은 최종 실패다. 원 계측 OFF actor/input64·chunk1·poll/retry360·RSS를 유지했고 재접수/재시작은 하지 않았다.

- 원 계산 단계는15:50:53Z 시작,15:57:16Z 실패다. 감독 자식1, guard382.266369초이며 고정 실패 단계는 원 계산 시간 제한/실패다. 원360초 안의 정상 완료를 증명하지 못했다.
- 두 actor 종료 후 readonly/repeatable-read로 회수한 **저장 metadata는41/64·yielded·sequence42·attempt1/simulating**, UTC `2026-10-01T00:01:22.123456Z`다. 현재 권리·공개 prefix·원 수치/UTC 대사나 정상 완료의 증거가 아니다.
- API/worker는 cleanup에서 각각−15, 정상/API/client proof와 원 DB 역할/schema0 count proof는 없다. actor 본문 SHA는 기존 원 두 값과 같다.
- hosted 단일/합 RSS131,084,288/366,546,944bytes로 상한 안, FD7→7·소유 비좀비/임시 잔여0이다. 자원 guard의 중단 사유는null이며 WSL 동시 용량 수용이 아니다.
- artifact12201495473은3,286bytes, digest `66ac606291a7ee38713ce7b50b29cd3f0369928453797a339fc1b5569dc97a23`다. run/head/name·ZIP SHA·허용4파일·원 actor/hash를 검증했고 terminal 재확인 때 같은 archive를 재사용했다.

앞서16:11Z까지 조회한 API는 queued/runner 미배정/steps0이었다. 이후 반환된 step 이력은 그보다 앞선 위 계산 시각을 나타냈다. 따라서 앞선 API 관측을 실제 미기동 확정으로 사용하지 않는다.16:22:01.956277Z에는 run=completed/failure인데 job=in_progress/null이었고,16:26:35.863173Z에 양쪽 completed/failure를 확인했다. 각 관측 원문은 별도로 보존했다. [공식 상태 공지](https://www.githubstatus.com/incidents/8tzbpcnl75jp)는 당시 Actions 처리 지연을 조사 중이었다. 상태 지연과 계산 시간 제한의 인과관계는 이 자료로 확정하지 않는다.

이전33/64·진단17/64와 이번41/64는 서로 다른 실행 기록이다. 단계 수의 차이를 paired 성능 개선율이나 정상 처리량으로 환산하지 않는다. 독립 정상 관문은 미수용이다.

## 현재 source의 별도 관측3건

제품 app261파일은8b5afe5 그대로다. 실제 독립 실패를 근거로 원 worker quantum의 **CPU 표본1·SQL 비용1·공통 canonical 호출자1**을 새로 관측했다. 앞선64 집중검사와 구 source 관측은 재실행/합산하지 않았다. 세 관측 모두 같은 단계2·원 checkpoint counts/UTC04.123456Z를 확인했으며 독립64 실패의 동시 API/worker 환경을 대체하지 않는다.

| 관측 | 실제 범위/값 | 해석 한계 |
|---|---|---|
| 요청2ms CPU 표본 | 1,347개·누락0·timer/handler 복원, quantum wall8.000363초/clientCPU5.593608초 | C 확장·신호·표본 편향이 있으므로 정확한 CPU 비중으로 쓰지 않는다. |
| SQL/fetch 별도 비용 | quantum8.220719초, execute11,723회/4.067691초·clientCPU1.688018초; role315/원천2,736 유지 | profiler/CPU sampler 없이 원 호출을 전달했다. observer 비용 포함, wall−clientCPU는 DB CPU가 아니다. |
| 공통 canonical 호출자 | 2,065회·선택 wall0.594774초, 전체 quantum13.796449초 | Python profiler 오버헤드 포함. 앞의 wall과 더하거나 처리량으로 사용하지 않는다. |

CPU 표본에는 현재 원천 조회·권한 감사·클라이언트 상태 확인과 JSON 처리가 나타났다. 공통 canonical의 큰 항목은 입력 증거의 verifier/signature와 hash다. 이전에 기각한 canonical envelope 후보를 다시 적용하지 않았다. 이 관측은 현재 확인을 생략하거나 권한 결과를 cache할 근거가 아니다.

## 순수 JSON 중복 키 검사 후보1: 미채택

현재 CPU 표본에 나타난 입력 parser의 Python 항목별 순회를 대상으로, `dict(items)` 후 입력 쌍 수/고유 키 수를 비교하는 사설 후보를 한 번 평가했다. 같은 Python JSON/UTF-8·constant 검사·자료/숫자·권리/SQL·원 quantum을 유지했다. API actor/input·수식/계수·한도는 바꾸지 않았다. Python 공식 문서의 [object_pairs_hook과 JSON key 설명](https://docs.python.org/3.12/library/json.html#json.JSONDecoder)을 참고했으며 문서만으로 동등성을 승인하지 않았다.

중첩/배열/escape 동치 키·빈 키의 중복 거부, 같은 값의 서로 다른 키 허용, signed-zero·bool/int/overflow float·Unicode/잘못된 UTF-8/BOM·잘못된 JSON/비유한 constant 등20개 경계 입력의 값/형식·오류/cause 일치를 비교했다.20개는 별도 pytest20건이 아니며 한 사설 trial의 preflight다. 실제 ABBA는 다음과 같다.

| 순서 | 기존 wall초 | 후보 wall초 | 감소율 |
|---|---:|---:|---:|
| 첫 짝 | 8.083531 | 7.989988 | 1.1572% |
| 둘째 짝 | 8.179657 | 8.042991 | 1.6708% |

평균1.4155%로 **사전2% 기준 미충족**이다. 사설 patch는 복원했고 제품 parser/의존성/설정/cache 변경은0이다. 안전성·보안 전체 수용이나 원64 통과를 주장하지 않는다. 같은 후보의 근거 없는 반복은 하지 않는다.

## 보존과 다음 단계

새 관측3+trial1의 고유4건은 모두 자식0/정리 통과다. guard합180.993915초, 단일/합 최대 RSS141,316,096/1,018,236,928bytes·5root/원본2,148/두 frozen source·자산·FD4→4/소유 PG·임시·passfile0을 확인했다. 전체 backend/browser·기존64 회귀를 재실행하지 않았다. 실제 native CLI `gpt-6.1-sol` / `xhigh`의 turn_context 시각/원행 SHA와 실행 source/receipt SHA는 기계 증거에 결속했으며 재귀 CLI/하위 에이전트는0회다.

다음 한 단계는 현재315회 권한 감사의 **순서와 보호 조회 경계**를 원 SQL11,723/원천2,736·원 counts/UTC와 함께 관측하는 것이다. 이전 호출자별 합계만으로 제거 가능한 중복을 판정하지 않는다. 같은 현재 정책/연결/역할·scope에서 보호 조회/외부 callback을 사이에 두지 않은 중복인지 source와 대조한 뒤에만 작은 호출 소유권 후보를 선택한다. 마지막 필수 감사·현재 권리·late revoke/lease/cancel·게시/조회 경계는 유지한다. 없다면 새 생략을 도입하지 않는다. 기각된15→4 SQL/pipeline/direct ACL·과거 receipt 대체를 재시도하는 작업이 아니다.

원 정상64를 수용한 뒤 독립 hold→실제 HTTP취소→계산 중WebGL→WSL 용량/사용자 적용으로 간다. 현재 UI 진행 기록은 이 실패/진단 결과로 교체하며, 새 Solar 미배포·실제 농장 Run0·실제 자료/독립 검증/G0–G4와 전체 완료일 미정·goal active를 유지한다.

최종 게시 `focused-solar-guard-native-normal41-status-v1`은 자식0·guard1.382572초였다. 두 HTTP200/동일bytes/no-store·frozen HTML/환기2,173파일·원본2,148/5root/FD4→4·소유 정리를 확인했다. 관련 링크2,608개와 기존64 검증의 링크2,514개는 겹치므로 합산하지 않는다. 진행 기록 시각은2026-10-19T16:30:12.120321Z이며 UI 코드·DOM/WebGL을 다시 검증한 것은 아니다.
