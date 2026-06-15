# AI 모델 평가 스크립트

챗봇 KCD 검증 및 OCR 정확도 평가, 비동기 성능 벤치마크, 결과 일관성 검증을 자동화한 스크립트 모음입니다.

---

## 디렉토리 구조

```
scripts/eval/
├── chatbot/
│   ├── run_eval.py          # 챗봇 KCD 평가 실행
│   ├── testcases.json       # 테스트 케이스 25개 (train 20 / test 5)
│   └── results/             # 평가 결과 JSON 저장 (자동 생성)
├── ocr/
│   ├── run_eval.py          # OCR 정확도 평가 실행
│   ├── testcases/           # OCR 테스트 이미지 + 정답 라벨
│   └── results/             # 평가 결과 JSON 저장 (자동 생성)
├── consistency_test.py      # 동일 입력 결과 일관성 검증 (3-3)
├── async_benchmark.py       # 비동기 처리 성능 벤치마크 (3-2)
└── show_history.py          # 전체 평가 히스토리 및 지표 비교
```

---

## 사전 준비

`envs/.local.env` 에 OpenAI API 키가 설정되어 있어야 합니다.

```
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini   # 생략 시 gpt-4o-mini 사용
```

---

## 스크립트별 설명 및 실행 방법

### 1. 챗봇 KCD 평가 — `chatbot/run_eval.py`

**무엇을 하는가**

사용자가 자연어로 질문했을 때 LLM이 올바른 질환명을 응답에 포함하는지 측정합니다.
실제 앱과 동일하게 disease_code를 `current_record`로 시스템 프롬프트에 주입한 뒤 응답을 평가합니다.

**측정 지표 (2개)**

| 지표 | 설명 |
|------|------|
| `name_accuracy` | 정확한 질환명이 응답에 포함된 비율 |
| `synonym_accuracy` | KCD 동의어 포함 기준 통과 비율 (최종 pass/fail 기준) |

**테스트 케이스 구조 (train / test 분리)**

- `train` 20개: 개발 및 프롬프트 튜닝에 사용한 케이스
- `test` 5개: 별도로 분리해 둔 held-out 검증 케이스
  - kcd_010 (증상 심각도), kcd_011 (약물 부작용), kcd_014 (복수 코드), kcd_021 (생활습관), kcd_024 (증상 심각도)

**실행 방법**

```bash
# train 케이스만 평가
uv run python scripts/eval/chatbot/run_eval.py --split train

# test 케이스만 평가 (held-out)
uv run python scripts/eval/chatbot/run_eval.py --split test

# 전체 평가
uv run python scripts/eval/chatbot/run_eval.py
```

**출력 예시**

```
[eval] 모델: gpt-4o-mini, split=train, 테스트 케이스: 20개

  [01/20] kcd_001 ... PASS
  [02/20] kcd_002 ... PASS
  ...

==================================================
  Split           : train  (20건)
  정확 명칭 일치율 : 0.8500
  동의어 포함 일치율: 0.9000
  통과 / 전체      : 18 / 20
==================================================
결과 저장: scripts/eval/chatbot/results/2026-06-15_130000.json
```

---

### 2. OCR 정확도 평가 — `ocr/run_eval.py`

**무엇을 하는가**

처방전 이미지를 OCR로 분석한 결과가 정답 라벨과 얼마나 일치하는지 측정합니다.

**측정 지표 (3개)**

| 지표 | 설명 |
|------|------|
| `avg_field_accuracy` | 환자명·병원명·질병코드 등 기본 필드 정확도 |
| `avg_medication_accuracy` | 약품명·함량·용량·횟수·일수 정확도 |
| `avg_overall` | 위 두 지표의 평균 종합 정확도 |

**테스트 케이스 준비**

```
scripts/eval/ocr/testcases/
└── case_001/
    ├── image.jpg    # 처방전 이미지
    └── label.json   # 정답 라벨
```

`label.json` 형식:
```json
{
  "patient_name": "홍길동",
  "hospital": "서울내과의원",
  "disease_code": "N30.0",
  "medications": [
    {"name": "아목시실린", "concentration": "250mg", "dosage": 1, "frequency": 3, "days": 5}
  ]
}
```

**실행 방법**

```bash
uv run python scripts/eval/ocr/run_eval.py
```

---

### 3. 결과 일관성 검증 — `consistency_test.py` (평가 항목 3-3)

**무엇을 하는가**

동일한 질문을 같은 모델에 30회 반복 전송해 응답이 항상 같은 결과를 내는지 검증합니다.
`temperature=0` 설정이 결과 일관성에 실제로 효과가 있음을 수치로 증명합니다.

**측정 지표**

| 지표 | 설명 |
|------|------|
| `pass_rate` | 30회 중 통과한 비율 |
| `std_dev` | 통과/실패 표준편차 (0에 가까울수록 일관) |
| `consistent_ratio` | 30회 모두 동일한 결과가 나온 케이스 비율 |

