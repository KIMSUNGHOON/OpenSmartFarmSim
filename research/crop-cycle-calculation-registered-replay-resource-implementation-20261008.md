# 같은 등록 DB→실제 App/3D의 작은 자원 검증 — 2026-10-08

## 수용 범위

[계약](../contracts/crop-cycle-calculation-registered-replay-resource-v1.md)의 작은 경로를
[실제 원 명령·최종 감사 기록](artifacts/crop-cycle-calculation-registered-replay-resource-reference-20261008.json)으로 로컬 수용했다.
고유 시험 **2개**, 원 명령 **종료 0 / 89.679888초**이며, 시험 자체는 88.99초다.
원 source **392개**와 선행 수치·제품 경로 294개를 보존했다. 선행 303개 중 바뀐 것은 소유 검증용 세 파일뿐이다.
조사·판단은 현재 Codex CLI `gpt-6.1-sol / xhigh`에서 수행했고 재귀 CLI 실행은 0이다.
기존 기능 수용과 화면은 [이전 기록](crop-cycle-calculation-registered-replay-harness-implementation-20261008.md)에 그대로 둔다.

| 확인 항목 | 실제 결과 |
| --- | --- |
| 계산·게시 | 실제 SCRAM의 같은 DB, 120걸음·원 3시점/3사건, 별도 Python 완료 게시·종료 0 |
| 현재 조회 | 조회 RHS 0, 원 입력/config/artifact·FD 목록 보존, custody FD 0 |
| 실제 App/3D | 실제 빌드 파일→native Nginx→보호 HTTPS→WebGL, 응답 대체 없음 |
| 값·시점 | 원 C/N 50구획씩·LAI·UTC·표/그래프, 3관리 사건의 전/후/제거량 대사 |
| 현재 권리·계정 | 철회 422→장면 제거→복원, 다른 계정 403→장면 제거·unmount |
| HTTPS | 8응답, 최대 2.392831초 / 35,816bytes, 기존 30초/2MiB, 성공 응답 no-store |
| primary RSS | 150,097,920bytes ≤ 512MiB |
| 동시 소유 pipeline RSS 합 | **1,048,477,696bytes ≤ 1GiB**, 0.1초 간격 820회 표본 |
| PostgreSQL tree RSS | 표본 최대 119,189,504bytes, pipeline 집계에 포함 |
| 정리 | primary/controller/계산·게시/Node/Chromium/Nginx/PG 종료, 역할·schema·passfile·임시 tree 0 |

RSS는 primary 자손과 재부모화된 소유 PG tree, controller의 **고유 PID별 동시 RSS 합**이다.
공유 페이지를 중복 집계할 수 있고 PSS·WSL 전체 메모리·표본 사이 순간 최대값을 뜻하지 않는다.
이번 표본 최대값의 여유는 약 **24.09MiB**다. 전체 166일이나 일반 운영 브라우저의 여유를 입증하지 않는다.

## 실제 검증 설정과 화면

- `npm run build -- --outDir <owned-private-directory>`: 타입 검사/빌드 종료 0,
  1.861500초·pipeline RSS 857,903,104bytes. 실제 빌드 161파일을 전/후 대사했다.
- 선택한 native Nginx **1.30.5**의 공식 소스·서명·공식 키를 HTTPS로 받고 GPG 검증했다.
  전용 경로에서 `make -j1`, 준비 원 명령 종료 0 / 52.309865초, RSS 140,599,296bytes.
  시스템 패키지 설치나 서비스 시작은 하지 않았다. native 실행은 배포 컨테이너 동등성/G4 증거가 아니다.
- 제품 `web/nginx.conf`의 TLS/CA/hostname 검사를 유지하고 소유 경로·loopback port만 치환했다.
  시험 인증서에 `localhost` SAN을 추가했다. 기존 공용 fixture·제품 Nginx 설정은 보존했다.
- Node `--max-old-space-size=64 --max-semi-space-size=2`, Chromium
  `--enable-unsafe-swiftshader --no-zygote`, 데스크톱 **1024×768**·모바일 **390×844** viewport 캡처다.
- 소유 시험이 CDP `HeapProfiler.collectGarbage`를 캡처 뒤와 사건 화면 전환 뒤 **2회 명시 호출**했다.
  각각 실제 응답 `{}`와 전/후 heap 지표를 기록했다. 첫 호출 후 같은 원 geometry를 다시 대사했다.
  따라서 이 수용은 명시한 시험 설정에 한정한다. 제품의 기본 브라우저 메모리 성능 수용이 아니다.
