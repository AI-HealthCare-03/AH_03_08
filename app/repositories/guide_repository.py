from app.core.config import config
from app.models.guide import Guide


async def create_guide(user_id: int, record_id: str) -> Guide:
    return await Guide.create(
        user_id=user_id,
        record_id=record_id,
        status="processing",
        llm_model=config.OPENAI_CHAT_MODEL,
        llm_temperature=config.GUIDE_LLM_TEMPERATURE,
    )


async def get_guides_by_user(user_id: int) -> list[Guide]:
    return await Guide.filter(user_id=user_id).order_by("-created_at").all()


async def get_guide_by_id(guide_id: str, user_id: int) -> Guide | None:
    return await Guide.get_or_none(id=guide_id, user_id=user_id)
