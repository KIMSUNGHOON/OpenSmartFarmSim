# 같은 저장 상태의3D·과실 수량 화면 수용 — 2026-10-31

[새 화면](http://localhost:5182/supply-production-replay.html)에서 같은 원 시점의 실제 잎·줄기3D,
모형 과실 저장량·구간 유출, 원50구획과 그래프를 함께 확인한다. 집중42검사·전체 웹/새 설정
타입·공개233파일 빌드·실제 Chrome38시점/3800좌표·12추가 상태와 원본 보존을 통과했다.
이 연구 화면의 소프트웨어 연결을 수용하며 실제 품종/한 작기·생과 수확·구매·마진·추천이나
최종 사실감 R2를 수용한 것은 아니다. 새 유한 preview는 **오늘15:19 KST까지**다.

[계약](../contracts/supply-terminal-screen-v1.md), [같은 원본 조회](supply-terminal-browser-implementation-20261031.md),
[기계 증거](artifacts/supply-production-stored-screen-20261031.json),
[실제 데스크톱](artifacts/supply-production-desktop-20261031.png) ·
[모바일](artifacts/supply-production-mobile-20261031.png) ·
[원본 오류 보류](artifacts/supply-production-hold-20261031.png).

## 사용자가 확인할 수 있는 동작

- 시점 슬라이더·이전/다음·그래프 점·키보드·재생을 조작하면 단일 조회 객체의 원 morphology와
  같은 index/정확 at/출현 전후 phase의 C/N 수량이 함께 바뀐다. 실제 WebGL 잎/줄기를 유지하며
  구획 수량을 임의 개별 과실 mesh·숙기/모양으로 만들지 않는다. 과실 수 상당량은 연속 모델량이다.
- 탄수화물과 과실 수 상당량의 저장량을 원 단위로 보여준다. 집계 시작 시점을 선택하면
  **현재3D 선택 시점까지**의 terminal 유출 합을 읽는다. 더 앞 시점으로 이동하면 시작도 조정한다.
  원점 누적을 생산량으로 세지 않으며 단일 시점 합은0, 같은 시각의 before/after5경계 유출도0이다.
- 원50구획의 C/N 좌표·정확 분수/단위·원 frame/CP/receipt/시각/기간 증거를 보존한다.
  표시만 소수6자리로 반올림하고 아주 작은 비영량은 `<0.000001`로 구분한다.
  그래프는 원 저장 순서 축이며 BigInt 비율로 표시해 큰 분모의 Infinity/NaN을 피한다.
- 메뉴 이동·새로고침·이력 뒤 같은 시점/집계 시작·기관 보기를 복원한다. 기존 화면의 저장 키를
  바꾸지 않는다. 재확인은 원본 전체를 새로 검증하고 실패 시 기존3D/수량을 지운 뒤 보류/재시도를
  제공한다. 대기 초를 표시하며 가짜 계산 완료율을 만들지 않는다.

원 source root `84daf00c44a964f904aa0b78e2c64f44c2753ec97641f23566fdfcc349bf4476`의
305181/1024초→512초/38시점 연구 재생이다. 시작 전의 상태나 전체 작기를 생성하지 않았다.
동일한 기존101파일을 읽으며 새 모델/RHS·제품 Codex CLI·DB/API/worker 실행은0이다.
농장/외부 자료의 현재 권리·서명 custody를 자체 공개 QA snapshot으로 대신하지 않는다.

## 실제 검증

신규 선택/표시14검사와 기존 선택16·원 수량 조회12를 합한42검사가 통과했다. 잘못된 선택,
source별 저장·URL/집계 끝 결속, 작은 수량/큰 분모·잘못된 단위/범위, 변경 후 재검증·취소/늦은
응답을 검사한다. 전체 웹 타입과 별도 새 Vite 설정 타입, 독립 공개 빌드233파일이 통과했다.
처음의 JSX 닫힘과 독립 타입 명령의 `--ignoreConfig` 누락은 실패 기록을 남기고 수정했다.

DevTools MCP가 없어 기존 설치 Playwright와 별도 프로필의 실제 Windows Chrome156.0.8078.74를
사용했다. 원38시점을 각각 실제 그리기 증가까지 기다린 뒤3D at/phase·표/두 수량 그래프·원3800좌표,
정확 stock/구간 합을 기존 독립 Decimal4030항목으로 감사한 Python 참조에 대사했다.
부분 창·메뉴/reload/이력/그래프 선택·재생 끝/유휴·제어한 visibility pause와 모바일390px,
WebGL 실패 시 수량 유지, 원본503 때 전부 제거/재시도를 포함해 추가12상태도 통과했다.
정상/대체 동작의 오류·경고와 외부 요청은0이다. 의도한503 오류1은 별도 phase로 보존했다.

첫 smoke는 원 시작/끝·합계·메뉴/reload와 실제133730삼각형/57draw call을 확인했다.
첫 전체 시험은48상태 통과 후 접힌 증거 영역을 열지 않은 테스트 절차 때문에 멈췄다.
이를 보완하고 JSON 키 순서의 문자열 비교를 값 비교로 바꾼 최종 시험이 통과했다.
시각 검토에서 발견한 활성 버튼 hover 대비를 새 화면에 한정해 수정했고 실제3종 버튼의
글자/배경 대비8.565를 확인했다. 이 검사는 전체 접근성 인증을 뜻하지 않는다.

## 디자인·자원·기존 자료

12ui0.2.65의 기존 C를 이어3영역의 연속 페이지와 실제 prototype을 생성했다. 기존 실제3D/
아이콘·제어를 보존하고 생성된2개 수량 패널/기간·구획 영역의 스타일을 적용했다. 사진, 예시 날짜/
센서 측정·증가율/수확 사실과 정적 그래프는 채택하지 않았다. 단일 실제3D와 원 저장값을 유지한다.
원 winner와 a/b를 각각 원래의 변경 없는 LayerDoc으로 무료 파생해 실제 root/그래프/구획 캡처에
target-based improve를 실행하고 각 kit/영역을 검토했다. 세 kit은 target-only **unanchored**이며
DOM coverage0·recurring token delta 없음, 추출 자산 없음의 제한을 기록한다. 생성 prototype/
원 스타일을 재사용한 기능적 비교이며 사진·픽셀 일치나 R2의 완료로 보고하지 않는다.

변환은 완료됐지만 첫 artifact 수집과 첫 standalone prototype은 WSL 합산1GiB를 넘어 종료됐다.
완료 변환을 재구매/변경하지 않고 prototype 단계에만 Node/Chromium 메모리·단일 renderer 설정을
적용해 원 inventory/analyze/build/runtime·모든 prototype gate를 통과했다. gate/원 HTML은
바꾸지 않았다. 최종 합산 peak1042903040bytes, PID peak373817344bytes였다. 첫 종료의 순간
남은1프로세스는 후속 authoritative `/proc` 조회에서 현재 probe 조상을 제외해0을 확인했다.

최종42검사16.387초·전체 타입3.757초·새 설정1.260초·공개 빌드1.799초·실제 전체 브라우저39.568초·
보존2.522초에 terminal0을 확인했다. guard4500원 항목·선행456source/1output·보존 체인의
private:false/public:true CAS124항목/원 입력32항목·기존 GUI/5175/5181과 새233파일을 보존했다.
기존5181은13:34 KST 만료를 유지한다. 소유 test build v1을 종료하고 v2로 바꿀 때 새 preview의
**처음 정한15:19 KST 만료를 연장하지 않았다.** 제어 프로세스 FD4→4·최종 소유 자식0이다.
Windows/전체 host RSS는 미계측이며 전체 backend/frontend suite·새 CI는 실행하지 않았다.
기본 브라우저에 새 로컬 URL을 전달한 exit0만 확인했고 일상 프로필/열린 탭은 읽지 않았다.

## 다음 한 단계

표시 연결 뒤에는 현재600초 기반·Context2MiB/공개 최대2034765bytes의 제약을 보존하며
**한 작기의 상태·이력·forcing 경계와 첫 장기 수치 계약**을 정한다. 현재 RHS/CP·기존 긴 cycle
재사용 대조0.5–1h, 상태/계보 참조·forcing/관리 의존성0.5–1.5h, 첫 구현 수용 기준/독립 검증
분해0.5–1h로 잠정1.5–3.5집중시간이다. 상한 숫자만 늘리거나 옛 typed handle/166일 수용을
새 형태 결합의 수용으로 가장하지 않는다. 이후 forcing/관리·기후, 장기/분할/cold/수지,
명시 η/DMC/수확·급배액/설비 구매량과 같은 기간 Decimal 경제·거시/수급을 연결한다.

국내 독립 raw 측정0·국내 첫 품종 미확정과 권리/QC/available_at·독립 작기/후보 비교 확보는
개발과 병행한다. 실제 자료/전체 제품 완료일은 미정이다. native gpt-6.1-sol/xhigh 판단과 출력
지문을 기록했고 재귀 Codex CLI0, G0–G4 미평가/R2 미승인·전체 goal active/incomplete를 유지한다.