- pageerror 0. SwiftShader ReadPixels GPU stall 경고 4개와 예상한 422/403 console 오류 2개를 보존했다.
  빌드의 큰 chunk 경고도 보존했다.

[실제 데스크톱 화면](artifacts/registered-cycle-resource-desktop.png) ·
[실제 모바일 화면](artifacts/registered-cycle-resource-mobile.png).
둘 다 실제 App의 **LAI·과실 구획 수치 모식도**다. 막대는 계산 구획의 비교 표시이며
실제 토마토 형상·과실 크기·숙기·생과 수확량을 표시하지 않는다.

## 앞선 시도와 수정 근거

모든 시도의 원 종료·로그 hash·자원 정리 감사와 다음 수정 전 source 고정을 보존했다.
표본 RSS는 중단 시점이 서로 달라 전체 경로의 개선율로 비교하지 않는다.

| 자원 시도 | 원 종료 | 초 | 표본 pipeline RSS bytes | 관측된 보류 이유 |
| --- | ---: | ---: | ---: | --- |
| baseline | 2 | 66.939 | 1,129,529,344 | 개발 Vite 시작 중 상한 초과 |
| production | 2 | 68.795 | 1,094,168,576 | Vite preview 시작 중 상한 초과 |
| nginx-v2 | 1 | 309.758 | 976,486,400 | 인증서 DNS SAN 불일치의 실제 502·실패 후 stdin 대기 |
| nginx-v3 | 2 | 74.317 | 1,075,564,544 | 인증서 수정 뒤 브라우저 구간 상한 초과 |
| viewport | 2 | 75.056 | 1,084,645,376 | 캡처 전 상한 초과; 그 시점에는 효과 미확인 |
| nozygote | 2 | 78.043 | 1,093,971,968 | 원 3시점 대사 뒤 full-page 캡처 중 상한 초과 |
| final | 2 | 79.712 | 1,076,748,288 | 1536 viewport 캡처 구간 상한 초과 |
| desktop1280 | 2 | 84.041 | 1,112,657,920 | 두 캡처 뒤 사건 검증 전 상한 초과 |
| desktop1024 | 2 | 76.450 | 1,103,089,664 | 사건 조회 중 상한 초과 |
| nodeheap | 2 | 79.299 | 1,084,080,128 | Node heap 제한 뒤에도 사건 검증 전 상한 초과 |
| collection | **0** | **89.680** | **1,048,477,696** | 원량·권리·정리와 자원 모두 통과 |

상한 초과에는 소유 primary에 SIGINT를 보내고 실제 종료를 관측했다. nginx-v2의 낮은 RSS는
정상 경로의 자원 수용이 아니다. 실패한 browser 자식의 -9를 정상 종료로 바꾸지 않았다.
native Nginx 최초 준비의 IPv6 네트워크 실패도 원 종료 1로 보존하고, 후속 준비는 명시한 IPv4로 새 경로에서 실행했다.
최종 시험 2개에 앞선 실패·중복 import 검증을 합산하지 않는다.

## 다음 단계와 보류

다음은 **전체 166일을 같은 DB로 유지할 실행 구성의 준비**다. 준비 전 원 마감을 고정하고,
계산→원 전체 47,809행/5사건·121상태/수지의 bounded streaming 대사→게시→API/대표 3D→정리를 연결한다.
작은 경로로 그 구성을 먼저 확인한 뒤 전체 실행을 별도 착수한다. 원 9시간 상한과 원 8초 RK4/300초 출력을 유지한다.
전체 166일의 등록 DB/API/3D는 아직 시작하지 않았으며 이 작은 측정에서 완료 날짜를 외삽하지 않는다.

새 생과 수확량·물/양분·구매 에너지·작물 손익 연결, 실제 제품 CLI와 독립 G1은 후속이다.
실제 품종 입력 0·국내 독립 검증 자료 0·실측 농장 작물 Run 0이며 G0–G4는 `not_assessed`, 예측·추천은 hold다.
Backend hosted 수용/host HBA 증거 보류와 push 보류도 유지한다. 전체 Backend/웹 시험은 반복하지 않았다.

공식 도구 근거: [Nginx 소스/서명](https://nginx.org/en/download.html),
[공식 키](https://nginx.org/en/pgp_keys.html),
[Node heap 옵션](https://nodejs.org/api/cli.html#--max-old-space-sizesize-in-megabytes),
[CDP collectGarbage](https://chromedevtools.github.io/devtools-protocol/tot/HeapProfiler/#method-collectGarbage).
실제 채택 버전·호출·다운로드 hash/서명과 회수 시각은 hash로 고정한 비공개 준비 기록에 있다.
