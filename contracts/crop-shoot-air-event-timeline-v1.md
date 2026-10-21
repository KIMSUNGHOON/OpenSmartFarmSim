# 공통 실내 기온과 정확한 출현 사건 시각 — 연구 v1

상태: 합성 timeline 새28/기존204검사 수용. [열적 문턱](crop-phytomer-thermal-events-v1.md)과
[실내 기온 시계](crop-morphology-thermal-clock-v1.md)의 합성 연결이다.
원 논문의 일별 시계를 세분한 이 프로젝트의 수치 정책이며 관측 출현 시각이 아니다.

`advance_shoot_event_timeline(*, inputs)`는 `input_id`, `state`, `segments`를 받는다.
state는 `origin=synthetic`, `age_basis=since_shoot_development_origin`, `shoot_id`,
`development_origin_id`, `schedule_id`, `started_at`, `at`, `base_temperature`, `age_exact`,
`next_threshold_exact`, `phyllochron_exact`, `next_sequence`만 포함한다.
식별자·순번/기약 유리수/단위·양수 간격/다음 문턱은 앞선 문턱 계약을 따른다.
두 시각은 whole-second UTC이며 `started_at<=at`, 같을 때 나이는0이다.
시작 이후 과거의 기온 이력을 이 순수 함수가 인증하지는 않는다.
segments는 원 시계와 같은1–512개 연속·전진하는 상수 실내 기온 구간이다.
기준온도 미만/결측/역행·잘못된 단위는 같은 hold이며 기본 계수/기온 clipping은 없다.

공용 `integrate_constant_air_segments`를 원 시계에서 추출하여 같은 정확 유리수 나이/구간을 만든다.
그 원 나이에서 문턱을 나열하고, 양의 기온차 구간에서 정확한 사건 경과 초를 역산한다.

```text
elapsed_event_seconds = seconds(started_at,segment.start)
                      + (threshold − segment.start_age) × 86400 / (Tair−Tbase)
```

출력은 `model_version=shoot-air-phytomer-timeline-research-v1`, 합성/연구/미평가 표식,
입력 SHA-256, `time_origin_utc=started_at`, 사건과 새 checkpoint다.
각 사건은 원 `sequence`/`thermal_age_exact`, `elapsed_seconds_exact {numerator,denominator,unit:s}`,
`utc_whole_second`다. 경과 초가 정수일 때만 UTC 문자열을 제공하며 소수 초에는 null이다.
정확 유리수 시각을 버리거나 반올림/clip하지 않는다. 소수 초도 이 timeline의 유효한 계산이며
whole-second 절간 상태에 결속하는 후속 어댑터는 명시 지원/hold 정책을 적용해야 한다.
오른쪽 문턱/구간 끝은 포함하고 무열증가 구간은 사건을 만들지 않는다.

사건/초 carry는1024자리·512사건 상한을 유지한다. checkpoint는 같은 시계 원점/식별자/온도 기준,
전진한 원 UTC/정확 나이·다음 문턱/순번이다. 분할/전체 실행의 사건 연결과 끝 checkpoint는 같아야 한다.
독립 손계산 시각/경계·flat구간·소수1/3초·윤일, 분할/재개·단위/기온/시계 혼합을 검증하고
기존204검사·원18계산 지문/6root·WSL 상한을 보존한다.
새 절간 초기 길이·초기 기관 목록/전체 키·저장/3D와 실제 품종 계수/관측·G0–G4는 별도다.

[원 수용 기록/실행 범위](../research/crop-shoot-event-timeline-20261021.md).
