# 등록 수확의 실제 SCRAM/HTTPS 연결 수용

2026-10-09 00:09:41 KST. native Codex CLI `gpt-6.1-sol / xhigh`, 재귀 CLI0회.
[공개 영수증](artifacts/crop-harvest-runtime-tls-implementation-reference-20261009.json)에 원 도구 종료·450 source·실제 HTTPS와 정리 증거를 결속했다.
선행 [보호된 reader factory](crop-harvest-protected-factory-implementation-20261008.md)를 재사용했다.

## 사용자 확인 산출물

[계약](../contracts/crop-harvest-runtime-tls-v1.md)·[소유 dependency fixture](../backend/tests/crop_harvest_tls_fixture.py)·
[집중 시험](../backend/tests/test_crop_harvest_runtime_tls.py)의3 core파일이다. 제품 수식·계수·운영 기본값은 변경하지 않았다.
기존 보호된 loader가 실제 module을 import해 표준 ApiRuntime/HTTPS 서버를 구성했다.
같은 실제 SCRAM DB의 계산 부모1건/파생 수확1건을 조회했고, 소유120걸음 계산과 합성 환산/배정의 원6행을 보존했다.
영수증의 공개 JSON에서 원 수량·UTC·단위·계수/배정 판본·미배정/hold·승인false를 확인할 수 있다.
새 화면/3D는 아직 연결하지 않았다. 소유 private bundle·권리/시계 제어는 시험 전용이며 운영 계정/제품 CLI 증거가 아니다.

## 통과한 검증

| 대상 | 실제 범위 |
| --- | --- |
| 집중 시험 | 새2개(새 Python import1·실제 SCRAM/HTTPS1)+기존 route72개=고유74개·원 도구79223 종료0 |
| HTTPS | 인증서 검증·no-store·query/code header·요약/원6행/두 분할/빈 끝·재구성 후 동일 결과·총17개 전체 응답 |
| 응답 한도 | 최대 25.699592초 / 59,463bytes. 각 전체 본문30초·2MiB 이내 |
| 거부 | 미인증401·조회 scope403·다른 tenant/없는 ID404·현재/투영 후 표시 철회422·소유 시계 만료403·선택 page/HEAD 변조422 |
| 보존 | 같은 원 result/farm/parent·6행/요약/UTC/단위/정확 수량·입력/설정/artifact bytes/mode/inode·DB counts |
| 읽기 | 계산 권리는 철회하고 표시 권리만 유지. 조회 중 RHS/행 재생성/증명 발행/게시0·custody FD0 |
| 복원·정리 | 서버/thread2개 종료·FD11→11 및 대상/device/inode 동일·private24개/양쪽 schema·role/passfile/PG/임시 경로0 |

요약은 서명된 root/summary를 검사하며 반환하지 않는 전체 page 검사로 표시하지 않는다.
페이지 변조 거부는 실제 해당 records 요청으로 확인했다.
첫 표준 서버 구성의 로깅 초기화가 닫는 pytest `/dev/null` FD1개를 별도 기록했다.
남은 FD identity를 보존하고 그 구성 직후부터 두 HTTPS 실행의 동일성을 검사했다.

최종 실행 2026-10-09 00:03:34 KST→2026-10-09 00:09:25 KST, 준비부터351.059초였다.
원600초 상한·nice19·0.1초 감시3,291표본에서 primary RSS239,456,256bytes≤512MiB,
PG/controller 포함 RSS 합326,733,824bytes≤1GiB였다.
공유 page가 중복될 수 있는 소유 PID 합이며 WSL 전체/production 용량 수용은 아니다.
별도 감사에서 원 종료0·450 source·세 core snapshot·현재 원 값·권리/자원/비밀 정리를 확인했다.

## 보존한 실패와 수정

앞선 네 실행은 원 종료1이며 수용하지 않았다. (1) 소유600 결과 증명을400 입력 helper로 읽은 오류,
(2) 공유 시험 fixture가 유지한 미사용 입력 FD1개, (3) 선택 page 변조를 summary로 요청한 잘못된 probe,
(4) HTTPS17개 완료 뒤 로깅 초기화 이전 FD 기준12와 최종11의 불일치였다.
각각 명시600 결과 reader·export 뒤 미사용 context 종료·records/HEAD 별도 probe·첫 서버 구성 뒤 FD 기준으로 수정했다.
기존400 입력 계약·custody FD0·최종 FD identity·17개 응답/30초/2MiB·전체 집중74개 범위를 유지했다.
네 원 종료/정리/로그 hash와 별도 실제 파일 권한 진단을 보존했으며 제품 코드는 그대로다.

## 다음 한 단계와 외부 의존성

`crop-harvest-runtime-tls`와 선행 자식을 합친 `crop-harvest-api-runtime` 부모만 추가 체크한다.
다음 SDK는 계약·닫힌 응답 decoder/client·집중 시험·필요한 공개 소유 JSON의3~5 core파일로 나눈다.
원 ID/farm/provenance/UTC/단위/정확 수량/미배정/hold를 보존하고 순차 페이지·전체성·취소·혼합/비정상 응답 거부,
타입/빌드·집중 검증을 통과해야 한다. 그 뒤 같은 UTC 수확 표/저장 수치3D→기후/물·양분/구매 에너지→Decimal 경제다.

새 SDK/UI/WebGL·전체166일 질량 부하·전체 backend suite/hosted CI/push·제품 CLI는 실행하지 않았다.
실제 품종 입력/환산 계수·국내 독립 자료·실측 작물 Run0건, G0–G4 `not_assessed`다.
생산/미래 마진/추천·원격 Backend 실패·구형25시간 원 종료 유실 hold는 유지한다.
완료 시각은 위 작은 검증의 실측이며, 독립 자료 확보 일정이 없어 최종 production 완료일은 확정하지 않는다.
