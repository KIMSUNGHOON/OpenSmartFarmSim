# JSON 재사용 후보의 관측 경계 검토·미채택 — 2026-10-20 KST

[기계 증거](artifacts/solar-json-observation-boundaries-20261020.json) · [직전 실행 시간 미수용](solar-json-dictionary-lookup-20261020.md) · [실제 구간 관측](solar-json-residual-whole-profile-20261020.md).

## 현재 결정

**JSON 소유권 재사용 후보의 평가를 미채택으로 종료한다.** 현재 검사로는 디코딩한 자료가 외부 도우미에 노출되지 않았음을 보장하지 못한다. 검사 횟수를 줄이는 구현으로 진행하지 않는다. 제품 app261개/SHA d477b74b…·호출0은 그대로다.

기존176개 집중검사의 통과는 당시 시험 범위의 기록이다. 이번 반례를 포함하는 소유권·오류 동등성의 채택 근거로 확대할 수 없다. 과거 보고서는 보존하고 이번 판정으로 현재 채택 상태를 정정한다. 세 연구 모듈에는 미채택·반례 재현용임을 표시했다. 실행 본문은 그대로 두고 core 의존성 pin만 현재 파일에 맞췄다.

## 구문 검사와 실제 호출

원 `_records`에는 구문 앞 검사14곳, 사설 `prepare_commit`에는13곳을 생성한다. 각 영역5곳은 해당 구문의 직접 표현에 호출이 없지만, 이것만으로 검사 제거의 안전성을 판단할 수 없다. 원 `type(row) … set(row) … clock._point(...)`처럼 하나의 식이 여러 실제 호출을 포함한다.

| 경계 | 현재 방식 | 검토 결과 |
| --- | --- | --- |
| 행 검증식 | 식 실행 전 상태를 검사 | 식 안에서 다른 함수가 선택되면 그 호출의 자료 노출을 놓칠 수 있다. |
| JSON 디코더 | 호출 전후 모듈·함수 상태 검사 | 내부 factory가 외부 scanner를 만들고 복원하면, 새 인스턴스 안에 남은 호출과 반환 자료의 노출을 증명하지 못한다. |
| source/payload 결합 | 비노출 자료라고 가정하고 이전 source bytes 사용 | 외부에 노출된 자료가 두 hash 사이에 바뀌면 원 오류 순서가 달라진다. |
| 순수 지역 대입·반환 | 추가 구문 검사 | 실제 호출·자료 수명에 관한 증거가 먼저 필요하다. 이번에는 관측을 제거하지 않았다. |

반례는 합성 자료와 시험 중 Python 공개 바인딩 교체를 사용했다. 자료는 실제 콜백 인자나 scanner 반환값으로 획득했다. 스택에서 비공개 자료를 꺼내거나 파일을 변조하지 않았다.

## 실제 반례3종

1. **식 안의 자기 복원 도우미/노출:** 원 행 검증의 `type(row)` 반환 뒤 `set`을 잠시 교체했다. 실제 `set(row)`가 행을 받아 보관한 뒤 native binding을 복원했다. 결과 값은 원 경로와 같았지만 후보는 노출된 자료를 포함한6개 source pair를 재사용했다.
2. **노출 뒤 변경/오류 차이:** 같은 행을 source hash 검사 뒤 변경했다. 원 경로는 `HASH_HOLD: exact bound result/context/scope`, 후보는 뒤의 `COMMIT_HOLD: original prefix/cursor`에서 실패했다. 기존 모든 구문 검사를 유지한 상태에서도 오류 순서가 달랐다.
3. **디코더 내부 factory/재사용 값 차이:** native `JSONDecoder`에 들어간 뒤 scanner factory를 잠시 교체했다. scanner는 실제 디코딩 결과를 보관하고 factory를 복원했다. 전후 native 판정은 참이었지만 보관한 graph를 바꾸자, 같은 파일을 재검사한 캐시가 새 원 읽기와 다른 값을 반환했다. 원 blob SHA는 `b62260bb…`, 캐시 값 SHA는 `9ba9dae6…`였다. cache hit1·raw 예산938bytes·종료 정리를 확인했다.

CPython3.12.3과 잠금 판본3.12.13에서 각3종을 재현했다. **3통과는 반례 재현의 성공이며 후보 기능의 수용이 아니다.** 판본별 출력은 각각의 변경 불가 증거 디렉터리에 보관했다. 잠금 판본 검사는 현재 설치된 패키지를 사용한 검사이며 clean hosted 설치는 아니다.

## 재현 코드

[공개 반례 검사](solar-json-observation-counterexamples.py)는 합성 fixture를 새 임시 디렉터리에 생성한다. 성공은 미채택 후보의 반례를 재현했다는 뜻이다. 이번 실제 실행은 보호 서비스/RSS를 검사하는 소유 실행기로 수행했다.

```bash
cd backend
.venv/bin/python -B -m pytest ../research/solar-json-observation-counterexamples.py -q
```

## 자원·검증 범위

최종 두 실행은 guard2.402515/2.424846초, 최대 합 RSS947,675,136bytes/1GiB·단일145,444,864bytes/512MiB다. 각 FD4→4·원5root/2,148·두 frozen UI source/자산·소유 프로세스/PG/임시 자료 잔여0을 확인했다. 초기 계측 설정 오류1회는 실제 반례 검증에 포함하지 않았다.

이전176·전체 backend/browser·실제 DB/원64·WebGL·성능 ABBA는 이번에 재실행하지 않았다. 앞선 성능 미달을 유리한 결과까지 반복하지 않았다. 제품·숫자 모델·권리·원 actor/입력/chunk1/poll/retry360/RSS는 유지한다.

## 다음 한 단계

`crop-solar-checkpoint-consumer-validation-boundary`: 제품의 `_snapshot`, `progress`, `_resume`, `_confirm`이 실제로 소비하는 저장 자료와 각 fresh validation의 역할을 대조한다. 기존 checkpoint packet은 hash·진행·시각·수량 metadata이고 수치 checkpoint의 `value`를 포함하지 않는다. `rights_or_gate_approval`도 `False`다. 이를 계산 재개 상태나 현재 권리 승인으로 대체할 수 없다.

다음 수용 기준은 호출자별 필드/불변 bytes/검증 의무·현재/늦은 권리·HEAD/ancestry/lease/cancel·오류 순서의 목록과 최소 변경 계약이다. 검증을 생략하거나 이전 proof를 현재 승인으로 재사용하지 않는다. 새 증거가 없으면 제품의 원 읽기 경로를 유지한다. 이후 제품 수정/회귀→원 독립 정상64→hold/HTTP취소→계산 중WebGL→WSL 적용 순서를 따른다.

실제 국내 품종·농장/시설·기후·재배/수확/자원과 경제/시장 자료의 권리·독립 검증은 외부 의존성이다. 실제 농장 Run0·G0–G4/미래 생산·마진·최적 추천은 보류이며 전체 완료일/남은 집중시간은 미정이다. native CLI gpt-6.1-sol/xhigh 문맥·source/출력 SHA를 기록했고 재귀 CLI/새 agent0·goal active다.

## 사용자 진행 정보 게시

[게시 영수증](artifacts/solar-json-observation-status-publication-20261020.json): 두5173/5174의 같은 최신 JSON·HTTP200/no-store·원 HTML과 환기2,173파일을 보존했다. 반례3종·JSON 후보 미채택 종료와 제품 checkpoint 검토를 표시한다. UI 코드·DOM/WebGL은 다시 실행하지 않았다. 기존 환기의 `new_model_deployed:true`를 유지하며 새 Solar 적용이 아니다.
