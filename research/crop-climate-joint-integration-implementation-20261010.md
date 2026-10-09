# 작물·기후의 짧은 공동 적분 — 2026-10-10 로컬 수용

## 완료 범위와 산출물

core `cd2870c261423e135142dacdd4de0f3255ff4ff8`의
[공동 적분](../backend/app/crop_climate_joint_integration.py)과
[core5 계약](../contracts/crop-climate-joint-short-integration-v1.md)을 로컬 수용했다.
[6개 합성 구간의 원 상태·22장부·수지·수렴 영수증](artifacts/crop-climate-joint-integration-reference-20261010.json)을 확인할 수 있다.
Artifact SHA-256: `efd2ad505e0d7920df93cc0ba574ec05fc46027348767b9faa46f4442896bc8e`.
`crop-climate-joint-short-integration` 자식만 완료다. 관리 사건을 포함한 부모와
온실 경계·continuation/새 저장/API·3D·실시간 U3는 미완료다.

기관5·과실 C/N100·signed 수관 저장 열/공기 온도/수증기3의 108상태를
같은 RK4 trial에서 갱신한다. 현재 leaf/LAI/용량과 Uref로 Tc를 유도하고
작물·열교환·총 용량 운반과 동적 T24/Tsum을 함께 계산한다.
각 stage의 실제 유량으로 탄소·개수·열·물·용량의 22개 장부를 같은 가중치로 적분한다.
매 endpoint에서 7개 수지를 통과해야 다음 확정 상태가 된다.

명시 상수 forcing/RGR의 사건 없는 한 구간이며 dt/count/horizon·sampling을 계산 해시에 묶었다.
기존121상태/상수 Tcan Fraction clock·checkpoint/전체 작기 결과는 보존했다.
외부 수관 액수는 `-integral(E)` 경계로 표시하며 급액 충분성/실제 물 소비를 계산하지 않는다.
과실 terminal 경계도 실제 수확 kg·판매량으로 해석하지 않는다.

## 실제 CLI와 근거

부모 native CLI `gpt-6.1-sol` / `xhigh`의 실제 turn-context는
`2026-10-09T15:47:42.621Z`, 원 JSONL 한 줄 LF 포함 SHA는
`c63cc6e20a504c92ede588a1ad5a70272178b1a3005be21551c8c25fad0a2c92`다.
실제 도구 `a55e96`과 별도 root가 대사했으며 재귀 CLI 실행은 0이다.
이는 개발 계산/검토 기록이며 제품 runtime CLI·독립 해제·관문 증거는 아니다.

선행 [공동 RHS](crop-climate-joint-rhs-implementation-20261010.md)와
[기후 인터페이스](crop-climate-interface-audit-20261009.md),
[가변 용량/물질 경계 원문 검토](crop-variable-canopy-energy-review-20261009.md)를 사용했다.
새 농업 계수/자료는 채택하지 않았다. 4개 프로필과 독립 참조/합성 입력 11개 SHA,
기존 RHS core5·의존 코드9개·BSD 고지를 재확인했다.
실제 조직 물성/잎 수분·대사열·품종/시설 입력은 미확인이다.

## 실행과 검증

Python3.12.3, 현재 checkout의 별도 소유 controller에서 실행했다.
각 실행은 wall120초/로그4MiB·0.25초 RSS 표본, 단일512MiB/소유+보호1GiB,
원본2,148항목·미리보기3개 boot/PID/start identity·FD·소유 정리를 검사했다.

| 실행 | 실제 결과 | terminal 도구/종료 |
| --- | --- | --- |
| 첫 smoke64233 | 18 passed / 0.41초 | `2bb646` / 0 |
| 독립 Decimal 생성67594 | 6사례 / controller20.242초 | `80b43c` / 0 |
| 집중75566 | 43 passed / 2.84초 | `1b074b` / 0 |
| 최종24304 | 새44 + 기존463 = 507 passed / 5.54초; controller5.930초 | `6c2d7b` / 0 |
| 별도 root18891 | 원 bytes/798수치·수렴60비율·source/FD/native; controller22.296초 | `5ebee7` / 0; 출력 `7e779b` |

