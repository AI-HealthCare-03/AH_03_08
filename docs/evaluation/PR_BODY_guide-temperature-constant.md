## Summary
- Add `GUIDE_LLM_TEMPERATURE` (default `0.0`) to `app/core/config.py` and `ai_worker/core/config.py`
- Use the setting in `guide_repository.create_guide` and `llm_task` ChatOpenAI init
- Align `llm_model` on guide create with `OPENAI_CHAT_MODEL` config

## Why
Guide DB metadata (`llm_temperature`) and actual LLM calls were hardcoded separately. Single env-backed constant keeps 3-3 eval (`llm_temperature=0`) consistent if the value changes.

## Test plan
- [x] `uv run ruff check` on changed files
- [ ] Generate guide → `GET /guides/{id}` shows `llm_temperature=0.0`
- [ ] CI lint / test
