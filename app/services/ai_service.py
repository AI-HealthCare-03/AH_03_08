from fastapi import HTTPException
from celery import Celery
from starlette import status

from app.models.users import User
from app.repositories.health_repository import HealthRepository

celery_app = Celery(broker="redis://redis:6379/1", backend="redis://redis:6379/2")


class AIService:
    def __init__(self):
        self.repo = HealthRepository()

    async def request_analysis(self, user: User, medical_record) -> object:
        task = celery_app.send_task(
            "ai_worker.tasks.ai_tasks.analyze_health_data",
            args=[{
                "user_id": str(user.id),
                "record_id": str(medical_record.id),
                "data": {
                    "ocr_raw_text": medical_record.ocr_raw_text,
                    "parsed_data": medical_record.parsed_data,
                },
            }],
        )
        guide = await self.repo.create_guide(
            user_id=user.id,
            medical_record_id=medical_record.id,
        )
        return guide, task.id

    async def get_guide_or_404(self, guide_id: str, user: User):
        guide = await self.repo.get_guide(guide_id=guide_id, user_id=user.id)
        if not guide:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="가이드를 찾을 수 없습니다.")
        return guide