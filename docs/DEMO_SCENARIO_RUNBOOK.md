# Demo Scenario Runbook (DeepPCB + Gemini)

## 1) 실제 입력 파일

- Error log: 문자열 또는 `.log/.txt`
- Spec: `spec_excerpt`(문자열) 또는 `spec_document_path`(PDF/TXT 파일 경로)
- CAD/Schematic image: 설계 기준 이미지 (`*_temp.jpg`)
- Tested PCB image: 결함 포함 이미지 (`*_test.jpg`)

DeepPCB 기준 실제 파일 매핑:

- Design: `data/external/DeepPCB/PCBData/*/*/<case>_temp.jpg`
- Tested: `data/external/DeepPCB/PCBData/*/*/<case>_test.jpg`
- GT box: `data/external/DeepPCB/PCBData/*/*_not/<case>.txt`

N-file grouped 입력 지원:

- Endpoint: `POST /orchestrate/grouped`
- 타입별로 분리 입력:
  - `error_logs[]`
  - `design_images[]` (GT/CAD/template)
  - `tested_images[]` (defect/physical)
  - `spec_excerpts[]` 또는 `spec_document_paths[]`
- 사전 매핑 점검: `POST /orchestrate/grouped/preview`

## 2) 오케스트레이션 시나리오

고정 순서:

1. Agent1 Symptom Analyzer
2. Agent2A Spec Precheck (parallel)
3. Agent2B CAD Mapper (parallel)
4. Agent3 Physical Defect Verifier
5. Agent4 Spec Compliance Resolver

핵심 handoff:

- Agent1 -> `agent_2a,agent_2b`
- Agent2A/2B -> `agent_3`
- Agent3 -> `agent_4`

## 3) Error code 형식 (권장)

통일 포맷:

`[ERROR] <ERROR_CODE> - <SHORT_DESCRIPTION> (<RISK_HINT>)`

예시:

- `[ERROR] NET_SHORT_DETECTED - adjacent nets show conductive bridge signature (short risk).`
- `[ERROR] NET_OPEN_DETECTED - continuity break suspected on target trace path (open-circuit risk).`

## 4) Spec 입력/파싱 방식

- `spec_excerpt`가 있으면 우선 사용
- 없으면 `spec_document_path`에서 PDF/TXT를 파싱
- 에러 로그 키워드 기반으로 라인 스코어링 후 주변 라인 포함 excerpt 생성

데모 권장 spec 파일:

- `data/specs/deeppcb_demo_spec_v1.md`

## 5) 실제 검증(benchmark) 절차

모델/vision 호출 가능성 확인:

```bash
PYTHONPATH=. .venv/bin/python -u tools/probe_latest_vision_models.py
```

DeepPCB 실벤치마크:

```bash
PYTHONPATH=. .venv/bin/python -u tools/benchmark_deeppcb_orchestration.py --max-cases 6 --per-class 1
```

산출물:

- JSON: `data/benchmarks/deeppcb_orchestration_*.json`
- MD: `data/benchmarks/deeppcb_orchestration_*.md`

## 6) 발표용으로 보여줄 검증 포인트

- 입력 분리: error/spec/design/tested
- trace 완결성: `agent_1, agent_2a, agent_2b, agent_3, agent_4`
- 모델/키 상태: key invalid 자동 제외 + round-robin success count
- 정량지표: IoU>=0.33 기준 localization/class-aware P/R/F1
- 정성결과: root cause + spec-grounded resolution + red-box overlay

## 7) 현재 프론트엔드 상태 (핵심)

- 5-agent branch UI(2A/2B fan-out/fan-in) 시각화 완료
- 현재 `runCustom`는 `spec_excerpt`만 전송하고 `spec_document_path`는 전송하지 않음
- 즉, PDF 경로 기반 spec 파싱은 백엔드 API에 있으나 프론트 커스텀 실행 경로에서는 미연결

권장 보완:

- spec 파일 업로드 시 백엔드 업로드/저장 후 `spec_document_path`로 연결
- 또는 프론트에서 PDF 텍스트 추출 후 `spec_excerpt`로 전송
