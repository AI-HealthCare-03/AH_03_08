# 평가 점수 — 가이드 API 측정 (3-2, 3-3, 3-4, 5-1)

## 사전 조건

- Docker: `fastapi`, `llm-worker`, `mysql`, `redis` 기동
- Swagger: http://localhost:8000/api/docs
- 고정 계정 (선택): `EVAL_EMAIL`, `EVAL_PASSWORD` 환경변수

```powershell
cd AI_HealthCare_Final_Project_Template
$env:EVAL_EMAIL="jimin_medilog@example.com"
$env:EVAL_PASSWORD="Password123!"
```

## 3-2 비동기 응답시간 (5점)

```powershell
uv run python scripts/eval_guide_async_timing.py --iterations 30 --output docs/evaluation/reports/3-2-report.md
```

| 지표 | 의미 |
|------|------|
| accept_ms | POST `/guides/generate` 202 응답 시간 |
| total_ms | 요청 ~ `status=done` (동기 대기 가정과 비교) |

## 3-3 반복 테스트 (5점)

처방전·약봉투 각 30회, 12항목 키워드 일치율 분석. `llm_task.py` **temperature=0** 확인 후 실행.

```powershell
uv run python scripts/eval_guide_3_3_final.py
```

- 출력: `docs/evaluation/reports/3-3-report-final.md`
- raw JSON: `docs/evaluation/reports/3-3-report-final-raw.json`

## 3-4 피드백 반영 구조 (5점)

사용자 피드백 POST/GET + 관리자 목록 조회 실측. 가이드 1건 이상 필요.

```powershell
# 선택: 관리자 계정 (기본 admin@medilog.com / Passwd1!)
$env:EVAL_ADMIN_EMAIL="admin@medilog.com"
$env:EVAL_ADMIN_PASSWORD="Passwd1!"
uv run python scripts/eval_3_4_feedback_flow.py
```

- 출력: `docs/evaluation/reports/3-4-feedback-verify.md`

## 5-1 P95 Latency (5점)

### 조회 API (단일 사용자)

조회(GET) API 30회 반복, P95 ≤ 3,000ms (llm-worker 불필요).

```powershell
uv run python scripts/eval_5_1_p95_latency.py --iterations 30 --output docs/evaluation/reports/5-1-report.md
```

### 부하 테스트 (동시 사용자)

`GET /users/me` 동시 사용자 시뮬레이션 (1/10/50/100 users × 100 req).

```powershell
uv run python scripts/eval_5_1_load_concurrent.py
uv run python scripts/eval_5_1_load_concurrent.py --quick   # 빠른 확인용
```

- 출력: `docs/evaluation/reports/5-1-load-report.md`

## Notion 정리

1. `docs/evaluation/reports/*.md` 생성 결과 복사
2. 스크린샷: Swagger Network 탭 (선택)
3. 결론 문단은 리포트 하단 `Notion 붙여넣기용 결론` 사용

`reports/` 는 실행 후 생성 (git에 커밋하지 않아도 됨).
