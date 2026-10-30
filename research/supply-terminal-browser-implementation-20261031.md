# 과실 수량의 원본 결속 브라우저 조회 수용 — 2026-10-31

기존101파일 공개 전달 경로에 과실 수량 조회를 연결했다. 새 파서는 한 번 검증한 원본에서
동일 index/정확 at/phase의 **원3D 형태 상태와 과실 수량**을 함께 반환한다. 집중46검사,
전체 웹 타입 검사, 독립 번들·실제5181 HTTP101파일/38시점 대사를 통과했다.
이 단계는 전달·조회 함수의 수용이며 새 수량 UI/WebGL 적용은 다음 단계다.

[계약](../contracts/supply-terminal-browser-v1.md),
[브라우저 조회기](../web/src/supplyTerminalReplay.ts),
[검사](../web/src/supplyTerminalReplay.test.ts),
[자체 합성 참조](fixtures/supply-terminal-window-own-20261031.json),
[기계 증거](artifacts/supply-terminal-browser-implementation-20261031.json),
[선행 Python/독립 산술](supply-terminal-window-implementation-20261031.md).

## 기존 전달의 재사용

`readSupplyMorphologyStoredQuantities`는 이미 원 Context/CP·material receipt·형태 DTO를
모두 검증해 반환한다. 이를 재사용하므로 원 자료를 복제한 새 export/서버·모델 실행은
필요하지 않았다. 기존 수용 SDK/모델/원101파일·고정233파일 preview는 변경하지 않았다.
이전 계획의 “새 불변 전달물”은 기존 불변 전달과 새 수량 인터페이스의 조합으로 구현했다.
추가 JSON은 제품 자료가 아니라 독립 대사를 재현할 **자체 합성 시험 참조**다.

`summary()`는 원 source/model/code·권리/terminal/관문을, `frame(index)`는 원 morphology와
같은 시점의 quantities를 방어 복사한다. `window(first,last)`는 원 index 양끝 포함이며
50개씩의 탄수화물/과실 수 상당량, 정확 stock/terminal lifetime·기간 차이/합계를 반환한다.
BigInt 분수로 저장된 수량을 합산/차감할 뿐 생장 식·생과 환산/경제 계산은 실행하지 않는다.
N은 질소나 개별 실제 과실이 아니다. Python 실행을 브라우저 실행으로 가장하지 않도록
새 browser schema와 **별도 backend reference 판본/코드 SHA**를 구분했다.

원 root는 `84daf00c44a964f904aa0b78e2c64f44c2753ec97641f23566fdfcc349bf4476`다.
원305181/1024초→512초/38시점·37구간·5동시점 경계의 의미와 source/권리·scope를 유지한다.
같은 시각의 조달 전·후를 합치거나 terminal 누적을 새 Context마다 초기화하지 않는다.
조회 객체 안의 수량은 같은 불변 snapshot이며 새 load마다 원본 전체를 다시 검증한다.
외부 농장 권리 철회/서명 custody를 이 자체 공개 snapshot의 검사로 대신하지 않는다.

## 검증 결과

- 신규12검사: 원101파일·38형태/수량, 첫/끝/단일/부분4창, 잘못된 선택/인덱스,
  방어 복사·성공 뒤 원본 변경 때 재검증, 첫/마지막 파일 취소, bounded no-store HTTP,
  늦은 이전 응답 거부·cancel/재시도. 기존 HTTP9·원 수량/단위/변조25검사와 합해
  최종 같은 source의46검사를 통과했다. 이전46검사는 타입 보완 전 기록으로 보존했다.
- 참조 생성은 현재 Python reader를 재계산 없이 읽어 원187565bytes/SHA
  `eb2091c898711e24b9f500f4aab0ee69783ef39765f34c6179095925e57f0368`와 동일함을 확인하고
  추가4창을 생성했다. 이 전체 결과는 선행 Decimal2200자리/4030항목의 독립 대사를 통과했다.
  신규 시험 참조355900bytes/SHA `1fdc6364e0ee55edd13b3131faf73611d52c154d5273feb273905f7974343270`는
  자체 공개 권리·원 notice/코드/자료 지문과 `software_reference_only_not_field_data`를 보존한다.