**실행 방법**

```bash
# 전체 실행 (25케이스 × 30회 = 750 API 호출, 시간 소요)
uv run python scripts/eval/consistency_test.py

# 빠른 확인용 (5케이스 × 5회)
uv run python scripts/eval/consistency_test.py --runs 5 --cases 5
```

**출력 예시**

```
[consistency] 모델: gpt-4o-mini, temperature=0, 케이스: 25/25개, 반복: 30회

  kcd_001 (1/30) ... PASS
  kcd_001 (2/30) ... PASS
  ...

==============================================================
  케이스       카테고리           pass_rate  std_dev  일관성
  ---------------------------------------------------------
  kcd_001      단순 코드 조회        1.0000   0.0000       O
  kcd_002      코드 + 생활습관       1.0000   0.0000       O
  ...
  평균                               0.9600   0.0400
  
  완전 일관 케이스: 23/25  (92%)
==============================================================
```

---

### 4. 비동기 처리 성능 벤치마크 — `async_benchmark.py` (평가 항목 3-2)

**무엇을 하는가**

동일한 LLM 호출 5건을 순차 실행(sequential)과 동시 실행(concurrent, `asyncio.gather`)으로 각각 수행해 소요 시간을 비교합니다.
Celery 비동기 워커의 성능 개선 효과를 수치로 제시합니다.

**측정 지표**

| 지표 | 설명 |
|------|------|
| 총 소요시간 | 순차 vs 동시 전체 시간 비교 |
| 평균 latency | 요청 1건당 평균 처리 시간 |
| speedup | 순차 대비 동시 처리 속도 향상 배율 |

**실행 방법**

```bash
# 기본 (5건 비교)
uv run python scripts/eval/async_benchmark.py

# 요청 수 조절
uv run python scripts/eval/async_benchmark.py --n 10
```

**출력 예시**

```
[async_benchmark] 모델: gpt-4o-mini, 요청 수: 5개

  [1/2] 순차 실행 (sequential) ...
        완료: 18.34s
  [2/2] 동시 실행 (concurrent) ...
        완료: 4.21s

========================================================
                       순차(sequential)  동시(concurrent)
  --------------------------------------------------------
  총 소요시간 (s)               18.34            4.21
  평균 latency (s)               3.67            3.89
  최대 latency (s)               4.12            4.21
  최소 latency (s)               3.21            3.54
  --------------------------------------------------------
  속도 향상 (speedup): 4.36x  (77.0% 단축)
========================================================
```

---

### 5. 평가 히스토리 비교 — `show_history.py`

**무엇을 하는가**

지금까지 실행한 모든 평가 결과를 날짜순으로 출력하고, 직전 실행 대비 주요 지표의 변화량(Δ)을 함께 표시합니다.

**실행 방법**

```bash
uv run python scripts/eval/show_history.py
```

**출력 예시**

```
[챗봇 KCD 검증 히스토리]
날짜                   split  모델            주요지표          Δ  보조지표
------------------------------------------------------------------------------
2026-06-04 10:56:56    all    gpt-4o-mini  f1    =0.2353        -  precision=0.2222
2026-06-11 14:17:18    all    gpt-4o-mini  f1    =0.7500  +0.5147  precision=0.7800
2026-06-15 13:00:00    train  gpt-4o-mini  syn_acc=0.9000  +0.1500  name_acc=0.8500
2026-06-15 13:05:00    test   gpt-4o-mini  syn_acc=0.8000  -0.1000  name_acc=0.7500
```

---

## 권장 실행 순서

```bash
# 1. train 평가로 기본 성능 확인
uv run python scripts/eval/chatbot/run_eval.py --split train

# 2. test 평가로 일반화 성능 확인
uv run python scripts/eval/chatbot/run_eval.py --split test

# 3. 히스토리에서 지표 변화 확인
uv run python scripts/eval/show_history.py

# 4. 일관성 검증 (시간이 오래 걸리므로 먼저 --runs 5로 테스트)
uv run python scripts/eval/consistency_test.py --runs 5
uv run python scripts/eval/consistency_test.py

# 5. 비동기 벤치마크
uv run python scripts/eval/async_benchmark.py
```

---

## 결과 파일 저장 위치

모든 결과는 JSON 형태로 자동 저장됩니다.

| 스크립트 | 저장 경로 |
|----------|-----------|
| `chatbot/run_eval.py` | `chatbot/results/YYYY-MM-DD_HHMMSS.json` |
| `ocr/run_eval.py` | `ocr/results/YYYY-MM-DD_HHMMSS.json` |
| `consistency_test.py` | `chatbot/results/consistency_YYYY-MM-DD_HHMMSS.json` |
| `async_benchmark.py` | `chatbot/results/async_benchmark_YYYY-MM-DD_HHMMSS.json` |

`show_history.py`는 `consistency_`와 `async_benchmark_` 접두사 파일을 히스토리에서 자동 제외합니다.
