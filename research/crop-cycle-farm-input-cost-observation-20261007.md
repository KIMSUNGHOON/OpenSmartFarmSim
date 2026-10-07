# 등록 계산 경로의 원 입력 검사 비용

2026-10-07 KST. [선행 비용 분해](crop-cycle-input-validation-cost-observation-20261006.md)가
측정하지 않았던 `CycleFarmBinding._input` 자체를 같은166일 입력에서 직접 실행했다.
**격리한 내부 함수의 비용 관측이며 등록 농장·현재 권리·전체 작기 계산 수용은 아니다.**

## 실제 실행과 범위

[측정 코드](crop-cycle-farm-input-cost-reference.py)와
[불변 영수증](artifacts/crop-cycle-farm-input-cost-reference-20261007.json)을 보존한다.
실제 session88990은 종료0이다. 정확한 원 `InputPacket`과 프로필만 제공하는
`SimpleNamespace`로 원 내부 함수를 호출했다.
이 최소 제공 객체는 `CycleFarmBinding` 생성자·`_bind`·테넌트·등록/권리 검사를 통과한 객체가 아니다.

```bash
nice -n 19 backend/.venv/bin/python research/crop-cycle-farm-input-cost-reference.py \
  --supervision /home/sunghoonk/.local/state/OpenSmartFarmSim/20261007-full166-durable-v2/supervision.json \
  --supervision-sha256 1952feae10039b2f955ee676b4ff3e7f79ce040420b3fa657f5ff3da03d9ecfc \
  --cli-context /home/sunghoonk/.local/state/OpenSmartFarmSim/20261007-result-evidence-resume/farm-input-cost-native-cli.json \
  --output research/artifacts/crop-cycle-farm-input-cost-reference-20261007.json
```

기존 nice15 전체 계산과 병행한 nice19 단일 읽기 프로세스다. 원 입력/root·artifact를
작성하거나 실행 중 worker를 중단하지 않았다. 최초 원 preflight 뒤 같은 reader로 두 번 호출했다.
OS cache는 통제하지 않았다. 함수 전후 원 root/plan과 두 반환값을 대사했으며 원55개 소스를 보존했다.
RHS guard0회·FD4→4·원 함수 복원을 확인했다. 프로그램 시험·PG·서버·브라우저는 실행하지 않았다.

| 실제 범위 | wall초 | CPU초 |
| --- | ---: | ---: |
| 최초 원 reader 열기/preflight | 22.567269 | 22.565806 |
| 첫 `_input` | 22.052056 | 22.050429 |
| 둘째 `_input` | 22.224901 | 22.223414 |
| 관측 프로세스 측정 구간 | 66.860726 | 66.856129 |

두 반환값의 공통 SHA는 `d67d68ea6cd7640d3495612dd2a3f513df6f81b841c63832a17f599c0b737136`이다.
원47,811경계·1,816,704걸음 plan·113,920,841 입력bytes를 유지했다.
영수증 SHA는 `2942bf8bb5e503c7fb2e7eb5d4c804015444839c8c23f5261fddac13f4972101`이다.
현재 native CLI는 `2026-10-07T06:46:44.459Z`, `gpt-6.1-sol/xhigh`, 원행 LF 제외 SHA
`0cf5096bcb23a7e188dff69f52818accc28f0ea60f0e8044d55345d9543c572a`; 재귀 CLI0회다.

## 메모리 관측의 한계

첫 프로세스의 `RUSAGE_SELF.ru_maxrss` 기록은581,406,720bytes다. 해당 프로세스의
활성 RSS를 단계별로 샘플링하지 않아 이 최대치를 특정 함수에 귀속하지 않는다.
잔여 메모리 위험을 좁히기 위한 별도 nice19 진단은 원 preflight/내부 함수 각1회만 실행했다.
그 진단의50ms 활성 RSS 표본 최대65,392,640bytes·커널 VmHWM65,159,168bytes,
wall45.452146초를 확인했다. 서로 다른 프로세스이므로 첫 최대치의 원인을 증명하거나 대체하지 않는다.
진단은 RHS 계측을 추가하지 않았으며 원 input/plan만 대사했다.
사설 `farm-input-cost-memory-phases.json`과 `farm-input-cost-memory-preparation.json`에 원 관측을 보존했다.
등록 계산의 메모리 수용은 실제 worker의 활성 RSS·한도 검사에서 별도로 확인해야 한다.

## 다음 구현 판단과 수용 기준

[원 농장 결합](../backend/app/crop_cycle_farm_binding.py)의 `_bind`는 `_input`을 앞뒤로 부른다.
이번 두 직접 호출의 합은44.276957초지만 **실제 `_bind`/HTTPS의 지연 실측이 아니다.**
등록/권리/DB·context·누적 artifact/proof 검사는 이 관측에 포함하지 않았다.
14,567commit 전체 시간을 이 두 값으로 외삽하거나 `_input`만 개선하면 전체 부하가 해결된다고 보지 않는다.

[현재 조회](crop-cycle-query-runtime-implementation-20261007.md)는 별도 읽기 문맥으로 수용했다.
그 작업은 계산 쪽 원 preflight 반복을 바꾸지 않았다. 다음 작은 개발은 계산용 검증 문맥과
현재 농장/권리·custody 연결로 나누고 [계획](../tasks/plan.md)·[작업 목록](../tasks/todo.md)에 연결한다.
실행 중55개 소스는 종료·증거 보존 전 변경하지 않는다. 계산용 공식 factory/별도 판본을 검증하며
조회 객체나 원 private token/캐시 주입으로 계산을 허용하지 않는다.
첫 수용은 원 값/UTC·121상태/checkpoint·수지/hold·현재 byte 변조 거부와 별도 프로세스 복원이다.
입력 schema/QC의 최초 실제 검사와 코드·프로필·키 변경 거부를 유지하고, 새 코드/manifest를 과거 결과에
소급 적용하지 않는다. 다음 연결은 실제 SCRAM에서 계산 권리·등록/Scope의 전후 철회·변조를 확인해야 한다.
원 전체 작기·저장/API/같은 UTC3D 수용과 G0–G4·생산/추천 보류는 유지한다.
