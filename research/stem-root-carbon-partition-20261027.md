# 줄기·뿌리 새 탄소 유입의 보존 배분 — 2026-10-27 KST

기존 `stem_root` 성장 유입을 명시 절간과 하나의 명시 뿌리계에 배분하는 [계산 모듈](../backend/app/crop_stem_root_carbon_partition.py)을 추가했다. [계약](../contracts/crop-stem-root-carbon-partition-v1.md)의 합성 순수 산술 자식만 수용했다. 기관별 현재 재고·유지호흡·고갈·공급 제한 길이/직경·생산량·농장/제품 실행을 수용한 것이 아니다.

## 근거와 판단

[1차 문헌/권리 조사](stem-carbon-growth-primary-sources-20261027.md)와 원 코드를 직접 대조했다. 기존 [growth rates](../backend/app/crop_growth_rates.py)의 `allocation.stem_root`는 구조 형성 유입이고 유지호흡을 뺀 `derivatives.stem_root`와 다르다. 원 성장호흡 비용 `cStemG`는 고정 프로필에서 그대로 읽는다. 기존 leaf용 비용이나 임의 새 계수를 사용하지 않았다. 합계에는 뿌리가 포함되므로 줄기에만 전부 배분하지 않는다.

상대 가중치는 자체 합성 우선순위다. 양의 가중치가 있으면 원 유입 예산을 전부 나누며, 절대 수요 상한이나 탄소 부족 생장 법칙이 아니다. 전부0 sink의 유입 보류와 미사용 구조/회피 호흡의 환급은 **프로젝트 정책**이다. 상위 buffer가 이미 차감한 비용을 두 번 부과하지 않도록 buffer·stem_root·성장호흡의 세 조정량을 함께 반환한다. 이 첫 함수는 상위 상태를 직접 수정하지 않는다.

현재 native Codex CLI의 실제 context는 `2026-10-26T16:34:47.652Z`, model `gpt-6.1-sol`, effort `xhigh`다. `2026-10-26T16:39:40.677799Z`에 원 LF를 읽었고 SHA-256은 `ec7abfa12c7b7c55cb7a1c7ccdf3e228512e4797229d733ea7e31b39055608fe`다. 재귀 CLI 실행0이다. research 스킬에 따라 같은 모델/effort를 명시해 background 연구자에게 1차 문헌과 자료 권리 조사를 위임했다. 자식의 실제 native context는 관측하지 못했으며 부모 증거로 대체하지 않는다. 모델 선택·계약·코드 판단은 부모가 원 코드와 연구 결과를 검토해 수행했다.

## 검증

| 범위 | 관측한 결과 |
|---|---|
| 집중 시험 | 새58개 통과. 독립 Decimal, 0/양수 G·전부0/일부0/상대 sink·root-only/512·잘못된 root/단위/범위·수치 유실·code/profile drift·입력/프로필 불변/동일 재실행 |
| 원 계산 대조 | 원6개 합성 프로그램 ×2 sink 조건의 실제 RHS에서 성장 G/유지호흡/제거·전체 탄소 수지에 세 조정을 함께 대입. 두 조정만 적용하면 남는 호흡 반례도 확인 |
| 독립 fresh | 별도 Python 프로세스2개, 각각72조건/576수치와 원 단위·범위 대조. 출력251,197bytes가 byte 단위로 동일, SHA `8dd081b754809f9deaa3c028845d17fe696029faa9f1f617b1e3941d9e24484f` |
| 호출/쓰기 | fresh에서 성장 함수·하위 프로세스·socket·파일 쓰기 호출0, FastAPI/SQLAlchemy/psycopg import0. 입력/프로필을 전진·수정하지 않음 |
| 보존 | 기존 SDK68의 source/output 지문·공개4,732파일·private:false132blob·이전 GUI1,502파일 bytes/metadata·현재 봉인 GUI4,865파일 hash·원512잎 hold와5175/5180 HTTP200 확인 |

최초 시험은 테스트가 재배면적을 기존 프로그램의 잘못된 하위 경로에서 읽어 12실패/46통과였다. 실제 `program.model_floor_area` 위치를 확인해 테스트만 수정한 뒤58개가 통과했다. 생산 계산이나 허용 범위는 이 수정으로 바뀌지 않았다.

