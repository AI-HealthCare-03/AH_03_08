## Summary
- Add `scripts/smoke_test_guide.py` — post-deploy smoke (login → generate → poll `done`, verify `llm_temperature=0`)
- Add `app/tests/guide_apis/test_guide_generate_api.py` — generate 202, Celery mock, status/detail, auth
- Add `app/tests/guide_apis/test_feedback_apis.py` — feedback POST/GET, MetricSnapshot, 404/401
- Document smoke test in `docs/evaluation/README.md`

## Test plan
- [x] `uv run ruff check app/tests/guide_apis/ scripts/smoke_test_guide.py`
- [x] `uv run python scripts/smoke_test_guide.py` → PASS
- [ ] `uv run pytest app/tests/guide_apis` (CI with MySQL service)
