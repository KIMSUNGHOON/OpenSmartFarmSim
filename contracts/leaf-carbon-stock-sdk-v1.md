# 저장된 C_i/a/A 원본을 읽는 웹 SDK — 연구 v1

상태: 합성 연구 SDK 수용 — [99신규/249관련·전체 타입/독립 SDK 빌드·HTTP276](../research/leaf-carbon-stock-sdk-20261026.md). [수용된 export](leaf-carbon-stock-export-v1.md)의 별도 자체 합성 공개 packet만 읽는다.
`loadLeafCarbonStockReplay(scenario,signal)`는 고정6개 index/root 지문과 원 provenance를 사용한다.
`decodeLeafCarbonStockFrame(value,checkpoint,descriptor,meta)`는 이미 읽은 원본의 닫힌 투영을 검사한다.
후자는 단독으로 새 root를 인증하지 않으며 게시된 byte 지문 검사는 loader가 담당한다.

모든 GET은 credentials=omit/cache=no-store/redirect=error·AbortSignal/2MiB 상한을 사용한다.
index/root·원10source/notice·모든 CP/DTO의 실제 bytes/길이/SHA, role/path/권리와 원 source 결속을 검사한다.
원 request/program/seed/context·코드/profile/float 환경·정책/격자/정확 분수 초·초기 영수증/curve 지문을 보존한다.
512KiB CP·원107+3n state/21+3n 동적 누적량과 개별 C_i/a/A, 원50과실 cohort/기후·파생 진단을 대사한다.
aggregate leaf를 별도 상태로 만들거나 C_i에서 면적/키/과실을 추론하지 않는다.
원 기록 수지/허용량·초기/최종 상태·이전 CP와 sample/prefix 지문을 보존한다. 새 생장/재개/보간 계산은 없다.

입력은 저장된 합성 표시 기준과 elapsed 격자다. 실제 farm/현재 권리·서명 custody·G0–G4 승인이 아니다.
공개 선언/원 fixture SHA를 고정한 재현 generator와 새 namespace만 추가하고 기존 private False/화면/자료는 유지한다.
반환값은 분리된 복사본이며 모르는 수량을0으로 대체하지 않는다.

수용:6×17 frame/원 CP·19,278수량의 보존, 모든46 wire 파일·DTO/source/단위/ID/권리/시각/경계·취소·상한 변조 거부,
1/512잎과 정확 fractional grid의 투영 경계, 기존 SDK 회귀·전체 타입·독립 SDK 빌드,
별도 실제 HTTP276개 원 응답 bytes와 같은 DTO·4root/WSL/원 private168blob 보존이다.
실제 잎 삼각형/표/그래프·URL/reload/브라우저·사용자 적용은 다음3D 자식에서 수용한다.
기존 주앱 전체 번들 생성은 별도 범위다. 현재 SDK가 그 진입점에 연결되지 않았으며 WSL 자원 상한에서
전체 번들 생성이 중단된 사실을 별도 보류로 남긴다. 독립 SDK 빌드를 주앱 전체 빌드 통과로 표시하지 않는다.