각 phase는 WSL PID당512MiB/소유+보호1GiB·0.25초·600초·4MiB 로그 한도로 순차 실행했다. 최종58검사의 관측 최대 PID/합계 RSS는60,252,160/123,654,144bytes, fresh는29,925,376/63,496,192bytes다. 보호 외형1개와 별도 유한 수명 미리보기를 계수했으며 검사 소유 프로세스0·FD4→4였다. Windows/전체 호스트 메모리를 이 수치로 측정했다고 하지 않는다.

[구조화 증거](artifacts/stem-root-carbon-partition-20261027.json)에 코드/입력/정책/검사 지문을 기록한다. 기존 [3D 연구 재생](complete-crop-stored-replay-20261027.md)은 같은 봉인 빌드/자료를 유지한다. 이번 함수는 UI나 runtime worker에 결합되지 않았다. 전체 backend/frontend 시험·새 3D·제품 DB/API 실행·실제 농장 검증은 이번 수용 범위가 아니다.

## 자료 확보를 병행한 결과

S3 논문의 Data Availability가 연결한 [VTC 저장소](https://github.com/ksmolen2/vtc)를 메타데이터/README/파일 목록/라이선스 범위에서 추가 확인했다. 현재 revision은 `ae01e73911103b934663f3b4406451a84cdc06d4`다. API의 license는 null이고 해당 revision의 license 경로는404이며 LICENSE/COPYING/NOTICE/별도 데이터 license 파일이 확인되지 않았다. 부모도 `2026-10-26T17:03:04Z`에 공식 repo API의 license=null을 다시 확인했다. **공개 접근을 코드/자료 재사용 허가로 취급하지 않는다.**

파일 이름에 실험/수확 평균 CSV가 있어도 대응되는 절간별 길이·직경·건물중·나이/품종/시각이 검증된 것은 아니다. output 파일을 측정으로 분류하지 않는다. 논문은 매개변수화 자료를 요청으로 제공한다고 설명하며, 이 저장소의 별도 자료 권리는 미확인이다. CSV·개별 식물 기록을 내려받거나 연락/계정/유료 이용을 하지 않았다. [후보 메타데이터 기록](artifacts/stem-root-allometry-data-screening-20261027.json)에 실제 조회 시각/응답 hash와 권리/QC 보류를 기록했다. 역사적 available_at을 repo 생성/commit 시각으로 채우지 않았다.

나중에 권리와 원 자료를 확보하면 모델 개발의 allometry/보정 후보로 검토할 수 있다. 같은 실험의 fitted 자료는 독립 분할 검토가 필요하며 국내 G2나 미사용 미래 G3 검증을 대신하지 않는다. 새 품종/관측 자료 채택0·독립 국내 측정0건·G0–G4 미평가를 유지한다.

## 다음 한 단계

기존 개별 잎/기후 RHS의 **같은 stage를 한 번** 평가하고 그 stem_root G와 같은 footprint/프로필을 새 배분에 결속한다. 세 조정을 함께 한 번 적용하며 원 광합성·잎·과실·기후·유지호흡/제거와 원 source hash를 보존한다. 원 G를 caller 값으로 대체하거나 상위가 hold한 상태를 임의로 복구하지 않는다. 독립 전체 C 수지·원 함수 호출 수·root/단위/source/profile 변조·all-zero sink·실패 출력과 기존 자료 보존을 수용 기준으로 한다.

그 뒤에 명시 초기 기관/뿌리 C 또는 미배정 잔량, 기관별 유지호흡/고갈·공동 적분/재개·출현 비용을 연결한다. 이들의 수용을 실제 품종의 탄소 제한 길이·공급 제한 면적·한 작기/수확의 수용으로 확대하지 않는다. 공급 제한 법칙의 소프트웨어 개발과 실제 allometry/품종·농장 자료 확보는 병행하며, 기존 QA 면적/길이·초기 이력을 자동 보정하지 않는다.

다음 공동 RHS 결속은 인터페이스/단위 대조15–30분 + 구현15–30분 + 독립 수지/거부·보존 검사30–60분으로 잠정60–120집중분, 낮은 신뢰다. 전체 제품 완료일은 자료 확보와 한 작기/자원·경제/거시·수급/후보 비교의 실제 분해 전 미정이며 전체 goal은 active/incomplete다.
