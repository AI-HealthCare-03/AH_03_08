from app.models.guide import Guide, Feedback
from app.models.guide import Guide, Feedback


# 가이드 목록 조회
async def get_guides(user_id: str):
    guides = await Guide.filter(user_id=user_id).all()
    return guides


# 가이드 상세 조회
async def get_guide(guide_id: str, user_id: str):
    guide = await Guide.get_or_none(id=guide_id, user_id=user_id)
    return guide


# 가이드 생성 (DB에 저장, LLM은 ai_worker에서 처리)
async def create_guide(user_id: str, medical_record_id: str):
    # fastapi는 DB에만 저장, LLM 호출은 ai_worker가 담당
    guide = await Guide.create(
        user_id=user_id,
        medical_record_id=medical_record_id,
        llm_model="gpt-4o-mini",
        llm_temperature=0.3
    )
    return guide


# 피드백 저장
async def create_feedback(user_id: str, guide_id: str, rating: int, comment: str = None):
    feedback = await Feedback.create(
        user_id=user_id,
        guide_id=guide_id,
        rating=rating,
        comment=comment,
        status="active"
    )
    return feedback


# 피드백 목록 조회 (관리자용)
async def get_feedbacks():
    feedbacks = await Feedback.all()
    return feedbacks


# 가이드 목록 조회
async def get_guides(user_id: str):
    guides = await Guide.filter(user_id=user_id).all()
    return guides


# 가이드 상세 조회
async def get_guide(guide_id: str, user_id: str):
    guide = await Guide.get_or_none(id=guide_id, user_id=user_id)
    return guide


# 가이드 생성 (LLM 호출 포함)
async def create_guide(user_id: str, medical_record_id: str, record_data: dict = None):
    # 1. DB에 먼저 저장 (processing 상태)
    guide = await Guide.create(
        user_id=user_id,
        medical_record_id=medical_record_id,
        llm_model="gpt-4o-mini",
        llm_temperature=0.3
    )

    # 2. LLM 호출해서 가이드 생성
    if record_data:
        llm_result = await generate_guide_with_llm(
            medical_record_data=record_data,
            user_info={"user_id": user_id}
        )
        # 3. 결과 DB에 업데이트
        guide.medication_guide = llm_result["medication_guide"]
        guide.lifestyle_guide = llm_result["lifestyle_guide"]
        await guide.save()

    return guide


# 피드백 저장
async def create_feedback(user_id: str, guide_id: str, rating: int, comment: str = None):
    feedback = await Feedback.create(
        user_id=user_id,
        guide_id=guide_id,
        rating=rating,
        comment=comment,
        status="active"
    )
    return feedback


# 피드백 목록 조회 (관리자용)
async def get_feedbacks():
    feedbacks = await Feedback.all()
    return feedbacks
