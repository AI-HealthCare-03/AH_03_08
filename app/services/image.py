# app/services/image.py
# 표준 라이브러리
import os

# 서드파티 라이브러리
from celery import Celery

# 로컬 모듈
from app.dtos.image import ImageAnalyzeResponse

# Celery 앱 초기화 (Redis 브로커 연결)
celery_app = Celery(broker=os.getenv("REDIS_URL", "redis://redis:6379/0"))


class ImageService:
    async def analyze_image(
        self,
        record_id: str,
        user_id: str,
        image_bytes: bytes,  # 사용자가 업로드한 이미지 데이터
    ) -> ImageAnalyzeResponse:
        """
        낱알약 이미지 분류 요청을 처리하고 Celery Task를 등록한다.
        REQ-IMG-001 ~ REQ-IMG-005 연동
        Args:
            record_id: 여진님 /records/upload에서 반환된 record_id
            user_id: 요청한 사용자 ID
            image_bytes: 사용자가 업로드한 이미지 파일 (bytes)
        Returns:
            ImageAnalyzeResponse: { record_id, status }
        Note:
            - 개인정보 보호: 이미지 데이터 로그 출력 금지
            - app과 ai_worker가 별도 컨테이너라 send_task()로 Redis에 등록
            - TODO: DB 연동 후 record_type == 2(낱알약) 검증 추가 필요
        """
        # Celery Task 등록
        celery_app.send_task(
            "ai_worker.tasks.image_task.classify_pill",
            kwargs={
                "record_id": record_id,
                "user_id": user_id,
                "image_bytes": image_bytes,
            },
            queue="image",
        )
        return ImageAnalyzeResponse(
            record_id=record_id,  # analysis_id 제거, record_id 반환
            status="processing",
        )
