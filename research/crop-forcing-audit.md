# Axiany Reference303 원천 입력 감사 — 2026-10-04

상태: **파일·채널/QC·권리 감사 수용, 실제 forcing/작기 재현은 보류**.
검사는 2026-10-04 UTC, 후속 문서 수용은 2026-10-05 KST다.
개발 참조 범위는 Axiany/Maxifort, Bleiswijk Reference303,
2019-12-16 정식~2020-05-29 마지막 수확이다.
[채택 계약](../contracts/crop-forcing-v1.md), [등록부](crop-forcing-register.json),
[원 모델 조사](crop-tomato-model-baseline-20261004.md)를 함께 읽는다.

## 실행과 원본

동일 Codex CLI 세션 `01a0e064-b01b-7a22-8ef8-dd4afe0eb7dc`, 실제 turn context
`2026-10-04T13:25:16.916Z`의 **gpt-6.1-sol / xhigh**에서 자료 해석·설계 판단을
수행했다. CLI 재귀 실행은 없다. 판단은 검토 가능한 근거이며 G0 승인 데이터가 아니다.

DOI `10.4121/uuid:88d22c60-21b3-4ea8-90db-20249a5be2a7` 판본 2,
[기탁 파일](https://ndownloader.figshare.com/files/24757220)의 실제 형식은 **7z**다.
캐시 이름의 `.json`은 컨텐츠 형식이 아니다. archive 8,418,715바이트,
SHA-256 `b889e9ab1663fe3b8a90a3dab71d4340a6ecd49492532c43784cc82d799708ca`와
기탁 MD5를 대사했다. 52개 entry 중 Reference CSV 7개, Weather CSV 1개,
ReadMe/Economics PDF 2개만 경로/크기·CRC를 확인해 임시 공간에 풀었다.
선택 파일은 총 22,171,390바이트다. 전체 archive/CSV/PDF 원문은 Git에 넣지 않았다.

[DataCite](https://api.datacite.org/dois/10.4121/uuid:88d22c60-21b3-4ea8-90db-20249a5be2a7)와
[기탁 메타데이터](https://api.figshare.com/v2/articles/12764777)의 CC0-1.0 선언과
2020-09-23T10:41:39Z 판본 게시를 고정했다. 실제 다운로드/메타데이터 raw hash와
retrieval은 앞선 원천 등록부의 판본을 유지했다. 이번 web 도구에서는 메타데이터
접근 오류와 PMC CAPTCHA가 있어 같은 고정 캐시 bytes를 사용했다.
미래 의사결정용 `available_at`은 복원하지 않았으며 retrospective 연구 전용이다.

도구는 프로젝트 의존성에 넣지 않았다. 공식 7-Zip 26.03 Linux 임시 binary의
GitHub release digest를 대사했고 LZMA thread 1/nice 10으로 선택 추출했다.
PDF는 임시 pypdf 6.19.0으로 페이지·content stream 크기를 제한해 읽었다.
ReadMe 17페이지, Economics 5페이지의 추출 표를 CSV header와 대사했다.
추출된 논문/설명서 원문은 재배포하지 않는다.

## 실제 파일·채널과 QC

모든 수는 원 CSV를 읽은 통계다. 새로운 생장/생산량 계산이나 누락값 생성이 아니다.
등록부에는 파일별 hash·원 header·각 열의 유한/결측/형식 수·min/max와 시간차를 보존했다.

| 파일 | 실제 행/열 | 측정·가공과 주요 제약 |
| --- | --- | --- |
| GreenhouseClimate | 47,809 / 50 | Tair·Rhair·CO2air raw, Tot_PAR/Tot_PAR_Lamps 가공값. 필수 공기온도/CO₂/PAR의 공동 결측 71행, CO₂ 음수 2행, RH 범위 밖 3행. Tair 최소 -1°C는 별도 적용성 검토 |
| GrodanSens | 47,809 / 7 | 두 배지의 EC·함수율·온도. 각 센서 열 결측 2,306행. 수관 온도가 아님 |
| CropParameters | 23 / 6 | 주별 10표본 줄기의 신장/직경/화방 평균, 밀도. LAI/초기 기관량/잎 제거 질량 없음 |
| Production | 24 / 9 | 등급별 kg/m²와 10표본 줄기의 수확 과실 개수/무게. 첫 serial 43510은 후보 Excel epoch에서 2019-02-14로 작기 밖. 자동 연도 정정하지 않음 |
| Resources | 166 / 7 | 일별 공급열·조명 전기·CO₂·급액/배액. 공급열/조명/CO₂는 설명서의 가공값. 구매 전력/연료의 독립 계량/청구가 아님 |
| TomQuality | 8행, header 7열/data 8열 | Weight와 DMC_fruit 사이 delimiter 누락. 원 스키마에서는 8행 모두 거부. 문서 기반 8열 mapping 후보에서 DMC 6개/결측 2개지만 수정/환산 채택은 보류 |
| LabAnalysis | 10 / 39 | 급액·배액 pH/EC, mmol/L·µmol/L 성분. 농도는 성분 소비량이 아니며 같은 급배액/재순환 질량과 별도 대사 필요 |
| Weather | 47,809 / 11 | 외기·일사/PAR/바람/강우 등, 기상 열별 결측 71행. 외기 일사를 수관 PAR로 대체하지 않음 |

CO2air는 ppm, Tair는 °C, Tot_PAR는 µmol/m²/s다(ReadMe p3–4).
Tot_PAR는 외기 PAR와 고정 피복/화면 투과율·조명 운전에서 산출한 **실내 가공 PAR**다.
수관 위 센서 관측이나 위치/변환 오차가 독립 검증된 입력으로 자동 분류하지 않는다.
수관 온도 채널과 초기 LAI/기관·버퍼·평활 온도·온도 합은 공개 Reference 파일에서
찾지 못했다. 문헌 코드의 초기조건으로 채워 실제 품종의 한 작기를 만들지 않는다.

### 시간과 전체 작기 처리

설명서는 Excel timestamps/5분을 밝히지만 시간대·UTC offset·DST 정책은 밝히지
않는다. 1899-12-30 epoch 후보는 논문의 정식일과 첫 serial 43815가 맞는다.
이는 날짜 대조이며 UTC 승인 변환이 아니다. 기후/기상 파일은 후보 날짜
2019-12-16 00:00~2020-05-30 00:00의 규칙적 166일을 담는다.
소수 5자리 serial 차이는 0.00347일 37,184번, 0.00348일 10,624번이다.
UTC 정수 초·DST·시각의 관측/평균 의미·반올림은 확인 전 보류한다.

실제 47,808 forcing interval/47,809 sample을 그대로 현재 v1에 넣을 수 없다.
현 계약은 segment/event/output 각 20,000개와 최대 1,000,000 step이다.
166일을 10초 간격으로 계산하면 **1,434,240 step**이다. 이는 파일 길이의 산술이며
실제 solver의 성능·적정 간격·작물 결과를 시험한 것은 아니다.
`crop-cycle-capacity`를 필요한 핵심 후속으로 추가한다. 연속 상태/누적 수지·사건·
불변 입력을 유지하는 실행/저장과 선택 출력 시간을 먼저 계약하고 실제 부하/재현을
확인한다. 임의 고해상도 제거·한도 증가·파라미터 교체로 해결하지 않는다.

### 면적·관리·생과 환산·경제

ReadMe p1/9는 96m² 전체와 62.5m² growing/production area, 논문 Figure 1은
76.8m² crop-growing area를 기술한다. ReadMe의 5개 팀 구역 서술과 Reference
적용을 확인해야 한다. 어느 분모를 Reference의 floor 정규화에 채택할지 **보류**다.
[실험 논문](https://pmc.ncbi.nlm.nih.gov/articles/PMC7698269/)의 Reference303 식별,
Axiany/Maxifort·정식/마지막 수확·적심일을 파일의 날짜/밀도와 대사했다.
주별 stem_dens 4→8, plant_dens 1.4의 면적과 측정 정의·개별 관리 사건은 미확인이다.
Stem_elong는 주별 cm이며 초기 키나 전체 식물 높이가 아니다.

Production의 kg/m², 10표본 줄기의 g/개수, 주별 화방 평균을 같은 모집단으로
합치지 않는다. 상세 개화·착과/적과·적엽/제거 질량·수확 개체 사건이 없어 과실
구획의 초기조건/관리로 자동 변환할 수 없다. 품질 header mapping/DMC 표본은
환산 근거의 후보이며 날짜·표본/오차와 품종 적용성을 별도로 검토해야 한다.

Economics PDF는 연구 경진대회 계산이다. 상업 농장의 전체 인건비/자본·포장·운송·
판매 등 비용이 빠지며 Class B의 경진대회 가치가 실제 판매를 증명하지 않는다.
Resources의 계산된 공급열도 독립 구매 에너지 측정이 아니다. 이 자료로 국내
미래 순마진이나 기존 Decimal 원장의 실제 판매/구매값을 생성하지 않는다.

## 재현·수용과 다음 단계

버전 있는 [QC 도구](crop-forcing-audit.py)는 기본 Python만으로 8개 CSV를 streaming
검사한다. 원본/hash·정확한 줄 수·기탁 크기를 대사했고 두 재실행 출력이 byte-identical이었다.
행/열 수와 원 header는 별도의 첫 파일 검사 및 물리적 줄 수와도 확인했다.
파일은 변경하지 않았고 UTC forcing·실제 모델 입력·새 Run은 **0개**다.
code/raw/QC-output/tool hash는 등록부에 있다. G0 승인이나 독립 국내 G2/G3는 없다.

실행 예(선택 파일은 권리 확인 후 사설/임시 경로에 제공):

    nice -n 10 python3 research/crop-forcing-audit.py \
      --root /tmp/ossf-crop-forcing-audit-20261004 --output /tmp/crop-forcing-qc.json

감사는 완료했지만 위 시간대·면적·수관/초기조건·관리/형식 문제가 해결되기 전 실제
Axiany 전체 작기는 보류한다. 국내 동의/독립 작기는 여전히 0건이다.
다음 작은 단계는 `crop-fruit-model-spec`: 문헌의 과실 발달 구획·개수/질량식과
매개변수 단위·권리·독립 수치 검증 가능성을 고정한다. 일반 참조 계산 개발과
국내 접근/측정 준비, 전체 작기 처리 계약은 병행한다.
