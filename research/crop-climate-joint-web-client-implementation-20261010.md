# 공동 작물·기후 결과의 typed 웹 reader — 2026-10-10

## 수용 범위

`crop-climate-joint-web-client`를 **로컬 소프트웨어 reader 자식만 수용**한다.
core는 `0f3a03e8dda1b8e141600dd988758b28d445bf0e`다.
[명시 runtime](crop-climate-joint-runtime-implementation-20261010.md)의 원 공개 응답을
기존 인증 transport로 읽는다. 새 화면·WebGL·계산 중 진행 상태/U3는 이번 수용에 포함하지 않는다.

[기계 증거](artifacts/crop-climate-joint-web-client-reference-20261010.json)는
22,724bytes / SHA256 `2d85472c8548268c1da7cce0ba025998a9587c1a2356837253d72e8b10646ab3`다.
원 전체 terminal/source pin/HTTPS wire와 controller는 저장소 밖 private 증거에 보존했다.
공개 증거에는 관측 PG 목록의 개수와 원 terminal hash를 남겼다.

## 변경한 다섯 파일

- [typed reader](../web/src/jointCropClimateReplay.ts): summary/page/순차 iterator와 닫힌 DTO 검사.
- [기존 API 조립](../web/src/api.ts): 새 reader factory import/조립 두 줄.
- [집중 검사](../web/src/jointCropClimateReplay.test.ts): 새113개.
- [웹 계약](../contracts/web-joint-crop-climate-replay-v1.md).
- [직접 작성한 합성 응답 fixture](../web/e2e/joint-crop-climate-recorded-responses.json):
  221,134bytes / SHA256 `0cee45324b6416867e9f969f3e77da1ae454778df9098dbc7744e77db795f71a`.

새108상태·22적분 장부·50 C/N 구획·관리 전후 상태/제거·잔차/예산을 원 단위와 값으로 검사한다.
기존121상태 응답으로 변환하지 않는다. result/farm/batch/zone/reference와 manifest/관리 code/profile/policy 결속,
닫힌 component/dependency map을 비교한다. HMAC·현재 권리·native code 승인·전체 context hash 증명은 서버가 검사한다.
웹의 형태 검사는 관문 승인 근거가 아니다.

원 UTC 마이크로초 문자열과 정수 격자/index를 보존한다. `1e-06` 같은 실제 Decimal 문자열 표현도 검사한다.
웹의1µs 사례는 기존 inventory를 복사한 **형태 검사**이며 실제1µs 작물 계산 시험이 아니다.
summary의 마지막 확정 상태/hold 실패 경계와 페이지64시점/8사건·2MiB/30초를 유지한다.
요청 전후 lookup/query/summary 변경, 잘못된 판본/단위/시간/값, foreign page,
취소/늦은 응답/권한 실패와 동시 요청을 거부하고 이후 요청은 복구한다.
iterator는 원 개수/순서를 확인한 경우만 완료를 반환한다.

## 통과한 검증

고유 **459개 = 새 웹113 + 기존 웹344 + 실제 SCRAM/검증된 HTTPS 캡처2**다.
중간 `test-v1`의113개는 중복 집계하지 않았다. 최종 타입 검사와 제한된 비압축 제품 빌드도 통과했다.

| 최종 그룹 | 원 session / terminal tool | 실제 controller/child 종료 | 검증 |
|---|---|---|---|
| 완료 결과 캡처 | 58362 / `5dd065` | 0 / 0 | 실제 SCRAM/TLS1개, summary/samples/events 원 wire |
| hold 결과 캡처 | 55134 / `2a5a56` | 0 / 0 | 실제 SCRAM/TLS1개, 마지막 확정/실패 경계 |
| 타입 | 81106 / `132636` | 0 / 0 | 최종 다섯 core 파일 |
| 새 웹 검사 | 6894 / `981453` | 0 / 0 | 113개 |
| 기존 SDK 회귀 | 55876 / `a6e1ca` | 0 / 0 | calculation/cycle/window/API344개 |
| 제한된 제품 빌드 | 99142 / `96c9c8` | 0 / 0 | `minify=false`, 소유 출력 |

