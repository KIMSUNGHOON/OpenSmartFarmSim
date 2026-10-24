# 잎 제거 후 상태를 보존하는 재개 문맥 — 2026-10-24

상태: **불변 문맥/무전진 복원의 소프트웨어 수용**.
[계약](../contracts/growing-geometry-post-removal-context-v1.md),
[구현](../backend/app/crop_growing_geometry_post_removal_context.py),
[시험](../backend/tests/test_growing_geometry_post_removal_context.py),
[기계 증거](artifacts/growing-geometry-post-removal-context-20261024.json),
[36문맥 장부](artifacts/growing-geometry-post-removal-context-20261024.csv).
실제 다음 구간·분할 재개/저장3D·전체 작기와 제품/관문 승인은 후속이다.
[현재 화면](http://localhost:5176/growing-geometry-replay.html)은 앞서 수용한 합성32초 재생을 유지한다.

## 보존되는 상태

기존 고정 목록 checkpoint는 잎 수가 정해져 있어 제거 후 벡터를 그대로 받을 수 없다.
새 frozen context는 원 parent context/CP·신뢰한 SHA/코드·profile/환경과 명시 제거 입력을 결속한다.
준비할 때 기존 point를 원 CP에 한 번 적용하고, 남은 원 잎 program/현재 a/A로 사건 후 RHS를 한 번 평가한다.
point 자체의 CP 복원 RHS1회를 포함해 준비의 현재 RHS는2회다. 실제 적용 영역을 벗어나면 부분 문맥을 반환하지 않는다.
새 품종/계수·시간 전진·과거 replay/초기 면적 재정규화는 없다.

새 snapshot은 같은 정확 Fraction 경과 초/원 global index와 `after_removal_before_next_step`을 가진다.
현재 면적·나이와 다른 C/N·기후 상태, 원 전체 D0/초기 영수증·남은 잎의 원 index mapping을 보존한다.
원21개 누적량·이번 사건 C/용량/signed 현열·새 segment의 명시0 누적량은 각각 별도다.
원 program의 initial_area는 원 메타데이터이며 현재 A로 다시 초기화하는 값이 아니다.
snapshot/bytes/restore는 같은 준비 context의 최초 checkpoint만 수용하고 생장·point·RHS 계산0이다.
임의로 재해시한 후속 상태를 현재 snapshot으로 받아들이지 않는다. 기존 모델의 checkpoint와 교환할 수 없다.

이 경계는 합성 첫 사건/양의 잔여 수관·연속 leaf C/용량 유출0에 한정된다.
원 여섯32초 프로그램의 nonzero outflow를 바꾸거나 실제 농장/서명 custody·in-process 악성 코드 격리로 확대하지 않는다.
이 단계는 다음 구간을 위한 문맥이며 다음 구간을 계산했다고 보고하지 않는다.

## 실제 검증

- 새 모듈 부재 RED를 확인한 뒤67, 강화한78을 통과했다. 최종은 **신규82+기존 point71/parent continuation160=고유313**검사가133.37초에 통과했다. 중간 실행은 합산하지 않는다.
- 여섯 새 zero-continuous-outflow 조건의 초기/중간7/완료16, dt1⁄8초·한 잎/동시 두 잎 제거를 확인했다.
  원 ID/현재 a/A·다른 상태·D0/원 영수증·과거/사건/새0 장부·정확 시각과 남은 step이 일치한다.
  준비의 point1/RHS2, 조회·복원의 재계산0과 모든 JSON view 복사를 검증했다.
- 원 source 지문을 바꾼 manifest/seed의 rehash, 코드/profile/환경/parent·typed token·단위/시각/상태/장부/목록 변조,
  중복/비유한/잘못된 외부 JSON/256KiB·2MiB 초과·다른 모델/다른 문맥의 checkpoint를 거부했다.
  사건 후 RHS의 domain 실패/크기 실패도 원 CP를 바꾸거나 부분 문맥을 반환하지 않는다.
- 별도 producer/fresh 프로세스의 **36문맥/36snapshot 전 bytes·SHA와3,996개 상태 성분**을 대사했다.
  초기 source parent6개는 fresh fence 전에 재구성했고, 그 후 capture36회의 point36/RHS72 외에
  재정규화/과거 replay/전진0이었다. 이후 모든 snapshot/restore에서는 point·RHS를 차단한 채 읽었다.
  원 CP의 다른 상태/선택된 a/A·D0/원 영수증/21누적량을 대사하고 C/U는 별도120자리 Decimal로 확인했다.
  원 `curve_invariant_changes`의 비영 값 **21개**도 그대로 보존했다. 생물학적 측정/정확도 수치가 아니라 원 적분의 면적 companion 불변량 변화다.
  다시 해시한 후속 step36개는 거부했다. DB/CLI/network/쓰기 시도0·원 bundle/FD 보존을 확인했다.

최종 관련 guard는134.367초·최대PID81,469,440bytes/합산457,285,632bytes,
fresh는6.658초·81,469,440/439,136,256bytes였다.
512MiB/PID·1GiB 소유+보호 합산·0.25초 표본/600초/로그4MiB를 바꾸지 않았다.
각 phase의 원3,545항목·소스/보호4root와 FD4→4/소유 잔류0을 확인했다.
Windows/전체 host 운영 용량은 위 관측 범위 밖이며 새 서비스·DB/키 변경0이다.
전체 backend·hosted CI·브라우저 회귀/배포는 이번 Python 자식에서 실행하지 않았다.

native Codex CLI `gpt-6.1-sol/xhigh`, turn_context2026-10-24T10:59:30.916Z,
원 LF SHA `d497ddb3d3d88c73d637beb4b5a1202baf36f967912870cdda988b59748cdd7a`·재귀 CLI0으로 판단했다.
선행 point/원 reference profile을 그대로 사용하며 새 자료/계수·실제 관문 채택은 없다.

## 다음 수용과 일정

다음은 **사건 후 실제 짧은 구간과 분할 재개**다.
새 문맥의 현재 a/A·C/N·기후를 초기 정규화 없이 같은 stage RK4에 전달하고, 원 global 격자/정확 시각을 잇는다.
사건 직후 기준의 새 segment21장부와 원21장부·별도 사건 C/용량/현열을 보존하고,
원점→사건→다음 상태의 C/N·열/물/용량 수지를 독립 참조로 대사한다.
모든 단일 cut/다중 예산의 같은 최종 bytes·D0/원 영수증과 실패 직전 상태를 확인한다.
남은 horizon0은 전진 거부이며 기존32초/nonzero outflow 결과를 새 조건으로 덮어쓰지 않는다.

다음 자식의 계약/원 RK4 경계30–50분, 최소 전진/수지70–120분,
독립·분할/실패 검증60–100분, fresh/검토·기록30–50분으로 **190–320집중분**을 낮은 신뢰로 추정한다.
저장3D·복수 사건/출현·공급·전체 작기·생산/자원/Decimal 경제·거시/수급/자율 후보 비교는 포함하지 않는다.
국내 원 측정/미사용 독립 작기0·첫 품종 미확정, 현재 farm/권리 runtime·실제 CLI G1 종단 간과 G0–G4/R2는 남는다.
자료 획득은 개발과 병행하며 전체 제품 완료일은 외부 자료/검증 일정이 없어 계속 미정이다.
