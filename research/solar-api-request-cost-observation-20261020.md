# 실제 API 요청별 비용 관측 — 2026-10-20 KST

[기계 증거](artifacts/solar-api-request-cost-observation-20261020.json) · [진단기/고유11검사](solar-api-request-cost-implementation-20261020.md) · [관측 계약](../contracts/solar-api-request-cost-diagnostics-v1.md).

## 실제 실행과 한계

[CI39369990827](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/39369990827), source `7fda9ba96b68297832d5d313091d041689f4fd39`/attempt1·job118455456705는 `completed/failure`다. 선택 `worker-api` 진단을 한 번 접수했고 원 actor 본문/단언·CASE6/input64/chunk1/조회·retry360/RSS를 유지했다. 원 계산 step은04:33:32Z에 시작했으며 최종 worker confirm은 **27/64·UTC2026-10-01T00:00:54.123456Z**였다. 계산 경과360초 제한을 통과하지 못했고 worker outcome/정상 proof·DB role/schema0 count proof는 없다. actor 종료−15/−15는 정리 종료다.

API 관측 자체는 수용했다. **전체 client24개와 서버 동기 구간24개를 각각 하나씩 시간 범위로 연결**했고, dropped response/server operation/active/counter는0이다. 예외는47건이 최근 창 밖으로 제외됐다. 마지막 원 DB의 READ ONLY/REPEATABLE READ metadata도27/64·sequence28/attempt1/simulating이지만 현재 권리나 전체 수치/정상 완료 proof는 아니다.

## 요청과 실제 대기 시간

아래는 관측된 전체 요청이다. 모든 값은 observer 비용을 포함하며 계측 OFF44/64와 처리량 비율로 비교하지 않는다.

| client 분류 | 건수 | 실제 HTTP status | wall 범위 초 |
|---|---:|---|---:|
|접수|1|202×1|3.334686|
|진행 조회|8|200×3 / 503×5|4.108649–10.433398|
|prefix 요약|8|200×7 / 503×1|4.038628–15.058669|
|samples|7|200×7|13.920491–15.677736|

성공한 진행200 세 건은7.937915–8.158556초·각 current4/원천 선택608/SQL3,391회였다. 성공한 prefix200 일곱 건은13.775957–15.058669초·각 current6/원천 선택912/SQL5,090회였고 samples200도 각 current6/원천912/SQL5,091회였다. 실패503은 원 이유와 current/HEAD 경합 검증을 보존한 결과이며, 느린 응답 모두를 같은 오류나 원인으로 합치지 않는다.

## 서버 동기 본체의 관측

| 구간 | 건수 | wall 합 초 | 해당 thread CPU 합 초 | SQL wall 합 초 | SQL 횟수 | current 횟수 | storage load 횟수 |
|---|---:|---:|---:|---:|---:|---:|---:|
|execution checked|9|59.385001|36.903200|24.638784|25,423|29|3|
|prefix read|15|207.124273|141.452458|72.262936|72,985|86|37|

이 시간들은 client/worker와 겹친다. SQL도 본체에 포함되므로 합산해 전체 runtime이나 병목 기여율로 쓰지 않는다. thread CPU는 client의 대기 CPU와 별도로 측정했고, 서버 본체 밖의 인증/ASGI 전송·직렬화는 이 구간에 없다. 수치만으로 나머지 CPU 전부를 특정 함수 탓으로 확정하지 않는다.

## 다음 최소 후보의 근거

[query `_current`](../backend/app/crop_greenhouse_solar_execution_query.py)는 full farm binding을 등록 scope 없이 호출한다. binding은 두 번 `read_registration`을 수행하며, 명시 scope 밖의 등록 읽기는 각각 `_prepare`를 수행한다. 반면 수용된 checkpoint `_current`는 그 한 쌍을 기존 등록 scope로 소유한다. 이번 실제 성공 응답에서 current4/6과 원천608/912를 확인해 **조회에서의 같은 현재 검사 한 쌍**을 다음 조사·비교 대상으로 좁혔다.

다음 `crop-solar-query-current-registration-scope-candidate`는 [별도 최소 계약](../contracts/solar-query-current-registration-scope-v1.md)에 따라 query의 한 `_current` 안에서만 기존 scope를 소유하는 후보를 평가한다. 먼저 실제 재구성2→1과 원 fresh lookup 순서를 확인하고, 실제 handler의 progress→prefix→samples 전체 비용과 같은 selector/수치/UTC·현재/늦은 권리·거부/정리를 대조한다. 이전 confirm scope의 미채택 후보를 다시 실행하거나 scope를 전체 query/HTTP 요청·worker까지 늘리지 않는다. 아직 제품 변경이나 비용 수용은 없다.

## 출처·자원·남은 관문

artifact12241058794/33,812bytes·ZIP SHA `4e9ee69b…`를 한 번 회수했고 경로/크기/압축 해제·run/head/원 actor/header/source/digest를 대사했다. 호스팅 guard385.421777초·단일/합 RSS130,134,016/367,919,104bytes·중단 사유null·FD7→7·소유 비좀비/임시 잔여0이다. WSL5root 동시 용량이나 DB0 count proof로 확대하지 않는다.

로컬 대사 guard3.542026초·합950,829,056bytes/1GiB·단일145,444,864bytes/512MiB, FD4→4·원5root/2,148·두 frozen UI/source/자산·소유 PG/비좀비/임시/passfile 잔여0을 확인했다. 실제 CLI 문맥 gpt-6.1-sol/xhigh와 검증기/출력/원 hash를 기록했다. 재귀 CLI/agent·새 framework/자료 채택0이다.

관측51의 수용은 원 계측 OFF 정상64·독립 hold/HTTP취소·계산 중WebGL·WSL 사용자 적용을 수용하지 않는다. 이번에는 전체 backend/browser CI나 새 DOM/WebGL을 실행하지 않았다. 제품 app261/d477b74b…는 유지하며 실제 농장/경제 검증과 G0–G4·새 Solar 배포·전체 완료 날짜는 미완료/미정이다. goal은 active다.

## 사용자 진행 정보 게시

[최종 게시 영수증](artifacts/solar-api-request-cost-final-publication-20261020.json): 두5173/5174의 같은 최신 JSON·HTTP200/no-store·원 HTML/환기2,173파일·app261/원본/5root/소유 정리와 로컬 링크2,746개를 확인했다. 종료된 CI27/64·24요청 관측과 후속 query 후보를 표시한다. UI 코드·DOM/WebGL 재검사는0이며 기존 환기 표시를 새 Solar 배포로 바꾸지 않았다.