실제 HTTPS6응답은 native current-query 원 bytes와 각각 같다. 각 wire는 fixture에 정확히 한 번 나타난다.
캡처 당시와 최종 현재의 **모든 backend Python pin이 같다**.
캡처 뒤 웹 검사/타입을 보완했으므로 캡처 당시와 최종 SDK 다섯 파일이 모두 같다고 주장하지 않는다.
최종 네 웹 그룹에서는 다섯 파일 SHA가 모두 같다. 원 값과 권리의 서버 책임을 바꾸지 않았다.

조회 중 감시한8개 수치/prepare 진입점 호출은 모두0이며 등록 row1·입력/저장 개수·빈 legacy root를 보존했다.
TLS FD는10→10, 각 controller FD는4→4다. 원본2,148항목과 기존 UI source/assets/PID를 보존했고
각 그룹에서5173이200이었다. 소유 PG/schema/role/passfile/임시 디렉터리를 정리했다.
최종 수용6그룹의 감시 시간 합은175.168초, 관측 단일/소유+보호 합 RSS 최대는
395,014,144 / 502,095,872bytes다. .25초 관측과 기존512MiB/1GiB 한도를 유지했다.

## 실패한 빌드와 수정 근거

최초 `build-v1`은 비압축이었지만 Node heap384MiB 설정에서 단일 PID RSS713,510,912bytes를 관측했다.
원 session87728 / terminal `4a4e52`의 controller1 / child-15, `RSS_limit`로 소유 트리만 종료했다.
이 실패를 수용 성공이나 한도 이내 관측으로 집계하지 않는다. 합 RSS는801,501,184bytes였고
원본/화면/FD·소유 정리는 유지됐다.

이전 수용 빌드의 `build-controller-v5.py`/`owned-node-gc-v2.cjs`를 직접 확인했다(`b696e3`, `75c93e`).
같은 CPU affinity1·nice19·heap48MiB/semi-space2MiB·250ms 명시 GC와 thread1 설정을
private controller에 적용했다. `build-v2`는 단일/합 RSS300,490,752 / 388,481,024bytes로 종료0이었다.
GC record1개와 controller/hook hash는 기계 증거에 있다. 앱/Vite/의존성/lock 설정을 바꾸거나 한도를 넓히지 않았다.
일반/압축 빌드·hosted CI를 새로 수용한 것은 아니다.
비수용 metadata 조회의 import 경로 오류1회도 backend 작업 디렉터리로 바로잡았고 제품 코드는 바꾸지 않았다.

## 판단 실행·현재 UI·다음 단계

현재 native CLI의 `gpt-6.1-sol` / `xhigh`를 사용했다. 원 turn-context는
2026-10-09T23:01:40.931Z, LF 포함 SHA256
`f59ec21d0f2fe2ae5bfa18b69658c19bb23e0aad15138d810771973ad0cd07ee`다.
CLI 재귀 실행과 별도 제품 runtime CLI 실행은0회다.
이 proof부터 마지막 빌드 기록23:18:47Z까지 약17분이며 기록/검토/commit 시간은 별도다.
기존 SDK2–4집중시간 예상은 이 실제 완료 관측으로 갱신한다.

현재 [사용자 화면 안내](../web/README.md#기존-제품-앱의-로컬-동시-기동--2026-10-09)의 run-v3는
**완료된 합성166일의 생장/수확을 조회·재생**한다. 백엔드와 연결되어 있지만 진행 중 계산을 구독하지 않는다.
기존 서버를 새 모델로 교체하지 않았다. 이번 SDK 수용도 해당 화면의 자동 갱신을 뜻하지 않는다.

다음은 `crop-climate-joint-numerical-3d`다. 같은 result/farm/version/UTC의 원108상태·50 C/N·LAI와
계산된 수관/공기 온도를 표·그래프·수치3D에 연결한다. 화면/adapter 경계를 고정한 뒤 시간을 다시 추정한다.
실제 DB/TLS/브라우저의 원값 대사·hold/권리 실패/늦은 응답 정리·기존 화면 공존/WSL 보존이 수용 조건이다.
이후 진행 상태/확정 prefix/완료 결과의 U3를 별도로 연결한다.
온실/전체 공동 작기·물/양분/구매 에너지·경제, 실제 품종 계수/독립 농장 자료0건과 G0–G4,
생산/미래 마진/순위 hold는 남아 있다. 기존 registry 실패에 따른 push hold를 유지하며 CI 재시도/배포는 하지 않았다.
