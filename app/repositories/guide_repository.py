from app.models.guide import Guide, Feedback

async def create_guide(user_id: str, medical_record_id: str):
    guide = await Guide.create(user_id=user_id, medical_record_id=medical_record_id, llm_model="gpt-4o-mini", llm_temperature=0.0)
    return guide

async def get_guides_by_user(user_id: str):
    return await Guide.filter(user_id=user_id).all()

async def get_guide_by_id(guide_id: str, user_id: str):
    return await Guide.get_or_none(id=guide_id, user_id=user_id)

async def update_guide_content(guide_id: str, medication_guide: str, lifestyle_guide: str):
    guide = await Guide.get(id=guide_id)
    guide.medication_guide = medication_guide
    guide.lifestyle_guide = lifestyle_guide
    await guide.save()
    return guide

async def create_feedback(user_id: str, guide_id: str, rating: int, comment: str = None):
    return await Feedback.create(user_id=user_id, guide_id=guide_id, rating=rating, comment=comment, status="active")

async def get_all_feedbacks():
    return await Feedback.all()
