# 원 입력 검사의 서버 영수증 primitive

2026-10-06 KST. [계약](../contracts/crop-cycle-input-evidence-v1.md)의3 core파일로
[비용 분해](crop-cycle-input-validation-cost-observation-20261006.md)·[연구 대사 실험](crop-cycle-input-witness-experiment-20261006.md)을
서버용 typed evidence 경계에 연결했다. **이 primitive의 로컬 소프트웨어 수용이며 실제 farm/runtime/API 연결 수용은 아니다.**

## 구현과 집중 검증

[InputEvidenceAuthority](../backend/app/crop_cycle_input_evidence.py)는 서버 제공 별도 키·issuer/key ID와
프로필/고지를 고정한다. 발행은 모든 원 bytes의 소유권/0400/단일 링크/ACL·읽기 전후 metadata·SHA를
먼저 확인하고 원 전체 preflight/context를 수행한 뒤 같은 bytes를 다시 확인한다.
원 manifest·index·initial/121 seed·Fraction clock·계획을 그대로 인증한다. 파일 검사는 기존
server custody/helper를 재사용했으며 새 비밀 저장소·서비스·DB 표를 만들지 않았다.
재조회는 canonical/닫힌 JSON·HMAC·정확한 issuer/key ID·영수증 판본/코드/의존성·
profile/notice/Python과 모든 현재 원 bytes/목록/총 bytes를 대사한다.
`VerifiedInputEvidence.context`는 사본이며 rights/gate 승인은 false다.
원 `InputPacket`/`StreamContext`의 private token/캐시에 주입하지 않고 기존 reader/farm/runtime/API를 유지했다.

[집중 시험](../backend/tests/test_crop_cycle_input_evidence.py)의 최종은 **33통과/1.89초**, session40751 종료0이다.
원 전체 검사 호출/발행 실패·조회 parser 재호출 금지·현재 root/blob 변조/누락·symlink/여분 파일·
쓰기 허용/다중 링크/디렉터리 mode·payload/MAC/key/issuer/key ID/판본/코드/source·
비정규/중복/NaN/크기·유효 서명의 잘못된 seed/clock/문맥·설정 drift·FD 정리를 확인했다.
같은 사설 시험 키를 보존한 별도 Python도 같은 context/hash·승인 false를 확인했다.

```bash
cd backend
nice -n 15 .venv/bin/python -m pytest tests/test_crop_cycle_input_evidence.py -q
```

최초 workspace-root 실행은 PYTHONPATH 오류1개/0.15초였고, backend에서의 실제 미구현 RED는
import 오류1개/0.13초다. 첫 구현28통과/2.13초 뒤 소유권 검사 순서/문맥 검사를 보완해 위33개를 통과했다.
반복 수를 합산하지 않는다. 전체 backend/web/browser는 이 단계에서 실행하지 않았다.
최종 사설 로그 `/tmp/ossf-cycle-input-evidence-focused-final-20261006.log` SHA256은
`317db3eff0ebed14ae55740cffc10ef50d8ce1820efb291add7808c467ebb043`다.

## 실제166일 입력의 발행·별도 Python 재조회

현재 native CLI `gpt-6.1-sol / xhigh` 문맥은 `2026-10-06T08:11:42.220Z`,
원 줄 SHA256 `61a600d7111a7739d9a3f5590b961538733ef8798d2f4f91fd21067d4eb024ce`다. CLI 재귀0회.

```bash
nice -n 15 backend/.venv/bin/python /tmp/ossf-cycle-input-evidence-measure-20261006.py issue
nice -n 15 backend/.venv/bin/python /tmp/ossf-cycle-input-evidence-measure-20261006.py verify
```

발행 session50536와 별도 verify exec chunk `a678d4`는 모두 종료0이다.
script SHA256 `af223e2c98a7529ef931dae3d488e650b968a17857305cbcb07c49c5a1abc125`.
[불변 receipt](artifacts/crop-cycle-input-evidence-reference-20261006.json)는 `2026-10-06T08:28:42.045603+00:00`,
SHA256 `6520ac3af1fa02557a2ad2c421aed2378a926e2713fb6d615f737c5842f6d2f4`다.

| 실제 primitive 호출 | wall초 | CPU초 | 원 byte 대사 |
|---|---:|---:|---|
| 원 전체 검사·검사 전후 대사·발행 | 31.342618 | 31.339059 | root+749 blob 두 번, 1,500읽기/227,841,682bytes |
| 보존 키·별도 Python 재조회 | 0.176492 | 0.176478 | root+749 blob 한 번, 750읽기/113,920,841bytes |

import/고정 spec·53source 검사/호출을 포함한 record 직전까지는32.004699초/0.845291초였다.
verify에는 다른 키의 서명 거부도 포함했고 추가 입력 읽기는0회였다. 이 합계는 마지막 record 저장·
process exit·farm/DB/HTTPS를 제외한다. 두 프로세스 RHS0·FD4→4·nice15,
peak RSS89,104,384/81,240,064bytes다. 원 nice10 전체 RHS와 동시 실행됐으며 OS cache는 미통제다.
별도 Python은 cold-cache·다른 장비·HTTP 상한의 증거가 아니다.

원 입력은 고유749 blob·113,920,841bytes이고 반환한 전체 context/index는 원 연구 증명과 같다.
해당 **전체 record** SHA256은 `2704b2aa70c3b2d6539c2ed1d893024413ecfb9eb8840b8dde6c31e7f913cd37`다.
앞선 다른 기록 형식의 common semantic SHA와 구분한다. 원 연구 증명의 raw SHA도 기존 receipt와 대사했다.
새 영수증149,004bytes/SHA256 `fc0fb2e12e39d9de2ae2e3f8a94215f4cb3009cbb88deb5b0e758935105080a7`와
0400 키/관측은 사설 `/tmp/ossf-cycle-input-evidence-native-final-20261006/`에 보관했다.
키는 자체 소유 검증용이며 실제 운영 배포 key custody/rotation 수용이 아니다.

첫 전체 측정 session36442는 **종료1**이다. 측정기가 전체 context-record SHA를 앞선 common
semantic SHA와 혼동했고 원 context의 달라진 필드는0개였지만 assertion 실패로 기록했다.
첫 helper 사본/실패 로그는 사설 보존했으며 당시 측정 script SHA는 미기록이다.
최종 script SHA를 첫 실패에 소급 적용하지 않는다.

## 남은 수용과 순서

실행 중인 원166일의53개 source·입력/기존 artifact를 변경하지 않았다. 원 전체 계산 종료·
모든 출력/수지/정확한 중단 복원을 먼저 수용한다. 이후 현재 영수증을 받는 **공식 typed reader/context
factory의 판본/과거 결과 재생 계약**을 해결하고 현재 farm/Scope·등록/권리의 전후 검사를 연결한다.
기존 v1의 exact type/private token·code SHA를 새 helper의 객체 구성이나 새 code의 v1 재표시로 우회하지 않는다.
최초31.34초 검사나 artifact 전체 검증 비용도 남는다. 실제 서버 보관/선택·typed reader·전체 저장 조회/
UTC page·3D·30초/2MiB·변조/철회·DB/서버/비밀/FD 정리 전에는 replay-restore/부하 부모를 체크하지 않는다.
실제 전체/API 실측 뒤 일정을 갱신한다. 실제 품종/독립 국내 자료0건과 G0–G4 `not_assessed`,
생과 → 자원 → Decimal 경제 순서와 생산 예측·추천 보류를 유지한다.
