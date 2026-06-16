## Summary
- Add `eval_3_4_feedback_flow.py` for **3-4** feedback POST/GET + admin list verification
- Add `eval_5_1_load_concurrent.py` for **5-1** concurrent load test (`GET /users/me`)
- Extend `eval_guide_common.py` with `login_admin_client()` helper
- Update `docs/evaluation/README.md` with 3-4 and 5-1 load run commands

## Included files
| File | Eval |
|------|------|
| `eval_3_4_feedback_flow.py` | 3-4 |
| `eval_5_1_load_concurrent.py` | 5-1 load |
| `eval_guide_common.py` | admin login helper |
| `docs/evaluation/README.md` | docs |

## Notes
- Measurement reports (`docs/evaluation/reports/`) are generated locally for submission; not included.
- Admin defaults: `EVAL_ADMIN_EMAIL` / `EVAL_ADMIN_PASSWORD` (optional env vars).

## Test plan
- [ ] `uv run python scripts/eval_3_4_feedback_flow.py` (requires existing guide + admin account)
- [ ] `uv run python scripts/eval_5_1_load_concurrent.py --quick`
