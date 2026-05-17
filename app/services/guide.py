from app.models.guide import Guide, Feedback


# 가이드 목록 조회
async def get_guides(user_id: str):
    guides = await Guide.filter(user_id=user_id).all()
    return guides


# 가이드 상세 조회
async def get_guide(guide_id: str, user_id: str):
    guide = await Guide.get_or_none(id=guide_id, user_id=user_id)
    return guide


# 가이드 생성 (DB에 저장)
async def create_guide(user_id: str, medical_record_id: str):
    # 의료기록 기반으로 가이드 생성 (LLM 호출 전 DB에 먼저 저장)
    guide = await Guide.create(
        user_id=user_id,
        medical_record_id=medical_record_id,  # ERD 기준 컬럼명
        llm_model="gpt-4o-mini",              # 사용할 LLM 모델
        llm_temperature=0.3                   # 코치님 피드백: 0 말고 조정
    )
    return guide


# 피드백 저장
async def create_feedback(user_id: str, guide_id: str, rating: int, comment: str = None):
    # 개인정보 보호: comment에 민감정보 포함 여부 주의
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