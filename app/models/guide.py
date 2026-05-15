from tortoise import fields
from tortoise.models import Model


class Guide(Model):
    # 테이블 이름 설정
    class Meta:
        table = "guides"

    # 각 컬럼 정의
    id = fields.UUIDField(pk=True)           # 고유 ID (자동생성)
    user_id = fields.UUIDField()             # 어떤 유저의 가이드인지
    record_id = fields.UUIDField()           # 어떤 진료기록 기반인지
    status = fields.CharField(max_length=20, default="processing")  # processing / done / failed
    medication_guide = fields.TextField(null=True)   # 복약 안내 텍스트
    lifestyle_guide = fields.TextField(null=True)    # 생활습관 안내 텍스트
    allergy_warnings = fields.JSONField(null=True)   # 알러지 경고 목록
    condition_interactions = fields.JSONField(null=True)  # 기저질환 상호작용
    prompt_version = fields.CharField(max_length=20, default="v1.0")  # 어떤 프롬프트 썼는지 (피드백 개선 추적용!)
    created_at = fields.DatetimeField(auto_now_add=True)  # 생성 시간 자동 기록


class Feedback(Model):
    # 테이블 이름 설정
    class Meta:
        table = "feedbacks"

    id = fields.UUIDField(pk=True)
    user_id = fields.UUIDField()
    guide_id = fields.UUIDField()
    rating = fields.IntField()        # 0 = 아쉬워요, 1 = 도움됐어요
    label = fields.IntField()         # 1~10 태그
    comment = fields.TextField(null=True)   # 유저 직접 입력 코멘트
    prompt_version = fields.CharField(max_length=20, null=True)  # 피드백→프롬프트 개선 연결고리
    created_at = fields.DatetimeField(auto_now_add=True)
    