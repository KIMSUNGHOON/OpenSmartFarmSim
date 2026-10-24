# 잎 생애 결과의 권리3종 연구 export — 2026-10-24

상태: **자체 합성 결과의 export를 소프트웨어 범위로 수용**.
[계약](../contracts/crop-leaf-lifecycle-export-v1.md), [기계 증거](artifacts/crop-leaf-lifecycle-export-20261024.json),
[실제 출력40파일 장부](artifacts/crop-leaf-lifecycle-export-files-20261024.csv)를 제공한다.
구현 commit은 `3e949487f8201abf835cd3e5962374e9cf149f10`이다.
[앞선 불변 수치 결과](crop-leaf-lifecycle-artifact-20261024.md)를 사용하며 새 생장 계산은 하지 않는다.

## 구현과 통과한 검증

기존 exporter 패턴을 사용해 source와 다른 새 output만 작성한다. appearance/관리/stem의 use/display/redistribute를
각각 확인하고 권리3종을 그대로 보존한다. root·두 program·준비·초기 state·stem root/program의 원7파일과
12개 원 DTO를 내보낸다. current/last와 active/removed/pending, UTC/ID/나이/면적/합계는 원 reader와 같다.
frame descriptor는 원 input/state/result/stem SHA와 공개 DTO의 bytes/SHA를 구분한다.
원 source graph/권리를 재검사하고 output directory identity/owner/mode·파일 목록/bytes/SHA를 확인한 뒤 index를 마지막에 게시한다.
기존 output을 덮어쓰지 않는다. 부분 파일은 완료 묶음이 아니다. 농장 권한·서명·G0나 제품 Run 게시를 승인하지 않는다.

최종 source의 **새30/관련81·고유111검사**가 통과했다. 새30, lifecycle reader68, 기존 appearance export13이다.
앞선591과 pilot을 합산하지 않는다. 두 시나리오/같은 bytes 반복, source3종 각각의 실제 redistribute=False,
늦은 use/display/redistribute9거부, 원 입력/준비/초기/비선택 결과·디렉터리 mode의 늦은 변경,
작성 bytes 변조3·쓰기/rename 실패2·같은/내부 output 거부2·output mode/교체/여분 파일3을 확인했다.
거부/부분 실패에서 완료 index는0이며 원 자료를 보존했다.

최초 red23건은 exporter 부재22건과 시험 입력 Fraction 변환 오류1건이었다. 입력을 수정한 red v2는
exporter 부재로 실패했다. 첫 green은29통과/시험 source-output 이름 충돌1건이었으며 source 내부 쓰기 거부가 정상 동작했다.
시험 디렉터리를 분리한 최종111을 수용한다. 두 시험 구성 오류를 제품 버그 수정으로 보고하지 않는다.

## 실제 두 결과와 별도 프로세스

각각31blob인 원 두 결과를 생장 모듈 없는 별도 Python 프로세스에서 내보냈다.

| 결과 | 원 artifact SHA | 완료 index SHA | 파일/시점/추적 상태 |
| --- | --- | --- | --- |
| 무제거 | `c1ae9fc67c6eb045b114cc0a0f38d8164b31384989ea5c9e9722d85302aad8fd` | `b589ed9009dc6ea6c2b35a3c8fa199aaf4b8b917ee62f34be430b56673763c5d` | 20/12/47 |
| 명시 제거 | `33b77aa4ab641918ec249701bab59d7e645b5a8083bc456a9f51b2788ffe9ff9` | `6d70cca86c686a70f4a9a8bbb889656e2362438807850aef3b7cb425a3aa8331` | 20/12/47 |

원24 DTO/94추적 상태를 typed reader와 다시 대사했고 원7파일씩의 bytes/hash·권리3종도 같았다.
허용된 crop reader/parser9개 외의 생장/준비/producer import를 차단했다.
DB/CLI/network·출력 밖 쓰기0, FD4→4와 원 lifecycle62blob·appearance52blob/stem29blob의 bytes/metadata 보존을 확인했다.
여기서 export의 파일쓰기는 허용된 새 output에 한하며 계산 없는 reader의 파일쓰기0과 구분한다.
독립 생물학 검증이나 새로운 나이/면적 oracle 검사는 아니다. 이전 수치 결과의 소프트웨어 수용을 전달한다.

최종111은46.11초·PID104,194,048bytes/보호+소유 합575,545,344bytes, fresh는2.70초·PID96,387,072bytes/합516,268,032bytes였다.
모든 phase의 기존4root/2,793감시 항목·source/FD4→4·소유 잔류0을 확인했다.
.25초 표본/512MiB PID·합1GiB/600초/로그4MiB를 유지했다. Windows Chrome/전체 host 수용은 아니다.
native CLI `gpt-6.1-sol/xhigh`, turn_context `2026-10-24T02:07:11.569Z` 원 LF SHA
`790daef8732d5d7d7fa8b0e2c31547b8bb37f2dcc1c01c5be110ab1f194c8560`·재귀 CLI0이다.
새 의존성/DB·키·기존 화면 변경0이다. 전체 backend·새 hosted CI/브라우저·사용자 적용은 실행하지 않았다.

기록 검증은 코드2개/graph code40개·JUnit111개·출력40행/파일과 실제 원문/frame38개 SHA를 대사했다.
상대 링크3,352개와 새 파일 staging을 포함한 변경의 공백/줄바꿈 검사도 통과했다.

## 다음 한 단계

다음 산출물은 **strict SDK와 active renderer adapter**다. 두 export의 원 index/source/frame bytes/크기/SHA,
40code/원 root/두 program/준비/초기/stem 연결·권리3종과 닫힌 schema·단위·정확 전체/마지막 시각을 확인한다.
원24 DTO/94상태·면적/개수를 보존하고 active만 기존 renderer용 현재 잎으로 투영한다.
removed 마지막 나이/면적/시각과 pending 예약은 별도로 보존한다. 혼합/변조·취소/부분 load에서는 표시를 보류한다.
생장 재계산0·기존 DTO/화면 보존이 수용 기준이며 React 화면 연결은 그 다음 자식이다.

SDK/adapter는 계약/fixture10–20분+strict parser/변경20–40분+adapter/대조10–20분+기록10–20분으로
**50–100집중분**의 낮은 신뢰 추정이다. 기존3D35–70분+실제 브라우저/배포·기록25–50분을 더하면 연구 화면까지
**110–220집중분**이다. 이전 export45–90분 예상은 위 실적으로 대체한다. 농장/runtime·외부 자료 확보 시간은 포함하지 않는다.
현재 사용자 화면에는 새 제거를 적용하지 않았다. 농장/현재 SourceRecord·서명/실행과
[국내 독립 자료 획득](independent-domestic-cherry-tomato-data-20261024.md)은 병행하며 원측정/미사용 독립 국내 작기0·국내 첫 품종 미확정이다.
생산/자원·Decimal 경제·시장/거시/수급·자율 비교, R2/첫 cold shader·G0–G4와 전체 완료일 미정은 유지한다.
