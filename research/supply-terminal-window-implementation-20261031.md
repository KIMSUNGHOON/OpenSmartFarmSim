# 저장 과실 구획·terminal 기간 조회 수용 — 2026-10-31

기존 저장 결과의38시점에서 과실 탄수화물량과 과실 수 상당량 각각50구획,
정확한 원점 기준 terminal 누적과37개 구간 차이를 읽는 조회기를 구현했다.
집중19검사와 별도 프로세스의 독립 Decimal4030항목을 통과해 이 연구 소프트웨어
경계를 수용한다. 여기서 N은 과실 수 상당량이며 질소량이 아니다.
새 생장 계산·실제 수확·생과kg·판매·예측/추천 승인이나 새 화면 적용은 아니다.

[계약](../contracts/supply-terminal-window-v1.md),
[조회기](../backend/app/crop_supply_terminal_window.py),
[집중 검사](../backend/tests/test_supply_terminal_window.py),
[기계 증거](artifacts/supply-terminal-window-implementation-20261031.json),
[선행 작기/생산 검토](season-production-readiness-20261031.md).

## 원본과 산술

원 공개 artifact `84daf00c44a964f904aa0b78e2c64f44c2753ec97641f23566fdfcc349bf4476`의
62파일 CAS·6Context/33CP/5조달점을 기존 reader로 매 요청 검증한다.
시작305181/1024초→512초의 실제 저장 창이며 시작 전 시점을 생성하지 않는다.
원 index/at/phase·Context/CP/receipt/event/cursor/prefix와 frame/state SHA를 보존한다.

CP는 그 CP의 원 lifetime에, CP 없는 dense-before는 실제 검증한 receipt의 pending
lifetime에 연결한다. 같은 출현 시각의 before/after5쌍은 별도 행으로 남고 유출 차이는0이다.
독립 검증은 receipt 투영을 재사용하지 않고 같은 정확 시각/후속 사건의 **별도 저장 seed**를
대사했다. 같은 면적 기준의 원50좌표를 보존하고 float64가 나타내는 값을 Fraction으로
정확 합산한다. 단위는 `mg_CH2O/m2_floor`, `fruits_equivalent/m2_floor`다.

창은 원 index의 양끝 포함이다. 누적을 Context마다 초기화하지 않으며 구간 차이의 합은
실제 창의 마지막−첫 누적과 정확히 같다. 단일 시점 창은 구간0개·합계0이다.
최초 누적을 창의 생산량으로 세지 않는다. 과실 수 상당량의 소수부를 개별 실제 과실 ID나
성숙도·위치/모양으로 바꾸지 않았다. CH2O→DM/FW 환산·등급/실제 수확·판매량도 만들지 않았다.

## 통과한 검증과 보존

- 집중19검사: 원38시점/3800구획 좌표·정확 stock/누적·37차이/5동시점·합계,
  첫/끝/단일/부분 창·9잘못된 선택·방어 복사·현재 파일 권한/늦은 source 변경·현재 코드
  지문, 시각 역전/원점 혼합·누적 감소·동시점 양의 유출·단위/phase 오류 거부.
- 별도 cold 프로세스: Decimal2200자리로4030수량 항목을 원 바이트에서 독립 대사했다.
  전체 창과 부분3–9창이 일치하고 결과187565bytes/SHA
  `eb2091c898711e24b9f500f4aab0ee69783ef39765f34c6179095925e57f0368`다.
  출력은 private 검증 파일이며 아직 public 전달물/제품 API가 아니다.
- 생장 모듈10개를 import 차단하고 import 시도0·로드0을 확인했다. 조회를 포함한 import
  구간의 파일 쓰기/프로세스/네트워크를 감사 hook으로 차단하고 DB connect를 거부했으며
  시도0이었다. 모델/RHS·농장 Run0, 공개101파일/별도 CAS62파일의 바이트·메타데이터와
  조회 FD3→3을 보존했다. 이 파일 검사는 외부 농장의 현재 권리/서명 custody를 대신하지 않는다.
- 선행445source/2output 및 기존437source/1output, 전체 보존 체인의 원 자료/기존 GUI와
  private:false/public:true CAS124항목·입력32항목을 다시 검사했다. guard의4500원 항목,
  보호 프로세스, 새 preview의 고정233파일·동일 PID/시작/boot/만료를 보존했다.
  기존5175와 새5181은 실제 HTTP200이었다. 브라우저/WebGL은 이번에 다시 실행하지 않았다.

최초 RED는 모듈 부재, 첫 GREEN은 `_load`의 `(bytes,metadata)`를 bytes로 취급한 연결
오류였으며 원본을 바꾸지 않고 수정했다. 두 번째 GREEN에서 독립 수치 대사는 통과했지만
테스트가37구간에38왼쪽 시점을 strict zip한 오류를 고쳤다. 최종19검사/독립 검증/보존은
모두 실제 terminal0을 확인했다. 실패 로그를 성공으로 재명명하지 않았다.

| 최종 단계 | Guard wall | WSL PID peak / 합산 peak |
| --- | ---: | ---: |
| 집중19검사 | 26.945초 | 167051264 / 235610112bytes |
| 별도 cold/독립 산술 | 6.582초 | 132657152 / 200986624bytes |
| 선행 source/GUI·preview 보존 | 2.538초 | 42999808 / 111325184bytes |

PID512MiB/합산1GiB·600초/로그4MiB·0.25초 표본 한도 안에서 종료했다.
controller FD4→4·소유 자식0이다. Windows/전체 host RSS를 계측한 것은 아니다.
기존2MiB/512frame/32768scalar·현재 코드/파일/embedded rights 검증과 최종 재검사를 유지했다.
전체 backend/frontend suite·새 CI·새 브라우저 검사는 실행하지 않았다.

## 다음 단계와 외부 의존성

다음은 **같은 원본에 결속한 전달/strict 파서 → 같은 시점의 표시**다. 첫 자식은 기존
재배포 허용 자체 자료의 새 불변 전달물·원 root/frame/code/단위/권리 결속·현재/늦은 변경 거부,
독립 수치 대사·원 화면/preview 보존이다. 준비/전달0.5–1h와 파서/실패·독립 검증0.5–1.5h로
잠정1–2.5집중시간을 계획한다. 뒤따르는 실제 표/그래프·3D 시점 동기화와 브라우저 검증은
인터페이스 크기 확인 후 따로 산정한다. 과실 구획 수치를 임의 과실 mesh로 바꾸지 않는다.

농장/API/worker 연결에는 원 source custody·현재 외부 권리의 별도 수용이 필요하다.
한 작기는 forcing/관리·기후,600초 기반/현재 Context 최대2034765bytes의 상태·이력 분리,
paging/장기 수렴·분할/cold/수지가 남았다. 이후 명시 η/DMC/수확 배정·설비 구매량과
같은 기간 Decimal 경제/거시·수급을 연결한다. 독립 국내 raw 측정0·국내 첫 품종 미확정,
실제 계수/초기 상태/면적/QC/available_at·독립 작기/후보 비교 자료 확보는 개발과 병행한다.

실제 native Codex CLI gpt-6.1-sol/xhigh 근거와 출력 지문을 기계 증거에 연결했다.
재귀 CLI0, G0–G4 `not_assessed`, R2 `not_approved`, 전체 goal active/incomplete다.
과거10월22일09시 기한을 새 날짜로 바꾸지 않았으며 전체 제품·외부 자료 확보일은 미정이다.
