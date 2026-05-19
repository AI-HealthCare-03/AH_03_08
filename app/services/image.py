# app/services/image.py

# 표준 라이브러리
import os
import uuid

# 서드파티 라이브러리
from celery import Celery
from fastapi import HTTPException, UploadFile
from starlette import status

# 로컬 모듈
from app.dtos.image import ImageAnalyzeResponse

# Celery 앱 초기화 (Redis 브로커 연결)
celery_app = Celery(broker=os.getenv("REDIS_URL", "redis://redis:6379/0"))

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png"}


class ImageService:
    async def analyze_image(
        self,
        file: UploadFile,
        record_id: str,
        user_id: str,
    ) -> ImageAnalyzeResponse:
        """
        낱알약 이미지 분류 요청을 처리하고 Celery Task를 등록한다.

        REQ-IMG-001 ~ REQ-IMG-005 연동

        Args:
            file: 사용자가 업로드한 이미지 파일
            record_id: MEDICAL_RECORDS 테이블의 record_id
            user_id: 요청한 사용자 ID

        Returns:
            ImageAnalyzeResponse: { analysis_id, status }

        Note:
            - 개인정보 보호: 이미지 데이터 로그 출력 금지
            - app과 ai_worker가 별도 컨테이너라 send_task()로 Redis에 등록
        """
        # 이미지 형식 검증
        if file.content_type not in ALLOWED_CONTENT_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="지원하지 않는 이미지 형식입니다.",
            )

        # 이미지 bytes 읽기
        image_bytes = await file.read()

        # 고유한 analysis_id 생성
        analysis_id = str(uuid.uuid4())

        # Celery Task 등록
        celery_app.send_task(
            "ai_worker.tasks.image_task.classify_pill",
            kwargs={
                "analysis_id": analysis_id,
                "image_bytes": image_bytes,
                "record_id": record_id,
                "user_id": user_id,
            },
        )

        return ImageAnalyzeResponse(
            analysis_id=analysis_id,
            status="processing",
        )
