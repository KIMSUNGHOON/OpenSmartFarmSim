# 저장 면적·기후 결과의 export와 strict SDK — 2026-10-24

상태: **연구 fixture 전달과 SDK 소프트웨어 수용**. [계약](../contracts/growing-geometry-web-replay-v1.md),
[기계 증거](artifacts/growing-geometry-web-20261024.json), [276파일 장부](artifacts/growing-geometry-export-files-20261024.csv).
[원 저장/계산 없는 조회](crop-growing-geometry-artifact-20261024.md) 다음 단계다. 새 계산의3D/사용자 적용은 아직 남아 있다.
기존5176 잎 생장·제거3D/서버·DB·키·기존 source는 변경하지 않았다.

## 산출물

[exporter](export-growing-geometry-replay.py)는 원11source/17checkpoint/17DTO와 마지막 index를46파일로 전달한다.
원 blob bytes/권리·원 모델/단위/ID/정확 grid·4profile의 출처/권리/검토 metadata와 Clear BSD notice를 보존한다.
새 소유 output만 허용하고 overwrite/symlink/원 source 안이나 상위 output을 거부한다. 파일·권리·코드 변경/부분 쓰기/rename 실패는 완료 index를 만들지 않는다.
exporter 자체의 import 때 코드와 게시 전 코드를 대사하며 계산하는 producer·생장/재개를 import하지 않는다.

[별도 자체 합성 선언](../fixtures/crop-growing-geometry-web-declaration-v1.json)으로 새로운 원 요청/결과6개를 만들었다.
기존 private6root의 redistribute=False는 유지한다. 새 선언은 자체 요청/소프트웨어 출력만 대상으로 하며 원 참고 문헌의 권리를 부여하지 않는다.
원 논문/PDF·그림·표의 전문은 포함하지 않고, 기존 연구 reference JSON의 수학 계수/출처/권리 metadata를 그대로 보존했다. 실제 품종/G0 채택은 아니다.
[재생성 도구](generate-growing-geometry-replay-fixtures.py)는 새로운 output에서 같은6root·export를 재생성한다.

[SDK](../web/src/growingGeometryReplay.ts)는 [고정 지문](../web/src/growingGeometryReplayFixture.ts)의6사례만 소비한다.
각46파일을 credential 없는 no-store GET/redirect 거부·2MiB 한도로 읽고 index/root와 모든 원 source/CP/DTO의 bytes·SHA를 대사한다.
원 leaf ID/a/A·114상태/7derived·21누적량/수지·영수증과 화면 투영·단위/정확 시각/권리를 확인한다. 상태를 보간/재계산하지 않는다.
고정 연구 fixture 소비자이며 실제 farm Run/현재 tenant 권리·서명 custody를 대체하지 않는다. 임의로 다시 해시한 외부 index는 수용하지 않는다.

## 실제 검증

- [export 집중](../backend/tests/test_growing_geometry_export.py) **18 passed**: 여섯17시점의 원 bytes/46파일/새 output 재현·권리 거부와 늦은 철회·실제 원 source 손상/출력 변조·코드/쓰기/rename/디렉터리 실패·경로 경계를 확인했다.
- [SDK 집중](../web/src/growingGeometryReplay.test.ts) **41 passed**와 전체 web 타입 검사가 통과했다. 원102 DTO/상태·모든 단위/투영·15개 wire 변조/17개 frame 변조·분수 dt·복사/취소·403/초과 응답 거부를 확인했다. 각 load는46GET이다.
- 별도 fresh exporter는 생장/초기화/재개/producer import와 DB/CLI/network·output 밖 쓰기를 금지한 채6×46=**276파일/102시점/3,149,941bytes**를 다시 전달했다. 원 export와 저장소의 모든 bytes가 같고 원444파일 metadata/bytes·FD를 보존했다. 금지 동작 시도0이다.

중간16/17 export·이전41 SDK는 합산하지 않는다. 이것은 새 생물학적 수치 검증이나 농장 예측 검증이 아니다.
처음 RED의 미구현 실패·최초 TypeScript 버퍼 타입 오류를 보존했다. 소유 ArrayBuffer 타입을 명시하고 시험 Response는 같은 bytes를 복사해 교정했다.
마지막 코드 fence 보완은6index/고정 register의 exporter 지문만 바꿨고 원 source/CP/DTO bytes는 바뀌지 않았다. 최종18/41·fresh와 타입을 다시 통과했다.
새 UI/build/browser·hosted 전체 CI는 이번 로컬 수용에 포함하지 않았다. 기존 컴포넌트/수치 코드에 변경이 없어 앞선 검사 수를 재집계하지 않는다.

최종 export wall34.585초/최대 PID81,375,232bytes·합산472,764,416bytes,
SDK2.239초/최대PID226,668,544·합산698,814,464,
fresh7.925초/합산433,078,272, 타입1.723초/최대PID514,682,880·합산905,084,928이었다.
기존512MiB/PID·1GiB 소유+보호 합산·.25초 표본/600초/로그4MiB를 바꾸지 않았고 모든 phase의 원2,966항목/4root·source/FD4→4·소유 잔류0을 확인했다.
Windows/전체 host 운영 용량 수용은 아니다.

소스 지문8개/공개276파일·상대 링크3,374개/새 Python3파일을 대사했다. 이전 private6root의 재배포False와 원102checkpoint bytes도 다시 확인했다.

현재 native Codex CLI gpt-6.1-sol/xhigh, turn_context2026-10-24T08:01:00.482Z,
원 LF 포함 SHA `0cca718c8dddf971c7f1394c13925c3a2213662b0d00c2b680660c646698f591`·재귀 CLI0으로 판단했다.
새 서비스·프레임워크/의존성이나 계정·비용 지출은 추가하지 않았다.

## 다음 사용자 산출물

다음은 이 SDK의 원 leaf ID/현재A를 기존 사실적 잎 표면·PBR 재질에 연결한 화면이다.
모델에 없는 stem/pose/attachment는 별도 제작 asset으로 명시하고 기존24시간 저장 줄기를 같은 생장 계산으로 합치지 않는다.
모든6×17시점의 실제 mesh 면적·원 표/그래프/정확 시각·URL/메뉴/reload·hold/유휴 자원과 실제 브라우저를 통과한 뒤 사용자에게 적용한다.
32초 변화량을 확대하지 않는다. 위 전달 단계는 완료했으며 남은 화면1.75–3.5집중시간은 낮은 신뢰 추정으로, 전체 완료일 약속이 아니다.
원 측정/미사용 독립 국내 작기0·첫 국내 품종 미확정이다. 정확 제거/새 출현·공급/자원/생산·경제/거시·수급/자율 선정·R2/실제 관문과 전체 완료일은 남아 있다.
