# 저장 이력 길이별 검증 비용 관측 — 2026-10-20 KST

[기계 증거](artifacts/solar-history-validation-cost-review-20261020.json) · [원 독립 정상 실패](solar-existing-intent-resume-native-normal-20261020.md).

## 범위

현재 제품 sourceaeb7a90/app261 집계a18da9는 유지했다. 원 CASE6·64단계·출력0..64/8·chunk1·UTC 원점 `.123456Z`의 수치/파일 fixture에서 **부모·서명 ancestry와 저장 이력 loader만** 별도로 관측했다. 서명 chain은 사설 fixture에서 구성했으며 실제 농장 등록/현재 권리·HTTP/API/worker는 실행하지 않았다. 원 독립64 관문을 더 쉬운 입력이나 이 시험으로 대체하지 않는다.

원 `_selected`/`_load`를 호출했고 첫 관측은 proof 읽기/검사 횟수만 전달 계측했다. 청크들을 실제 불변 파일로 쓰고, 마지막 checkpoint bytes·sample/event 값·각 UTC를 같은 원 입력의 전체 계산 및 실제 reader와 대사했다. 이는 합성 소프트웨어 검증이며 농작물 생산/미래 예측의 검증이 아니다.

## 관측

| 저장 단계 | commit 수 | proof 읽기/검사 | ancestry ms | 저장 이력 loader ms |
|---:|---:|---:|---:|---:|
|1|2|5/5|0.778|27.688|
|16|17|35/35|3.712|111.602|
|32|33|67/67|7.322|216.523|
|41|42|85/85|8.538|256.211|
|64|65|131/131|14.155|372.452|

원점0의 초기 경계도 commit이므로 단계 수와 commit 수는1 차이다. 이는 한 독립 파일 시험의 값이며 실제 동시 API/worker quantum·전체 처리량·예측 일정으로 환산하지 않는다.

두 번째 별도 관측은41단계 loader의 Python profiler를 수집했다. 전체 관측275.625ms 중 JSON encoder411회/exclusive158.471ms, raw decoder99회/cumulative91.966ms, 중복 키 pairs54,223회/cumulative39.805ms가 나타났다. 중첩 시간은 합산하지 않으며 profiler 오버헤드/편향이 있어 정확한 미계측 비용 비중으로 쓰지 않는다. 실제 파일 read는 이 관측의 exclusive1.435ms였다.

작은 ancestry 중복을 먼저 바꾸는 후보는 선택하지 않았다. 부모 MAC/서명·fresh read·연결 검사는 모두 유지했다. 남은 검토 대상은 여러 loader 호출에서 반복되는 큰 JSON 이력 해석이다. 기존 JSON parser bulk 후보/입력 envelope 후보의 미채택을 되돌리는 판단은 아니다.

## 통과한 검사와 다음 경계

새 관측은 **고유2건**이며 기존72를 다시 실행하거나 합산하지 않았다. 첫 사설 probe는 pytest import 경로 누락으로 수집 전에 실패했다. 그 기록을 보존하고 새 v2에서 경로만 고쳤으며 실패를 수용에 넣지 않았다.

통과 guard합22.485209초·단일/합 최대 RSS141,316,096/940,691,456bytes·FD4→4·5root/원본2,148/두 frozen source/자산·소유 PG/임시/passfile0을 확인했다. 상한을 올리거나 기존 서비스를 멈추지 않았다. 실제 native CLI `gpt-6.1-sol` / `xhigh` 문맥과 probe/source/원 증거/종료 SHA는 기계 증거에 결속했고 재귀 CLI/하위 에이전트는0회다.

다음 한 단계는 **같은 닫힌 작업 안의 반복 저장 load에 대한 원문 검증 기록**을 source로 검토하는 것이다. 모든 현재 파일의 fresh 읽기/metadata/원문 SHA·HEAD·전체 부모/수치 검증, 코드/설정 의존성과 반환값의 가변성·닫힌 수명을 먼저 대조한다. 권한 승인 결과를 보관하지 않으며 증거 없이 loader/검사를 생략하지 않는다. 원문 변경·삭제/교체·제한·코드/설정 변경·수명/동시성 반례와 원 quantum paired 비용 기준을 정의한 뒤에만 사설 후보를 평가한다. 아직 새 primitive나 제품 변경을 수용하지 않았다.

다음 후보의 수용도 원64 정상의 선행 로컬 작업이다. 원 정상→독립 hold→HTTP취소→계산 중WebGL→WSL 용량/사용자 적용 순서, 새 Solar 미배포·실제 농장 Run0·독립 자료/G0–G4 보류·전체 완료일 미정·goal active를 유지한다.

최종 게시 `focused-solar-normal41-history2-final-status-v1`는 자식0·guard1.380470초였다. 새 보고서 링크5개/관련 문서2,737개는 중첩을 합산하지 않았고, 원 actor·기존72 증거·새 관측2·원 artifact와 app hash를 대사했다. 두 HTTP200/동일bytes/no-store·frozen HTML/환기2,173파일·5root/원본2,148·FD4→4·소유 정리를 확인했다. 진행 기록은2026-10-19T19:02:17.148115Z이며 UI 코드·DOM/WebGL 재수용은 아니다.

후속 [반복 load 검증 기록 평가](solar-storage-load-transcript-evaluation-20261020.md)에서 실제 늦은 quantum 비교 평균0.1529%/한 짝 악화로 후보를 미채택했다. 제품은 유지했고 위 다음 단계 문단은 당시 기록이다. 다음은 원 감사 마지막4개 SELECT의 결과 전달 동등성 검토다.
