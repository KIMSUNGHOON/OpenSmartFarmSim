# 검증 계산 결과의 실제 runtime·SCRAM·HTTPS — 로컬 수용

2026-10-07 KST. [개발 계약](../contracts/api-crop-cycle-calculation-transport-v1.md)의 runtime/TLS 자식과
작은 API/transport 부모를 **소유 합성 등록 결과의 소프트웨어 범위**에서 수용했다.
[고정 영수증](artifacts/crop-cycle-calculation-runtime-tls-reference-20261007.json)에 실제 native Codex CLI
`gpt-6.1-sol / xhigh`·재귀 CLI0회·명령/종료/source/로그 SHA와 정리를 보존한다.
전체166일 등록 경로·새 client/3D·hosted·실제 농업 정확도와 관문 수용은 별도다.

## 변경·검토

[runtime](../backend/app/api_runtime.py)이 이미 조립한 exact 새 store/query 두 객체를
`create_app`에 전달하도록 연결했다. 원 runtime 시험은 전달된 동일 객체까지 확인한다.
[실제 TLS 시험](../backend/tests/test_api_crop_cycle_calculation_tls.py)은 원 보호 설정 loader,
실제 SCRAM DB/등록 농장/현재 source 권리·signed 결과와 새 route를 연결한다.
trusted operator factory는 같은 시험 프로세스 안에서 제공한다. 별도 배포 plugin이나 실제 제품 CLI의 증거는 아니다.

정확성·가독성·구조·보안·비용의 다섯 축을 검토했다. 원 API·모델·store/query·operator loader/helper와
기존 시험81 source SHA가 그대로이며, runtime의 명시 kwargs 외 제품 동작/서비스/계수/CI·HTTP 한도 변경은 없다.
현재 수치 대사는 별도 짧은 solver의 결과를 사용하지만 같은 물리 rates를 공유한다.
독립 농장 검증 또는 독립 농업 모델의 정확도 비교로 보고하지 않는다.

## 실제 검증과 실패 이력

| 실행 | 결과 |
| --- | --- |
| runtime 전달 RED → GREEN | 1실패/12.80초 → 1통과/13.27초 |
| 첫 전체 HTTPS | 비활성 fixture/source policy 불일치·1실패/253.70초 |
| 실제 DB에서 source policy 두 경우 원인 확인 | 2통과/23.64초 |
| 두 번째 전체 HTTPS | 마지막 FD12→11 검사·1실패/2통과·276.96초 |
| 원 HTTPS logging의 FD 원인 확인 | 1통과/0.93초·DB 실행0 |
| 최종 실제 SCRAM/TLS 전체 | **3통과/278.41초** |
| 현재 runtime 전체 | **19통과/15.52초** |
| 관련 runtime/설정/route/OpenAPI 회귀 | **315통과/117.01초** |

최종 세 실행의 고유 시험은 **337개 분할 검증**이다. 원인 확인·반복 RED/GREEN은 합계에 더하지 않는다.
단일337개 또는 전체 backend 수용이 아니다. 원 실패의 로그·command/source/정리 영수증을 모두 보존했다.
첫 실패는 비활성 설정에도 활성 policy의 source factory를 반환한 시험 구성이 원인이었다.
같은 실제 DB/grant/typed dependencies에서 source policy만 선택 설정에 맞추면 조립됐다.
제품의 거부 검사를 유지했다.

두 번째 실패는 원 `HttpsApiService.server()`의 logging 설정이 pytest logging-plugin의
`/dev/null` file handler FD 하나를 닫은 결과였다. 작은 시험에서 그 FD만 사라지고
나머지 target/device/inode 및 두 번째 설정 전후 목록이 정확히 같음을 재현했다.
첫 서버의 로깅 설정 뒤, 네트워크 시작 전 기준을 잡았으며 최종에는 원 strict FD 개수와
target/device/inode 전체 일치를 함께 검사했다. logging 교체·GC·허용 오차나 `<=` 완화는 없다.

## 실제 HTTPS·원량·권리

소유 등록 결과는 정상120걸음/3시점/3관리 사건, 확인 과거 hold60걸음/1시점/1사건,
빈 hold0걸음/0시점/0사건이다. 원 manifest/validation·양·UTC와 순차 sample/event·빈 마지막 page를 대사했다.
보호 config loader와 환경 loader로 같은 시험 프로세스에서 HTTPS 서버3개를 순서대로 생성·종료했다.
별도 OS 프로세스 재시작이나 실제 운영 배포 검증은 아니다.

실제 Bearer/TLS **전체26응답**은 200×17,401×1,403×1,404×1,422×4,503×2다.
전체 본문 최대는 **5.258614초·23,546bytes**로 기존30초/2MiB 안이다.
no-store·query version/code header·비공개 필드 부재, 현재 입력/source 권리 철회와
byte 투영 뒤 철회, 실제 source 권리 없음·다른 tenant/권한, 올바른 시험 HMAC으로 다시 서명한
summary 변조·live grant 변경의503, 명시 비활성/authority grant 제거의503을 확인했다.
이 작은 응답 지연을 전체166일 HTTP 지연으로 외삽하지 않는다.

준비 뒤 parser/context/QC/RHS/advance/put/입력·결과 proof 발급을 금지했다.
jobs89/job_events89/새 결과3/thermal Run0은 전후 같고 원 입력·설정·TLS·custody의 hash/mode/inode도 같다.
로깅 설정 뒤 FD11→11과 전체 target/device/inode 동일, custody FD0·request principal 해제,
서버 thread3개 종료·소켓 해제와 최종 SCRAM 암호 인증을 확인했다.
최종 TLS의 DB schema/role/passfile0·PG PID/data 부재·임시 tree 정리도 확인했다.
runtime1개/회귀3개의 소유 PG도 순차 종료·정리됐다.
nice19·최종 TLS 주 시험 프로세스의 표본 최대 RSS169,197,568bytes이며 PG 합산/WSL 전체 peak가 아니다.

## 다음 단계와 보류

[새 SDK → 현재 범위/3D → 실제 WebGL 계약](../contracts/web-crop-cycle-calculation-replay-v1.md)에 따라
다음은 SDK4 core파일이다. 새 ID/manifest/validation을 구형 형식으로 바꾸지 않고 원량/UTC와
현재 범위·직렬 요청·철회 의미를 보존한다. 작은 웹 연결7–12집중시간은 작업 분해의 잠정치이며
실제 통과/실패로 갱신한다. 전체166일 등록 prefix/복원 비용·생과/자원/Decimal 경제·자료 확보는 포함하지 않는다.

remote `353bffb`의 C0/웹/작성 PG는 성공, 앱 검증은 기존 설정 필드 거부로 실패했다.
Backend는3분할 성공/2진행/1대기로 관측했으며 기존 live 증거를 취소할 push/rerun은 하지 않았다.
앱 설정 생성 호환 수정은 로컬 수용했지만 해당 수정과 이번 변경의 hosted 수용은 남아 있다.
실제 품종 입력·국내 독립 검증 자료·실제 작물 Run0건, G0–G4 `not_assessed`다.
생과 수확·구매 에너지·미래 마진/작물 순위와 최종 제품 완료 날짜는 필요한 증거 확보 전 보류한다.
