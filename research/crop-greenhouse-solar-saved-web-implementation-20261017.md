# 일사 저장 계산과 같은 UTC의 웹 3D — 2026-10-17

[기계 증거](artifacts/crop-greenhouse-solar-saved-web-implementation-20261017.json) · [저장 웹 계약](../contracts/web-crop-greenhouse-solar-replay-v1.md).

## 수용 범위와 사용자 산출물

**S2a 저장 화면 개발·기록 응답 회귀를 수용한다.** 소스 `c500c79588e7eb1220454d1fe57a3f5473446ec8`의
Solar 전용 소비자·선택 연결·14개 브라우저 시험이다. S1a의 원 정상/hold HTTPS6응답을
기록한 전송 시험이며 제품에는 fixture fallback을 추가하지 않았다. **실제 API 연결
S1b/S2b, 실행 중3D S3, 사용자 적용/재시작 S4와 최종 UI 디자인은 미수용이다.**
localhost5173/5174에는 기존 수용 서비스를 유지했다. 새 Solar 선택자는 아직 그 주소에 배포하지 않았다.
캡처 상단의 개발 기록은 CI 캡처 당시의 이전 게시 판본이다. 현재 진행 기록은 이 검증 뒤 별도로 갱신한다.

확인 가능한 실제 Chromium 캡처:

- [첫 저장 시점](artifacts/greenhouse-solar-initial-desktop.png)
- [마지막 저장 시점](artifacts/greenhouse-solar-completed-desktop.png)
- [보류 진단과 확정 출력](artifacts/greenhouse-solar-hold-desktop.png)
- [빈 출력](artifacts/greenhouse-solar-empty-desktop.png)
- [모바일·WebGL 소실 뒤 표](artifacts/greenhouse-solar-mobile-fallback.png)

이는 합성32초 연구의 수치 모식도다. 실제 품종의 형태·숙기·생과 kg·수확량·구매 에너지·사업성 예측이 아니다.

## 제품 변경

`GreenhouseSolarReplay.tsx`가 해당 모델의 별도 ID/summary/samples/events 클라이언트를 사용한다.
`CropReplay.tsx`는 Solar 선택과 최초 ID prefix를 연결한다. 기존 geometry/scene/chart/CSS/잎 자산을
재사용하고 다른 모델 타입으로 캐스팅하지 않는다. 생장·열·수확·비용 수식이나 계수는 바꾸지 않았다.

정상3/보류2의 원 microsecond UTC에서108상태·50구획,41연속/6사건 장부·15수지와 허용 예산을
표·그래프·실제 WebGL의 LAI/구획/온도 표현과 대사했다. PAR/NIR의 원 열 경계·광학·분배·수지·
입력 hash와 작물 입력 광량, 환기 진단, 관리 사건의 직전/직후 진단을 보존한다. 재생은 다음
저장 시점으로만 이동한다. 실패 경계·시작/끝의 가상 프레임이나 중간 상태를 만들지 않는다.

빈 출력과 잘못된 단위 등은 원 응답을 변형한 계약 반례이며 별도 원 서버 출력/현장 측정으로 간주하지 않는다.
선택 변경·계정 변경·취소·401/403/404/422·혼합 판본/단위는 이전 값과 장면을 제거한다.
늦은 응답은 취소/계정/화면 전환 뒤 복구하지 못한다. 빈 출력, 키보드·동작 줄이기·모바일 폭과
WebGL 소실 때의 원 표/시각 이동도 확인했다. 원 fixture331,274bytes의 SHA-256은
`b9be03e0dc7ea9e5ac9aa80bfbf7e013d855acdbfc77dc6f89f2e14df672a908`로 유지했다.

## 실제 검증

