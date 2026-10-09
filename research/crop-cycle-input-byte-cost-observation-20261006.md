# 고정 작기 입력의 원본 byte/hash 비용 관측

2026-10-06 KST. [profile](crop-cycle-burden-profile-implementation.md)에서 전체 입력 열기
21.902006초와 context 준비9.171754초를 관측했다. 후속 전체 저장 조회의 비용 개선에 앞서,
같은 자작 합성 입력의 **원본 읽기·해시 검사만** 별도 측정했다.

## 실제 실행과 산출물

[측정 코드](crop-cycle-input-byte-cost-reference.py)와
[불변 영수증](artifacts/crop-cycle-input-byte-cost-reference-20261006.json)을 보존했다.
현재 native Codex CLI `gpt-6.1-sol` / `xhigh`에서 판단했으며 CLI 재귀 실행은0회다.
실제 context 시각은 `2026-10-06T07:18:08.847Z`, 원 줄 SHA256은
`b4c4541d96b02830f3981ba6fbebcb84fdb2ff8a6b05789c1ded4be1218c668a`다.

```bash
nice -n 10 backend/.venv/bin/python research/crop-cycle-input-byte-cost-reference.py \
  --run /tmp/ossf-cycle-full-rhs-166day-20261006 \
  --spec-sha256 9f0415126674a2ab1dd4ccd6fc216c27cdd8cfadf063735c3053d25bc1ee5df6 \
  --cli-context /tmp/ossf-cycle-input-byte-cost-cli-20261006.json \
  --output research/artifacts/crop-cycle-input-byte-cost-reference-20261006.json \
  > /tmp/ossf-cycle-input-byte-cost-20261006.log 2>&1
```

실제 종료0, 영수증 관측 시각 `2026-10-06T07:21:51.899376+00:00`.
영수증 SHA256은 `db6f6ef3967f927014dc56f39c197ec6cea871c9ffbb23e11f28964236890451`,
로그 SHA256은 `f41edfd71d708d06365c9392b8db9a2d53fa4d001645ef2f47198ebfe5e9143f`다.

| 관측 항목 | 실제 값 |
|---|---:|
| 고유 원본 블록 / root 포함 bytes | 749 / 113,920,841 |
| 최대 단일 원본 읽기 | 301,441 bytes |
| 측정 범위 wall / CPU | 0.485012841초 / 0.251883252초 |
| 이 프로세스 peak RSS / nice | 40,095,744 bytes / 10 |
| RHS 호출 / FD 시작·끝 | 0 / 4·4 |

원 reader의 bounded/no-follow 읽기로 root의 canonical bytes/hash, 정확한 파일 목록,
모든 참조 블록의 SHA와 총 bytes를 확인했다. 실행에 앞서 기존 spec/프로필/코드 해시도 확인했지만
그 시간은 위 측정 범위 밖이다. 원 실행의53개 계산·입력·저장·API/profile/runner 파일은 동일하다.
입력과 artifact를 수정하지 않았고 농장/DB/서버/브라우저를 기동하지 않았다.

## 해석과 다음 수용 조건

이 입력은 앞선 실험에서 이미 읽었으며 OS cache 조건을 통제하지 않았다. 한 번의 관측에서
원본 byte/hash 비용이 기존 전체 검사보다 작았다는 근거다. 두 시간을 빼서 형식 검사 비용이나
개선 뒤 API 시간을 확정할 수 없다. 블록 JSON/schema/단위/clock/grid QC, context 준비,
현재 농장·자료 권리, artifact 수지, 실제 HTTPS/3D는 이 측정에 포함하지 않았다.

다음 비용 수정은 같은 원본 byte/hash/schema/QC/격자와 현재 권리·변조 거부를 유지하고,
전체 저장의 시작·중간·끝과 사건 전후를 실제 공개 경로의 기존30초/2MiB 안에서 검증해야 한다.
QC 생략이나 검토되지 않은 cache 사용을 승인한 증거가 아니다.
현재 input root의 normalization과 실행 manifest는 input reader 코드 SHA를 포함한다.
reader 변경 시 새 판본·root/manifest 및 과거 결과 재현을 명시적으로 다뤄야 하며,
진행 중인 원166일 결과에 새 코드의 검증 주장을 소급 연결할 수 없다.

전체 backend/web/browser 검증은 이 관측에서 실행하지 않았다. 실제166일 계산·전체 공개 조회와
`crop-cycle-burden-replay-restore` 수용은 남아 있다. 실제 품종·국내 독립 농장 자료 채택은0건,
G0–G4는 `not_assessed`, 생산 예측·추천은 계속 보류다.
