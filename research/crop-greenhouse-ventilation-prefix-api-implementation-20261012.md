# 환기 모델의 계산 중 확정 결과 API — 2026-10-12

## 수용 범위

`crop-greenhouse-ventilation-confirmed-prefix-api`를 합성 입력의 로컬 소프트웨어 범위로 수용한다.
[계약](../contracts/crop-greenhouse-ventilation-prefix-v1.md)과
[기계 증거](artifacts/crop-greenhouse-ventilation-prefix-api-20261012.json)에 현재 코드10파일의 SHA와 원 도구 종료를 남겼다.
새 모델의 실행 중 실제 WebGL·사용자 서버 적용은 다음 단계다. 실제 농장 Run0·G0–G4 `not_assessed`를 유지한다.

## 변경

- 별도 reader가 서버에서 수용된 선택자의 원 sample/event와 UTC를 읽는다. 계산 전진·임대 갱신 중에도
  선택한 사건·서명 계보를 확인하며 권리 철회·취소·역행·변조는 거부한다. 조회의 수치 계산·DB 쓰기는0이다.
- typed 공개 응답은 새 모델의108상태·25장부·10수지·환기 진단을 보존한다.
  `/crop-greenhouse-ventilation-execution/prefix`와 `/samples`, `/events`를 보호 HTTPS에 연결했다.
  같은 selector를 요구하며64시점/8사건·2MiB 한도, 전후 인증과 서버 내부 witness 검사를 적용한다.
- 공통 변경은 `api.py`, `api_runtime.py`, 새 모델의 operator loader3파일이다.
  새 설정 판본과 명시 flag를 요구하며 기존 설정에서는 기능이 꺼져 있다. 수치 모델·저장 형식·기존 client/scene은 바꾸지 않았다.

## 검증

| 범위 | 통과 결과 |
| --- | --- |
| 공개 형식·HTTP 제어 |204개. 닫힌 형식·모델/단위/수지·요청/응답 한도·인증·현재 권리·기본 비활성 |
| 실제 SCRAM reader |18개. 원 값/UTC·이전 판본·fresh process·ready/끝/65시점64+1페이지·독립 전진/heartbeat·권리/취소/서명/파일 변조·terminal 전환 |
| 실제 인증 projection/검증 TLS |11개. 인증 projection2·HTTPS9, 같은 원 selector/값/UTC·전후 권리·독립 전진/취소·witness·정상/보류 완료 |
| 실제 명시 runtime/독립 자동 작업자 |4개. 장벽 없는 정상/보류·취소·기본 비활성. 정상/보류 각각 같은 선택자의 사건/생장200을8회 읽고 원 terminal 값/UTC와 대사 |
| 새 설정과 기존 회귀 |146개 중 새 prefix42·기존104. 구 모델 실제 SCRAM/검증 TLS1개 추가 |
| 최종 보존 |원6624 실제0. 기존279source 중276불변·공통3변경, 현재172자산·원본2,148항목·두 frozen source/자산·보호4root 유지 |

새 prefix279개와 기존 호환105개를 합친 **고유384개**다. 마지막 설정 검사146개에 포함된 새42개를 중복 합산하지 않았다.
현재 code10파일은 각 수용 실행의 source pin과 대사했다. 이전 공개 형식 실행 이후 바뀐 runtime 시험 fixture는
현재 명시 runtime4개와 설정42개를 통해 다시 확인했다.

독립 자동 실행은64걸음/합성128초·chunk8이며 정상/보류의 공개 요약에서 선택자를 얻었다.
running 성공을 직접 DB 탐색이나 계산 정지 장벽으로 대체하지 않았다.
private PG16MiB/32연결 어댑터는 시험용 자원 설정만 바꿨으며 기계 증거에 SHA를 보존했다.
이 자동 실행의611.483초 receipt에는562.32초 pytest 후 보존/정리가 포함된다. 전체 receipt가600초 안이라고 주장하지 않는다.

인증 projection과 HTTPS 모듈을 합친 원37325는6개 기능 통과 뒤 두 module fixture가 같은 정리 증거 파일을 써서
실제1로 종료됐다. DB schema/role0 검사 뒤 발생한 파일 이름 충돌이다. 이 실행을 최종 통과 수에서 제외하고
모듈별 원74202/79709의 정상 종료·정리0으로 확인했다. 이전 RSS 실패와 시험용 `start`/`offset` 인자 오류도 보존했다.

## 사용자 화면과 자원

WSL 상한512MiB/1GiB·nice19·단일 스레드·0.25초 RSS 샘플을 유지했다.
자동 실행의 자원 창에서는5174를 계속 제공하고5173만 점검했으며,
[같은 결과/접속 정보로 복구](product-ui-waiting-feedback-20261012.md#0744-kst-후속-복구와-실제-표시)한 뒤 후속 검사는 두 화면을 유지했다.
API 수용 실행의 최대 단일/합산 RSS는189,706,240/1,042,001,920bytes다.
종료된 수용 실행에서FD4→4·소유 프로세스/PG/임시PG/passfile잔여0을 확인했다.

최종 대사에서 modern112작업/370사건/37attempt·464파일/권리/키,
legacy89작업/47,809sample/5사건/47,813수확행·결과 키·접속 token을 보존했다.
5174는 재시작하지 않았다. 기존 사용자 화면에 새 모델을 배포했다는 뜻은 아니다.
두 주소의 공개 개발 기록은 단계 검증 뒤 갱신하며15초마다 조회한다.

원65200 실제0으로 **08:31:56 KST**의 최신 기록을 두 실제 브라우저 화면에서 확인했다.
같은 원 기록/실제 DOM5단계·다음 자동 조회·인증정보/쓰기/pageerror0·양쪽390px·2–4시간/미배포/전체 완료일 미정을 확인했다.
브라우저의 최대 단일/합산 RSS는260,898,816/995,356,672bytes이며 두 화면과 원본/소유 정리도 통과했다.
[5173 현재 표시](artifacts/crop-greenhouse-ventilation-prefix-status-5173-20261012.png) · [5174 현재 표시](artifacts/crop-greenhouse-ventilation-prefix-status-5174-20261012.png).

## 다음 단계와 일정

1. 새 모델 전용 실행 접수/상태/취소와 prefix의 typed 웹 client를 연결한다.
   원 selector·manifest·페이지·UTC·판본/권리 오류를 검사하고 기존 모델 응답을 받아들이지 않는다.
2. 같은 실행의 원 확정 sample/event를 기존 장면·차트·표에 연결한다.
   실제 장벽 없는 정상/보류 계산 중 원 값/UTC/WebGL→terminal, 취소/재접속/철회 시 장면 제거와 WSL 상한을 확인한다.
3. 검증한 웹/API/worker를 사용자 서버에 적용하고 기존 결과·키·권리·두 주소를 대사한다.

API 잔여 검증을 마친 현재, 웹 client/실행 중3D 검증1.5–3집중시간과 사용자 적용0.5–1집중시간으로
**남은2–4집중시간**을 잠정 추정한다. 고정 완료 시각이나 전체 제품 완료일이 아니다.
전체 작기 생산량·자원 사용·경제/수급·최종 UI와 독립 농장 자료·권리·관문은 후속이다.
전체 backend/원격CI·새 모델의 실제 실행 중WebGL/사용자 적용·독립 농장 검증은 이번 API 수용에서 실행하지 않았다.
