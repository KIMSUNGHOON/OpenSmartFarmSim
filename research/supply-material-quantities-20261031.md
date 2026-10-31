# 같은 material 창의 과실·연속 자원 수치 — 2026-10-31

[새 읽기 전용 조회](../backend/app/crop_supply_material_quantities.py)와
[계약](../contracts/supply-material-quantity-window-v1.md)을 수용했다. 원4시점/50구획의
과실 탄수화물·수량 저장량과10개 연속 누적량/선택 구간 차를 원 source/cursor/phase에 결속한다.
새 root에 이전 Context/CP 참조를 만들어 넣지 않는다. 실제 수확/생과 무게·관개/에너지 구매·
판매/요금·수익/추천을 계산한 것은 아니다. [3D 화면](http://localhost:5183/supply-material-replay.html)은
기존4시점을 유지하며 새 수치 패널은 다음 단계다.

원 source의 units와 `_flux`/climate RHS를 exact native `gpt-6.1-sol/xhigh`에서 대조했다.
terminal C/N 외의8개 자원 counter는 현열/잠열, 유입/유출 열, canopy/air 외부 열,
exchange/외부 수증기의 **부호 있는 연속 적분량**이다. 명시한 이 channel만 읽으며
별도 물질점 이동·구매 계량기나 전체 농장 사용량으로 바꾸지 않는다. 새로운 계수/품종·요금/무게 변환0이다.

## 검증

- 같은 최종 코드의 신규40검사와 공개 fixture1검사, 고유41개가 통과했다. 원4×100 stock 좌표와
  정확합8개,10counter×3interval·0시간 채택 전후·선택/한 frame 창과 망원합을 독립 대조했다.
  음수 external vapor를 그대로 보존하고 terminal 감소·잘못된 float/bool/index/layout/단위·비유한/음수 stock,
  양수 탄수화물/0수량·거짓 boundary/sequence·원 권리·늦은 원본/자기 코드 변경·방어 복사/2MiB를 확인했다.
- 별도 cold 프로세스는14개 생장/owner 모듈 import를 차단했고 조회의 DB/network/CAS put/하위 process·CLI 호출0,
  원 파일 bytes/metadata와 FD 보존을 확인했다. 모델/RHS를 다시 계산하거나 source에 쓰지 않는다.
- 원 공개106파일에서 별도101blob CAS를 만들고 실제 조회했다. 독립 Decimal(precision300)의400좌표/8합계와
  30구간 counter가 원 저장값에 일치했다. 조회2.1275초·결과40,481bytes,
  SHA256 `ccc1d63a51279017b4b8400d8dfc5cbb59da8b23a7be899858ecb273f2010dbd`.
  FD4→4·원101파일 metadata 보존, 새 모델/DB/network/CAS 쓰기/CLI0이었다.
- [공개 합성 QA fixture](fixtures/supply-material-quantity-own-20261031.json)는 이 실제 결과와 코드/root/
  NOTICE·권리/단위/생성 시각을 보존한다. 관측 시각은 null·QC는 software-only이며 G0–G4 미평가/R2 미승인이다.
  원 공개 use/display/redistribute가 모두 true일 때만 생성했고 private false 결과의 권리를 승격하지 않았다.

첫 RED는 없는 import의 수집 실패였다. 첫40검사는 통과했으나 응답 한도 시험이 원본 한도에서 먼저
거부될 수 있음을 자체 검토에서 찾았다. 새 모듈의 응답 한도를 분리하고 정확한 거부 사유를 검증한
최종40검사가 통과했다. 이후 같은 코드에 공개 fixture 검증1개만 추가 실행했으며 이전40개 시험 본문은
그대로 보존했다. 현재 CLI 메타데이터를 읽을 때 이전 로그의 비정상/대형 행을 만났고,
제한된 UTF-8 scanner로 현재 turn의 정확 model/effort/CLI version·LF hash만 확인했다.
초기 기록과 실제 출력은 [기계 증거](artifacts/supply-material-quantities-20261031.json)에 보존한다.

원657source/4output·UI private307개·기존 source/CAS/불변 export/GUI 사슬과
237고정 HTTP 파일·boot/PID/start/첫 만료·4,500원 항목을 대사했다. 새 실제101blob도 보존했다.
최종40검사40.50초/guard41.782초·PID 최고173,219,840bytes/합계396,718,080bytes,
실제 조회 guard5.796초·보존 guard5.820초였다. WSL PID512MiB/합계1GiB를 유지했고
모든 소유 단계는 terminal·잔여0/FD4→4였다. 사용자3D/기존 미리보기와 만료를 변경하지 않았다.
전체 backend/frontend suite·새 UI/browser/DB/API/worker/hosted CI는 실행하지 않았다.
기존93SDK/17화면/상위39검사는 이번41개에 재실행한 것으로 합산하지 않는다.

다음은 이 원 수치·참조를 공개 DTO/strict SDK와 같은3D 시각의 패널에 연결하는 일이다.
고정 hash/bytes·권리·범위/단위/부호·취소/latest/변조와 실제 browser·메뉴/reload·오류 때 이전 값 제거를
수용 기준으로 유지한다. 남은1.5–3집중시간의 잠정 추정이며 실제 구현/검증 후 갱신한다.
이후 명시된 조달/판매량·단가/요금·근거/기간의 Decimal 비용 연결을 검토한다.
독립 국내 raw0·첫 실제 품종 미확정/긴 작기·경제/거시/수급·자율 비교와 G0–G4/R2,
전체 goal은 미완료이며 실제 생산·수익 예측의 완료 날짜를 정할 근거는 아직 없다.