[독립 Decimal80 생성기](crop-climate-joint-integration-reference.py)는 app을 import하지 않고
고정 원식과 별도130벡터 RK4로 상태108+장부22를 진행한다.
32초 낮/밤·역 교환·음/0 Uref·빈 과실 첫 진입의 6사례를 같은 dt2초에서 대사했다.
원 fixture bytes를 별도 프로세스에서 재생하고 798개 상태/장부/유도량이
사전 상대5e-12/절대5e-14·온도 절대2e-10 K를 통과했다.
온도 관련 최대 절대차는 `4.547473508864641e-13 K`다.

양의 tail 낮/밤·역 교환의 dt8/4/2초 해를 독립 dt0.25초 해와 비교했다.
Tc/Tair/m_v/T24/Tsum·buffer/과실 C합·H/LE/E의 10개 관측량마다
두 반분 비율, 총60개가 사전 기준8을 초과했다. 최소 비율은 `15.948887424637553`이다.
빈 과실 첫 진입은 같은 dt 알고리즘/원량만 확인했다. 기존 초기 전환 불확실성과
그 사례의 시간 수렴·실제 착과 정확도 보류는 유지한다.
32초 결과로 전체 작기 비용·수렴·품종 정확도를 외삽하지 않는다.

Tref 이동에서 물리 궤적·signed Uref/누적 물질 열의 대응 변환을 확인했다.
실제 같은 stage/호출 수 `4*n+1`·동적 leaf/Tc 피드백·T24/Tsum·입력 불변과
수치/코드/프로필 identity, 닫힌 schema/unit/배열·예산·단계/온도/수치/수지 실패를 검사했다.
실패한 trial/endpoint는 게시하지 않고 마지막 확정108상태/유도량·시각을 남긴다.
초기 장부의 산술 실패도 명시 initial hold로 감싼다.

최대 누적 잔차는 축소 열 `6.140533914678059e-11 J/m2_floor`,
탄소 `7.770474693379048e-12 mg_CH2O/m2_floor`,
수증기 `1.8309464187848956e-17 kg_water/m2_floor`다.
다른 수지도 artifact에 단위와 함께 기록했다. 사전 절대 기준과
64 ulp/걸음 기반 runtime 예산을 모두 통과했다. 물리 정확도 관문이 아니다.

최종/root source1,693개·원본2,148항목·이전 core5·기존 웹 자산/미리보기를 보존했다.
controller/root FD4→4, 소유 non-zombie 잔존0이다.
표본 최대 단일 PID147,255,296bytes·소유+보호 합327,208,960bytes로 한도 안이다.
이 hash/source 검사는 실행 당시 snapshot이며 이후 계획 문서는 별도 commit이다.
새 PG/브라우저·전체 작기 RHS/writer를 실행하지 않았다.

## UI/CI·다음 단계와 외부 의존성

사용자 서버24180은 `ea632c` 관측에서 계속 실행 중이다.
검증 중5173 응답200과 정확한 서비스/DB identity를 유지했다.
현재 UI는 완료 합성166일 생장/수확을 읽는다. 새 공동 적분과 실시간 U3는 미연결이다.
exact4b7fe6f의 [Backend37941890045](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/37941890045)는
2026-10-10 KST 관측 `07a8d0`에서0–4 성공·5 실행 중이다.
같은 판본의 나머지 workflow4개는 `156831`에서 success다.
원 실행을 유지하며 새 core hosted 수용은 주장하지 않는다. 실행 중 CI를 취소하는 push는 보류한다.

다음은 **부분 적엽/줄기·과실 관리 사건의 원자 적용**이다.
입력/같은 초 사건 순서 계약→crop/구획과 U/C의 공동 제거→독립 전후값/실패 보존을 나눠 확인한다.
그 뒤 온실 경계→새 continuation/저장·현재 권리 API·같은 UTC3D→물/양분·구매 에너지
→사용자 실행/Decimal 경제다. 후속 작업량은 관리/경계 계약과 실행 비용을 근거로 갱신한다.
이번 자식 수용일은2026-10-10이며 전체 결합/최종 UI·production 완료일은 아직 산정할 수 없다.
독립 국내 자료 확보는 개발과 병행한다. 실제 농장 Run/국내 독립 자료0건,
G0–G4·생산/미래 마진/추천 hold와 운영 기반 고정을 유지한다.
