from tortoise import fields
from tortoise.models import Model


class Guide(Model):
    # 테이블 이름 설정
    class Meta:
        table = "guides"

    # ERD 기준 컬럼 정의
    id = fields.UUIDField(pk=True)
    user_id = fields.UUIDField()                          # 어떤 유저의 가이드인지
    medical_record_id = fields.UUIDField()                # 어떤 진료기록 기반인지 (ERD: medical_record_id)
    medication_guide = fields.TextField(null=True)        # 복약 안내 텍스트
    lifestyle_guide = fields.TextField(null=True)         # 생활습관 안내 텍스트
    llm_model = fields.CharField(max_length=50, null=True)       # 사용한 LLM 모델명
    llm_temperature = fields.FloatField(null=True)        # 사용한 temperature 값
    created_at = fields.DatetimeField(auto_now_add=True)  # 생성 시간 자동 기록


class Feedback(Model):
    # 테이블 이름 설정
    class Meta:
        table = "feedbacks"

    # ERD 기준 컬럼 정의
    id = fields.UUIDField(pk=True)
    guide_id = fields.UUIDField()         # 어떤 가이드에 대한 피드백인지
    user_id = fields.UUIDField()          # 누가 남긴 피드백인지
    rating = fields.IntField(null=True)   # 평점
    comment = fields.CharField(max_length=500, null=True)  # 코멘트
    status = fields.CharField(max_length=20, null=True)    # 피드백 상태
    deactive_at = fields.DatetimeField(null=True)          # 비활성화 시간
    deactive_by = fields.UUIDField(null=True)              # 비활성화한 유저
    created_at = fields.DatetimeField(auto_now_add=True)