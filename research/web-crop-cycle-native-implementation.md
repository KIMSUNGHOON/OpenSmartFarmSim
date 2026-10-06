# 긴 저장 연구 결과의 실제 HTTPS·3D 연결

상태: **로컬 소프트웨어 경로 수용, 실제166일·품종/생산 검증과 hosted 수용은 별도**, 2026-10-06 KST.
[불변 receipt](artifacts/web-crop-cycle-native-reference-20261006.json)에 실제 CLI
`gpt-6.1-sol / xhigh` 문맥·출력 검증·source/로그/화면 hash와 정리를 기록했다. 재귀 CLI0회다.
`348b162`의 실제 시험2파일/장면 정리와 `6747add`의 시험 signed zero 표현 수정까지의3 core파일이다.
고정 계산/저장/API49개·client5개·window2개는 동일하다. 이전 화면 receipt의 장면 hash는 당시 판본으로 보존한다.

## 실제 경로와 원값

새 PostgreSQL16.15/SCRAM의 등록 소유 합성 입력4개를 실제 서버 writer로 계산·서명·저장했다.
25시간 입력 root는 [선행 실제 API](api-crop-cycle-runtime-implementation.md)의 고정 root와 같다.
수치 기준선은 이전 HTTP 원행과 이미 대사한 독립 제어 흐름이며 그 흐름은 고정 rate 함수를 공유한다.
이번 실행에서 독립 제어 흐름을 새로 실행한 것은 아니고 독립 생물학/현장 검증도 아니다.

| 실제 저장 사례 | 실행 결과 | 원 출력·사건 |
| --- | --- | --- |
| 25시간 | 92advance·11,400실제 걸음·완료 | 27시점·5관리 사건 |
| 과거 보류 | RK4-k2 평가00:00:00.500000Z에서 고갈 보류 | 원 경계00:00:00Z의 확인 시점1개·사건0 |
| 빈 보류 | 원 경계에서 고갈 보류 | 시점/사건0·확인 과거 없음 |
| 출력 없는 완료 | 120실제 걸음·완료 | 선택 출력/사건0 |

표준 HTTPS/Bearer/실제 WebGL에서 같은 ID/farm/전체 reference/UTC의 원값을 확인했다.
고유27시점·5사건, 총31frame 방문에서50 C/N의100mesh와 LAI 면적,
기관/16누적/4진단·수지·현재 범위 로그 척도와 그래프/표를 대사했다.
페이지의 원 offset7/2·이전 범위 재조회·원 사건 전후·완료/보류·출력0을 확인했다.
보류의 실패 평가 시각을 새 정상 sample로 만들지 않았고 자동 재생은 저장 원 인덱스만 이동했다.

전체 HTTP21응답 중 정상19개는 전체 본문을 읽었으며 최대 **20.484300초/64,791bytes**다.
기존30초/2MiB·`no-store`·한 번에 실제 요청1개를 지켰다.
현재 권리 철회422·계정 권한 부족403도 각각1번 확인했고 재연결과 표시 제거를 검증했다.
GET 중 RHS/advance 호출은0, 저장 행은 전후4개다. frontend를 통해 실제 TLS 서버를 호출했으며
native 시험에서 API 응답을 브라우저 route로 대체하지 않았다.

## 자원 정리와 수정

장면 전환 검사에서 남았던 context와 OrbitControls의 document 키보드 listener를 재현했다.
layout cleanup에서 DOM 분리 전에 controls를 해제하고, 분리된 canvas의 context를 마지막에
해제하도록 idempotent dispose를 연결했다. 화면 값/계산식/기존 v2/v3 의미는 바꾸지 않았다.
실제 경로와 별도 기록 응답 검사에서 이전 observer/listener/timer/RAF/요청과 차트 instance는
최종0이다. 이전 GL context는 loss 또는 GC를 확인했다. GPU driver byte 측정은 아니다.

별도 형식용512/128 반복 입력의 CPU4배 throttle20범위에서는 현재7/0개 원 행·100mesh·
canvas1/차트3/observer4를 유지하고 이전 범위를 누적하지 않았다.
입력 반응 최대 **256.520837ms**, JS heap 관측 최대 **40,784,648bytes**다.
명시적 GC·emulator의 측정이며 실제 저사양 기기·전체166일 계산이나 WSL 전체 메모리 증거가 아니다.
그 검사는 기록된 실제 과거 보류 원값을 썼지만 일부 header/많은 행은 형식용 fixture다.

native1개는 **2044.35초/34분4초**, runner2044.965068초로 통과했다.
실행 구간 기록의 긴 입력1461.568147초에는 finish/저장/summary도 포함되며 순수 RHS 시간으로 표시하지 않는다.
시험 role/schema/비밀번호 파일은0, private PG와 admin 비밀번호 파일 제거·PG status3·
frontend/HTTPS/browser 종료·custody FD0을 확인했다. Linux `RUSAGE_CHILDREN` peak는
**338.51171875MiB**이며 동시 프로세스 합계나 WSL/GPU 전체 메모리가 아니다.

## 검증·산출물·다음 단계

- 웹 단위522개/19파일·6.00초, typecheck/build 통과; 기존 큰 chunk 경고는 유지한다.
- cycle Chromium16개/약1.5분, 기존 v2/v3 도형·WebGL loss/restore5개/28.7초 통과.
- 새 실제 SCRAM/TLS/WebGL 수동 smoke1개/2044.35초 통과. default backend inventory에 포함된 시험이나 단일 전체 backend 수용으로 합산하지 않는다.
- 첫 [signed zero 기대값 실패/정리](web-crop-cycle-native-signed-zero-hold-20261006.md)와 앞선 자원 사전 검사 실패는 보존했다. 축의 정확한 `-0`만 JSON의`0` 표현으로 맞췄고 다른 원량/축·예산 검사는 유지했다.

실제 캡처는 [데스크톱](artifacts/cycle-native-desktop.png), [모바일](artifacts/cycle-native-mobile.png),
[과거 보류](artifacts/cycle-native-past.png), [빈 보류](artifacts/cycle-native-empty.png),
[출력 없는 완료](artifacts/cycle-native-empty_completed.png)다. 앞 세 캡처를 직접 확인했다.
기존 검토용/기록 응답 캡처5개는 덮어쓰지 않았다. Pixel fidelity 수용은 별도다.

자식 window/view/browser와 실제 경로 증거를 모아 replay/result-pages 부모를 로컬 수용한다.
[종료된 d61 CI](crop-cycle-route-runtime-ci-hold-20261006.md)는 실패 판본으로 유지하며 수정 판본 hosted CI는 별도다.
다음 [작기 부하](../contracts/crop-cycle-burden-v1.md)는 비용 측정 → 실제166일 RHS → 전체 저장 조회/중단 복원이다.
profile 구현/검증2–3집중시간 잠정이며 전체 완료 날짜는 실측/global 예산 뒤 갱신한다.
실제 품종/작기 입력·국내 독립 검증 자료·crop Run은0건이다. 생과·자원·Decimal 경제 연결과
현장/미래 예측·추천·G0–G4/배포는 별도이며 현재 관문은`not_assessed`다.
