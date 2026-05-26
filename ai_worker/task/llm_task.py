import json
import os

from celery import shared_task
from openai import OpenAI

from ai_worker.prompts.llm_prompts import GUIDE_SYSTEM, build_guide_user_prompt
from ai_worker.user_health import load_user_health

_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


async def _load_user_health_by_id(user_id: int) -> dict:
    from ai_worker.models import User
    from ai_worker.task.llm_tasks import _init_tortoise

    await _init_tortoise()
    user = await User.get_or_none(id=user_id)
    return await load_user_health(user_id=user_id, user=user)


@shared_task(name="ai_worker.task.llm_task.generate_guide")
def generate_guide(
    guide_id: str,
    medications: list,
    user_health: dict | None = None,
    rag_context: str = "",
    user_id: int | None = None,
) -> dict:
    if (not user_health) and user_id is not None:
        from ai_worker.task.llm_tasks import _run_async

        user_health = _run_async(_load_user_health_by_id(user_id))
    user_health = user_health or {"allergies": [], "conditions": []}

    user_prompt = build_guide_user_prompt(medications=medications, user_health=user_health, rag_context=rag_context)
    response = _client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": GUIDE_SYSTEM}, {"role": "user", "content": user_prompt}],
        temperature=0,
    )
    result = response.choices[0].message.content or ""
    try:
        parsed = json.loads(result)
    except Exception:
        parsed = {"medication_guide": result, "lifestyle_guide": "", "summary": ""}
    return {
        "guide_id": guide_id,
        "medication_guide": parsed.get("medication_guide", ""),
        "lifestyle_guide": parsed.get("lifestyle_guide", ""),
        "summary": parsed.get("summary", ""),
    }
