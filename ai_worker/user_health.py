"""LLM 프롬프트용 사용자 건강 프로필 (알러지·기저질환).

`ai_worker.prompts.llm_prompts` 가 기대하는 dict 형태로 반환한다.
- allergies: [{"name": str, "severity": str}]
- conditions: [{"name": str}]
"""

from datetime import date


async def load_user_health(user_id: int, user) -> dict:
    """사용자 알러지·기저질환을 DB에서 조회해 프롬프트용 dict를 만든다."""
    if not user:
        return {"allergies": [], "conditions": []}
    from ai_worker.models import Allergy, UnderlyingDisease

    allergy_rows = await Allergy.filter(user_id=user_id).all()
    disease_rows = await UnderlyingDisease.filter(user_id=user_id).all()
    return build_user_health(user, allergy_rows, disease_rows)


def build_user_health(user, allergy_rows=None, disease_rows=None) -> dict:
    """User ORM + 조회 결과를 프롬프트용 프로필 dict로 변환한다."""
    if not user:
        return {"allergies": [], "conditions": []}
    age = None
    if getattr(user, "birth_date", None):
        today = date.today()
        age = (
            today.year
            - user.birth_date.year
            - ((today.month, today.day) < (user.birth_date.month, user.birth_date.day))
        )
    allergies = [{"name": row.allergy_name, "severity": row.severity or "unknown"} for row in (allergy_rows or [])]
    conditions = [{"name": row.underlying_disease_name} for row in (disease_rows or [])]
    return {
        "age": age,
        "gender": getattr(user, "gender", None),
        "height_cm": getattr(user, "height_cm", None),
        "weight_kg": getattr(user, "weight_kg", None),
        "allergies": allergies,
        "conditions": conditions,
    }