- 전체 웹 TypeScript 검사를 통과했다. 최초 타입 오류는 기존 파서가 반환하는 원 metadata의
  정적 추론 경계였으며 기존 모듈을 수정하거나 cast로 건너뛰지 않고 원 object 경계로 읽었다.
- 독립 ES 번들103666bytes/SHA `34f50894c7f1a2592532dea0500f6229dd8552a24b4e2a1e09649cdb79ade114`를 만들었다.
  [Vite 공식 library mode](https://vite.dev/guide/build#library-mode)와 설치된8.3.3을 확인했다.
  이 번들은 검증용 private 산출물이며 사용자 페이지에 적용한 빌드가 아니다.
- 별도 Node 프로세스가 실제 `http://127.0.0.1:5181/`에서101개 고유 원 파일/14197795bytes를
  한 번 읽었다. 같은38형태와3800C/N좌표·stock/누적·37차이/5경계/합계·추가4창이 Python과
  모두 같고 공개101파일을 보존했다. browser window 응답187638bytes·검사 내부3.155초는
  이 환경의 한 관측이며 제품 처리량·브라우저 초기 렌더링 시간 보장이 아니다.
- 선행450source/1output,437source/1output과 전체 보존 체인의 CAS124항목·원 입력32항목,
  guard4500원 항목/기존 GUI·두 보호 preview를 확인했다. 기존5175/5181은 HTTP200,
  고정233파일·같은 PID/시작/boot/당초13:34 KST 만료를 유지했다.

RED1은 임시 Vitest 설정의 CJS/ESM 경로 오류로 테스트 시작 전 실패했고, 설정을 단순화한
RED2에서 새 모듈 부재를 확인했다. 최초 신규12검사는 통과했다. 메모리 보존 범위를 줄이고
타입 경계를 보완한 뒤 최종46검사·전체 타입·번들/실제 HTTP·보존을 모두 terminal0으로 확인했다.

| 최종 단계 | Guard wall | WSL PID peak / 합산 peak |
| --- | ---: | ---: |
| 같은 source의46검사 | 34.336초 | 356941824 / 425443328bytes |
| 전체 웹 타입 | 4.037초 | 436703232 / 505122816bytes |
| 독립 번들 | 1.523초 | 168140800 / 236630016bytes |
| 실제 HTTP/38시점 | 4.589초 | 165675008 / 234307584bytes |
| 원본/GUI·preview 보존 | 2.538초 | 42692608 / 111243264bytes |

각 단계는 PID512MiB/합산1GiB·600초/로그4MiB·0.25초 표본 한도 안에서 종료했고
controller FD4→4·소유 자식0이었다. Windows/전체 host RSS는 미계측이다.
새 모델/RHS·CLI/DB/API/worker 실행0이며 전체 backend/frontend suite·새 브라우저/WebGL·CI는
실행하지 않았다. 실제 HTTP 검사를 브라우저 수량 표시의 수용으로 세지 않는다.

## 다음 화면과 남은 의존성

다음은 이 단일 조회 객체를 기존 실제 잎/줄기3D·시점 선택/재생·표/그래프에 연결하는 단계다.
새 sibling 화면/동일 상태 연결0.5–1h, 수량·단위/기간 선택·실패/재시도0.5–1h,
실제38시점/동시점·메뉴/reload/모바일/유휴·보존 검증0.75–1.5h로 잠정1.75–3.5집중시간을
계획한다. 실제 렌더링/검증 증거로 갱신하며 최종 사실감 R2를 자동으로 완료하지 않는다.

한 작기 forcing/관리·기후 결합, 상태/이력 분리와 paging/장기 수렴·분할/cold/수지,
명시 η/DMC/수확 배정·설비 구매량/같은 기간 Decimal 경제/거시·수급은 후속이다.
국내 독립 raw 측정0·국내 첫 품종 미확정과 실제 자료 권리/QC/available_at·독립 작기/후보 비교
확보는 개발과 병행한다. 전체 제품·자료 확보 완료일은 미정이다.
실제 native Codex CLI gpt-6.1-sol/xhigh 판단·출력 지문을 기록했다. 재귀 CLI0,
G0–G4 `not_assessed`, R2 `not_approved`, 전체 goal active/incomplete를 유지한다.
