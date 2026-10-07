# 새 실제 DB·HTTPS·3D 기능 검증과 종료 기록 보류

2026-10-08 KST. [시험 TLS 발급 순서 수정](web-crop-cycle-calculation-native-tls-hold-20261008.md) 후
같은 수정 실행의 pytest 로그는 **1통과 / 1,665.51초(27분45초)**로 종료했다.
[기능 검증·별도 정리 영수증](artifacts/web-crop-cycle-calculation-native-observed-reference-20261008.json)에
실제 원값/HTTP/WebGL/권리·변조 검사와 source/로그·캡처 SHA를 보존한다.
native Codex CLI `gpt-6.1-sol / xhigh`에서 판단했으며 재귀 CLI0회다.

## 확인한 실제 경로

실제 SCRAM의 소유 등록 합성 입력4개를 계산·서명·DB 게시하고 보호 설정 loader의
같은 jobs/farm/store/query를 통해 기존 App에서 읽었다. native 브라우저는 응답 route 대체를 사용하지 않았다.

| 저장 사례 | 실제 계산 | 출력 |
| --- | --- | --- |
| 25시간 정상 | 11,400걸음·92 bounded 호출·완료 | 원27시점/5관리 사건 |
| 확인 과거 보류 | 0걸음·수치 hold | 실패 평가 전 원1시점/0사건 |
| 빈 보류 | 0걸음·수치 hold | 0시점/0사건 |
| 출력 없는 완료 | 120걸음·완료 | 0시점/0사건 |

25시간 advance 루프는1,320.889221초, DB 게시·증명·현재 조회를 포함한 준비는1,351.419795초다.
원 수치/단위·명시273일 UTC 이동과 이번 저장 결과의 동일 ID/reference/manifest·두 validation 객체를 대사했다.
총34frame 방문에서 고유27시점/5사건의 원 기관량·50 C/N 구획·LAI를 표·그래프·mesh와 비교했다.
현재7시점/2사건만 유지하고 보류 시각을 새 정상 frame으로 만들지 않았다.

실제 HTTPS는24응답(정상21·권리/변조422 두 번·계정403 한 번)이다.
정상 전체 본문 최대 **5.516900초/66,841bytes**, 기존30초/2MiB·`no-store`를 유지했다.
브라우저 fetch/reader와 실제 ASGI 처리 최대 동시성은 각각1이고 종료 후0이다. socket 개수 측정은 아니다.
조회 중 parser/context/QC/RHS/advance/put/새 증명 발급은0이다. 결과4행과 jobs/events는 전후 같다.
유효 HMAC의 잘못된 steps도 거부했고 현재 권리·계정 거부 후 이전 값/장면 제거와 정상 복구를 확인했다.
실제 WebGL loss/restore·모바일·키보드·동작 줄이기와 장면/차트/observer/listener/timer/RAF 정리를 통과했다.
pageerror는0이나 SwiftShader ReadPixels 경고와 의도한403/422 console 오류는 남긴다.
GL context loss/GC 가능성은 검증했으며 driver GPU bytes나 실제 기기 성능을 측정한 것은 아니다.

실제 [데스크톱](artifacts/calculation-cycle-native-desktop.png),
[모바일](artifacts/calculation-cycle-native-mobile.png), [과거 보류](artifacts/calculation-cycle-native-past.png),
[빈 보류](artifacts/calculation-cycle-native-empty.png),
[출력 없는 완료](artifacts/calculation-cycle-native-empty_completed.png)를 보존했다.
데스크톱·모바일·빈 보류를 직접 확인했다. 기존 캡처는 보존했고 pixel fidelity는 미수용이다.

## 별도 정리와 남은 기록 누락

원 도구 handle과 감시 프로세스가 유실돼 감시기의 최종 종료 코드/RSS 영수증이 없다.
실제 시험 PID는 종료했고 위 pytest terminal 로그·브라우저 보고서·Python 후속 검증 보고서·
fixture의 schema/role/passfile0·실제 host SCRAM 기록은 남아 있다.
별도 관측에서 해당 PG 임시 디렉터리와 살아 있는 소유 프로세스/FD/cwd 참조가 없음을 확인한 뒤
기록된 소유 임시 tree만 제거했다. 원118 source와 실행3 core SHA는 같다.

**원 pytest/감시기 종료 코드는 `null`이며0으로 추정하지 않는다.** 기능 검증을 확인한 범위와
별개로 최종 native·웹 부모 체크는 원 명령 종료 기록 누락 때문에 보류한다.
관측 유실만을 이유로 같은25시간 계산을 재시작하지 않았다. 작은 기능 검증의 보류를
후속 독립 비용 측정의 착수 조건으로 만들지 않는다.

## 다음 구현

[등록 누적 비용 측정](crop-cycle-calculation-prefix-cost-prepared-20261008.md)의 실제 시험을
이전 실행 정리 후 시작했다. 감시기 자체를 독립 세션으로 유지하며 첫 전체 관측 예산은20분이다.
정상/hold의 원량 대사 → 32회 누적 곡선 → 전체166일 농장·경제 기간 등록/비용과 필요한 개선 →
전체 저장/복원·같은 UTC3D → 생과·자원·Decimal 경제 순서를 유지한다.
전체166일 등록 저장/API/3D는 미완료다. 실제 품종 입력·국내 독립 자료·측정 작물 Run은0건이며,
G0–G4 `not_assessed`·예측·추천 보류는 그대로다. 이27분 시험으로 최종 제품 완료 날짜를 추정하지 않는다.
