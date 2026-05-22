import json
import os

from celery import shared_task
from openai import OpenAI

from ai_worker.prompts.llm_prompts import GUIDE_SYSTEM, build_guide_user_prompt

@shared_task(name="ai_worker.tasks.llm_task.generate_guide")
def generate_guide(guide_id: str, medications: list, user_health: dict, rag_context: str = "") -> dict:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    user_prompt = build_guide_user_prompt(medications=medications, user_health=user_health, rag_context=rag_context)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": GUIDE_SYSTEM}, {"role": "user", "content": user_prompt}],
        temperature=0.3,
    )
    result = response.choices[0].message.content
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