| 실행 | 결과와 범위 |
| --- | --- |
| [39009679433](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/39009679433), c36dfe4 | 연결 집중19개·전체 타입/단위/build/audit 통과. 첫 연결 뒤 닫힌 폼을 시험 helper로 다시 열었으며 기존 기대값·요청은 보존했다. |
| [39009965582](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/39009965582), b720890 | Solar13/기존 환기·공동기후24 = 집중37개 통과. 전체 회귀를 뜻하지 않는다. |
| [39010122550](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/39010122550), c500c79 | **전체 웹 브라우저243개/26파일·단위1,864개/35파일·타입/build/audit 통과.** Solar14개를 포함하며 앞의 집중 수를 더해 고유 검사 수를 늘리지 않는다. 백엔드 전체 CI/G1/G4 수용은 아니다. |
| 36245:0 / 80867:0 | 로컬242/243개 수집·소스/원본/5root/기존 서비스 보존. 실행 통과 수가 아니다. |
| 원 디자인 대조 | 원 main/past/empty의 변경 없는 LayerDoc과 실제 CI PNG를12ui로 대조했다. 이미지 입력의 unanchored 계획이며 DOM 매핑/시각 정합 통과를 주장하지 않는다. 최종 U5는 남는다. |

호스팅 Chromium 결과는 WSL 동시 용량 수용을 대신하지 않는다. 로컬 전체 compiler/실제 브라우저는
이 단계에서 다시 실행하지 않았다. 기존 S1b의 합 RSS hold3회와 native/실행 중 부모 hold는 그대로다.
로컬 guard는5root/동적 자식·512MiB/PID/합1GiB·nominal0.25초를 유지했다. 로컬 수집/디자인 대조의
실제 시간·RSS/FD는 기계 증거를 따른다. 원2,148항목·소스/기존 자산·필수 root를 보존했고
소유 비좀비/임시 PG/자격 파일 잔여0, FD4→4였다. 그림은 소유 합성 응답이며 농장 원자료가 아니다.

최초 디자인 실행의 읽기 전용 설정 갱신 실패로 잘못 실행된 수집과 이미지 모드의 URL 전용 flag
거부는 수용에서 제외했다. 반복 구매는 없었다. 이미지 계획은 token delta가 없고 원 요소에 매핑되지
않으므로 정적 예제 숫자/그림을 실제 장면에 덮어쓰지 않았다. 기존 변환 자산과 스타일을 유지했다.

## 진행 현황 게시

갱신한 공개 기록의 React/기존5173 parser28검사(`86043:0`)가 통과했다.
실제 HTTP 확인(`16257:0`)은5173/5174 양쪽200·no-store·같은 새 bytes와 원 HTML,
기존 환기 frozen2,173파일의 일치를 확인했다. 새 기록 시각은 2026-10-17T06:42:54.428434Z이며
이 게시 뒤 로컬 브라우저를 다시 실행하거나 backend/worker를 재시작하지 않았다.

## 다음 한 단계와 남은 의존성

1. **S1b:** 기존 실제 SDK/API의 동시 RSS 초과에 대한 새 할당 근거를 확보하고 필요한 작은 수정만 선택한다.
   같은 실패 조건의 재시도·한도 상향/보호 root 제거로 수용하지 않는다. 정상/hold의 실제 인증 SDK
   요청과 현재 권리/계정/판본·취소/전송 정리·원 값/단위/UTC·조회 계산/SQL 변경0이 수용 기준이다.
2. **S2b:** 수용된 S1b와 이 화면을 실제 HTTPS→저장 WebGL로 결합하고 같은 원 UTC·거부 시 제거·
   재접속·원본/기존 UI/자원을 검증한다. 이번 recorded routing으로 대체하지 않는다.
3. **S3/S4:** 독립 unpaused worker·전진 prefix/정상/hold/취소·동시 자원 뒤 실행 중3D와 고정 판본
   사용자 적용·재접속/재시작을 수용한다. 기존 관문과 생산량→자원→Decimal 경제의 후속 순서를 유지한다.

지역/품종/시설 계수의 승인 자료와 독립 농장·미래 생산/판매/비용·후보 대응 비교 자료는 외부 의존성이다.
개발과 병행하되 예측/추천 게시 조건은 기존 명세대로다. 실제 농장 Run0/G0–G4 미평가/승인False다.
집중 기록 브라우저는1.8분, 전체243브라우저는10.7분이었다. 준비·분석·전체 회귀 대기·자료 확보까지의 완료 시간은 아니다.
실제 동시 자원 문제의 수정 범위와 외부 자료 확보 일정이 정해지지 않아 **전체 완료 날짜/남은 집중시간은 미정**이다.
전체 goal은 active다. 판단은 현재 native Codex CLI gpt-6.1-sol/xhigh에서 수행했고 CLI를 재귀 실행하지 않았다.
